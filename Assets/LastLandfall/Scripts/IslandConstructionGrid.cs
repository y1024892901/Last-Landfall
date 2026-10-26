using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    // The coordinate grid covers the complete model bounds. Terrain suitability
    // is a property of a cell, never a reason to remove it from the grid.
    public sealed class IslandConstructionGrid
    {
        public const float BuildingSlopeLimit = 22f;
        public const float FoundationReliefLimit = 0.65f;
        public const float SatelliteBuildingSlopeLimit = 32f;
        public const float SatelliteFoundationReliefLimit = 0.95f;
        public const float SatelliteFootprintReliefLimit = 1.35f;
        public readonly Transform Root;
        public readonly MeshCollider[] Surfaces;
        public readonly Bounds LocalBounds;
        public readonly float SeaLevel;
        public readonly int OriginX;
        public readonly int OriginZ;
        public readonly int Width;
        public readonly int Depth;
        private readonly Dictionary<Vector2Int, CellTerrain> terrain = new Dictionary<Vector2Int, CellTerrain>();
        private readonly Bounds[] satelliteSurfaceBounds;
        public const float CoastalWaterBuildMargin = 24f;
        private float[] coastField;
        private int coastResolution;
        private Vector2 coastMin, coastSize;
        private float coastRange;

        public void SetCoastDistanceField(float[] values, int resolution, Vector2 minimum, Vector2 size, float range)
        {
            coastField = values; coastResolution = resolution; coastMin = minimum;
            coastSize = size; coastRange = range;
        }

        public bool IsCoastalWaterCell(Vector2Int cell)
        {
            if (!Contains(cell) || GetTerrain(cell).HasLand) return false;
            if (coastField == null) return false;
            float x = (OriginX + cell.x + .5f - coastMin.x) / coastSize.x * (coastResolution - 1);
            float z = (OriginZ + cell.y + .5f - coastMin.y) / coastSize.y * (coastResolution - 1);
            if (x < 0 || z < 0 || x > coastResolution - 1 || z > coastResolution - 1) return false;
            int ix = Mathf.FloorToInt(x), iz = Mathf.FloorToInt(z);
            int nx = Mathf.Min(ix + 1, coastResolution - 1), nz = Mathf.Min(iz + 1, coastResolution - 1);
            float encoded = Mathf.Lerp(Mathf.Lerp(coastField[iz * coastResolution + ix], coastField[iz * coastResolution + nx], x - ix),
                Mathf.Lerp(coastField[nz * coastResolution + ix], coastField[nz * coastResolution + nx], x - ix), z - iz);
            float distance = (encoded - .5f) * coastRange * 2f;
            return distance >= 0 && distance <= CoastalWaterBuildMargin;
        }

        public struct CellTerrain
        {
            public bool HasLand;
            public bool CompleteLand;
            public float MinimumHeight;
            public float MaximumHeight;
            public float MaximumSlope;
            public float AllowedBuildingSlope;
            public float AllowedCellRelief;
            public float AllowedFootprintRelief;
            public float AllowedRoadSlope;
            public float AllowedRoadRelief;
            public bool AllowsBuilding => CompleteLand && MaximumSlope <= AllowedBuildingSlope &&
                MaximumHeight - MinimumHeight <= AllowedCellRelief;
            public bool AllowsRoad => CompleteLand && MaximumSlope <= AllowedRoadSlope &&
                MaximumHeight - MinimumHeight <= AllowedRoadRelief;
        }

        public IslandConstructionGrid(Transform root, MeshCollider[] surfaces, Bounds localBounds, float seaLevel,
            MeshCollider[] satelliteSurfaces = null)
        {
            Root = root;
            Surfaces = surfaces;
            LocalBounds = localBounds;
            SeaLevel = seaLevel;
            int margin = Mathf.CeilToInt(CoastalWaterBuildMargin);
            OriginX = Mathf.FloorToInt(localBounds.min.x) - margin;
            OriginZ = Mathf.FloorToInt(localBounds.min.z) - margin;
            Width = Mathf.CeilToInt(localBounds.max.x) + margin - OriginX;
            Depth = Mathf.CeilToInt(localBounds.max.z) + margin - OriginZ;
            satelliteSurfaceBounds = BuildLocalSurfaceBounds(root, satelliteSurfaces);
        }

        public bool Contains(Vector2Int cell) => cell.x >= 0 && cell.y >= 0 && cell.x < Width && cell.y < Depth;

        public Vector2Int PointToCell(Vector3 localPoint) => new Vector2Int(
            Mathf.FloorToInt(localPoint.x) - OriginX, Mathf.FloorToInt(localPoint.z) - OriginZ);

        public Vector3 CellCenter(Vector2Int cell)
        {
            Vector3 point = new Vector3(OriginX + cell.x + 0.5f, SeaLevel, OriginZ + cell.y + 0.5f);
            return TrySample(point.x, point.z, out Vector3 ground, out _) ? ground : point;
        }

        public bool TryRaycast(Ray ray, out RaycastHit nearest)
        {
            nearest = default;
            float distance = float.PositiveInfinity;
            if (Surfaces == null) return false;
            foreach (MeshCollider surface in Surfaces)
            {
                if (surface != null && surface.enabled && surface.Raycast(ray, out RaycastHit hit, distance))
                {
                    nearest = hit;
                    distance = hit.distance;
                }
            }
            return !float.IsPositiveInfinity(distance);
        }

        public bool TrySample(float x, float z, out Vector3 point, out Vector3 normal)
        {
            Vector3 origin = Root.TransformPoint(new Vector3(x, LocalBounds.max.y + 8f, z));
            if (TryRaycast(new Ray(origin, -Root.up), out RaycastHit hit))
            {
                point = Root.InverseTransformPoint(hit.point);
                normal = Root.InverseTransformDirection(hit.normal).normalized;
                return point.y > SeaLevel + 0.002f;
            }
            point = new Vector3(x, SeaLevel, z);
            normal = Vector3.up;
            return false;
        }

        public CellTerrain GetTerrain(Vector2Int cell)
        {
            if (!Contains(cell)) return default;
            if (terrain.TryGetValue(cell, out CellTerrain cached)) return cached;
            CellTerrain result = new CellTerrain
            {
                CompleteLand = true,
                MinimumHeight = float.PositiveInfinity,
                MaximumHeight = float.NegativeInfinity,
                AllowedBuildingSlope = IsSatelliteCell(cell) ? SatelliteBuildingSlopeLimit : BuildingSlopeLimit,
                AllowedCellRelief = IsSatelliteCell(cell) ? SatelliteFoundationReliefLimit : FoundationReliefLimit,
                AllowedFootprintRelief = IsSatelliteCell(cell) ? SatelliteFootprintReliefLimit : FoundationReliefLimit,
                AllowedRoadSlope = IsSatelliteCell(cell) ? SatelliteBuildingSlopeLimit : 28f,
                AllowedRoadRelief = IsSatelliteCell(cell) ? SatelliteFoundationReliefLimit : 0.65f
            };
            // Edges, centre and midpoints catch shore crossings and local rock
            // relief, while the visual overlay covers every original triangle.
            for (int x = 0; x < 3; x++)
            for (int z = 0; z < 3; z++)
            {
                float px = OriginX + cell.x + Mathf.Lerp(0.015f, 0.985f, x * 0.5f);
                float pz = OriginZ + cell.y + Mathf.Lerp(0.015f, 0.985f, z * 0.5f);
                if (!TrySample(px, pz, out Vector3 point, out Vector3 normal))
                {
                    result.CompleteLand = false;
                    continue;
                }
                result.HasLand = true;
                result.MinimumHeight = Mathf.Min(result.MinimumHeight, point.y);
                result.MaximumHeight = Mathf.Max(result.MaximumHeight, point.y);
                result.MaximumSlope = Mathf.Max(result.MaximumSlope, Vector3.Angle(Vector3.up, normal));
            }
            terrain[cell] = result;
            return result;
        }

        public bool TryBuildingFootprint(Vector2Int anchor, int width, int depth,
            out Vector3 center, out float foundationHeight)
        {
            center = CellCenter(anchor) + new Vector3((width - 1) * 0.5f, 0f, (depth - 1) * 0.5f);
            float minimum = float.PositiveInfinity;
            float maximum = float.NegativeInfinity;
            float allowedRelief = float.PositiveInfinity;
            bool suitable = true;
            for (int x = 0; x < width; x++)
            for (int z = 0; z < depth; z++)
            {
                CellTerrain cell = GetTerrain(anchor + new Vector2Int(x, z));
                suitable &= cell.AllowsBuilding;
                if (!cell.HasLand) continue;
                minimum = Mathf.Min(minimum, cell.MinimumHeight);
                maximum = Mathf.Max(maximum, cell.MaximumHeight);
                allowedRelief = Mathf.Min(allowedRelief, cell.AllowedFootprintRelief);
            }
            foundationHeight = 0f;
            if (!float.IsNegativeInfinity(maximum))
            {
                center.y = maximum + 0.025f;
                foundationHeight = maximum - minimum + 0.055f;
            }
            return suitable && maximum - minimum <= allowedRelief;
        }

        private bool IsSatelliteCell(Vector2Int cell)
        {
            float x = OriginX + cell.x + 0.5f;
            float z = OriginZ + cell.y + 0.5f;
            if (satelliteSurfaceBounds == null) return false;
            for (int i = 0; i < satelliteSurfaceBounds.Length; i++)
            {
                Bounds bounds = satelliteSurfaceBounds[i];
                if (x >= bounds.min.x && x <= bounds.max.x && z >= bounds.min.z && z <= bounds.max.z)
                    return true;
            }
            return false;
        }

        private static Bounds[] BuildLocalSurfaceBounds(Transform root, MeshCollider[] surfaces)
        {
            if (root == null || surfaces == null || surfaces.Length == 0) return System.Array.Empty<Bounds>();
            List<Bounds> result = new List<Bounds>(surfaces.Length);
            foreach (MeshCollider surface in surfaces)
            {
                Mesh mesh = surface != null ? surface.sharedMesh : null;
                if (mesh == null) continue;
                Bounds meshBounds = mesh.bounds;
                Bounds localBounds = default;
                bool hasBounds = false;
                for (int corner = 0; corner < 8; corner++)
                {
                    Vector3 point = meshBounds.center + Vector3.Scale(meshBounds.extents, new Vector3(
                        (corner & 1) == 0 ? -1f : 1f,
                        (corner & 2) == 0 ? -1f : 1f,
                        (corner & 4) == 0 ? -1f : 1f));
                    point = root.InverseTransformPoint(surface.transform.TransformPoint(point));
                    if (!hasBounds) { localBounds = new Bounds(point, Vector3.zero); hasBounds = true; }
                    else localBounds.Encapsulate(point);
                }
                if (hasBounds) result.Add(localBounds);
            }
            return result.ToArray();
        }
    }
}

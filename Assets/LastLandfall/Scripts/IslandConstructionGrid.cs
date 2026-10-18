using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    // The coordinate grid covers the complete model bounds. Terrain suitability
    // is a property of a cell, never a reason to remove it from the grid.
    public sealed class IslandConstructionGrid
    {
        public const float BuildingSlopeLimit = 14f;
        public const float BuildingElevationLimit = 2.76f;
        public const float FoundationReliefLimit = 0.65f;
        public readonly Transform Root;
        public readonly MeshCollider[] Surfaces;
        public readonly Bounds LocalBounds;
        public readonly float SeaLevel;
        public readonly int OriginX;
        public readonly int OriginZ;
        public readonly int Width;
        public readonly int Depth;
        private readonly Dictionary<Vector2Int, CellTerrain> terrain = new Dictionary<Vector2Int, CellTerrain>();

        public struct CellTerrain
        {
            public bool HasLand;
            public bool CompleteLand;
            public float MinimumHeight;
            public float MaximumHeight;
            public float MaximumSlope;
            public bool AllowsBuilding => CompleteLand && MaximumSlope <= BuildingSlopeLimit &&
                MaximumHeight <= BuildingElevationLimit && MaximumHeight - MinimumHeight <= FoundationReliefLimit;
            public bool AllowsRoad => CompleteLand && MaximumSlope <= 28f && MaximumHeight - MinimumHeight <= 0.65f;
        }

        public IslandConstructionGrid(Transform root, MeshCollider[] surfaces, Bounds localBounds, float seaLevel)
        {
            Root = root;
            Surfaces = surfaces;
            LocalBounds = localBounds;
            SeaLevel = seaLevel;
            OriginX = Mathf.FloorToInt(localBounds.min.x) - 1;
            OriginZ = Mathf.FloorToInt(localBounds.min.z) - 1;
            Width = Mathf.CeilToInt(localBounds.max.x) + 1 - OriginX;
            Depth = Mathf.CeilToInt(localBounds.max.z) + 1 - OriginZ;
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
                MaximumHeight = float.NegativeInfinity
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
            bool suitable = true;
            for (int x = 0; x < width; x++)
            for (int z = 0; z < depth; z++)
            {
                CellTerrain cell = GetTerrain(anchor + new Vector2Int(x, z));
                suitable &= cell.AllowsBuilding;
                if (!cell.HasLand) continue;
                minimum = Mathf.Min(minimum, cell.MinimumHeight);
                maximum = Mathf.Max(maximum, cell.MaximumHeight);
            }
            foundationHeight = 0f;
            if (!float.IsNegativeInfinity(maximum))
            {
                center.y = maximum + 0.025f;
                foundationHeight = maximum - minimum + 0.055f;
            }
            return suitable && maximum - minimum <= FoundationReliefLimit;
        }
    }
}

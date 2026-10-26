using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
using LastLandfall.Prototype;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEditor;
using UnityEditor.SceneManagement;

public static class ExpansionAudit
{
    static BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
    static BuildPlacementPrototype host;
    static Camera camera;
    static string output;
    static int frame;
    static Bounds[] islandBounds;
    public static void Run()
    {
        try
        {
            string project = Directory.GetCurrentDirectory();
            if (!Directory.Exists(Path.Combine(project, "Tools", "Blender"))) project = Path.GetFullPath("../..");
            output = Path.Combine(project, "Art", "Reports", "IslandExpansion");
            Directory.CreateDirectory(output);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
            var pipeline=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/LastLandfall/Settings/PrototypePipeline.asset");
            GraphicsSettings.defaultRenderPipeline=pipeline; QualitySettings.renderPipeline=pipeline;
            host=new GameObject("Expansion runtime audit").AddComponent<BuildPlacementPrototype>();
            host.enabled=false;
            typeof(BuildPlacementPrototype).GetMethod("Awake",Private).Invoke(host,null);
            camera=(Camera)typeof(BuildPlacementPrototype).GetField("gameCamera",Private).GetValue(host);
            if (!(bool)typeof(BuildPlacementPrototype).GetField("usingExpandedArchipelago",Private).GetValue(host))
                throw new Exception("Expanded models were not selected by the production loader.");
            var grid=(IslandConstructionGrid)typeof(BuildPlacementPrototype).GetField("constructionGrid",Private).GetValue(host);
            if(grid.Surfaces.Length!=3) throw new Exception("Expected exactly three independently loaded terrain surfaces.");
            islandBounds=new Bounds[3];
            foreach(var surface in grid.Surfaces)
            {
                int index=surface.name.Contains("West")?1:surface.name.Contains("East")?2:0;
                islandBounds[index]=surface.bounds;
                Debug.Log("EXPANSION_BOUNDS "+surface.name+" "+surface.bounds);
            }
            var rows=new List<string>{"island,land_cells,building_cells,three_by_three_anchors,dock_anchors,coastal_water_cells"};
            int[] land=new int[3],build=new int[3],footprint=new int[3],dock=new int[3],water=new int[3],boom=new int[3];
            var definitions=(Array)typeof(BuildPlacementPrototype).GetField("Buildables",BindingFlags.Static|BindingFlags.NonPublic).GetValue(null);
            object boomDefinition=null,dockDefinition=null;
            foreach(object definition in definitions)
            {
                string asset=(string)definition.GetType().GetField("AssetName").GetValue(definition);
                if(asset=="DriftwoodCollectionBoom_DeepSeek")boomDefinition=definition;
                if(asset=="RescueDock")dockDefinition=definition;
            }
            var waterMethod=typeof(BuildPlacementPrototype).GetMethod("CanPlaceWater",Private);
            var dockMethod=typeof(BuildPlacementPrototype).GetMethod("TryFindDockDirection",Private);
            for(int z=0;z<grid.Depth;z++) for(int x=0;x<grid.Width;x++)
            {
                var cell=new Vector2Int(x,z);
                float px=grid.OriginX+x+.5f,pz=grid.OriginZ+z+.5f;
                Vector3 query=new Vector3(px,0,pz);
                int island=0;float best=float.PositiveInfinity;
                for(int k=0;k<3;k++)
                {
                    Bounds b=islandBounds[k];b.center=new Vector3(b.center.x,0,b.center.z);
                    float distance=b.SqrDistance(query);
                    if(distance<best){best=distance;island=k;}
                }
                var terrain=grid.GetTerrain(cell);
                if(terrain.HasLand) land[island]++;
                if(terrain.AllowsBuilding)build[island]++;
                if(grid.TryBuildingFootprint(cell,3,3,out _,out _)) footprint[island]++;
                if(grid.IsCoastalWaterCell(cell))
                {
                    water[island]++;
                    if(x%3==0&&z%3==0)
                    {
                        object[] args={cell,boomDefinition,null};
                        if((bool)waterMethod.Invoke(host,args))boom[island]++;
                    }
                }
                if(terrain.HasLand)
                {
                    object[] args={cell,Vector2Int.zero};
                    if((bool)dockMethod.Invoke(host,args))
                    {
                        dock[island]++;
                        var center=(Vector3)typeof(BuildPlacementPrototype).GetMethod("GetObjectCenter",Private)
                            .Invoke(host,new[]{(object)cell,dockDefinition});
                        if(Mathf.Abs(center.y+.92f)>.001f)throw new Exception("Dock root floats above the waterline.");
                    }
                }
            }
            for(int i=0;i<3;i++)
            {
                rows.Add(string.Join(",",new[]{"Main","West","East"}[i],land[i],build[i],footprint[i],dock[i],water[i]));
                if(footprint[i]<30)throw new Exception("Too few 3x3 construction footprints: "+i);
                if(dock[i]==0)throw new Exception("No valid dock connection: "+i);
                if(boom[i]==0)throw new Exception("No complete 9x3 near-shore water footprint: "+i);
                Debug.Log("EXPANSION_GRID "+rows.Last());
                Debug.Log("EXPANSION_WATER_FOOTPRINTS "+i+" "+boom[i]);
            }
            File.WriteAllLines(Path.Combine(output,"UnityConstructionAudit.csv"),rows);
            AuditBaseline();
            if(host.ConstructionGridRenderers.Length!=4)throw new Exception("Missing continuous water grid overlay.");
            foreach(var renderer in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
                foreach(var mat in renderer.sharedMaterials)
                    if(mat!=null && mat.shader!=null && ShaderUtil.ShaderHasError(mat.shader))
                    {
                        foreach(var message in ShaderUtil.GetShaderMessages(mat.shader))Debug.LogError(message.message);
                        throw new Exception("Shader compile error "+mat.shader.name);
                    }
            EditorApplication.update+=Tick;
        }
        catch(Exception e){Debug.LogException(e);EditorApplication.Exit(1);}
    }
    static void AuditBaseline()
    {
        var root=new GameObject("Baseline audit only").transform;
        root.rotation=Quaternion.Euler(0,180,0);
        var surfaces=new List<MeshCollider>();var satellites=new List<MeshCollider>();
        Bounds bounds=default;bool hasBounds=false;
        foreach(string file in new[]{"IslandReference_Gate25_Natural","BasinTwinIslands_Natural_v2"})
        {
            var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/LastLandfall/Resources/Models/Environment/"+file+".fbx");
            var instance=(GameObject)PrefabUtility.InstantiatePrefab(prefab,root);
            foreach(var renderer in instance.GetComponentsInChildren<Renderer>())renderer.enabled=false;
            foreach(var mesh in instance.GetComponentsInChildren<MeshFilter>())
            {
                if(!mesh.name.Contains("terrain source"))continue;
                var collider=mesh.gameObject.AddComponent<MeshCollider>();collider.sharedMesh=mesh.sharedMesh;
                surfaces.Add(collider);if(file.Contains("Twin"))satellites.Add(collider);
                var b=mesh.GetComponent<Renderer>().bounds;
                if(!hasBounds){bounds=b;hasBounds=true;}else bounds.Encapsulate(b);
            }
        }
        Physics.SyncTransforms();
        // Map coordinates are world-aligned, just like the production Play Space root.
        var map=new GameObject("Baseline grid space").transform;
        var grid=new IslandConstructionGrid(map,surfaces.ToArray(),bounds,-.92f,satellites.ToArray());
        var records=new List<string>{"island,building_cells,three_by_three_anchors"};
        int[] build=new int[3],footprint=new int[3];
        for(int z=0;z<grid.Depth;z++)for(int x=0;x<grid.Width;x++)
        {
            var cell=new Vector2Int(x,z);float pz=grid.OriginZ+z+.5f,px=grid.OriginX+x+.5f;
            int island=pz>24?(px<0?1:2):0;
            if(grid.GetTerrain(cell).AllowsBuilding)build[island]++;
            if(grid.TryBuildingFootprint(cell,3,3,out _,out _))footprint[island]++;
        }
        for(int i=0;i<3;i++)records.Add(string.Join(",",new[]{"Main","West","East"}[i],build[i],footprint[i]));
        File.WriteAllLines(Path.Combine(output,"UnityConstructionBaseline.csv"),records);
        UnityEngine.Object.DestroyImmediate(root.gameObject);UnityEngine.Object.DestroyImmediate(map.gameObject);
    }
    static void Render(string name,Vector3 focus,float size,float pitch)
    {
        camera.orthographic=true;camera.orthographicSize=size;
        camera.transform.rotation=Quaternion.Euler(pitch,350,0);
        camera.transform.position=focus-camera.transform.forward*250;
        camera.farClipPlane=800;
        var rt=new RenderTexture(1600,1000,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB);
        rt.Create();
        RenderPipeline.SubmitRenderRequest(camera,new UniversalRenderPipeline.SingleCameraRequest{destination=rt});
        var prev=RenderTexture.active;RenderTexture.active=rt;
        var image=new Texture2D(1600,1000,TextureFormat.RGB24,false);
        image.ReadPixels(new Rect(0,0,1600,1000),0,0);image.Apply();RenderTexture.active=prev;
        File.WriteAllBytes(Path.Combine(output,name+".png"),image.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(image);rt.Release();UnityEngine.Object.DestroyImmediate(rt);
    }
    static void Tick()
    {
        if(++frame<35)return;
        try
        {
            Bounds all=islandBounds[0];all.Encapsulate(islandBounds[1]);all.Encapsulate(islandBounds[2]);
            Render("Expanded_Archipelago",all.center,91,65);
            Render("Expanded_Main",islandBounds[0].center,53,52);
            Render("Expanded_West",islandBounds[1].center,32,58);
            Render("Expanded_East",islandBounds[2].center,32,58);
            typeof(BuildPlacementPrototype).GetField("selectedBuildableIndex",Private).SetValue(host,0);
            foreach(var r in host.ConstructionGridRenderers)r.enabled=true;
            Render("Expanded_ConstructionGrid",all.center,91,70);
            Debug.Log("EXPANSION_AUDIT_COMPLETE");EditorApplication.update-=Tick;EditorApplication.Exit(0);
        }
        catch(Exception e){Debug.LogException(e);EditorApplication.Exit(1);}
    }
}

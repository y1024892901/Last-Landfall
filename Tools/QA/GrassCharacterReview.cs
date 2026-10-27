using System;
using System.IO;
using System.Collections;
using System.Reflection;
using LastLandfall.Prototype;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class GrassCharacterReview
{
    const string Key="LastLandfall.GrassCharacterReview";
    static readonly BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
    static BuildPlacementPrototype host;
    static SurvivorCharacterController actor;
    static EditorWindow view;
    static int stage,frames;
    static double started,next;
    static float largestSwing;
    static bool stop;
    static readonly System.Collections.Generic.List<string> errors=new System.Collections.Generic.List<string>();
    static GrassCharacterReview()
    {
        EditorApplication.playModeStateChanged+=state=>
        {
            if(!SessionState.GetBool(Key,false))return;
            if(state==PlayModeStateChange.EnteredPlayMode)
            {
                Application.logMessageReceived+=Log;
                EditorApplication.update-=Tick;EditorApplication.update+=Tick;
                started=EditorApplication.timeSinceStartup;next=started+2;stage=0;
            }
            if(state==PlayModeStateChange.EnteredEditMode&&stop)
            {SessionState.SetBool(Key,false);EditorApplication.Exit(errors.Count==0?0:1);}
        };
    }
    static void Log(string message,string trace,LogType type)
    {
        if(type==LogType.Error||type==LogType.Exception||type==LogType.Assert)errors.Add(message);
    }
    static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
    public static void Run()
    {
        Directory.CreateDirectory("GrassCharacterReview");
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene(),"Assets/GrassCharacterReview.unity");
        view=EditorWindow.GetWindow(typeof(Editor).Assembly.GetType("UnityEditor.GameView"));
        view.position=new Rect(0,0,1600,1030);view.Focus();
        SessionState.SetBool(Key,true);EditorApplication.EnterPlaymode();
    }
    static void Tick()
    {
        try
        {
            if(view!=null){view.Repaint();EditorApplication.QueuePlayerLoopUpdate();}
            if(actor!=null)
            {
                var leg=(Transform)typeof(SurvivorCharacterController).GetField("leftLeg",Private).GetValue(actor);
                Quaternion rest=(Quaternion)typeof(SurvivorCharacterController).GetField("leftLegRest",Private).GetValue(actor);
                if(leg!=null)largestSwing=Mathf.Max(largestSwing,Quaternion.Angle(leg.localRotation,rest));
            }
            if(EditorApplication.timeSinceStartup<next)return;
            if(view==null)view=EditorWindow.GetWindow(typeof(Editor).Assembly.GetType("UnityEditor.GameView"));
            view.Repaint();EditorApplication.QueuePlayerLoopUpdate();
            next=EditorApplication.timeSinceStartup+1;
            if(stage==0)
            {
                host=UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();
                var menu=UnityEngine.Object.FindAnyObjectByType<MainMenuController>();
                Check(host!=null&&host.ConstructionGrid!=null&&menu!=null&&menu.IsInitialized,"Scene did not load.");
                menu.BeginGame(false);
                var survivors=UnityEngine.Object.FindObjectsByType<SurvivorCharacterController>(FindObjectsSortMode.None);
                Check(survivors.Length>=2,"Two initial crew members were not spawned.");
                foreach(var person in survivors)
                {
                    foreach(string field in new[]{"leftLeg","rightLeg","leftArm","rightArm","head"})
                    {
                        var pivot=(Transform)typeof(SurvivorCharacterController).GetField(field,Private).GetValue(person);
                        Check(pivot!=null&&pivot.childCount>0,"Missing articulated character joint: "+field);
                    }
                    var renderers=person.GetComponentsInChildren<Renderer>();
                    Check(renderers.Length>=15,"Character model lacks its visible parts.");
                    foreach(var renderer in renderers)foreach(var mat in renderer.sharedMaterials)
                        Check(mat!=null&&mat.shader!=null&&mat.shader.name=="Universal Render Pipeline/Lit","Character material is missing or unsupported.");
                    var bounds=renderers[0].bounds;foreach(var renderer in renderers)bounds.Encapsulate(renderer.bounds);
                    Check(bounds.size.y>1.4f&&bounds.size.y<2.1f,"Character scale is not human-sized: "+bounds.size.y);
                }
                actor=survivors[0];var grid=host.ConstructionGrid;
                Vector3 local=grid.Root.InverseTransformPoint(actor.transform.position);
                bool found=false;
                foreach(var offset in new[]{new Vector2(.8f,0),new Vector2(-.8f,0),new Vector2(0,.8f),new Vector2(0,-.8f)})
                {
                    if(!grid.TrySample(local.x+offset.x,local.z+offset.y,out Vector3 p,out Vector3 n)||n.y<.78f)continue;
                    typeof(SurvivorCharacterController).GetField("currentTarget",Private).SetValue(actor,grid.Root.TransformPoint(p));
                    typeof(SurvivorCharacterController).GetField("isWalking",Private).SetValue(actor,true);found=true;break;
                }
                Check(found,"No safe walking target found.");
                var grass=host.GetComponent<IslandGrassCover>();
                Check(grass!=null,"Grass cover missing.");
                var freshwater=(System.Collections.Generic.List<MeshCollider>)typeof(IslandGrassCover).GetField("freshWater",Private).GetValue(grass);
                Check(freshwater.Count>=2,"Pond and stream exclusion surfaces were not loaded.");
                var pond=freshwater.Find(c=>c.name.Contains("Pond"));
                Check(pond!=null,"Pond collider was not loaded.");
                var pondCenter=pond.bounds.center;
                var pondRay=new Ray(new Vector3(pondCenter.x,grid.LocalBounds.max.y+8,pondCenter.z),Vector3.down);
                Check(pond.Raycast(pondRay,out RaycastHit pondHit,100),"Could not sample the pond surface.");
                Vector3 pondLocal=grid.Root.InverseTransformPoint(pondHit.point);
                Check(grid.TrySample(pondLocal.x,pondLocal.z,out Vector3 pondFloor,out _)&&grass.IsFreshWater(pondFloor),"Pond did not exclude grass.");
                object[] waterArgs={grid.Root.TransformPoint(pondFloor),null};
                Check(!(bool)typeof(SurvivorCharacterController).GetMethod("TryGround",Private).Invoke(actor,waterArgs),"Survivor can wander through the pond.");
                foreach(var renderer in grid.Root.GetComponentsInChildren<Renderer>())
                {
                    string name=renderer.name.ToLowerInvariant();
                    if(!name.StartsWith("grounded detail |") &&
                        (name.StartsWith("grass_")||name.Contains("_grass_")||name.EndsWith("_grass")))
                        Check(!renderer.enabled,"Oversized legacy grass is still visible: "+renderer.name);
                }
                var mesh=(Mesh)typeof(IslandGrassCover).GetField("mesh",Private).GetValue(grass);
                Check(mesh!=null&&mesh.vertexCount==90&&mesh.triangles.Length==162,"Fine dense grass mesh missing.");
                Shader shader=Resources.Load<Shader>("Shaders/GrassBlades");
                Check(shader!=null&&!ShaderUtil.ShaderHasError(shader),"Grass shader failed compilation.");
                var grassMaterial=(Material)typeof(IslandGrassCover).GetField("material",Private).GetValue(grass);
                var camera=Camera.main;
                camera.orthographicSize=30f;grass.SendMessage("LateUpdate");
                Check(grassMaterial.GetFloat("_GrassVisibility")<.001f,"Distant grass detail did not fade out.");
                camera.orthographicSize=21f;grass.SendMessage("LateUpdate");
                float midFade=grassMaterial.GetFloat("_GrassVisibility");
                Check(midFade>.05f&&midFade<.95f,"Grass zoom transition is not gradual.");
                camera.orthographicSize=3f;grass.SendMessage("LateUpdate");
                Check(grassMaterial.GetFloat("_GrassVisibility")>.99f,"Close grass detail did not return.");
                typeof(BuildPlacementPrototype).GetField("cameraOrbitTarget",Private).SetValue(host,actor.transform.position+Vector3.up*.8f);
                typeof(BuildPlacementPrototype).GetField("cameraOrthographicSize",Private).SetValue(host,3f);
                typeof(BuildPlacementPrototype).GetField("cameraOrbitPitchDegrees",Private).SetValue(host,35f);
                typeof(BuildPlacementPrototype).GetMethod("ClampCameraView",Private).Invoke(host,null);
                typeof(BuildPlacementPrototype).GetMethod("UpdateCameraPose",Private).Invoke(host,null);
                stage=1;next=EditorApplication.timeSinceStartup+4;return;
            }
            if(stage==1)
            {
                var grid=host.ConstructionGrid;
                Vector3 local=grid.Root.InverseTransformPoint(actor.transform.position);
                Check(grid.TrySample(local.x,local.z,out Vector3 point,out _)&&Mathf.Abs(local.y-point.y)<.12f,"Walking character lost ground contact.");
                Check(largestSwing>3,"The articulated legs did not animate.");
                var grass=host.GetComponent<IslandGrassCover>();
                var chunks=(IDictionary)typeof(IslandGrassCover).GetField("chunks",Private).GetValue(grass);
                Check(chunks.Count>0,"No grass instances were generated.");
                var targetCell=grid.PointToCell(local);
                var key=new Vector2Int(targetCell.x/8,targetCell.y/8);
                // Wait for generation to reach the initial crew's visible island area.
                if(!chunks.Contains(key)&&EditorApplication.timeSinceStartup-started<35){next=EditorApplication.timeSinceStartup+1;return;}
                Check(chunks.Contains(key),"Grass did not reach the starting area within 35 seconds.");
                int grassCells=0,tuftCount=0;
                foreach(DictionaryEntry entry in chunks)
                {
                    var cells=(IDictionary)entry.Value.GetType().GetField("cells",BindingFlags.Instance|BindingFlags.Public).GetValue(entry.Value);
                    foreach(DictionaryEntry cell in cells){grassCells++;tuftCount+=((IList)cell.Value).Count;}
                }
                float density=grassCells>0?(float)tuftCount/grassCells:0;
                Check(density>=2.4f,"The grass is too sparse: "+density+" tufts per occupied cell.");
                int visible=0,visibleChunks=0;
                var planes=GeometryUtility.CalculateFrustumPlanes(Camera.main);
                foreach(DictionaryEntry entry in chunks)
                {
                    var renderer=(MeshRenderer)entry.Value.GetType().GetField("renderer",BindingFlags.Instance|BindingFlags.Public).GetValue(entry.Value);
                    var matrices=(Matrix4x4[])entry.Value.GetType().GetField("local",BindingFlags.Instance|BindingFlags.Public).GetValue(entry.Value);
                    if(renderer!=null&&renderer.enabled&&GeometryUtility.TestPlanesAABB(planes,renderer.bounds))
                    {visibleChunks++;visible+=matrices.Length;}
                }
                Debug.Log("GRASS_VISIBLE instances="+visible+" chunks="+visibleChunks+" camera="+Camera.main.orthographicSize);
                Check(visible>0,"No generated grass is being drawn in the visible camera frustum.");
                int projected=0;Vector3 example=Vector3.zero;
                foreach(DictionaryEntry entry in chunks)
                {
                    var matrices=(Matrix4x4[])entry.Value.GetType().GetField("local",BindingFlags.Instance|BindingFlags.Public).GetValue(entry.Value);
                    foreach(var matrix in matrices)
                    {
                        Vector3 world=grid.Root.TransformPoint((Vector3)matrix.GetColumn(3));
                        Vector3 viewport=Camera.main.WorldToViewportPoint(world);
                        if(viewport.z>0&&viewport.x>.05f&&viewport.x<.95f&&viewport.y>.05f&&viewport.y<.95f)
                        {projected++;example=world;}
                    }
                }
                Debug.Log("GRASS_PROJECTED count="+projected+" example="+example);
                Check(projected>0,"No grass tufts project into the close-up viewport.");
                Capture();
                AuditPlacementAndResources(grass,chunks);
                File.WriteAllText("GrassCharacterReview/results.txt",$"passed; grass chunks={chunks.Count}; average tufts/cell={density:F2}; blades/tuft=18; human models=2; peak leg swing={largestSwing:F1}; grounded=true\n");
                Check(errors.Count==0,string.Join("\n",errors));
                Debug.Log("GRASS_CHARACTER_REVIEW_COMPLETE");EditorApplication.update-=Tick;Application.logMessageReceived-=Log;
                stop=true;EditorApplication.ExitPlaymode();stage=2;
            }
        }
        catch(Exception e)
        {
            File.WriteAllText("GrassCharacterReview/error.txt",e+"\n"+string.Join("\n",errors));
            Debug.LogException(e);SessionState.SetBool(Key,false);EditorApplication.Exit(1);
        }
    }
    static void AuditPlacementAndResources(IslandGrassCover grass,IDictionary chunks)
    {
        var grid=host.ConstructionGrid;Vector2Int chosen=default;bool found=false;
        foreach(DictionaryEntry entry in chunks)
        {
            var cells=(IDictionary)entry.Value.GetType().GetField("cells",BindingFlags.Instance|BindingFlags.Public).GetValue(entry.Value);
            foreach(DictionaryEntry cell in cells)
            {
                var anchor=(Vector2Int)cell.Key;
                if(grid.TryBuildingFootprint(anchor,2,2,out _,out _)){chosen=anchor;found=true;break;}
            }
            if(found)break;
        }
        Check(found,"No grass-covered 2x2 site is buildable.");
        var resources=ColonyResourceManager.Instance;Check(resources!=null,"Resource manager missing.");
        float before=resources.Wood;
        typeof(BuildPlacementPrototype).GetMethod("SelectBuildable",Private).Invoke(host,new object[]{12});
        typeof(BuildPlacementPrototype).GetMethod("TryPlaceSelected",Private).Invoke(host,new object[]{chosen});
        Check(Mathf.Abs(resources.Wood-(before-15))<.001f,"Building did not spend the visible wood stockpile.");
        var coord=new Vector2Int(chosen.x/8,chosen.y/8);var chunk=chunks[coord];
        var after=(IDictionary)chunk.GetType().GetField("cells",BindingFlags.Instance|BindingFlags.Public).GetValue(chunk);
        Check(!after.Contains(chosen),"Grass was not cleared beneath a building.");
        var last=host.PlacedBuildings[host.PlacedBuildings.Count-1];host.DemolishBuilding(last);
        Check(Mathf.Abs(resources.Wood-(before-15+8))<.001f,"Demolition refund did not reach the visible stockpile.");
        typeof(BuildPlacementPrototype).GetField("researchLevel",Private).SetValue(host,1);
        var lighthouse=host.GetComponent<LighthouseSite>();float lighthouseBefore=resources.Wood;
        lighthouse.SetPreviewMode(false);
        Check(lighthouse.TryBuildNextStage()&&Mathf.Abs(resources.Wood-(lighthouseBefore-40))<.001f,
            "Lighthouse stage did not spend the visible wood stockpile.");
    }
    static void Capture()
    {
        RenderTexture target=null;
        for(Type t=view.GetType();t!=null&&target==null;t=t.BaseType)
            foreach(var f in t.GetFields(Private|BindingFlags.Public|BindingFlags.DeclaredOnly))
                if(typeof(RenderTexture).IsAssignableFrom(f.FieldType))
                {var texture=f.GetValue(view) as RenderTexture;if(texture!=null&&texture.IsCreated()){target=texture;break;}}
        Check(target!=null,"Game View target unavailable.");
        var prior=RenderTexture.active;RenderTexture.active=target;
        var image=new Texture2D(target.width,target.height,TextureFormat.RGB24,false);
        image.ReadPixels(new Rect(0,0,target.width,target.height),0,0);image.Apply();RenderTexture.active=prior;
        if(SystemInfo.graphicsUVStartsAtTop)
        {
            var pixels=image.GetPixels32();int w=image.width,h=image.height;
            for(int y=0;y<h/2;y++)for(int x=0;x<w;x++)
            {int a=y*w+x,b=(h-1-y)*w+x;Color32 c=pixels[a];pixels[a]=pixels[b];pixels[b]=c;}
            image.SetPixels32(pixels);image.Apply();
        }
        File.WriteAllBytes("GrassCharacterReview/game.png",image.EncodeToPNG());UnityEngine.Object.DestroyImmediate(image);
    }
}

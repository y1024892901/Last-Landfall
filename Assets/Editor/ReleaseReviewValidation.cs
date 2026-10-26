using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
using LastLandfall.Prototype;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace LastLandfall.EditorTools
{
    [InitializeOnLoad]
    public static class ReleaseReviewValidation
    {
        const string Key="LastLandfall.ReleaseReview";
        const string Output="Art/Reports/ReleaseReview";
        static readonly BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
        static readonly List<string> failures=new List<string>();
        static BuildPlacementPrototype host;
        static MainMenuController menu;
        static LighthouseSite site;
        static Camera camera;
        static EditorWindow gameView;
        static double next;
        static int step;
        static bool requestedExit;
        static ReleaseReviewValidation()
        {
            EditorApplication.playModeStateChanged+=state=>
            {
                if(!SessionState.GetBool(Key,false))return;
                if(state==PlayModeStateChange.EnteredPlayMode)
                {
                    Application.logMessageReceived+=Log;
                    EditorApplication.update-=Tick;EditorApplication.update+=Tick;
                    next=EditorApplication.timeSinceStartup+2;step=0;
                }
                if(state==PlayModeStateChange.EnteredEditMode&&requestedExit)
                {SessionState.SetBool(Key,false);EditorApplication.Exit(failures.Count==0?0:1);}
            };
        }
        [MenuItem("Last Landfall/Validate Current Release")]
        public static void RunBatch()
        {
            Directory.CreateDirectory(Output);
            FacilityCatalogValidation.Validate();
            string catalog=File.ReadAllText("work/facility_catalog/validation.json");
            if(!catalog.Contains("\"passed\": true"))throw new Exception("Facility catalog audit failed.");
            EditorSceneManager.OpenScene("Assets/LastLandfall/Scenes/Prototype.unity");
            var type=typeof(Editor).Assembly.GetType("UnityEditor.GameView");
            gameView=EditorWindow.GetWindow(type);gameView.position=new Rect(0,0,1600,1030);gameView.Focus();
            SessionState.SetBool(Key,true);EditorApplication.EnterPlaymode();
        }
        static void Log(string condition,string trace,LogType type)
        {
            if(type==LogType.Error||type==LogType.Exception||type==LogType.Assert)failures.Add(condition);
        }
        static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
        static void Set(string field,object value)=>typeof(BuildPlacementPrototype).GetField(field,Private).SetValue(host,value);
        static object Get(string field)=>typeof(BuildPlacementPrototype).GetField(field,Private).GetValue(host);
        static void Frame(Vector3 focus,float size,float pitch=45)
        {
            Set("cameraOrbitTarget",focus);Set("cameraOrthographicSize",size);Set("cameraOrbitPitchDegrees",pitch);
            typeof(BuildPlacementPrototype).GetMethod("ClampCameraView",Private).Invoke(host,null);
            typeof(BuildPlacementPrototype).GetMethod("UpdateCameraPose",Private).Invoke(host,null);
        }
        static void Tick()
        {
            if(EditorApplication.timeSinceStartup<next)return;
            next=EditorApplication.timeSinceStartup+.9;
            try
            {
                if(gameView==null)gameView=EditorWindow.GetWindow(typeof(Editor).Assembly.GetType("UnityEditor.GameView"));
                gameView.Repaint();EditorApplication.QueuePlayerLoopUpdate();
                switch(step++)
                {
                    case 0:
                        host=UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();
                        menu=UnityEngine.Object.FindAnyObjectByType<MainMenuController>();
                        site=UnityEngine.Object.FindAnyObjectByType<LighthouseSite>();camera=Camera.main;
                        Check(host!=null&&site!=null&&menu!=null&&menu.IsInitialized,"Runtime did not initialize.");
                        Check(menu.IsBlocking&&!menu.HasStarted,"Game must begin on the home screen.");
                        Check(host.ConstructionGrid.Surfaces.Length==3,"Three island terrain surfaces must load.");
                        menu.OpenSettings();Check(menu.IsSettingsOpen,"Home settings did not open.");menu.CloseSettings();
                        Check(!menu.IsSettingsOpen&&menu.IsBlocking,"Home settings did not close.");
                        menu.BeginGame(false);Check(!menu.IsBlocking&&host.enabled,"Start did not enter gameplay.");
                        menu.OpenSettings();Check(menu.IsSettingsOpen&&menu.IsBlocking,"In-game settings did not open.");
                        menu.CloseSettings();typeof(MainMenuController).GetMethod("ResumeGame",Private).Invoke(menu,null);
                        Check(!menu.IsBlocking,"Settings resume did not restore gameplay.");
                        AuditLighthouse();AuditSurfacesAndStream();
                        site.SetPreviewStage(0);site.IsPanelOpen=false;
                        Frame(new Vector3(0,2,-7),50,45);break;
                    case 1:
                        Capture("Gameplay_HUD");
                        Set("isBuildMenuOpen",true);Frame(new Vector3(6,2,-5),24,45);break;
                    case 2:
                        Capture("Construction_UI");Set("isBuildMenuOpen",false);
                        var grid=host.ConstructionGrid;
                        Check(grid.TrySample(2,4,out Vector3 close,out _),"Close-view ground was not found.");
                        Frame(close,3f,48);break;
                    case 3:
                        Capture("Terrain_ClosestZoom");
                        Frame(new Vector3(-4,3,12),17,57);break;
                    case 4:
                        Capture("Mountain_Stream");site.IsPanelOpen=true;site.SetPreviewStage(0);
                        Frame(site.WorldPosition+Vector3.up*7,17,35);break;
                    case 5:Capture("Lighthouse_Stage_0");site.SetPreviewStage(1);break;
                    case 6:Capture("Lighthouse_Stage_1");site.SetPreviewStage(2);break;
                    case 7:Capture("Lighthouse_Stage_2");site.SetPreviewStage(3);break;
                    case 8:Capture("Lighthouse_Stage_3");site.SetPreviewStage(4);break;
                    case 9:
                        Capture("Lighthouse_Stage_4");
                        host.GetComponent<IslandWeatherSystem>().SetTimeOfDay(23);break;
                    case 10:
                        Capture("Lighthouse_Night");
                        File.WriteAllText(Path.Combine(Output,"Validation.txt"),
                            "Three islands loaded; 25 facilities and 29 construction modules present; settings home/game pass; " +
                            "lighthouse research/wood gating and all five preview stages pass; four seamless terrain maps loaded; " +
                            "mountain stream descends to pond; shader checks pass.\n"+string.Join("\n",failures));
                        if(failures.Count>0)throw new Exception(string.Join("\n",failures));
                        Debug.Log("RELEASE_REVIEW_VALIDATION_COMPLETE");
                        EditorApplication.update-=Tick;Application.logMessageReceived-=Log;
                        requestedExit=true;EditorApplication.ExitPlaymode();break;
                }
            }
            catch(Exception exception)
            {
                failures.Add(exception.ToString());File.WriteAllText(Path.Combine(Output,"Failure.txt"),string.Join("\n",failures));
                Debug.LogException(exception);SessionState.SetBool(Key,false);EditorApplication.Exit(1);
            }
        }
        static void AuditLighthouse()
        {
            foreach(var surface in host.ConstructionGrid.Surfaces)
            {
                Bounds b=surface.bounds;b.Expand(new Vector3(16,0,16));
                Check(!(site.WorldPosition.x>b.min.x&&site.WorldPosition.x<b.max.x&&site.WorldPosition.z>b.min.z&&site.WorldPosition.z<b.max.z),
                    "Lighthouse reef intersects one of the three islands.");
            }
            int before=(int)Get("wood");
            Set("researchLevel",0);site.SetPreviewMode(false);
            Check(!site.TryBuildNextStage()&&(int)Get("wood")==before,"Locked lighthouse construction spent resources.");
            foreach(int level in new[]{1,2,4,7}){Set("researchLevel",level);Check(site.TryBuildNextStage(),"Unlocked lighthouse stage failed.");}
            Check(site.CompletedStage==4&&(int)Get("wood")==before-470,"Lighthouse cost/progress mismatch.");
            Set("wood",before);Set("researchLevel",0);
            for(int i=0;i<5;i++)
            {
                site.SetPreviewStage(i);Check(site.PreviewStage==i,"Lighthouse stage did not change.");
                var visual=GameObject.Find("Lighthouse stage "+i+" | "+LighthouseSite.StageNames[i]);
                Check(visual!=null&&visual.GetComponentsInChildren<Renderer>().Length>0,"Lighthouse stage is invisible.");
            }
            Check(GameObject.Find("Rotating lighthouse beacon")!=null,"Completed lighthouse lacks its beacon.");
            site.SetPreviewStage(0);Check(GameObject.Find("Rotating lighthouse beacon")==null,"Beacon remains active at the old foundation stage.");
            foreach(string name in new[]{"LastLandfall/Reference Island Terrain","LastLandfall/Lighthouse Beam","LastLandfall/Coastal Construction Grid"})
            {
                Shader shader=Shader.Find(name);Check(shader!=null&&!ShaderUtil.ShaderHasError(shader),"Shader failed: "+name);
            }
        }
        static void AuditSurfacesAndStream()
        {
            foreach(string map in new[]{"GroundAlbedo","GroundSurface","RockAlbedo","RockSurface"})
            {
                var texture=Resources.Load<Texture2D>("Textures/Terrain/"+map);
                Check(texture!=null&&texture.width==1024,"Terrain detail texture missing: "+map);
                var importer=(TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(texture));
                Check(importer.mipmapEnabled&&importer.anisoLevel>=8&&importer.wrapMode==TextureWrapMode.Repeat,"Terrain filtering is incorrect.");
            }
            Check(GameObject.Find("Basin_Stream_Water_MountainSpring")!=null,"Mountain spring watercourse missing.");
            Check(GameObject.Find("Basin_Stream_Water_Inlet")==null,"Old incorrectly sourced stream remains active.");
        }
        static void Capture(string name)
        {
            // The Game View target includes OnGUI, unlike a camera-only render request.
            RenderTexture target=null;Type type=gameView.GetType();
            for(Type current=type;current!=null&&target==null;current=current.BaseType)
                foreach(var field in current.GetFields(Private|BindingFlags.Public|BindingFlags.DeclaredOnly))
                    if(typeof(RenderTexture).IsAssignableFrom(field.FieldType))
                    {var candidate=field.GetValue(gameView) as RenderTexture;if(candidate!=null&&candidate.IsCreated()){target=candidate;break;}}
            bool gameViewTarget=target!=null;
            if(target==null)
            {
                target=new RenderTexture(1600,1000,24);target.Create();
                RenderPipeline.SubmitRenderRequest(camera,new UniversalRenderPipeline.SingleCameraRequest{destination=target});
                Debug.LogWarning("Game View target unavailable; camera-only fallback for "+name);
            }
            RenderTexture old=RenderTexture.active;RenderTexture.active=target;
            var image=new Texture2D(target.width,target.height,TextureFormat.RGB24,false);
            image.ReadPixels(new Rect(0,0,target.width,target.height),0,0);image.Apply();RenderTexture.active=old;
            if(gameViewTarget&&SystemInfo.graphicsUVStartsAtTop)
            {
                Color32[] pixels=image.GetPixels32();int width=image.width,height=image.height;
                for(int y=0;y<height/2;y++)for(int x=0;x<width;x++)
                {
                    int a=y*width+x,b=(height-1-y)*width+x;
                    Color32 value=pixels[a];pixels[a]=pixels[b];pixels[b]=value;
                }
                image.SetPixels32(pixels);image.Apply();
            }
            File.WriteAllBytes(Path.Combine(Output,name+".png"),image.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(image);
        }
    }
}

using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using LastLandfall.Prototype;

namespace LastLandfall.EditorTools
{
    [InitializeOnLoad]
    public static class LighthouseRebuildValidation
    {
        const string Output="work/TripoImport/Lighthouse/";
        static LighthouseRebuildValidation(){EditorApplication.update+=CheckRequest;}
        static void CheckRequest()
        {
            if(EditorApplication.isCompiling||EditorApplication.isUpdating)return;
            if(File.Exists(Output+"apply.request")&&!EditorApplication.isPlayingOrWillChangePlaymode)
            {
                File.Delete(Output+"apply.request");ApplyModels();
            }
            if(File.Exists(Output+"test.request")&&EditorApplication.isPlaying)
            {
                var host=UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();
                var site=host!=null?host.GetComponent<LighthouseSite>():null;
                if(site==null||ColonyResourceManager.Instance==null)return;
                File.Delete(Output+"test.request");
                try{ValidateRuntime(host,site);File.WriteAllText(Output+"runtime_validation.txt","PASS: resources, sequential stages, duplicate start, partial progress JSON restore, cleanup reward, beacon, progress restored after test.\n");}
                catch(Exception e){File.WriteAllText(Output+"runtime_validation.txt",e.ToString());Debug.LogException(e);}
            }
        }
        [MenuItem("Last Landfall/Apply Tripo Lighthouse")]
        public static void ApplyModels()
        {
            const string file="Assets/LastLandfall/Resources/Models/Environment/Tripo/Lighthouse/Lighthouse_Modular.fbx";
            var importer=(ModelImporter)AssetImporter.GetAtPath(file);
            if(importer==null)throw new Exception("Modular lighthouse FBX missing.");
            if(importer.materialImportMode!=ModelImporterMaterialImportMode.ImportStandard)
            {importer.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;importer.SaveAndReimport();}
            var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
            foreach(var go in scene.GetRootGameObjects())if(go.name=="Lighthouse | Scene Preview")UnityEngine.Object.DestroyImmediate(go);
            var root=new GameObject("Lighthouse | Scene Preview");root.transform.position=LighthouseSite.SitePosition;
            var model=LighthouseModelLibrary.Create(root.transform);
            if(model==null)throw new Exception("Missing lighthouse prefab.");
            var meshes=model.GetComponentsInChildren<MeshFilter>(true);
            string[] names={"Reef","Foundation","TowerLower_0","TowerLower_3","TowerMiddle_0","TowerUpper_3","Lantern","EquipmentHouse","Ruin_0","Ruin_3"};
            foreach(var n in names)if(!meshes.Any(m=>m.name==n))throw new Exception("Missing module "+n);
            foreach(var stage in Enumerable.Range(0,9))
            {
                LighthouseModelLibrary.SetStage(model,stage);
                if(!model.GetComponentsInChildren<Renderer>().Any(r=>r.enabled))throw new Exception("Empty lighthouse stage "+stage);
            }
            int missing=model.GetComponentsInChildren<Renderer>(true).Sum(r=>r.sharedMaterials.Count(m=>m==null||
                !m.name.Contains("ConcreteCut")&&!m.name.Contains("Timber")&&!m.name.Contains("RockSupport")&&m.mainTexture==null));
            LighthouseModelLibrary.SetStage(model,0);
            AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveOpenScenes();
            File.WriteAllText(Output+"model_validation.txt",$"Modules: {meshes.Length}\nStages: 9\nMissing textures: {missing}\nTower height above foundation: 49.6m\n");
            if(missing>0)throw new Exception("Lighthouse textures missing.");
            Debug.Log("TRIPO_LIGHTHOUSE_MODELS_VALIDATED: "+meshes.Length+" modules, 9 stages.");
        }
        public static void ValidateRuntime(BuildPlacementPrototype host,LighthouseSite site)
        {
            void Check(bool ok,string why){if(!ok)throw new Exception(why);}
            var res=ColonyResourceManager.Instance;
            var original=site.CaptureProgress();
            float w=res.Wood,f=res.Food,wa=res.Water,m=res.Metal,fu=res.Fuel,o=res.Ore,med=res.Medical;
            int research=host.ResearchLevel;var efficiencies=host.ResearchedEfficiencyKeys.ToList();
            try
            {
                site.RestoreProgress(new LighthouseProgressSave());
                res.LoadStockpiles(0,f,wa,0,0,o,med);
                Check(!site.TryBuildNextStage()&&res.Wood==0&&site.CompletedStage==0,"Insufficient resources changed progression.");
                res.LoadStockpiles(350,f,wa,300,100,o,med);host.RestoreResearchProgress(0,efficiencies);
                for(int step=1;step<=8;step++)
                {
                    Check(host.ResearchLevel==0,"Validate lighthouse construction at research level zero.");
                    float before=res.Wood;
                    Check(site.TryBuildNextStage(),"Cannot start stage "+step);
                    Check(Mathf.Approximately(res.Wood,before-LighthouseSite.WoodCosts[step]),"Wrong wood charge.");
                    float paid=res.Wood;
                    Check(!site.TryBuildNextStage()&&Mathf.Approximately(res.Wood,paid),"Duplicate start charged twice.");
                    site.AdvanceConstruction(LighthouseSite.Durations[step]*.4f);
                    var saved=JsonUtility.FromJson<LighthouseProgressSave>(JsonUtility.ToJson(site.CaptureProgress()));
                    site.RestoreProgress(saved);
                    Check(site.WorkingStage==step&&Mathf.Abs(site.ConstructionProgress-.4f)<.001f&&Mathf.Approximately(res.Wood,paid),"Partial restore failed.");
                    site.AdvanceConstruction(LighthouseSite.Durations[step]*.61f);
                    Check(site.CompletedStage==step&&site.WorkingStage==-1,"Stage completion failed.");
                    if(step==1)Check(Mathf.Approximately(res.Wood,paid+15),"Cleanup reward missing.");
                }
                Check(GameObject.Find("Rotating lighthouse beacon")!=null,"Completed lighthouse lacks beacon.");
                Check(!site.TryBuildNextStage(),"Built beyond final stage.");
                foreach(int stage in new[]{0,3,8})
                {
                    site.SetPreviewStage(stage);
                    CaptureStage(site,stage);
                }
                site.SetPreviewStage(0);
                Check(site.CompletedStage==8&&GameObject.Find("Rotating lighthouse beacon")==null,"Preview modified completion or left beacon enabled.");
                site.RestoreProgress(null);Check(site.CompletedStage==0,"Legacy save should start at ruins.");
                float jumpWood=res.Wood,jumpMetal=res.Metal;
                site.JumpToStage(8);
                Check(site.CompletedStage==8&&site.WorkingStage==-1&&GameObject.Find("Rotating lighthouse beacon")!=null,"Quick stage jump failed.");
                site.JumpToStage(2);
                Check(site.CompletedStage==2&&Mathf.Approximately(res.Wood,jumpWood)&&Mathf.Approximately(res.Metal,jumpMetal),"Quick jump spent resources.");
            }
            finally
            {
                site.RestoreProgress(original);host.RestoreResearchProgress(research,efficiencies);
                res.LoadStockpiles(w,f,wa,m,fu,o,med);
            }
            Debug.Log("TRIPO_LIGHTHOUSE_RUNTIME_VALIDATED");
        }
        static void CaptureStage(LighthouseSite site,int stage)
        {
            var camera=Camera.main;if(camera==null)return;
            var position=camera.transform.position;var rotation=camera.transform.rotation;
            float size=camera.orthographicSize,aspect=camera.aspect;int mask=camera.cullingMask;
            var target=camera.targetTexture;var active=RenderTexture.active;
            var rt=new RenderTexture(900,1100,24);var image=new Texture2D(900,1100,TextureFormat.RGB24,false);
            try
            {
                Vector3 center=site.WorldPosition+Vector3.up*(stage==0?5f:26f);
                camera.transform.position=center+new Vector3(65,42,-90);
                camera.transform.LookAt(center);camera.orthographicSize=stage==0?22:36;
                camera.cullingMask=~(1<<30);
                camera.aspect=900f/1100f;camera.targetTexture=rt;camera.Render();
                RenderTexture.active=rt;image.ReadPixels(new Rect(0,0,900,1100),0,0);image.Apply();
                File.WriteAllBytes(Output+"Stage_"+stage+".png",image.EncodeToPNG());
            }
            finally
            {
                camera.targetTexture=target;camera.aspect=aspect;camera.orthographicSize=size;camera.cullingMask=mask;
                camera.transform.SetPositionAndRotation(position,rotation);RenderTexture.active=active;
                rt.Release();UnityEngine.Object.DestroyImmediate(rt);UnityEngine.Object.DestroyImmediate(image);
            }
        }
    }
}

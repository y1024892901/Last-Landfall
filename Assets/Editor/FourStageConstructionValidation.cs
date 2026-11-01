using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using LastLandfall.Prototype;
[InitializeOnLoad]
public static class FourStageConstructionValidation
{
    [Serializable] sealed class Catalog { public BuildingConstructionCatalog.Entry[] entries; }
    static FourStageConstructionValidation() { EditorApplication.delayCall += Run; }
    static void Run()
    {
        const string request="work/four-stage.request";
        if(!File.Exists(request) || EditorApplication.isPlayingOrWillChangePlaymode) return;
        File.Delete(request);
        GameObject host=null;
        try
        {
            var shader=Resources.Load<Shader>("Shaders/ConstructionReveal");
            if(shader==null || !shader.isSupported) throw new Exception("Reveal shader unsupported");
            host=new GameObject("Construction test");
            host.transform.position=new Vector3(10000,10000,10000);
            var model=UnityEngine.Object.Instantiate(Resources.Load<GameObject>("Models/Buildings/WoodShelter"));
            model.transform.SetParent(host.transform,false);
            model.transform.localPosition=Vector3.up;
            model.transform.localScale=new Vector3(2,2,2);
            if(!BuildingConstructionController.TryBegin(host,"WoodShelter",model,null,0)) throw new Exception("TryBegin failed");
            host.transform.position=new Vector3(10000,10000,10000);
            var c=host.GetComponent<BuildingConstructionController>();
            c.SetAutomaticProgress(false);
            float[] progress={0,.3f,.75f,1};
            string[] phases={"地基准备","结构搭建","主体完善","完工"};
            for(int i=0;i<4;i++)
            {
                c.SetProgress(progress[i]);
                var cameraObject=new GameObject("Stage preview camera");
                var camera=cameraObject.AddComponent<Camera>();
                camera.transform.position=host.transform.position+new Vector3(6,5,-7);
                camera.transform.LookAt(host.transform.position+Vector3.up);
                camera.clearFlags=CameraClearFlags.SolidColor; camera.backgroundColor=new Color(.12f,.16f,.2f);
                camera.orthographic=true; camera.orthographicSize=4;
                var target=new RenderTexture(512,512,24); camera.targetTexture=target; camera.Render();
                var previous=RenderTexture.active; RenderTexture.active=target;
                var image=new Texture2D(512,512,TextureFormat.RGB24,false); image.ReadPixels(new Rect(0,0,512,512),0,0); image.Apply();
                File.WriteAllBytes("work/construction-stage-"+i+".png",image.EncodeToPNG());
                RenderTexture.active=previous; camera.targetTexture=null;
                UnityEngine.Object.DestroyImmediate(image); UnityEngine.Object.DestroyImmediate(target); UnityEngine.Object.DestroyImmediate(cameraObject);
                if(c.CurrentPhaseName!=phases[i]) throw new Exception("Phase mismatch "+c.CurrentPhaseName);
                if(model.activeSelf!=(i==3)) throw new Exception("Final model visibility mismatch");
                if(i<3 && host.GetComponentInChildren<FourStageConstructionVisual>()==null) throw new Exception("Missing staged visual");
            }
            c.SetProgress(.4f);
            if(model.activeSelf || c.IsComplete) throw new Exception("Saved/rewound progress failed");
            foreach(var message in ShaderUtil.GetShaderMessages(shader))
                if(message.severity.ToString()=="Error") throw new Exception(message.message);
            int validated=0;
            var catalog=JsonUtility.FromJson<Catalog>(Resources.Load<TextAsset>("Construction/Catalog").text);
            foreach(var entry in catalog.entries)
            {
                if(entry.key.StartsWith("DirtRoad") || entry.key.StartsWith("Lighthouse")) continue;
                var asset=Resources.Load<GameObject>(entry.finalResource);
                var instance=UnityEngine.Object.Instantiate(asset);
                var jobHost=new GameObject("Catalog construction validation");
                instance.transform.SetParent(jobHost.transform,false);
                try
                {
                    if(!BuildingConstructionController.TryBegin(jobHost,entry.key,instance,null,.3f)) throw new Exception("Catalog entry failed: "+entry.key);
                    var job=jobHost.GetComponent<BuildingConstructionController>();
                    job.SetAutomaticProgress(false);
                    if(job.CurrentPhaseName!="结构搭建") throw new Exception("Catalog phase failed: "+entry.key);
                    job.SetProgress(1);
                    if(!instance.activeSelf) throw new Exception("Catalog completion failed: "+entry.key);
                    validated++;
                }
                finally { UnityEngine.Object.DestroyImmediate(jobHost); }
            }
            File.WriteAllText("work/four-stage-validation.txt","PASS: "+validated+" catalog buildings;  four phase labels; completed model visibility; temporary construction visuals; rewind/save progress; reveal shader compilation. Lighthouse untouched.");
        }
        catch(Exception e) { File.WriteAllText("work/four-stage-validation.txt","FAIL: "+e); Debug.LogException(e); }
        finally { if(host!=null) UnityEngine.Object.DestroyImmediate(host); }
    }
}

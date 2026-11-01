using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using LastLandfall.Prototype;
[InitializeOnLoad]
public static class CoastalDockValidation
{
 static CoastalDockValidation(){EditorApplication.update+=Check;}
 static void Check(){if(EditorApplication.isCompiling||EditorApplication.isUpdating||!EditorApplication.isPlaying||!File.Exists("work/TripoImport/RescueDock/test.request"))return; File.Delete("work/TripoImport/RescueDock/test.request"); try{Run();}catch(Exception e){File.WriteAllText("work/TripoImport/RescueDock/validation.txt",e.ToString());}}
 static void Run(){
 var host=UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();var grid=host.ConstructionGrid;
 var flags=BindingFlags.Instance|BindingFlags.NonPublic;
 var find=typeof(BuildPlacementPrototype).GetMethod("TryFindDockDirection",flags);
 Vector2Int chosen=default,dir=default; bool found=false;int checkedCells=0;
 for(int z=0;z<grid.Depth&&!found;z++)for(int x=0;x<grid.Width&&!found;x++){
 var cell=new Vector2Int(x,z);var t=grid.GetTerrain(cell);if(!t.HasLand||t.MaximumHeight>grid.SeaLevel+3||t.MaximumHeight<grid.SeaLevel+.8f)continue;
 checkedCells++;object[] args={cell,Vector2Int.zero};if((bool)find.Invoke(host,args)){chosen=cell;dir=(Vector2Int)args[1];found=true;}}
 if(!found)throw new Exception("No valid low-cliff dock found; checked "+checkedCells);
 var occupied=(System.Collections.Generic.HashSet<Vector2Int>)typeof(BuildPlacementPrototype).GetField("occupiedCells",flags).GetValue(host);
 var blocked=chosen;bool added=occupied.Add(blocked);object[] blockedArgs={chosen,Vector2Int.zero};
 // Check the selected direction's complete footprint through the same reservation table.
 if((bool)find.Invoke(host,blockedArgs))throw new Exception("Occupied anchor accepted");if(added)occupied.Remove(blocked);
 var create=typeof(BuildPlacementPrototype).GetMethod("CreatePlaceableObject",flags);
 var dock=(GameObject)create.Invoke(host,new object[]{"RescueDock","Dock validation"});
 var map=(Transform)typeof(BuildPlacementPrototype).GetField("mapRoot",flags).GetValue(host);dock.transform.SetParent(map,false);
 dock.transform.localPosition=grid.CellCenter(chosen);dock.transform.localPosition=new Vector3(dock.transform.localPosition.x,grid.SeaLevel,dock.transform.localPosition.z);
 dock.transform.localRotation=Quaternion.FromToRotation(Vector3.back,new Vector3(dir.x,0,dir.y));
 typeof(BuildPlacementPrototype).GetMethod("UpdateDockAccess",flags).Invoke(host,new object[]{dock,chosen});
 var model=dock.transform.Find("RescueDock Model");if(model==null||model.GetComponentInChildren<MeshFilter>().sharedMesh.vertexCount<1000)throw new Exception("Tripo model missing");
 BuildingConstructionController.TryBegin(dock,"RescueDock",model.gameObject,()=>1f,0f);
 var job=dock.GetComponent<BuildingConstructionController>();
 if(job==null)throw new Exception("Construction missing");
 foreach(float progress in new[]{0f,.5f,1f}){job.SetProgress(progress);bool visible=false;foreach(var renderer in dock.GetComponentsInChildren<Renderer>())if(renderer.enabled && renderer.gameObject.activeInHierarchy && renderer.GetComponent<MeshFilter>() != null && renderer.GetComponent<MeshFilter>().sharedMesh.vertexCount > 1000)visible=true;if(!visible)throw new Exception("Dock hidden during construction "+progress);}
 var stairs=dock.transform.Find("Adaptive shore stairs");if(stairs==null)throw new Exception("Cliff stairs missing");
 foreach(var r in model.GetComponentsInChildren<Renderer>())if(r.sharedMaterial.mainTexture==null)throw new Exception("Texture missing");
 var shader=Shader.Find("LastLandfall/Island Construction Grid");if(UnityEditor.ShaderUtil.ShaderHasError(shader))throw new Exception("Grid shader error");
 var bounds=new Bounds(dock.transform.position,Vector3.zero);foreach(var r in dock.GetComponentsInChildren<Renderer>())bounds.Encapsulate(r.bounds);
 foreach(var tr in dock.GetComponentsInChildren<Transform>())tr.gameObject.layer=31;
 var cameraObject=new GameObject("Dock proof camera");var cam=cameraObject.AddComponent<Camera>();cam.cullingMask=1<<31;cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.13f,.18f,.23f);cam.orthographic=true;cam.orthographicSize=bounds.size.magnitude*.55f;
 cam.transform.position=bounds.center+new Vector3(8,7,-9)*bounds.size.magnitude*.12f;cam.transform.LookAt(bounds.center);
 var rt=new RenderTexture(1100,800,24);cam.targetTexture=rt;cam.Render();var previous=RenderTexture.active;RenderTexture.active=rt;var image=new Texture2D(1100,800,TextureFormat.RGB24,false);image.ReadPixels(new Rect(0,0,1100,800),0,0);image.Apply();File.WriteAllBytes("work/TripoImport/RescueDock/unity-dock.png",image.EncodeToPNG());RenderTexture.active=previous;cam.targetTexture=null;rt.Release();UnityEngine.Object.Destroy(rt);UnityEngine.Object.Destroy(image);UnityEngine.Object.Destroy(cameraObject);
 File.WriteAllText("work/TripoImport/RescueDock/validation.txt","PASS: Tripo mesh and texture loaded; grid shader compiled; low-cliff placement found at "+chosen+" direction "+dir+"; construction visibility passed; occupancy rejection passed; stairs "+stairs.childCount+" parts; bounds "+bounds.size+"; checked candidates "+checkedCells);
 UnityEngine.Object.Destroy(dock);
 }
}

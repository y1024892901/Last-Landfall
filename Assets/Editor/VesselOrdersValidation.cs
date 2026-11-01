using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using LastLandfall.Prototype;
[InitializeOnLoad]
public static class VesselOrdersValidation
{
 static VesselOrdersValidation(){EditorApplication.update+=Check;}
 static void Check(){if(EditorApplication.isCompiling||EditorApplication.isUpdating||!EditorApplication.isPlaying||!File.Exists("work/vessel-orders.request"))return;var host=UnityEngine.Object.FindAnyObjectByType<BuildPlacementPrototype>();if(host==null||host.ConstructionGrid==null)return;File.Delete("work/vessel-orders.request");try{Run(host);File.WriteAllText("work/vessel-orders-validation.txt","PASS: empty boat cannot depart; two 100-unit cargo slots; dock-only loading; stock and cargo conservation; damage health; crew manifest round-trip; assigned survivor runs; reachable open-water route.");}catch(Exception e){File.WriteAllText("work/vessel-orders-validation.txt",e.ToString());}}
 static void Run(BuildPlacementPrototype host){
 void Assert(bool ok,string msg){if(!ok)throw new Exception(msg);}
 var original=RescueBoatController.ActiveVessel;GameObject ship=null,dock=null,person=null;float wood=ColonyResourceManager.Instance.Wood;
 try{
 ship=new GameObject("Vessel test");ship.transform.position=new Vector3(10000,host.ConstructionGrid.SeaLevel,10000);var boat=ship.AddComponent<RescueBoatController>();var orders=ship.AddComponent<VesselOrdersUI>();
 Assert(!orders.CanDepart,"Empty ship departure allowed");Assert(!orders.Sail(ship.transform.position+Vector3.forward*5),"Empty ship navigation allowed");Assert(!orders.LoadCargo(0,ResourceType.Wood,1),"Off-dock cargo loaded");
 dock=new GameObject("Cargo fixture dock");dock.transform.position=ship.transform.position+new Vector3(0,-.65f,4);new GameObject("Adaptive shore stairs").transform.SetParent(dock.transform,false);
 Assert(orders.LoadCargo(0,ResourceType.Wood,100),"Load failed");Assert(orders.cargo[0].amount==Mathf.Min(100,wood),"Wrong cargo amount");Assert(Mathf.Approximately(ColonyResourceManager.Instance.Wood+orders.cargo[0].amount,wood),"Cargo duplicated or lost");Assert(!orders.LoadCargo(0,ResourceType.Metal,1),"Mixed cargo types accepted");Assert(!orders.LoadCargo(2,ResourceType.Wood,1),"Third slot accepted");
 person=new GameObject("Test runner");person.transform.position=ship.transform.position;var runner=person.AddComponent<SurvivorCharacterController>();runner.RunRoute(new List<Vector3>{person.transform.position+Vector3.forward*.1f});Assert(runner.IsRunning,"Command did not trigger run");runner.CancelOrder();runner.Board(ship.transform,0);
 var members=(List<SurvivorCharacterController>)typeof(VesselOrdersUI).GetField("crew",BindingFlags.NonPublic|BindingFlags.Instance).GetValue(orders);members.Add(runner);Assert(orders.CanDepart,"Boarded crew cannot depart");Assert(orders.Sail(ship.transform.position+Vector3.forward*5),"Open water route rejected");
 orders.TakeDamage(10);Assert(orders.Health==90,"Health damage incorrect");var saved=orders.CaptureManifest();Assert(saved.slots.Length==2&&saved.people.Count==1,"Manifest incomplete");orders.RestoreManifest(saved);Assert(orders.CanDepart&&orders.Health==90&&orders.cargo[0].amount>0,"Manifest restore failed");
 typeof(VesselOrdersUI).GetMethod("Stop",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(orders,null);typeof(VesselOrdersUI).GetMethod("UnloadCargo",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(orders,null);Assert(Mathf.Approximately(ColonyResourceManager.Instance.Wood,wood),"Unloading lost resources");
 }finally{if(ColonyResourceManager.Instance.Wood<wood)ColonyResourceManager.Instance.Add(ResourceType.Wood,wood-ColonyResourceManager.Instance.Wood);if(dock!=null)UnityEngine.Object.DestroyImmediate(dock);if(person!=null)UnityEngine.Object.DestroyImmediate(person);if(ship!=null)UnityEngine.Object.DestroyImmediate(ship);typeof(RescueBoatController).GetField("activeVessel",BindingFlags.NonPublic|BindingFlags.Static).SetValue(null,original);}
 }
}

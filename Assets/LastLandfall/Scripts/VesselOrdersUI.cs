using System;
using System.Collections.Generic;
using UnityEngine;
namespace LastLandfall.Prototype
{
 [DefaultExecutionOrder(50)]
 public sealed class VesselOrdersUI : MonoBehaviour
 {
  [Serializable] public sealed class CargoSlot { public ResourceType type; public float amount; }
  [Serializable] public sealed class Manifest { public CargoSlot[] slots; public float health=100; public List<string> people=new List<string>(); }
  public Manifest CaptureManifest(){var data=new Manifest{slots=cargo,health=health};foreach(var person in crew)if(person!=null)data.people.Add(person.ResidentName);return data;}
  public void RestoreManifest(Manifest data)
  {
   Stop(); foreach(var person in pending)if(person!=null)person.CancelOrder();pending.Clear();hasAssignedBerth=true;
   foreach(var person in crew)if(person!=null)person.LeaveBoat(transform.position);crew.Clear();
   if(data==null){cargo=new[]{new CargoSlot(),new CargoSlot()};health=100;return;}
   cargo=data.slots!=null&&data.slots.Length==2?data.slots:new[]{new CargoSlot(),new CargoSlot()};health=Mathf.Clamp(data.health,0,100);
   if(data.people!=null)foreach(var name in data.people)foreach(var person in FindObjectsByType<SurvivorCharacterController>(FindObjectsSortMode.None))if(person.ResidentName==name&&!person.IsAboard&&crew.Count<boat.CrewCapacity){person.Board(transform,crew.Count);crew.Add(person);break;}
  }
  public CargoSlot[] cargo={new CargoSlot(),new CargoSlot()};
  readonly List<SurvivorCharacterController> crew=new List<SurvivorCharacterController>();
  readonly HashSet<SurvivorCharacterController> pending=new HashSet<SurvivorCharacterController>();
  bool hasAssignedBerth; float nextDockScan; GameObject gangway;
  Queue<Vector3> route; RescueBoatController boat; BuildPlacementPrototype host; float health=100; string message="靠泊后可安排人员登船。"; int resourceChoice; int slotChoice;
  public bool CanDepart=>crew.Count>0&&pending.Count==0&&health>0&&boat!=null&&boat.FuelPercent>0;
  public float Health=>health;
  public void TakeDamage(float amount){health=Mathf.Max(0,health-Mathf.Max(0,amount));if(health<=0){route=null;boat.enabled=false;}}
  void Awake(){boat=GetComponent<RescueBoatController>();host=FindAnyObjectByType<BuildPlacementPrototype>();}
  const float MaximumBoardingGap = 3.5f;
  const float BoardingEdgeHalfWidth = 3.1f;
  const float BoardingEdgeHeight = .65f;
  const float BoardingEdgeDepth = -4f;
  // The 2.48 x 6.20 m rescue hull needs extra clearance as it rocks and pitches.
  const float HullClearanceHalfWidth = 1.65f;
  const float HullClearanceHalfLength = 3.5f;
  static readonly float[] BerthSides = { 4.9f, -4.9f, 5.3f, -5.3f };
  static readonly float[] BerthDepths = { -5.8f, -6.2f, -6.6f };
  const string OpeningBerthMessage = "在救援艇旁的岸边建造救援码头，完工后可安排人员登船。";
  const string BerthTooFarMessage = "请将船靠近码头侧边（3.5米以内）再登船。";
  const string ReadyToBoardMessage = "救援船已靠泊，人员可以登船。";

  internal void UseOpeningBerth()
  {
   hasAssignedBerth = true;
   message = OpeningBerthMessage;
  }

  static Vector3 GetBoardingEdge(Transform dock, Vector3 boatPosition)
  {
   float side = dock.InverseTransformPoint(boatPosition).x >= 0f ? BoardingEdgeHalfWidth : -BoardingEdgeHalfWidth;
   return dock.TransformPoint(new Vector3(side, BoardingEdgeHeight, BoardingEdgeDepth));
  }

  static float GapToBoardingEdge(Transform dock, Vector3 boatPosition)
  {
   Vector3 edge = GetBoardingEdge(dock, boatPosition);
   boatPosition.y = edge.y;
   return Vector3.Distance(edge, boatPosition);
  }

  internal static bool TryFindDockBerth(IslandConstructionGrid grid, Pose dock, out Pose berth)
  {
   Vector3 center = grid.Root.InverseTransformPoint(dock.position);
   center.y = grid.SeaLevel;
   Vector3 across = grid.Root.InverseTransformVector(dock.rotation * Vector3.right);
   Vector3 forward = grid.Root.InverseTransformVector(dock.rotation * Vector3.forward);
   foreach(float depth in BerthDepths)
   foreach(float side in BerthSides)
   {
    Vector2 boardingOffset = new Vector2(Mathf.Abs(side) - BoardingEdgeHalfWidth, depth - BoardingEdgeDepth);
    if(boardingOffset.sqrMagnitude > MaximumBoardingGap * MaximumBoardingGap) continue;
    Vector3 point = center + across * side + forward * depth;
    if(!IsClearBerth(grid, point, across, forward)) continue;
    berth = new Pose(grid.Root.TransformPoint(point), dock.rotation);
    return true;
   }
   berth = default;
   return false;
  }

  static bool IsClearBerth(IslandConstructionGrid grid, Vector3 center, Vector3 across, Vector3 forward)
  {
   for(int side = -3; side <= 3; side++)
   for(int length = -6; length <= 6; length++)
   {
    Vector3 point = center + across * (HullClearanceHalfWidth * side / 3f) +
     forward * (HullClearanceHalfLength * length / 6f);
    if(grid.TrySample(point.x, point.z, out _, out _)) return false;
   }
   return true;
  }

  void UpdateMooring()
  {
   if(Time.unscaledTime < nextDockScan || crew.Count > 0 || pending.Count > 0 ||
    route != null || boat.IsPlayerPiloting || !boat.enabled) return;
   nextDockScan = Time.unscaledTime + 2f;
   Transform currentDock = NearbyDock();
   if(currentDock != null && GapToBoardingEdge(currentDock, transform.position) <= MaximumBoardingGap)
   {
    if(!hasAssignedBerth || message == BerthTooFarMessage || message == OpeningBerthMessage) message = ReadyToBoardMessage;
    hasAssignedBerth = true;
    return;
   }

   var grid = host != null ? host.ConstructionGrid : null;
   if(grid == null || (currentDock == null && hasAssignedBerth)) return;
   foreach(var access in FindObjectsByType<Transform>(FindObjectsSortMode.None))
   {
    if(!IsCompletedDockAccess(access) || (currentDock != null && access.parent != currentDock)) continue;
    Transform dock = access.parent;
    if(!TryFindDockBerth(grid, new Pose(dock.position, dock.rotation), out Pose berth)) continue;
    boat.SetBasePosition(berth.position, berth.rotation);
    boat.SetMoored(true);
    hasAssignedBerth = true;
    message = ReadyToBoardMessage;
    return;
   }
  }

  void Update()
  {
   UpdateMooring();
   pending.RemoveWhere(p=>p==null);crew.RemoveAll(p=>p==null);boat.SetActualCrew(crew.Count);
   if(route!=null){if(!CanDepart||boat.FuelPercent<=0){Stop();message="航行中止：检查船员、血量和燃料。";}else{Vector3 target=route.Peek();Vector3 delta=Vector3.ProjectOnPlane(target-transform.position,Vector3.up);Quaternion rotation=delta.sqrMagnitude>.001f?Quaternion.RotateTowards(transform.rotation,Quaternion.LookRotation(delta),70*Time.deltaTime):transform.rotation;Vector3 position=Vector3.MoveTowards(transform.position,target,5*Time.deltaTime);boat.SetBasePosition(position,rotation);boat.ConsumeNavigationFuel(Time.deltaTime*.08f);if(Vector3.Distance(position,target)<.08f){route.Dequeue();if(route.Count==0){Stop();message="已到达目的地。";}}}}
  }

  internal void OrderSail(IslandConstructionGrid grid, Ray ray)
  {
   // A visible land hit is never interpreted as a water command behind the island.
   if (grid.TryRaycast(ray, out RaycastHit land) && grid.Root.InverseTransformPoint(land.point).y > grid.SeaLevel + .02f)
   {
    message = "请选择海面，船不能穿过岛屿。";
    return;
   }
   var plane = new Plane(grid.Root.up, grid.Root.TransformPoint(new Vector3(0, grid.SeaLevel, 0)));
   if (plane.Raycast(ray, out float length)) Sail(ray.GetPoint(length));
  }
  public bool Sail(Vector3 destination)
  {
   if(!CanDepart){message=pending.Count>0?"等待全部人员登船。":"请先在救援码头安排人员登船。";return false;}
   if(!VesselGridNavigation.Find(host.ConstructionGrid,transform.position,destination,true,out var path)){message="没有安全水路：目标靠岸过近或被陆地阻挡。";return false;}
   if(gangway!=null){Destroy(gangway);gangway=null;}
   boat.SetPiloting(false);boat.enabled=false;route=new Queue<Vector3>(path);message="正在航行。";return true;
  }
  void Stop(){route=null;boat.SetBasePosition(transform.position,transform.rotation);boat.SetMoored(true);boat.enabled=health>0;}
  static bool IsCompletedDockAccess(Transform access)
  {
   if (access.name != "Adaptive shore stairs") return false;
   Transform dock = access.parent;
   if (dock == null || dock.name.Contains("Preview") || dock.name.Contains("validation")) return false;
   var construction = dock.GetComponent<BuildingConstructionController>();
   return construction == null || construction.IsComplete;
  }
  Transform NearbyDock()
  {
   Transform best=null;float distance=8f;
   foreach(var tr in FindObjectsByType<Transform>(FindObjectsSortMode.None))if(IsCompletedDockAccess(tr)){
    Vector3 berth=tr.parent.TransformPoint(new Vector3(0,BoardingEdgeHeight,BoardingEdgeDepth));float d=Vector3.Distance(berth,transform.position);if(d<distance){best=tr.parent;distance=d;}}
   return best;
  }
  internal bool IsMooredAt(Transform dock) => dock != null && route == null && !boat.IsPlayerPiloting &&
   GapToBoardingEdge(dock, transform.position) <= MaximumBoardingGap && NearbyDock() == dock;
  void OnDestroy(){if(gangway!=null)Destroy(gangway);}
  void BoardPeople()
  {
   var dock=NearbyDock();if(dock==null||route!=null){message="请先将船停在已完工的救援码头旁。";return;}
   Vector3 edge=GetBoardingEdge(dock,transform.position);
   Vector3 shipEntry=transform.position;shipEntry.y=edge.y;
   float gap=GapToBoardingEdge(dock,transform.position);
   if(gap>MaximumBoardingGap){message=BerthTooFarMessage;return;}
   if(gangway!=null)Destroy(gangway);
   gangway=GameObject.CreatePrimitive(PrimitiveType.Cube);gangway.name="Boarding gangway";
   gangway.transform.position=(edge+shipEntry)*.5f;gangway.transform.rotation=Quaternion.LookRotation(shipEntry-edge);
   gangway.transform.localScale=new Vector3(.9f,.12f,Mathf.Max(.3f,gap));
   var grid=host.ConstructionGrid;int issued=0;
   foreach(var person in FindObjectsByType<SurvivorCharacterController>(FindObjectsSortMode.None)){
    if(person.IsAboard||pending.Contains(person)||person.IsRunning||crew.Count+pending.Count>=boat.CrewCapacity)continue;
    Vector3 landing=dock.TransformPoint(new Vector3(0,0,2));
    if(!VesselGridNavigation.Find(grid,person.transform.position,landing,false,out var path))continue;
    // Follow the landing, each stair tread, then the dock deck before crossing onto the vessel.
    Transform access=dock.Find("Adaptive shore stairs");if(access==null)continue;
    Transform platform=access.Find("Shore landing");if(platform!=null)path.Add(platform.TransformPoint(new Vector3(0,.5f,0)));
    for(int i=0;i<access.childCount;i++){var step=access.GetChild(i);if(step.name.StartsWith("Shore stair "))path.Add(step.TransformPoint(new Vector3(0,.5f,0)));}
    path.Add(dock.TransformPoint(new Vector3(0,.65f,-3f)));
    path.Add(edge);path.Add(shipEntry);pending.Add(person);issued++;
    person.RunRoute(path,()=>{pending.Remove(person);if(person!=null&&this!=null){person.Board(transform,crew.Count);crew.Add(person);message="人员已登船，可以点击海面航行。";}});
   }
   message=issued>0?"人员正在跑向码头登船，登船完成后才能出航。":"没有空闲且能够抵达此码头的人员。";
  }
  public bool LoadCargo(int slot,ResourceType type,float quantity)
  {
   if(slot<0||slot>=2||quantity<=0||type==ResourceType.Power||NearbyDock()==null||route!=null)return false;
   var stock=ColonyResourceManager.Instance;if(stock==null)return false;var item=cargo[slot];if(item.amount>0&&item.type!=type)return false;
   float amount=Mathf.Min(quantity,100-item.amount,stock.GetAmount(type));if(amount<=0||!stock.TrySpend(type,amount))return false;item.type=type;item.amount+=amount;return true;
  }
  void UnloadCargo(){if(NearbyDock()==null||route!=null)return;var stock=ColonyResourceManager.Instance;if(stock==null)return;foreach(var item in cargo){float amount=Mathf.Min(item.amount,Mathf.Max(0,stock.GetCapacity(item.type)-stock.GetAmount(item.type)));stock.Add(item.type,amount);item.amount-=amount;}}
  internal static readonly string[] InspectorTabs = { "航行", "船员", "货舱" };
  internal string InspectorTitle => boat.VesselName;

  internal void DrawInspectionPage(BuildingInspectorUI panel, int page)
  {
   switch (page)
   {
    case 0: DrawNavigation(panel); break;
    case 1: DrawCrew(panel); break;
    case 2: DrawCargo(panel); break;
   }
  }

  void DrawNavigation(BuildingInspectorUI panel)
  {
   panel.Meter("船体耐久", $"{health:F0} / 100", health / 100f, new Color32(103, 185, 145, 255));
   panel.Meter("燃料", $"{boat.FuelPercent:F0}%", boat.FuelPercent / 100f, HudTheme.FrostCyan);
   string status = route != null ? "航行中" : boat.IsPlayerPiloting ? "手动驾驶" :
    IsMooredAt(NearbyDock()) ? "已靠泊" : "海面待命";
   panel.Row("状态", status);
   panel.Row("船员", $"{crew.Count} / {boat.CrewCapacity}");
   panel.Note(message);
  }

  void DrawCrew(BuildingInspectorUI panel)
  {
   panel.Section($"已登船 · {crew.Count} / {boat.CrewCapacity}");
   foreach (var person in crew)
    if (person != null) panel.Row(person.ResidentName, person.Profession);
   if (crew.Count == 0) panel.Note("暂无船员。");

   if (pending.Count > 0)
   {
    panel.Section($"待登船 · {pending.Count}");
    foreach (var person in pending)
     if (person != null) panel.Row(person.ResidentName, "正在前往码头");
   }

   GUILayout.BeginHorizontal();
   if (panel.ActionButton("安排人员登船", route == null)) BoardPeople();
   if (panel.ActionButton("靠岸下船", crew.Count > 0 && pending.Count == 0 && route == null)) Disembark();
   GUILayout.EndHorizontal();
   panel.Note(message);
  }

  void Disembark()
  {
   var dock = NearbyDock();
   var grid = host != null ? host.ConstructionGrid : null;
   if (dock == null || grid == null)
   {
    message = "请先停靠已完工的救援码头。";
    return;
   }

   Vector3 landing = grid.Root.InverseTransformPoint(dock.TransformPoint(new Vector3(0, 0, 2)));
   if (!grid.TrySample(landing.x, landing.z, out var ground, out _))
   {
    message = "无法找到安全的下船位置。";
    return;
   }

   Vector3 shore = grid.Root.TransformPoint(ground);
   foreach (var person in crew)
    if (person != null) person.LeaveBoat(shore);
   crew.Clear();
   message = "船员已下船。";
  }

  void DrawCargo(BuildingInspectorUI panel)
  {
   for (int i = 0; i < cargo.Length; i++)
   {
    CargoSlot item = cargo[i];
    string amount = item.amount > 0f ? $"{ResourceName(item.type)} · {item.amount:F0} / 100" : "空置";
    panel.Row($"货舱 {i + 1}", amount);
   }

   panel.Row("装载目标", $"货舱 {slotChoice + 1} · {ResourceName(Types[resourceChoice])}");
   GUILayout.BeginHorizontal();
   if (panel.ActionButton("选货舱 1")) slotChoice = 0;
   if (panel.ActionButton("选货舱 2")) slotChoice = 1;
   if (panel.ActionButton("切换品类")) resourceChoice = (resourceChoice + 1) % Types.Length;
   GUILayout.EndHorizontal();

   GUILayout.BeginHorizontal();
   if (panel.ActionButton("装载 100", route == null))
    message = LoadCargo(slotChoice, Types[resourceChoice], 100) ? "物资已装船。" :
     "装载需要停靠码头、货舱品类匹配，并且有剩余库存。";
   if (panel.ActionButton("卸下物资", route == null))
   {
    if (NearbyDock() == null) message = "请先停靠已完工的救援码头。";
    else
    {
     UnloadCargo();
     message = "卸货完成。";
    }
   }
   GUILayout.EndHorizontal();
   panel.Note(message);
  }

  void OnGUI()
  {
   if (health >= 100f || Camera.main == null || (host != null && !host.isActiveAndEnabled)) return;
   Vector3 point = Camera.main.WorldToScreenPoint(transform.position + Vector3.up * 3f);
   if (point.z <= 0f) return;

   var rect = new Rect(point.x - 35f, Screen.height - point.y, 70f, 6f);
   Color previous = GUI.color;
   GUI.color = Color.black;
   GUI.DrawTexture(rect, Texture2D.whiteTexture);
   rect.width *= health / 100f;
   GUI.color = HudTheme.DangerRed;
   GUI.DrawTexture(rect, Texture2D.whiteTexture);
   GUI.color = previous;
  }

  static readonly ResourceType[] Types = { ResourceType.Wood, ResourceType.Food, ResourceType.Water, ResourceType.Metal, ResourceType.Fuel, ResourceType.Ore, ResourceType.Medical };
  static string ResourceName(ResourceType type)
  {
   switch(type)
   {
    case ResourceType.Wood: return "木材";
    case ResourceType.Food: return "食物";
    case ResourceType.Water: return "淡水";
    case ResourceType.Metal: return "金属";
    case ResourceType.Fuel: return "燃料";
    case ResourceType.Ore: return "矿石";
    case ResourceType.Medical: return "医疗";
    default: return "电力";
   }
  }
 }
}

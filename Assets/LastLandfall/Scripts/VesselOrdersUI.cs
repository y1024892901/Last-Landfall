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
   Stop(); foreach(var person in pending)if(person!=null)person.CancelOrder();pending.Clear();initialDockPlaced=true;
   foreach(var person in crew)if(person!=null)person.LeaveBoat(transform.position);crew.Clear();
   if(data==null){cargo=new[]{new CargoSlot(),new CargoSlot()};health=100;return;}
   cargo=data.slots!=null&&data.slots.Length==2?data.slots:new[]{new CargoSlot(),new CargoSlot()};health=Mathf.Clamp(data.health,0,100);
   if(data.people!=null)foreach(var name in data.people)foreach(var person in FindObjectsByType<SurvivorCharacterController>(FindObjectsSortMode.None))if(person.ResidentName==name&&!person.IsAboard&&crew.Count<boat.CrewCapacity){person.Board(transform,crew.Count);crew.Add(person);break;}
  }
  public CargoSlot[] cargo={new CargoSlot(),new CargoSlot()};
  readonly List<SurvivorCharacterController> crew=new List<SurvivorCharacterController>();
  readonly HashSet<SurvivorCharacterController> pending=new HashSet<SurvivorCharacterController>();
  readonly HashSet<SurvivorCharacterController> selectedPeople=new HashSet<SurvivorCharacterController>();
  bool initialDockPlaced; float nextDockScan; GameObject gangway;
  Queue<Vector3> route; RescueBoatController boat; BuildPlacementPrototype host; bool selected; float health=100; string message="选择船只，安排人员登船后点击海面航行。"; int resourceChoice; int slotChoice;
  public static void ClearSelection()
  {
   foreach(var ui in FindObjectsByType<VesselOrdersUI>(FindObjectsSortMode.None)){ui.selected=false;ui.selectedPeople.Clear();}
  }
  public bool CanDepart=>crew.Count>0&&pending.Count==0&&health>0&&boat!=null&&boat.FuelPercent>0;
  public float Health=>health;
  Vector2 infoScroll;
  // Docked flush to bottom-right

  public Rect InfoRect => BuildingInspectorUI.GetPanelRect();
  public static VesselOrdersUI Selected => Array.Find(FindObjectsByType<VesselOrdersUI>(FindObjectsSortMode.None), ui => ui.selected || ui.selectedPeople.Count > 0);

  public static bool ContainsPoint(Vector2 point)
  {
   foreach(var ui in FindObjectsByType<VesselOrdersUI>(FindObjectsSortMode.None))
   {
    if((ui.selected || ui.selectedPeople.Count > 0) && ui.InfoRect.Contains(point)) return true;
   }
   return false;
  }
  public void TakeDamage(float amount){health=Mathf.Max(0,health-Mathf.Max(0,amount));if(health<=0){route=null;boat.enabled=false;}}
  void Awake(){boat=GetComponent<RescueBoatController>();host=FindAnyObjectByType<BuildPlacementPrototype>();}
  bool Hit(Transform target,Ray ray,out float distance){distance=float.MaxValue;bool hit=false;foreach(var renderer in target.GetComponentsInChildren<Renderer>()){if(!renderer.enabled)continue;var bounds=renderer.bounds;bounds.Expand(.3f);if(bounds.IntersectRay(ray,out float d)&&d<distance){distance=d;hit=true;}}return hit;}
  const float MaximumBoardingGap=3.5f;
  float GapToBoardingEdge(Transform dock,Vector3 boatPosition)
  {
   Vector3 edge=dock.TransformPoint(new Vector3(dock.InverseTransformPoint(boatPosition).x>=0?3.1f:-3.1f,.65f,-4f));
   boatPosition.y=edge.y;return Vector3.Distance(edge,boatPosition);
  }
  bool IsClearBerth(IslandConstructionGrid grid,Transform dock,Vector3 offset)
  {
   float[] sides={-.85f,0,.85f};float[] lengths={-2f,0,2f};
   foreach(float side in sides)foreach(float length in lengths)
   {
    Vector3 world=dock.TransformPoint(offset+new Vector3(side,0,length));
    Vector3 local=grid.Root.InverseTransformPoint(world);
    if(grid.TrySample(local.x,local.z,out _,out _))return false;
   }
   return true;
  }
  void Update()
  {
   if(Time.unscaledTime>=nextDockScan)
   {
    nextDockScan=Time.unscaledTime+2f;
    Transform currentDock=initialDockPlaced&&crew.Count==0&&route==null&&!boat.IsPlayerPiloting?NearbyDock():null;
    if(currentDock!=null&&message=="请将船靠近码头侧边（3.5米以内）再登船。"&&GapToBoardingEdge(currentDock,transform.position)<=MaximumBoardingGap)
     message="救援船已靠泊，人员可以登船。";
    bool shouldSnapToDock=!initialDockPlaced||(currentDock!=null&&GapToBoardingEdge(currentDock,transform.position)>MaximumBoardingGap);
    if(shouldSnapToDock)
    {
    foreach(var access in FindObjectsByType<Transform>(FindObjectsSortMode.None))if(access.name=="Adaptive shore stairs"&&access.parent!=null&&!access.parent.name.Contains("Preview")&&!access.parent.name.Contains("validation"))
    {
     if(currentDock!=null&&access.parent!=currentDock)continue;
     var job=access.parent.GetComponent<BuildingConstructionController>();if(job!=null&&!job.IsComplete)continue;
     var mooringGrid=host!=null?host.ConstructionGrid:null;
     float seaY=mooringGrid!=null?mooringGrid.Root.TransformPoint(new Vector3(0,mooringGrid.SeaLevel,0)).y:access.parent.position.y;
     // The mooring needs to clear the rocky shoreline with the full hull while
     // staying close enough to the side boarding point. The previous -4 to
     // -4.8 m placements left most of the boat over the shore collision.
     Vector3[] berthOffsets={new Vector3(4.2f,0,-6.2f),new Vector3(-4.2f,0,-6.2f),new Vector3(4.2f,0,-5.8f),new Vector3(-4.2f,0,-5.8f),new Vector3(4.2f,0,-6.5f),new Vector3(-4.2f,0,-6.5f),new Vector3(4.8f,0,-6.2f),new Vector3(-4.8f,0,-6.2f),new Vector3(4.8f,0,-5.8f),new Vector3(-4.8f,0,-5.8f),new Vector3(5.4f,0,-6.2f),new Vector3(-5.4f,0,-6.2f)};
     foreach(var offset in berthOffsets)
     {
      Vector3 berth=access.parent.TransformPoint(offset);berth.y=seaY;
      if(mooringGrid!=null&&!IsClearBerth(mooringGrid,access.parent,offset))continue;
      boat.SetBasePosition(berth,access.parent.rotation);initialDockPlaced=true;message="救援船已靠泊，人员可以登船。";
      Debug.Log("默认救援船已停靠于救援码头外侧："+access.parent.name+"，位置 "+berth);
      break;
     }
     if(initialDockPlaced)break;
    }
    }
   }
   pending.RemoveWhere(p=>p==null);crew.RemoveAll(p=>p==null);boat.SetActualCrew(crew.Count);
   if(route!=null){if(!CanDepart||boat.FuelPercent<=0){Stop();message="航行中止：检查船员、血量和燃料。";}else{Vector3 target=route.Peek();Vector3 delta=Vector3.ProjectOnPlane(target-transform.position,Vector3.up);Quaternion rotation=delta.sqrMagnitude>.001f?Quaternion.RotateTowards(transform.rotation,Quaternion.LookRotation(delta),70*Time.deltaTime):transform.rotation;Vector3 position=Vector3.MoveTowards(transform.position,target,5*Time.deltaTime);boat.SetBasePosition(position,rotation);boat.ConsumeNavigationFuel(Time.deltaTime*.08f);if(Vector3.Distance(position,target)<.08f){route.Dequeue();if(route.Count==0){Stop();message="已到达目的地。";}}}}
   if(!Input.GetMouseButtonDown(0)||host==null||Camera.main==null)return;
   Vector2 point=new Vector2(Input.mousePosition.x,Screen.height-Input.mousePosition.y);
   if(((selected||selectedPeople.Count>0)&&InfoRect.Contains(point))||BuildingInspectorUI.ContainsPoint(point)||host.BlocksWorldOrders(point))return;
   Ray ray=Camera.main.ScreenPointToRay(Input.mousePosition);
   if(Hit(transform,ray,out _)){host.CollapseResourceDetails();BuildingInspectorUI.Close();selected=true;selectedPeople.Clear();return;}
   SurvivorCharacterController nearest=null;float closest=float.MaxValue;
   foreach(var person in FindObjectsByType<SurvivorCharacterController>(FindObjectsSortMode.None))if(!person.IsAboard&&Hit(person.transform,ray,out float d)&&d<closest){closest=d;nearest=person;}
   if(nearest!=null){host.CollapseResourceDetails();if(!Input.GetKey(KeyCode.LeftShift)&&!Input.GetKey(KeyCode.RightShift))selectedPeople.Clear();selectedPeople.Add(nearest);BuildingInspectorUI.Close();selected=false;return;}
   var grid=host.ConstructionGrid;if(grid==null)return;
   if(selectedPeople.Count>0){if(grid.TryRaycast(ray,out RaycastHit hit)){foreach(var person in selectedPeople)if(VesselGridNavigation.Find(grid,person.transform.position,hit.point,false,out var path))person.RunRoute(path);message="选中的人物正在奔跑前往目标。";}return;}
   if(!selected)
   {
    foreach(var building in host.PlacedBuildings)if(building.GameObject!=null&&Hit(building.GameObject.transform,ray,out _)){BuildingInspectorUI.Inspect(building);host.CollapseResourceDetails();break;}
    return;
   }
   // A visible land hit is never interpreted as a water command behind the island.
   if(grid.TryRaycast(ray,out RaycastHit land)&&grid.Root.InverseTransformPoint(land.point).y>grid.SeaLevel+.02f){message="请选择海面，船不能穿过岛屿。";return;}
   Plane plane=new Plane(grid.Root.up,grid.Root.TransformPoint(new Vector3(0,grid.SeaLevel,0)));
   if(plane.Raycast(ray,out float length))Sail(ray.GetPoint(length));
  }
  public bool Sail(Vector3 destination)
  {
   if(!CanDepart){message=pending.Count>0?"等待全部人员登船。":"请先在救援码头安排人员登船。";return false;}
   if(!VesselGridNavigation.Find(host.ConstructionGrid,transform.position,destination,true,out var path)){message="没有安全水路：目标靠岸过近或被陆地阻挡。";return false;}
   if(gangway!=null){Destroy(gangway);gangway=null;}
   boat.SetPiloting(false);boat.enabled=false;route=new Queue<Vector3>(path);message="正在航行。";return true;
  }
  void Stop(){route=null;boat.SetBasePosition(transform.position,transform.rotation);boat.SetMoored(true);boat.enabled=health>0;}
  Transform NearbyDock()
  {
   Transform best=null;float distance=8f;
   foreach(var tr in FindObjectsByType<Transform>(FindObjectsSortMode.None))if(tr.name=="Adaptive shore stairs"&&tr.parent!=null&&!tr.parent.name.Contains("Preview")&&!tr.parent.name.Contains("validation")){
    var construction=tr.parent.GetComponent<BuildingConstructionController>();if(construction!=null&&!construction.IsComplete)continue;
    Vector3 berth=tr.parent.TransformPoint(new Vector3(0,.65f,-4f));float d=Vector3.Distance(berth,transform.position);if(d<distance){best=tr.parent;distance=d;}}
   return best;
  }
  void OnDestroy(){if(gangway!=null)Destroy(gangway);}
  void BoardPeople()
  {
   var dock=NearbyDock();if(dock==null||route!=null){message="请先将船停在已完工的救援码头旁。";return;}
   Vector3 edge=dock.TransformPoint(new Vector3(dock.InverseTransformPoint(transform.position).x>=0?3.1f:-3.1f,.65f,-4f));
   Vector3 shipEntry=transform.position;shipEntry.y=edge.y;
   float gap=GapToBoardingEdge(dock,transform.position);
   if(gap>MaximumBoardingGap){message="请将船靠近码头侧边（3.5米以内）再登船。";return;}
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
    int vesselTab = 0;
  static readonly string[] VesselTabs = { "航行概况", "船员乘员", "货舱物资" };
  static readonly string[] PeopleTabs = { "人员档案", "行动指令" };

  static GUIStyle panelStyle;
  static GUIStyle cardStyle;
  static GUIStyle titleStyle;
  static GUIStyle subtitleStyle;
  static GUIStyle labelStyle;
  static GUIStyle valueStyle;
  static GUIStyle activeTabStyle;
  static GUIStyle inactiveTabStyle;
  static GUIStyle buttonStyle;
  static GUIStyle dangerButtonStyle;
  static GUIStyle closeButtonStyle;
  static Texture2D barBgTex;
  static Texture2D barFillTex;
  static Texture2D barFuelTex;

  static void EnsureStyles()
  {
   if(panelStyle != null) return;

   Texture2D panelTex = MakeOpaqueConsoleTexture(64,
       new Color(0.045f, 0.055f, 0.065f, 0.98f),
       new Color(0.85f, 0.70f, 0.38f, 0.95f),
       1.5f, 7f);

   panelStyle = new GUIStyle(GUI.skin.box)
   {
       normal = { background = panelTex },
       border = new RectOffset(10, 10, 10, 10),
       padding = new RectOffset(0, 0, 0, 0)
   };

   Texture2D cardTex = MakeOpaqueConsoleTexture(32,
       new Color(0.075f, 0.090f, 0.110f, 0.96f),
       new Color(0.85f, 0.70f, 0.38f, 0.30f),
       1.0f, 5f);

   cardStyle = new GUIStyle(GUI.skin.box)
   {
       normal = { background = cardTex },
       border = new RectOffset(6, 6, 6, 6),
       padding = new RectOffset(0, 0, 0, 0)
   };

   Texture2D activeTabTex = MakeOpaqueConsoleTexture(32,
       new Color(0.68f, 0.52f, 0.20f, 0.98f),
       new Color(0.98f, 0.85f, 0.45f, 1.0f),
       1.5f, 5f);
   Texture2D inactiveTabTex = MakeOpaqueConsoleTexture(32,
       new Color(0.065f, 0.080f, 0.095f, 0.95f),
       new Color(0.85f, 0.70f, 0.38f, 0.40f),
       1.0f, 5f);
   Texture2D inactiveTabHoverTex = MakeOpaqueConsoleTexture(32,
       new Color(0.16f, 0.14f, 0.08f, 0.95f),
       new Color(0.98f, 0.85f, 0.45f, 0.85f),
       1.2f, 5f);

   activeTabStyle = new GUIStyle(GUI.skin.button)
   {
       normal = { background = activeTabTex, textColor = new Color(1.0f, 0.96f, 0.88f) },
       hover = { background = activeTabTex, textColor = Color.white },
       active = { background = activeTabTex, textColor = Color.white },
       fontStyle = FontStyle.Bold,
       fontSize = 12,
       alignment = TextAnchor.MiddleCenter
   };

   inactiveTabStyle = new GUIStyle(GUI.skin.button)
   {
       normal = { background = inactiveTabTex, textColor = new Color(0.68f, 0.76f, 0.82f) },
       hover = { background = inactiveTabHoverTex, textColor = new Color(0.96f, 0.92f, 0.80f) },
       active = { background = inactiveTabHoverTex, textColor = Color.white },
       fontStyle = FontStyle.Normal,
       fontSize = 12,
       alignment = TextAnchor.MiddleCenter
   };

   Texture2D btnNormal = MakeOpaqueConsoleTexture(32,
       new Color(0.085f, 0.105f, 0.130f, 0.98f),
       new Color(0.85f, 0.70f, 0.38f, 0.75f),
       1.2f, 5f);
   Texture2D btnHover = MakeOpaqueConsoleTexture(32,
       new Color(0.24f, 0.20f, 0.10f, 0.98f),
       new Color(1.0f, 0.88f, 0.48f, 1.0f),
       1.5f, 5f);

   buttonStyle = new GUIStyle(GUI.skin.button)
   {
       normal = { background = btnNormal, textColor = new Color(0.95f, 0.93f, 0.88f) },
       hover = { background = btnHover, textColor = Color.white },
       active = { background = btnHover, textColor = Color.white },
       fontStyle = FontStyle.Bold,
       fontSize = 12,
       alignment = TextAnchor.MiddleCenter
   };

   Texture2D dangerNormal = MakeOpaqueConsoleTexture(32,
       new Color(0.26f, 0.06f, 0.06f, 0.98f),
       new Color(0.92f, 0.38f, 0.32f, 0.85f),
       1.2f, 5f);
   Texture2D dangerHover = MakeOpaqueConsoleTexture(32,
       new Color(0.42f, 0.08f, 0.08f, 0.98f),
       new Color(1.0f, 0.50f, 0.45f, 1.0f),
       1.5f, 5f);

   dangerButtonStyle = new GUIStyle(buttonStyle)
   {
       normal = { background = dangerNormal, textColor = new Color(1.0f, 0.85f, 0.82f) },
       hover = { background = dangerHover, textColor = Color.white },
       active = { background = dangerHover, textColor = Color.white }
   };

   Texture2D closeNormal = MakeOpaqueConsoleTexture(24,
       new Color(0.08f, 0.10f, 0.12f, 0.95f),
       new Color(0.85f, 0.70f, 0.38f, 0.60f),
       1.0f, 4f);
   Texture2D closeHover = MakeOpaqueConsoleTexture(24,
       new Color(0.28f, 0.14f, 0.08f, 0.98f),
       new Color(1.0f, 0.82f, 0.42f, 1.0f),
       1.2f, 4f);

   closeButtonStyle = new GUIStyle(GUI.skin.button)
   {
       normal = { background = closeNormal, textColor = new Color(0.90f, 0.80f, 0.60f) },
       hover = { background = closeHover, textColor = Color.white },
       active = { background = closeHover, textColor = Color.white },
       fontStyle = FontStyle.Bold,
       fontSize = 13,
       alignment = TextAnchor.MiddleCenter
   };

   titleStyle = new GUIStyle(GUI.skin.label)
   {
       fontSize = 16,
       fontStyle = FontStyle.Bold,
       normal = { textColor = new Color(0.96f, 0.90f, 0.76f) }
   };

   subtitleStyle = new GUIStyle(GUI.skin.label)
   {
       fontSize = 11,
       fontStyle = FontStyle.Bold,
       normal = { textColor = new Color(0.45f, 0.80f, 0.85f) }
   };

   labelStyle = new GUIStyle(GUI.skin.label)
   {
       fontSize = 12,
       normal = { textColor = new Color(0.68f, 0.76f, 0.82f) }
   };

   valueStyle = new GUIStyle(GUI.skin.label)
   {
       fontSize = 12,
       fontStyle = FontStyle.Bold,
       normal = { textColor = new Color(0.94f, 0.96f, 1.0f) },
       alignment = TextAnchor.MiddleRight
   };

   barBgTex = MakeSolidTexture(new Color(0.12f, 0.15f, 0.18f, 1f));
   barFillTex = MakeSolidTexture(new Color(0.35f, 0.85f, 0.55f, 1f));
   barFuelTex = MakeSolidTexture(new Color(0.95f, 0.72f, 0.25f, 1f));
  }

  void OnGUI()
  {
   if(health<100&&Camera.main!=null)
   {
    Vector3 screen=Camera.main.WorldToScreenPoint(transform.position+Vector3.up*3);
    if(screen.z>0)
    {
     Rect bar=new Rect(screen.x-35,Screen.height-screen.y,70,6);
     GUI.color=Color.black;GUI.DrawTexture(bar,Texture2D.whiteTexture);
     GUI.color=Color.red;bar.width*=health/100;GUI.DrawTexture(bar,Texture2D.whiteTexture);
     GUI.color=Color.white;
    }
   }

  }

  public void DrawSelectionContents()
  {
   if(!selected&&selectedPeople.Count==0)return;
   EnsureStyles();

   float scale = Mathf.Clamp(Screen.height / 1080f, 0.75f, 1.15f);
   Rect panelRect = InfoRect;

   // Draw Opaque Victorian Console Plate
   GUI.Box(panelRect, GUIContent.none, panelStyle);

   // Top specular highlight line
   GUI.color = new Color(0.85f, 0.70f, 0.38f, 0.50f);
   GUI.DrawTexture(new Rect(panelRect.x + 12f * scale, panelRect.y + 1f, panelRect.width - 24f * scale, 1.5f), Texture2D.whiteTexture);
   GUI.color = Color.white;

   if (selected)
   {
    DrawBoatPanel(panelRect, scale);
   }
   else
   {
    DrawPeoplePanel(panelRect, scale);
   }
  }

  void DrawBoatPanel(Rect panelRect, float scale)
  {
   // 1. Header
   GUI.Label(new Rect(panelRect.x + 14f * scale, panelRect.y + 10f * scale, 22f * scale, 22f * scale), "⛵", titleStyle);
   GUI.Label(new Rect(panelRect.x + 38f * scale, panelRect.y + 8f * scale, panelRect.width - 74f * scale, 22f * scale), boat.VesselName, titleStyle);
   GUI.Label(new Rect(panelRect.x + 38f * scale, panelRect.y + 27f * scale, panelRect.width - 74f * scale, 16f * scale), "[搜救巡航艇]", subtitleStyle);

   // Close Button
   Rect closeRect = new Rect(panelRect.xMax - 30f * scale, panelRect.y + 9f * scale, 22f * scale, 22f * scale);
   if (GUI.Button(closeRect, "×", closeButtonStyle))
   {
    selected = false;
    selectedPeople.Clear();
    return;
   }

   // Divider below header
   GUI.color = new Color(0.85f, 0.70f, 0.38f, 0.35f);
   GUI.DrawTexture(new Rect(panelRect.x + 12f * scale, panelRect.y + 48f * scale, panelRect.width - 24f * scale, 1f), Texture2D.whiteTexture);
   GUI.color = Color.white;

   // 2. Tab Bar
   float tabY = panelRect.y + 54f * scale;
   float tabH = 27f * scale;
   float tabGap = 4f * scale;
   float tabW = (panelRect.width - 24f * scale - tabGap * 2f) / 3f;

   for (int i = 0; i < VesselTabs.Length; i++)
   {
    Rect tRect = new Rect(panelRect.x + 12f * scale + i * (tabW + tabGap), tabY, tabW, tabH);
    bool isActive = vesselTab == i;
    GUIStyle tStyle = isActive ? activeTabStyle : inactiveTabStyle;

    if (GUI.Button(tRect, VesselTabs[i], tStyle))
    {
     vesselTab = i;
    }

    if (isActive)
    {
     GUI.color = new Color(1.0f, 0.88f, 0.45f, 0.95f);
     GUI.DrawTexture(new Rect(tRect.x + 6f * scale, tRect.yMax - 2f * scale, tRect.width - 12f * scale, 2f * scale), Texture2D.whiteTexture);
     GUI.color = Color.white;
    }
   }

   // 3. Tab Content Area
   float contentY = tabY + tabH + 8f * scale;
   Rect contentArea = new Rect(panelRect.x + 12f * scale, contentY, panelRect.width - 24f * scale, panelRect.yMax - contentY - 12f * scale);

   if (vesselTab == 0)
   {
    DrawBoatOverviewTab(contentArea, scale);
   }
   else if (vesselTab == 1)
   {
    DrawBoatCrewTab(contentArea, scale);
   }
   else
   {
    DrawBoatCargoTab(contentArea, scale);
   }
  }

  void DrawBoatOverviewTab(Rect area, float scale)
  {
   float cardH1 = 118f * scale;
   Rect card1 = new Rect(area.x, area.y, area.width, cardH1);
   GUI.Box(card1, GUIContent.none, cardStyle);

   float rowY = card1.y + 8f * scale;
   float rowH = 24f * scale;

   // HP Bar
   GUI.Label(new Rect(card1.x + 10f * scale, rowY, 70f * scale, 18f * scale), "船体耐久", labelStyle);
   Rect barRect = new Rect(card1.x + 85f * scale, rowY + 3f * scale, card1.width - 95f * scale, 14f * scale);
   GUI.DrawTexture(barRect, barBgTex);
   Rect fillRect = new Rect(barRect.x, barRect.y, barRect.width * Mathf.Clamp01(health / 100f), barRect.height);
   GUI.DrawTexture(fillRect, barFillTex);
   GUI.Label(new Rect(card1.x + 85f * scale, rowY, card1.width - 95f * scale, 18f * scale), $"{health:F0} / 100", valueStyle);
   rowY += rowH;

   // Fuel Bar
   float fuelPct = boat != null ? boat.FuelPercent : 100f;
   GUI.Label(new Rect(card1.x + 10f * scale, rowY, 70f * scale, 18f * scale), "动力燃料", labelStyle);
   Rect fuelBarRect = new Rect(card1.x + 85f * scale, rowY + 3f * scale, card1.width - 95f * scale, 14f * scale);
   GUI.DrawTexture(fuelBarRect, barBgTex);
   Rect fuelFillRect = new Rect(fuelBarRect.x, fuelBarRect.y, fuelBarRect.width * Mathf.Clamp01(fuelPct / 100f), fuelBarRect.height);
   GUI.DrawTexture(fuelFillRect, barFuelTex);
   GUI.Label(new Rect(card1.x + 85f * scale, rowY, card1.width - 95f * scale, 18f * scale), $"{fuelPct:F0} %", valueStyle);
   rowY += rowH;

   // Crew count & departure state
   GUI.Label(new Rect(card1.x + 10f * scale, rowY, 70f * scale, 18f * scale), "船员编制", labelStyle);
   GUI.Label(new Rect(card1.x + 85f * scale, rowY, card1.width - 95f * scale, 18f * scale), $"{crew.Count} / {boat.CrewCapacity} 人 (待登船 {pending.Count})", valueStyle);
   rowY += rowH;

   GUI.Label(new Rect(card1.x + 10f * scale, rowY, 70f * scale, 18f * scale), "航向状态", labelStyle);
   string statusStr = route != null && route.Count > 0 ? "航向执行中" : (NearbyDock() != null ? "已靠泊码头" : "海面待命");
   GUI.Label(new Rect(card1.x + 85f * scale, rowY, card1.width - 95f * scale, 18f * scale), statusStr, valueStyle);

   // Card 2: Mission Logs & Orders
   float card2Y = card1.yMax + 8f * scale;
   float cardH2 = 82f * scale;
   Rect card2 = new Rect(area.x, card2Y, area.width, cardH2);
   GUI.Box(card2, GUIContent.none, cardStyle);

   GUI.Label(new Rect(card2.x + 10f * scale, card2.y + 6f * scale, card2.width - 20f * scale, 18f * scale), "航行指令简讯", labelStyle);
   GUI.Label(new Rect(card2.x + 10f * scale, card2.y + 26f * scale, card2.width - 20f * scale, 48f * scale), message, subtitleStyle);
  }

  void DrawBoatCrewTab(Rect area, float scale)
  {
   float cardH1 = 80f * scale;
   Rect card1 = new Rect(area.x, area.y, area.width, cardH1);
   GUI.Box(card1, GUIContent.none, cardStyle);

   GUI.Label(new Rect(card1.x + 10f * scale, card1.y + 6f * scale, card1.width - 20f * scale, 18f * scale), $"已登船人员 ({crew.Count}/{boat.CrewCapacity})", labelStyle);
   float rowY = card1.y + 26f * scale;
   if (crew.Count == 0)
   {
    GUI.Label(new Rect(card1.x + 10f * scale, rowY, card1.width - 20f * scale, 18f * scale), "当前船内暂无常驻船员", subtitleStyle);
   }
   else
   {
    for (int i = 0; i < Mathf.Min(crew.Count, 2); i++)
    {
     if (crew[i] != null)
     {
      GUI.Label(new Rect(card1.x + 10f * scale, rowY, card1.width - 20f * scale, 18f * scale), $"⚓ {crew[i].ResidentName}  ·  船员执勤中", valueStyle);
      rowY += 20f * scale;
     }
    }
   }

   float card2Y = card1.yMax + 8f * scale;
   float cardH2 = 72f * scale;
   Rect card2 = new Rect(area.x, card2Y, area.width, cardH2);
   GUI.Box(card2, GUIContent.none, cardStyle);

   GUI.Label(new Rect(card2.x + 10f * scale, card2.y + 6f * scale, card2.width - 20f * scale, 18f * scale), $"待登船响应人员 ({pending.Count})", labelStyle);
   rowY = card2.y + 26f * scale;
   if (pending.Count == 0)
   {
    GUI.Label(new Rect(card2.x + 10f * scale, rowY, card2.width - 20f * scale, 18f * scale), "暂无奔跑向码头的人员", subtitleStyle);
   }
   else
   {
    foreach (var p in pending)
    {
     if (p != null)
     {
      GUI.Label(new Rect(card2.x + 10f * scale, rowY, card2.width - 20f * scale, 18f * scale), $"🏃 {p.ResidentName}  ·  正赶往码头登船", valueStyle);
      rowY += 20f * scale;
      break;
     }
    }
   }

   // Action buttons
   float bW = (area.width - 8f * scale) * 0.5f;
   float bH = 32f * scale;
   float bY = area.yMax - bH - 4f * scale;

   if (GUI.Button(new Rect(area.x, bY, bW, bH), "安排本岛人员登船", buttonStyle))
   {
    BoardPeople();
   }

   if (GUI.Button(new Rect(area.x + bW + 8f * scale, bY, bW, bH), "靠岸下船", buttonStyle))
   {
    var dock = NearbyDock();
    if (dock != null && route == null && pending.Count == 0)
    {
     Vector3 p = dock.TransformPoint(new Vector3(0, 0, 2));
     var grid = host.ConstructionGrid;
     var local = grid.Root.InverseTransformPoint(p);
     if (grid.TrySample(local.x, local.z, out var ground, out _))
     {
      foreach (var person in crew)
      {
       if (person != null) person.LeaveBoat(grid.Root.TransformPoint(ground));
      }
      crew.Clear();
     }
    }
   }
  }

  void DrawBoatCargoTab(Rect area, float scale)
  {
   float cardH1 = 68f * scale;
   Rect card1 = new Rect(area.x, area.y, area.width, cardH1);
   GUI.Box(card1, GUIContent.none, cardStyle);

   float rowY = card1.y + 6f * scale;
   for (int i = 0; i < 2; i++)
   {
    string slotStr = cargo[i].amount > 0 ? $"{ResourceName(cargo[i].type)}  {cargo[i].amount:F0} / 100" : "空置 (可装载)";
    GUI.Label(new Rect(card1.x + 10f * scale, rowY, 70f * scale, 22f * scale), $"货舱 {i + 1}", labelStyle);
    GUI.Label(new Rect(card1.x + 85f * scale, rowY, card1.width - 95f * scale, 22f * scale), slotStr, valueStyle);
    rowY += 24f * scale;
   }

   // Loading Controls
   float card2Y = card1.yMax + 8f * scale;
   float cardH2 = 120f * scale;
   Rect card2 = new Rect(area.x, card2Y, area.width, cardH2);
   GUI.Box(card2, GUIContent.none, cardStyle);

   GUI.Label(new Rect(card2.x + 10f * scale, card2.y + 6f * scale, card2.width - 20f * scale, 18f * scale), "码头物资装卸调度", labelStyle);

   float btnRowY = card2.y + 28f * scale;
   float btnW = (card2.width - 28f * scale) * 0.5f;

   if (GUI.Button(new Rect(card2.x + 10f * scale, btnRowY, btnW, 26f * scale), slotChoice == 0 ? "● 选择货舱 1" : "○ 选择货舱 1", buttonStyle))
   {
    slotChoice = 0;
   }
   if (GUI.Button(new Rect(card2.x + 18f * scale + btnW, btnRowY, btnW, 26f * scale), slotChoice == 1 ? "● 选择货舱 2" : "○ 选择货舱 2", buttonStyle))
   {
    slotChoice = 1;
   }

   btnRowY += 30f * scale;
   string currentResName = ResourceName(Types[resourceChoice % Types.Length]);
   if (GUI.Button(new Rect(card2.x + 10f * scale, btnRowY, card2.width - 20f * scale, 26f * scale), $"品类切换：【{currentResName}】(点击循环切换)", buttonStyle))
   {
    resourceChoice = (resourceChoice + 1) % Types.Length;
   }

   btnRowY += 30f * scale;
   if (GUI.Button(new Rect(card2.x + 10f * scale, btnRowY, btnW, 26f * scale), "装载 100", buttonStyle))
   {
    message = LoadCargo(slotChoice, Types[resourceChoice % Types.Length], 100) ? "物资已成功装船。" : "无法装载：需停靠码头、货舱类型一致且有剩余物资。";
   }
   if (GUI.Button(new Rect(card2.x + 18f * scale + btnW, btnRowY, btnW, 26f * scale), "卸下物资", buttonStyle))
   {
    UnloadCargo();
   }
  }

  void DrawPeoplePanel(Rect panelRect, float scale)
  {
   // 1. Header
   GUI.Label(new Rect(panelRect.x + 16f * scale, panelRect.y + 11f * scale, 24f * scale, 24f * scale), "🧑", titleStyle);
   GUI.Label(new Rect(panelRect.x + 44f * scale, panelRect.y + 9f * scale, panelRect.width - 150f * scale, 24f * scale), $"已选岛民 ({selectedPeople.Count} 人)", titleStyle);
   GUI.Label(new Rect(panelRect.x + 44f * scale, panelRect.y + 29f * scale, panelRect.width - 150f * scale, 16f * scale), "[岛屿开拓者]", subtitleStyle);

   // Drag hint
   GUI.Label(new Rect(panelRect.xMax - 120f * scale, panelRect.y + 13f * scale, 82f * scale, 18f * scale), "⋮⋮ 按住拖拽", subtitleStyle);

   // Close Button
   Rect closeRect = new Rect(panelRect.xMax - 34f * scale, panelRect.y + 12f * scale, 22f * scale, 22f * scale);
   if (GUI.Button(closeRect, "×", closeButtonStyle))
   {
    selected = false;
    selectedPeople.Clear();
    return;
   }

   // Divider below header
   GUI.color = new Color(0.85f, 0.70f, 0.38f, 0.35f);
   GUI.DrawTexture(new Rect(panelRect.x + 12f * scale, panelRect.y + 48f * scale, panelRect.width - 24f * scale, 1f), Texture2D.whiteTexture);
   GUI.color = Color.white;

   // 2. Tab Bar
   float tabY = panelRect.y + 54f * scale;
   float tabH = 27f * scale;
   float tabGap = 4f * scale;
   float tabW = (panelRect.width - 24f * scale - tabGap) * 0.5f;

   for (int i = 0; i < PeopleTabs.Length; i++)
   {
    Rect tRect = new Rect(panelRect.x + 12f * scale + i * (tabW + tabGap), tabY, tabW, tabH);
    bool isActive = vesselTab == i;
    GUIStyle tStyle = isActive ? activeTabStyle : inactiveTabStyle;

    if (GUI.Button(tRect, PeopleTabs[i], tStyle))
    {
     vesselTab = i;
    }

    if (isActive)
    {
     GUI.color = new Color(1.0f, 0.88f, 0.45f, 0.95f);
     GUI.DrawTexture(new Rect(tRect.x + 6f * scale, tRect.yMax - 2f * scale, tRect.width - 12f * scale, 2f * scale), Texture2D.whiteTexture);
     GUI.color = Color.white;
    }
   }

   // 3. Content
   float contentY = tabY + tabH + 8f * scale;
   Rect contentArea = new Rect(panelRect.x + 12f * scale, contentY, panelRect.width - 24f * scale, panelRect.yMax - contentY - 12f * scale);

   if (vesselTab == 0)
   {
    float cardH = contentArea.height - 40f * scale;
    Rect card1 = new Rect(contentArea.x, contentArea.y, contentArea.width, cardH);
    GUI.Box(card1, GUIContent.none, cardStyle);

    float rowY = card1.y + 8f * scale;
    int count = 0;
    foreach (var p in selectedPeople)
    {
     if (p != null)
     {
      string pState = p.IsRunning ? "奔跑执行中" : "待命休息";
      GUI.Label(new Rect(card1.x + 10f * scale, rowY, card1.width - 20f * scale, 20f * scale), $"🧑 {p.ResidentName}  ·  {pState}", valueStyle);
      rowY += 22f * scale;
      count++;
      if (count >= 6) break;
     }
    }
   }
   else
   {
    float cardH = contentArea.height - 40f * scale;
    Rect card1 = new Rect(contentArea.x, contentArea.y, contentArea.width, cardH);
    GUI.Box(card1, GUIContent.none, cardStyle);

    GUI.Label(new Rect(card1.x + 12f * scale, card1.y + 12f * scale, card1.width - 24f * scale, 45f * scale), "右键点击岛屿陆地指派移动地点，点击靠泊的搜救码头可登船出海。", labelStyle);
   }

   // Cancel Button at bottom
   float bH = 30f * scale;
   float bY = contentArea.yMax - bH;
   if (GUI.Button(new Rect(contentArea.x, bY, contentArea.width, bH), "取消选择", buttonStyle))
   {
    selected = false;
    selectedPeople.Clear();
   }
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

  static Texture2D MakeSolidTexture(Color c)
  {
   var t = new Texture2D(1, 1, TextureFormat.RGBA32, false);
   t.SetPixel(0, 0, c);
   t.Apply();
   return t;
  }

  static Texture2D MakeOpaqueConsoleTexture(int size, Color face, Color border, float borderWidth, float cornerRadius)
  {
   var texture = new Texture2D(size, size, TextureFormat.RGBA32, false)
   {
       hideFlags = HideFlags.HideAndDontSave,
       filterMode = FilterMode.Bilinear,
       wrapMode = TextureWrapMode.Clamp
   };
   Color[] pixels = new Color[size * size];
   float half = size * 0.5f;

   for (int y = 0; y < size; y++)
   {
       float ny = y / (float)(size - 1);
       for (int x = 0; x < size; x++)
       {
           float qx = Mathf.Abs(x + 0.5f - half) - (half - cornerRadius);
           float qy = Mathf.Abs(y + 0.5f - half) - (half - cornerRadius);
           float outside = Mathf.Sqrt(Mathf.Max(qx, 0f) * Mathf.Max(qx, 0f) + Mathf.Max(qy, 0f) * Mathf.Max(qy, 0f));
           float dist = outside + Mathf.Min(Mathf.Max(qx, qy), 0f) - cornerRadius;

           float alpha = Mathf.Clamp01(0.5f - dist);
           float edge = Mathf.Clamp01((dist + borderWidth) / borderWidth);

           float sheen = Mathf.Lerp(0.92f, 1.10f, ny);
           Color faceCol = new Color(face.r * sheen, face.g * sheen, face.b * sheen, 0.98f);

           float topHighlight = ny > 0.88f ? 1.30f : 1.0f;
           Color borderCol = new Color(border.r * topHighlight, border.g * topHighlight, border.b * topHighlight, border.a);

           Color c = Color.Lerp(faceCol, borderCol, edge);
           c.a *= alpha;
           pixels[y * size + x] = c;
       }
   }

   texture.SetPixels(pixels);
   texture.Apply(false, false);
   return texture;
  }
 }
}
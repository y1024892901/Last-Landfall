using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace LastLandfall.Prototype
{
    [Serializable]
    public sealed class LighthouseProgressSave
    {
        public int completedStage;
        public int workingStage = -1;
        public float progress;
    }

    public sealed class LighthouseSite : MonoBehaviour
    {
        public static readonly Vector3 SitePosition = new Vector3(112f,-.92f,26f);
        public static readonly string[] StageNames = { "陨石撞毁基址", "废墟清理完成", "新地基浇筑", "下段塔身", "中段塔身", "上段塔身", "灯室与透镜", "设备房与供电", "首次点亮" };
        public static readonly int[] WoodCosts = { 0,20,60,45,45,50,40,35,0 };
        public static readonly int[] MetalCosts = { 0,0,12,8,10,12,25,20,0 };
        public static readonly float[] Durations = { 0,20,30,45,45,45,35,30,5 };
        internal static readonly string[] InspectorTabs = { "工程", "阶段" };
        [SerializeField,Range(0,8)] int previewStage;
        [SerializeField,Range(0,8)] int completedStage;
        [SerializeField] bool stagePreview;
        [SerializeField] int workingStage = -1;
        [SerializeField,Range(0,1)] float constructionProgress;
        GameObject root,visual,beamRoot;
        Light beacon,lanternGlow;
        Action<Vector3> focus;
        Func<int,bool> spend;
        Material beamMaterial;
        Material lanternCoreMaterial;
        Mesh beamMesh;
        bool initialized;
        GUIStyle launcherStyle;
        int renderedStage=-1;
        float beamAngle;
        string message="先投入工具与木材，拆解陨石撞毁的地基，再原址重建。";
        public int PreviewStage => previewStage;
        public int CompletedStage => completedStage;
        public int WorkingStage => workingStage;
        public float ConstructionProgress => constructionProgress;
        public bool IsPanelOpen
        {
            get => BuildingInspectorUI.IsInspecting(this);
            set
            {
                if (value && initialized) BuildingInspectorUI.Inspect(this);
                else if (IsPanelOpen) BuildingInspectorUI.Close();
            }
        }
        public bool PreviewEnabled => stagePreview;
        public Vector3 WorldPosition => root!=null?root.transform.position:SitePosition;
        public Vector3 FocusPosition => WorldPosition+Vector3.up*27f;
        public void Initialize(Transform parent,Action<Vector3> focusCamera,Func<int> researchProvider,Func<int,bool> spendWood)
        {
            if(initialized)return;
            var scenePreview=GameObject.Find("Lighthouse | Scene Preview");
            if(scenePreview!=null)scenePreview.SetActive(false);
            focus=focusCamera;spend=spendWood;
            root=new GameObject("Lighthouse | detached reef construction site");
            root.transform.SetParent(parent,false);root.transform.localPosition=SitePosition;
            visual=LighthouseModelLibrary.Create(root.transform);
            if(visual==null){Debug.LogError("Tripo 灯塔模块尚未导入。");return;}
            stagePreview=false;initialized=true;Refresh();
        }
        public void SetPreviewStage(int stage)
        {
            if(stage<0||stage>=StageNames.Length)throw new ArgumentOutOfRangeException(nameof(stage));
            previewStage=stage;stagePreview=true;Refresh();
        }
        public void SetPreviewMode(bool enabled){stagePreview=enabled;Refresh();}
        public void JumpToStage(int stage)
        {
            if(stage<0||stage>=StageNames.Length)throw new ArgumentOutOfRangeException(nameof(stage));
            completedStage=stage;workingStage=-1;constructionProgress=0f;stagePreview=false;
            message="调试跳转至："+StageNames[stage]+"。未消耗资源，当前施工已停止。";
            Refresh();
        }
        public bool TryBuildNextStage()
        {
            if(!initialized)return false;
            if(workingStage>=0){message="当前工序尚未完成。";return false;}
            int next=completedStage+1;
            if(next>=StageNames.Length){message="灯塔已点亮，群岛航标正在运转。";return false;}
            var resources=ColonyResourceManager.Instance;
            if(MetalCosts[next]>0&&(resources==null||resources.Metal<MetalCosts[next])){message="金属不足，需要 "+MetalCosts[next]+"。";return false;}
            if(next==8&&(resources==null||resources.Fuel<5f)){message="首次启动需要燃料 5。";return false;}
            if(spend==null||!spend(WoodCosts[next])){message="木材不足，需要 "+WoodCosts[next]+"。";return false;}
            // Validate the entire cost before spending, so a failed request never partially charges resources.
            if(MetalCosts[next]>0)resources.TrySpend(ResourceType.Metal,MetalCosts[next]);
            if(next==8)resources.TrySpend(ResourceType.Fuel,5f);
            workingStage=next;constructionProgress=0f;stagePreview=false;
            message=next==1?"已投入清理物资，正在分批拆解残破地基。":"物资已投入，开始："+StageNames[next];
            Refresh();return true;
        }
        public void AdvanceConstruction(float seconds)
        {
            if(!initialized||workingStage<1||seconds<=0f)return;
            constructionProgress=Mathf.Clamp01(constructionProgress+seconds/Durations[workingStage]);
            if(constructionProgress>=1f)
            {
                completedStage=workingStage;workingStage=-1;constructionProgress=0f;
                if(completedStage==1)
                {
                    var resources=ColonyResourceManager.Instance;
                    if(resources!=null){resources.Add(ResourceType.Wood,15);resources.Add(ResourceType.Metal,12);}
                    message="废墟已清走，回收木材 15、金属 12。下一步修建新地基。";
                }
                else message=completedStage==8?"航标首次点亮！救援船现在有了返回群岛的方向。":"已完成："+StageNames[completedStage];
            }
            Refresh();
        }
        public LighthouseProgressSave CaptureProgress()=>new LighthouseProgressSave{completedStage=completedStage,workingStage=workingStage,progress=constructionProgress};
        public void RestoreProgress(LighthouseProgressSave state)
        {
            completedStage=Mathf.Clamp(state!=null?state.completedStage:0,0,8);
            workingStage=state!=null&&state.workingStage==completedStage+1&&state.workingStage<=8?state.workingStage:-1;
            constructionProgress=workingStage>=0?Mathf.Clamp01(state.progress):0f;
            stagePreview=false;message=workingStage>=0?"已恢复施工："+StageNames[workingStage]:"已恢复灯塔进度："+StageNames[completedStage];Refresh();
        }
        void Refresh()
        {
            if(!initialized)return;
            int stage=stagePreview?previewStage:completedStage;
            LighthouseModelLibrary.SetStage(visual,stage,stagePreview?-1:workingStage,constructionProgress);
            if(stage==8&&beamRoot==null)CreateBeacon();
            if(stage!=8&&beamRoot!=null){RemoveObject(beamRoot);beamRoot=null;beacon=null;}
            renderedStage=stage;
        }
        void CreateBeacon()
        {
            beamRoot=new GameObject("Rotating lighthouse beacon");beamRoot.transform.SetParent(root.transform,false);
            beamRoot.transform.localPosition=new Vector3(-.1f,54.2f,-.1f);
            beacon=beamRoot.AddComponent<Light>();beacon.type=LightType.Spot;beacon.color=new Color(1f,.86f,.62f);
            beacon.range=280;beacon.spotAngle=22;beacon.intensity=24;beacon.shadows=LightShadows.None;
            var glow=new GameObject("Lantern glow");glow.transform.SetParent(beamRoot.transform,false);
            lanternGlow=glow.AddComponent<Light>();lanternGlow.type=LightType.Point;
            lanternGlow.color=beacon.color;lanternGlow.range=12;lanternGlow.intensity=4;
            lanternGlow.shadows=LightShadows.None;
            var core=GameObject.CreatePrimitive(PrimitiveType.Sphere);
            core.name="Lighthouse luminous lens core";core.transform.SetParent(beamRoot.transform,false);
            core.transform.localScale=Vector3.one*1.15f;
            var coreCollider=core.GetComponent<Collider>();if(coreCollider!=null)RemoveObject(coreCollider);
            lanternCoreMaterial=new Material(Shader.Find("Universal Render Pipeline/Lit"));
            lanternCoreMaterial.SetColor("_BaseColor",new Color(1f,.92f,.68f));
            lanternCoreMaterial.EnableKeyword("_EMISSION");
            lanternCoreMaterial.SetColor("_EmissionColor",new Color(6f,4.7f,2.5f));
            core.GetComponent<Renderer>().sharedMaterial=lanternCoreMaterial;
            Shader shader=Shader.Find("LastLandfall/Lighthouse Beam");
            if(shader!=null)
            {
                if(beamMaterial==null)beamMaterial=new Material(shader);
                beamMaterial.SetFloat("_BeamLength",260f);beamMaterial.SetFloat("_BeamHalfWidth",28f);
                if(beamMesh==null)beamMesh=new Mesh{name="Lighthouse atmosphere beam"};
                beamMesh.vertices=new[]{Vector3.zero,new Vector3(-28,-3,260),new Vector3(28,-3,260),new Vector3(0,8,260)};
                beamMesh.triangles=new[]{0,1,2,0,2,3,0,3,1};beamMesh.RecalculateNormals();
                beamRoot.AddComponent<MeshFilter>().sharedMesh=beamMesh;beamRoot.AddComponent<MeshRenderer>().sharedMaterial=beamMaterial;
            }
        }
        // Kept for legacy scene setup callers; preserve source textures during URP conversion.
        public static void ConvertMaterials(GameObject model)
        {
            foreach(var r in model.GetComponentsInChildren<Renderer>())
            {
                var slots=r.sharedMaterials;
                for(int i=0;i<slots.Length;i++)
                {
                    var source=slots[i];if(source==null||source.shader.name=="Universal Render Pipeline/Lit")continue;
                    var m=new Material(Shader.Find("Universal Render Pipeline/Lit")){name=source.name+" | URP"};
                    m.SetColor("_BaseColor",source.color);if(source.mainTexture!=null)m.SetTexture("_BaseMap",source.mainTexture);slots[i]=m;
                }
                r.sharedMaterials=slots;
            }
        }
        void Update()
        {
            if(!initialized)return;
            var menu=FindAnyObjectByType<MainMenuController>();
            if(menu!=null&&menu.IsBlocking)return;
            var weather=GetComponent<IslandWeatherSystem>();
            AdvanceConstruction(Time.deltaTime*(weather!=null?Mathf.Max(0f,weather.SimulationSpeed):1f));
            if(beamRoot!=null)
            {
                beamAngle=(beamAngle+Time.deltaTime*12f)%360f;beamRoot.transform.localRotation=Quaternion.Euler(0,beamAngle,0);
                float hour=weather!=null?weather.TimeOfDayHours:20f;float night=hour<6||hour>18?1f:.3f;
                beacon.intensity=24*night;if(lanternGlow!=null)lanternGlow.intensity=4*night;
                if(beamMaterial!=null)beamMaterial.SetFloat("_Visibility",night);
            }
            if (!ColonyModalDialog.IsDialogOpen && Input.GetKeyDown(KeyCode.L))
            {
                IsPanelOpen = true;
                focus?.Invoke(FocusPosition);
            }
        }

        internal bool Hit(Ray ray, ref float nearest) =>
            initialized && visual != null && BuildingInspectorUI.Hit(visual.transform, ray, ref nearest);

        internal void DrawLauncher()
        {
            if (!initialized) return;
            if (launcherStyle == null)
            {
                launcherStyle = new GUIStyle(GUI.skin.button) { fontSize = 12, alignment = TextAnchor.MiddleCenter };
                HudTheme.StyleButton(launcherStyle);
            }
            if (GUI.Button(BuildPlacementPrototype.GetLighthouseLauncherRect(), "灯塔重建  [L]", launcherStyle))
                IsPanelOpen = !IsPanelOpen;
        }

        internal void DrawInspectionPage(BuildingInspectorUI panel, int page)
        {
            if (page == 1)
            {
                panel.Note("点击阶段可直接跳转。调试跳转不消耗资源。");
                for (int i = 0; i < StageNames.Length; i++)
                {
                    string status = i == workingStage ? "施工中" : i <= completedStage ? "已完成" : "待建设";
                    if (i == 0) status = completedStage == 0 ? "初始现场" : "已清理";
                    if (panel.ActionButton($"{i:00}  {StageNames[i]}  ·  {status}")) JumpToStage(i);
                }
                panel.Note(message);
                return;
            }

            panel.Row("当前阶段", stagePreview ? StageNames[previewStage] + " · 预览" : StageNames[completedStage]);
            int next = completedStage + 1;
            bool hasNext = next < StageNames.Length;
            if (workingStage >= 0)
                panel.Meter("施工进度", $"{StageNames[workingStage]} · {constructionProgress:P0}", constructionProgress);
            else if (hasNext)
            {
                panel.Row("下一阶段", StageNames[next]);
                string materials = next == StageNames.Length - 1 ? "5 燃料" : $"{WoodCosts[next]} 木材";
                if (MetalCosts[next] > 0) materials += $" · {MetalCosts[next]} 金属";
                panel.Row("所需物资", materials);
            }
            else panel.Row("航标", "已点亮");

            GUILayout.BeginHorizontal();
            if (hasNext && panel.ActionButton(next == 1 ? "清理废墟" : next == StageNames.Length - 1 ? "首次点亮" : "开始施工",
                    workingStage < 0)) TryBuildNextStage();
            if (panel.ActionButton("定位灯塔")) focus?.Invoke(FocusPosition);
            GUILayout.EndHorizontal();
            panel.Note(message);
        }
        static void RemoveObject(UnityEngine.Object obj){if(obj==null)return;if(obj is GameObject go)go.SetActive(false);if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj);}
        void OnDestroy(){RemoveObject(root);RemoveObject(beamMaterial);RemoveObject(lanternCoreMaterial);RemoveObject(beamMesh);}
    }
}

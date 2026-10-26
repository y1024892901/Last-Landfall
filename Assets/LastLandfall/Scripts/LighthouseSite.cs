using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace LastLandfall.Prototype
{
    public sealed class LighthouseSite : MonoBehaviour
    {
        public static readonly Vector3 SitePosition = new Vector3(112f,-.92f,26f);
        public static readonly string[] StageNames = { "旧基址", "石砌基座", "塔身施工", "灯室安装", "航标点亮" };
        public static readonly int[] RequiredResearch = { 0,1,2,4,7 };
        public static readonly int[] WoodCosts = { 0,40,90,140,200 };
        [SerializeField,Range(0,4)] int previewStage;
        [SerializeField,Range(0,4)] int completedStage;
        [SerializeField] bool stagePreview = true;
        GameObject root,visual,beamRoot;
        Light beacon;
        Action<Vector3> focus;
        Func<int> research;
        Func<int,bool> spend;
        Material beamMaterial;
        readonly List<Material> ownedMaterials = new List<Material>();
        readonly List<Mesh> ownedMeshes = new List<Mesh>();
        bool panelOpen,initialized;
        GUIStyle panel,label,small,title,button,chosen;
        int renderedStage=-1;
        float fade;
        string message="可直接选择阶段预览，正式建设按科技阶段解锁。";
        public int PreviewStage => previewStage;
        public int CompletedStage => completedStage;
        public bool IsPanelOpen
        {
            get => panelOpen;
            set { panelOpen=value; if(value)GetComponent<BuildPlacementPrototype>()?.CloseTransientHudMenus(); }
        }
        public bool PreviewEnabled => stagePreview;
        public Vector3 WorldPosition => root != null ? root.transform.position : SitePosition;
        public void Initialize(Transform parent,Action<Vector3> focusCamera,Func<int> researchProvider,Func<int,bool> spendWood)
        {
            if(initialized)return;
            GameObject scenePreview=GameObject.Find("Lighthouse | Scene Preview");
            if(scenePreview!=null)scenePreview.SetActive(false);
            focus=focusCamera;research=researchProvider;spend=spendWood;
            root=new GameObject("Lighthouse | detached reef construction site");
            root.transform.SetParent(parent,false);root.transform.localPosition=SitePosition;
            var prefab=Resources.Load<GameObject>("Models/Lighthouse/Lighthouse_Reef");
            if(prefab==null){Debug.LogError("灯塔礁石模型未导入。");return;}
            var reef=Instantiate(prefab,root.transform,false);ConvertOwnedMaterials(reef);
            initialized=true;SetPreviewStage(previewStage);
        }
        public void SetPreviewStage(int stage)
        {
            if(stage<0||stage>=StageNames.Length)throw new ArgumentOutOfRangeException(nameof(stage));
            previewStage=stage;stagePreview=true;Refresh();
        }
        public void SetPreviewMode(bool enabled)
        {
            stagePreview=enabled;Refresh();
        }
        public bool TryBuildNextStage()
        {
            int next=completedStage+1;
            if(next>=StageNames.Length){message="灯塔已全部建成。";return false;}
            if(research==null||research()<RequiredResearch[next]){message="需要科技阶段 "+RequiredResearch[next]+" 才能建设。";return false;}
            if(spend==null||!spend(WoodCosts[next])){message="木材不足，需要 "+WoodCosts[next]+"。";return false;}
            completedStage=next;stagePreview=false;Refresh();message="已完成："+StageNames[next];return true;
        }
        void RemoveObject(UnityEngine.Object obj)
        {
            if(obj==null)return;
            if(obj is GameObject go)go.SetActive(false);
            if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj);
        }
        void Refresh()
        {
            if(!initialized)return;
            int stage=stagePreview?previewStage:completedStage;
            if(stage==renderedStage)return;
            var prefab=Resources.Load<GameObject>("Models/Lighthouse/Lighthouse_Stage_"+stage);
            if(prefab==null){Debug.LogError("灯塔阶段模型缺失："+stage);return;}
            RemoveObject(visual);RemoveObject(beamRoot);beacon=null;
            visual=Instantiate(prefab,root.transform,false);visual.name="Lighthouse stage "+stage+" | "+StageNames[stage];
            ConvertOwnedMaterials(visual);renderedStage=stage;
            if(stage==4)CreateBeacon();
        }
        void CreateBeacon()
        {
            beamRoot=new GameObject("Rotating lighthouse beacon");beamRoot.transform.SetParent(root.transform,false);
            beamRoot.transform.localPosition=new Vector3(0,18.8f,0);
            beacon=beamRoot.AddComponent<Light>();beacon.type=LightType.Spot;
            beacon.color=new Color(1f,.82f,.48f);beacon.range=85;beacon.spotAngle=19;
            beacon.intensity=8;beacon.shadows=LightShadows.None;
            Shader shader=Shader.Find("LastLandfall/Lighthouse Beam");
            if(shader!=null)
            {
                if(beamMaterial==null)beamMaterial=new Material(shader);
                var mesh=new Mesh{name="Lighthouse atmosphere beam"};
                mesh.vertices=new[]{Vector3.zero,new Vector3(-7,-.65f,65),new Vector3(7,-.65f,65),new Vector3(0,2.4f,65)};
                mesh.triangles=new[]{0,1,2,0,2,3,0,3,1};mesh.RecalculateNormals();
                ownedMeshes.Add(mesh);
                var filter=beamRoot.AddComponent<MeshFilter>();filter.sharedMesh=mesh;
                beamRoot.AddComponent<MeshRenderer>().sharedMaterial=beamMaterial;
            }
        }
        public static void ConvertMaterials(GameObject model)
        {
            var converted=new Dictionary<Material,Material>();
            foreach(var renderer in model.GetComponentsInChildren<Renderer>())
            {
                var values=renderer.sharedMaterials;
                for(int i=0;i<values.Length;i++)
                {
                    var source=values[i];if(source==null)continue;
                    if(converted.TryGetValue(source,out Material cached)){values[i]=cached;continue;}
                    var mat=new Material(Shader.Find("Universal Render Pipeline/Lit"));
                    mat.name=source.name+" | URP";
                    mat.SetColor("_BaseColor",source.HasProperty("_BaseColor")?source.GetColor("_BaseColor"):source.color);
                    mat.SetFloat("_Smoothness",.22f);
                    if(source.name.Contains("lantern glazing"))
                    {
                        Color color=mat.GetColor("_BaseColor");color.a=.27f;mat.SetColor("_BaseColor",color);
                        mat.SetFloat("_Surface",1);mat.SetOverrideTag("RenderType","Transparent");
                        mat.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
                        mat.SetInt("_SrcBlend",(int)BlendMode.SrcAlpha);mat.SetInt("_DstBlend",(int)BlendMode.OneMinusSrcAlpha);
                        mat.SetInt("_ZWrite",0);mat.renderQueue=3000;
                    }
                    converted.Add(source,mat);
                    values[i]=mat;
                }
                renderer.sharedMaterials=values;
            }
        }
        void ConvertOwnedMaterials(GameObject model)
        {
            ConvertMaterials(model);
            foreach(var renderer in model.GetComponentsInChildren<Renderer>())
                foreach(var material in renderer.sharedMaterials)
                    if(material!=null&&!ownedMaterials.Contains(material))ownedMaterials.Add(material);
        }
        void Update()
        {
            if(!initialized)return;
            Refresh();
            fade=Mathf.MoveTowards(fade,panelOpen?1:0,Time.unscaledDeltaTime*8);
            if(beamRoot!=null)
            {
                beamRoot.transform.localRotation=Quaternion.Euler(0,Time.unscaledTime*12,0);
                var weather=GetComponent<IslandWeatherSystem>();
                float hour=weather!=null?weather.TimeOfDayHours:20;
                float night=hour<6||hour>18?1:.32f;
                beacon.intensity=8*night;
                if(beamMaterial!=null)beamMaterial.SetFloat("_Visibility",night);
            }
            if(Input.GetKeyDown(KeyCode.L)){IsPanelOpen=true;focus?.Invoke(WorldPosition+Vector3.up*8);}
        }
        float Scale => Mathf.Clamp(Screen.height/900f,.72f,1.15f);
        public Rect LauncherRect => new Rect(Screen.width-164*Scale,Mathf.Clamp(Screen.height*.072f,52,76)+12*Scale,144*Scale,36*Scale);
        public Rect PanelRect => new Rect(Mathf.Max(12,Screen.width-500*Scale),LauncherRect.y,316*Scale,390*Scale);
        public bool ContainsPointer(Vector2 point) => initialized && (LauncherRect.Contains(point)||(panelOpen&&PanelRect.Contains(point)));
        void EnsureStyles()
        {
            if(panel!=null)return;
            panel=new GUIStyle(GUI.skin.box);HudTheme.StylePanel(panel);
            label=HudTheme.Label(13,HudTheme.Text);small=HudTheme.Label(11,HudTheme.Muted);
            title=HudTheme.Label(18,HudTheme.Text,true);
            button=new GUIStyle(GUI.skin.button){fontSize=12,alignment=TextAnchor.MiddleLeft,padding=new RectOffset(12,8,4,4)};HudTheme.StyleButton(button);
            chosen=new GUIStyle(button);HudTheme.StyleButton(chosen,true);
        }
        void OnGUI()
        {
            var menu=FindAnyObjectByType<MainMenuController>();
            if(!initialized||(menu!=null&&menu.IsBlocking))return;
            EnsureStyles();float s=Scale;label.fontSize=Mathf.RoundToInt(13*s);small.fontSize=Mathf.RoundToInt(11*s);
            if(GUI.Button(LauncherRect,"◈  灯塔基址  /  阶段",button))IsPanelOpen=!panelOpen;
            if(!panelOpen)return;
            Rect p=PanelRect;GUI.Box(p,GUIContent.none,panel);
            GUI.Label(new Rect(p.x+18*s,p.y+15*s,p.width-60*s,28*s),"群岛航标",title);
            if(GUI.Button(new Rect(p.xMax-38*s,p.y+12*s,26*s,26*s),"×",button))panelOpen=false;
            GUI.Label(new Rect(p.x+18*s,p.y+47*s,p.width-36*s,22*s),"独立礁石 · 远海救援灯塔",small);
            for(int i=0;i<StageNames.Length;i++)
            {
                string info=i==0?"现有基址":"科技 "+RequiredResearch[i]+"  ·  木材 "+WoodCosts[i];
                Rect row=new Rect(p.x+16*s,p.y+(80+i*39)*s,p.width-32*s,34*s);
                bool selected=(stagePreview?previewStage:completedStage)==i;
                if(GUI.Button(row,(i+1).ToString("00")+"   "+StageNames[i]+"       "+info,selected?chosen:button))SetPreviewStage(i);
            }
            if(GUI.Button(new Rect(p.x+16*s,p.y+287*s,135*s,32*s),"定位灯塔  [L]",button))focus?.Invoke(WorldPosition+Vector3.up*8);
            if(GUI.Button(new Rect(p.x+160*s,p.y+287*s,140*s,32*s),stagePreview?"退出阶段预览":"建设下一阶段",button))
            {if(stagePreview)SetPreviewMode(false);else TryBuildNextStage();}
            GUI.Label(new Rect(p.x+18*s,p.y+330*s,p.width-36*s,48*s),message,small);
        }
        void OnDestroy()
        {
            if(root!=null)
            {
                RemoveObject(root);
            }
            foreach(var material in ownedMaterials)RemoveObject(material);
            foreach(var mesh in ownedMeshes)RemoveObject(mesh);
            RemoveObject(beamMaterial);
        }
    }
}

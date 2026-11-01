using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    public static class LighthouseModelLibrary
    {
        public const string ResourcePath = "Models/Environment/Tripo/Lighthouse/";
        static readonly Dictionary<string, Material> Materials = new Dictionary<string, Material>();
        public static GameObject Create(Transform parent)
        {
            var source = Resources.Load<GameObject>(ResourcePath + "Lighthouse_Modular");
            if (source == null) return null;
            var model = Object.Instantiate(source,parent,false);
            model.name = "Tripo Lighthouse | modular reconstruction";
            foreach (var r in model.GetComponentsInChildren<Renderer>(true))
            {
                var slots=r.sharedMaterials;
                for(int i=0;i<slots.Length;i++) slots[i]=MaterialFor(slots[i]);
                r.sharedMaterials=slots;
                if(r.name.StartsWith("Reef") && r.TryGetComponent<MeshFilter>(out var f))
                    r.gameObject.AddComponent<MeshCollider>().sharedMesh=f.sharedMesh;
            }
            return model;
        }
        static Material MaterialFor(Material source)
        {
            string key=source!=null?source.name.Replace(" (Instance)",""):"Lighthouse_Complete";
            if(Materials.TryGetValue(key,out var material) && material!=null)return material;
            material=Resources.Load<Material>(ResourcePath+key);
            if(material==null)
            {
                material=new Material(Shader.Find("Universal Render Pipeline/Lit")){name=key,enableInstancing=true};
                if(key.Contains("ConcreteCut"))material.SetColor("_BaseColor",new Color(.72f,.70f,.65f));
                else if(key.Contains("RockSupport"))material.SetColor("_BaseColor",new Color(.36f,.34f,.30f));
                else if(key.Contains("Timber"))material.SetColor("_BaseColor",new Color(.28f,.17f,.08f));
                else material.SetTexture("_BaseMap",Resources.Load<Texture2D>(ResourcePath+(key.Contains("Ruin")?"Lighthouse_Ruin_BaseColor":"Lighthouse_Complete_BaseColor")));
                material.SetFloat("_Smoothness",.15f);
                material.SetFloat("_Cull",0f);
#if UNITY_EDITOR
                if(!Application.isPlaying)UnityEditor.AssetDatabase.CreateAsset(material,"Assets/LastLandfall/Resources/"+ResourcePath+key+".mat");
#endif
            }
            Materials[key]=material;return material;
        }
        public static void SetStage(GameObject model,int completed,int working=-1,float progress=0f)
        {
            if(model==null)return;
            foreach(var f in model.GetComponentsInChildren<MeshFilter>(true))
            {
                string n=f.name;
                bool show=false;
                if(n.StartsWith("Reef"))show=true;
                else if(n.StartsWith("Ruin_"))
                {
                    int.TryParse(n.Substring(5),out int piece);
                    show=completed==0 && (working!=1 || piece>=Mathf.FloorToInt(progress*4f));
                }
                else if(n.StartsWith("Scaffold"))
                {
                    int s=n.Contains("Lower")?3:n.Contains("Middle")?4:5;
                    show=working>=s && working<=6;
                }
                else
                {
                    int stage=n.StartsWith("Foundation")?2:n.StartsWith("TowerLower")?3:
                        n.StartsWith("TowerMiddle")?4:n.StartsWith("TowerUpper")?5:
                        n.StartsWith("Lantern")?6:n.StartsWith("EquipmentHouse")?7:99;
                    show=completed>=stage;
                    if(working==stage)
                    {
                        float build=Mathf.Clamp01((progress-.2f)/.8f);
                        int layer=n.LastIndexOf('_');
                        show=layer>=0 && int.TryParse(n.Substring(layer+1),out int index)
                            ? build>=(index+1)/4f : build>=.8f;
                    }
                }
                f.gameObject.SetActive(show);
            }
        }
    }
}

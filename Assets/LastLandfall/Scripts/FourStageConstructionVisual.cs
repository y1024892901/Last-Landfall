using System.Collections.Generic;
using UnityEngine;

namespace LastLandfall.Prototype
{
    // Temporary visual only. Never edits the imported mesh or the finished materials.
    public sealed class FourStageConstructionVisual : MonoBehaviour
    {
        readonly List<Material> owned = new List<Material>();
        GameObject scaffold;
        GameObject supplies;
        Bounds bounds;
        public bool Initialize(GameObject model)
        {
            Shader shader = Resources.Load<Shader>("Shaders/ConstructionReveal");
            if (shader == null || !shader.isSupported) return false;
            Renderer[] renderers = model.GetComponentsInChildren<Renderer>(true);
            if (renderers.Length == 0) return false;
            bounds = renderers[0].bounds;
            foreach (Renderer r in renderers) bounds.Encapsulate(r.bounds);
            foreach (Renderer r in renderers)
            {
                Material[] materials = r.sharedMaterials;
                for (int i = 0; i < materials.Length; i++)
                {
                    Material source = materials[i];
                    Material m = new Material(shader);
                    if (source != null)
                    {
                        string texture = source.HasProperty("_BaseMap") ? "_BaseMap" : "_MainTex";
                        if (source.HasProperty(texture))
                        {
                            m.SetTexture("_BaseMap", source.GetTexture(texture));
                            m.SetTextureScale("_BaseMap", source.GetTextureScale(texture));
                            m.SetTextureOffset("_BaseMap", source.GetTextureOffset(texture));
                        }
                        if (source.HasProperty("_BaseColor")) m.SetColor("_BaseColor",source.GetColor("_BaseColor"));
                        else if (source.HasProperty("_Color")) m.SetColor("_BaseColor",source.GetColor("_Color"));
                    }
                    owned.Add(m); materials[i] = m;
                }
                r.sharedMaterials = materials;
            }
            scaffold = new GameObject("Temporary scaffolding"); scaffold.transform.SetParent(transform,false);
            supplies = new GameObject("Construction supplies"); supplies.transform.SetParent(transform,false);
            Material timber = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            timber.color = new Color(.36f,.24f,.12f); owned.Add(timber);
            // Derive corners from model bounds, so rotated and coastal assets keep their actual footprint.
            float bottom = bounds.min.y;
            float top = bounds.max.y;
            float width = Mathf.Max(.5f,bounds.size.x);
            float depth = Mathf.Max(.5f,bounds.size.z);
            for (int x=-1; x<=1; x+=2)
            for (int z=-1; z<=1; z+=2)
            {
                Vector3 p=new Vector3(bounds.center.x+x*(width*.5f+.12f),bottom,bounds.center.z+z*(depth*.5f+.12f));
                Block(scaffold,p+Vector3.up*bounds.size.y*.5f,new Vector3(.07f,bounds.size.y,.07f),timber);
            }
            for (int level=1;level<=3;level++)
            {
                float y=Mathf.Lerp(bottom,top,level/3f);
                for(int z=-1;z<=1;z+=2)
                    Block(scaffold,new Vector3(bounds.center.x,y,bounds.center.z+z*(depth*.5f+.12f)),new Vector3(width+.32f,.06f,.12f),timber);
            }
            Block(supplies,new Vector3(bounds.center.x,bottom+.035f,bounds.center.z),new Vector3(width,.07f,depth),timber);
            for(int i=0;i<4;i++)
                Block(supplies,new Vector3(bounds.center.x-width*.25f,bottom+.04f+i*.065f,bounds.min.z-.25f),new Vector3(width*.45f,.06f,.18f),timber);
            return true;
        }
        static void Block(GameObject parent,Vector3 position,Vector3 size,Material material)
        {
            GameObject cube=GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.transform.SetParent(parent.transform,false); cube.transform.position=position;
            cube.transform.rotation=Quaternion.identity;
            Vector3 scale=parent.transform.lossyScale;
            cube.transform.localScale=new Vector3(size.x/Mathf.Max(.0001f,Mathf.Abs(scale.x)),size.y/Mathf.Max(.0001f,Mathf.Abs(scale.y)),size.z/Mathf.Max(.0001f,Mathf.Abs(scale.z)));
            cube.GetComponent<Renderer>().sharedMaterial=material;
            Collider c=cube.GetComponent<Collider>(); c.enabled=false; if(Application.isPlaying) if(Application.isPlaying) Destroy(c); else DestroyImmediate(c); else DestroyImmediate(c);
        }
        public void Sample(float progress)
        {
            // Three working stages plus completion. Foundation remains visible at the start.
            float fraction = progress < .2f ? Mathf.Lerp(.025f,.16f,progress/.2f)
                : progress < .6f ? Mathf.Lerp(.16f,.62f,(progress-.2f)/.4f)
                : Mathf.Lerp(.62f,1f,(progress-.6f)/.4f);
            float height=Mathf.Lerp(bounds.min.y,bounds.max.y,fraction);
            foreach(Material m in owned) if(m.HasProperty("_CutHeight")) m.SetFloat("_CutHeight",height);
            scaffold.SetActive(progress>=.2f && progress<.95f);
            supplies.SetActive(progress<.85f);
        }
        void OnDestroy() { foreach(Material m in owned) if(m!=null) { if(Application.isPlaying) Destroy(m); else DestroyImmediate(m); } }
    }
}

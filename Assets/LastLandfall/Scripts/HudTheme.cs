using UnityEngine;

namespace LastLandfall.Prototype
{
    /// <summary>Shared slate-glass panels, quiet borders and warm navigation accents.</summary>
    public static class HudTheme
    {
        public static readonly Color Ink = new Color(.055f,.082f,.101f,.92f);
        public static readonly Color Text = new Color(.91f,.93f,.91f);
        public static readonly Color Muted = new Color(.60f,.69f,.72f);
        public static readonly Color Accent = new Color(.81f,.72f,.48f);
        static Texture2D panel,card,hover,selected,gradient;
        public static Texture2D Panel => panel != null ? panel : panel = Rounded(Ink);
        public static Texture2D Card => card != null ? card : card = Rounded(new Color(.12f,.16f,.18f,.72f));
        public static Texture2D Hover => hover != null ? hover : hover = Rounded(new Color(.20f,.27f,.29f,.85f));
        public static Texture2D Selected => selected != null ? selected : selected = Rounded(new Color(.25f,.29f,.26f,.92f));
        static Texture2D Rounded(Color color)
        {
            const int size=64;const float radius=10;
            var texture=new Texture2D(size,size,TextureFormat.RGBA32,false){hideFlags=HideFlags.HideAndDontSave,wrapMode=TextureWrapMode.Clamp,filterMode=FilterMode.Bilinear};
            var pixels=new Color[size*size];
            for(int y=0;y<size;y++)for(int x=0;x<size;x++)
            {
                float dx=x+.5f-Mathf.Clamp(x+.5f,radius,size-radius);
                float dy=y+.5f-Mathf.Clamp(y+.5f,radius,size-radius);
                float alpha=Mathf.Clamp01(radius-Mathf.Sqrt(dx*dx+dy*dy));
                Color value=color;value.a*=alpha;pixels[y*size+x]=value;
            }
            texture.SetPixels(pixels);texture.Apply(false,true);return texture;
        }
        public static void StylePanel(GUIStyle style)
        {
            if(style==null)return;
            style.normal.background=Panel;style.border=new RectOffset(12,12,12,12);
        }
        public static void StyleButton(GUIStyle style,bool isSelected=false)
        {
            if(style==null)return;
            style.normal.background=isSelected?Selected:Card;
            style.hover.background=Hover;style.active.background=Selected;style.focused.background=Hover;
            style.normal.textColor=Text;style.hover.textColor=Color.white;
            style.active.textColor=Text;style.border=new RectOffset(12,12,12,12);
        }
        public static void TopShade(Rect rect)
        {
            if(gradient==null)
            {
                gradient=new Texture2D(1,128,TextureFormat.RGBA32,false){hideFlags=HideFlags.HideAndDontSave,wrapMode=TextureWrapMode.Clamp};
                for(int y=0;y<128;y++)gradient.SetPixel(0,y,new Color(.025f,.045f,.065f,Mathf.Pow(y/127f,1.6f)*.56f));
                gradient.Apply(false,true);
            }
            GUI.DrawTexture(new Rect(0,0,rect.width,rect.height+44),gradient);
        }
        public static GUIStyle Label(int size,Color color,bool bold=false)
        {
            var style=new GUIStyle(GUI.skin.label){fontSize=size,fontStyle=bold?FontStyle.Bold:FontStyle.Normal,wordWrap=true};
            style.normal.textColor=color;return style;
        }
    }
}

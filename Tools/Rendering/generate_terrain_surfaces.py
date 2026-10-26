"""Seamless multi-scale ground/stone albedo and linear height-roughness maps."""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Assets/LastLandfall/Resources/Textures/Terrain'
OUT.mkdir(parents=True,exist_ok=True)
N=1024
rng=np.random.default_rng(271027)
def noise(cut):
    z=rng.normal(size=(N,N))
    freq=np.fft.fftfreq(N);x,y=np.meshgrid(freq,freq)
    z=np.fft.ifft2(np.fft.fft2(z)*np.exp(-(x*x+y*y)/(cut/N)**2)).real
    return np.clip((z-z.mean())/(z.std()*3)+.5,0,1)
def save(name,color,height,rough):
    Image.fromarray(np.uint8(np.clip(color,0,1)*255)).save(OUT/(name+'Albedo.png'))
    gx=(np.roll(height,-1,1)-np.roll(height,1,1))*3
    gy=(np.roll(height,-1,0)-np.roll(height,1,0))*3
    packed=np.stack([.5+gx,.5+gy,height,rough],axis=-1)
    Image.fromarray(np.uint8(np.clip(packed,0,1)*255)).save(OUT/(name+'Surface.png'))
fine=noise(210);grain=noise(440);mid=noise(55);macro=noise(8)
soil=np.clip(.26+.35*mid+.15*fine+.12*grain,0,1)
color=np.stack([.29+.13*soil,.31+.17*soil,.19+.11*soil],axis=-1)
moss=np.clip((macro-.38)*2,0,.5)[...,None]
color=color*(1-moss)+np.array([.28,.37,.20])*moss
# Small mineral grains and thin dried plant fibres, never oversized painted blades.
pebble=np.maximum(0,(mid-.72)*5)[...,None]
color=color*(1-pebble*.5)+np.array([.49,.47,.39])*pebble*.5
save('Ground',color,.5*mid+.28*fine+.22*grain,np.full((N,N),.92))
stone=noise(18);rough=noise(95);micro=noise(390)
y,x=np.mgrid[:N,:N]
vein=np.sin(2*np.pi*(x*5/N+y*3/N)+stone*3)
crack=np.exp(-np.square(vein)*170)*(.4+.6*rough)
h=np.clip(.48*stone+.30*rough+.22*micro-crack*.13,0,1)
base=.28+.22*stone+.08*micro-crack*.07
rock=np.stack([base*.97,base,base*.98],axis=-1)
save('Rock',rock,h,.75+.18*rough)
print('Generated four seamless 1024px terrain maps:',OUT)

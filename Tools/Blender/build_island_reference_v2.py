"""Build the reference island as real geometry, with no vegetation or props.

Blender 5.2: blender --background --factory-startup --python this_file.py
The coastline is an explicit concave polygon, not a deformed ellipse. A
constrained triangulation follows the shoreline and keeps the exported surface
focused on the visible island terrain.
"""
from pathlib import Path
import json
import math
import sys
import time

import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from island_reference_landform import terrain_height, _noise
from island_reference_lookdev import create_materials, render_previews

NAME = "IslandReference_V2"
MODELS = ROOT / "Assets/LastLandfall/Resources/Models/Environment"
SOURCE = ROOT / "Assets/LastLandfall/Art/Source/Environment"
PREVIEW = ROOT / "Assets/LastLandfall/Art/Previews/Environment"
REPORT = ROOT / "work/island_reference_v2/geometry_report.json"

# Walk clockwise from the rear mountain coast, around asymmetric eastern
# headlands, the long southern peninsula, and three deep western inlets.
COAST_CONTROL = [
    (-650,980),(-420,1070),(-220,1020),(-65,1090),(80,1010),
    (260,1010),(390,920),(570,950),(680,850),(840,850),
    (860,740),(1050,650),(1070,520),(1230,390),(1185,285),
    (1270,170),(1300,80),(1240,0),(1090,-35),(1040,-150),
    (1170,-300),(1250,-420),(1200,-490),(1085,-520),(950,-485),
    (890,-600),(990,-715),(980,-805),(870,-860),(780,-810),
    (690,-740),(580,-725),(500,-825),(470,-1010),(530,-1125),
    (470,-1220),(365,-1290),(210,-1330),(85,-1295),(35,-1210),
    (-120,-1130),(-215,-1040),(-270,-885),(-410,-800),(-560,-795),
    (-710,-900),(-870,-840),(-950,-765),(-870,-665),(-760,-630),
    (-760,-520),(-925,-460),(-1080,-465),(-1215,-390),
    (-1260,-275),(-1160,-205),(-1040,-195),(-990,-95),
    (-1025,10),(-1160,90),(-1230,180),(-1165,295),
    (-1010,335),(-1040,480),(-1110,550),(-1100,670),
    (-955,730),(-900,865),(-785,900),
]

# Bedrock outcrops are part of the island geology, not placed resource props.
# (X,Y,half-width,half-length,top elevation,rotation radians)
REEFS = [
    (-1330,-365,45,72,25,.35),(-1405,-290,24,38,13,-.2),
    (-1080,-830,56,44,32,-.6),(-1215,35,20,43,16,-.3),
    (625,-1190,48,80,31,-.5),(565,-1345,27,48,20,-.4),
    (280,-1455,48,68,34,.25),(120,-1470,22,39,17,.2),
    (1100,-790,36,61,28,.55),(1360,-400,25,37,18,.4),
    (1380,160,29,45,19,-.4),(-1140,790,36,55,24,-.15),
]


def smoothstep(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def coast_polygon(spacing):
    p = np.asarray(COAST_CONTROL, dtype=float)
    # Slightly ease major corners, retaining deep bays and projecting capes.
    eased = []
    for i in range(len(p)):
        eased.append(p[i]*.88+p[(i-1)%len(p)]*.12)
        eased.append(p[i]*.88+p[(i+1)%len(p)]*.12)
    p = np.asarray(eased)
    area = np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])
    if area < 0:
        p = p[::-1]
    result = []
    for i,a in enumerate(p):
        b = p[(i+1)%len(p)]
        delta = b-a
        length = np.linalg.norm(delta)
        normal = np.asarray([delta[1],-delta[0]]) / max(length,1e-5)
        count = max(1, math.ceil(length/spacing))
        for j in range(count):
            t = j/count
            # Fracture-scale angular variation, never a sinusoidal scalloped rim.
            rough = math.sin(math.pi*t)*(5.5*math.sin(t*16.1+i*4.7)+2.3*math.sin(t*38+i))
            result.append(a+t*delta+normal*rough)
    return np.asarray(result)


def inside_and_distance(x, y, polygon):
    x,y = np.broadcast_arrays(np.asarray(x),np.asarray(y))
    inside = np.zeros_like(x,dtype=bool)
    d2 = np.full_like(x,1e20,dtype=float)
    for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
        dx,dy = b-a
        if abs(dy)>1e-8:
            inside ^= ((a[1]>y)!=(b[1]>y)) & (x < (dx*(y-a[1])/dy+a[0]))
        along = np.clip(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy),0,1)
        d2 = np.minimum(d2,(x-a[0]-along*dx)**2+(y-a[1]-along*dy)**2)
    return inside,np.sqrt(d2)


def triangulation(polygon, spacing):
    lo,hi = polygon.min(axis=0),polygon.max(axis=0)
    xx,yy=np.meshgrid(np.arange(lo[0]+spacing/2,hi[0],spacing),
                      np.arange(lo[1]+spacing/2,hi[1],spacing))
    # Use major segments for the bulk inclusion operation. Detailed boundary
    # constraints are then applied by Blender's exact constrained triangulator.
    inside,dist=inside_and_distance(xx,yy,polygon)
    mask=inside & (dist>spacing*.42)
    points=np.concatenate([polygon,np.column_stack([xx[mask],yy[mask]])])
    n=len(polygon)
    result=delaunay_2d_cdt([Vector(p) for p in points],[],[list(range(n))],1,.001,True)
    coords=np.asarray([tuple(v) for v in result[0]])
    faces=[tuple(f) for f in result[2]]
    coast_map={}
    for out_id,orig_ids in enumerate(result[3]):
        for idx in orig_ids:
            if idx<n:
                coast_map[idx]=out_id
    if len(coast_map)!=n:
        raise RuntimeError(f"Coast constraints lost: {len(coast_map)}/{n}")
    return coords,faces,[coast_map[i] for i in range(n)]


def clipped_height(x,y,distance):
    raw=terrain_height(x,y)
    # Keep the coastline at the water datum. The submerged bedrock shell starts
    # on this same outline; raising this edge exposes it as a black wall ring.
    edge=np.zeros_like(raw)
    shore_width=70+25*(.5+.5*_noise(x,y,260,107))
    h=edge+(raw-edge)*smoothstep(0,shore_width,distance)
    rocky=np.maximum(0,1-smoothstep(80,210,distance))*smoothstep(0,25,distance)
    bedding_phase=.028*x+.045*y+2.1*_noise(x,y,90,109)
    joints=-5.5*np.exp(-((np.sin(bedding_phase)/.20)**2))
    h+=rocky*(5.2*_noise(x,y,60,113)+2.7*_noise(x,y,17,127)+joints)
    return h


def append_reef(vertices,faces,materials,reef,detail):
    cx,cy,rx,ry,top,angle=reef
    n=24 if detail else 12
    ca,sa=math.cos(angle),math.sin(angle)
    starts=[]
    for t,r in [(0,.78),(.17,1),(.37,.97),(.57,.84),(.76,.64),(.90,.32)]:
        starts.append(len(vertices))
        for j in range(n):
            a=math.tau*j/n
            fractured=1+.09*math.sin(3*a+.8)+.07*math.sin(7*a+cx)
            px,py=rx*r*fractured*math.cos(a),ry*r*fractured*math.sin(a)
            z=-36+(top+36)*t+math.sin(a*3+cy)*3*r
            vertices.append((cx+ca*px-sa*py,cy+sa*px+ca*py,z))
    for first,second in zip(starts[:-1],starts[1:]):
        for j in range(n):
            k=(j+1)%n
            faces.extend([(first+j,first+k,second+k),(first+j,second+k,second+j)])
            materials.extend([1,1])
    bottom=len(vertices);vertices.append((cx,cy,-36))
    peak=len(vertices);vertices.append((cx-rx*.1,cy+ry*.12,top))
    for j in range(n):
        k=(j+1)%n
        faces.extend([(bottom,starts[0]+k,starts[0]+j),
                      (peak,starts[-1]+j,starts[-1]+k)])
        materials.extend([2,1])


def build_landform(name,spacing,coast_spacing,materials):
    polygon=coast_polygon(coast_spacing)
    print(f"{name}: constrained triangulation at {spacing}m",flush=True)
    xy,faces,coast_ids=triangulation(polygon,spacing)
    _,dist=inside_and_distance(xy[:,0],xy[:,1],polygon)
    heights=clipped_height(xy[:,0],xy[:,1],dist)
    vertices=np.column_stack([xy,heights]).tolist()
    faces=list(faces)
    material_ids=[0]*len(faces)
    top_count=len(faces)
    for reef in REEFS:
        append_reef(vertices,faces,material_ids,reef,True)

    mesh=bpy.data.meshes.new(name+"_Mesh")
    mesh.from_pydata(vertices,[],faces)
    for mat in materials:mesh.materials.append(mat)
    mesh.update()
    # Large exposed faces and coastal rock have distinct geology; central
    # lowland retains mineral bare earth without grass-like coloration.
    normals=np.empty(len(mesh.polygons)*3,dtype=np.float32)
    mesh.polygons.foreach_get("normal",normals)
    slopes=np.degrees(np.arccos(np.clip(normals.reshape(-1,3)[:,2],-1,1)))
    for p in mesh.polygons:
        if p.index<top_count:
            v=np.asarray([vertices[i] for i in p.vertices])
            height=v[:,2].mean()
            cx,cy=v[:,:2].mean(axis=0)
            # Headlands and mountain outcrops have exposed fractured rock.
            rock=(slopes[p.index]>24 or height>215 or
                  dist[p.vertices[0]]<44 or (cy < -820 and height>26))
            # Use bare earth on every face touching the lowest shoreline band.
            # Steep coast faces are otherwise classified as rock, which leaves
            # a dark outline along the water even when the submerged skirt is
            # hidden from the visible mesh.
            touches_shore_band=np.min(v[:,2])<18
            material_ids[p.index]=0 if touches_shore_band else (1 if rock else 0)
        p.material_index=material_ids[p.index]
        p.use_smooth=True
    # Subtle exported vertex tint also carries natural variation into Unity.
    attr=mesh.color_attributes.new(name="GeologyTint",type="FLOAT_COLOR",domain="POINT")
    positions=np.asarray(vertices)
    tint=.93+.09*_noise(positions[:,0],positions[:,1],65,139)
    colors=np.column_stack([tint,tint,tint,np.ones(len(tint))]).astype(np.float32)
    attr.data.foreach_set("color",colors.ravel())
    mesh.color_attributes.active_color=attr
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj,top_count


def validate_mesh(obj, expected_boundary_edges=0):
    # Check topology and maximum edge length. The visible terrain intentionally
    # has one open coastline.
    import bmesh
    bm=bmesh.new();bm.from_mesh(obj.data)
    result={"vertices":len(bm.verts),"triangles":len(bm.faces),
            "boundary_edges":sum(e.is_boundary for e in bm.edges),
            "nonmanifold_edges":sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
            "max_edge_metres":round(max(e.calc_length() for e in bm.edges),2)}
    bm.free()
    if result["nonmanifold_edges"] or result["boundary_edges"] != expected_boundary_edges:
        raise RuntimeError(f"Non-manifold landform: {result}")
    return result


def export_fbx(obj,path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={"MESH"},
        axis_forward="-Z",axis_up="Y",apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",use_mesh_modifiers=True,
        add_leaf_bones=False,bake_anim=False,path_mode="AUTO",colors_type="LINEAR")


def main():
    started=time.time()
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    for path in [MODELS,SOURCE,PREVIEW,REPORT.parent]:path.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    scene.unit_settings.system="METRIC";scene.unit_settings.scale_length=1
    bpy.context.preferences.filepaths.save_version=0
    materials=create_materials()
    terrain,_=build_landform(NAME,4.5,9,materials)
    render_boundary_edges=len(coast_polygon(9))
    report={"render":validate_mesh(terrain,render_boundary_edges),"sea_level":0,"buildable_datum":54,
            "features":["rear-left dominant massif","descending branching rear ridge",
                "broad open central lowland","separated lateral hills and saddles",
                "long asymmetric southern rock peninsula","deep coves and inundated rock shore"],
            "excluded":["trees","grass","sand","buildings","resources","exported water"]}
    export_fbx(terrain,MODELS/(NAME+".fbx"))
    bpy.ops.object.select_all(action="DESELECT")
    terrain.select_set(True);bpy.context.view_layer.objects.active=terrain
    # Source opens on the actual bare island.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=="VIEW_3D":
                area.spaces.active.clip_end=20000
                area.spaces.active.region_3d.view_distance=3100
                area.spaces.active.region_3d.view_location=(0,0,100)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+".blend")))
    report["previews"]=render_previews(terrain,PREVIEW,NAME)
    report["seconds"]=round(time.time()-started,1)
    REPORT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__":main()

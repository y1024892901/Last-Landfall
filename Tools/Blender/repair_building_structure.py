"""Apply the reviewed structural repairs to existing editable building sources.
The original generators include the same fixes for subsequent full rebuilds.
"""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path.cwd();SOURCE=ROOT/'Assets/LastLandfall/Art/Source'
FIXES={
 'Greenhouse_DeepSeek':'Added eight feet beneath the growing beds to bridge the 30 mm floor gap.',
 'CouncilHall_DeepSeek':'Connected both door handles to the door leaves with mounting stems.',
 'PublicKitchen_DeepSeek':'Seated all four supply crates on shelves and connected the drain pipe to its elbow.',
 'MedicalStation_DeepSeek':'Extended the front glass and mullion into the window frame rebates.',
 'RescueOutpost_DeepSeek':'Turned the three platform joists perpendicular to the deck planks.',
 'FishingDock_DeepSeek':'Attached horizontal net strands to posts and vertical strands to the drying bar.',
 'WeatherTideBuoy_DeepSeek':'Connected the wind vane tail to the main pivot with an arm.',
 'SalvageWorkshop_DeepSeek':'Added a shear foundation, rear guide, blade crosshead and load suspension link.',
 'ResidentHut_DeepSeek':'Added four studs supporting the separated side wall boards and window frames.',
 'RescueDock_DeepSeek':'Connected the boarding ladder, boat windshield and steering wheel to their supporting structures.',
 'Shipyard_DeepSeek':'Connected the two upper hull stringers to three rib stations with six timber cleats.'}

def box(col,name,center,size,mat,bevel=0):
 old=bpy.data.objects.get(name)
 if old:bpy.data.objects.remove(old,do_unlink=True)
 bpy.ops.mesh.primitive_cube_add(size=1,location=center)
 o=bpy.context.object;o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(mat)
 if bevel:
  m=o.modifiers.new('Structural edge chamfer','BEVEL');m.width=bevel;m.segments=1
 return o

def extent(o,axis,low,high):
 bpy.context.view_layer.update();world=[o.matrix_world@v.co for v in o.data.vertices]
 a=min(v[axis] for v in world);b=max(v[axis] for v in world);inv=o.matrix_world.inverted()
 for vertex,p in zip(o.data.vertices,world):
  p[axis]=low+(p[axis]-a)*(high-low)/(b-a);vertex.co=inv@p
 o.data.update()

def mat(name):return bpy.data.objects[name].data.materials[0]

for asset,description in FIXES.items():
 path=next(SOURCE.glob('*/'+asset+'.blend'));bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.preferences.filepaths.save_version=0
 col=bpy.data.collections[asset]
 if asset=='Greenhouse_DeepSeek':
  for side,x in [('L',-1.03),('R',1.03)]:
   for i,(dx,y) in enumerate([(-.45,-.94),(.45,-.94),(-.45,1.04),(.45,1.04)]):box(col,f'PlantBed_{side}_Foot_{i}',(x+dx,y,.615),(.1,.1,.05),mat('PlantBed_L_Body'),.004)
 elif asset=='CouncilHall_DeepSeek':
  for side in [-1,1]:box(col,f'CouncilHall_DeepSeek_Door_Handle_Mount_{side}',(side*.1,-4.62,1.58),(.04,.08,.04),mat(f'CouncilHall_DeepSeek_Door_Handle_{side}'),.003)
 elif asset=='PublicKitchen_DeepSeek':
  for i,z in enumerate([.935,.935,1.335,1.735]):extent(bpy.data.objects[f'PK_ProvisionCrate_{i}'],2,z,z+.16)
  extent(bpy.data.objects['PK_SideDrainPipe'],2,.18,2.255)
 elif asset=='MedicalStation_DeepSeek':
  extent(bpy.data.objects['Window_Glass'],0,.13,1.37)
  for name in ['Window_Glass','Window_Mullion']:extent(bpy.data.objects[name],2,1.28,2.12)
 elif asset=='RescueOutpost_DeepSeek':
  for name,x in [('Platform_Joist_F',-.7),('Platform_Joist_B',.7),('Platform_Joist_M',0)]:
   o=bpy.data.objects[name];extent(o,0,x-.05,x+.05);extent(o,1,-.8,.8)
 elif asset=='FishingDock_DeepSeek':
  for i in range(3):extent(bpy.data.objects[f'Net_String_H_{i}'],1,-.1,1.1)
  for i in range(5):extent(bpy.data.objects[f'Net_String_V_{i}'],2,1.2,2.15)
 elif asset=='WeatherTideBuoy_DeepSeek':
  vane=bpy.data.objects['Vane_Tail'];z=sum((vane.matrix_world@v.co).z for v in vane.data.vertices)/len(vane.data.vertices)
  box(col,'Vane_Tail_Arm',(0,.075,z),(.02,.15,.02),mat('Vane_Arm'))
 elif asset=='SalvageWorkshop_DeepSeek':
  extent(bpy.data.objects['Interior rear shadow'],1,.7025,.7275)
  dark=mat('Scrap shear pedestal');teal=mat('Shear upper ram')
  box(col,'Scrap shear mounting plinth',(0,.28,.26),(.52,.38,.04),dark,.004)
  box(col,'Shear rear guide',(0,.39,.96),(.22,.16,.70),dark,.012)
  box(col,'Shear blade crosshead',(0,.20,.85),(.66,.30,.08),teal,.008)
  box(col,'Load suspension link',(.18,-.71,1.255),(.025,.025,.10),dark,.003)
 elif asset=='ResidentHut_DeepSeek':
  for side in [-1,1]:
   for i,y in enumerate([-.12,.72]):box(col,f'Side_Window_Stud_{side}_{i}',(side*1.76,y,2.095),(.08,.10,1.85),mat('Foundation_Pile_0'))
 elif asset=='RescueDock_DeepSeek':
  for side,x in [('Left',-.32),('Right',.32)]:box(col,f'Ladder_Mount_{side}',(x,-2.125,1.66),(.12,.25,.10),mat('MooringPost_Cap_0'))
  box(col,'Boat_SteeringColumn',(1.4,2.66,1.39),(.06,.14,.12),mat('MooringPost_Cap_0'))
  for i,dy in enumerate([-.22,.22]):box(col,f'Boat_Windshield_Bracket_{i}',(1.63,2.95+dy,1.20),(.32,.06,.08),mat('MooringPost_Cap_0'))
 elif asset=='Shipyard_DeepSeek':
  for i,x in enumerate([-1.4,-.7,0]):
   for side,sign in [('L',-1),('R',1)]:box(col,f'Hull_Stringer_Cleat_{side}_{i}',(x,sign*.46,1.23),(.12,.26,.08),mat('Hull_Stringer_L_High'))
 col['structural_review']='2026-10-26: '+description
 bpy.ops.wm.save_as_mainfile(filepath=str(path));print('REPAIRED',asset,flush=True)
output=ROOT/'Assets/LastLandfall/Art/Reports/BuildingAudit/structural_repairs.json'
output.write_text(json.dumps(FIXES,ensure_ascii=False,indent=2),encoding='utf-8')

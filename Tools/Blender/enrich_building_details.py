"""Add editable, purpose-specific coastal details to all 25 finished assets.
Run from the project root with Blender. Repeat runs replace only this pass.
"""
from pathlib import Path
import bpy, math, json, shutil, sys
from mathutils import Vector, Matrix

ROOT=Path.cwd()
SOURCE=ROOT/'Assets/LastLandfall/Art/Source'
OUT=ROOT/'Assets/LastLandfall/Art/Reports/BuildingDetail'
BACKUP=ROOT/'work/BuildingDetail_Before/Source'
PREFIX='DetailPass__'
OUT.mkdir(parents=True,exist_ok=True)

class Detail:
    def __init__(self,path):
        self.path=path;self.asset=path.stem;self.counter=0;self.parent=None;self.features=[]
        backup=BACKUP/path.parent.name/path.name
        if not backup.exists():
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
        bpy.ops.wm.open_mainfile(filepath=str(path))
        bpy.context.preferences.filepaths.save_version=0
        self.model=bpy.data.collections[self.asset]
        old=bpy.data.collections.get(self.asset+'_DetailPass')
        if old:
            for o in list(old.objects):
                mesh=o.data if o.type=='MESH' else None
                bpy.data.objects.remove(o,do_unlink=True)
                if mesh and mesh.users==0:bpy.data.meshes.remove(mesh)
            bpy.data.collections.remove(old)
        self.parts=[o for o in self.model.all_objects if o.type=='MESH']
        self.col=bpy.data.collections.new(self.asset+'_DetailPass');self.model.children.link(self.col)
        mats=set(m for o in self.parts for m in o.data.materials if m)
        self.mats=[]
        for mat in mats:
            shader=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat.use_nodes else None
            color=Vector(shader.inputs['Base Color'].default_value[:3] if shader else mat.diffuse_color[:3])
            alpha=shader.inputs['Alpha'].default_value if shader else mat.diffuse_color[3]
            ec=shader.inputs.get('Emission Color') if shader else None
            es=shader.inputs.get('Emission Strength') if shader else None
            glow=ec and es and max(ec.default_value[:3])*es.default_value>0.01
            if alpha>=.999 and not glow:self.mats.append((mat,color))
        self.palette={name:self.color(rgb) for name,rgb in {
            'iron':(.10,.13,.14),'paper':(.78,.72,.58),'wood':(.42,.29,.17),
            'teal':(.16,.37,.38),'rust':(.50,.23,.10),'light':(.60,.58,.48),'red':(.65,.08,.06),
        }.items()}
        bpy.context.view_layer.update()

    def color(self,rgb):
        target=Vector(rgb)
        return min(self.mats,key=lambda m:(m[1]-target).length_squared)[0]

    def find(self,*names):
        for name in names:
            exact=next((o for o in self.parts if o.name==name),None)
            if exact:return exact
        for name in names:
            matches=[o for o in self.parts if name.lower() in o.name.lower()]
            if matches:return max(matches,key=lambda o:o.dimensions.length)
        raise RuntimeError(f'{self.asset}: missing anchor {names}')

    def all(self,fragment,limit=8):
        return sorted([o for o in self.parts if fragment.lower() in o.name.lower()],key=lambda o:o.name)[:limit]

    def move(self,o,role,anchor=None):
        self.counter+=1;o.name=f'{PREFIX}{self.counter:03d}_{role}'
        for owner in list(o.users_collection):owner.objects.unlink(o)
        self.col.objects.link(o)
        o['detail_role']=role
        if anchor:o['detail_anchor']=anchor.name
        if self.parent:
            world=o.matrix_world.copy();o.parent=self.parent;o.matrix_world=world
        return o

    def box(self,role,p,size,mat=None,rotation=None,bevel=0,anchor=None):
        bpy.ops.mesh.primitive_cube_add(size=1,location=p)
        o=bpy.context.object;o.dimensions=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if rotation is not None:o.rotation_euler=rotation.to_euler() if hasattr(rotation,'to_euler') else rotation
        o.data.materials.append(mat or self.palette['iron'])
        if bevel:
            mod=o.modifiers.new('Small handmade edge','BEVEL');mod.width=min(bevel,min(size)*.18);mod.segments=1
        return self.move(o,role,anchor)

    def cylinder(self,role,p,r,depth,mat=None,axis=(0,0,1),vertices=8,anchor=None):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=p)
        o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
        o.data.materials.append(mat or self.palette['iron'])
        return self.move(o,role,anchor)

    def beam(self,role,a,b,width,mat=None,anchor=None):
        a,b=Vector(a),Vector(b);v=b-a
        return self.box(role,(a+b)/2,(width,width,v.length),mat,v.to_track_quat('Z','Y'),anchor=anchor)

    def ring(self,role,p,r,thickness,mat=None,axis=(0,0,1),anchor=None):
        bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=thickness,major_segments=12,minor_segments=4,location=p)
        o=bpy.context.object;o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
        o.data.materials.append(mat or self.palette['wood'])
        return self.move(o,role,anchor)

    def face(self,ref,facing=(0,-1,0)):
        o=ref if hasattr(ref,'matrix_world') else self.find(ref)
        deps=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(deps);mesh=ev.to_mesh()
        direction=Vector(facing).normalized();normal_matrix=o.matrix_world.to_3x3().inverted().transposed()
        candidates=[]
        for f in mesh.polygons:
            n=(normal_matrix@f.normal).normalized();alignment=n.dot(direction)
            if alignment>.60:candidates.append((f.area*alignment**3,f,n))
        if not candidates:raise RuntimeError('No usable face '+o.name)
        _,f,n=max(candidates,key=lambda item:item[0])
        vertices=[o.matrix_world@mesh.vertices[i].co for i in f.vertices]
        center=sum(vertices,Vector())/len(vertices)
        u=Vector((1,0,0));u-=n*u.dot(n)
        if u.length<.1:u=Vector((0,1,0));u-=n*u.dot(n)
        u.normalize();v=n.cross(u).normalized()
        w=max((p-center).dot(u) for p in vertices)-min((p-center).dot(u) for p in vertices)
        h=max((p-center).dot(v) for p in vertices)-min((p-center).dot(v) for p in vertices)
        ev.to_mesh_clear()
        return {'object':o,'p':center,'n':n,'u':u,'v':v,'w':w,'h':h,'rotation':Matrix((u,v,n)).transposed()}

    def plate(self,s,role,x,y,w,h,t,mat=None,depth=0):
        p=s['p']+s['u']*x+s['v']*y+s['n']*(depth+t/2-.002)
        return self.box(role,p,(w,h,t),mat,s['rotation'],anchor=s['object'])

    def bolts(self,s,w,h,r=.012,depth=.015):
        r=min(r,w*.10,h*.10)
        for x in [-w*.40,w*.40]:
            for y in [-h*.40,h*.40]:
                p=s['p']+s['u']*x+s['v']*y+s['n']*depth
                self.cylinder('Hex_fastener',p,r,.018,self.palette['iron'],s['n'],6,s['object'])

    def hardware(self,ref,facing=(0,-1,0)):
        s=self.face(ref,facing);w,h=s['w'],s['h']
        for y in [-h*.30,h*.30]:
            self.plate(s,'Hinge_leaf',-w*.36,y,min(.09,w*.22),min(.14,h*.16),.014,self.palette['iron'])
            p=s['p']-s['u']*w*.36+s['v']*y+s['n']*.018
            self.cylinder('Hinge_pin',p,min(.018,w*.04),min(.15,h*.18),self.palette['rust'],s['v'],8,s['object'])
        self.features.append('门窗五金和铰链')

    def notice(self,ref,kind='chart',facing=(0,-1,0)):
        s=self.face(ref,facing);w=min(.85,s['w']*.75);h=min(.65,s['h']*.70)
        self.plate(s,'Notice_backboard',0,0,w,h,.016,self.palette['iron'])
        for i,(x,y) in enumerate([(-.23,.10),(.20,.13),(-.04,-.23)]):
            pw=w*(.36 if i<2 else .65);ph=h*(.50 if i<2 else .20)
            self.plate(s,'Pinned_paper',x*w,y*h,pw,ph,.009,self.palette['paper'],.017)
            for line in range(3 if i<2 else 1):
                self.plate(s,'Notice_marks',x*w,y*h+ph*.25-line*ph*.22,pw*(.65-.1*(line%2)),max(.004,ph*.025),.004,self.palette['teal'],.027)
            p=s['p']+s['u']*(x*w)+s['v']*(y*h+ph*.38)+s['n']*.031
            self.cylinder('Notice_pin',p,min(.012,w*.018),.008,self.palette['rust'],s['n'],6,s['object'])
        self.features.append('带图表的公告与记录板')

    def menu(self,ref):
        s=self.face(ref);w=min(.60,s['w']*.78);h=min(.70,s['h']*.64)
        self.plate(s,'Kitchen_menu_frame',0,0,w,h,.028,self.palette['wood'])
        self.plate(s,'Kitchen_chalkboard',0,0,w*.88,h*.90,.012,self.palette['iron'],.029)
        for i in range(5):
            self.plate(s,'Daily_menu_row',-w*.04,h*(.30-i*.15),w*(.62 if i%2 else .48),h*.025,.004,self.palette['paper'],.042)
        self.features.append('每日供餐黑板菜单')

    def vent(self,ref,facing=(0,-1,0)):
        s=self.face(ref,facing);w=min(.42,s['w']*.65);h=min(.32,s['h']*.48)
        self.plate(s,'Vent_mount',0,0,w,h,.025,self.palette['iron'])
        for i in range(5):self.plate(s,'Vent_louver',0,(i-2)*h*.15,w*.86,h*.07,.022,self.palette['light'],.026)
        self.bolts(s,w,h,min(.012,w*.035),.033)
        self.features.append('百叶散热罩与紧固件')

    def gauge(self,ref,facing=(0,-1,0)):
        s=self.face(ref,facing);r=min(.11,s['w']*.32,s['h']*.30)
        p=s['p']+s['n']*.018
        self.cylinder('Instrument_case',p,r,.04,self.palette['iron'],s['n'],12,s['object'])
        self.cylinder('Instrument_dial',p+s['n']*.025,r*.82,.013,self.palette['paper'],s['n'],12,s['object'])
        a=p+s['n']*.035;self.beam('Instrument_needle',a-s['u']*r*.15,a+s['u']*r*.42+s['v']*r*.42,max(.006,r*.07),self.palette['rust'],s['object'])
        for angle in [-2.2,-1.1,0,1.1,2.2]:
            d=s['u']*math.sin(angle)+s['v']*math.cos(angle)
            self.beam('Dial_tick',a+d*r*.65,a+d*r*.78,max(.004,r*.04),self.palette['iron'],s['object'])
        self.features.append('可辨识的仪表盘')

    def control(self,ref,facing=(0,-1,0)):
        s=self.face(ref,facing);w=min(.44,s['w']*.67);h=min(.42,s['h']*.64)
        self.plate(s,'Control_faceplate',0,0,w,h,.022,self.palette['teal'])
        self.plate(s,'Control_display',0,h*.15,w*.68,h*.25,.012,self.palette['iron'],.023)
        for i in [-1,0,1]:
            p=s['p']+s['u']*i*w*.23-s['v']*h*.22+s['n']*.041
            self.cylinder('Control_pushbutton',p,min(.021,w*.065),.018,self.palette['rust' if i==1 else 'light'],s['n'],8,s['object'])
        self.bolts(s,w,h,min(.012,w*.03),.028)
        self.features.append('检修面板与操作按钮')

    def hatch(self,ref,facing=(0,-1,0)):
        s=self.face(ref,facing);w=min(.38,s['w']*.65);h=min(.42,s['h']*.55)
        self.plate(s,'Cleanout_hatch',0,0,w,h,.025,self.palette['iron'])
        self.plate(s,'Hatch_latch',w*.25,0,w*.12,h*.26,.025,self.palette['rust'],.026)
        self.bolts(s,w,h,min(.014,w*.05),.028)
        self.features.append('检修门与锁扣')

    def valve(self,ref,facing=(0,-1,0)):
        s=self.face(ref,facing);r=min(.11,max(.055,s['w']*.45))
        center=s['p']+s['n']*.075
        self.cylinder('Valve_spindle',s['p']+s['n']*.035,.018,.09,self.palette['iron'],s['n'],8,s['object'])
        self.ring('Valve_handwheel',center,r,.012,self.palette['rust'],s['n'],s['object'])
        for i in range(3):
            angle=i*math.tau/3;edge=center+(s['u']*math.cos(angle)+s['v']*math.sin(angle))*r
            self.beam('Valve_wheel_spoke',center,edge,.014,self.palette['iron'],s['object'])
        self.features.append('管线阀门手轮')

    def toolrack(self,ref,facing=(1,0,0)):
        s=self.face(ref,facing);w=min(.60,s['w']*.75);h=.40
        self.plate(s,'Toolrack_backboard',0,0,w,h,.028,self.palette['wood'])
        self.plate(s,'Toolrack_rail',0,h*.36,w*.95,.045,.03,self.palette['iron'],.030)
        for i in [-1,0,1]:
            c=s['p']+s['u']*i*w*.29+s['n']*.055
            self.beam('Stored_tool_handle',c-s['v']*h*.25,c+s['v']*h*.38,.022,self.palette['wood'],s['object'])
            self.box('Stored_tool_head',c-s['v']*h*.25,(w*.20,.08,.045),self.palette['iron'],s['rotation'],anchor=s['object'])
        self.features.append('壁挂工具架与手工具')

    def crate(self,ref,offset=0):
        s=self.face(ref,(0,0,1));p=s['p']+s['u']*offset
        w,h,height=.48,.34,.32
        self.box('Stored_supply_crate',p+Vector((0,0,height/2-.002)),(w,h,height),self.palette['wood'],bevel=.006,anchor=s['object'])
        for z in [.06,.17,.28]:
            self.box('Crate_front_slatted_board',p+Vector((0,-h/2-.008,z)),(w*.94,.025,.075),self.palette['light'],anchor=s['object'])
        for x in [-w*.32,w*.32]:
            self.box('Crate_binding',p+Vector((x,-h/2-.025,height/2)),(.032,.025,height*.96),self.palette['iron'],anchor=s['object'])
            self.box('Crate_lid_binding',p+Vector((x,0,height+.008)),(.032,h,.025),self.palette['iron'],anchor=s['object'])
        self.box('Crate_inventory_label',p+Vector((0,-h/2-.025,height*.5)),(.14,.012,.08),self.palette['paper'],anchor=s['object'])
        self.features.append('有包边、绑带与标签的物资箱')

    def strap(self,ref):
        s=self.face(ref,(0,0,1));w,h=s['w']*.90,s['h']*.90
        self.plate(s,'Cargo_cross_strap',0,0,w,h*.10,.016,self.palette['iron'])
        self.plate(s,'Cargo_long_strap',0,0,w*.10,h,.014,self.palette['iron'],.015)
        self.plate(s,'Strap_buckle',w*.05,h*.10,w*.20,h*.18,.015,self.palette['rust'],.032)
        self.features.append('货物捆扎带及锁扣')

    def patch(self,ref):
        s=self.face(ref,(0,0,1));w=min(.48,s['w']*.60);h=min(.36,s['h']*.60)
        self.plate(s,'Weathered_repair_plate',0,0,w,h,.018,self.palette['rust'])
        self.bolts(s,w,h,min(.014,w*.04),.026)
        for i in range(3):self.plate(s,'Repair_surface_scuff',(i-1)*w*.20,0,w*.035,h*.65,.004,self.palette['wood'],.020)
        self.features.append('带铆钉的修补与磨损细节')

    def top_props(self,ref,kind,offset=0):
        s=self.face(ref,(0,0,1));scale=min(1,s['w']/.65,s['h']/.45)
        w,h=.45*scale,.28*scale
        offset=max(-s['w']/2+w/2+.01,min(offset,s['w']/2-w/2-.01))
        s['p']+=s['u']*offset
        p=s['p'];u,v,n=s['u'],s['v'],s['n']
        self.plate(s,'Utility_tray',0,0,w,h,.025,self.palette['wood'])
        if kind=='samples':
            for i in range(4):
                pos=p+u*(i-1.5)*w*.21+n*(.025+.052*scale)
                self.cylinder('Specimen_jar',pos,w*.07,.13*scale,self.palette['teal' if i%2 else 'light'],n,8,s['object'])
                self.cylinder('Jar_lid',pos+n*.065*scale,w*.08,.025*scale,self.palette['iron'],n,8,s['object'])
        elif kind=='rope':
            for i in range(3):self.ring('Rope_coil',p+n*(.035+i*.014)*scale,w*(.27+i*.045),.014*scale,self.palette['wood'],n,s['object'])
        elif kind=='books':
            for i in range(3):
                self.plate(s,'Book_binding',0,0,w*(.78-i*.04),h*.78,.018*scale,self.palette['teal' if i%2 else 'wood'],(.028+i*.052)*scale)
                self.plate(s,'Book_pages',0,0,w*(.73-i*.04),h*.72,.034*scale,self.palette['paper'],(.043+i*.052)*scale)
        elif kind=='medical':
            self.plate(s,'First_aid_case',0,0,w*.82,h*.80,.13*scale,self.palette['paper'],.026)
            self.plate(s,'Aid_cross_vertical',0,0,w*.13,h*.55,.008,self.palette['red'],.029+.13*scale)
            self.plate(s,'Aid_cross_horizontal',0,0,w*.47,h*.16,.008,self.palette['red'],.030+.13*scale)
        elif kind=='kitchen':
            for i in [-1,1]:
                c=p+u*i*w*.22+n*.038
                self.cylinder('Serving_bowl_base',c,h*.23,.018,self.palette['light'],n,12,s['object'])
                self.ring('Serving_bowl_rim',c+n*.011,h*.23,.011,self.palette['light'],n,s['object'])
            self.beam('Serving_ladle_handle',p-v*h*.35+n*.037,p+v*h*.26+n*.037,.016,self.palette['wood'],s['object'])
        elif kind=='tools':
            for i in [-1,1]:
                c=p+u*i*w*.22+n*.055*scale
                self.beam('Handtool_shaft',c-v*h*.34,c+v*h*.30,.024*scale,self.palette['wood'],s['object'])
                self.box('Handtool_head',c+v*h*.30,(w*.19,h*.20,.06*scale),self.palette['iron'],s['rotation'],anchor=s['object'])
        self.features.append({'samples':'样品瓶与收纳托盘','rope':'甲板缆绳卷','books':'成叠书本与纸页','medical':'急救用品箱','tools':'检修手工具','kitchen':'餐碗与盛菜勺'}[kind])

    def seam(self,ref,facing=(0,0,1)):
        s=self.face(ref,facing);w=s['w']*.80;h=s['h']*.88
        for x in [-w*.33,w*.33]:
            self.plate(s,'Canvas_reinforced_seam',x,0,max(.015,w*.025),h,.012,self.palette['wood'])
            for i in range(5):self.plate(s,'Canvas_cross_stitch',x,(i-2)*h*.16,max(.035,w*.055),max(.005,h*.008),.008,self.palette['light'],.014)
        self.features.append('帆布包边、缝线与加固带')

    def joint(self,ref,facing=(0,-1,0)):
        s=self.face(ref,facing);w=min(.23,s['w']*.8);h=min(.23,s['h']*.8)
        self.plate(s,'Structural_joint_plate',0,0,w,h,.015,self.palette['iron'])
        self.bolts(s,w,h,min(.014,w*.065),.025)

    def finish(self):
        bpy.context.view_layer.update()
        self.col['detail_pass']='coastal functional detail v1';self.col['features_zh']=list(dict.fromkeys(self.features))
        bpy.ops.wm.save_as_mainfile(filepath=str(self.path),compress=True)
        print('DETAILED',self.asset,'new_parts',self.counter,'features',self.col['features_zh'],flush=True)
        return {'asset':self.asset,'added_objects':self.counter,'features_zh':list(dict.fromkeys(self.features)),'source':str(self.path.relative_to(ROOT)).replace('\\','/')}


def detail_asset(d):
    a=d.asset
    if a=='Archive_DeepSeek':
        d.notice(d.find('NoticeBoard_Surface'));d.hardware('Door_Left');d.hardware('Door_Right');d.vent('Back_Vent_Grille',(0,1,0));d.patch('Roof_Patch')
    elif a=='CouncilHall_DeepSeek':
        d.notice(d.find('Community_Noticeboard_Blank'));d.hardware(d.find('Door_Leaf_-1'));d.hardware(d.find('Door_Leaf_1'));d.patch('Roof_RepairPatch_Front')
        for o in d.all('Porch_Post',4):d.joint(o)
    elif a=='DesalinationPlant_DeepSeek':
        d.gauge('PreFilter_Body');d.vent('Pump_Motor');d.valve('Pipe_Intake_1');d.valve('Pipe_Outlet_Drop')
        for o in d.all('Skid_Cross',3):d.joint(o)
    elif a=='Forge_DeepSeek':
        d.joint('SW_FireHood');d.patch('SW_ChimBand_F');d.joint('SW_Stump');d.hardware('SW_BellowsBody')
        d.hatch('SW_ForgeWall_R',(1,0,0));d.joint('SW_BellowsNozzle')
    elif a=='Greenhouse_DeepSeek':
        d.control('ControlCabinet_Body',(1,0,0));d.gauge('WaterTank_Body');d.hardware('Door_Leaf');d.vent('Roof_HighVent_Housing',(0,1,0));d.valve('RainPipe_ToTank')
        for side in ['L','R']:
            bed=d.find(f'PlantBed_{side}_Body');s=d.face(bed)
            d.plate(s,'Growing_bed_nameplate',0,0,min(.35,s['w']*.5),.09,.014,d.palette['paper'])
            for i in range(3):d.plate(s,'Crop_label_mark',(i-1)*.07,0,.035,.018,.006,d.palette['teal'],.015)
        d.features.append('种植槽分类标签')
    elif a=='LocalCommunicationsCenter_DeepSeek':
        d.notice('Panel_Board');d.control('Battery_Box',(1,0,0));d.joint('Antenna_Base',(0,0,1));d.hardware('Door_Panel');d.vent('Wall_Right',(1,0,0))
    elif a=='MedicalStation_DeepSeek':
        d.top_props('MedicalSupply_Crate_L','medical');d.strap('MedicalSupply_Crate_R');d.vent('Utility_Cabinet_Body',(1,0,0));d.hardware('Door_Panel')
    elif a=='MedicalTent_DeepSeek':
        d.seam('Canvas_Roof_L',(-1,0,.5));d.seam('Canvas_Roof_R',(1,0,.5));d.top_props('SideCrate_Lid','medical');d.strap('MedicalBag_Body')
    elif a=='PublicKitchen_DeepSeek':
        d.menu('PK_FrontWall_C');d.top_props('PK_ServiceCounter','kitchen');d.hardware('PK_Door');d.hatch('PK_StoveDoor');d.joint('PK_FlueRoofCollar',(0,0,1))
    elif a=='RescueOutpost_DeepSeek':
        d.control('Cabin_Wall_Front_M');d.hardware('Cabin_Door');d.joint('Mast_Pole');d.vent('Cabin_Wall_Back',(0,1,0))
        for o in d.all('Ladder_Mount',2)+d.all('Rail_Post_Front',2):d.joint(o)
        d.crate('Platform_Plank_1',.55)
    elif a=='RescueRadioCenter_DeepSeek':
        d.control('RRC_CtrlDoor');d.vent('RRC_BatteryBox');d.hardware('RRC_Door');d.joint('RRC_MastBase',(0,0,1));d.gauge('RRC_FuseCover')
    elif a=='ResearchStation_DeepSeek':
        d.top_props('SampleTable_Top','samples');d.notice('SideBoard_Surface',(0,-1,0));d.strap('TransportBox_Lid');d.hardware('Door_Panel');d.control('SideBox_Main',(1,0,0))
    elif a=='ResidentHut_DeepSeek':
        d.hardware('Door_Main');d.patch('Roof_Panel');d.vent('Vent_Frame',(0,1,0));d.crate('Floor_Plank_Porch_1',1.25)
        for side in [-1,1]:d.hardware(f'Window_Shutter_R_{side}',(side,0,0))
        for o in d.all('Door_Jamb',2):d.joint(o)
    elif a=='SalvageWorkshop_DeepSeek':
        d.gauge('Shear upper ram');d.vent('Workshop side wall',(1,0,0));d.patch('Roof rust patch');d.top_props('Sorting bin body','tools')
        for o in d.all('Gantry foot plate',2):d.joint(o,(0,0,1))
    elif a=='School_DeepSeek':
        d.notice('Board_Panel');d.hardware('Door_Left');d.hardware('Door_Right');d.top_props('Floor_Porch','books',-1.8);d.patch('Roof_Patch_Front')
    elif a=='SolarPowerStation_DeepSeek':
        d.control('Cabinet_Door');d.vent('Cabinet_Main',(1,0,0));d.joint('Pad_CableEntry',(0,0,1))
        for o in d.all('Rack_BasePlate',6):d.joint(o,(0,0,1))
    elif a=='StorageDepot_DeepSeek':
        d.hardware(d.find('Door_Panel_0'));d.gauge('RainBarrel_Body');d.strap('Cargo_Drum_Lid');d.patch('Loading_Awning_Panel')
        for o in d.all('Door_Frame',2):d.joint(o)
    elif a=='WoodShelter_DeepSeek':
        d.seam('Roof_Canvas');d.strap('Crate_Lid');d.top_props('Crate_Lid','rope')
        for o in d.all('Frame_Post',4):d.joint(o)
    elif a=='DriftwoodCollectionBoom_DeepSeek':
        d.top_props('Pocket_Top','rope');d.joint('Pocket_Mount_L');d.joint('Pocket_Mount_R')
        for o in d.all('Float_Saddle',6):d.joint(o,(0,0,1))
        d.features.append('浮栅夹具与连接板')
    elif a=='FishingDock_DeepSeek':
        d.strap('Crate_Lid');d.top_props('Crate_Lid','rope');d.joint('Rack_TopBar')
        for o in d.all('Deck_Plank',3):d.joint(o,(0,0,1))
    elif a=='RescueDock_DeepSeek':
        d.control('Boat_Console');d.gauge('Boat_Console',(0,-1,0))
        for o in d.all('MooringPost_Cleat_Cross',4):d.joint(o,(0,0,1))
        for o in d.all('Ladder_Mount',2):d.joint(o,(0,0,1))
        d.top_props('Boat_Seat_Aft','medical')
    elif a=='Shipyard_DeepSeek':
        d.hardware('Shed_Door');d.hatch('Shed_Exterior_Tool_Cabinet');d.top_props('Shed_Exterior_Tool_Cabinet','tools');d.patch('Shed_Roof')
        for o in d.all('Hull_Stringer_Cleat',4):d.joint(o,(0,0,1))
    elif a=='WeatherTideBuoy_DeepSeek':
        d.control('Sensor_Box');d.joint('Mast_Base',(0,0,1));d.joint('Solar_Frame',(0,0,1));d.gauge('Tide_Scale',(1,0,0))
    elif a=='WaterStorageTank':
        for i in [0,1]:d.gauge(f'Tank_Body_{i}');d.joint(f'Tank_Hatch_{i}',(0,0,1))
        for o in d.all('Base_MetalCap',4):d.joint(o)
    elif a=='DirtRoadTiles_DeepSeek':
        for root in sorted([o for o in d.model.all_objects if o.type=='EMPTY' and o.name.startswith('DirtRoad')],key=lambda o:o.name):
            d.parent=root;road=d.find(root.name+'_Road');s=d.face(road,(0,0,1))
            # Keep the full border and connection ports clear; details stay inside
            # the central 0.68 m square of each independently exported tile.
            base=root.matrix_world.translation
            for i,(x,y) in enumerate([(-.29,-.24),(.28,.25),(-.24,.29),(.27,-.26)]):
                origin=Vector((base.x+x,base.y+y,1.0));direction=Vector((0,0,-1))
                ev=road.evaluated_get(bpy.context.evaluated_depsgraph_get());inv=ev.matrix_world.inverted()
                hit,p,n,_=ev.ray_cast(inv@origin,inv.to_3x3()@direction)
                if not hit:
                    base_mesh=d.find(root.name+'_Base').evaluated_get(bpy.context.evaluated_depsgraph_get())
                    inv=base_mesh.matrix_world.inverted()
                    hit,p,n,_=base_mesh.ray_cast(inv@origin,inv.to_3x3()@direction)
                    if not hit:raise RuntimeError('Missing road shoulder surface '+root.name)
                    p=base_mesh.matrix_world@p
                else:p=ev.matrix_world@p
                d.box('Road_edge_cobble',p+Vector((0,0,.012)),(.08,.065,.032),d.palette['light'],(0,0,i*.57),.008,road)
                d.box('Weathered_road_chip',p+Vector((.035,.02,.005)),(.045,.023,.012),d.palette['wood'],(0,0,i*.43),anchor=road)
            d.parent=None
        d.features.append('道路边缘碎石与磨损，保留四向接口')
    else:raise RuntimeError('Missing detail plan '+a)

paths=sorted(SOURCE.glob('*/*_DeepSeek.blend'))+[SOURCE/'Buildings/WaterStorageTank.blend']
selected=[v.split('=',1)[1] for v in sys.argv if v.startswith('--asset=')]
if selected:paths=[p for p in paths if p.stem in selected]
records=[]
for path in paths:
    d=Detail(path);detail_asset(d);records.append(d.finish())
manifest=OUT/'detail_manifest.json'
existing=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
index={r['asset']:r for r in existing};index.update({r['asset']:r for r in records})
manifest.write_text(json.dumps(list(index.values()),ensure_ascii=False,indent=2),encoding='utf-8')
print('DETAIL_PASS_COMPLETE',len(records),flush=True)

"""Blender approximation of the runtime continuous landscape palette."""
import bpy
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=m.diffuse_color;n.inputs['Roughness'].default_value=.9;return m

def terrain_material():
 m=mat('NaturalLandscape_Preview',(.20,.28,.11));nodes=m.node_tree.nodes;links=m.node_tree.links;bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
 geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Normal'],sep.inputs[0])
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.56;ramp.color_ramp.elements[0].color=(.30,.31,.27,1);ramp.color_ramp.elements[1].position=.90;ramp.color_ramp.elements[1].color=(.18,.27,.085,1);links.new(sep.outputs['Z'],ramp.inputs[0])
 tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=1.6;tex.inputs['Detail'].default_value=3;links.new(geo.outputs['Position'],tex.inputs['Vector'])
 mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.26;links.new(ramp.outputs['Color'],mix.inputs[1]);links.new(tex.outputs['Color'],mix.inputs[2])
 pos=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],pos.inputs[0]);shore=nodes.new('ShaderNodeMapRange');shore.inputs['From Min'].default_value=-.65;shore.inputs['From Max'].default_value=.3;shore.inputs['To Min'].default_value=1;shore.inputs['To Max'].default_value=0;links.new(pos.outputs['Z'],shore.inputs['Value'])
 beach=nodes.new('ShaderNodeMixRGB');links.new(shore.outputs[0],beach.inputs[0]);links.new(mix.outputs[0],beach.inputs[1]);beach.inputs[2].default_value=(.43,.37,.24,1);links.new(beach.outputs[0],bs.inputs['Base Color'])
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.07;links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 return m

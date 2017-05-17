import bpy
import sys
import bmesh
import array
from math import *
from mathutils import *
from bpy.props import *

from gBlender import *
import SourceReloader
import G

from CBody import *
import CCloth
import CClothSrc
import CSoftBody

import Client
import Border
import Curve
import Cut
import Breasts
import CMesh
import CBodyImporter
import COrificeRig
from operator import itemgetter

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    PANEL & UI
#---------------------------------------------------------------------------    

class Panel_gBL_Object(bpy.types.Panel):      ###LEARN: Docs at http://www.blender.org/documentation/blender_python_api_2_67_release/bpy.types.Panel.html
    bl_space_type = "VIEW_3D"       ###LEARN: From "EMPTY", "VIEW_3D", "GRAPH_EDITOR", "OUTLINER", "PROPERTIES", "FILE_BROWSER", "IMAGE_EDITOR", "INFO", "SEQUENCE_EDITOR", "TEXT_EDITOR", "AUDIO_WINDOW", "DOPESHEET_EDITOR", "NLA_EDITOR", "SCRIPTS_WINDOW", "TIMELINE", "NODE_EDITOR", "LOGIG.C_EDITOR", "CONSOLE", "USER_PREFERENCES"
    bl_region_type = "TOOLS"        ###LEARN: From "WINDOW", "HEADER", "CHANNELS", "TEMPORARY", "UI", "TOOLS", "TOOL_PROPS", "PREVIEW"
    bl_context = "objectmode"       ###LEARN: From "mesh_edit", "curve_edit", "surface_edit", "text_edit", "armature_edit", "mball_edit", "lattice_edit", "posemode", "sculpt_mode", "weightpaint", "vertexpaint", "texturepaint", "particlemode", "objectmode"
    bl_label = "gBlender V.083A"
    bl_category = "gBlender"        ###LEARN: Shows up as tab name in blender panel!
  
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="WORLD")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("gbl.reload_source_files")
        col.operator("gbl.remove_game_meshes")
        col.operator("gbl.hide_game_meshes")
        col.operator("gbl.showreal")
        col.operator("gbl.showfake")
        col.operator("gbl.temp0")
        col.operator("gbl.temp1")
        col.operator("gbl.temp2")
        col.operator("gbl.temp3")
        col.operator("gbl.temp4")
        col.operator("gbl.temp5")
        col.operator("gbl.temp6")
        col.operator("gbl.temp7")
        col.operator("gbl.temp8")
        col.operator("gbl.temp9")
        col.operator("gbl.temp10")
        col.operator("gbl.temp11")
        col.operator("gbl.temp12")
        col.operator("gbl.temp13")

        

class gBL_reload_source_files(bpy.types.Operator):
    bl_idname = "gbl.reload_source_files"
    bl_label = "Reload Source"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        SourceReloader.ImportSource_ReloadFiles()
        gBL_Initialize()                            ###NOTE: Initialize normally called from OnLoad()  Manually call here to simulate load
        return {"FINISHED"}

class gBL_remove_game_meshes(bpy.types.Operator):
    bl_idname = "gbl.remove_game_meshes"
    bl_label = "Remove Game Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        gBL_Util_RemoveGameMeshes()                ###BUG!!!: Must clear cached scene properties!
        Util_RemoveProperty(bpy.context.scene, 'A-sNameSrcBody')
        Util_RemoveProperty(bpy.context.scene, 'A-sNameSrcGenitals')
        Util_RemoveProperty(bpy.context.scene, 'B-sNameSrcBody')
        Util_RemoveProperty(bpy.context.scene, 'B-sNameSrcGenitals')
        return {"FINISHED"}

class gBL_hide_game_meshes(bpy.types.Operator):
    bl_idname = "gbl.hide_game_meshes"
    bl_label = "Hide Game Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        gBL_Util_HideGameMeshes()        
        return {"FINISHED"}

class gBL_show_real(bpy.types.Operator):
    bl_idname = "gbl.showreal"
    bl_label = "Real"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        o = bpy.data.objects["WomanA"];         o.name = o.data.name = "WomanA-Fake"
        o = bpy.data.objects["WomanA-Real"];    o.name = o.data.name = "WomanA"
        o = bpy.data.objects["BodySuit"];       o.name = o.data.name = "BodySuit-Fake"
        o = bpy.data.objects["BodySuit-Real"];  o.name = o.data.name = "BodySuit"
        return {"FINISHED"}

class gBL_show_fake(bpy.types.Operator):
    bl_idname = "gbl.showfake"
    bl_label = "Fake"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        o = bpy.data.objects["WomanA"];         o.name = o.data.name = "WomanA-Real"
        o = bpy.data.objects["WomanA-Fake"];    o.name = o.data.name = "WomanA"
        o = bpy.data.objects["BodySuit"];       o.name = o.data.name = "BodySuit-Real"
        o = bpy.data.objects["BodySuit-Fake"];  o.name = o.data.name = "BodySuit"
        return {"FINISHED"}

class gBL_temp0(bpy.types.Operator):
    bl_idname = "gbl.temp0"
    bl_label = "0: Init"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        G.CGlobals.Initialize(0.02)
        return {"FINISHED"}

class gBL_temp1(bpy.types.Operator):
    bl_idname = "gbl.temp1"
    bl_label = "1: BodyBase"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBodyBase_Create(0, 'WomanA', 'WomanA','JUNK')
        CBodyBase_GetBodyBase(0).CreateCBody()
#         CBodyBase_GetBodyBase(0).OnChangeBodyMode('Play')
#         CBodyBase_GetBodyBase(0).oBody.oMeshBody.GetMesh().hide = True    ###HACK17:
#         CBodyBase_GetBodyBase(0).oMeshMorph.GetMesh().hide = True    ###HACK17:
#         bpy.data.objects['BodySuit'].hide = True
        #oBody.CreateFlexkin("TestFlexkin", 10)
        return {"FINISHED"}

class gBL_temp2(bpy.types.Operator):
    bl_idname = "gbl.temp2"
    bl_label = "2: SoftBodySkin"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context , event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        G.CGlobals.cm_nFlexParticleSpacing = 0.005       ###HACK!!!!!
        CBodyBase_GetBodyBase(0).oBody.CreateSoftBodySkin('Vagina', 1, 0.03)
        return {"FINISHED"}

class gBL_temp3(bpy.types.Operator):
    bl_idname = "gbl.temp3"
    bl_label = "3: XXX"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        #oClothSrc = CClothSrc.CClothSrc(CBodyBase_GetBodyBase(0), "BodySuit") 
        return {"FINISHED"}

class gBL_temp4(bpy.types.Operator):
    bl_idname = "gbl.temp4"
    bl_label = "4: ClothCreate"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBodyBase_GetBodyBase(0).CreateCloth("MyShirt", "Shirt", "BodySuit", "_ClothSkinnedArea_ShoulderTop")
        #CBody._aBodyBases[0].CreateSoftBody("BreastL", 0.1)        
        #CBody._aBodyBases[0].CreateCloth("MyShirt", "Shirt", "BodySuit", "_ClothSkinnedArea_Top")      ###One of the body suits?
        #CBody._aBodyBases[0].aCloths["MyShirt"].aCurves[0].oCurveO
        return {"FINISHED"}

class gBL_temp5(bpy.types.Operator):
    bl_idname = "gbl.temp5"
    bl_label = "5: ClothCut"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        #CBodyBase_GetBodyBase(0).aCloths['MyShirt'].UpdateCutterCurves()
        CBodyBase_GetBodyBase(0).aCloths['MyShirt'].CutClothWithCutterCurves()
        return {"FINISHED"}

class gBL_temp6(bpy.types.Operator):
    bl_idname = "gbl.temp6"
    bl_label = "6: Cloth3D"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBodyBase_GetBodyBase(0).aCloths['MyShirt'].ConverBackTo3D()
        return {"FINISHED"}

class gBL_temp7(bpy.types.Operator):
    bl_idname = "gbl.temp7"
    bl_label = "7: Import"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        oBodyImporter = CBodyImporter.CBodyImporter() 
        return {"FINISHED"}

class gBL_temp8(bpy.types.Operator):
    bl_idname = "gbl.temp8"
    bl_label = "8: Pose"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBodyImporter.CBodyImporter.INSTANCE.DEBUG_ShowDazPose()
        return {"FINISHED"}

class gBL_temp9(bpy.types.Operator):
    bl_idname = "gbl.temp9"
    bl_label = "9:COrificeRig()"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        #CBodyImporter.CBodyImporter.INSTANCE.CreateVisibleBoneRig()
        oOrificeRig = COrificeRig.COrificeRig(24, 0.15, True)
        return {"FINISHED"}

class gBL_temp10(bpy.types.Operator):
    bl_idname = "gbl.temp10"
    bl_label = "10:Or-Skin()"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        COrificeRig.COrificeRig.INSTANCE.AdjustAreaSkinWeights()
        #print(COrificeRig.COrificeRig.INSTANCE.SerializeOrificeRig())
        return {"FINISHED"}

class gBL_temp11(bpy.types.Operator):
    bl_idname = "gbl.temp11"
    bl_label = "11:Or-Move1()"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        COrificeRig.COrificeRig.INSTANCE.Test_MoveBones(0.0)
        return {"FINISHED"}

class gBL_temp12(bpy.types.Operator):
    bl_idname = "gbl.temp12"
    bl_label = "12:Or-Move2()"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        COrificeRig.COrificeRig.INSTANCE.Test_MoveBones(0.0125)
        return {"FINISHED"}

class gBL_temp13(bpy.types.Operator):
    bl_idname = "gbl.temp13"
    bl_label = "13:Or-Move3()"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        COrificeRig.COrificeRig.INSTANCE.Test_MoveBones(0.025)
        return {"FINISHED"}

#if __name__ == "__main__" :
bpy.utils.register_module(__name__)


        #CBody._aBodyBases[0].SlaveMesh_ResyncWithMasterMesh("BreastCol")
        #CBody(0, 'WomanA', 'Shemale', 'PenisW-EroticVR-A-Big', 5000)
        #G.CGlobals._oTempHACK = CMesh.CMeshUV("BodySuit", bpy.data.objects["BodySuit"])
        #G.CGlobals._oTempHACK.ConvertBackTo3D()
        #CBody._aBodyBases[0].aCloths["MyShirt"].PrepareClothForGame()

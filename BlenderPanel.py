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

from CBodyBase import *
from CBody import *
import CCloth
import CClothSrc
import CSoftBody
import CBodyBase

import Client
import Border
import Curve
import Cut
import Breasts
import CPenis
from CMesh import *
import CBodyImporter
import CHoleRig
from operator import itemgetter
from bpy.props import *

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    PANEL & UI
#---------------------------------------------------------------------------    

def Debug_InitDebugProperties(scn):
    bpy.types.Scene.SafetyChecks    = BoolProperty(name = "SafetyChecks")     # Set to true when some Blender-side debug actions are taken.  Read by some costly algorithms to 'less quality' so development is faster
    bpy.types.Scene.QuickMode       = BoolProperty(name = "QuickMode")     # Set to true when some Blender-side debug actions are taken.  Read by some costly algorithms to 'less quality' so development is faster
    bpy.types.Scene.Int1            = IntProperty(name = "Int1")            ###TEMP: ###IMPROVE: Improve upon this technique to dynamically create properties + widgets to control code in development?
    bpy.types.Scene.Int2            = IntProperty(name = "Int2")
    bpy.types.Scene.Int3            = IntProperty(name = "Int3")
    bpy.types.Scene.Float1          = FloatProperty(name = "Float1")
    bpy.types.Scene.Float2          = FloatProperty(name = "Float2")
    bpy.types.Scene.Float3          = FloatProperty(name = "Float3")
    bpy.types.Scene.String1         = StringProperty(name = "String1")
    bpy.types.Scene.String2         = StringProperty(name = "String2")
    bpy.types.Scene.String3         = StringProperty(name = "String3")
    return
 
Debug_InitDebugProperties(bpy.context.scene)


class Panel_gBL_Object(bpy.types.Panel):      ###INFO: Docs at http://www.blender.org/documentation/blender_python_api_2_67_release/bpy.types.Panel.html
    bl_space_type = "VIEW_3D"       ###INFO: From "EMPTY", "VIEW_3D", "GRAPH_EDITOR", "OUTLINER", "PROPERTIES", "FILE_BROWSER", "IMAGE_EDITOR", "INFO", "SEQUENCE_EDITOR", "TEXT_EDITOR", "AUDIO_WINDOW", "DOPESHEET_EDITOR", "NLA_EDITOR", "SCRIPTS_WINDOW", "TIMELINE", "NODE_EDITOR", "LOGIG.C_EDITOR", "CONSOLE", "USER_PREFERENCES"
    bl_region_type = "TOOLS"        ###INFO: From "WINDOW", "HEADER", "CHANNELS", "TEMPORARY", "UI", "TOOLS", "TOOL_PROPS", "PREVIEW"
    bl_context = "objectmode"       ###INFO: From "mesh_edit", "curve_edit", "surface_edit", "text_edit", "armature_edit", "mball_edit", "lattice_edit", "posemode", "sculpt_mode", "weightpaint", "vertexpaint", "texturepaint", "particlemode", "objectmode"
    bl_label = "gBlender V.083A"    ###:EARM: idname_must.be_all_lowercase_and_contain_one_dot
    bl_category = "gBlender"        ###INFO: Shows up as tab name in blender panel!
  
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="WORLD")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        scn = context.scene
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
        layout.prop(scn, 'SafetyChecks')
        layout.prop(scn, 'QuickMode')
        layout.prop(scn, 'Float1')
        layout.prop(scn, 'Float2')
        layout.prop(scn, 'Float3')
        layout.prop(scn, 'Int1')
        #layout.prop(scn, 'Int2')
        #layout.prop(scn, 'Int3')
        layout.prop(scn, 'String1')
        #layout.prop(scn, 'String2')
        #layout.prop(scn, 'String3')
        
        

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
        o = bpy.data.objects["Woman"];         o.name = o.data.name = "Woman-Fake"
        o = bpy.data.objects["Woman-Real"];    o.name = o.data.name = "Woman"
        o = bpy.data.objects["BodySuit"];       o.name = o.data.name = "BodySuit-Fake"
        o = bpy.data.objects["BodySuit-Real"];  o.name = o.data.name = "BodySuit"
        return {"FINISHED"}

class gBL_show_fake(bpy.types.Operator):
    bl_idname = "gbl.showfake"
    bl_label = "Fake"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        o = bpy.data.objects["Woman"];         o.name = o.data.name = "Woman-Real"
        o = bpy.data.objects["Woman-Fake"];    o.name = o.data.name = "Woman"
        o = bpy.data.objects["BodySuit"];       o.name = o.data.name = "BodySuit-Real"
        o = bpy.data.objects["BodySuit-Fake"];  o.name = o.data.name = "BodySuit"
        return {"FINISHED"}

class gBL_temp0(bpy.types.Operator):
    bl_idname = "gbl.temp0"
    bl_label = "0: Init"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        G.CGlobals.Initialize(0.02, bSkipLongUnnecessaryOps=True)
        return {"FINISHED"}

class gBL_temp1(bpy.types.Operator):
    bl_idname = "gbl.temp1"
    bl_label = "1: BodyBase"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        #CBodyBase_Create(0, 'Woman', 'Woman')
        G.CGlobals.Initialize(0.02, bSkipLongUnnecessaryOps=False)
        CBodyBase_Create(0, 'Shemale')
        CBodyBase_GetBodyBase(0).CreateCBody()
#         CBodyBase_GetBodyBase(0).OnChangeBodyMode('Play')
#         CBodyBase_GetBodyBase(0).oBody.oSkinMeshGame.GetMesh().hide = True    ###HACK17:
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
        CBodyBase_GetBodyBase(0).oBody.CreateSoftBodySkin('Penis', 1, 0.03)
        #CBodyBase_GetBodyBase(0).oBody.CreateSoftBodySkin('Vagina', 1, 0.03)
        return {"FINISHED"}

class gBL_temp3(bpy.types.Operator):
    bl_idname = "gbl.temp3"
    bl_label = "3: VG_Copy"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        #oClothSrc = CClothSrc.CClothSrc(CBodyBase_GetBodyBase(0), "BodySuit")
        #CBodyImporter.CBodyImporter_Original.Materials_MergeSlavesToMasters()
#         oMeshSrc = CMesh.Create("Woman-Original")
#         oMeshDst = CMesh.Create("Woman-Source")
        oMeshSrc = CMesh.Attach("PenisA-VertGroupReference")
        oMeshDst = CMesh.Attach("TAB_Gen3M_27097.Shape")
        CBodyImporter.Util_CopyVertGroups(oMeshSrc, oMeshDst)        
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
    bl_label = "6: Import-Penis"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        #CBodyBase_GetBodyBase(0).aCloths['MyShirt'].ConverBackTo3D()
        CBodyImporter.CBodyImporter_Penis()
        #CBodyImporter.CBodyImporter_Original() 
        return {"FINISHED"}

class gBL_temp7(bpy.types.Operator):
    bl_idname = "gbl.temp7"
    bl_label = "7: Import-Source"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBodyImporter.CBodyImporter_Source() 
        return {"FINISHED"}

class gBL_temp8(bpy.types.Operator):
    bl_idname = "gbl.temp8"
    #bl_label = "8: ?"
    bl_label = "8: PenisFit"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        #oSkinMeshGame.ShapeKeys_RemoveAll()
        CPenis.CPenisFit.INSTANCE = CPenis.CPenisFit("Woman", "Shemale")
        CPenis.CPenisFit.INSTANCE.JoinPenisToBody()
        return {"FINISHED"}

class gBL_temp9(bpy.types.Operator):
    bl_idname = "gbl.temp9"
    bl_label = "9: ShakeKeyPr"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        oMesh = CMesh.Attach(bpy.context.scene.String1)
        oMesh.ShapeKey_Print("__")
        #CBodyImporter.CBodyImporter.INSTANCE.CreateVisibleBoneRig()
        return {"FINISHED"}

class gBL_temp10(bpy.types.Operator):
    bl_idname = "gbl.temp10"
    bl_label = "10: HoleRig()"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CHoleRig.CHoleRig("Woman", 0.15)
        return {"FINISHED"}

class gBL_temp11(bpy.types.Operator):
    bl_idname = "gbl.temp11"
    bl_label = "11:Hole-Skin()"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CHoleRig.CHoleRig.INSTANCE.AdjustAreaSkinWeights()
        #print(CHoleRig.CHoleRig.INSTANCE.SerializeHoleRig())
        return {"FINISHED"}

class gBL_temp12(bpy.types.Operator):
    bl_idname = "gbl.temp12"
    bl_label = "12:Rig:Wom"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        #self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBodyBase_Create(0, 'Woman', 'Woman')
        CBodyBase_GetBodyBase(0).CreateCBody()
        return {"FINISHED"}

class gBL_temp13(bpy.types.Operator):
    bl_idname = "gbl.temp13"
    bl_label = "13:Rig:Shem"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        #self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBodyBase_Create(0, 'Shemale', 'ShemaleA')
        CBodyBase_GetBodyBase(0).CreateCBody()
        return {"FINISHED"}
        


#if __name__ == "__main__" :
bpy.utils.register_module(__name__)


        #CBody._aBodyBases[0].SlaveMesh_ResyncWithMasterMesh("BreastCol")
        #CBody(0, 'Woman', 'Shemale', 'PenisW-EroticVR-A-Big', 5000)
        #G.CGlobals._oTempHACK = CMesh.CMeshUV("BodySuit", bpy.data.objects["BodySuit"])
        #G.CGlobals._oTempHACK.ConvertBackTo3D()
        #CBody._aBodyBases[0].aCloths["MyShirt"].PrepareClothForGame()




# class CBodyImporter_Source(CBodyImporter_Base):
#     
#     def __init__(self):
#         
#         print("\n=== CBodyImporter_Source() ===")
# 
#         #=== First-order intialization of the raw DAZ mesh ===
#         self.oMesh = CMesh.Attach(self.sNamePrefix_Daz + ".Shape")              # The DAZ exporter appends '.Shape' to the actual body mesh.
#         self.oMesh.SetName(self.sNamePrefix + self.sNameSuffix)
#         self.oMesh.GetMesh().show_all_edges = True
#         SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)
#     
#         #=== Remove the root node's children that are NOT the expected mesh names (Deletes unwanted DAZ nodes like separated genitals) ===
#         oRootNodeO = SelectObject(self.oMesh.GetMesh().parent.name, True)     # Select parent node (owns the bone rig)
#         for oChildNodesO in oRootNodeO.children:
#             if oChildNodesO.name != self.oMesh.GetName():
#                 DeleteObject(oChildNodesO.name)
# 
#         if self.oMesh.Open():
#             bpy.ops.mesh.customdata_custom_splitnormals_clear()         ###INFO:!! Fixes the annoying 'Invalid clnors in this fan!' warnings... See https://blender.stackexchange.com/questions/77332/invalid-clnors-in-this-fan-warning  ###CHECK:!! Are custom loop normal useful for anything?  Placing in this super-important call appropriate for all contexts?  (Can damage some meshes??)
#             bpy.ops.mesh.select_all(action='DESELECT')          ###CHECK: No longer required?  What happened to export / import?
#             bpy.ops.object.vertex_group_sort(sort_type='NAME')
#             self.oMesh.Close()
#         
#         #=== Lock up all the DAZ vertex groups for protection ===
#         self.oMesh.VertGrp_LockUnlock(True, G.C_RexPattern_EVERYTHING)
# 
#         self.oMeshOriginal = CMesh.Attach(self.sNamePrefix + "-Original")       # Obtain access to the original mesh (Original import must have ran before!)
# 
#         DeleteObject(self.sNamePrefix_Daz)                          # Delete the just-imported armature object.  We use the armature created in original import step
#         self.oMesh.SetParent(self.sNameArmatureNode)                # Reparent the just-imported source mesh to the previously-processed armature node created in 'CBodyImporter_Original' class
# 
#         #=== Rotate and rescale all the morphs / shape keys so source mesh is properly oriented in Blender without any node rotation.  We also change their names to human-friendly names ===
#         Util_ConvertShapeKeys(self.oMesh, self.sNamePrefix_Daz)
# 
#         #=== Connect our mesh to the armature of the '-Original' mesh previously imported ===
#         self.oMesh.GetMesh().modifiers[0].name = "Armature"         # Ensure first modifier is called what we need throughout codebase (FBX sets only one modifier = Armature)
#         self.oMesh.GetMesh().modifiers["Armature"].object = bpy.data.objects[self.sNameArmatureNode]  
# 
#         #=== Copy the vertex groups from the original mesh to the just-imported 'source' one ===  ###NOTE: Note that this procedure CANNOT transfer vertex groups that have verts at exactly 0 weight!!  (Set them to a tiny value like 1e-30 or something)
#         Util_CopyVertGroups(self.oMeshOriginal, self.oMesh)        
# 
#         #=== Merge the slave materials into the master ones (as we did for the original mesh) ===
#         self.Materials_MergeSlavesToMasters(bDefineResources = False)
# 
#         #=== Modify the source woman mesh to give it new bones around vagina opening ===         ###DESIGN: Merge CHoleRig here??
#         if self.bIsWoman:
#             CHoleRig.CHoleRig(self.oMesh, 0.15)
# 
#         print("--- CBodyImporter_Source() finishes ---\n")

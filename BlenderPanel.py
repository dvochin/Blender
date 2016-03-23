###TODO: Blender to Unity morph ops
# Define class and how to serialize to Unity... built in C serializer?
# Build Sliders as in Blender
# Add more properties
# Breast move / down moving out-of-breast verts?
    # Body col and cloth collider has to move too!
        # Map vert to vert and autoadjust?  Or glue in base mesh keeping same verts
# Then... cloth in static mode... sliders with cuts!!


import bpy
import sys
import bmesh
import array
from math import *
from mathutils import *
from bpy.props import *

import gBlender
import SourceReloader
import G

import CBody
import CCloth
import CSoftBody

import Client
import Border
import Curve
import Cut
import Breasts
import Penis
import CBBodyCol

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    PANEL & UI
#---------------------------------------------------------------------------    

class Panel_gBL_Object(bpy.types.Panel):      ###LEARN: Docs at http://www.blender.org/documentation/blender_python_api_2_67_release/bpy.types.Panel.html
    bl_space_type = "VIEW_3D"       ###LEARN: From "EMPTY", "VIEW_3D", "GRAPH_EDITOR", "OUTLINER", "PROPERTIES", "FILE_BROWSER", "IMAGE_EDITOR", "INFO", "SEQUENCE_EDITOR", "TEXT_EDITOR", "AUDIO_WINDOW", "DOPESHEET_EDITOR", "NLA_EDITOR", "SCRIPTS_WINDOW", "TIMELINE", "NODE_EDITOR", "LOGIG.C_EDITOR", "CONSOLE", "USER_PREFERENCES"
    bl_region_type = "TOOLS"        ###LEARN: From "WINDOW", "HEADER", "CHANNELS", "TEMPORARY", "UI", "TOOLS", "TOOL_PROPS", "PREVIEW"
    bl_context = "objectmode"       ###LEARN: From "mesh_edit", "curve_edit", "surface_edit", "text_edit", "armature_edit", "mball_edit", "lattice_edit", "posemode", "sculpt_mode", "weightpaint", "vertexpaint", "texturepaint", "particlemode", "objectmode"
    bl_label = "gBlender V.083A"
  
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="WORLD")

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("gbl.reload_source_files")
        col.operator("gbl.remove_game_meshes")
        col.operator("gbl.hide_game_meshes")
        col.operator("gbl.temp1")
        col.operator("gbl.temp2")
        col.operator("gbl.temp3")
        col.operator("gbl.temp4")
        col.operator("gbl.temp5")
        col.operator("gbl.temp6")
        col.operator("gbl.temp7")
        col.operator("gbl.temp8")
        col.operator("gbl.temp9")

        

class gBL_reload_source_files(bpy.types.Operator):
    bl_idname = "gbl.reload_source_files"
    bl_label = "Reload Source"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        SourceReloader.ImportSource_ReloadFiles(False)
        gBlender.gBL_Initialize()                            ###NOTE: Initialize normally called from OnLoad()  Manually call here to simulate load
        return {"FINISHED"}

class gBL_remove_game_meshes(bpy.types.Operator):
    bl_idname = "gbl.remove_game_meshes"
    bl_label = "Remove Game Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        gBlender.gBL_Util_RemoveGameMeshes()                ###BUG!!!: Must clear cached scene properties!
        gBlender.Util_RemoveProperty(bpy.context.scene, 'A-sNameSrcBody')
        gBlender.Util_RemoveProperty(bpy.context.scene, 'A-sNameSrcGenitals')
        gBlender.Util_RemoveProperty(bpy.context.scene, 'B-sNameSrcBody')
        gBlender.Util_RemoveProperty(bpy.context.scene, 'B-sNameSrcGenitals')
        return {"FINISHED"}

class gBL_hide_game_meshes(bpy.types.Operator):
    bl_idname = "gbl.hide_game_meshes"
    bl_label = "Hide Game Meshes"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        gBlender.gBL_Util_HideGameMeshes()        
        return {"FINISHED"}

class gBL_temp1(bpy.types.Operator):
    bl_idname = "gbl.temp1"
    bl_label = "1: BodyInit"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        gBlender.Body_InitialPrep("WomanA")
        return {"FINISHED"}

class gBL_temp2(bpy.types.Operator):
    bl_idname = "gbl.temp2"
    bl_label = "2: CBody"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context , event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        oBody = CBody.CBody(0, 'WomanA', 'Woman', 'Vagina-Erotic9-A', 5000)
        oBody.CreateSoftBody("BreastL", True)
        oBody.CreateSoftBody("BreastR", True)
        return {"FINISHED"}

class gBL_temp3(bpy.types.Operator):
    bl_idname = "gbl.temp3"
    bl_label = "3: BreastOp"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBody.CBody._aBodies[0].Breasts_ApplyMorph('RESIZE', 'Nipple', 'Center', 'Wide', (1.6,1.6,1.6,0), None)
        return {"FINISHED"}

class gBL_temp4(bpy.types.Operator):
    bl_idname = "gbl.temp4"
    bl_label = "4: Cloth"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBody.CBody._aBodies[0].CreateCloth("BodySuit", "_ClothSkinnedArea_Top", "Shirt")      ###One of teh body suits?
        return {"FINISHED"}

class gBL_temp5(bpy.types.Operator):
    bl_idname = "gbl.temp5"
    bl_label = "5: ClothCrv"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBody.CBody._aBodies[0].aCloths["Shirt"].UpdateCutterCurves()
        return {"FINISHED"}

class gBL_temp6(bpy.types.Operator):
    bl_idname = "gbl.temp6"
    bl_label = "6: ClothCut"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBody.CBody._aBodies[0].aCloths["Shirt"].CutClothWithCutterCurves()
        return {"FINISHED"}

class gBL_temp7(bpy.types.Operator):
    bl_idname = "gbl.temp7"
    bl_label = "7: ClothGame"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBody.CBody._aBodies[0].aCloths["Shirt"].PrepareClothForGame()
        return {"FINISHED"}

class SlaveMesh_DefineMasterSlaveRelationship(bpy.types.Operator):
    bl_idname = "gbl.temp8"
    bl_label = "8: SlvCreate"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBody.SlaveMesh_DefineMasterSlaveRelationship("WomanA", "BreastCol", 0.000001)
        return {"FINISHED"}

class gBL_temp9(bpy.types.Operator):
    bl_idname = "gbl.temp9"
    bl_label = "9:SlvApply"
    bl_options = {'REGISTER', 'UNDO'}
    def invoke(self, context, event):
        self.report({"INFO"}, "GBOP: " + self.bl_label)
        CBody.CBody._aBodies[0].SlaveMesh_ResyncWithMasterMesh("BreastCol")
        return {"FINISHED"}



# class gBL_apply_morphs(bpy.types.Operator):
#     bl_idname = "gbl.apply_morphs"
#     bl_label = "Apply Morphs"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def call(self, oOp, nVal):
#         nVal = nVal / 100
#         Breasts.Breasts_ApplyMorph('BodyA_Morph', 'WomanA', oOp.sOp, oOp.sVertGrp, oOp.sFrom, oOp.sInfluence, (nVal*oOp.nRatioX, nVal*oOp.nRatioY, nVal*oOp.nRatioZ, 0), None)
#     
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         scn = context.scene
#         for nOp in aMapMorphOps:
#             oOp = aMapMorphOps[nOp]
#             nVal = scn[oOp.sName]
#             self.call(oOp, nVal)
#             
#         return {"FINISHED"}
# 
# 
# 
# 
# 
# 
# aMapMorphOps = {}
# 
# 
# class CMorphOp:       ####DEV  ####CLEANUP  ####SOON: Testing code... Finish it or remove it!
#     def CreateProperty(self, sPropName, nVal, nMin, nMax):        ###MOVE???
#         scene = bpy.context.scene
#         scene['_RNA_UI'] = scene.get('_RNA_UI', {})                         ###LEARN: Technique to add custom properties from http://blenderartists.org/forum/showthread.php?383326-How-to-create-scene-properties-from-a-string-name&p=2950142#post2950142
#         scene[sPropName] = nVal
#         scene['_RNA_UI'][sPropName] = {"name": sPropName, "description": sPropName + " description TODO", "default": nVal, "min": nMin, "max": nMax }      ###IMPROVE: Human name?, Tooltip?        
# 
#     def __init__(self, sName, sOp, sVertGrp, sFrom, sInfluence, nVal, nMin, nMax, nRatioX, nRatioY, nRatioZ):
#         self.sName      = sName
#         self.sOp        = sOp
#         self.sVertGrp   = sVertGrp
#         self.sFrom      = sFrom
#         self.sInfluence = sInfluence
#         self.nVal       = nVal
#         self.nMin       = nMin
#         self.nMax       = nMax
#         self.nRatioX    = nRatioX
#         self.nRatioY    = nRatioY
#         self.nRatioZ    = nRatioZ
#         ###self.oProp      = FloatProperty(name=sName, default=1.0, min=0.5, max=2.5)            ####SOON Put in position from post!
#         #bpy.types.Scene.Op1 = FloatProperty(name="Op1", default=100, min=50, max=2500)
#         self.CreateProperty(self.sName, self.nVal, self.nMin, self.nMax) 
#         aMapMorphOps[sName] = self
# 
# 
# 
# 
# bpy.types.Scene.SizeFromCenterREAL = FloatProperty(name="SizeFromCenterREAL", default=100, min=50, max=2500)
# 
# CMorphOp("SizeCenter",      "RESIZE",       "Nipple", "Center", "Wide",     100,  50, 200, 1, 1, 1)
# CMorphOp("MoveLeftRight",   "TRANSLATION",  "Nipple", "Center", "Wide",       0, -10,  10, 1, 0, 0)           ####HACK: Why 2 not work???: Because of same name!!!!!  Give ops an unique name!
# CMorphOp("MoveUpDown",      "TRANSLATION",  "Nipple", "Center", "Medium",     0, -10,  10, 0, 0, 1)



#if __name__ == "__main__" :
bpy.utils.register_module(__name__)


#===============================================================================
# class gBL_define_breast(bpy.types.Operator):
#     bl_idname = "gbl.define_breast"
#     bl_label = "Define Breast"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         ###oMeshBodyO = gBlender.SelectAndActivate(G.C_NameBaseCharacter + G.C_NameSuffix_Morph)        ###IMPROVE?
#         ###Breasts.BodyInit_CreateCutoffBreastFromSourceBody(oMeshBodyO)
#         return {"FINISHED"}
# 
# class gBL_perform_breast_op(bpy.types.Operator):
#     bl_idname = "gbl.perform_breast_op"
#     bl_label = "Perform breast op"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         #Breasts.Breasts_ApplyMorph("TRANSLATION", "Nipple", "Top", "Wide", (0,-.03,0,0), None)
#         Breasts.Breasts_ApplyMorph("ROTATION",    "Nipple", "Top", "Wide", -20/57, (1,0,0))
#         #Breasts.Breasts_ApplyMorph("RESIZE",      "Nipple", "Top", "Wide", (1.2,1.2,1.2,0), None)
#         return {"FINISHED"}
# 
# class gBL_update_breast(bpy.types.Operator):
#     bl_idname = "gbl.update_breast"
#     bl_label = "Update Breast"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         ###oMeshBodyO = bpy.data.objects[G.C_NameBaseCharacter + G.C_NameSuffix_Morph]
#         ###Breasts.Breast_ApplyOntoBody(oMeshBodyO)
#         return {"FINISHED"}
#===============================================================================




#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    TEMP CODE
#---------------------------------------------------------------------------    
#         col.operator("gbl.body_create_man")
#         col.operator("gbl.body_create_woman")
#         col.operator("gbl.body_create_shemale")
#         col.operator("gbl.gamemode_play_prepbody")
#         col.operator("gbl.create_body_collider")
#        col.operator("gbl.border_create_all")
#        col.operator("gbl.debug_remove_markers")

        #Penis.gBL_Penis_CalcColliders("PenisM-Erotic9-A-Big")
        #Client.CBMeshMorph_GetMorphVerts('Face', 'Face-MouthOpen')
        #oMeshBodyO = gBlender.SelectAndActivate("BodyA_Detach_Breasts")
        #oMeshBodyO = gBlender.SelectAndActivate("WomanA")
        #oBody = CBody.CBody(0, 'WomanA', 'Shemale', 'PenisW-Erotic9-A-Big')
        #oBody = CBody.CBody(0, 'WomanA', 'Woman', 'Vagina-Erotic9-A', 5000)

        #Client.IsolateHead()
        #print(Client.gBL_GetBones('WomanA'))
        #Client.Client_ConvertMesh(bpy.data.objects["BodyA_BodyCol"], True)
        #CBBodyCol.SlaveMesh_SetupMasterSlatve("BodyA-BreastCol-ToBody", "BodyA_Morph", 0.000001)
        #CBodyColBreast_GetColliderInfo("")
        #CBody.CBody._aBodies[0].CreateTempMesh(100)

        #Client.ManCleanup_RemoveExtraMaterials()
        #Client.DumpShapeKey()
        #Client.CreateBoxCollidersFromMesh_All()
        #CBBodyCol.CBBodyColSpheres_GetEncodedMesh("CBBodyColSpheres_Breasts")
        #CBBodyCol.CBBodyColBreasts_PrepareBreastMeshColliderTemplate()
        #CBBodyCol.CBSoftBreasts_GetColliderSourceMeshInfo("BodyA")
        #CBBodyCol.CBBodyCol_Generate("ManA", 1000)
        ##Client.gBL_Cloth_SplitIntoSkinnedAndSimulated("BodySuit-Top_ClothSimulated", "BodySuit-Top", "WomanA", "_ClothSkinnedArea_Top")
        ##Client.Client_ConvertMesh(gBlender.SelectAndActivate("WomanA_Morph"), True)
        #CBBodyCol.SlaveMesh_SetupMasterSlave("BodyA-BreastCol-ToBreasts", "BodyA_Detach_Breasts", 0.000001)
        #Breasts.Breasts_ApplyMorph('WomanA', 'WomanA', 'RESIZE', 'Nipple', 'Center', 'Wide', (1.6,1.6,1.6,0), None)

        #CBBodyCol.SlaveMesh_ResyncWithMasterMesh("BodyA-BreastCol-ToBody", "BodyA_Morph")
        #Client.gBL_Body_Create("BodyA", "WomanA", "Woman", "Vagina-Erotic9-A", [])
        #Client.gBL_Body_CreateForMorph("WomanA", "BodyA", "BodyA_Morph")



# class gBL_body_create_man(bpy.types.Operator):
#     bl_idname = "gbl.body_create_man"
#     bl_label = "Create M"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.gBL_Body_CreateMorphBody("A", "ManA", "PenisM-Erotic9-A-Big")
#         Client.gBL_Body_Create("BodyA", "Man", "PenisM-Erotic9-A-Big", [], 1, 0)
#         return {"FINISHED"}
# 
# class gBL_body_create_woman(bpy.types.Operator):
#     bl_idname = "gbl.body_create_woman"
#     bl_label = "Create W"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.gBL_Body_CreateMorphBody("B", "WomanA", "Vagina-Erotic9-A")
#         Client.gBL_Body_Create("BodyB", "Woman", "Vagina-Erotic9-A", ["TiedTop"], 1.3, 0.3)
#         return {"FINISHED"}
# 
# class gBL_body_create_shemale(bpy.types.Operator):
#     bl_idname = "gbl.body_create_shemale"
#     bl_label = "Create S"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.gBL_Body_CreateMorphBody("A", "WomanA", "PenisW-Erotic9-A-Big")
#         ###REV Client.gBL_Body_Create("BodyA", "Shemale", "PenisW-Erotic9-A-Big", ["TiedTop"], 1.3, 0.3)
#         Client.gBL_Body_Create("BodyA", "Shemale", "PenisW-Erotic9-A-Big", [], 1.0, 0.0)
#         return {"FINISHED"}
# 
# class gBL_gamemode_play_prepbody(bpy.types.Operator):
#     bl_idname = "gbl.gamemode_play_prepbody"
#     bl_label = "GameMode_Play_PrepBody"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.GameMode_Play_PrepBody("BodyA")
#         return {"FINISHED"}
# 
# class gBL_create_body_collider(bpy.types.Operator):
#     bl_idname = "gbl.create_body_collider"
#     bl_label = "Create Body Collider"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         #CBBodyCol.CBBodyCol_GetClothColTris("BodyA_BodyCol", "BodySuit-Top", 0.04)
#         CBBodyCol.CBBodyCol_Generate("BodyA", 3000)
#         return {"FINISHED"}
# 
# class gBL_debug_remove_markers(bpy.types.Operator):
#     bl_idname = "gbl.debug_remove_markers"
#     bl_label = "Remove Markers"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         G.Debug_RemoveMarkers()
#         return {"FINISHED"}










###LEARN: http://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Advanced_Tutorials/Python_Scripting/Addon_Custom_Property 
###LEARN: See also http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Interface
###LEARN: idname_must.be_all_lowercase_and_contain_one_dot

# class Panel_Test(bpy.types.Panel):
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "TOOLS"
#     bl_context = "objectmode"
#     bl_label = "Test Panel"
#   
#     def draw_header(self, context):
#         layout = self.layout
#         layout.label(text="", icon="WORLD")

        #ob = context.object
        #scn = context.scene
        ###BROKEN col.prop(scn, "SizeFromCenter")
        #col.prop(scn, "SizeFromCenterREAL")

        #for nOp in aMapMorphOps:
        #    oOp = aMapMorphOps[nOp]
        #    col.prop(scn, oOp.sName)
        
        #col.operator("gbl.apply_morphs")

        #layout.prop(ob, 'myRnaFloat')

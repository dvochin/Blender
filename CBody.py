### Breast colliders should be in game subfolder!
### UV seams now visible in Unity!
    # Keep extra arg in Client_ConvertMesh()?
### What is wrong with fucking names?
### Hotspots and breast morphs only in design mode.
### Start working on cloth cutting?
### Unity shows Unity2Blender mesh!
### Apply push-like functionality to keep body col on body verts.

# Missing vert on cloth body collider... can cause problem?
### Had to disable breast colliders because of inter-breast collision!  Define groups!

#? Combine call for CBodyColBreast and SlaveMesh into one??

###BUGS
#? Some weird shimmer around rim!

###IDEAS
# Two breasts now, have to have entity to manage both (e.g. hotspot, etc)>

###OLD
# Now  implement system for all detached parts to update their verts when morph body changed!  (Same with body)
# Create different hotspot for softbodies based on type and game mode (e.g. morph ops there??)

# Can now apply breast morphs to morph body...
    # Must now have mecanism to update all body parts (& collider!) once morph body changed
    # Blender pushing into Unity or Unity pulling from Blender?
    # Central mechanism needed once above decision made to 'trickle down'
        # Will have to revisit with colliders!
            # Collider have same ID even with different verts? (e.g. not one-to-one during remap??)

# Implement character editing... with all the normal entities in place?  (softbody, actors, etc) but just 'paused'
# Mesh temp still there!
# Broke breast collider for cloth. fix it!
# Broke cloth body collider?

# One breast or both??
# Problem with UV maps?  Can remove one?  What about penis / vagina?


#=== Problems ===
# Temp mesh and deletion!
# Large vagina cutout means we can't morph body!
#   Find a way to subdivide vanilla mesh?
#   Or... Re-import from DAZ a body with a top-quality vagina mesh?
#   Related: Can we import DAZ meshes and blend them there?
# Assembled mesh can only display one UV at a time?? 

#=== Improve ===
# Store permutations of source body, genitals as cached meshes?  (If quick to do don't bother?)
# Comments for functions using standard """
# user assert!


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
import CSoftBody
import CCloth
import CMesh
import Client




#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CBODY
#---------------------------------------------------------------------------    

class CBody:
    _aBodies = []                       # The global array of bodies.  Unity finds bodies

    def __init__(self, nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts):
        CBody._aBodies.append(self)                         # Append ourselves to global array.  The only way Unity can find our instance is through CBody._aBodies[<OurID>]
        self.nBodyID            = nBodyID                   # Our ID is passed in by Blender and remains the only public way to access this instance (e.g. CBody._aBodies[<OurID>])
        self.sMeshSource        = sMeshSource               # The name of the source body mesh (e.g. 'WomanA', 'ManA', etc)
        self.sSex               = sSex                      # The body's sex (one of 'Man', 'Woman' or 'Shemale')
        self.sGenitals          = sGenitals                 # The body's genitals (e.g. 'Vagina-Erotic9-A', 'PenisW-Erotic9-A' etc.)
        self.sMeshPrefix        = "Body" + chr(65 + self.nBodyID) + '-'  # The Blender object name prefix of every submesh (e.g. 'BodyA-Detach-Breasts', etc)
        self.nUnity2Blender_NumVerts = nUnity2Blender_NumVerts

        self.oMeshSource        = None                      # The 'source body'.  Never modified in any way
        self.oMeshAssembled     = None                      # The 'assembled mesh'.  Fully assembled with proper genitals.  Basis of oMeshMorph                  
        self.oMeshMorph         = None                      # The 'morphing mesh'.   Orinally copied from oMeshAssembled and morphed to the user's preference.  Basis of oMeshBody
        self.oMeshBody          = None                      # The 'body' skinned mesh.   Orinally copied from oMeshMorph.  Has softbody parts (like breasts and penis) removed. 
        self.oMeshFace          = None                      # The 'face mesh'  Simply referenced here to service Unity's request for it  
        self.oMeshSrcBreast     = None                      # Our copy of source separated breast.  Used for breast morphs

        self.aSoftBodies        = {}                        # Dictionary of CSoftBody objects representing softbody-simulated meshes.  (Contains items such as "BreastL", "BreastR", "Penis", "VaginaL", "VaginaR", to point to the object responsible for their meshes)
        self.aCloths            = {}                        # Dictionary of CCloth objects fitted to this body
        
        self.aMapVertsSrcToMorph   = {}                     # Map of which original vert maps to what morph/assembled mesh verts.  Used to traverse morphs intended for the source body                  

        
        print("\n=== CBody()  nBodyID:{}  sMeshPrefix:'{}'  sMeshSource:'{}'  sSex:'{}'  sGenitals:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sMeshSource, self.sSex, self.sGenitals))
    

        self.oMeshClothHACK = CMesh.CMesh.CreateFromExistingObject("FullShirt",  bpy.data.objects["FullShirt"])            ###DEV!!!!! 

    
        self.oMeshSource = CMesh.CMesh.CreateFromExistingObject(self.sMeshSource,            bpy.data.objects[self.sMeshSource])            ###DEV: Special ctor??
        self.oMeshFace   = CMesh.CMesh.CreateFromExistingObject(self.sMeshSource + "-Face",  bpy.data.objects[self.sMeshSource + "-Face"])
    
        #=== Duplicate the source body (kept in the most pristine condition possible) as the assembled body. Delete unwanted parts and attach the user-specified genital mesh instead ===
        self.oMeshAssembled = CMesh.CMesh.CreateFromDuplicate(self.sMeshPrefix + "Assembled", self.oMeshSource)     # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
        self.oMeshAssembled.SetParent(G.C_NodeFolder_Game)    
        sNameVertGroupToCutout = None
        if self.sGenitals.startswith("Vagina"):         # Woman has vagina and breasts
            sNameVertGroupToCutout = "_Cutout_Vagina"
        elif self.sGenitals.startswith("Penis"):        # Man & Shemale have penis
            sNameVertGroupToCutout = "_Cutout_Penis"
        if sNameVertGroupToCutout is not None:
            bpy.ops.object.mode_set(mode='EDIT')
            gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled.oMeshO, sNameVertGroupToCutout)     # This vert group holds the verts that are to be soft-body simulated...
            bpy.ops.mesh.delete(type='FACE')                    # ... and delete the mesh part we didn't want copied to output body
            bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== Import and preprocess the genitals mesh and assemble into this mesh ===
        oMeshGenitalsSource = CMesh.CMesh.CreateFromExistingObject(self.sGenitals)          ###WEAK: Create another ctor?
        oMeshGenitals = CMesh.CMesh.CreateFromDuplicate("TEMP_Genitals", oMeshGenitalsSource)
        bpy.context.scene.objects.active = oMeshGenitals.oMeshO
        bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings
     
        #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
        self.oMeshAssembled.oMeshO.select = True
        bpy.context.scene.objects.active = self.oMeshAssembled.oMeshO
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')      # Deselect all verts in assembled mesh
        bpy.ops.object.mode_set(mode='OBJECT')

        ####LEARN: Screws up ConvertMesh royally!  self.oMeshAssembled.data.uv_textures.active_index = 1       # Join call above selects the uv texture of the genitals leaving most of the body untextured.  Revert to full body texture!   ###IMPROVE: Can merge genitals texture into body's??
        gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled.oMeshO, sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
        bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###LEARN: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 

        #=== Create the custom data layer storing assembly vert index.  Enables traversal from Assembly / Morph meshes to Softbody parts 
        gBlender.DataLayer_CreateVertIndex(self.oMeshAssembled.GetName(), G.C_DataLayer_VertsAssy)
        
        #=== Prepare a ready-for-morphing body for Unity.  Also create the 'body' mesh that will have parts detached from it where softbodies are ===
        self.oMeshMorph = CMesh.CMesh.CreateFromDuplicate(self.sMeshPrefix + 'Morph', self.oMeshAssembled)   
        self.oMeshBody  = CMesh.CMesh.CreateFromDuplicate(self.sMeshPrefix + 'Body' , self.oMeshAssembled)   

        #=== Create map of source verts to morph verts ===  (Enables some morphs such as Breast morphs to be applied to morphing mesh)
        bmMorph = self.oMeshMorph.Open();
        oLayVertsSrc = bmMorph.verts.layers.int[G.C_DataLayer_VertsSrc]
        for oVert in bmMorph.verts:
            if (oVert[oLayVertsSrc] >= G.C_OffsetVertIDs):
                nVertOrig = oVert[oLayVertsSrc] - G.C_OffsetVertIDs        # Remove the offset pushed in during creation
                self.aMapVertsSrcToMorph[nVertOrig] = oVert.index       
        self.oMeshMorph.Close();

        #=== Create our own local copy of the breast mesh for breast morphs ===
        if (sSex != "Man"):
            oMeshSrcBreast = CMesh.CMesh.CreateFromExistingObject(self.sMeshSource + "-Breast")          ###WEAK: Create another ctor?
            self.oMeshSrcBreast = CMesh.CMesh.CreateFromDuplicate(self.sMeshPrefix + "Breast", oMeshSrcBreast)        
            self.oMeshSrcBreast.SetParent(G.C_NodeFolder_Game)    
        


    def CreateSoftBody(self, sSoftBodyPart, bIsBreast):
        "Create a softbody by detaching sSoftBodyPart verts from game's skinned main body"
        if (bIsBreast == True):     ####WEAK: Consider other ways of static creation branching??
            self.aSoftBodies[sSoftBodyPart] = CSoftBody.CSoftBodyBreast(self, sSoftBodyPart)  # This will enable Unity to find this instance by our self.sSoftBodyPart key and the body.
        else:
            self.aSoftBodies[sSoftBodyPart] = CSoftBody.CSoftBody(self, sSoftBodyPart)        # This will enable Unity to find this instance by our self.sSoftBodyPart key and the body.
        return "OK"


    def CreateCloth(self, sNameClothSrc, sVertGrp_ClothSkinArea, sClothType):
        "Create a CCloth object compatible with this body"
        self.aCloths[sNameClothSrc] = CCloth.CCloth(self, sNameClothSrc, sVertGrp_ClothSkinArea, sClothType)
        return "OK"
    
    
    def Morph_UpdateDependentMeshes(self):
        "Update all the softbodies connected to this body.  Needed after an operation on self.oMeshMorph"
        for oSoftBody in self.aSoftBodies.values():
            oSoftBody.Morph_UpdateDependentMeshes();
   
   
    


    #---------------------------------------------------------------------------    BREASTS

    def Breasts_ApplyMorph(self, sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue, vecOpAxis):
        "Apply a breast morph operation onto this body"
        ###DESIGN: Design decisions needed on what to do in Client and what in Blender as considerable shift is possible...
        
        sOpName = sOpMode + "_" + sOpArea + "_" + sOpPivot + "_" + sOpRange     ####PROBLEM!!!!  Not specialized enough for all cases (add extra params)
        self.oMeshSrcBreast.Open()
        bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== If a previous shape key for our operation exists we must delete it in order to guarantee that we can undo our previous ops and keep our op from influencing the other ops and keep everything 'undoable' ===
        if self.oMeshSrcBreast.oMeshO.data.shape_keys is None:                   # Add the 'basis' shape key if shape_keys is None
            bpy.ops.object.shape_key_add(from_mix=False)
        if sOpName in self.oMeshSrcBreast.oMeshO.data.shape_keys.key_blocks:
            self.oMeshSrcBreast.oMeshO.active_shape_key_index = self.oMeshSrcBreast.oMeshO.data.shape_keys.key_blocks.find(sOpName)     ###LEARN: How to find a key's index in a collection!
            bpy.ops.object.shape_key_remove()
        for oShapeKey in self.oMeshSrcBreast.oMeshO.data.shape_keys.key_blocks:       # Disable the other shape keys so our operation doesn't bake in their modifications 
            oShapeKey.value = 0
    
        #=== Create a unique shape key to this operation to keep this transformation orthogonal from the other so we can change it later or remove it regardless of transformations that occur after ===
        bpy.ops.object.mode_set(mode='EDIT')
        oShapeKey = self.oMeshSrcBreast.oMeshO.shape_key_add(name=sOpName)        ###TODO: Add shape key upon first usage so we remain orthogonal and unable to touch-up our own modifications.
        self.oMeshSrcBreast.oMeshO.active_shape_key_index = self.oMeshSrcBreast.oMeshO.data.shape_keys.key_blocks.find(sOpName)     ###LEARN: How to find a key's index in a collection!
        self.oMeshSrcBreast.oMeshO.active_shape_key.vertex_group = G.C_VertGrp_Area_BreastMorph                           ###TODO: Finalize the name of the breast vertex groups 
        oShapeKey.value = 1
        
        #=== Set the cursor to the pivot point requested ===               ###TODO: Set view as cursor and proper axis coordinates!!
        sBreastMorphPivotPt = G.C_BreastMorphPivotPt + "-" + sOpPivot
        if sBreastMorphPivotPt not in bpy.data.objects:
            return "ERROR: Could not find BreastMorphPivotPt = " + sBreastMorphPivotPt 
        oBreastMorphPivotPt = bpy.data.objects[sBreastMorphPivotPt] 
        gBlender.SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', False)
        bpy.context.scene.cursor_location = oBreastMorphPivotPt.location
    
        if sOpRange == "Wide":          ###TUNE
            nOpSize = 0.4
        elif sOpRange == "Medium":
            nOpSize = 0.2
        elif sOpRange == "Narrow":
            nOpSize = 0.1
        else:
            return "ERROR: Breasts_ApplyMorph() could not decode sOpRange " + sOpRange
    
        #=== Select the verts from predefined vertex groups that is to act as the center of the proportional transformation that is about to be executed ===
        sVertGrpName = G.C_VertGrp_Morph + sOpArea
        nVertGrpIndex = self.oMeshSrcBreast.oMeshO.vertex_groups.find(sVertGrpName)
        if (nVertGrpIndex == -1):
            return "ERROR: Breasts_ApplyMorph() could not find point op area (vertex group) '" + sVertGrpName + "'"
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Make sure we're in vert mode
        self.oMeshSrcBreast.oMeshO.vertex_groups.active_index = nVertGrpIndex
        bpy.ops.object.vertex_group_select()
    
        ###NOTE: Important coordinate conversion done in Client on a case-by-case for move/rotate/scale...  (Coordinates we receive here a purely Blender global with our z-up)  
        aContextOverride = gBlender.AssembleOverrideContextForView3dOps()    ###IMPORTANT; For view3d settings to be active when this script code is called from the context of Client we *must* override the context to the one interactive Blender user uses.
        if sOpMode == 'ROTATION':
            aResult = bpy.ops.transform.rotate(aContextOverride, value=vecOpValue, axis=vecOpAxis, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')  ###SOON?: Why only x works and bad axis??
        else:        
            aResult = bpy.ops.transform.transform(aContextOverride, mode=sOpMode, value=vecOpValue, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')    
        self.oMeshSrcBreast.Close()
    
        sResult = aResult.pop()
        if (sResult != 'FINISHED'):
            sResult = "ERROR: Breasts_ApplyMorph() transform operation did not succeed: " + sResult
            print(sResult)
            return sResult
    
        for oShapeKey in self.oMeshSrcBreast.oMeshO.data.shape_keys.key_blocks:       # Re-enable all modifications now that we've commited our transformation has been isolated to just our shape key 
            oShapeKey.value = 1
    
        sResult = "OK: Breasts_ApplyMorph() applying op '{}' on area '{}' with pivot '{}' and range '{}' with {}".format(sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue)
        self.Breast_ApplyMorphOntoMorphBody()             ####OPT: Don't need to apply everytime!  Only when batch is done!  # Apply the breasts onto the current body morph character... ####IMPROVE? Pass in name in arg?
        print(sResult)
        return sResult


    def Breast_ApplyMorphOntoMorphBody(self):
        "Apply a breast morph operation onto this body's morphing body (and update the dependant softbodies)"

        aVertsBodyMorph = self.oMeshMorph.oMeshO.data.vertices
    
        #=== 'Bake' all the shape keys in their current position into one and extract its verts ===
        aKeys = self.oMeshSrcBreast.oMeshO.data.shape_keys.key_blocks
        bpy.ops.object.shape_key_add(from_mix=True)         ###LEARN: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)
        nKeys = len(aKeys)
        aVertsBakedKeys = aKeys[nKeys-1].data               # We obtain the vert positions from the 'baked shape key'
    
        #=== Obtain custom data layer containing the vertIDs of our breast verts into body ===
        bmBreast = self.oMeshSrcBreast.Open()
        oLayBodyVerts = bmBreast.verts.layers.int[G.C_DataLayer_SourceBreastVerts]      # Each integer in this data layer stores the vertex ID of the left breast in low 16-bits and vert ID of right breast in high 16-bit  ###LEARN: Creating this kills our bmesh references!
        ###bmBreast.verts.index_update()
    
        #=== Iterate through the breast verts, extract the source verts from body from custom data layer, and set the corresponding verts in body ===
        for oVertBreast in bmBreast.verts:
            nVertsEncoded = oVertBreast[oLayBodyVerts]          ####DEV ####HACK!!!
            nVertBodyBreastL = self.aMapVertsSrcToMorph[(nVertsEncoded & 65535)]          # Breast has been defined from original body.  Map our verts to the requested morphing body  
            nVertBodyBreastR = self.aMapVertsSrcToMorph[nVertsEncoded >> 16]
            vecVert = aVertsBakedKeys[oVertBreast.index].co.copy()
            aVertsBodyMorph[nVertBodyBreastL].co = vecVert
            vecVert.x = -vecVert.x
            aVertsBodyMorph[nVertBodyBreastR].co = vecVert
        self.oMeshSrcBreast.Close()
        
        #=== Delete the 'baked' shape key we created above ===
        self.oMeshSrcBreast.oMeshO.active_shape_key_index = nKeys - 1
        bpy.ops.object.shape_key_remove()
        #self.oMeshSrcBreast.oMeshO.hide = True;        ###BUG? Causes delete???

        #=== Make sure the change we just did to the morphing body propagates to all dependent meshes ===
        self.Morph_UpdateDependentMeshes()


    

    #---------------------------------------------------------------------------    SLAVE MESH
    def SlaveMesh_ResyncWithMasterMesh(self, sTypeOfSlaveMesh):
        "Set the positions of the slave mesh verts to the positions of their coresponding verts in the master mesh (always self.oMeshMorph)"
        # Uses information previously stored in sNameSlaveMeshSlave by SlaveMesh_DefineMasterSlaveRelationship() at design time  sTypeOfSlaveMesh is like 'BreastCol', 'BodyCol', 'ClothColTop', etc
    
        sNameSlaveMeshSlave = self.sMeshSource + "-" + sTypeOfSlaveMesh + "-Slave"          ###IMPROVE: Create a function that assembles this name!
    
        oMeshSlaveO = gBlender.SelectAndActivate(sNameSlaveMeshSlave)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    
        #=== Retreive the previously-calculated information from our custom data layers ===
        bm = bmesh.from_edit_mesh(oMeshSlaveO.data)
        oLaySlaveMeshVerts = bm.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
        
        #=== Iterate through the slave mesh, find the corresponding vert in the morph body (going through map from source mesh to morph mesh) and set slave vert
        aVertsMorph = self.oMeshMorph.oMeshO.data.vertices
        for oVert in bm.verts:
            nVertSource = oVert[oLaySlaveMeshVerts]                 # Master/Slave relationship setup with master as source body...
            nVertMorph  = self.aMapVertsSrcToMorph[nVertSource]     #... but we need to set our verts to morphing body!  Use the map we have for this purpose
            oVert.co = aVertsMorph[nVertMorph].co.copy()
    
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
    
        return ""

    ###DEV
#     def SlaveMesh_GetVertMapSlaveToMaster(self, sNameMeshSlave):    # Return the map of vert-to-vert to Unity so it can restore slave-mesh verts to position of master-mesh verts.  SlaveMesh_DefineMasterSlaveRelationship() must have been called before this function
#         #=== Open the mesh and obtain BMesh and previously-constructed map in custom properties ===
#         oMeshSlaveO = gBlender.SelectAndActivate(sNameMeshSlave)
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#         bm = bmesh.from_edit_mesh(oMeshSlaveO.data)
#         bm.verts.index_update()
#         oLaySlaveMeshVerts = bm.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
#         aMapSlaveMeshSlaveToMaster = array.array('H')                           # This outgoing array stores the map of source vert to destination vert.  Used by Unity to set the slave mesh to the vert position of its master mesh
#      
#         #=== Iterate through the mesh to construct outgoing map from info previously calculated in SlaveMesh_DefineMasterSlaveRelationship() ===     
#         for oVertBM in bm.verts:
#             aMapSlaveMeshSlaveToMaster.append(oVertBM.index)
#             aMapSlaveMeshSlaveToMaster.append(oVertBM[oLaySlaveMeshVerts])
#         bpy.ops.object.mode_set(mode='OBJECT')
#         bpy.ops.object.select_all(action='DESELECT')
#      
#         #=== Send outgoing map back to Unity so it can set slave mesh to master mesh at gametime ===
#         oBA = bytearray()
#         gBlender.Stream_SerializeArray(oBA, aMapSlaveMeshSlaveToMaster.tobytes())
#         oBA += Client.Stream_GetEndMagicNo();
#         return oBA

    ###BROKEN: Related to vert traversal from source to morph body, or to destination softbody??
#     def SlaveMesh_CreateMappingArrayForUnity(self, oMeshSlave):    
#         "Create the vert-to-vert map Unity needs so it can restore slave-mesh verts to position of master-mesh verts.  SlaveMesh_DefineMasterSlaveRelationship() must have been called before this function"
#         ###DEV: Untested / unused?  ###OBS???
# 
#         #=== Open the mesh and obtain BMesh and previously-constructed map in custom properties ===
#         bm = oMeshSlave.Open()
#         bm.verts.index_update()
#         oLaySlaveMeshVerts = bm.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
#         aMapSlaveMeshSlaveToMaster = array.array('H')                           # This outgoing array stores the map of source vert to destination vert.  Used by Unity to set the slave mesh to the vert position of its master mesh
#      
#         #=== Iterate through the mesh to construct outgoing map from info previously calculated in SlaveMesh_DefineMasterSlaveRelationship() ===     
#         for oVertBM in bm.verts:
#             nVertSlave = oVertBM.index
#             nVertMorph  = self.aMapVertsSrcToMorph[nVertSlave]     #... but we need to set our verts to morphing body!  Use the map we have for this purpose
#             aMapSlaveMeshSlaveToMaster.append(nVertSlave)
#             aMapSlaveMeshSlaveToMaster.append(oVertBM[oLaySlaveMeshVerts])
#         bm = oMeshSlave.Close()
# 
#         return aMapSlaveMeshSlaveToMaster


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    SLAVE MESH
#---------------------------------------------------------------------------    

###DISCUSSION: SlaveMesh
#? Update GetVertMap()
#? Currently applied to orig vert... integrate with mechanism to drill-down?

def SlaveMesh_DefineMasterSlaveRelationship(sNameBodySrc, sTypeOfSlaveMesh, nVertTolerance, bMirror=True, bSkin=False):       ####DEV: An init call
    "Create a master / slave relationship so the slave mesh can follow the vert position of master mesh at runtime.  Only invoked at design time.  Stores its information in mesh custom layer"
    # sNameBodySrc is like 'WomanA', 'ManA'.  sTypeOfSlaveMesh is like 'BreastCol', 'BodyCol', 'ClothColTop', etc
    # bMirror is set for most colliders but NOT for breast (as each collider is handled separately)
    # (Used by breast colliders, cloth colliders, etc so they can update themselves when the source body has been morphed at runtime by the user)

    print("\n=== SlaveMesh_DefineMasterSlaveRelationship() sNameBodySrc: '{}'  sTypeOfSlaveMesh: '{}' ===".format(sNameBodySrc, sTypeOfSlaveMesh))
    
    sNameSlaveMeshSource = sNameBodySrc + "-" + sTypeOfSlaveMesh + "-Source"        # This is the design-time mesh.  It only has half the body and is mirrored to create the Slave mesh.
    sNameSlaveMeshSlave  = sNameBodySrc + "-" + sTypeOfSlaveMesh + "-Slave"         # This is the mesh that will be compled to the master mesh so we can mo
    
    #=== Copy the source mesh to a new mesh that will represent both left & right side of the body ===
    gBlender.DataLayer_RemoveLayers(sNameSlaveMeshSource)           # Design-time mesh should not have any layers.
    oMeshO = gBlender.DuplicateAsSingleton(sNameSlaveMeshSource, sNameSlaveMeshSlave, None, True)       # Create the mirrored mesh.  This is the one that will store the SlaveMesh info and be used for processing

    #=== 'Mirror' the source mesh so it represents both the left and right side of the body.  (Source only has left) ===
    if (bMirror):
        oModMirrorX = gBlender.Util_CreateMirrorModifierX(oMeshO)
        gBlender.AssertFinished(bpy.ops.object.modifier_apply(modifier=oModMirrorX.name))
    
    #=== Create mirrored mesh copy and fetch bmesh for editing ===
    oMeshCopyO   = gBlender.DuplicateAsSingleton(sNameSlaveMeshSlave, sNameSlaveMeshSlave + "_TEMPCOPY_SlaveMesh", G.C_NodeFolder_Temp, False)       # Create a temporary copy of mesh to be slaved so we can edit as we go
    oMeshMasterO = gBlender.SelectAndActivate(sNameBodySrc)
    oMeshSlaveO  = gBlender.SelectAndActivate(sNameSlaveMeshSlave)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

    #=== Create a new data layer to store the mapping between each vert to the closest vert found in sNameBodySrc ===
    bm = bmesh.from_edit_mesh(oMeshSlaveO.data)
    oLaySlaveMeshVerts = bm.verts.layers.int.new(G.C_DataLayer_SlaveMeshVerts)
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()        ###TODO Needed in later versions of Blender!
    
    #=== Find the matching vert between master mesh and its to-be-slaved mesh ===
    #print("=== Finding vert-to-vert mapping between master and slave meshes ===")
    for oVert in oMeshCopyO.data.vertices:                              # We iterate through copy mesh because Util_FindClosestVert() below must operate in object mode and we need to store info in the source mesh
        nVert = oVert.index
        vecVert = oVert.co.copy()
        nVertClosest, nDistMin, vecVertClosest = gBlender.Util_FindClosestVert(oMeshMasterO, vecVert, nVertTolerance)
        if nVertClosest != -1:
            #print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %8.6f" % (nVert, nVertClosest, vecVert.x, vecVert.y, vecVert.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
            oVertBM = bm.verts[nVert]                       # Obtain reference to our vert's through bmesh
            oVertBM.co = vecVertClosest                     # Set the source mesh vert exactly at the position of the closest vert on target mesh
            oVertBM[oLaySlaveMeshVerts] = nVertClosest       # S tore the index of the closest vert in target mesh
        else:
            print("###WARNING: Vert %3d @  (%6.3f,%6.3f,%6.3f) was not found!" % (nVert, vecVert.x, vecVert.y, vecVert.z))
    
    #=== Close the mesh and delete copy ====
    bpy.ops.object.mode_set(mode='OBJECT')
    gBlender.DeleteObject(oMeshCopyO.name)              # Delete the temporary mesh  ###PROBLEM!!! When Unity calls this DeleteObject destroys two meshes!!!

    #=== Skin the slave mesh to the original mesh if required ===    
    if (bSkin):         ###IMPROVE: Remove existing skin info?
        oMeshSlaveO = gBlender.SelectAndActivate(sNameSlaveMeshSlave)
        oMeshSourceO = bpy.data.objects[sNameBodySrc]
        oMeshSourceO.select = True                             # Select the original rim mesh (keeping rim+tetraverts mesh activated)
        oMeshSourceO.hide = False
        bpy.ops.object.vertex_group_transfer_weight()
        gBlender.Cleanup_VertGrp_RemoveNonBones(oMeshSlaveO)
    
    bpy.ops.object.select_all(action='DESELECT')




#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CBODY PUBLIC ACCESSOR
#---------------------------------------------------------------------------    

def CBody_Create(nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts):
    "Proxy for CBody ctor as we can only return primitives back to Unity"
    oBody = CBody(nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts)
    return str(oBody.nBodyID)           # Strings is one of the only things we can return to Unity

def CBody_GetBody(nBodyID):
    "Easy accessor to simplify Unity's access to bodies by ID"
    return CBody._aBodies[nBodyID]

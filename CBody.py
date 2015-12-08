###NOW: Finally back and forth!
# Can now morph from Unity...
# Need to convert CBSoft modes to transitions instead.
    # Start with define mode, then game mode (until we have top-level menu)
# Then start on redoing the bodycol (pair mesh?) to survive morphs
# Then boobs collider in both mode...
# Then constant update to cloth in all modes...
# Then cloth cutting!!

# Morph of breast plate up/down:  Too much effort just for that.  Integrate it a new shape keys when we re-import from DAZ

# Create CMesh class!  Open and close, obtain BMesh, various ops, etc
# What is wrong with fucking names?
# Some weird shimmer around rim!

# Two breasts now, have to have entity to manage both (e.g. hotspot, etc)>


###RESUME:
## Now have half-baked init destroy with some bug on 2nd init... still temp mesh a problem!
# Now  implement system for all detached parts to update their verts when morph body changed!  (Same with body)
# Create different hotspot for softbodies based on type and game mode (e.g. morph ops there??)

### Razor line between breasts and body now??? WTF went wrong??

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
import Client





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

        self.aSoftBodies        = {}                        # Dictionary of CSoftBody objects representing softbody-simulated meshes.  (Contains items such as "BreastL", "BreastR", "Penis", "VaginaL", "VaginaR", to point to the object responsible for their meshes)
        
        self.aMapVertsSrcToMorph   = {}                    # Map of which original vert maps to what morph/assembled mesh verts.  Used to traverse morphs intended for the source body                  
        
        print("\n=== CBody()  nBodyID:{}  sMeshPrefix:'{}'  sMeshSource:'{}'  sSex:'{}'  sGenitals:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sMeshSource, self.sSex, self.sGenitals))
    
        self.oMeshSource = bpy.data.objects[self.sMeshSource]
        self.oMeshFace = bpy.data.objects[self.sMeshSource + "-Face"]
    
        #=== Duplicate the source body (kept in the most pristine condition possible) as the assembled body. Delete unwanted parts and attach the user-specified genital mesh instead ===    
        self.oMeshAssembled = gBlender.DuplicateAsSingleton(self.oMeshSource.name, self.sMeshPrefix + "Assembled", G.C_NodeFolder_Game, False)  # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
        
        sNameVertGroupToCutout = None
        if self.sGenitals.startswith("Vagina"):         # Woman has vagina and breasts
            sNameVertGroupToCutout = "_Cutout_Vagina"
        elif self.sGenitals.startswith("Penis"):        # Man & Shemale have penis
            sNameVertGroupToCutout = "_Cutout_Penis"
        if sNameVertGroupToCutout is not None:
            bpy.ops.object.mode_set(mode='EDIT')
            gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled, sNameVertGroupToCutout)     # This vert group holds the verts that are to be soft-body simulated...
            bpy.ops.mesh.delete(type='FACE')                    # ... and delete the mesh part we didn't want copied to output body
            bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== Import and preprocess the genitals mesh and assemble into this mesh ===
        oMeshGenitalsO = gBlender.DuplicateAsSingleton(self.sGenitals, "TEMP_Genitals", G.C_NodeFolder_Temp, True)  ###TEMP!! Commit to file-based import soon!
        bpy.context.scene.objects.active = oMeshGenitalsO
        bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings
     
        #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
        self.oMeshAssembled.select = True
        bpy.context.scene.objects.active = self.oMeshAssembled
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')      # Deselect all verts in assembled mesh
        bpy.ops.object.mode_set(mode='OBJECT')

        ####LEARN: Screws up ConvertMesh royally!  self.oMeshAssembled.data.uv_textures.active_index = 1       # Join call above selects the uv texture of the genitals leaving most of the body untextured.  Revert to full body texture!   ###IMPROVE: Can merge genitals texture into body's??
        gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled, sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
        bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###LEARN: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 

        #=== Create the custom data layer storing assembly vert index.  Enables traversal from Assembly / Morph meshes to Softbody parts 
        gBlender.DataLayer_CreateVertIndex(self.oMeshAssembled.name, G.C_DataLayer_VertsAssy)
        
        #=== Prepare a ready-for-morphing body for Unity.  Also create the 'body' mesh that will have parts detached from it where softbodies are ===   
        self.oMeshMorph = gBlender.DuplicateAsSingleton(self.oMeshAssembled.name, self.sMeshPrefix + 'Morph',   G.C_NodeFolder_Game, True)
        self.oMeshBody  = gBlender.DuplicateAsSingleton(self.oMeshAssembled.name, self.sMeshPrefix + 'Body',    G.C_NodeFolder_Game, True)

        #=== Create map of source verts to morph verts ===  (Enables some morphs such as Breast morphs to be applied to morphing mesh)
        gBlender.SelectAndActivate(self.oMeshMorph.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(self.oMeshMorph.data)
        oLayVertsSrc = bm.verts.layers.int[G.C_DataLayer_VertsSrc]
        for oVert in bm.verts:
            if (oVert[oLayVertsSrc] >= G.C_OffsetVertIDs):
                nVertOrig = oVert[oLayVertsSrc] - G.C_OffsetVertIDs        # Remove the offset pushed in during creation
                self.aMapVertsSrcToMorph[nVertOrig] = oVert.index       
        bpy.ops.object.mode_set(mode='OBJECT')




    def CreateSoftBody(self, sSoftBodyPart):
        "Create a softbody by detaching sSoftBodyPart verts from game's skinned main body"
        self.aSoftBodies[sSoftBodyPart] = CSoftBody.CSoftBody(self, sSoftBodyPart)        # This will enable Unity to find this instance by our self.sSoftBodyPart key and the body.
        return "OK"


    
    def Morph_UpdateDependentMeshes(self):
        "Update all the softbodies connected to this body.  Needed after an operation on self.oMeshMorph"
        for oSoftBody in self.aSoftBodies.values():
            oSoftBody.Morph_UpdateDependentMeshes();
   
   
    
    def Breasts_ApplyOp(self, sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue, vecOpAxis):
        "Apply a breast morph operation onto this body"
        ###DESIGN: Design decisions needed on what to do in Client and what in Blender as considerable shift is possible...
        
        sOpName = sOpMode + "_" + sOpArea + "_" + sOpPivot + "_" + sOpRange     ####PROBLEM!!!!  Not specialized enough for all cases (add extra params)
        sNameSrcBreast = self.oMeshSource.name + G.C_NameSuffix_Breast
        oMeshSrcBreastO = gBlender.SelectAndActivate(sNameSrcBreast)                     ###DESIGN: Make generic!
        bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== If a previous shape key for our operation exists we must delete it in order to guarantee that we can undo our previous ops and keep our op from influencing the other ops and keep everything 'undoable' ===
        if oMeshSrcBreastO.data.shape_keys is None:                   # Add the 'basis' shape key if shape_keys is None
            bpy.ops.object.shape_key_add(from_mix=False)
        if sOpName in oMeshSrcBreastO.data.shape_keys.key_blocks:
            oMeshSrcBreastO.active_shape_key_index = oMeshSrcBreastO.data.shape_keys.key_blocks.find(sOpName)     ###LEARN: How to find a key's index in a collection!
            bpy.ops.object.shape_key_remove()
        for oShapeKey in oMeshSrcBreastO.data.shape_keys.key_blocks:       # Disable the other shape keys so our operation doesn't bake in their modifications 
            oShapeKey.value = 0
    
        #=== Create a unique shape key to this operation to keep this transformation orthogonal from the other so we can change it later or remove it regardless of transformations that occur after ===
        bpy.ops.object.mode_set(mode='EDIT')
        oShapeKey = oMeshSrcBreastO.shape_key_add(name=sOpName)        ###TODO: Add shape key upon first usage so we remain orthogonal and unable to touch-up our own modifications.
        oMeshSrcBreastO.active_shape_key_index = oMeshSrcBreastO.data.shape_keys.key_blocks.find(sOpName)     ###LEARN: How to find a key's index in a collection!
        oMeshSrcBreastO.active_shape_key.vertex_group = G.C_VertGrp_Area_BreastMorph                           ###TODO: Finalize the name of the breast vertex groups 
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
            return "ERROR: Breasts_ApplyOp() could not decode sOpRange " + sOpRange
    
        #=== Select the verts from predefined vertex groups that is to act as the center of the proportional transformation that is about to be executed ===
        sVertGrpName = G.C_VertGrp_Morph + sOpArea
        nVertGrpIndex = oMeshSrcBreastO.vertex_groups.find(sVertGrpName)
        if (nVertGrpIndex == -1):
            return "ERROR: Breasts_ApplyOp() could not find point op area (vertex group) '" + sVertGrpName + "'"
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Make sure we're in vert mode
        oMeshSrcBreastO.vertex_groups.active_index = nVertGrpIndex
        bpy.ops.object.vertex_group_select()
    
        ###NOTE: Important coordinate conversion done in Client on a case-by-case for move/rotate/scale...  (Coordinates we receive here a purely Blender global with our z-up)  
        aContextOverride = gBlender.AssembleOverrideContextForView3dOps()    ###IMPORTANT; For view3d settings to be active when this script code is called from the context of Client we *must* override the context to the one interactive Blender user uses.
        if sOpMode == 'ROTATION':
            aResult = bpy.ops.transform.rotate(aContextOverride, value=vecOpValue, axis=vecOpAxis, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')  ###SOON?: Why only x works and bad axis??
        else:        
            aResult = bpy.ops.transform.transform(aContextOverride, mode=sOpMode, value=vecOpValue, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')    
        bpy.ops.object.mode_set(mode='OBJECT')
    
        sResult = aResult.pop()
        if (sResult != 'FINISHED'):
            sResult = "ERROR: Breasts_ApplyOp() transform operation did not succeed: " + sResult
            print(sResult)
            return sResult
    
        for oShapeKey in oMeshSrcBreastO.data.shape_keys.key_blocks:       # Re-enable all modifications now that we've commited our transformation has been isolated to just our shape key 
            oShapeKey.value = 1
    
        sResult = "OK: Breasts_ApplyOp() applying op '{}' on area '{}' with pivot '{}' and range '{}' with {}".format(sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue)
        self.Breast_ApplyOntoBody()             ####OPT: Don't need to apply everytime!  Only when batch is done!  # Apply the breasts onto the current body morph character... ####IMPROVE? Pass in name in arg?
        print(sResult)
        return sResult


    def Breast_ApplyOntoBody(self):
        "Apply a breast morph operation onto this body's morphing body (and update the dependant softbodies)"

        aVertsBodyMorph = self.oMeshMorph.data.vertices
        sNameBreast = self.oMeshSource.name + G.C_NameSuffix_Breast
        oMeshBreast = gBlender.SelectAndActivate(sNameBreast)
    
        #=== 'Bake' all the shape keys in their current position into one and extract its verts ===
        aKeys = oMeshBreast.data.shape_keys.key_blocks
        bpy.ops.object.shape_key_add(from_mix=True)         ###LEARN: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)
        nKeys = len(aKeys)
        aVertsBakedKeys = aKeys[nKeys-1].data               # We obtain the vert positions from the 'baked shape key'
    
        #=== Obtain custom data layer containing the vertIDs of our breast verts into body ===
        bpy.ops.object.mode_set(mode='EDIT')
        bmBreast = bmesh.from_edit_mesh(oMeshBreast.data)
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
        bpy.ops.object.mode_set(mode='OBJECT')
        
        #=== Delete the 'baked' shape key we created above ===
        oMeshBreast.active_shape_key_index = nKeys - 1
        bpy.ops.object.shape_key_remove()
        oMeshBreast.hide = True;

        #=== Make sure the change we just did to the morphing body propagates to all dependent meshes ===
        self.Morph_UpdateDependentMeshes()
    



def CBody_Create(nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts):
    "Proxy for CBody ctor as we can only return primitives back to Unity"
    oBody = CBody(nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts)
    return str(oBody.nBodyID)           # Strings is one of the only things we can return to Unity

def CBody_GetBody(nBodyID):
    "Easy accessor to simplify Unity's access to bodies by ID"
    return CBody._aBodies[nBodyID]

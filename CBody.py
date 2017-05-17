###LAST: Can now have Unity-2-Blender morph flow...
# Moving breasts down cause morph result mesh to break at seams... because of split of verts for Unity.
    # Does latest Unity still need that??  Can it have double UVs?
    # Could also import body via FBX and just move verts?  (Would be pain in the ass with detached parts tho)
# Develop pipe to absorb all the morphs into one body shareable with Unity...
# Can either create a new body at every refresh or copy verts every time??  (Could also improve this with a new C++ pipe for shape key block sharing??)
# Also need to serialize CObject get/set and create panel in Unity :)
#        bpy.ops.object.shape_key_add(from_mix=True)         ###LEARN: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)



#    bm.verts.index_update()
#    bm.verts.ensure_lookup_table()        ###TODO Needed in later versions of Blender!


### Breast colliders should be in game subfolder!
### UV seams now visible in Unity!
    # Keep extra arg in Client_ConvertMeshForUnity()?
### What is wrong with fucking names?
### Hotspots and breast morphs only in design mode.
### Start working on cloth cutting?
### Unity shows Unity2Blender mesh!
### Apply push-like functionality to keep body col on body verts.

# Missing vert on cloth body collider... can cause problem?
### Had to disable breast colliders because of inter-breast collision!  Define groups!

###BUGS
# ? Some weird shimmer around rim!

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

from gBlender import *
import G
import CSoftBody
import CCloth
import CClothSrc
import CMesh
import Client
import CFlexSkin
import COrificeRig
import CObject




#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CBODYBASE
#---------------------------------------------------------------------------    

class CBodyBase:
    _aBodyBases = []  # The global array of bodies.  Unity acceses body instances through this one global collection

    def __init__(self, nBodyID, sMeshSource, sSex, sGenitals):
        self.nBodyID = nBodyID              # Our ID is passed in by Blender and remains the only public way to access this instance (e.g. CBody._aBodyBases[<OurID>])
        self.sMeshSource = sMeshSource      # The name of the source body mesh (e.g. 'WomanA', 'ManA', etc)        ###TODO11: Separate sex from mesh version!
        self.sSex = sSex                    # The body's sex (one of 'Man', 'Woman' or 'Shemale')
        self.sGenitals = sGenitals          # The body's genitals (e.g. 'Vagina-EroticVR-A', 'PenisW-EroticVR-A' etc.)
        self.sMeshPrefix = "B" + chr(65 + self.nBodyID) + '-'  # The Blender object name prefix of every submesh (e.g. 'BodyA-Detach-Breasts', etc)
        
        self.oBody = None                   # Our game-time body.  Created when we enter play mode, destroyed when we leave play mode for configure mode.
        self.sBodyBaseMode = "Uninitialized"      # The Body Base mode.  Blender equivalent of Unity's CBodyBase._eBodyBaseMode enumeration

        self.oMeshSource = None             # The 'source body'.  Never modified in any way
        self.oMeshAssembled = None          # The 'assembled mesh'.  Fully assembled with proper genitals.  Basis of oMeshMorph                  
        self.oMeshMorph = None              # The 'morphing mesh'.   Orinally copied from oMeshAssembled and morphed to the user's preference.  Basis of oMeshBody
        self.oMeshMorphResult = None        # The 'baked' morphing mesh.   Baled version of the body mesh as adjusted by the user's morphing selection.  This is the (only) mesh serialized to Unity and updated every morphing change for WYSIWYG real-time updates.
        
        self.oNodeRoot = None  # The root Blender node (an empty) where we store all our objects under.  Used to de-clutter Blender outline)

        self.oObjectMeshShapeKeys = None    # The Unity-editable shape keys that enable Unity player to morph our body.    
        self.aVertsFlexCollider = CByteArray()  # Collection of verts sent to Unity that determine which verts form a morphing-time Flex collider capable of repelling morph-time bodysuit master cloth.
        self.aCloths = {}                   # Dictionary of CCloth objects fitted to this body
        
        self.oOrificeRig = None             # Orifice rig for this body (in charge of building Flex collider for body orifice (vagina, anus)


        print("\n=== CBodyBase()  nBodyID:{}  sMeshPrefix:'{}'  sMeshSource:'{}'  sSex:'{}'  sGenitals:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sMeshSource, self.sSex, self.sGenitals))

        
        CBodyBase._aBodyBases.append(self)  # Append ourselves to global array.  The only way Unity can find our instance is through CBody._aBodyBases[<OurID>]
        SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)     # Make sure we're starting Blender operations with Blender in a known state...
        self.oMeshSource = CMesh.CMesh.CreateFromExistingObject(self.sMeshSource, bpy.data.objects[self.sMeshSource])  ###DEV: Special ctor??

        #=== Create a empty node in game folder where every mesh related to this body will go ===
        self.oNodeRoot = CreateEmptyBlenderNode("Body" + chr(65 + self.nBodyID), G.C_NodeFolder_Game)

        #=== Duplicate the source body (kept in pristine condition) as the assembled body. Delete unwanted parts and attach the user-specified genital mesh instead ===
        self.oMeshAssembled = CMesh.CMesh.CreateFromDuplicate(self.sMeshPrefix + "Assembled", self.oMeshSource)  # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
        self.oMeshAssembled.SetParent(self.oNodeRoot.name)
        self.oMeshAssembled.ConvertMeshForUnity(True)  ###DESIGN13: This early??

        #=== Prepare a ready-for-morphing body for Unity.  Also create the 'body' mesh that will have parts detached from it where softbodies are ===
        self.oMeshMorph = CMesh.CMesh.CreateFromDuplicate(self.sMeshPrefix + 'Morph', self.oMeshAssembled)   
        self.oMeshMorph.SetParent(self.oNodeRoot.name)

        #=== Prepare the Unity-serialized mesh that is updated every time player adjusts a slider ===
        self.oMeshMorphResult = CMesh.CMesh.CreateFromDuplicate(self.sMeshPrefix + 'MorphResult', self.oMeshMorph)   
        self.oMeshMorphResult.SetParent(self.oNodeRoot.name)
        bpy.ops.object.shape_key_remove(all=True)  # Remove all the shape keys of the outgoing mesh.  We set its verts manually at every morph change.

        #=== Connect our Unity-editable collection of properties so Unity player can edit our body mesh ===
        self.oObjectMeshShapeKeys = CObject.CObjectMeshShapeKeys("Body Mesh Shape Keys", self.oMeshMorph.GetName())  # The Unity-visible CObject properties.  Enables Unity to manipulate morphing body's morphs
        # self.oObjectMeshShapeKeys.PropSet("Breasts-Implants", 1.0)

        #=== Form the collection of Flex collider verts Unity will use to form a Flex collider capable of repelling morph-time bodysuit ===
        bAllVertsInCollider = True          ###NOTE: Bit of a hack to avoid having to define this damn group at every mesh rebuild... should be defined for final game tho!
        if VertGrp_FindByName(self.oMeshMorphResult.GetMesh(), "_CFlexCollider", False):
            VertGrp_SelectVerts(self.oMeshMorphResult.GetMesh(), "_CFlexCollider")
            bAllVertsInCollider = False
        else:
            print("\n###WARNING: _CFlexCollider vertex group not found = Inneficient collisions!")
        bmMorphResult = self.oMeshMorphResult.Open()
        for oVert in bmMorphResult.verts:
            if (oVert.select or bAllVertsInCollider):
                self.aVertsFlexCollider.AddUShort(oVert.index)
        self.oMeshMorphResult.Close()
        

    def UpdateMorphResultMesh(self):  # 'Bake' the morphing mesh as per the player's morphing parameters into a 'MorphResult' mesh that can be serialized to Unity.  Matches Unity's CBodyBase.UpdateMorphResultMesh()
        #=== 'Bake' all the shape keys in their current position into one and extract its verts ===
        SelectAndActivate(self.oMeshMorph.GetName())
        aKeys = self.oMeshMorph.GetMesh().data.shape_keys.key_blocks
        bpy.ops.object.shape_key_add(from_mix=True)  ###LEARN: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)
        nKeys = len(aKeys)
        aVertsBakedKeys = aKeys[nKeys - 1].data  # We obtain the vert positions from the 'baked shape key'
    
        #=== Obtain reference to the morphing mesh and the morphing result mesh ===
        bmMorph = self.oMeshMorph.Open()
        aVertsMorphResults = self.oMeshMorphResult.GetMesh().data.vertices
    
        #=== Iterate through the verts, extract the 'baked' position of the just-created 'mix' shape key to set the position of the outgoing MorphResult mesh
        for oVert in bmMorph.verts:
            vecVert = aVertsBakedKeys[oVert.index].co.copy()  # Get the final morphing position...
            aVertsMorphResults[oVert.index].co = vecVert  # And apply it to outgoing mesh so Unity can get its refreshed vert positions
        self.oMeshMorph.ExitFromEditMode()
        
        #=== Delete the 'baked' shape key we created above ===
        self.oMeshMorph.GetMesh().active_shape_key_index = nKeys - 1
        bpy.ops.object.shape_key_remove()
        self.oMeshMorph.Close()
        
        return "OK"  # Called from Unity so we must return something


    #---------------------------------------------------------------------------    MORPH EXTRACTION
    def CMorphChannel_GetMorphVerts(self, sNameShapeKey):  # Called by CBMeshMorph to get the morphed verts on a given shape key and a given mesh.  Used to morph non-skinned meshes at runtime such as face eyelids and mouth open/close
        #=== Find requested shape key to obtain morph data ===
        oMeshMorphO = self.oMeshMorph.GetMesh()
        oMeshShapeKeyBlocks = oMeshMorphO.data.shape_keys.key_blocks
        if sNameShapeKey in oMeshShapeKeyBlocks:
            nMorphKeyBlockIndex = oMeshShapeKeyBlocks.find(sNameShapeKey)  ###LEARN: How to find a key's index in a collection! (Set by oMeshMorphO.active_shape_key_index)
        else:
            return G.DumpStr("ERROR: CMorphChannel_GetMorphVerts() cannot find shape key " + sNameShapeKey)
     
        #=== Obtain access to shape key vert data ===        
        aVertsBasis = oMeshShapeKeyBlocks[0].data                       # 'Basis' is always index zero
        aVertsMorph = oMeshShapeKeyBlocks[nMorphKeyBlockIndex].data     # We obtain the vert positions from the 'baked shape key'  ###LEARN: How to get raw shape key data
        bm = bmesh.new()                                ###LEARN: How to operate with bmesh without entering edit mode!        ###TODO11: Change codebase to this technique?
        bm.from_object(oMeshMorphO, bpy.context.scene)  ###DESIGN: Selection of body! 
     
        #=== Iterate through all the mesh verts and test all verts that are different for the given shape key so we can serialize its delta data to client
        print("\n=== CMorphChannel_GetMorphVerts('{}', '{}' ===".format(self.oMeshMorph.GetName(), sNameShapeKey))
        oBA = CByteArray()
        nMorphedVerts = 0
        for oVert in bm.verts:
            vecVertBasis = aVertsBasis[oVert.index].co
            vecVertMorph = aVertsMorph[oVert.index].co
            vecVertDelta = vecVertMorph - vecVertBasis
            nLengthDelta = vecVertDelta.length
            if (nLengthDelta >= 0.0001):           # Don't bother with verts that change such a tiny amount to optimize performance          #if vecVertBasis != vecVertMorph:            ###LEARN: For some reason this doesn't work!  It lets through tiny values through like 0.00000001!
                #print("{:4}  #{:5} = Dist {:6.4} = ({:10.7},{:10.7},{:10.7})".format(nMorphedVerts, oVert.index, nLengthDeltaSqr, vecVertDelta.x, vecVertDelta.y, vecVertDelta.z))
                oBA.AddFloat(oVert.index)         ###NOTE: Packing ID as a float so that we can conveniently view all data as float (as vector is three floats)
                oBA.AddVector(vecVertDelta)
                nMorphedVerts += 1

        return oBA.Unity_GetBytes()


    def CreateCloth(self, sNameCloth, sClothType, sNameClothSrc):
        "Create a CCloth object compatible with this body base"
        self.aCloths[sNameCloth] = CCloth.CCloth(self, sNameCloth, sClothType, sNameClothSrc)
        return "OK"

    def DestroyCloth(self, sNameCloth):
        "Destroy the specified cloth from this body base"
        self.aCloths[sNameCloth].DoDestroy()
        del self.aCloths[sNameCloth]
        return "OK"

    def CreateCBody(self):
        print("\n=== CBodyBase.CreateCBody() called on CBodyBase '{}' ===".format(self.sMeshPrefix))
        if (self.oBody == None):
            self.oBody = CBody(self)                # Create a game-time body.  Expensive operation!
        return "OK"

    def DestroyCBody(self):                 # Called by Unity so a body base can free the resources from its CBody instance (game-time body)  (Means the user went back to body editing)
        print("\n=== CBodyBase.DestroyCBody() called on CBodyBase '{}' ===".format(self.sMeshPrefix))
        if (self.oBody != None):
            self.oBody = self.oBody.DoDestroy()     # Destroy the entire gametime body... lots of meshes!
        return "OK"

    def SelectClothSrc_HACK(self, sNameClothSrc):           ###HACK18: To overcome Unity's CBMesh.Create requiring every mesh to be accessible from a CBodyBase instance.
        self.oClothSrcSelected_HACK = CMesh.CMesh.CreateFromExistingObject(G.CGlobals.cm_aClothSources[sNameClothSrc].oMeshO_3DS.name)       # 'Select' the current cloth src and put it in this variable.  It will the be pulled by Unity to interact with the cloth source
        return "OK"

    def CreateOrificeRig(self):
        self.oOrificeRig = COrificeRig.COrificeRig(24, 0.10)        ###DEV19: Args to Unity?
        return self.oOrificeRig.SerializeOrificeRig()

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CBODY
#---------------------------------------------------------------------------    

class CBody:

    def __init__(self, oBodyBase):
        self.oBodyBase = oBodyBase          # Our owning body base.  In charge of creating / destroying us.  Body base is form morphing / configuration, CBody for gameplay
        self.oMeshBody = None               # The 'body' skinned mesh.   Orinally copied from oMeshMorph.  Has softbody parts (like breasts and penis) removed. 
        self.oMeshFlexCollider = None       # The 'Flex collider' skinned mesh.  Responsible for repelling clothing, softbody body parts and fluid away from the body. 
        self.oMeshSrcBreast = None          # Our copy of source separated breast.  Used for breast morphs        ###OBS?

        self.aSoftBodies = {}               # Dictionary of CSoftBody objects representing softbody-simulated meshes.  (Contains items such as "BreastL", "BreastR", "Penis", to point to the object responsible for their meshes)
        
        self.aMapVertsSrcToMorph = {}  # Map of which original vert maps to what morph/assembled mesh verts.  Used to traverse morphs intended for the source body                  

        print("\n=== CBody()  nBodyID:{}  sMeshPrefix:'{}' ===".format(self.oBodyBase.nBodyID, self.oBodyBase.sMeshPrefix))
    
        #=== Create the main skinned body from the base's MorphResult mesh.  This mesh will have softbody body parts cut out from it ===
        self.oMeshBody = CMesh.CMesh.CreateFromDuplicate(self.oBodyBase.sMeshPrefix + 'Body' , self.oBodyBase.oMeshMorphResult)
        Cleanup_RemoveDoublesAndConvertToTris(0.000001)                                 # Convert to tris and remove the super-close geometry                             
        self.oMeshBody.SetParent(self.oBodyBase.oNodeRoot.name)
        
        #=== Create a data layer that will store source body verts for possible vert domain traversal (e.g. soft body skin) ===
        bmBody = self.oMeshBody.Open()
        oLayVertSrcBody = bmBody.verts.layers.int.new(G.C_DataLayer_VertSrcBody)
        for oVert in bmBody.verts:
            oVert[oLayVertSrcBody] = oVert.index            # Store the vert ID into its own data layer.  This way we can always get back the (authoritative) vert ID and always know exactly which vert we're refering to in any vert domain (e.g. mesh parts cut off from source body)
        self.oMeshBody.Close()



    def DoDestroy(self):
        print("X--- CBody.DoDestroy() called on body '{}' ---X".format(self.oBodyBase.sMeshPrefix))
        self.oMeshBody.DoDestroy()
        self.oMeshFlexCollider.DoDestroy() 
        # self.oMeshSrcBreast.DoDestroy()
        for sSoftBody in self.aSoftBodies:  # Destroy the members of our collections
            self.aSoftBodies[sSoftBody].DoDestroy()
#         for sCloth in self.aCloths:
#             self.aCloths[sCloth].DoDestroy()
        return None         # Conveniently return None so CBodyBase can set its oBody member to none.
    
    

    def CreateSoftBody(self, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio):
        "Create a softbody by detaching sSoftBodyPart verts from game's skinned main body"
        self.aSoftBodies[sSoftBodyPart] = CSoftBody.CSoftBody(self, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio)  # This will enable Unity to find this instance by our self.sSoftBodyPart key and the body.
        return "OK"

#     def CreateSoftBodySkin(self, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio, nHoleRadius):
#         "Create a softbody skin by detaching sSoftBodyPart verts from game's skinned main body"
#         self.aSoftBodies[sSoftBodyPart] = CSoftBody.CSoftBodySkin(self, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio, nHoleRadius)  # This will enable Unity to find this instance by our self.sSoftBodyPart key and the body.
#         return "OK"




#     def Morph_UpdateDependentMeshes(self):
#         "Update all the softbodies connected to this body.  Needed after an operation on self.oMeshMorph"
#         for oSoftBody in self.aSoftBodies.values():
#             oSoftBody.Morph_UpdateDependentMeshes()
   
   
    def CreateFlexCollider(self, nDistFlexColliderShrinkMult):
        "Called by Unity when all soft body parts have been removed from self.oMeshBody.  Creates the gametime Flex collider."
        
        print("=== CBody.CreateFlexCollider()  on '{}' ===".format(self.oBodyBase.sMeshPrefix))
        #=== Start the Flex collider from the current self.oMeshBody.  (It just had all softbody bits removed) ===
        self.oMeshFlexCollider = CMesh.CMesh.CreateFromDuplicate(self.oBodyBase.sMeshPrefix + 'FlexCollider' , self.oMeshBody)
        oMeshFlexCollider = self.oMeshFlexCollider.GetMesh()
        
        #=== Simplify the mesh so remesh + shrink below work better (e.g. remove teeth, eyes, inside of ears & nostrils, etc) ===
        ###TODO15: Cleanup mesh!

        #=== Gut the mesh's armature, vertex groups, etc as it has to be reskined after the remesh ===
        #oMeshFlexCollider.modifiers.remove(oMeshFlexCollider.modifiers['Armature'])     ###LEARN: How to remove a modifier by name
        bpy.ops.object.vertex_group_remove(all=True)

        #=== Remesh the Flex collider mesh so that it has particles spaced evenly to efficiently repell other Flex objects ===
        oModRemesh = oMeshFlexCollider.modifiers.new(name="REMESH", type="REMESH")
        oModRemesh.mode = 'SMOOTH'
        oModRemesh.octree_depth = 7         ###IMPROVE15: Need to convert remesh arguments based on body height to inter-particular distance
        oModRemesh.scale = 0.90 
        oModRemesh.use_remove_disconnected = True
        AssertFinished(bpy.ops.object.modifier_apply(modifier=oModRemesh.name))     # This call destroys skinning info / vertex groups

        #=== Transfer the skinning information from the body back to the just remeshed flex collider mesh ===
        Util_TransferWeights(oMeshFlexCollider, self.oMeshBody.GetMesh())
        
        #=== Now that we have re-skinned we can 'shrink' the collision mesh to compensate for the Flex inter-particle distance ===
        self.oMeshFlexCollider.Open()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.shrink_fatten(value=G.CGlobals.cm_nFlexParticleSpacing * nDistFlexColliderShrinkMult)
        self.oMeshFlexCollider.Close()
        
        return "OK"         # Called from Unity so we must return something it can understand

    #---------------------------------------------------------------------------    BREASTS

#     def Breasts_ApplyMorph(self, sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue, vecOpAxis):
#         "Apply a breast morph operation onto this body"
#         ###DESIGN: Design decisions needed on what to do in Client and what in Blender as considerable shift is possible...
#         
#         sOpName = sOpMode + "_" + sOpArea + "_" + sOpPivot + "_" + sOpRange  ####PROBLEM!!!!  Not specialized enough for all cases (add extra params)
#         self.oMeshSrcBreast.Open()
#         bpy.ops.object.mode_set(mode='OBJECT')
#     
#         #=== If a previous shape key for our operation exists we must delete it in order to guarantee that we can undo our previous ops and keep our op from influencing the other ops and keep everything 'undoable' ===
#         if self.oMeshSrcBreast.GetMesh().data.shape_keys is None:  # Add the 'basis' shape key if shape_keys is None
#             bpy.ops.object.shape_key_add(from_mix=False)
#         if sOpName in self.oMeshSrcBreast.GetMesh().data.shape_keys.key_blocks:
#             self.oMeshSrcBreast.GetMesh().active_shape_key_index = self.oMeshSrcBreast.GetMesh().data.shape_keys.key_blocks.find(sOpName)  ###LEARN: How to find a key's index in a collection!
#             bpy.ops.object.shape_key_remove()
#         for oShapeKey in self.oMeshSrcBreast.GetMesh().data.shape_keys.key_blocks:  # Disable the other shape keys so our operation doesn't bake in their modifications 
#             oShapeKey.value = 0
#     
#         #=== Create a unique shape key to this operation to keep this transformation orthogonal from the other so we can change it later or remove it regardless of transformations that occur after ===
#         bpy.ops.object.mode_set(mode='EDIT')
#         oShapeKey = self.oMeshSrcBreast.GetMesh().shape_key_add(name=sOpName)  ###TODO: Add shape key upon first usage so we remain orthogonal and unable to touch-up our own modifications.
#         self.oMeshSrcBreast.GetMesh().active_shape_key_index = self.oMeshSrcBreast.GetMesh().data.shape_keys.key_blocks.find(sOpName)  ###LEARN: How to find a key's index in a collection!
#         self.oMeshSrcBreast.GetMesh().active_shape_key.vertex_group = G.C_VertGrp_Area_BreastMorph  ###TODO: Finalize the name of the breast vertex groups 
#         oShapeKey.value = 1
#         
#         #=== Set the cursor to the pivot point requested ===               ###TODO: Set view as cursor and proper axis coordinates!!
#         sBreastMorphPivotPt = G.C_BreastMorphPivotPt + "-" + sOpPivot
#         if sBreastMorphPivotPt not in bpy.data.objects:
#             return "ERROR: Could not find BreastMorphPivotPt = " + sBreastMorphPivotPt 
#         oBreastMorphPivotPt = bpy.data.objects[sBreastMorphPivotPt] 
#         SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', False)
#         bpy.context.scene.cursor_location = oBreastMorphPivotPt.location
#     
#         if sOpRange == "Wide":  ###TUNE
#             nOpSize = 0.4
#         elif sOpRange == "Medium":
#             nOpSize = 0.2
#         elif sOpRange == "Narrow":
#             nOpSize = 0.1
#         else:
#             return "ERROR: Breasts_ApplyMorph() could not decode sOpRange " + sOpRange
#     
#         #=== Select the verts from predefined vertex groups that is to act as the center of the proportional transformation that is about to be executed ===
#         sVertGrpName = G.C_VertGrp_Morph + sOpArea
#         nVertGrpIndex = self.oMeshSrcBreast.GetMesh().vertex_groups.find(sVertGrpName)
#         if (nVertGrpIndex == -1):
#             return "ERROR: Breasts_ApplyMorph() could not find point op area (vertex group) '" + sVertGrpName + "'"
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Make sure we're in vert mode
#         self.oMeshSrcBreast.GetMesh().vertex_groups.active_index = nVertGrpIndex
#         bpy.ops.object.vertex_group_select()
#     
#         ###NOTE: Important coordinate conversion done in Client on a case-by-case for move/rotate/scale...  (Coordinates we receive here a purely Blender global with our z-up)  
#         aContextOverride = AssembleOverrideContextForView3dOps()  ###IMPORTANT: For view3d settings to be active when this script code is called from the context of Client we *must* override the context to the one interactive Blender user uses.
#         if sOpMode == 'ROTATION':
#             aResult = bpy.ops.transform.rotate(aContextOverride, value=vecOpValue, axis=vecOpAxis, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')  ###SOON?: Why only x works and bad axis??
#         else:        
#             aResult = bpy.ops.transform.transform(aContextOverride, mode=sOpMode, value=vecOpValue, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')    
#         self.oMeshSrcBreast.Close()
#     
#         sResult = aResult.pop()
#         if (sResult != 'FINISHED'):
#             sResult = "ERROR: Breasts_ApplyMorph() transform operation did not succeed: " + sResult
#             print(sResult)
#             return sResult
#     
#         for oShapeKey in self.oMeshSrcBreast.GetMesh().data.shape_keys.key_blocks:  # Re-enable all modifications now that we've commited our transformation has been isolated to just our shape key 
#             oShapeKey.value = 1
#     
#         sResult = "OK: Breasts_ApplyMorph() applying op '{}' on area '{}' with pivot '{}' and range '{}' with {}".format(sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue)
#         self.Breast_ApplyMorphOntoMorphBody()  ####OPT: Don't need to apply everytime!  Only when batch is done!  # Apply the breasts onto the current body morph character... ####IMPROVE? Pass in name in arg?
#         print(sResult)
#         return sResult
# 
# 
#     def Breast_ApplyMorphOntoMorphBody(self):
#         "Apply a breast morph operation onto this body's morphing body (and update the dependant softbodies)"
# 
#         aVertsBodyMorph = self.oMeshMorph.GetMesh().data.vertices
#     
#         #=== 'Bake' all the shape keys in their current position into one and extract its verts ===
#         SelectAndActivate(self.oMeshSrcBreast.GetName())
#         aKeys = self.oMeshSrcBreast.GetMesh().data.shape_keys.key_blocks
#         bpy.ops.object.shape_key_add(from_mix=True)  ###LEARN: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)
#         nKeys = len(aKeys)
#         aVertsBakedKeys = aKeys[nKeys - 1].data  # We obtain the vert positions from the 'baked shape key'
#     
#         #=== Obtain custom data layer containing the vertIDs of our breast verts into body ===
#         bmBreast = self.oMeshSrcBreast.Open()
#         oLayBodyVerts = bmBreast.verts.layers.int[G.C_DataLayer_SourceBreastVerts]  # Each integer in this data layer stores the vertex ID of the left breast in low 16-bits and vert ID of right breast in high 16-bit  ###LEARN: Creating this kills our bmesh references!
#         bmBreast.verts.index_update()
#     
#         #=== Iterate through the breast verts, extract the source verts from body from custom data layer, and set the corresponding verts in body ===
#         for oVertBreast in bmBreast.verts:
#             nVertsEncoded = oVertBreast[oLayBodyVerts]  ####DEV ####HACK!!!
#             nVertBodyBreastL = self.aMapVertsSrcToMorph[(nVertsEncoded & 65535)]  # Breast has been defined from original body.  Map our verts to the requested morphing body  
#             nVertBodyBreastR = self.aMapVertsSrcToMorph[nVertsEncoded >> 16]
#             vecVert = aVertsBakedKeys[oVertBreast.index].co.copy()
#             aVertsBodyMorph[nVertBodyBreastL].co = vecVert
#             vecVert.x = -vecVert.x
#             aVertsBodyMorph[nVertBodyBreastR].co = vecVert
#         self.oMeshSrcBreast.ExitFromEditMode()
#         
#         #=== Delete the 'baked' shape key we created above ===
#         self.oMeshSrcBreast.GetMesh().active_shape_key_index = nKeys - 1
#         bpy.ops.object.shape_key_remove()
#         self.oMeshSrcBreast.Close()
# 
#         #=== Make sure the change we just did to the morphing body propagates to all dependent meshes ===
#         self.Morph_UpdateDependentMeshes()
# 
# 
#     
# 
#     #---------------------------------------------------------------------------    SLAVE MESH
#     def SlaveMesh_ResyncWithMasterMesh(self, sTypeOfSlaveMesh):  ###DEVO?
#         "Set the positions of the slave mesh verts to the positions of their coresponding verts in the master mesh (always self.oMeshMorph)"
#         # Uses information previously stored in sNameSlaveMeshSlave by SlaveMesh_DefineMasterSlaveRelationship() at design time  sTypeOfSlaveMesh is like 'BreastCol', 'BodyCol', 'ClothColTop', etc
#     
#         sNameSlaveMeshSlave = self.oBodyBase.sMeshSource + "-" + sTypeOfSlaveMesh + "-Slave"  ###IMPROVE: Create a function that assembles this name!
#     
#         oMeshSlaveO = SelectAndActivate(sNameSlaveMeshSlave)
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#     
#         #=== Retreive the previously-calculated information from our custom data layers ===
#         bm = bmesh.from_edit_mesh(oMeshSlaveO.data)  ###NOW### Need a matching update_edit_mesh()!!!! 
#         oLaySlaveMeshVerts = bm.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
#         
#         #=== Iterate through the slave mesh, find the corresponding vert in the morph body (going through map from source mesh to morph mesh) and set slave vert
#         aVertsMorph = self.oMeshMorph.GetMesh().data.vertices
#         for oVert in bm.verts:
#             nVertSource = oVert[oLaySlaveMeshVerts]  # Master/Slave relationship setup with master as source body...
#             nVertMorph = self.aMapVertsSrcToMorph[nVertSource]  # ... but we need to set our verts to morphing body!  Use the map we have for this purpose
#             oVert.co = aVertsMorph[nVertMorph].co.copy()
#     
#         bpy.ops.object.mode_set(mode='OBJECT')
#         bpy.ops.object.select_all(action='DESELECT')
#         Util_HideMesh(oMeshSlaveO)
#     
#         return ""

    ###DEV
#     def SlaveMesh_GetVertMapSlaveToMaster(self, sNameMeshSlave):    # Return the map of vert-to-vert to Unity so it can restore slave-mesh verts to position of master-mesh verts.  SlaveMesh_DefineMasterSlaveRelationship() must have been called before this function
#         #=== Open the mesh and obtain BMesh and previously-constructed map in custom properties ===
#         oMeshSlaveO = SelectAndActivate(sNameMeshSlave)
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
#         oBA = CByteArray()
#         Stream_SerializeArray(oBA, aMapSlaveMeshSlaveToMaster.tobytes())
#         return oBA.CloseArray()

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
# ? Update GetVertMap()
# ? Currently applied to orig vert... integrate with mechanism to drill-down?
###DEVO???
# def SlaveMesh_DefineMasterSlaveRelationship(sNameBodySrc, sTypeOfSlaveMesh, nVertTolerance, bMirror=True, bSkin=False):  ####DEV: An init call
#     "Create a master / slave relationship so the slave mesh can follow the vert position of master mesh at runtime.  Only invoked at design time.  Stores its information in mesh custom layer"
#     # sNameBodySrc is like 'WomanA', 'ManA'.  sTypeOfSlaveMesh is like 'BreastCol', 'BodyCol', 'ClothColTop', etc
#     # bMirror is set for most colliders but NOT for breast (as each collider is handled separately)
#     # (Used by breast colliders, cloth colliders, etc so they can update themselves when the source body has been morphed at runtime by the user)
# 
#     print("\n=== SlaveMesh_DefineMasterSlaveRelationship() sNameBodySrc: '{}'  sTypeOfSlaveMesh: '{}' ===".format(sNameBodySrc, sTypeOfSlaveMesh))
#     
#     sNameSlaveMeshSource = sNameBodySrc + "-" + sTypeOfSlaveMesh + "-Source"  # This is the design-time mesh.  It only has half the body and is mirrored to create the Slave mesh.
#     sNameSlaveMeshSlave = sNameBodySrc + "-" + sTypeOfSlaveMesh + "-Slave"  # This is the mesh that will be compled to the master mesh so we can mo
#     
#     #=== Copy the source mesh to a new mesh that will represent both left & right side of the body ===
#     DataLayer_RemoveLayers(sNameSlaveMeshSource)  # Design-time mesh should not have any layers.
#     oMeshO = DuplicateAsSingleton(sNameSlaveMeshSource, sNameSlaveMeshSlave, None, True)  # Create the mirrored mesh.  This is the one that will store the SlaveMesh info and be used for processing
# 
#     #=== 'Mirror' the source mesh so it represents both the left and right side of the body.  (Source only has left) ===
#     if (bMirror):
#         oModMirrorX = Util_CreateMirrorModifierX(oMeshO)
#         AssertFinished(bpy.ops.object.modifier_apply(modifier=oModMirrorX.name))
#     
#     #=== Create mirrored mesh copy and fetch bmesh for editing ===
#     oMeshCopyO = DuplicateAsSingleton(sNameSlaveMeshSlave, sNameSlaveMeshSlave + "_TEMPCOPY_SlaveMesh", G.C_NodeFolder_Temp, False)  # Create a temporary copy of mesh to be slaved so we can edit as we go
#     oMeshMasterO = SelectAndActivate(sNameBodySrc)
#     oMeshSlaveO = SelectAndActivate(sNameSlaveMeshSlave)
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
# 
#     #=== Create a new data layer to store the mapping between each vert to the closest vert found in sNameBodySrc ===
#     bm = bmesh.from_edit_mesh(oMeshSlaveO.data)
#     oLaySlaveMeshVerts = bm.verts.layers.int.new(G.C_DataLayer_SlaveMeshVerts)
#     bm.verts.index_update()
#     bm.verts.ensure_lookup_table()  ###TODO Needed in later versions of Blender!
#     
#     #=== Find the matching vert between master mesh and its to-be-slaved mesh ===
#     # print("=== Finding vert-to-vert mapping between master and slave meshes ===")
#     for oVert in oMeshCopyO.data.vertices:  # We iterate through copy mesh because Util_FindClosestVert() below must operate in object mode and we need to store info in the source mesh
#         nVert = oVert.index
#         vecVert = oVert.co.copy()
#         nVertClosest, nDistMin, vecVertClosest = Util_FindClosestVert(oMeshMasterO, vecVert, nVertTolerance)
#         if nVertClosest != -1:
#             # print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %8.6f" % (nVert, nVertClosest, vecVert.x, vecVert.y, vecVert.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
#             oVertBM = bm.verts[nVert]  # Obtain reference to our vert's through bmesh
#             oVertBM.co = vecVertClosest  # Set the source mesh vert exactly at the position of the closest vert on target mesh
#             oVertBM[oLaySlaveMeshVerts] = nVertClosest  # S tore the index of the closest vert in target mesh
#         else:
#             print("###WARNING: Vert %3d @  (%6.3f,%6.3f,%6.3f) was not found!" % (nVert, vecVert.x, vecVert.y, vecVert.z))
#     
#     #=== Close the mesh and delete copy ====
#     bpy.ops.object.mode_set(mode='OBJECT')
#     DeleteObject(oMeshCopyO.name)  # Delete the temporary mesh  ###PROBLEM!!! When Unity calls this DeleteObject destroys two meshes!!!
# 
#     #=== Skin the slave mesh to the original mesh if required ===    
#     if (bSkin):  ###IMPROVE: Remove existing skin info?
#         oMeshSlaveO = SelectAndActivate(sNameSlaveMeshSlave)
#         oMeshSourceO = bpy.data.objects[sNameBodySrc]
#         Util_HideMesh(oMeshSourceO)
#         Util_TransferWeights(oMeshSlaveO, oMeshSourceO)  # bpy.ops.object.vertex_group_transfer_weight()
#     
#     bpy.ops.object.select_all(action='DESELECT')
#     Util_HideMesh(oMeshO)



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CBODY PUBLIC ACCESSOR
#---------------------------------------------------------------------------    

def CBodyBase_Create(nBodyID, sMeshSource, sSex, sGenitals):
    "Proxy for CBody ctor as we can only return primitives back to Unity"
    oBodyBase = CBodyBase(nBodyID, sMeshSource, sSex, sGenitals)
    return str(oBodyBase.nBodyID)           # Strings is one of the only things we can return to Unity

def CBodyBase_GetBodyBase(nBodyID):
    "Easy accessor to simplify Unity's access to bodies by ID. Used throughout Unity codebase to easily obtain instances from the global scope."
    return CBodyBase._aBodyBases[nBodyID]




###OBS: Stuff in ctor of CBody
        ###OBS?
#         sNameVertGroupToCutout = None
#         if self.sGenitals.startswith("Vagina"):         # Woman has vagina and breasts
#             print("###### VAGINA CUTOUT BROKEN!!!")     ###NOW### Repair to old vagina being out-of-main body?
#             ###BROKEN!!!!!!! sNameVertGroupToCutout = "_Cutout_Vagina"
#         elif self.sGenitals.startswith("Penis"):        # Man & Shemale have penis
#             sNameVertGroupToCutout = "_Cutout_Penis"
#         if sNameVertGroupToCutout is not None:
#             bpy.ops.object.mode_set(mode='EDIT')
#             VertGrp_SelectVerts(self.oMeshAssembled.GetMesh(), sNameVertGroupToCutout)     # This vert group holds the verts that are to be soft-body simulated...
#             bpy.ops.mesh.delete(type='FACE')                    # ... and delete the mesh part we didn't want copied to output body
#             bpy.ops.object.mode_set(mode='OBJECT')
#     
#         #=== Import and preprocess the genitals mesh and assemble into this mesh ===
#         if (self.sGenitals.startswith("Vagina") == False):      ###V ###CHECK!!!
#             oMeshGenitalsSource = CMesh.CMesh.CreateFromExistingObject(self.sGenitals)          ###WEAK: Create another ctor?
#             oMeshGenitals = CMesh.CMesh.CreateFromDuplicate("TEMP_Genitals", oMeshGenitalsSource)
#             bpy.context.scene.objects.active = oMeshGenitals.GetMesh()
#             bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings
#          
#             #=== Transfer weight from body to add-on genitals ===
#             Util_TransferWeights(oMeshGenitals.GetMesh(), self.oMeshSource.GetMesh())      #bpy.ops.object.vertex_group_transfer_weight()
#          
#             #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
#             self.oMeshAssembled.GetMesh().select = True
#             bpy.context.scene.objects.active = self.oMeshAssembled.GetMesh()
#             bpy.ops.object.join()                   ###IMPROVE: Make into a function?
#             bpy.ops.object.mode_set(mode='EDIT')
#             bpy.ops.mesh.select_all(action='SELECT')      # Deselect all verts in assembled mesh
#             bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###LEARN: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 
#             bpy.ops.mesh.select_all(action='DESELECT')      # Deselect all verts in assembled mesh
#             bpy.ops.object.mode_set(mode='OBJECT')

        ####LEARN: Screws up ConvertMeshForUnity royally!  self.oMeshAssembled.data.uv_textures.active_index = 1       # Join call above selects the uv texture of the genitals leaving most of the body untextured.  Revert to full body texture!   ###IMPROVE: Can merge genitals texture into body's??
        ###VertGrp_SelectVerts(self.oMeshAssembled.GetMesh(), sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
        # bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###LEARN: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 

        #=== Create the custom data layer storing assembly vert index.  Enables traversal from Assembly / Morph meshes to Softbody parts 
        ###BROKEN11: DataLayer_CreateVertIndex(self.oMeshAssembled.GetName(), G.C_DataLayer_VertsAssy)
        

        #=== Create map of source verts to morph verts ===  (Enables some morphs such as Breast morphs to be applied to morphing mesh)
        ###OBS??
#         bmMorph = self.oMeshMorph.Open()
#         oLayVertsSrc = bmMorph.verts.layers.int[G.C_DataLayer_VertsSrc]
#         for oVert in bmMorph.verts:
#             if (oVert[oLayVertsSrc] >= G.C_OffsetVertIDs):
#                 nVertOrig = oVert[oLayVertsSrc] - G.C_OffsetVertIDs        # Remove the offset pushed in during creation
#                 self.aMapVertsSrcToMorph[nVertOrig] = oVert.index       
#         self.oMeshMorph.Close()

        #=== Create our own local copy of the breast mesh for breast morphs ===
        ###OBS
#         if (sSex != "Man"):
#             oMeshSrcBreast = CMesh.CMesh.CreateFromExistingObject(self.oBodyBase.sMeshSource + "-Breast")          ###WEAK: Create another ctor?
#             self.oMeshSrcBreast = CMesh.CMesh.CreateFromDuplicate(self.oBodyBase.sMeshPrefix + "Breast", oMeshSrcBreast)        
#             self.oMeshSrcBreast.SetParent(G.C_NodeFolder_Game)
#             self.oMeshSrcBreast.Hide()    
# 
#         nSize = 1.75
#         self.Breasts_ApplyMorph('RESIZE', 'Nipple', 'Center', 'Wide', (nSize,nSize,nSize,0), None)     ###NOW###  ###HACK!



#     def OnChangeBodyMode(self, sBodyBaseMode):  # Blender-side equivalent of Unity's CBodyBase.OnChangeBodyMode().  Switches between configure / play mode for this body.
#         if (sBodyBaseMode == self.sBodyBaseMode):
#             return
#         print("--- CBodyBase '{}' going from mode '{}' to mode '{}' ---".format(self.sMeshPrefix, self.sBodyBaseMode, sBodyBaseMode))
#         self.sBodyBaseMode = sBodyBaseMode
#         
#         if (self.sBodyBaseMode == "MorphBody"):         # If we enter MorphBody mode and body is created destory it
#             if (self.oBody != None):
#                 self.oBody = self.oBody.DoDestroy()     # Destroy the entire gametime body... lots of meshes!
#         elif (self.sBodyBaseMode == "CutCloth"):
#             if (self.oBody != None):
#                 self.oBody = self.oBody.DoDestroy()     # Destroy the entire gametime body... lots of meshes!
#         elif (self.sBodyBaseMode == "Play"):
#             if (self.oBody == None):
#                 self.oBody = CBody(self)                # Create a game-time body.  Expensive operation!
#         else:
#             raise Exception("###EXCEPTION in CBodyBase.OnChangeBodyMode().  Unrecognized body mode " + sBodyBaseMode)
#         return "OK"  # Unity called so we must return something it recognizes like a string ###IMPROVE: Remove this dumb requirement and transfer null too!


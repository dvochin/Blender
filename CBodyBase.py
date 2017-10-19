#===============================================================================

###DOCS24: Aug 2017 - CBodyBase
# === DEV ===
 
# === NEXT ===
 
# === TODO ===
 
# === LATER ===
 
# === OPTIMIZATIONS ===
 
# === REMINDERS ===
 
# === IMPROVE ===
 
# === NEEDS ===
 
# === DESIGN ===
 
# === QUESTIONS ===
 
# === IDEAS ===
 
# === LEARNED ===
 
# === PROBLEMS ===
 
# === WISHLIST ===


import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

import G
from gBlender import *
from CMesh import *
import CObject
from CBody import *



class CBodyBase:
    _aBodyBases = []  # The global array of bodies.  Unity acceses body instances through this one global collection

    def __init__(self, nBodyID, sSex):
        self.nBodyID = nBodyID                  # Our ID is passed in by Blender and remains the only public way to access this instance (e.g. CBody._aBodyBases[<OurID>])
        self.sSex = sSex                        # The body's sex (one of 'Man', 'Woman' or 'Shemale')
        self.sMeshPrefix = "B" + chr(65 + self.nBodyID) + '-'  # The Blender object name prefix of every submesh (e.g. 'BodyA-Detach-Breasts', etc)
        
        self.oBody = None                       # Our game-time body.  Created when we enter play mode, destroyed when we leave play mode for configure mode.
        self.sBodyBaseMode = "Uninitialized"    # The Body Base mode.  Blender equivalent of Unity's CBodyBase._eBodyBaseMode enumeration

        self.oMeshSource = None                 # The 'source body'.  Never modified in any way
        self.oMeshMorph = None              # The 'assembled mesh'.  Fully assembled with proper genitals.  Basis of oMeshMorph                  
        self.oMeshMorph = None                  # The 'morphing mesh'.   Orinally copied from oMeshMorph and morphed to the user's preference.  Basis of oMeshBody
        self.oMeshMorphResult = None            # The 'baked' morphing mesh.   Baled version of the body mesh as adjusted by the user's morphing selection.  This is the (only) mesh serialized to Unity and updated every morphing change for WYSIWYG real-time updates.
        
        self.oNodeRoot = None                   # The armature and root Blender node where we store all our meshes under.  Used to group & de-clutter Blender outline tree)

        self.oObjectMeshShapeKeys = None        # The Unity-editable shape keys that enable Unity player to morph our body.    
        self.aVertsFlexCollider = CByteArray()  # Collection of verts sent to Unity that determine which verts form a morphing-time Flex collider capable of repelling morph-time bodysuit master cloth.
        self.aCloths = {}                       # Dictionary of CCloth objects fitted to this body
        

        print("\n=== CBodyBase()  nBodyID:{}  sMeshPrefix:'{}'  sSex:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sSex))

        
        CBodyBase._aBodyBases.append(self)  # Append ourselves to global array.  The only way Unity can find our instance is through CBody._aBodyBases[<OurID>]
        SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)     # Make sure we're starting Blender operations with Blender in a known state...
        self.oMeshSource = CMesh.Attach(self.sSex + "-Source")      ###WEAK: Use constant??
        
        #=== Create a data layer that will store source body verts for possible vert domain traversal (e.g. soft body skin) ===
        self.oMeshSource.DataLayer_Create_SimpleVertID(G.C_DataLayer_VertSrcBody)
        
        #=== Lock the DAZ-based bone vertex groups so they are not touched unless we deliberately unlock them ===
        self.oMeshSource.VertGrp_LockUnlock(True, G.C_RexPattern_StandardBones)

        #=== Duplicate the armature node of the source body so this body gets its own bone instance ===
        self.oNodeRoot = CMesh.AttachFromDuplicate_ByName("Body" + chr(65 + self.nBodyID), "[" + self.sSex + "]")
        self.oNodeRoot.SetParent(G.C_NodeFolder_Game)

        #=== Duplicate the source body (kept in pristine condition) as the morphing body ===
        self.oMeshMorph = CMesh.AttachFromDuplicate(self.sMeshPrefix + "Morph", self.oMeshSource)
        self.oMeshMorph.SetParent(self.oNodeRoot.GetName())
        self.oMeshMorph.GetMesh().modifiers["Armature"].object = self.oNodeRoot.GetMesh()       # Redirect the copied mesh to the just-duplicated armature we created above.  (Changes to bones do not affect the original body)         
        Util_ConvertToTriangles()           ###CHECK: Anything else that runs super early?

        #=== Prepare the Unity-serialized mesh that is updated every time player adjusts a slider ===
        self.oMeshMorphResult = CMesh.AttachFromDuplicate(self.sMeshPrefix + 'MorphResult', self.oMeshMorph)
        self.oMeshMorphResult.oMeshSource = self.oMeshSource     # Push in what the source to this mesh is so Unity can extract valid normals
        self.oMeshMorphResult.ShapeKeys_RemoveAll()       # Remove all the shape keys of the outgoing mesh.  We set its verts manually at every morph change.
        self.oMeshMorphResult.Hide()

        #=== Connect our Unity-editable collection of properties so Unity player can edit our body mesh ===
        self.oObjectMeshShapeKeys = CObject.CObjectMeshShapeKeys("Body Mesh Shape Keys", self.oMeshMorph.GetName())  # The Unity-visible CObject properties.  Enables Unity to manipulate morphing body's morphs
        # self.oObjectMeshShapeKeys.PropSet("Breasts-Implants", 1.0)

        #=== Form the collection of Flex collider verts Unity will use to form a Flex collider capable of repelling morph-time bodysuit ===
        if self.oMeshMorphResult.Open():
            self.oMeshMorphResult.VertGrp_SelectVerts("_StaticBodyCollider")
            for oVert in self.oMeshMorphResult.bm.verts:
                if oVert.select:
                    self.aVertsFlexCollider.AddUShort(oVert.index)
            self.oMeshMorphResult.Close()


    def Unity_UpdateMorphResultMesh(self):  # 'Bake' the morphing mesh as per the player's morphing parameters into a 'MorphResult' mesh that can be serialized to Unity.  Matches Unity's CBodyBase.Unity_UpdateMorphResultMesh()
        #=== 'Bake' all the shape keys in their current position into one and extract its verts ===
        SelectObject(self.oMeshMorph.GetName())
        aKeys = self.oMeshMorph.GetMeshData().shape_keys.key_blocks
        bpy.ops.object.shape_key_add(from_mix=True)  ###INFO: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)
        nKeys = len(aKeys)
        aVertsBakedKeys = aKeys[nKeys - 1].data  # We obtain the vert positions from the 'baked shape key'
    
        #=== Iterate through the verts, extract the 'baked' position of the just-created 'mix' shape key to set the position of the outgoing MorphResult mesh
        if self.oMeshMorph.Open():
            aVertsMorphResults = self.oMeshMorphResult.GetMeshData().vertices
            for oVert in self.oMeshMorph.bm.verts:
                vecVert = aVertsBakedKeys[oVert.index].co.copy()    # Get the final morphing position...
                aVertsMorphResults[oVert.index].co = vecVert        # And apply it to outgoing mesh so Unity can get its refreshed vert positions
            self.oMeshMorph.Close()
            
        #=== Delete the 'baked' shape key we created above ===
        self.oMeshMorph.GetMesh().active_shape_key_index = nKeys - 1
        bpy.ops.object.shape_key_remove()
        
        return "OK"  # Called from Unity so we must return something

    def Unity_GetBones(self):  
        ###BROKEN: Breaks CBodyEd!  Called by the CBodyEd (Unity's run-in-edit-mode code for CBody) to update the position of the bones for the selected Unity template.  Non destructive call that assumes existing bones are already there with much extra information such as ragdoll colliders, components on bones, etc.)
        ###IDEA: Move this to a new class that encapsulates the concept of an armature?  (e.g. CArmature with all kinds of functions to service it) 
        # This call only updates bones position and creates bones if they are missing.  Rotation isn't touched and extraneous bones have to be deleted in Unity if needed.
        print("\n=== gBL_GetBones('{}') ===".format(self.sMeshPrefix))
        oMeshO = self.oMeshMorph.GetMesh()
        if "Armature" not in oMeshO.modifiers:
            return G.DumpStr("ERROR: gBL_GetBones() cannot find armature modifier for '" + self.sMeshPrefix + "'")
        oArmObject = oMeshO.modifiers["Armature"].object        ###INFO: How to get Blender node that holds bones
        oArm = oArmObject.data
        
        #=== Send bone tree (without bone positions) Unity needs our order to map to its existing bone which remain the authority ===
        oBA = CByteArray()
        SelectObject(oArmObject.name)          # Select armature node
        bpy.ops.object.mode_set(mode='EDIT')
        oBA.AddBone(oArm.edit_bones[0])             # Recursively send the bone tree starting at root bone (0) 
        bpy.ops.object.mode_set(mode='OBJECT')
    
        return oBA.CloseArray() 


    #---------------------------------------------------------------------------    MORPH EXTRACTION
    def CMorphChannel_GetMorphVerts(self, sNameShapeKey):  # Called by CBMeshMorph to get the morphed verts on a given shape key and a given mesh.  Used to morph non-skinned meshes at runtime such as face eyelids and mouth open/close
        #=== Find requested shape key to obtain morph data ===
        oMeshMorphO = self.oMeshMorph.GetMesh()
        oMeshShapeKeyBlocks = oMeshMorphO.data.shape_keys.key_blocks
        if sNameShapeKey in oMeshShapeKeyBlocks:
            nMorphKeyBlockIndex = oMeshShapeKeyBlocks.find(sNameShapeKey)  ###INFO: How to find a key's index in a collection! (Set by oMeshMorphO.active_shape_key_index)
        else:
            return G.DumpStr("ERROR: CMorphChannel_GetMorphVerts() cannot find shape key " + sNameShapeKey)
     
        #=== Obtain access to shape key vert data ===        
        aVertsBasis = oMeshShapeKeyBlocks[0].data                       # 'Basis' is always index zero
        aVertsMorph = oMeshShapeKeyBlocks[nMorphKeyBlockIndex].data     # We obtain the vert positions from the 'baked shape key'  ###INFO: How to get raw shape key data
        bmMorph = bmesh.new()                                ###INFO: How to operate with bmesh without entering edit mode!        ###TODO11: Change codebase to this technique?
        bmMorph.from_object(oMeshMorphO, bpy.context.scene)  ###DESIGN: Selection of body!
        
        #=== Obtain access to the 'morph result' mesh.  We need it to expand result set to duplicate morph deltas accross verts split by material seams ===
        oMeshMorphResultO = self.oMeshMorphResult.GetMesh() 
        bmMorphResult = bmesh.new()
        bmMorphResult.from_object(oMeshMorphResultO, bpy.context.scene)
        oLaySplitVertID = bmMorphResult.verts.layers.int[G.C_DataLayer_SplitVertIDs]
        bmMorphResult.verts.ensure_lookup_table()
     
        #=== Iterate through all the mesh verts and test all verts that are different for the given shape key so we can serialize its delta data to client
        print("\n=== CMorphChannel_GetMorphVerts('{}', '{}' ===".format(self.oMeshMorph.GetName(), sNameShapeKey))
        oBA = CByteArray()
        for oVert_Morph in bmMorph.verts:
            oVert_MorphResult = bmMorphResult.verts[oVert_Morph.index]        ###CHECK: Same verts except for split ones??
            vecVertBasis = aVertsBasis[oVert_Morph.index].co
            vecVertMorph = aVertsMorph[oVert_Morph.index].co
            vecVertDelta = vecVertMorph - vecVertBasis
            nLengthDelta = vecVertDelta.length
            if (nLengthDelta >= 0.0001):           # Don't bother with verts that change such a tiny amount to optimize performance          #if vecVertBasis != vecVertMorph:            ###INFO: For some reason this doesn't work!  It lets through tiny values through like 0.00000001!
                #print("{:4}  #{:5} = Dist {:6.4} = ({:10.7},{:10.7},{:10.7})".format(nMorphedVerts, oVert_Morph.index, nLengthDeltaSqr, vecVertDelta.x, vecVertDelta.y, vecVertDelta.z))
                oBA.AddFloat(oVert_Morph.index)       ###NOTE: Packing ID as a float so that we can conveniently view all data as float (as vector is three floats)
                oBA.AddVector(vecVertDelta)     ###NOTE: AddVector() will convert from Blender coordinate system to Unity.  (Unity can read straight up)
                nSplitVertID = oVert_MorphResult[oLaySplitVertID]
                if nSplitVertID >= G.C_OffsetVertIDs:
                    aSplitVerts = self.oMeshMorphResult.aaSplitVerts[nSplitVertID]
                    for nVertSplit in aSplitVerts:
                        if nVertSplit != oVert_Morph.index:     # Don't add the vert already added above
                            oBA.AddFloat(nVertSplit)
                            oBA.AddVector(vecVertDelta)

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
        self.oClothSrcSelected_HACK = CMesh.Attach(G.CGlobals.cm_aClothSources[sNameClothSrc].oMeshO_3DS.name)       # 'Select' the current cloth src and put it in this variable.  It will the be pulled by Unity to interact with the cloth source
        return "OK"

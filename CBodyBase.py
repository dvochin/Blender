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

    def __init__(self, nBodyID, sSex, sMeshSource, sGenitals):
        self.nBodyID = nBodyID              # Our ID is passed in by Blender and remains the only public way to access this instance (e.g. CBody._aBodyBases[<OurID>])
        self.sSex = sSex                    # The body's sex (one of 'Man', 'Woman' or 'Shemale')
        self.sMeshSource = sMeshSource      # The name of the source body mesh (e.g. 'WomanA', 'ManA', etc)        ###TODO11: Separate sex from mesh version!
        self.sGenitals = sGenitals          # The body's genitals (e.g. Penis-EroticVR-A' etc.)  ###OBS21:??? Changed meaning now that we no longer support different penises?  Keep in case we have different ones?  (Always one vagina now)
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
        

        print("\n=== CBodyBase()  nBodyID:{}  sMeshPrefix:'{}'  sMeshSource:'{}'  sSex:'{}'  sGenitals:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sMeshSource, self.sSex, self.sGenitals))

        
        CBodyBase._aBodyBases.append(self)  # Append ourselves to global array.  The only way Unity can find our instance is through CBody._aBodyBases[<OurID>]
        SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)     # Make sure we're starting Blender operations with Blender in a known state...
        self.oMeshSource = CMesh.Create(self.sMeshSource)
        
        #=== Lock the DAZ-based bone vertex groups so they are not touched unless we deliberately unlock them ===
        self.oMeshSource.VertGrp_LockUnlock(True, G.C_RexPattern_StandardBones)

        #=== Create a empty node in game folder where every mesh related to this body will go ===
        self.oNodeRoot = CreateEmptyBlenderNode("Body" + chr(65 + self.nBodyID), G.C_NodeFolder_Game)

        #=== Duplicate the source body (kept in pristine condition) as the assembled body. Delete unwanted parts and attach the user-specified genital mesh instead ===
        self.oMeshAssembled = CMesh.CreateFromDuplicate(self.sMeshPrefix + "Assembled", self.oMeshSource)  # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
        self.oMeshAssembled.SetParent(self.oNodeRoot.name)
        Util_ConvertToTriangles()           ###DEV24: Anything else that runs super early?
        #self.oMeshAssembled.ConvertMeshForUnity(True)  ###DESIGN13: This early??

        #=== Prepare a ready-for-morphing body for Unity.  Also create the 'body' mesh that will have parts detached from it where softbodies are ===
        self.oMeshMorph = CMesh.CreateFromDuplicate(self.sMeshPrefix + 'Morph', self.oMeshAssembled)   
        self.oMeshMorph.SetParent(self.oNodeRoot.name)

        #=== Prepare the Unity-serialized mesh that is updated every time player adjusts a slider ===
        self.oMeshMorphResult = CMesh.CreateFromDuplicate(self.sMeshPrefix + 'MorphResult', self.oMeshMorph)   
        self.oMeshMorphResult.SetParent(self.oNodeRoot.name)
        self.oMeshMorphResult.ShapeKeys_RemoveAll()       # Remove all the shape keys of the outgoing mesh.  We set its verts manually at every morph change.
        self.oMeshMorphResult.Hide()

        #=== Connect our Unity-editable collection of properties so Unity player can edit our body mesh ===
        self.oObjectMeshShapeKeys = CObject.CObjectMeshShapeKeys("Body Mesh Shape Keys", self.oMeshMorph.GetName())  # The Unity-visible CObject properties.  Enables Unity to manipulate morphing body's morphs
        # self.oObjectMeshShapeKeys.PropSet("Breasts-Implants", 1.0)


    def UpdateMorphResultMesh(self):  # 'Bake' the morphing mesh as per the player's morphing parameters into a 'MorphResult' mesh that can be serialized to Unity.  Matches Unity's CBodyBase.UpdateMorphResultMesh()
        #=== 'Bake' all the shape keys in their current position into one and extract its verts ===
        SelectObject(self.oMeshMorph.GetName())
        aKeys = self.oMeshMorph.GetMeshData().shape_keys.key_blocks
        bpy.ops.object.shape_key_add(from_mix=True)  ###INFO: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)
        nKeys = len(aKeys)
        aVertsBakedKeys = aKeys[nKeys - 1].data  # We obtain the vert positions from the 'baked shape key'
    
        #=== Obtain reference to the morphing mesh and the morphing result mesh ===
        bmMorph = self.oMeshMorph.Open()
        aVertsMorphResults = self.oMeshMorphResult.GetMeshData().vertices
    
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
            nMorphKeyBlockIndex = oMeshShapeKeyBlocks.find(sNameShapeKey)  ###INFO: How to find a key's index in a collection! (Set by oMeshMorphO.active_shape_key_index)
        else:
            return G.DumpStr("ERROR: CMorphChannel_GetMorphVerts() cannot find shape key " + sNameShapeKey)
     
        #=== Obtain access to shape key vert data ===        
        aVertsBasis = oMeshShapeKeyBlocks[0].data                       # 'Basis' is always index zero
        aVertsMorph = oMeshShapeKeyBlocks[nMorphKeyBlockIndex].data     # We obtain the vert positions from the 'baked shape key'  ###INFO: How to get raw shape key data
        bm = bmesh.new()                                ###INFO: How to operate with bmesh without entering edit mode!        ###TODO11: Change codebase to this technique?
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
            if (nLengthDelta >= 0.0001):           # Don't bother with verts that change such a tiny amount to optimize performance          #if vecVertBasis != vecVertMorph:            ###INFO: For some reason this doesn't work!  It lets through tiny values through like 0.00000001!
                #print("{:4}  #{:5} = Dist {:6.4} = ({:10.7},{:10.7},{:10.7})".format(nMorphedVerts, oVert.index, nLengthDeltaSqr, vecVertDelta.x, vecVertDelta.y, vecVertDelta.z))
                oBA.AddFloat(oVert.index)         ###NOTE: Packing ID as a float so that we can conveniently view all data as float (as vector is three floats)
                oBA.AddVector(vecVertDelta)         ###BUG:???  Converted coordinates now!!
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

    def CreateCBody(self, bDisableRigCreation_HACK=False):
        print("\n=== CBodyBase.CreateCBody() called on CBodyBase '{}' ===".format(self.sMeshPrefix))
        if (self.oBody == None):
            self.oBody = CBody(self, bDisableRigCreation_HACK)                # Create a game-time body.  Expensive operation!
        return "OK"

    def DestroyCBody(self):                 # Called by Unity so a body base can free the resources from its CBody instance (game-time body)  (Means the user went back to body editing)
        print("\n=== CBodyBase.DestroyCBody() called on CBodyBase '{}' ===".format(self.sMeshPrefix))
        if (self.oBody != None):
            self.oBody = self.oBody.DoDestroy()     # Destroy the entire gametime body... lots of meshes!
        return "OK"

    def SelectClothSrc_HACK(self, sNameClothSrc):           ###HACK18: To overcome Unity's CBMesh.Create requiring every mesh to be accessible from a CBodyBase instance.
        self.oClothSrcSelected_HACK = CMesh.Create(G.CGlobals.cm_aClothSources[sNameClothSrc].oMeshO_3DS.name)       # 'Select' the current cloth src and put it in this variable.  It will the be pulled by Unity to interact with the cloth source
        return "OK"



        #=== Form the collection of Flex collider verts Unity will use to form a Flex collider capable of repelling morph-time bodysuit ===
#         bAllVertsInCollider = True          ###NOTE: Bit of a hack to avoid having to define this damn group at every mesh rebuild... should be defined for final game tho!
#         if VertGrp_FindByName(self.oMeshMorphResult.GetMesh(), "_CFlexCollider", False):
#             VertGrp_SelectVerts(self.oMeshMorphResult.GetMesh(), "_CFlexCollider")
#             bAllVertsInCollider = False
#         else:
#             print("\n###WARNING: _CFlexCollider vertex group not found = Inneficient collisions!")
#         bmMorphResult = self.oMeshMorphResult.Open()
#         for oVert in bmMorphResult.verts:
#             if (oVert.select or bAllVertsInCollider):
#                 self.aVertsFlexCollider.AddUShort(oVert.index)
#         self.oMeshMorphResult.Close()

#===============================================================================

###DOCS24: Aug 2017 - CBody rewrite
# === DEV ===

# === NEXT ===
#- Could retune fluid collider to have more verts
 
# === TODO ===
#- Blender should feed Unity with list of softbodies that were created.
 
# === LATER ===
 
# === OPTIMIZATIONS ===
 
# === REMINDERS ===
 
# === IMPROVE ===
#- Could insert a line of particles along penis shaft center just before decimation.  Those that stay would help large girth penis simulate more like a solid
 
# === NEEDS ===
 
# === DESIGN ===
 
# === QUESTIONS ===
 
# === IDEAS ===
 
# === LEARNED ===
 
# === PROBLEMS ===
#- Last bone of penis softbody is always very low density!  Why??
    #- Problem with penis last bone being different is because a loop doesn't iterate from 1?

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
from CBodyBase import *

import CFlexSoftBody
import CObject


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CBODY PUBLIC ACCESSOR
#---------------------------------------------------------------------------    

def CBodyBase_Create(nBodyID, sSex):
    "Proxy for CBody ctor as we can only return primitives back to Unity"
    oBodyBase = CBodyBase(nBodyID, sSex)
    return str(oBodyBase.nBodyID)

def CBodyBase_GetBodyBase(nBodyID):
    "Easy accessor to simplify Unity's access to bodies by ID. Used throughout Unity codebase to easily obtain instances from the global scope."
    return CBodyBase._aBodyBases[nBodyID]

def CBodyBase_GetBody(nBodyID):
    "Easy accessor to simplify Unity's access to bodies by ID. Used throughout Unity codebase to easily obtain instances from the global scope."
    return CBodyBase._aBodyBases[nBodyID].oBody




#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CBODY
#---------------------------------------------------------------------------    

class CBody:
    #-------------------------------------------------- Flex particle distance and related multipliers          
    C_FlexParticleSpacing               = 0.02          ###DEV24: Merge with main constant!!!
    C_RatioSpacingMult_MeshShrink       = 0.50          ###DEV24: ###TUNE Ratio of C_FlexParticleSpacing we use to pull meshes so collisions appear realistic.  Shrinking is needed to provide the illusion that collision occur as skin-depth. (In theory this should be 1 but smaller values are observed to look better in game)
    C_RatioSpacingMult_BodyShrink       = 1.0           # Ratio of particle spacing for the final 'remove_doubles()' to get us to particles spaced by the Flex requirement cuts off too much.  Reduce the ratio by this percentage to get closer to the actual limit
    C_RatioSpacingMult_ShapeLinkDist    = 3.0           # Ratio of C_FlexParticleSpacing to determine MAXIMUM distance for links to form.  Note that link algorithm first stops at 'C_MaxShapeLinks' number of links so links that should be included but ignored because the search distance was too small should be very rare indeed 
    C_RatioSpacingMult_SurfaceCram      = 0.90          # How much to 'cram' surface particles for superior surface coverage & collision against other softbodies & cloth.  Flex will space them out     ###TUNE 
    C_RatioSpacingMult_BoneInfluence    = 1.5           # Multiplier of Flex particle distance use to find how large to make the bone envelope that is used to re-weight the softbody presentation mesh
    #-------------------------------------------------- Constants related to shrinking process
    C_MaxShapeLinks                     = 10            # Maximum number of links a shape can have with its neighbors.  ###TUNE ###OPT
    C_RemoveDoublesDistDuringShrink     = 0.005         # Distance for 'remove_doubles()' during the shrinking process.  Reduces geometry as we shrink to maintain a manifold mesh
    C_ExtraEdgeSmoothing                = 0.1           # Global smoothing applied during shrinking.  Helps smooth out the 'smooth shrunken mesh' during shrinking
    C_NumIterationsForFullBodyShrink    = 1             # Number of iterations to shrink the entire body by the desired shrink distance.  Each iteration is expensive but having enough iterations for a quality manifold mesh is imperative!  
    #-------------------------------------------------- Bit masks used in the 'oFlexSoftBody.aParticleInfo' collection sent to Unity 
    C_ParticleInfo_Mask_Type        = 0x000000FF        # This mask enables the multi-purpose ParticleInfo field to read/write the C_ParticleType_XXX particle type as stuffed in the oFlexSoftBody.aParticleInfo array sent to Unity 
    C_ParticleInfo_Mask_Stiffness   = 0x0000F000        # This mask enables the ParticleType field to read/write the particle stiffness (e.g. how resistant to bending that shape is) 
    C_ParticleInfo_Mask_BoneID      = 0x0FFF0000        # This mask enables the ParticleType field to store the bone ID when it is of type 'C_ParticleType_SimulatedSurface'  Bones are 1-based and BoneID 0 means 'no bone' 
    C_ParticleInfo_Mask_Flags       = 0x70000000        # This mask enables the ParticleType field to store custom flags to identify 'special particles' such as Penis uretra, breast nipples, etc 
    #-------------------------------------------------- Types of particles / verts in the rig.  Contained in 'oFlexSoftBody.aParticleInfo' collection sent to Unity 
    C_ParticleType_SkinnedBackplate     = 0x02          # Particle is skinned and not simulated but is a member of a softbody 'backplate' so these particles can be recipients of new links / edges to dynamic particles.  (Prevents dynamic particles connecting to unwanted parts of the body like legs or under breast)
    C_ParticleType_SkinnedBackplateRim  = 0x03          # Particle is skinned and not simulated but is a member of a softbody 'backplate rim'  so these particles can be recipients of new links / edges to dynamic particles.  Kept separate from backplate as algorithm needs to find them through decimation
    C_ParticleType_SimulatedSurface     = 0x04          # Particle is Flex-simulated at at the skin surface.  They all drive a 'dynamic bone' that has been created to move that area of the presentation mesh along with the moving particle.  (e.g. breast surface, penis surface, etc)  The bone is a one-based ID in the lower 12 bits of our ParticleType field (0 = no bone)
    C_ParticleType_SimulatedInner       = 0x05          # Particle is Flex-simulated but not on the skin surface.  It has no bone and exists solely for softbody shapes to provide the softbody look and feel.
    #-------------------------------------------------- Bit tests used in the 'oFlexSoftBody.aParticleInfo' collection sent to Unity 
    C_ParticleInfo_BitTest_IsOnBackpate     = C_ParticleType_SkinnedBackplate       # Bitmask to find backplate particles only.  Catches both C_ParticleType_SkinnedBackplate and C_ParticleType_SkinnedBackplateRim
    C_ParticleInfo_BitTest_IsSimulated      = C_ParticleType_SimulatedSurface       # Bitmask to find simulated particles only.  Catches both C_ParticleType_SimulatedSurface and C_ParticleType_SimulatedInner   
    #-------------------------------------------------- Bit shifts used in the 'oFlexSoftBody.aParticleInfo' collection sent to Unity 
    C_ParticleInfo_BitShift_Stiffness   = 12            # Stiffness is stored in bits 12-15 for 16 possible values
    C_ParticleInfo_BitShift_BoneID      = 16            # BoneIDs are stored from bits 16-27
    C_ParticleInfo_BitShift_Flags       = 28            # Flags are stored from bits 28-30
    #-------------------------------------------------- Flags used in C_ParticleInfo_Mask_Flags collection
    C_ParticleInfo_BitFlag_Uretra       = 1 << C_ParticleInfo_BitShift_Flags        # Flags the uretra particle / vert
    #-------------------------------------------------- Types of softbodies ###MOVE:?
    C_SoftBodyID_None       = 0x00                      # Particle that have a softbody of zero mean they are not a member of a softbody (these should ALL be C_ParticleType_Skinned particles) 
    C_SoftBodyID_Vagina     = 0x01
    C_SoftBodyID_BreastL    = 0x02                      # Note that both breasts occupy bit 1 for convenience
    C_SoftBodyID_BreastR    = 0x03
    C_SoftBodyID_Penis      = 0x04
    #-------------------------------------------------- Dynamic Bone naming constants shared between Blender and Unity        ###DEV24:2???
    C_Prefix_DynBone_Penis      = "+Penis-"             # The dynamic penis bones.   Created and skinned in Blender and responsible to repel (only) vagina bones
    C_Prefix_DynBone_Vagina     = "+Vagina-"            # The dynamic vagina bones.  Created and skinned in Blender and repeled (only) by penis bones
    C_Prefix_DynBone_VaginaHole = "+VaginaHole-"        ###OBS?? The dynamic vagina hole bones.  Created and skinned in Blender and responsible to guide penis in rig body.
    #-------------------------------------------------- DEV
    DEBUG_INSTANCE = None                               # Stores the singleton class instance to facilitate access from Blender Python console 


    def __init__(self, oBodyBase):
        self.oBodyBase = oBodyBase          # Our owning body base.  In charge of creating / destroying us.  Body base is form morphing / configuration, CBody for gameplay
        self.oMeshBody = None               # The 'gametime body' skinned mesh   Originally copied from the morphing body encompassing the user's morphing preferences.  Has softbody parts (like breasts and penis) removed. 
        self.aMapVertsSrcToMorph = {}       # Map of which original vert maps to what morph/assembled mesh verts.  Used to traverse morphs intended for the source body
        self.oArmNode   = None              # Our source body's armature Blender node 
        self.oArm       = None              # The armature itself.  This is what we use to edit bones

        self.mapFlexSoftBodies = {}                     # Dictionary of the CFlexSoftBody instances we own / manage.  Key is nSoftBodyID, Value is CFlexSoftBody instance
        
        self.oMeshFlexTriCol_BodyMain   = None          # The 'Flex Triangle Collider' this class creates representing this body's shape in Flex's main solver and has the softbody parts removed.   This mesh is 'shrunken' for skin-level collisions and this is what repels softbodies and cloth from non-softbody areas.  Separated from the rig in Finalize() from the skinned particles.
        self.oMeshFlexTriCol_BodyFluid  = None          # The 'Flex Triangle Collider' representing this full body's shape in Flex's fluid solver and includes the softbody parts.  This is what repels fluid particles from the ENTIRE body.  A simple remesh of the source body
        self.oMeshBodySimplified = None            # Simplified version of main body free of extraneous geometry (inner mouth, vagina, anus, etc) to act as source to our colliders.  This mesh is TEMPORARY and becomes 'self.oMeshFlexTriCol_BodyFluid' in Finalize()
        self.oMeshPenisColliderPhysX = None

        self.nBoneID = 1                                # Static counter that uniquely identifies each bone created by this class.  These are sent to Unity and enable it to match raw vertices in the Flex rig with the ID used in the presentation vertex groups.  FlexParticleType with a bone ID of 0 have no bone.
        self.bPerformSafetyChecks = bpy.context.scene.SafetyChecks  # If true algorithm performs many 'safety checks' as complex Flex Rig construction proceeds. 

        self.aVertGroups_SoftBodies = []                # List of vertex groups that are 'bone parents' to the softbodies that have been processed.  Needed in finalize for smoothing
        self.aVertGroups_ToDelete = []                  # List of vertex groups Finalize must delete.  (They would interfere with bone re-weighting / blending / normalize / limit)
        self.setBonesNeedingSmoothing = set()           # Set of vertex groups that must be smoothed in Finalize().  Each softbody process request provides a list of the vertex groups it damages so they can be smoothed in Finalize()

        CBody.DEBUG_INSTANCE = self                  # The last instance created.  Used for direct access from Blender python console


        print("\n=== CBody()  nBodyID:{}  sMeshPrefix:'{}' ===".format(self.oBodyBase.nBodyID, self.oBodyBase.sMeshPrefix))

        #=== Create the main skinned body from the base's Morph mesh.  This mesh will have softbody body parts cut out from it ===
        self.oMeshBody = CMesh.AttachFromDuplicate(self.oBodyBase.sMeshPrefix + 'Body' , self.oBodyBase.oMeshMorph)
        self.oMeshBody.oMeshSource = self.oBodyBase.oMeshSource     # Push in what the source to this mesh is so Unity can extract valid normals

        #=== Obtain access to the armature Blender node and the armature itself ===
        self.oArmNode               = self.oMeshBody.GetMesh().modifiers["Armature"].object 
        self.oArm                   = self.oArmNode.data

        #=== 'Bake' the user's morphing choices into a regular mesh this code needs for softbody separation & processing ===
        aKeys = self.oMeshBody.GetMeshData().shape_keys.key_blocks
        bpy.ops.object.shape_key_add(from_mix=True)  ###INFO: How to 'bake' the current shape key mix into one: We first create a new shape from the user's mix of morphs the delete all the shape keys starting at the first one ('Basis')
        nKeys = len(aKeys)
        for nKey in range(nKeys): 
            bpy.context.object.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove(all=False)
        
        #===== SIMPLIFY SOURCE BODY =====
        #=== Obtain access to main body and setup vert groups properly ===
        self.oMeshBody.VertGrp_LockUnlock(False, G.C_RexPattern_DynamicBones)      # Unlock ALL our dynamic bones vertex groups so we can edit what we need  ###
        ###DEV24:!!!!! self.oMeshBody.VertGrp_RemoveAndSelect_RegEx(G.C_RexPattern_DynamicBones)                 # Ensure the source body has none of our dynamic bones assigned.
        ###IMPROVE: Bones_RemoveBonesWithNamePrefix(self.oArm, G.C_Prefix_DynBones)                      # Ensure the source body has none of our dynamic bones assigned. and clean up bones / vertex groups containing our reserved prefix (left from a previous run?)

        #=== Create a version of the main body stripped of extraneous geometry like inner mouth, inner vagina, anus, eyebrows, etc.  This will be the source for our colliders & rig ===
        self.oMeshBodySimplified = CMesh.AttachFromDuplicate(self.oBodyBase.sMeshPrefix + "CBody-Simplified", self.oMeshBody)
        self.oMeshBodySimplified.Materials_Remove(G.C_RexPattern_EVERYTHING, bLeaveVerts = True)         # Remove all REMAINING materials but leave their verts.  (Above removed verts + materials we don't want, now we remove all materials to have one mesh un-divided by materials)

        #=== Remove the geometry-dense areas like fingers and toes so the decimated mesh is much more efficient over the large body areas ===
        if self.oMeshBodySimplified.Open(bSelect = True):
            bpy.ops.mesh.mark_seam(clear=True)                              ###INFO: How to remove the 'red lines' between UV seams (formed when we had several materials).  See https://blender.stackexchange.com/questions/10580/what-are-the-colored-highlighted-edges-in-edit-mode
            self.oMeshBodySimplified.VertGrps_SelectVerts("_CBody_DeleteForSimplification")
            bpy.ops.mesh.delete(type='FACE')
            
            #=== Fill holes so the mesh remains closed ===
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.fill_holes(sides = 0)                               ###WEAK: Still can contain holes!  (e.g. left eye)
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
            self.oMeshBodySimplified.Close(bDeselect = True)


        #===== CREATE MAIN-SCENE COLLIDER BODY =====
        #=== Shrink the entire main-scene Flex collider body (still containing softbody geometry ===
        self.oMeshFlexTriCol_BodyMain = CMesh.AttachFromDuplicate(self.oBodyBase.sMeshPrefix + "CBody-BodyMain", self.oMeshBodySimplified)
        if self.oMeshFlexTriCol_BodyMain.Open():
            nDistShrink = CBody.C_FlexParticleSpacing / 2 * CBody.C_RatioSpacingMult_MeshShrink       # Our shrink distance is the Flex particle radius (so collisions appear at skin-depth) but adjusted by a multiplier for best effect in game (it is beneficial to have colliders stick out of the skin a bit because collisions are 'soft') 
            self.Util_DoSafeShrink(self.oMeshFlexTriCol_BodyMain, nDistShrink, CBody.C_NumIterationsForFullBodyShrink, 0)  ###DEV24:2:!!! Remove doubles??  CBody.C_RemoveDoublesDistDuringShrink)
            self.oMeshFlexTriCol_BodyMain.bm.verts.layers.int.new(G.C_DataLayer_FlexParticleInfo)          # Create the important 'ParticleInfo' custom data layer to store much info on each particle including the type of Flex particle each vert in Unity represents (e.g. 'skinned', simulated-surface-with-bone, simulated-inner, etc)
            self.oMeshFlexTriCol_BodyMain.Close() 

        #=== If mesh has a vagina (woman or shemale), perform important removal of the vagina / anus geometry and replace it with the prepared vagina hole collision mesh (a simple hexagon tube) ===
        if self.oBodyBase.sSex != "Man":
            if self.oMeshFlexTriCol_BodyMain.Open(): 
                self.oMeshFlexTriCol_BodyMain.VertGrp_SelectVerts("_CBody_VaginaCollider_DeleteVerts")        ###CHECK24: Usage of #?
                bpy.ops.mesh.delete(type='FACE')
                self.oMeshFlexTriCol_BodyMain.Close() 
            oMeshVaginaHoleCollider_TEMP = CMesh.AttachFromDuplicate_ByName("CBody_VaginaRig_Collider_TEMPFORJOIN", "CBody_VaginaRig_Collider") 
            oMeshVaginaHoleCollider_TEMP = oMeshVaginaHoleCollider_TEMP.Util_JoinWithMesh(self.oMeshFlexTriCol_BodyMain)            # Call always returns None so we can clear our reference (source of join is destroyed by join as its geometry becomes part of target)
            if self.oMeshFlexTriCol_BodyMain.Open(bDeselect = True):
                self.oMeshFlexTriCol_BodyMain.VertGrp_SelectVerts("_CBody_VaginaCollider_DeleteVerts")         # Select the edge of the just-removed vagina geometry and the bottom part of the vagina collider cylinder to bridge them with the amazing 'bridge edge loop'
                self.oMeshFlexTriCol_BodyMain.VertGrp_SelectVerts(CBody.C_Prefix_DynBone_VaginaHole + "Lower", bClearSelection = False)
                bpy.ops.mesh.bridge_edge_loops(type = "PAIRS")
                self.oMeshFlexTriCol_BodyMain.Close(bDeselect = True)

        #=== Define the appropriate soft-bodies for the character's sex ===
        if self.oBodyBase.sSex != "Woman":          ###CHECK24: Identification / separation of the softbodies for each sex done here??
            CFlexSoftBody.CFlexSoftBodyPenis(self, CBody.C_SoftBodyID_Penis, "Penis", "#Penis", ["pelvis", "Genitals", "abdomenLower", "lThighBend", "lThighTwist", "rThighBend", "rThighTwist"])
        CFlexSoftBody.CFlexSoftBody(self, CBody.C_SoftBodyID_BreastL, "BreastL", "lPectoral", ["chestLower", "chestUpper", "lCollar", "lShldrBend"])    ###IMPROVE: Add a 'quick mode' from Unity to not separate breasts??
        CFlexSoftBody.CFlexSoftBody(self, CBody.C_SoftBodyID_BreastR, "BreastR", "rPectoral", ["chestLower", "chestUpper", "rCollar", "rShldrBend"])
        self.Finalize()

    def DoDestroy(self):
        print("X--- CBody.DoDestroy() called on body '{}' ---X".format(self.oBodyBase.sMeshPrefix))
        self.oMeshBody.DoDestroy()
        self.oMeshFlexTriCol_BodyMain .DoDestroy()
        self.oMeshFlexTriCol_BodyFluid.DoDestroy()
        
        for sNameSoftBody in self.mapFlexSoftBodies:
            oSoftBody = self.mapFlexSoftBodies[sNameSoftBody]
            oSoftBody.DoDestroy()
            
        return None         # Conveniently return None so CBodyBase can set its oBody member to none.
    
    

          

    
    
    
    #-----------------------------------------------------------------------    ADD SOFT BODY

    def AddSoftBody(self, oFlexSoftBody):           # Called by CFlexSoftBody-derived ctor to convert a portion of the body mesh (e.g. left breast, penis, etc) into a complex 'Flex rig' that Unity uses to populate complex Flex structures to simulate that body part as a Flex softbody.  Critical to gameplay!
        #=== Add provided Flex soft body to the collection we manage.  We now own and manage the object ===
        self.mapFlexSoftBodies[oFlexSoftBody.nSoftBodyID] = oFlexSoftBody
        print("\n===== CBody.AddSoftBody() '{}' ID={} =====".format(oFlexSoftBody.sNameSoftBody, oFlexSoftBody.nSoftBodyID))

        #=== Define local variables ===
        sNameVertGrp_SoftBody = "_CSoftBody_" + oFlexSoftBody.sNameSoftBody               # The full name of our softbody-delimiter vertex group as defined in source mesh.
        
        #=== Append the relevant vertex groups needed for future processing in Finalize() ===
        self.aVertGroups_SoftBodies.append(sNameVertGrp_SoftBody)           # Add the softbody definition vert group to the global list.  We need these in Finalize() for smoothing
        self.aVertGroups_ToDelete.append(oFlexSoftBody.sNameVertGrp_BoneParent)           # Add the 'parent bone' for this softbody as a vert group to delete in Finalize().  Leaving this vertex group in place could interfere with bone re-weighting in Finalize (It previously defined the softbody group we can take over)   
        for sBoneToTakeOver in oFlexSoftBody.aListBonesToTakeOver:                        # Append every vertex group identified by caller as 'bones we can take over' to the set of groups we need to smooth in Finalize()
            self.setBonesNeedingSmoothing.add(sBoneToTakeOver)
       
       
        #=======  PHASE I: PROCESS RIG MESH =======
        #===== A. EXTRACT SOFTBODY FLEX COLLIDER FROM BODY FLEX COLLIDER =====
        #=== Separate the softbody from the work-in-progress Flex collider mesh being constructed ===
        if self.oMeshFlexTriCol_BodyMain.Open():
            self.oMeshFlexTriCol_BodyMain.VertGrp_SelectVerts(sNameVertGrp_SoftBody)
            bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.
            self.oMeshFlexTriCol_BodyMain.Close()
        bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')
        oFlexSoftBody.oMeshSoftBody = CMesh(self.oBodyBase.sMeshPrefix + "CBody-SoftBody-" + oFlexSoftBody.sNameSoftBody, bpy.context.scene.objects.active, bDeleteBlenderObjectUponDestroy = True)  # Obtain CMesh reference to the just-separated softbody mesh

        #=== Separate a copy of the softbody rim from the just-separated softbody mesh.  (We need to process backplate separately from surface particles) ===
        if oFlexSoftBody.oMeshSoftBody.Open(bDeselect = True):
            oFlexSoftBody.oMeshSoftBody.VertGrp_Remove(G.C_RexPattern_CodebaseBones)        # Remove all the codebase vertex groups so this doesn't interfere with weighting
            bpy.ops.mesh.select_non_manifold()          # Select the edge of the mesh...
            bpy.ops.mesh.duplicate()                    # Make a copy as we need to keep softbody surface intact 
            bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.
            oFlexSoftBody.oMeshSoftBody.Close()
        bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')
        oMeshSoftBodyBackplate = CMesh(self.oBodyBase.sMeshPrefix + "CBody-SoftBody-" + oFlexSoftBody.sNameSoftBody  + "-Backplate-TEMP", bpy.context.scene.objects.active, bDeleteBlenderObjectUponDestroy = True)  # Obtain CMesh reference to the just-separated softbody mesh
        

        #===== B. PROCESS 'BACKPLATE' SOFTBODY FLEX PARTICLES =====        
        #=== Fill the just-separated rim wire-mesh into a new surface with verts spaced at approximately the Flex particle distance.  Close the open mesh by selecting non-manifold edges and capping them.  This will form our 'backplate' of skinned particle that will anchor this softbody at runtime ===
        if oMeshSoftBodyBackplate.Open():     
            bpy.ops.mesh.select_non_manifold()          # Select the edge of the mesh...
            bpy.ops.mesh.duplicate()                    # Create a duplicate of the rim so ALL the original rim verts are included back into the source Flex collider mesh 
            bpy.ops.mesh.extrude_edges_indiv()          # With the copy of the rim verts selected collapse them to a single vert to create a surface from the wire-mesh.
            bpy.ops.mesh.edge_collapse()                # Collapse them to a single point to 'close' the mesh. We have now converted the original wire mesh into a surface ressembing a 'backplate' to the soft body.  ###INFO: The collapse will combine all selected verts into one vert at the center
    
            #=== Create regularly-spaced verts on the backplate so simulated verts / particles have a skinned neighbor to anchor to ===
            bpy.ops.mesh.select_more()                  # Singular backplate vert is now selected.  Select one more ring to select the copy of the rim verts as well ===
            bpy.ops.mesh.subdivide(number_cuts=4)       # Subdivide backfaces to provided additional verts in the back faces.  (Needed so we can find particles near the backfaces as neighboring search is vert-based)
            bpy.ops.mesh.remove_doubles(threshold=CBody.C_FlexParticleSpacing)     # First remove the excess geometry to leave only vertices spaced by the Flex particle distance...
            bpy.ops.mesh.remove_doubles(threshold=CBody.C_FlexParticleSpacing, use_unselected=True)    #... then snap that reduced geometry to the non-selected original rim verts. 
            bpy.ops.mesh.select_all(action='SELECT')        #... and finally select the entire mesh to... 
            bpy.ops.mesh.remove_doubles(threshold=.000001)  #... merge all the verts that are right on top of each other (the just moved backplate verts and our original untouched rim verts.  This leaves us with verts that represent the backplate AND all the original unmoved rim verts = All particles we need to skin at gameplay to attach the softbody to the body.
            bpy.ops.mesh.delete(type='EDGE_FACE')           # The resultant faces are heavily corrupted from the many remove_doubles().  As we only need the verts anyway clear the lines and faces to leave on the verts.
            
            #=== Flag the backplate verts as such.  Yes they are skinned but they will also be the recipients of new links / edges from simulated Flex particles (unlike regular skinned particles)  They are also used to flag 'stiff shapes' in Finalize() ===
            oLayFlexParticleInfo = oMeshSoftBodyBackplate.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
            for oVert in oMeshSoftBodyBackplate.bm.verts:
                oVert[oLayFlexParticleInfo] = CBody.C_ParticleType_SkinnedBackplate
            oMeshSoftBodyBackplate.Close()        
        

        #===== C. PROCESS 'SURFACE' SOFTBODY FLEX PARTICLES =====        
        #=== Create the simulated surface verts / particles.  These will also have bones that will drive the presentation mesh and collider meshes at runtime ===
        if oFlexSoftBody.oMeshSoftBody.Open(bDeselect = True):            # Open the working-copy softbody mesh so we can simplify its geometry for appropriately-spaced Flex particles
            oLayFlexParticleInfo = oFlexSoftBody.oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
            bpy.ops.mesh.select_non_manifold()              # Select the non manifold geometry.  This will select the rim verts of the softbody...        ###WEAK: This code assumes this surface mesh is perfectly manifold!  Any non-manifold geometry will trip this next test where code will think non-manifold geometry is the rim we're now searching for
            for n in range(2):                              # Select more verts around the rim to account for heavy decimation.  (If we just flag real rim very few verts will have that flag set after heavy decimation resulting in very few pinned rim particles)
                bpy.ops.mesh.select_more()                  ###BUG:!! Is dependant on geometry!  Penis much denser than breasts!!
            for oVert in oFlexSoftBody.oMeshSoftBody.bm.verts:            # Flag the backplate rim verts as such so we can find them again after remove_doubles()
                if oVert.select:
                    oVert[oLayFlexParticleInfo] = CBody.C_ParticleType_SkinnedBackplateRim
                    
            #=== Perform the super-important remove double to obtain the edge-length we need for proper Flex runtime simulation.  If verts / particles were any closer Softbody would 'jitter' and be unstable ===
            bpy.ops.mesh.select_all(action='SELECT') 
            bpy.ops.mesh.remove_doubles(threshold=CBody.C_FlexParticleSpacing)
            bpy.ops.mesh.select_all(action='DESELECT') 
    
            #=== Flag the softbody surface verts as Simulated-Surface Flex particle type.  Most of these will have bones assigned later on to drive the important gametime presentation mesh appearance ===
            for oVert in oFlexSoftBody.oMeshSoftBody.bm.verts:
                nParticleType = oVert[oLayFlexParticleInfo] & CBody.C_ParticleInfo_Mask_Type
                if nParticleType != CBody.C_ParticleType_SkinnedBackplateRim:                    # If this is not a rim vert it is 'surface simulated' and has a bone.  (The only ones that do!)
                    oVert[oLayFlexParticleInfo] = CBody.C_ParticleType_SimulatedSurface     ###DEV24:2:!!!!! leaves very little rim!
            oFlexSoftBody.oMeshSoftBody.Close()

        #=== Give an opportunity for our Flex Soft Body instance to modify the surface particles.  (Penis will for example will identify the uretra particle Unity needs for the fluid emitter) ===
        oFlexSoftBody.OnModifyParticles()

        
        #===== D. CREATE 'INNER' PARTICLES BY REPEATEDLY 'SHRINKING' SOFTBODY RIG MESH =====        
        #=== Create a temporary copy of our softbody surface mesh that we will gradually 'shrink' in order to provide a source of inner verts for remove_doubles() to create the inner particles ===
        aVertsInnerParticles = []
        if oFlexSoftBody.bPreventInnerParticleCreation == False:
            oMeshSoftBodyShrinker = CMesh.AttachFromDuplicate(self.oBodyBase.sMeshPrefix + "CBody-SoftBody" + oFlexSoftBody.sNameSoftBody  + "-Shrinker-TEMP", oFlexSoftBody.oMeshSoftBody)
    
            if oMeshSoftBodyShrinker.Open(bDeselect = True):
                #=== Make the shrinker mesh fully closed === 
                bpy.ops.mesh.select_non_manifold()          # Select the edge of the mesh...
                bpy.ops.mesh.extrude_edges_indiv()          # With the copy of the rim verts selected collapse them to a single vert to create a surface from the wire-mesh.
                bpy.ops.mesh.edge_collapse()                # Collapse them to a single point to 'close' the mesh. We have now converted the original wire mesh into a surface ressembing a 'backplate' to the soft body.  ###INFO: The collapse will combine all selected verts into one vert at the center
                bpy.ops.mesh.select_more()                  # Singular backplate vert is now selected.  Select one more ring to select the copy of the rim verts as well ===
                bpy.ops.mesh.subdivide(number_cuts=3)       # Subdivide back faces to provided additional verts in the back faces.  (Needed so we can find particles near the backfaces as neighboring search is vert-based)
                
                #=== Shrink the full body Flex collider by the Flex particle radius.  (We do this so collisions appear to take place at skin level instead of protruding from skin by radius) ===
                nVertsInWorkMesh = sys.float_info.max
                C_ShrinkPerIterationOnShrinker  = 0.01          ###TUNE:
                while nVertsInWorkMesh > 25:                    # Stop when the shrunken mesh have very few verts        
                    nVertsInWorkMesh = self.Util_DoSafeShrink(oMeshSoftBodyShrinker, C_ShrinkPerIterationOnShrinker, 1, C_ShrinkPerIterationOnShrinker)
                    for oVert in oMeshSoftBodyShrinker.bm.verts:      # Add the position of the continuously shrinking softbody mesh at each 'shrink level'.  We need these 'raw verts' to act as source for the softbody inner particles for remove_doubles() below
                        aVertsInnerParticles.append(oVert.co.copy())
                oMeshSoftBodyShrinker = oMeshSoftBodyShrinker.DoDestroy()          # We're done with this helper mesh and can destroy it.  (The results we needed are in 'aVertsInnerParticles')      


        #===== E. MERGE THE SURFACE AND BACKPLATE MESHES TOGETHER =====        
        #=== Join the backplate mesh into softbody mesh.  (Backplate mesh gets destroyed.  (We need to make sure no backplate verts are too close to surface particles) ===
        oMeshSoftBodyBackplate = oMeshSoftBodyBackplate.Util_JoinWithMesh(oFlexSoftBody.oMeshSoftBody)            # Call always returns None so we can clear our reference (source of join is destroyed by join as its geometry becomes part of target)

        #=== Manually insert the inner particles into our softbody mesh-in-construction === 
        if oFlexSoftBody.oMeshSoftBody.Open(bDeselect=True):
            oLayFlexParticleInfo = oFlexSoftBody.oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
            for vecVert in aVertsInnerParticles:
                oVertNew = oFlexSoftBody.oMeshSoftBody.bm.verts.new(vecVert)
                oVertNew[oLayFlexParticleInfo] = CBody.C_ParticleType_SimulatedInner        # Simulated inner particles are fully Flex-simulated and exist solely to provide 'soft body' functionality to their attached softbody shapes
            
            #=== Remove the backplate or inner verts that are too close ===
            oLayFlexParticleInfo = oFlexSoftBody.oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]          # The code below is structure to 'eat' particles too close together in a very deliberate order...  We do NOT want simulated particles too close to kinematic ones to prevent 'jumping particles'
            #--- Remove inner verts too close to either surface or backplate verts ---
            for nRepeat in range(3):          ###INFO: Remove doubles frequently fails to do everything... several iterations needed 
                oFlexSoftBody.oMeshSoftBody.DataLayer_SelectMatchingVerts(oLayFlexParticleInfo, CBody.C_ParticleType_SimulatedInner, CBody.C_ParticleInfo_Mask_Type)
                bpy.ops.mesh.remove_doubles(threshold=CBody.C_FlexParticleSpacing, use_unselected=True)
            #--- Remove backplate verts too close to either surface or inner verts ---
            for nRepeat in range(1):      
                oFlexSoftBody.oMeshSoftBody.DataLayer_SelectMatchingVerts(oLayFlexParticleInfo, CBody.C_ParticleType_SkinnedBackplate, CBody.C_ParticleInfo_Mask_Type)
                bpy.ops.mesh.remove_doubles(threshold=CBody.C_FlexParticleSpacing, use_unselected=True) 
            #--- Remove inner verts that are too close to each other --- 
            oFlexSoftBody.oMeshSoftBody.DataLayer_SelectMatchingVerts(oLayFlexParticleInfo, CBody.C_ParticleType_SimulatedInner, CBody.C_ParticleInfo_Mask_Type)
            bpy.ops.mesh.remove_doubles(threshold=CBody.C_FlexParticleSpacing)

            #=== Assign bone IDs to all simulated surface particles / verts ===                ###IMPROVE: Backplate rim verts are sparse and jagged
            oFlexSoftBody.oMeshSoftBody.DataLayer_SelectMatchingVerts(oLayFlexParticleInfo, CBody.C_ParticleType_SimulatedSurface, CBody.C_ParticleInfo_Mask_Type)     # Select only the surface-simulated verts / particles
            aBonesToAdd = {}                          # Dictionary of bones we add for this softbody.  Done this way so we can keep only one mesh open at a time.  Key is BoneID, Value is bone position
            for oVert in oFlexSoftBody.oMeshSoftBody.bm.verts:           # Remove doubles above messed up some of the verts that were previously as simulated surface.  Set again so we get every one.
                if oVert.select:
                    oVert[oLayFlexParticleInfo] |= CBody.C_ParticleType_SimulatedSurface | (self.nBoneID << CBody.C_ParticleInfo_BitShift_BoneID)       # These particles have a type, a softbodyID and a bone!
                    aBonesToAdd[self.nBoneID] = oVert.co.copy()
                    self.nBoneID += 1                               # Increment our global dynamic bone counter so no dynamic bone we create have the same ID.  This counter is important!

            oFlexSoftBody.oMeshSoftBody.Close(bDeselect=True)





        #===== F. FINALIZE SOFTBODY BY CREATING NEEDED UNITY GAME-TIME STRUCTURES =====        
        #=== Transfer the skinning information from the body mesh back to the heavily-modified softbody rig mesh ===
        if oFlexSoftBody.nSoftBodyID == CBody.C_SoftBodyID_Penis:           # Penis get special weight-transfer processing.  Because game-time penis morphing & gameplay is centered around highly-organized 'penis slice' to bend / resize the penis its weight mapping is 100% straight mapping to its particles / bones
            aBonesToChange = {}
            if oFlexSoftBody.oMeshSoftBody.Open():
                oLayFlexParticleInfo = oFlexSoftBody.oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
                oFlexSoftBody.oMeshSoftBody.DataLayer_SelectMatchingVerts(oLayFlexParticleInfo, CBody.C_ParticleType_SimulatedSurface, CBody.C_ParticleInfo_Mask_Type)     # Select only the surface-simulated verts / particles
                oFlexSoftBody.oMeshSoftBody.VertGrp_LockUnlock(False, G.C_RexPattern_EVERYTHING)
                bpy.ops.object.vertex_group_remove_from(use_all_groups=True)            # Remove the simulated surface particles / bones from all groups.  All these verts get only ONE bone = their own (for complete simulation control during morphing) while we leave the base alone to glue SoftBody to body
                for oVert in oFlexSoftBody.oMeshSoftBody.bm.verts:
                    nParticleInfo = oVert[oLayFlexParticleInfo]
                    nParticleBoneID = (nParticleInfo & CBody.C_ParticleInfo_Mask_BoneID) >> CBody.C_ParticleInfo_BitShift_BoneID
                    if nParticleBoneID > 0:
                        aBonesToChange[oVert.index] = nParticleBoneID                  
                oFlexSoftBody.oMeshSoftBody.Close()
            for nVert in aBonesToChange:            ###WEAK: We access non BMesh structure in object mode as vertex_group.add() can only be called in Object mode and current CMesh implementation would overwrite our changes in Close() with stale BMesh data
                nParticleBoneID = aBonesToChange[nVert]
                oVert = oFlexSoftBody.oMeshSoftBody.GetMeshData().vertices[nVert]
                oVertGrp_Vert = oFlexSoftBody.oMeshSoftBody.GetMesh().vertex_groups.new(self.C_Prefix_DynBone_Penis + str(nParticleBoneID))
                oVertGrp_Vert.add([oVert.index], 1, 'REPLACE')          # Every vert gets to take 100% of only one vertex group = its own
        else:        
            oFlexSoftBody.oMeshSoftBody.Util_TransferWeights(self.oMeshFlexTriCol_BodyMain)             # Other softbodies have regular weight transfer

        #===== CREATE SHAPE LINKS BETWEEN NEIGHBORING PARTICLES BY CREATING WIRE EDGES =====
        #=== Create a spacial-search KDTree so each vert can efficiently find its neighbors === 
        if oFlexSoftBody.oMeshSoftBody.Open():
            oLayFlexParticleInfo = oFlexSoftBody.oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
            oKDTree = kdtree.KDTree(len(oFlexSoftBody.oMeshSoftBody.bm.verts))
            oFlexSoftBody.oMeshSoftBody.bm.verts.ensure_lookup_table()
            for oVert in oFlexSoftBody.oMeshSoftBody.bm.verts:
                oKDTree.insert(oVert.co.copy(), oVert.index)
            oKDTree.balance()
    
            #=== For each simulated particle find the neighboring particles of the appropriate type to form 'softbody links' / Blender edges between them.  These edges will form the basis of Flex shapes below ===
            nSearchDistance = CBody.C_FlexParticleSpacing * CBody.C_RatioSpacingMult_ShapeLinkDist
            nStat_LinksActive   = 0
            nStat_LinksCreated  = 0
            for oVert1 in oFlexSoftBody.oMeshSoftBody.bm.verts:                          # In this loop we only connect dynamic particles to other dynamic particles OR backplate skinned ones (to prevent softbody from floating in space) 
                nParticleType1 = oVert1[oLayFlexParticleInfo] & CBody.C_ParticleInfo_Mask_Type
                if (nParticleType1 & CBody.C_ParticleInfo_BitTest_IsSimulated) != 0:                # Iterate through all the non-skinned particles / verts.  Only those participate in softbody shapes
                    nLinksCreatedForThisShape = 0
                    for (vecVertNeighbor, nVertNeighbor, nDist) in oKDTree.find_range(oVert1.co.copy(), nSearchDistance):           ###INFO: KDTree.find_range() conveniently returns results sorted by distance!
                        if oVert1.index != nVertNeighbor:                           # Avoid forming link with ourselves (Impossible to form edge with two same verts!)
                            oVert2 = oFlexSoftBody.oMeshSoftBody.bm.verts[nVertNeighbor]
                            nParticleType2 = oVert2[oLayFlexParticleInfo] & CBody.C_ParticleInfo_Mask_Type 
                            if ((nParticleType1 & CBody.C_ParticleInfo_BitTest_IsOnBackpate) == 0 or (nParticleType2 & CBody.C_ParticleInfo_BitTest_IsOnBackpate) == 0):      # Avoid two backplate verts forming links
                                oEdge = oFlexSoftBody.oMeshSoftBody.bm.edges.get([oVert1, oVert2])          ###INFO: How to find an existing edge
                                if oEdge == None:
                                    oEdge = oFlexSoftBody.oMeshSoftBody.bm.edges.new([oVert1, oVert2])      ###INFO: How to create a new edge
                                    nStat_LinksCreated += 1
                                nLinksCreatedForThisShape += 1
                                nStat_LinksActive += 1
                                if nLinksCreatedForThisShape >= CBody.C_MaxShapeLinks:     # Stop adding edges / links to this vert / particle when we have enough.  (As find_range() returns its results in increasing distance this means we have the closest ones!)
                                    break
            print("\n[STATS] Softbody '{}' created {} new softbody links between neighboring particles for a total of {} links.\n".format(oFlexSoftBody.sNameSoftBody, nStat_LinksCreated, nStat_LinksActive))
            
            #=== Determine the 'shape stiffness' by selecting the backplate particles and expanding ===  (These shapes are responsible for 'stiffening' the base of softbodies so they don't appear pulled out too far when moving (particular needed at penis base so base is not the only part that bends) 
            oFlexSoftBody.oMeshSoftBody.DataLayer_SelectMatchingVerts(oLayFlexParticleInfo, CBody.C_ParticleType_SkinnedBackplate, CBody.C_ParticleInfo_Mask_Type)
            bpy.ops.mesh.select_more()
            for oVert in oFlexSoftBody.oMeshSoftBody.bm.verts:
                if oVert.select: 
                    nParticleType = oVert[oLayFlexParticleInfo] & CBody.C_ParticleInfo_Mask_Type
                    if (nParticleType & CBody.C_ParticleInfo_BitTest_IsSimulated) != 0:
                        oVert[oLayFlexParticleInfo] |= 1 << CBody.C_ParticleInfo_BitShift_Stiffness      ###IMPROVE: More than one stiffness value by repeated runs 
            
    
            #===== CREATE UNITY FLEX RUNTIME STRUCTURES =====
            #=== Iterate through all verts to populate the Flex softbody arrays that Unity expects for easy Flex softbody creation ===
            nNumParticleIndices = 0
            nShapeID = 0                                            # This is where we assign super-important global shape IDs... a simple counter in this loop!
            for oVertShape in oFlexSoftBody.oMeshSoftBody.bm.verts:
                nParticleInfo = oVertShape[oLayFlexParticleInfo]
                nParticleType       = nParticleInfo & CBody.C_ParticleInfo_Mask_Type
                nParticleBoneID     = (nParticleInfo & CBody.C_ParticleInfo_Mask_BoneID)      >> CBody.C_ParticleInfo_BitShift_BoneID
                #nParticleSoftBodyID = (nParticleInfo & CBody.C_ParticleInfo_Mask_SoftBodyID)  >> CBody.C_ParticleInfo_BitShift_SoftBodyID
    
                oFlexSoftBody.aParticleInfo.AddInt(nParticleInfo)
                
                if (nParticleType & CBody.C_ParticleInfo_BitTest_IsSimulated) != 0:                # Iterate through all the non-skinned particles / verts.  Only those participate in softbody shapes
                    #print("--- FlexRig:  ShapeId={:3d}   Type={}   SB={}   Bone={}".format(nShapeID, nParticleType, nParticleSoftBodyID, nParticleBoneID))
                    oFlexSoftBody.aShapeVerts.AddInt(oVertShape.index)
                    oFlexSoftBody.aShapeParticleIndices.AddInt(oVertShape.index)             # We always add our vert to our own shape (1:1 relationship)      
                    nNumParticleIndices += 1
                    vecShapeCenter = oVertShape.co.copy()
                     
                    #=== Iterate through all edges of this simulated particle / vert.  They are part of this shape === 
                    for oEdge in oVertShape.link_edges:
                        oVertNeighbor = oEdge.other_vert(oVertShape)
                        oFlexSoftBody.aShapeParticleIndices.AddInt(oVertNeighbor.index)
                        nNumParticleIndices += 1
                        vecShapeCenter += oVertNeighbor.co.copy()
                        #print("-- Shape {:3d} adds Particle {:3d}.  # indices = {:4d}".format(oVertShape.index, oVertNeighbor.index, nNumParticleIndices ))
                    vecShapeCenter /= len(oVertShape.link_edges) + 1
                         
                    #=== Push in our split point in oFlexSoftBody.aShapeParticleIndices so Flex can unflatten the aShapeParticleIndices flat array and properly match what particle connects to which shape === 
                    oFlexSoftBody.aShapeParticleOffsets.AddInt(nNumParticleIndices)
    
                    #=== Add values to the particle-to-bone indirection map ===        ###DESIGN24: Ditch this indirection now that we're separated??
                    if nParticleBoneID > 0:                         # Bones are one-based and a zero bone ID = no bone
                        oFlexSoftBody.aFlatMapBoneIdToShapeId.AddUShort(nParticleBoneID)     # Flat map is a simple list of <Bone1>, <Shape1>, <Bone2>, <Shape2>, etc. 
                        oFlexSoftBody.aFlatMapBoneIdToShapeId.AddUShort(nShapeID)
                    nShapeID += 1                                           # We're done defining this shape, switch our important shape counter to the next one
                    
            
            #=== Smooth, limit than normalize all bones in Flex rig ===
            oFlexSoftBody.oMeshSoftBody.VertGrp_Remove(G.C_RexPattern_CodebaseBones)        # Remove all the codebase vertex groups so this doesn't interfere with weighting
            oFlexSoftBody.oMeshSoftBody.VertGrp_LimitAndNormalize(0.5)
            oFlexSoftBody.oMeshSoftBody.Close()
        
        #=== Ensure that all verts have legal weighting ===
        if self.bPerformSafetyChecks:
            #oFlexSoftBody.oMeshSoftBody.MeshMode_Edit()
            oFlexSoftBody.oMeshSoftBody.SafetyCheck_CheckBoneWeighs()
        oFlexSoftBody.oMeshSoftBody.Finalize()
            
        #=== Close the serialization arrays so Unity can grab them ===         
        oFlexSoftBody.aParticleInfo.CloseArray()
        oFlexSoftBody.aShapeVerts.CloseArray()
        oFlexSoftBody.aShapeParticleIndices.CloseArray()
        oFlexSoftBody.aShapeParticleOffsets.CloseArray()
        oFlexSoftBody.aFlatMapBoneIdToShapeId.CloseArray() 





        
        
        #=======  PHASE II: PROCESS PRESENTATION SOFTBODY MESH =======
        #===== A. CREATE BONES WHERE SURFACE-LEVEL PARTICLES ARE =====
        #=== Open the main body's armature ===         
        SelectObject(self.oArmNode.name)                                # Must select armature Blender object to modify 'edit_bones' collection...
        bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
        oBoneParent = self.oArm.edit_bones[oFlexSoftBody.sNameVertGrp_BoneParent] 
        nDistBone = CBody.C_FlexParticleSpacing * CBody.C_RatioSpacingMult_BoneInfluence  # Determine how large the envelope influence as a ratio of Flex particle distance 
        nRatioEnvelopeToBone = 0.9                                      # Most of the envelope is the envelope part itself with a tiny hard 'bone part' with 100% weighting (we want mostly a blend of influence, not 100% bone competition with one-another)

        #=== Add the new bones to the open armature ===
        for nBoneID in aBonesToAdd:
            vecPosBone = aBonesToAdd[nBoneID]
            oBone = self.oArm.edit_bones.new(G.C_Prefix_DynBones + oFlexSoftBody.sNameSoftBody + "-" + str(nBoneID))
            oBone.parent = oBoneParent
            oBone.head = vecPosBone                                         ###NOTE: The bone will *move* from the particle position we're setting it now (so bone envelope work properly) to the shape center that Unity needs later (converted in Finalize)
            oBone.tail = oBone.head - Vector((0,0.001,0))                   ###OPT:!!!! We can probably find a bone orientation that gets ride of nasty runtime bone re-orientation in Unity Update()
            oBone.use_connect = False
            oBone.envelope_weight = 1
            oBone.envelope_distance = nDistBone * nRatioEnvelopeToBone      ###NOTE: 'envelope distance does not appear to work as we want (e.g. setting head_radius and tail_radius ot zero and our radius in envelope_distance -> head and tail get set to that value!)
            oBone.head_radius = oBone.tail_radius = nDistBone * (1 - nRatioEnvelopeToBone)

        #=== Separate the softbody in the presentation mesh so we can re-weight it from the envelopes of the bones we just created ===
        if self.oMeshBody.Open():
            self.oMeshBody.VertGrp_SelectVerts(sNameVertGrp_SoftBody)
            bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.
            self.oMeshBody.Close()
        bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')
        oMeshSoftBodyPres = CMesh(self.oBodyBase.sMeshPrefix + "CBody-" + oFlexSoftBody.sNameSoftBody  + "-Presentation", bpy.context.scene.objects.active, bDeleteBlenderObjectUponDestroy = True)
        
        #=== Remove vertex groups we're supposed to take over.  This will clear their influence in just the softbody area while not touching the other body verts.  This will give us the dynamic range to claim all four bones for the softbody and have the smoothing possible run-time appearance (Smoothing in Finalize() will blend DAZ-bones at the border)  Note that still exist in main body and will feature an abrubt cut in bone weighting that is deliberate.  (Smoothing in Finalize() will take care of this)
        for sBoneToTakeOver in oFlexSoftBody.aListBonesToTakeOver:
            oMeshSoftBodyPres.VertGrp_Remove(re.compile(sBoneToTakeOver))       ###INFO: How to create a Regular Expression from a string on-the-fly
        oMeshSoftBodyPres.VertGrp_Remove(re.compile(oFlexSoftBody.sNameVertGrp_BoneParent))        # Also remove our owner bone (We completely take that one over and destroy it in Finalize())
        
        #=== Un-parent and then re-parent to armature object in envelope weight mode to automatically assign bone weights via the bones we just defined ===
        oMeshSoftBodyPres.MeshMode_Object()
        SelectObject(oMeshSoftBodyPres.GetName())
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')                ###INFO: How to properly un-parent.
        self.oArmNode.select = True
        bpy.context.scene.objects.active = self.oArmNode
        bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')                     ###INFO: How to re-parent with an operation  ###INFO: How to re-weight an entire mesh by envelope  Note that this clears existing vertex groups            #self.oArmNode.hide = True                                                   ###INFO: For some reason hiding the parent makes it impossible later on to deselect causing next iteration of this call to crash when body armature cannot be unselected during next softbody separation!
        
        if oFlexSoftBody.nSoftBodyID == CBody.C_SoftBodyID_Penis:               ###DESIGN24: Move to subclass??
            self.oMeshPenisColliderPhysX = CMesh.AttachFromDuplicate(self.oBodyBase.sMeshPrefix + "CBody-Penis-Collider", oMeshSoftBodyPres)
            self.oMeshPenisColliderPhysX.SetParent(self.oBodyBase.oNodeRoot.GetName())
            self.oMeshPenisColliderPhysX.Materials_Remove(G.C_RexPattern_EVERYTHING, bLeaveVerts = True)    # Remove all materials as we're a PhysX collider
            if self.oMeshPenisColliderPhysX.Open():
                self.oMeshPenisColliderPhysX.VertGrp_SelectVerts("_CPenis_Shaft")        # Remove the scrotum from the penis collider.  Only the shaft is needed to expand vagina
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.mesh.delete(type='FACE')          
                self.oMeshPenisColliderPhysX.VertGrp_Remove(G.C_RexPattern_CodebaseBones)        # Remove all the codebase vertex groups so this doesn't interfere with weighting
                self.oMeshPenisColliderPhysX.Decimate_All(600)          ###TUNE:
                #self.oMeshPenisColliderPhysX.Decimate_MinArea(0.50, nFaceAreaMin = 0.000015)
                self.oMeshPenisColliderPhysX.Close(bHide = True)

        #=== Join temporarily-separated softbody presentation mesh back into main body presentation mesh =====
        oMeshSoftBodyPres = oMeshSoftBodyPres.Util_JoinWithMesh(self.oMeshBody)            # Call always returns None so we can clear our reference (source of join is destroyed by join as its geometry becomes part of target)




    #-----------------------------------------------------------------------    FINALIZE
    
    def Finalize(self):                             # Called by top-level CBody to 'Finalize' the mesh following a sequence of calls to 'AddSoftBody()'.  In charge of smoothing the meshes around damaged areas, forming softbody links and constructing structures Unity needs for Flex softbody creation.   
        print("\n=== CBody.Finalize() ===")
        G.Dump("- Finalize()")


        #=======  BODY MAIN-SCENE COLLIDER MESH FINALIZATION =======
        #=== Shrink the main-scene Flex body collider so collisions appear at skin level ===
        if self.oMeshFlexTriCol_BodyMain.Open():
            G.Dump("- Before area decimates")
            #=== Perform gradual decimation of smallest geometry ===
#             self.oMeshFlexTriCol_BodyMain.Decimate_MinArea(0.30, nFaceAreaMin = 0.000005)         ###TUNE:
#             self.oMeshFlexTriCol_BodyMain.Decimate_MinArea(0.35, nFaceAreaMin = 0.000010)        ###BROKEN:!!! These make Decimate_All() crash Blender below!!
#             self.oMeshFlexTriCol_BodyMain.Decimate_MinArea(0.45, nFaceAreaMin = 0.000015)
#             self.oMeshFlexTriCol_BodyMain.Decimate_MinArea(0.50, nFaceAreaMin = 0.000025)

            #=== Perform controlled decimation ===
            G.Dump("- Before DecimateAll()")
            self.oMeshFlexTriCol_BodyMain.Decimate_All(900)         ###TUNE:            ###WARNING: Decimate on woman can decimate vagina track!!
            G.Dump("- After DecimateAll()")
            #self.oMeshFlexTriCol_BodyMain.Decimate_MinArea(0.50, nFaceAreaMin = 0.000200)        # Perform one final LARGE area-based decimation as master decimate-all above still leaves faces that can be quite small
            #G.Dump("- After DecimateArea()")

            #=== Limit and normalize then check that all verts have four bones and the weight sums add to one ===
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.faces_shade_flat()
            self.oMeshFlexTriCol_BodyMain.VertGrp_Remove(G.C_RexPattern_CodebaseBones)        # Remove all the codebase vertex groups so this doesn't interfere with weighting
            self.oMeshFlexTriCol_BodyMain.VertGrp_LimitAndNormalize()
            self.oMeshFlexTriCol_BodyMain.Close()  
            
        if self.bPerformSafetyChecks:
            self.oMeshFlexTriCol_BodyMain.SafetyCheck_CheckBoneWeighs()




        #=======  PRESENTATION MESH FINALIZATION =======
        if self.oMeshBody.Open():
            #=== Weld the separated-then-rejoined softbody presentation meshes back with the main presentation mesh by welding non-manifold (rim) verts ===
            bpy.ops.mesh.select_non_manifold()                      ###WEAK: This non-manifold can easily pickup bad geometry on the softbodies and perform heaving smoothing on them... a problem?
            bpy.ops.mesh.remove_doubles(threshold=0.000001)
    
            #=== Destroy the vertex groups we're supposed to remove before any smoothing occurs (we need their dynamic range during important 'Normalize' below) ===
            for sNameVertGrp_ToDelete in self.aVertGroups_ToDelete:
                self.oMeshBody.VertGrp_Remove(re.compile(sNameVertGrp_ToDelete))
    
            #=== Decimate high-geometry parts of the body mesh to reasonable levels (now that user has morphed the body we can decimate) ===
            if self.oBodyBase.sSex != "Woman":
                self.oMeshBody.Decimate_VertGrp("_CSoftBody_Penis", 0.15)           ###TUNE:
            if self.oBodyBase.sSex != "Man":
                self.oMeshBody.VertGrp_SelectVerts("_CVagina_Decimate")
                bpy.ops.mesh.tris_convert_to_quads()            ###IMPROVE: Do this before triangulation?
                bpy.ops.mesh.unsubdivide(iterations=6)
                bpy.ops.mesh.quads_convert_to_tris()
                bpy.ops.object.vertex_group_assign()
                #self.oMeshBody.Decimate_VertGrp("_CVagina_Decimate", 0.1)           ###TUNE:    ###INFO: Crashes Blender!  (Because of non-manifold geometry?)  ->  Switched to unsubdivide approach
            
            #=== Perform HEAVY *global* smoothing on the verts around the rims of all softbodies for ALL vertex groups ===
            bpy.ops.mesh.select_all(action='DESELECT')
            for sNameVertGrp_SoftBodies in self.aVertGroups_SoftBodies:
                self.oMeshBody.VertGrp_SelectVerts(sNameVertGrp_SoftBodies, bClearSelection = False)
            bpy.ops.mesh.select_less()          # Select one less so region-to-loop + select_more select more toward the softbody
            bpy.ops.mesh.region_to_loop()       ###INFO: The amazing weight paint mode unfortunately cannot perform advanced selection, but it takes the selection of edit mode so we do our advanced selection stuff there.
            for nRepeat in range(2):            # Select rings around the rim border for heavy smoothing below        ###TUNE
                bpy.ops.mesh.select_more()
            self.oMeshBody.VertGrp_LockUnlock(False, G.C_RexPattern_EVERYTHING)
            #bpy.ops.object.mode_set(mode='WEIGHT_PAINT')            #self.oMeshBody.GetMeshData().use_paint_mask_vertex = True            ###INFO: Weight paint's masking by vertex is amazing!  Enables partial update to bones!
            bpy.ops.object.vertex_group_smooth(factor=0.5, repeat=3, expand=0, group_select_mode='ALL')     ###TUNE
            
            #=== Fix possible problem with vertex_group_smooth() above leaving some verts completely ungrouped ===
            bpy.ops.mesh.select_ungrouped()     ###INFO: It has been observed that vertex_group_smooth() above frequently leaves some vertices completely ungrouped!  Here we find them and smooth around them to re-insert them into the skinned mesh!  WTF???  
            bpy.ops.mesh.select_more()
            bpy.ops.object.vertex_group_smooth(factor=0.5, repeat=3, expand=0, group_select_mode='ALL')
    
            #=== Select only the softbodies and perform strong smoothing of ONLY our dynamic bones ===
            bpy.ops.mesh.select_all(action='DESELECT')
            for sNameVertGrp_SoftBodies in self.aVertGroups_SoftBodies:
                self.oMeshBody.VertGrp_SelectVerts(sNameVertGrp_SoftBodies, bClearSelection = False)
            self.oMeshBody.VertGrp_LockUnlock(True,  G.C_RexPattern_StandardBones)
            self.oMeshBody.VertGrp_LockUnlock(False, G.C_RexPattern_DynamicBones)
            bpy.ops.object.vertex_group_smooth(repeat=3, factor=0.5)
    
            #=== Unlock EVERYTHING and perform FINAL limit and normalize that ensure Mesh renders properly in Unity === 
            bpy.ops.mesh.select_all(action='SELECT')
            self.oMeshBody.VertGrp_LockUnlock(False, G.C_RexPattern_EVERYTHING)
            self.oMeshBody.VertGrp_Remove(G.C_RexPattern_CodebaseBones)        # Remove all the codebase vertex groups so this doesn't interfere with weighting
            bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)       ###INFO: We *must* first limit, then normalize to guarantee we have a max of 4 bones AND all verts have weight sums of 1
            bpy.ops.object.vertex_group_normalize_all(lock_active=False)

            self.oMeshBody.Close()
            
        #=== Ensure that all verts have four bones and the weight sums add to one ===
        if self.bPerformSafetyChecks:
            self.oMeshBody.SafetyCheck_CheckBoneWeighs()

            
        
        
        #===== CREATE FLEX FLUID COLLIDER =====    
        #=== Take over the simplified mesh so it becomes our fluid-scene collider mesh.  (No further need of simplified body) ===
        #self.oMeshFlexTriCol_BodyFluid = CMesh.AttachFromDuplicate(self.oBodyBase.sMeshPrefix + "CBody-BodyFluid", self.oMeshBodySimplified)
        self.oMeshFlexTriCol_BodyFluid = self.oMeshBodySimplified
        self.oMeshFlexTriCol_BodyFluid.SetName(self.oBodyBase.sMeshPrefix + "CBody-BodyFluid")
        self.oMeshBodySimplified = None
        SelectObject(self.oMeshFlexTriCol_BodyFluid.GetName())                ###IMPROVE: Remove inner parts of the body mesh like teeth, eyes, vagina inside and anus so no verts of decimate are wasted on geometry we don't need
        self.oMeshFlexTriCol_BodyFluid.Modifier_Remesh(7, 0.7)          ###OPT: ###TUNE # Remesh the whole source body into reasonably-spaced geometry suitable for repeling fluid particles in Flex fluid solver

        #=== Perform controlled decimation and cleanup ===
        if self.oMeshFlexTriCol_BodyFluid.Open():
            self.oMeshFlexTriCol_BodyFluid.Decimate_All(1100)         ###TUNE:        ###IMPROVE: Grow mesh?
            self.oMeshFlexTriCol_BodyFluid.Decimate_MinArea(0.50, nFaceAreaMin = 0.00040)        # Perform one LARGE final area-based decimation as master decimate-all above still leaves faces that can be quite small
            #--- Just delete the non-manifold geometry  (They are probably inner like between the breasts and not that important) ===
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_non_manifold()        
            bpy.ops.mesh.delete(type='VERT')                ###HACK24:!!! Taking a sizable shortcut... deleting non-manifold verts for expediency... a more refined approach could save that geometry?          
            self.oMeshFlexTriCol_BodyFluid.Close()
    
        #=== Re-skin the mesh so this Flex fluid collider moves with the body's bones during gameplay ===
        self.oMeshFlexTriCol_BodyFluid.Util_TransferWeights(self.oMeshBody, bAddArmature = True)     ###IMPROVE: Push the mesh further so no part of coarse mesh gives the appearance of fluid going into body?  ###IMPROVE: Perform less aggressive decimation on some parts of mesh (e.g. Penis)
    
        #=== Limit and normalize then check that all verts have four bones and the weight sums add to one ===
        if self.oMeshFlexTriCol_BodyFluid.Open(bSelect = True):
            bpy.ops.mesh.faces_shade_flat()
            self.oMeshFlexTriCol_BodyFluid.VertGrp_Remove(G.C_RexPattern_CodebaseBones)        # Remove all the codebase vertex groups so this doesn't interfere with weighting
            self.oMeshFlexTriCol_BodyFluid.VertGrp_LimitAndNormalize()       
            self.oMeshFlexTriCol_BodyFluid.Close()

        #=== Perform safety checks ===
        if self.bPerformSafetyChecks:
            self.oMeshFlexTriCol_BodyFluid.SafetyCheck_CheckBoneWeighs()      ###OPT:!!!! This safety check stuff adds up!  Can find a way to not have to limit + normalize??

        #=== Finalize all the CMesh we manage.  Entire codebase is done modifying them and they are ready for final modifications for Unity ===
        self.oMeshFlexTriCol_BodyMain.Finalize()
        self.oMeshFlexTriCol_BodyFluid.Finalize()
        self.oMeshFlexTriCol_BodyMain.Finalize()
        self.oMeshBody.Hide()
        self.oArmNode.hide = True
        G.Dump("- Done Finalize()")

        print("\n=== CBody.Finalize('{}') finishes without errors ===\n".format(self.oBodyBase.sMeshPrefix))





    #-----------------------------------------------------------------------    WORKER FUNCTIONS

    def Util_DoSafeShrink(self, oMesh, nShrinkDistance, nIterations, nRemoveDoublesPerIteration):       # Utility function that performs a 'safe shrink' of the 'oMesh' mesh while maintaining mesh fully manifold 
        nShrinkPerIteration = nShrinkDistance / nIterations
        
        #=== Perform the super-important safe remove doubles first.  This safe version will clean up horrible degenerate geometry that would cause later code to fail ===
        oMesh.VertGrp_SelectVerts("#CBody_SafeVertsForShrink", bDeselect=True, bThrowIfNotFound=False)
        oMesh.Util_SafeRemoveDouble(nRemoveDoublesPerIteration)      # Start with dissolve right off the top so every shrink in loop below is followed by a dissolve to clean things up
        
        #=== Iterate the required number of times to gradually & safely shrinking the mesh.  We clean up after every iteration to avoid compounding non-manifold problems ===
        for nIteration in range(nIterations):
            nVertsInWorkMesh = len(oMesh.bm.verts)
            #print("-- DoShrink #{}/{}   Shrinking to {}   Verts={}".format(nIteration, nIterations, (nIteration+1)*nShrinkPerIteration, nVertsInWorkMesh))

            #=== Shrink the mesh by the amount for this iteration ===
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.shrink_fatten(value=nShrinkPerIteration)

            #=== Right after shrink we perform the super-important safe remove doubles.  This safe version will clean up horrible degenerate geometry that would cause later code to fail ===
            oMesh.VertGrp_SelectVerts("#CBody_SafeVertsForShrink", bDeselect=True, bThrowIfNotFound=False)
            oMesh.Util_SafeRemoveDouble(nRemoveDoublesPerIteration)
            
            #=== Perform smoothing on the sharpest edges, applying more strength to sharpest ones first ===
            bpy.ops.mesh.select_all(action='DESELECT')
            for nRepeat in range(1):                                                      ###OPT: Optimize some of this... probably not all required now that Util_SafeRemoveDouble() above does so much!
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.edges_select_sharp(sharpness=radians(45))
                bpy.ops.mesh.vertices_smooth(factor=1.0, repeat=1)
            for nRepeat in range(1):
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.edges_select_sharp(sharpness=radians(30))
                bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=1)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.edges_select_sharp(sharpness=radians(20))
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.vertices_smooth(factor=CBody.C_ExtraEdgeSmoothing, repeat=1)
            
            #=== Perform small amount of smoothing on whole mesh ===
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.vertices_smooth(factor=0.1, repeat=1)
            
            nVertsInWorkMesh = len(oMesh.bm.verts)

        #=== Make sure we are leaving a shrunken mesh that is still manifold! ===
        if self.bPerformSafetyChecks:       ###DEV24:!!! Too expensive? ###OPT:
            oMesh.SafetyCheck_CheckForManifoldMesh("Util_DoSafeShrink() found non-manifold geometry on mesh '{}'".format(oMesh.GetName()))      # If this fails we need to refine shrinking algorithm that ran above
        
        return nVertsInWorkMesh

    
    @classmethod
    def DEBUG_SelectDataLayerMatch(cls, nSoftBodyID, nValueSearch, nValueMask = C_ParticleInfo_Mask_Type):           # Debug function to show which rig verts are of what C_ParticleType_xxx
        ###DEBUG: To call: from CBody import *; CBody.DEBUG_SelectDataLayerMatch(4, 4)
        oSoftBody = cls.DEBUG_INSTANCE.mapFlexSoftBodies[nSoftBodyID]       ###IMPROVE: Have more of these 'debug functions' to easily verify algorithm functioning from Python console!
        oSoftBody.oMeshSoftBody.MeshMode_Object()
        if oSoftBody.oMeshSoftBody.Open():
            oLayFlexParticleInfo = oSoftBody.oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
            oSoftBody.oMeshSoftBody.DataLayer_SelectMatchingVerts(oLayFlexParticleInfo, nValueSearch, nValueMask)
            oSoftBody.oMeshSoftBody.Close(bDeselect = False)
        oSoftBody.oMeshSoftBody.MeshMode_Edit()

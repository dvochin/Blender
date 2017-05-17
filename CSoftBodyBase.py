import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

from gBlender import *
import G
from CBody import *
from CMesh import *


class CSoftBodyBase():          ###DESIGN19: Re-merge CSoftBody in here now that skin is gone??
    # CSoftBodyBase: Abstract base class offering the common denominator for CSoftBody and CSoftBodySkin: rim and pinned particle creation.
    def __init__(self, oBody, sSoftBodyPart):
        self.oBody                  = oBody             # The back-reference to the owning body.
        self.sSoftBodyPart          = sSoftBodyPart     # The name of the soft body part.  (e.g. "BreastL", "BreastR", "Penis", "Vagina", etc)  This is our key in self.oBody.aSoftBodies[self.sSoftBodyPart]

        self.oMeshSoftBody          = None              # The softbody user-visible presentation mesh.  Visible in Unity and moved by Flex softbody simulation.
        self.oMeshSoftBodyRim       = None              # The small body cutout mesh responsible to manually move softbody edge verts to the position and normal of their corresponding rim verts on the main skinned body.  Critically important for a 'seamless' connection to the main skinned body!

        self.aMapRimVerts           = CByteArray()      # Map that is serialized to Unity to map which edge verts from the 'detached softbody' maps to which edge vert in the skinned main body.  Unity needs this to move at every frame each softbody edge vert for seamless connection with main skinned body.

        ###TODAY### Belongs here??  Do we reuse backmesh for FlexSkin with two meanings??
        self.oMeshSoftBodyRimBackmesh = None            # The 'backmesh' mesh is a 'filled-in' version of the 'cap' applied to the cutout softbody mesh to make it solid.  It exists for the purpose of finding Flex particles that should be pinned instead of simulated and therefore 'pin' the softbody to the 'hard part' of the main skinned body (e.g. hip for penis, torso for breasts, etc)  It is created by subclasses 
        self.oMeshPinnedParticles   = None              # Skinned mesh containing the 'pinned particles' responsible for fixing some of the softbody particles to appropriate positions on the skinned main body (so softbody doesn't float into space!)  Created by finding Flex particles that are close to verts on self.oMeshSoftBodyRimBackmesh     
        self.aMapPinnedParticles    = None              # Map that is serialized to Unity storing pairs of <#RimParticle in self.oMeshSoftBodyRim, #Particle in SoftBody> so Unity can pin the softbody particles to their appropriate location on the skinned main body.


        print("=== CSoftBodyBase.ctor()  oBody = '{}'  sSoftBodyPart = '{}'  ===".format(self.oBody.oBodyBase.sMeshPrefix, self.sSoftBodyPart))


        #===== EXTRACT SOFT BODY MESH FROM BODY AND MAP EDGE VERTS =====
        #=== Prepare naming of the meshes we'll create and manage ===
        sNameSoftBody = self.oBody.oBodyBase.sMeshPrefix + "SB-" + self.sSoftBodyPart         # Name for to-be-created detached softbody mesh
        sNameSoftBodyRim = sNameSoftBody + G.C_NameSuffix_Rim                       # The name of the 'softbody rim' mesh (for pinning softbody to skinned body) 
     
        #=== Open the body's mesh (the one meant to be a source of softbody mesh removals) and create a temporary data layer for mapping of rim verts ===
        bmBody = self.oBody.oMeshBody.Open()
        oLayTwinID = bmBody.verts.layers.int.new(G.C_DataLayer_TwinID)  # Create a temp custom data layer to store IDs of rim verts so we remap easily when softbody is detached from main body.    ###LEARN???: This call causes BMesh references to be lost, so do right after getting bmesh reference
        
        #=== Obtain the vertex group of name 'self.sSoftBodyPart' from the source body mesh so we can detach into our softbody mesh ===
        VertGrp_SelectVerts(self.oBody.oMeshBody.GetMesh(), G.C_VertGrp_CSoftBody + self.sSoftBodyPart)

        #=== Find the edge verts of the softbody submesh so that we can determine the verts that will become edge verts between the two split meshes ===
        bpy.ops.mesh.region_to_loop()           # This will select only the edge verts at the boundary of the softbody vertex group selected above (find the edge verts)
        nNextTwinID = 1                         # We start the next rim vert ID to one (non rim-verts have a default value of zero)
        for oVert in bmBody.verts:              # Iterate over the verts at the edge at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut...
            if oVert.select:                    # ... this enables us to avoid inserting erroneous edge verts such as for vagina/anus opening)
                if oVert.is_manifold:           ###OPT!! Faster if we first create a list of BVerts using [] notation?  
                    oVert[oLayTwinID] = nNextTwinID
                    nNextTwinID += 1
    

        #===== A. SOFTBODY SKINNED RIM CREATION =====
        #=== Create the 'rim' skinned mesh that Unity will 'bake' at every frame so verts & normals are moved at every frame for a seamless connection to main skinned body.  (for a short while it also contains the softbody mesh (detached in section below) === 
        #=== Split and separate the rim + softbody mesh from the body mesh.  (Body gets that geometry removed and is what is rendered in game) ===
        VertGrp_SelectVerts(self.oBody.oMeshBody.GetMesh(), G.C_VertGrp_CSoftBody + self.sSoftBodyPart)      # Select from the skinned mesh game body the softbody part to remove from it...
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')           # We perform the split by faces so edge verts remain in both meshes (to have a seamless bridge)
        bpy.ops.mesh.select_more()              # Select one more ring of faces.  This extra ring will form our 'rim' responsible to 'pin' the edges of the softbody to the skinned body.
        bpy.ops.mesh.duplicate()                # Duplicate the rim + softbody geometry for separation below.  Note that body geometry not modified yet.  Its verts will be removed in group below when we can select only softbody part (e.g. rim stays in body!)
        bpy.ops.mesh.separate()                 # 'Separate' the selected polygon into its own mesh.  It will become our 'rim + softbody mesh' and eventually just the rim mesh.  Rest of main body simulates as usual while what will be separated requires extra runtime processing for softbodies, soft skins, etc ===

        #=== Delete from the main skinned body the softbody mesh only (e.g. without rim!) ===
        VertGrp_SelectVerts(self.oBody.oMeshBody.GetMesh(), G.C_VertGrp_CSoftBody + self.sSoftBodyPart)      # Re-select the softbody verts but this time don't expand selection by one for rim
        bpy.ops.mesh.delete(type='FACE')        # Delete the softbody faces.  Edge verts are still there and will form the bridge to the just-separated softbody mesh
        self.oBody.oMeshBody.Close()            # We're done modifying main skinned body.             

        #=== Process and rename the just-separated rim + softbody mesh ===
        bpy.context.object.select = False                                       ###LEARN: Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]      # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBodyRim = CMesh(sNameSoftBodyRim, bpy.context.scene.objects.active, None)     # Obtain CMesh reference to our softbody mesh. 
        self.oMeshSoftBodyRim.GetMesh().modifiers.clear()                       # Remove the modifiers to save memory (e.g. armature) ###LEARN: How to remove all modifiers
        self.oMeshSoftBodyRim.SetParent(self.oBody.oMeshBody.GetName())
        self.oBody.oMeshBody.Close()

        #=== Separate the softbody out of the rim + softbody (leaving only the rim) ===  
        self.oMeshSoftBodyRim.Open()                # Open the rim + softbody mesh so we can further process it.
        VertGrp_SelectVerts(self.oMeshSoftBodyRim.GetMesh(), G.C_VertGrp_CSoftBody + self.sSoftBodyPart)
#         if type(self) is CSoftBodySkin:             # If we're a soft body skin we need to keep the rim with the full geometry for further processing as a collider in subclass...       ###LEARN: How to determine type of an object
#             bpy.ops.mesh.duplicate()                # ... so duplicate the vert group instead of splitting it so we have the rim + soft body geometry for subclass processing. (CSoftBodySkin need these vertices skinned as well so the 'soft skinned' can move closely with the actual skinned body part)
#         else:
        bpy.ops.mesh.split()                    # ... for regular softobdy 'split' the softbody faces to leave in the rim mesh only the rim.  Both 'sides' will now have 'rim verts' where the two submeshes meet
        bpy.ops.mesh.separate()                     # ... and finally 'separate' the softbody geometry into its own softbody presentation + Flex mesh.  It will become our 'softbody mesh'
        self.oMeshSoftBodyRim.Close()

        #=== Fetch the just-created 'soft body' mesh and set it to its proper name ===
        bpy.context.object.select = False                                               # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]              # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBody = CMesh(sNameSoftBody, bpy.context.scene.objects.active)     # Obtain CMesh reference to our rim mesh
        bpy.ops.object.vertex_group_remove(all=True)                                    # Remove all vertex groups from detached softbody to save Blender memory
        self.oMeshSoftBody.SetParent(self.oBody.oMeshBody.GetName())

        #=== Cleanup the rim mesh by removing all materials and non-bones vertex groups ===
        SelectAndActivate(self.oMeshSoftBodyRim.GetName())
        Cleanup_RemoveMaterials(self.oMeshSoftBodyRim.GetMesh())
        #self.oMeshSoftBodyRim.Hide()


        #===== B. CREATE THE RIM VERT MAPPING in self.aMapRimVerts: Responsible to 'glue' the simulated edge verts to the main skinned body for 'seamless' appearance =====
        #===1. Iterate over all rim mesh verts to find the edge verts so #3 below can map softbody edge verts to the edge verts on the rim ===
        bmRim = self.oMeshSoftBodyRim.Open()
        oLayTwinID = bmRim.verts.layers.int[G.C_DataLayer_TwinID]
        aMapTwinId2VertRim = {}             # Map from TwinID to vert index on rim vert
        for oVert in bmRim.verts:
            nTwinID = oVert[oLayTwinID]     ###OPT!!!  Do earlier??
            if nTwinID != 0:
                aMapTwinId2VertRim[nTwinID] = oVert.index
                #print("TwinID {:3d} = RimVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
        self.oMeshSoftBodyRim.Close()

        #===2. Iterate through the verts of the newly separated softbody to access the freshly-created TwinID custom data layer help us travers from the softbody mesh to its rim mesh ===
        bmSoftBody = self.oMeshSoftBody.Open()
        oLayTwinID = bmSoftBody.verts.layers.int[G.C_DataLayer_TwinID]
        aMapTwinId2VertSoftBody = {}
        for oVert in bmSoftBody.verts:
            nTwinID = oVert[oLayTwinID]
            if nTwinID != 0:
                aMapTwinId2VertSoftBody[nTwinID] = oVert.index
                #print("TwinID {:3d} = SoftBodyVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
        self.oMeshSoftBody.Close()

        #===3. Bridge the two maps together to 'flatten' them into a map of SoftBody edge vert to rim edge vert ===
        for nTwinID in aMapTwinId2VertSoftBody:
            nVertTwinSoftBody = aMapTwinId2VertSoftBody[nTwinID]
            if nTwinID in aMapTwinId2VertRim:
                nVertTwinRim = aMapTwinId2VertRim[nTwinID]
                #print("TwinID {:3d} = SoftBodyVert {:5d} = RimVert {:5d}".format(nTwinID, nVertTwinSoftBody, nVertTwinRim))
                self.aMapRimVerts.AddUShort(nVertTwinSoftBody)
                self.aMapRimVerts.AddUShort(nVertTwinRim)
            else:
                print("###EXCEPTION: CSoftBody.SeparateSoftBodyPart() finding nTwinID {} in aMapTwinId2VertRim".format(nTwinID))
                #raise Exception("###EXCEPTION: CSoftBody.SeparateSoftBodyPart() finding nTwinID {} in aMapTwinId2VertRim".format(nTwinID))
                ###CHECK13:?: Why do softbody splits not have all mapping?  Because of material split?  (Can we survive this?  Do we need to not split morph body instead?)

        DataLayer_RemoveLayerInt(self.oBody.oMeshBody.GetName(), G.C_DataLayer_TwinID)          # Remove the data layer we used for separation so next softbody can work correctly.






    def DoDestroy(self):
        self.oMeshSoftBody.DoDestroy()
        self.oMeshSoftBodyRim.DoDestroy()
        self.oMeshPinnedParticles.DoDestroy()     
        if self.oMeshSoftBodyRimBackmesh is not None:
            self.oMeshSoftBodyRimBackmesh.DoDestroy() 




###OBS19: Really well done implementation of 'soft body skin' with a large scale effort from Blender and Unity to create a sophisticated 'soft body area' that is then glued to the skinned body
###OBS19: The problem encountered is that the simulated part of the body would move too much and would provide a sharp contrast versus the unmoving skinned body.
###OBS19: As a much more stable solution was found (re-boning the main skinned body around vagina and moving these new bones via Flex soft body shapes and particles this approach was shelved.
# class CSoftBodySkin_VertRimInfo():                  # Helper storage object to CSoftBodySkin.  Acts as central storage to store everything there is to know about a vert in the 'rim collider mesh'.  Has equivalent class in Unity by the same name
#     
#     C_HasShape                  = 1                 # This rim vert has a soft-body shape representing it (e.g. it and neighbor verts participate in making this area of the mesh feel like a 'thick skin' soft body.
#     C_HasParticle               = 2                 # This rim vert has a 'particle'. (e.g. it participates in the simulate of shapes in the area).  Every shape has a particle but not all of these particles drive a corresponding presentation vert (e.g. C_ParticleSetsPresentation flag)    
#     C_HasParticleSkinned        = 4                 # This rim vert has a 'skinned particle'.    This particle's position is set at every frame form a skinned position from our associated nVertRim (us) skinned mesh vert.  It is responsible for influencing its shape to move as close to possible to the skin surface.  Setting this particle's position forms the 'input stage' and is done first. 
#     C_ParticleSetsPresentation  = 8                 # This rim vert has its particle set its associated 'presentation vert'.  This particle's position is read at every frame and sets the position of our associated nVertSoftBody presentation just before presentation mesh rendering.  Reading this particle's position forms the 'output stage' and is done last.
#     C_HasBone                   = 16                # This rim vert is a bone.  It drives the position of a single bone which is in turn in charge of setting presentation verts around the 'hole' of this CSoftBodySkin implementation.
#     C_Serialization_EndOfRecord = 0xFFFF            # Magic number added at the end of each record in Serialize().  Used to trap serialization errors
#               
#     def __init__(self, nVertSrcBody, nVertRim, nVertSoftBody):
#         self.nVertSrcBody       = nVertSrcBody      # The vertex ID in the original untouched source body mesh. (The only 'authoritative' vert ID) 
#         self.nVertRim           = nVertRim          # The vertex ID in the rim collision mesh.
#         self.nVertSoftBody      = nVertSoftBody     # The vertex ID in the soft body presentation mesh.
#         self.aFlags             = 0                 # Collection of C_ flags above.  Helps Unity construct the softbody shape & bones as appropriate for each rim collider vert.
#         self.aNeighbors         = []                # Collection of rim vert IDs representing our the immediate rim vert neighbor to this rim vert.  (Used for Flex shape creation in Unity for soft skin effect)
#         
#     def AddNeighbor(self, nVertNeighbor):
#         self.aNeighbors.append(nVertNeighbor)
#         
#     def FlagAdd(self, nFlag):
#         if (nFlag & self.C_HasShape):               # Every shape has its own particle
#             nFlag = nFlag | self.C_HasParticle
#         self.aFlags = self.aFlags | nFlag 
#         
#     def FlagRemove(self, nFlag):
#         self.aFlags = self.aFlags & ~nFlag 
#     
#     def Serialize(self, oBA):                       # Serialize all our fields into a CByteArray() for Unity to de-serialize
#         #oBA.AddUShort(self.nVertSrcBody)
#         oBA.AddUShort(self.nVertRim)
#         oBA.AddUShort(self.nVertSoftBody)
#         oBA.AddUShort(self.aFlags)
#         oBA.AddUShort(len(self.aNeighbors))
#         for nNeighbor in self.aNeighbors:
#             oBA.AddUShort(nNeighbor)
#         oBA.AddUShort(self.C_Serialization_EndOfRecord)
#         
#     def __str__(self):
#         sFlags = "Flags="
#         if self.aFlags & self.C_HasShape:
#             sFlags = sFlags + "Shape "
#         if self.aFlags & self.C_HasParticle:
#             sFlags = sFlags + "Par "
#         if self.aFlags & self.C_HasParticleSkinned:
#             sFlags = sFlags + "Skin "
#         if self.aFlags & self.C_ParticleSetsPresentation:
#             sFlags = sFlags + "Pres "
#         if self.aFlags & self.C_HasBone:
#             sFlags = sFlags + "Bone "
#         return("VertRimInfo:  nVertSrcBody={:5d}  nVertRim={:4d}  nVertSoftBody={:4d}  Flags={:}  aNeighbors={:}".format(self.nVertSrcBody, self.nVertRim, self.nVertSoftBody, sFlags, self.aNeighbors))
#
#
# class CSoftBodySkin(CSoftBodyBase):         
#     # CSoftBodySkin: Specialized version of CSoftBodyBase that enables 'thick skin with holes' to be simulated in Unity.  (Used for vagina, anus, possibly mouth etc)
#     # This class is derived from CSoftBodyBase for its common elements with CSoftBody (both have a skinned rim and pinned Flex particles) (CSoftBody has its solid geometry created by Unity+Flex while CSoftBodySkin has its Flex geometry created here in Blender)
#     # The data flow that occurs at each frame is:
#     # 1. The Skinned mesh of this 'thick skin soft body' is 'baked' to extract the position of the skinned particles.
#     # 2. The Unity runtime code converts the VertID of each skinned vert to the SkinnedParticleID and updates its position through our self.aMapSkinnedVertToParticle collection
#     # 3. The Flex runtime adjusts the position of all its shapes to minimize distortions which in turns moves the 'SimulatedParticleID' particles we need to draw the presentation mesh.
#     # 4. The Unity runtime code converts the 'SimulatedParticleID' to the corresponding vert ID in the presentation mesh via our self.aMapParticleToVisibleMeshVert collection
#     # 5. The Unity runtime updates the verts in the presentation mesh and renders it to the player
#     
#     def __init__(self, oBody, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio, nHoleRadius):
#         super(self.__class__, self).__init__(oBody, sSoftBodyPart)      ###LEARN: How to call base class ctor.  Recommended over 'CSoftBodyBase.__init__(oBody, sSoftBodyPart)' (for what reason again??)
#         G.CGlobals.DEBUG = self             # import G;G.CGlobals.DEBUG.DEBUG_SelectVertsByFlag(1)
#         
#         self.aVertRimInfos = {}             # Our collection of information structures for each vert in the rim collsion mesh.  Shared with Unity (which has a similar class and associated functionality)
# 
# 
#         #===== A. FORM THE RIM COLLISION MESH BY REMOVING VERTS WHERE 'HOLE' SHOULD BE =====
#         #=== 1. Remove in our collision mesh (which right now still has geometry where hole should be) the geometry where the hole is. ===
#         bmSoftBodyRim = self.oMeshSoftBodyRim.Open() 
#         sNameVertGroupHole = "_CSoftBodySkin_Hole_" + self.sSoftBodyPart            # Mesh has to have this vert group defined for this soft skin part to function!
#         VertGrp_SelectVerts(self.oMeshSoftBodyRim.GetMesh(), sNameVertGroupHole)
#         bpy.ops.mesh.select_less()                                                  # Hole vert group is defined as having one vert ring too many so we can still flag edge-of-hole verts with it.  (That's the ring that forms bones for skinning hole verts)  Select less to select only the verts we need to delete
#         
#         #=== 2. Figure out the center of the hole from the average of the hole verts we're about to delete ===
#         vecCenter = Vector()
#         nVertsAtHole = 0
#         for oVert in bmSoftBodyRim.verts:
#             if oVert.select == True:
#                 vecCenter = vecCenter + oVert.co
#                 nVertsAtHole = nVertsAtHole + 1
#         vecCenter = vecCenter / nVertsAtHole
#         print("- CSoftBodySkin '{}' has hole center at {} with nHoleRadius = {}".format(self.sSoftBodyPart, vecCenter, nHoleRadius))
#         
#         #=== 3. Delete the hole verts as they no longer have purpose in Flex collisions as they are in a 'hole'.  They are neither skinned or simulated ===
#         bpy.ops.mesh.delete(type='VERT')
# 
# 
# 
#         #===== B. CREATE MAP BETWEEN COLLISION (RIM) AND PRESENTATION (SOFTBODY) MESHES =====
#         #===1. Iterate over all rim mesh verts to map the authoritative nVertSrcBody to the rim vert ID for map lookup in loop #3 below 
#         bmRim = self.oMeshSoftBodyRim.Open()
#         oLayVertSrcBody = bmRim.verts.layers.int[G.C_DataLayer_VertSrcBody]
#         aMapVertSrcBody2VertRim = {}
#         for oVert in bmRim.verts:
#             nVertSrcBody = oVert[oLayVertSrcBody]
#             aMapVertSrcBody2VertRim[nVertSrcBody] = oVert.index
#             #print("- VertSrcBody {:5d} = RimVert {:4d} at {:}".format(nVertSrcBody, oVert.index, oVert.co))
#         bmRim = self.oMeshSoftBodyRim.Close()
# 
#         #===1. Iterate over all softbody mesh verts to map the authoritative nVertSrcBody to the source vert ID for map lookup in loop #3 below 
#         bmSoftBody = self.oMeshSoftBody.Open()
#         oLayVertSrcBody = bmSoftBody.verts.layers.int[G.C_DataLayer_VertSrcBody]
#         aMapVertSrcBody2VertSoftBody = {}
#         for oVert in bmSoftBody.verts:
#             nVertSrcBody = oVert[oLayVertSrcBody]
#             aMapVertSrcBody2VertSoftBody[nVertSrcBody] = oVert.index
#             #print("- VertSrcBody {:5d} = SoftBodyVert {:4d} at {:}".format(nVertSrcBody, oVert.index, oVert.co))
#         bmSoftBody = self.oMeshSoftBody.Close()
# 
#         #===3. Bridge the two above-generated maps together to 'flatten' them into a map of SoftBody edge vert to rim edge vert ===
#         for nVertSrcBody in aMapVertSrcBody2VertSoftBody:
#             nVertSoftBody = aMapVertSrcBody2VertSoftBody[nVertSrcBody]
#             if nVertSrcBody in aMapVertSrcBody2VertRim:
#                 nVertRim = aMapVertSrcBody2VertRim[nVertSrcBody]
#                 self.aVertRimInfos[nVertRim] = CSoftBodySkin_VertRimInfo(nVertSrcBody, nVertRim, nVertSoftBody)
#                 #print("- VertSrcBody {:5d} = SoftBodyVert {:4d} = RimVert {:4d}".format(nVertSrcBody, nVertSoftBody, nVertRim))
#             #else:
#                 #print("- VertSrcBody {:5d} = SoftBodyVert {:4d} = RimVert NOT FOUND (probably removed hole vert)".format(nVertSrcBody, nVertSoftBody))
# 
# 
# 
#         #===== C. IDENTIFY RIM COLLSION VERT NEIGHBORS.  (USED TO FORM SOFT BODY FLEX SHAPES) =====
#         bmRim = self.oMeshSoftBodyRim.Open()
#         #bpy.ops.mesh.select_all(action='DESELECT')
#         for nVertRim in self.aVertRimInfos:
#             oVertRimInfo = self.aVertRimInfos[nVertRim]
#             oVertRim = bmRim.verts[oVertRimInfo.nVertRim]
#             #oVertRim.select_set(True)
# 
#             #=== Determine all the particles that will be included in this Flex softbody shape ===
#             aSetVertsAroundThisVert = set()
#             for oFaceNeighbors in oVertRim.link_faces:                              # Iterate over every face connected to the vert currently being processed...
#                 for oVertNeighbor in oFaceNeighbors.verts:                         #... then iterate through all verts connected to this face to...
#                     aSetVertsAroundThisVert.add(oVertNeighbor.index)      #... add that vert to the 'set of all verts connected to oVert' (including oVert)
#     
#             #=== Push in the list of particles connected to this shape in the flattened array Flex requires ===
#             aSetVertsAroundThisVert.remove(oVertRim.index)                 # Remove our vert so we're not our own neighbor!
#             for nVertNeighbor in aSetVertsAroundThisVert:
#                 if nVertNeighbor in self.aVertRimInfos:
#                     oVertRimInfo.AddNeighbor(nVertNeighbor)
#                     print("- Rim vert {:4d} gets new neighbor {:4d}".format(oVertRim.index, nVertNeighbor))
#                 #else:
#                     #print("- Rim vert {:4d} SKIPPED  neighbor {:4d}".format(oVertRim.index, nVertNeighbor))
# 
#         
#         
#         #===== SET COLLISION RIM VERT FLAGS (E.G. Shape, Skinned, Simulated, Bone) =====
#         #=== 1. Flag the rim collision verts that have shape = Every vert except the outermost rim (responsible for runtime normal adjustment and 'glueing' the presenation softbody mesh with the main skinned body) ===
#         VertGrp_SelectVerts(self.oMeshSoftBodyRim.GetMesh(), G.C_VertGrp_CSoftBody + self.sSoftBodyPart)     # Selecting the vert group for our softbody split will select every vert in the rim except the outermost ring
#         for oVertRim in bmRim.verts:
#             if oVertRim.select == True:
#                 oVertRimInfo = self.aVertRimInfos[oVertRim.index]
#                 oVertRimInfo.FlagAdd(oVertRimInfo.C_HasShape)
# 
#         #=== 2. Flag the rim collision 'skinned' particles = Responsible for moving each associated shape as close to skinned body as possible ===
#         VertGrp_SelectVerts(self.oMeshSoftBodyRim.GetMesh(), G.C_VertGrp_CSoftBody + self.sSoftBodyPart)     # Start with all the verts exception outermost ring.  From that we remove verts too close to hole
#         for oVertRim in bmRim.verts:
#             if oVertRim.select == True:
#                 vecVertLessCenter = oVertRim.co - vecCenter
#                 nDistAwayFromCenter = vecVertLessCenter.length
#                 if nDistAwayFromCenter > nHoleRadius:
#                     oVertRimInfo = self.aVertRimInfos[oVertRim.index]
#                     oVertRimInfo.FlagAdd(oVertRimInfo.C_HasParticleSkinned)
#                     #print("- Rim skinned Vert {:3d} at {:.3f} dist = {}".format(oVertRim.index, nDistAwayFromCenter, str(oVert.co)))
# 
#         #=== 3. Flag the rim collision 'presentation' particles = responsible for setting their corresponding vert in the user-visible presentation mesh ===
#         VertGrp_SelectVerts(self.oMeshSoftBodyRim.GetMesh(), G.C_VertGrp_CSoftBody + self.sSoftBodyPart)     # Selecting the vert group for our softbody split will select every vert in the rim except the outermost ring
#         bpy.ops.mesh.select_less()                  # Select one less ring than the shapes for the presentation particles
#         VertGrp_SelectVerts(self.oMeshSoftBodyRim.GetMesh(), sNameVertGroupHole, True)                    # Unselect the hole verts.  (These are skinned around bones we create so we don't drive these presentation verts directly from presentation particles!
#         for oVertRim in bmRim.verts:
#             if oVertRim.select == True:
#                 oVertRimInfo = self.aVertRimInfos[oVertRim.index]
#                 oVertRimInfo.FlagAdd(oVertRimInfo.C_ParticleSetsPresentation)
# 
#         #=== 4. Flag the bone rim collision verts.  These are responsible for 'skinning' the 'hole part of the mesh' ===
#         VertGrp_SelectVerts(self.oMeshSoftBodyRim.GetMesh(), sNameVertGroupHole)  # Re-select the hole verts (right next to an actual hole in the mesh!)  These are the 'bones' that will 'skin' the presentation hole verts
#         for oVertRim in bmRim.verts:
#             if oVertRim.select == True:
#                 oVertRimInfo = self.aVertRimInfos[oVertRim.index]
#                 oVertRimInfo.FlagAdd(oVertRimInfo.C_HasBone)
#         ###########################################DEV19: BUG!  Has some extra verts in there!!
# 
#         bmRim = self.oMeshSoftBodyRim.Close()
#         
#         if 0:
#             self.DEBUG_PrintInfo()
#         
# 
#     def SerializeVertRimInfos(self):                        # Serialize our aVertRimInfos into a CByteArray() for Unity to de-serialize
#         oBA = CByteArray()
#         oBA.AddUShort(len(self.aVertRimInfos))              # Send length of array first
#         for nVertRim in self.aVertRimInfos:
#             oVertRimInfo = self.aVertRimInfos[nVertRim]
#             oVertRimInfo.Serialize(oBA)
#         return oBA.Unity_GetBytes()
# 
# 
#     def DEBUG_PrintInfo(self):
#         #=== Print out all the information we have on each rim vert ===
#         print("\n=== COLLISION RIM VERTS INFO DUMP ===")    
#         for nVertRim in self.aVertRimInfos:
#             oVertRimInfo = self.aVertRimInfos[nVertRim]
#             print(oVertRimInfo)
#         print("=====================================\n")    
#         
#     def DEBUG_SelectVertsByFlag(self, nFlag):
#         print("\n=== COLLISION RIM VERTS INFO DUMP ===")    
#         print("\n-> DEBUG_SelectVertsByFlag() select verts of flag: " + str(nFlag))    
#         bmRim = self.oMeshSoftBodyRim.Open()
#         bpy.ops.mesh.select_all(action='DESELECT')              ###CHECK Open() above no longer deselecting?? 
#         for nVertRim in self.aVertRimInfos:
#             oVertRimInfo = self.aVertRimInfos[nVertRim]
#             if oVertRimInfo.aFlags & nFlag:
#                 bmRim.verts[nVertRim].select_set(True)
#                 print(oVertRimInfo)
#         bpy.ops.object.mode_set(mode='OBJECT')                  # Go to object and the edit mode so polygons are properly selected (select_set on verts doesn't work its way up to lines / polys)
#         bpy.ops.object.mode_set(mode='EDIT')
#         print("=====================================\n")    

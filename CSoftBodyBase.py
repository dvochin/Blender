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


class CSoftBodyBase():
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
        Util_SelectVertGroupVerts(self.oBody.oMeshBody.GetMesh(), G.C_VertGrp_Detach + self.sSoftBodyPart)

        #=== Find the edge verts of the softbody submesh so that we can determine the verts that will become edge verts between the two split meshes ===
        bpy.ops.mesh.region_to_loop()           # This will select only the edge verts at the boundary of the softbody vertex group selected above (find the edge verts)
        nNextTwinID = 1                         # We start the next rim vert ID to one (non rim-verts have a default value of zero)
        for oVert in bmBody.verts:              # Iterate over the verts at the edge at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut...
            if oVert.select:                    # ... this enables us to avoid inserting erroneous edge verts such as for vagina/anus opening)
                if oVert.is_manifold:           ###OPT!! Faster if we first create a list of BVerts using [] notation?  
                    oVert[oLayTwinID] = nNextTwinID
                    nNextTwinID += 1
    
        #=== Reselect the softbody faces so we can split below ===
        Util_SelectVertGroupVerts(self.oBody.oMeshBody.GetMesh(), G.C_VertGrp_Detach + self.sSoftBodyPart)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')           # We perform the split by faces so edge verts remain in both mesh

        #=== Split and separate the softbody mesh from the body mesh.  (Body gets that geometry removed and is what is rendered in game) ===
        bpy.ops.mesh.split()                    # 'Split' the selected faces.  Both 'sides' will now have 'rim verts' where the two submeshes meet
        bpy.ops.mesh.separate()                 # 'Separate' the selected polygon into its own mesh.  It will become our 'softbody mesh'
        self.oBody.oMeshBody.ExitFromEditMode()

        #=== Name the newly detached mesh as our 'softbody mesh' ===        ###IMPROVE: Find way to split easily and add to CMesh!
        bpy.context.object.select = False                                       ###LEARN: Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]      # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBody = CMesh(sNameSoftBody, bpy.context.scene.objects.active, None)     # Obtain CMesh reference to our softbody mesh. 
        bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from detached softbody to save Blender memory
        self.oMeshSoftBody.GetMesh().modifiers.clear()         # Remove the modifiers to save memory (e.g. armature) ###LEARN: How to remove all modifiers
        self.oBody.oMeshBody.Close()


        #===== SOFTBODY SKINNED RIM CREATION IN self.oMeshSoftBodyRim =====
        #=== Create the 'rim' skinned mesh that Unity will 'bake' at every frame so verts & normals are moved at every frame for a seamless connection to main skinned body=== 
        #=== Iterate through the verts of the main skinned mesh to select all the twin verts so we can create the rim mesh
        bmBody = self.oBody.oMeshBody.Open()
        oLayTwinID = bmBody.verts.layers.int[G.C_DataLayer_TwinID]
        for oVert in bmBody.verts:
            nTwinID = oVert[oLayTwinID]
            if (nTwinID != 0):              ###TODAY### Save verts in array to avoid re-iterations!!
                oVert.select_set(True)      # Select this edge boundary vertex for the upcoming code in which we expand the rim selection to create the rim submesh

        #=== Select the faces neighboring the twin verts and duplicate them into the new 'rim mesh'
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')  # With rim verts selected, switch to Face mode with expand to select all faces that use these verts... then switch to poly mode to have the smallest set of polygons that have an edge at the boundary are left selected.  These will form their own 'reduced skin mesh' that will be baked at every frame to calculate pin positions
        bpy.ops.mesh.duplicate()            # 'Duplicate' the rim faces so we get two copies...
        bpy.ops.mesh.separate()             # and 'Separate' the the above faces so they become the rim faces.
        bmBody.verts.layers.int.remove(oLayTwinID)  # Remove the temp data layer in the skin mesh as the just-separated mesh has the info now...
        self.oBody.oMeshBody.ExitFromEditMode()
            
        #=== Fetch the just-created 'rim' skinned mesh and set it to its proper name ===
        bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBodyRim = CMesh(sNameSoftBodyRim, bpy.context.scene.objects.active)   # Obtain CMesh reference to our rim mesh
        self.oMeshSoftBodyRim.SetParent(self.oMeshSoftBody.GetName())
        self.oMeshSoftBodyRim.GetMesh().modifiers.clear()          # Remove the modifiers to save memory
        self.oBody.oMeshBody.Close()
        
        #=== Cleanup the rim mesh by removing all materials and non-bones vertex groups ===
        Cleanup_RemoveMaterials(self.oMeshSoftBodyRim.GetMesh())
        Cleanup_VertGrp_RemoveNonBones(self.oMeshSoftBodyRim.GetMesh(), True)  # Remove the extra vertex groups (not skinning related)
        self.oMeshSoftBodyRim.Hide()


        #===== CREATE THE RIM VERT MAPPING in self.aMapRimVerts: Responsible to 'glue' the simulated edge verts to the main skinned body for 'seamless' appearance =====
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
                print("TwinID {:3d} = SoftBodyVert {:5d} = RimVert {:5d}".format(nTwinID, nVertTwinSoftBody, nVertTwinRim))
                self.aMapRimVerts.AddUShort(nVertTwinSoftBody)
                self.aMapRimVerts.AddUShort(nVertTwinRim)
            else:
                print("###EXCEPTION: CSoftBody.SeparateSoftBodyPart() finding nTwinID {} in aMapTwinId2VertRim".format(nTwinID))
                #raise Exception("###EXCEPTION: CSoftBody.SeparateSoftBodyPart() finding nTwinID {} in aMapTwinId2VertRim".format(nTwinID))
                ###NOW#13: Why do softbody splits not have all mapping?  Because of material split?  (Can we survive this?  Do we need to not split morph body instead?)


    def DoDestroy(self):
        self.oMeshSoftBody.DoDestroy()
        self.oMeshSoftBodyRim.DoDestroy()
        self.oMeshPinnedParticles.DoDestroy()     
        if self.oMeshSoftBodyRimBackmesh is not None:
            self.oMeshSoftBodyRimBackmesh.DoDestroy() 


#     def SerializeCollection_aMapRimVerts(self):               ###IMPROVE: Fanning out by function the best way?
#         return Stream_SerializeCollection(self.aMapRimVerts) 
# 
#     def SerializeCollection_aMapPinnedParticles(self):
#         return Stream_SerializeCollection(self.aMapPinnedParticles)

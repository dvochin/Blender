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
from CSoftBodyBase import *     ###INFO: Inheritance requires this method of importing a class from another file!





class CSoftBody(CSoftBodyBase):         
    # CSoftBody: Centrally-important class responsible for separating 'soft' body parts (e.g. breasts, penis, vagina, anus, etc) and performing the proper separation, modification and calculations for Flex-based simulation in Unity.
    
    def __init__(self, oBody, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio):
        super(self.__class__, self).__init__(oBody, sSoftBodyPart)      ###INFO: How to call base class ctor.  Recommended over 'CSoftBodyBase.__init__(oBody, sSoftBodyPart)' (for what reason again??)

        self.nSoftBodyFlexColliderShrinkRatio  = nSoftBodyFlexColliderShrinkRatio # The multiplier applied to the global G.nFlexParticleSpacing.  Used to 'shrink' the 'self.oMeshFlexCollider' mesh from the presentation mesh so that collisions appear to occur on the surface of the visible meshes.

        self.oMeshFlexCollider      = None              # The 'Flex collision' mesh is a 'slightly shrunken' version of 'self.oMeshSoftBody' in order so that Flex simulates a smaller mesh so that the appearance mesh appears to collide at the presentation depth (even though this is impossibly to do by Flex)    
        self.oMeshUnity2Blender     = None              # The 'Unity-to-Blender' mesh created by CreateUnity2BlenderMesh().  Used by Unity to pass in geometry for Blender processing (e.g. Softbody particle skinning and pinning)   

        #===== SOFTBODY CAPPING: Turns the separated softbody mesh from a 2D mesh to a solid =====
        #=== Select the edge of the softbody mesh, extrude to create new geometry and collapse these new verts at the center.  This will turn the presentation mesh into the solid mesh needed by Flex ===
        self.oMeshSoftBody.Open()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')  ###BUG?? ###CHECK: Possible that edge collapse could fail depending on View3D mode...
        bpy.ops.mesh.select_non_manifold()          # Select the edge of the mesh... ###INFO: Will select the edge of the detached softbody mesh = what we have to collapse to make a solid for Flex
        bpy.ops.mesh.extrude_edges_indiv()          #... and extrude them to create new verts... ###INFO: This is the function we need to really extrude!
        bpy.ops.mesh.edge_collapse()                #... and collapse them to a single point to 'close' the mesh. ###INFO: The collapse will combine all selected verts into one vert at the center
        #bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from detached softbody to save Blender memory
        ###DEV19
        
        
        





        #=== Create the 'backmesh' mesh from the cap.  This mesh is used to find Flex particles that should be pinned to the body instead of simulated ===
        bpy.ops.mesh.select_more()                  # Add the verts immediate to the just-created center vert (the rim verts)  We now have the entire cap faces.
        bpy.ops.mesh.duplicate()                    # Duplicate the 'backmesh' faces so we can process them further and separate them into the backmesh CMesh object
        bpy.ops.mesh.subdivide(number_cuts=4)       # Subdivide backfaces to provided additional verts in the back faces.  (Needed so we can find particles near the backfaces as neighboring search is vert-based)
        bpy.ops.mesh.remove_doubles(threshold=0.02) # Remove verts that are too close together (to speed up particle search)
        bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.  This will become our 'backmesh' mesh use to find pinned particles
        self.oMeshSoftBody.ExitFromEditMode()
        bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')
        self.oMeshSoftBodyRimBackmesh = CMesh(self.oMeshSoftBody.GetName() + G.C_NameSuffix_RimBackmesh, bpy.context.scene.objects.active, None)  # Obtain reference to the backmesh mesh
        self.oMeshSoftBodyRimBackmesh.SetParent(self.oMeshSoftBody.GetName())
        DataLayer_RemoveLayers(self.oMeshSoftBodyRimBackmesh.GetName())
        self.oMeshSoftBodyRimBackmesh.Hide()
        self.oMeshSoftBody.Close()


        #===== FLEX COLLISION MESH CREATION =====
        #=== Create the 'collision mesh' as a 'shrunken version' of appearance mesh (about vert normals) ===
        self.oMeshFlexCollider = CMesh.CreateFromDuplicate(self.oMeshSoftBody.GetMesh().name + G.C_NameSuffix_FlexCollider, self.oMeshSoftBody)
        self.oMeshFlexCollider.SetParent(self.oMeshSoftBody.GetName())
        self.oMeshFlexCollider.Open()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.shrink_fatten(value=self.nSoftBodyFlexColliderShrinkRatio * G.CGlobals.cm_nFlexParticleSpacing)      # Shrink presentation mesh by the particle distance multiplied by the shrink ratio provided for this softbody
        self.oMeshFlexCollider.Close()


    
    def DoDestroy(self):
        super(self.__class__, self).DoDestroy()         ###INFO: How to call base class method
        self.oMeshFlexCollider.DoDestroy()
        self.oMeshUnity2Blender.DoDestroy()   
  
  
  
    def FindPinnedFlexParticles(self, nDistSoftBodyParticlesFromBackmesh):        
        # FindPinnedFlexParticles: Process the Flex-created particles and create softbody rim mesh.  Updates our rim mesh currently containing only rim (for normals).  This mesh will be responsible to 'pin' some softbody particles to the skinned body so softbody doesn't 'fly out'
        # Note: Unity must have created the self.oMeshUnity2Blender mesh before calling this (pushing its Flex-generated verts)
        print("-- CSoftBody.FindPinnedFlexParticles() on body '{}' and softbody '{}' with distance {} --".format(self.oBody.oBodyBase.sMeshPrefix, self.sSoftBodyPart, nDistSoftBodyParticlesFromBackmesh))

        #=== Open the temp mesh Unity requested in CreateTempMesh() and push in a data layer with vert index.  This will prevent us from losing access to Unity's particles as we process this mesh toward the softbody rim ===        
        oMeshUnity2BlenderTEMPCOPY = CMesh.CreateFromDuplicate("TEMPFORJOIN-Unity2Blender", self.oMeshUnity2Blender)        # Create a temporary copy of Unity2Blender mesh because we need to destroy our copy and Unity owns its copy and must release it on its own
        bmUnity2Blender = oMeshUnity2BlenderTEMPCOPY.Open()
        oLayParticles = bmUnity2Blender.verts.layers.int.new(G.C_DataLayer_Particles)
        for oVert in bmUnity2Blender.verts:                             # Iterate through Unity's particles so we can map between pinned particles mesh and all the Flex particles at gametime    
            oVert[oLayParticles] = oVert.index + G.C_OffsetVertIDs      # Apply offset to easily tell real IDs in later loop
        oMeshUnity2BlenderTEMPCOPY.Close()
        
        #===== Remove the particles that are too far from the backmesh =====
        #=== Combine the Flex-constructed particle verts with the backmesh mesh of our softbody.  We need to isolate the particles close to the backmesh of the softbody particles to 'pin' them ===
        self.oMeshPinnedParticles = CMesh.CreateFromDuplicate(self.oMeshSoftBody.GetName() + "-PinnedParticles", self.oMeshSoftBodyRimBackmesh)
        self.oMeshPinnedParticles.SetParent(self.oMeshSoftBody.GetName())
         
        SelectObject(oMeshUnity2BlenderTEMPCOPY.GetName())       # First select and activate mesh that will be destroyed (temp mesh)    (Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh))
        self.oMeshPinnedParticles.GetMesh().hide = False
        self.oMeshPinnedParticles.GetMesh().select = True                         # Now select...
        bpy.context.scene.objects.active = self.oMeshPinnedParticles.GetMesh()    #... and activate mesh that will be kept (merged into)  (Note that to-be-destroyed mesh still selected!)
        bpy.ops.object.join()                                           #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###INFO: Existing custom data layer in merged mesh destroyed!!
        oMeshUnity2BlenderTEMPCOPY = None                               # Above join destroyed the copy mesh so set our variable to None
        #=== Select the rim verts in the joined mesh ===
        bmPinnedParticles = self.oMeshPinnedParticles.Open()
        bpy.ops.mesh.select_loose()                             # Select the loose geometry...  (This will only select Unity's particle)
        bpy.ops.mesh.select_all(action='INVERT')                #... and invert it (leaving only the backmesh selected (for upcoming nearby selection)
        #=== Move the rim verts with the close particles some distance so we can quickly separate the particles close to rim verts ===        
        C_TempMove = 5                                         ###IMPROVE: Possible to do this with the 'transfer mesh' modifier?  Ask forum question!
        bpy.ops.transform.transform(mode='TRANSLATION', value=(0, C_TempMove, 0, 0), proportional='ENABLED', proportional_size=nDistSoftBodyParticlesFromBackmesh, proportional_edit_falloff='CONSTANT')  # Move the rim verts with propportional editing so the particles near rim are moved too.  This is how we separate them
        #=== Delete all particles that are too far from rim ===
        bpy.ops.mesh.select_all(action='DESELECT')
        for oVert in bmPinnedParticles.verts:       # Select all body verts that remained close to where they were before progressive move (Separated by translation operation above)                                  
            if oVert.co.y < (C_TempMove / 2):       # Verts that didn't make it halfway were not close enough and are no longer needed
                oVert.select_set(True)
        bpy.ops.mesh.delete(type='VERT')    # Delete all particles that were too far from backmesh.  (These will be softbody-simulated and the others pinned)
        if len(bmPinnedParticles.verts) == 0:
            raise Exception("###EXCEPTION in CSoftBody.FindPinnedFlexParticles()  Cannot find pinned particles for softbody " + self.sSoftBodyPart)
        
        #=== Move back the remaining rim and 'close particles to their original position.  At this point only particles near rim remain ===
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.transform(mode='TRANSLATION', value=(0, -C_TempMove, 0, 0))  # Move the clothing verts with proportional enabled with a constant curve.  This will also move the body verts near any clothing ###TUNE
        bpy.ops.mesh.select_all(action='DESELECT')
        #=== Delete the verts of the backmesh... to leave only the 'close particles to the backmesh' that need to be pinned instead of simulated ===
        bpy.ops.mesh.select_loose()                             # Select the loose geometry...  (This will only select Unity's particle)
        bpy.ops.mesh.select_all(action='INVERT')                #... and invert it (leaving only the backmesh selected (for upcoming nearby selection)
        bpy.ops.mesh.delete(type='VERT')
 

        #===== CREATE THE MAP OF PINNED FLEX PARTICLES: Responsible to move simulated Flex particles to the position of their corresponding skinned vert  =====
        #=== Iterate through particles to fill in its map traversal ===
        oLayParticles = bmPinnedParticles.verts.layers.int[G.C_DataLayer_Particles]
        self.aMapPinnedParticles = CByteArray()  # Blank out the two arrays that must be created everytime this is called
        self.oMeshPinnedParticles.UpdateBMeshTables()
        for oVert in bmPinnedParticles.verts:                               ###IMPROVE: Code that generates 'aMapPinnedParticles' is duplicate between soft body and cloth... can be merged together?? 
            nOrigFlexParticleID = oVert[oLayParticles]
            if (nOrigFlexParticleID >= G.C_OffsetVertIDs):            # The real particles are over this offset (as created above)
                nOrigFlexParticleID -= G.C_OffsetVertIDs              # Retrieve the non-offsetted particle
                self.aMapPinnedParticles.AddUShort(oVert.index)
                self.aMapPinnedParticles.AddUShort(nOrigFlexParticleID)
                #print("PinParticle {:4d} = Flex Particle {:4d}". format(oVert.index, nOrigFlexParticleID))
        self.oMeshPinnedParticles.Close()

        #=== Skin the pinned particle mesh from original rim mesh.  (So particles are skinned too)
        Util_TransferWeights(self.oMeshPinnedParticles.GetMesh(), self.oBody.oBodyBase.oMeshMorphResult.GetMesh())   ###CHECK: Proper source mesh? ###OPT?
        VertGrp_RemoveNonBones(self.oMeshPinnedParticles.GetMesh(), True)

        return "OK"


    def CreateMesh_Unity2Blender(self, nVerts):       ###MOVE: Not really related to CBody but is global
        "Create a temporary Unity2Blender with 'nVerts' vertices.  Used by Unity to pass Blender temporary mesh geometry for Blender processing (e.g. Softbody tetramesh pinning)"
        sNameMeshUnity2Blender = self.oMeshSoftBody.GetName() + G.C_NameSuffix_Unity2Blender
        if (self.oMeshUnity2Blender != None):
            self.oMeshUnity2Blender.DoDestroy()
            self.oMeshUnity2Blender = None
        oMeshD = bpy.data.meshes.new(sNameMeshUnity2Blender)
        oMeshO = bpy.data.objects.new(oMeshD.name, oMeshD)
        print("== CreateMesh_Unity2Blender() for mesh '{}' and verts {} ==".format(sNameMeshUnity2Blender, nVerts))
        #oMeshO.rotation_euler.x = radians(90)            # Old rotation needed before Vic7
        bpy.context.scene.objects.link(oMeshO)
        aVerts = []
        for nVert in range(nVerts):
            aVerts.append((0,0,0))
        oMeshD.from_pydata(aVerts,[],[])
        oMeshD.update()
        SetParent(oMeshO.name, G.C_NodeFolder_Game)
        self.oMeshUnity2Blender = CMesh.Create(oMeshO.name)     # Store CMesh reference into the member dedicated for this purpose so Unity can access and upload to us via its normal (efficient) channel
        self.oMeshUnity2Blender.SetName(sNameMeshUnity2Blender)     # Ensure we have the name we need. 
        self.oMeshUnity2Blender.SetParent(self.oMeshSoftBody.GetName())
        self.oMeshUnity2Blender.bDeleteBlenderObjectUponDestroy = True
        self.oMeshUnity2Blender.Hide()
        return "OK"         # Return OK to Unity
    
    






    
    
    
    
    
    
    
#     def Morph_UpdateDependentMeshes(self):      ###OBS?
#         "Updates this softbody mesh from its source morph body"
#         #=== Iterate through this softbody mesh and update our vert position to our corresponding morph source body ===
#         bmSoftBody = self.oMeshSoftBody.Open()
#         oLayVertAssy = bmSoftBody.verts.layers.int[G.C_DataLayer_VertsAssy]
#         aVertsMorph = self.oBody.oMeshMorph.GetMeshData().vertices
#         for oVert in bmSoftBody.verts:
#             if (oVert[oLayVertAssy] >= G.C_OffsetVertIDs):
#                 nVertMorph = oVert[oLayVertAssy] - G.C_OffsetVertIDs        # Obtain the vertID from the assembled mesh (removing offset added during creation)
#                 oVert.co = aVertsMorph[nVertMorph].co.copy()
#         self.oMeshSoftBody.Close()





#     def SerializeCollection_aMapRimVerts2SourceVerts(self):
#         return Stream_SerializeCollection(self.aMapRimVerts2SourceVerts)





#     def FindPinnedFlexParticles(self, nNumVerts_UnityToBlenderMesh, nDistParticlesFromBackmesh):
#         "Process the Flex-created particles and create softbody rim mesh.  Updates our rim mesh currently containing only rim (for normals).  This mesh will be responsible to 'pin' some softbody particles to the skinned body so softbody doesn't 'fly out'"
#         print("-- CSoftBody.FindPinnedFlexParticles() on body '{}' and softbody '{}' with tetra distance {} --".format(self.oBody.oBodyBase.sMeshPrefix, self.sSoftBodyPart, nDistParticlesFromBackmesh))
# 
#         #=== Create a temporary copy of rim mesh so we can transfer weights efficiently from it to new mesh including particles ===
#         ####BUG? DoDestroy mesh of rim??
#         self.oMeshSoftBodyRim = CMesh.CreateFromDuplicate("TEMP_SoftBodyRim", self.oMeshSoftBodyRim_Orig)
#         oMeshSoftBodyRim_Copy = CMesh.CreateFromDuplicate("TEMP_SoftBodyRim_Copy", self.oMeshSoftBodyRim_Orig)
# 
#         #=== Create a temporary copy of Unity2Blender mesh so we can trim it to 'nNumVerts_UnityToBlenderMesh' verts ===  
#         self.oMeshUnity2Blender = CMesh.CreateFromDuplicate("TEMP_Unity2Blender", self.oMeshUnity2Blender)
#         self.aMapPinnedParticles = array.array('H')  # Blank out the two arrays that must be created everytime this is called
#         self.aMapRimVerts         = array.array('H')
# 
#         #=== Open the temp mesh Unity requested in CreateTempMesh() and push in a data layer with vert index.  This will prevent us from losing access to Unity's particles as we process this mesh toward the softbody rim ===        
#         bm = self.oMeshUnity2Blender.Open()
#         for oVert in bm.verts:
#             if (oVert.index >= nNumVerts_UnityToBlenderMesh):
#                 oVert.select_set(True)
#         bpy.ops.mesh.delete(type='VERT')        # Delete all verts from Unity2Blender mesh that are 'extra' (That is only created once with the max # of verts we can ever expect)
#         nVertsRimOrig = len(self.oMeshSoftBodyRim.oMesh.data.vertices)     # Remember how many verts rim had before join (so we can resync below) 
#         print("- CSoftBody.FindPinnedFlexParticles() shifts joined rim verts by {} from inserting Unity particles.".format(nNumVerts_UnityToBlenderMesh))
#  
#         #=== Create the custom data layer and store vert indices into it === 
#         oLayParticles = bm.verts.layers.int.new(G.C_DataLayer_Particles)
#         for oVert in bm.verts:
#             oVert[oLayParticles] = oVert.index + G.C_OffsetVertIDs    # Apply offset to easily tell real IDs in later loop
#         self.oMeshUnity2Blender.Close()
#         
#         #===== Combine the particle-mesh with the rim mesh of that softbody.  We need to isolate the particles close to the rim verts to 'pin' them =====
#         ###INFO: Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh)
#         SelectObject(self.oMeshUnity2Blender.GetName())             # First select and activate mesh that will be destroyed (temp mesh)
#         self.oMeshSoftBodyRim.oMesh.select = True                         # Now select...
#         bpy.context.scene.objects.active = self.oMeshSoftBodyRim.oMesh    #... and activate mesh that will be kepp (merged into)  (Note that to-be-destroyed mesh still selected!)
#         bpy.ops.object.join()                                       #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###INFO: Existing custom data layer in merged mesh destroyed!!
#         self.oMeshUnity2Blender = None                              # Above join destroyed the copy mesh so set our variable to None
# 
#         #===== Remove the particles that are too far from the rim =====
#         #=== Select the rim verts in the joined mesh ===
#         bmRim = self.oMeshSoftBodyRim.Open()
#         oLayParticles = bmRim.verts.layers.int[G.C_DataLayer_Particles]
#         for oVert in bmRim.verts:
#             if (oVert.index > nNumVerts_UnityToBlenderMesh):
#                 oVert.select_set(True)                      # Select only the verts with no OrigVertID = particles
#         #=== Move the rim verts with the close particles some distance so we can quickly separate the particles close to rim verts ===        
#         C_TempMove = 10
#         bpy.ops.transform.transform(mode='TRANSLATION', value=(0, C_TempMove, 0, 0), proportional='ENABLED', proportional_size=nDistParticlesFromBackmesh, proportional_edit_falloff='CONSTANT')  # Move the rim verts with propportional editing so the particles near rim are moved too.  This is how we separate them
#         #=== Delete all particles that are too far from rim ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         for oVert in bmRim.verts:  # Select all body verts far from clothing (Separated by translation operation above)                                  
#             if oVert.co.z > -C_TempMove / 2:
#                 oVert.select_set(True)
#         bpy.ops.mesh.delete(type='VERT')  # Delete all particles that were too far from rim.  (These will be softbody-simulated and the others pinned)
#         #=== Move back the remaining rim and 'close particles to their original position.  At this point only particles near rim remain ===
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.transform.transform(mode='TRANSLATION', value=(0, -C_TempMove, 0, 0))  # Move the clothing verts with proportional enabled with a constant curve.  This will also move the body verts near any clothing ###TUNE
#         bpy.ops.object.mode_set(mode='OBJECT')    
#         #=== Skin the rim+particles mesh from original rim mesh.  (So particles are skinned too!)
#         Util_TransferWeights(self.oMeshSoftBodyRim.oMesh, oMeshSoftBodyRim_Copy.oMesh)      #bpy.ops.object.vertex_group_transfer_weight()
#         VertGrp_RemoveNonBones(self.oMeshSoftBodyRim.oMesh, True)        
#         nVertsRimJoined = len(self.oMeshSoftBodyRim.oMesh.data.vertices)     # Remember how many verts rim now has once close particles are kept in
#         nShiftAppliedToOrigRimVerts = nVertsRimJoined - nVertsRimOrig   # Calculate the shift applied to orig verts  
#         self.oMeshSoftBodyRim.Close()
# 
#         #===== CREATE THE MAP PIN TETRAVERTS TO TETRAVERT MAP =====
#         bmRim = self.oMeshSoftBodyRim.Open()
#         oLayParticles = bmRim.verts.layers.int[G.C_DataLayer_Particles]
# 
#         #=== Iterate through particles to fill in its map traversal ===
#         for oVert in bmRim.verts:                                                                        
#             nParticleID = oVert[oLayParticles]
#             if (nParticleID >= G.C_OffsetVertIDs):            # The real particles are over this offset (as created above)
#                 nParticleID -= G.C_OffsetVertIDs              # Retrieve the non-offsetted particle
#                 self.aMapPinnedParticles.append(oVert.index)
#                 self.aMapPinnedParticles.append(nParticleID)
#                 #print("RimParticle {:4d} = Particle {:4d}". format(oVert.index, nParticleID))
#         self.oMeshSoftBodyRim.Close()
# 
# 
#         #===== CREATE THE TWIN VERT MAPPING =====
#         #===1. Iterate over the rim copy vertices, and find the rim vert for every 'twin verts' so next loop can map softbody part verts to rim verts for pinning === 
#         bmRimCopy = oMeshSoftBodyRim_Copy.Open()
#         oLayRimVerts = bmRimCopy.verts.layers.int[G.C_DataLayer_TwinID]
#         aMapTwinId2VertRim = {}
#         for oVert in bmRimCopy.verts:
#             nTwinID = oVert[oLayRimVerts]
#             if nTwinID != 0:
#                 aMapTwinId2VertRim[nTwinID] = oVert.index + nShiftAppliedToOrigRimVerts ###NOTE: Apply shift forced upon rim verts from join with tetra verts above
#                 #print("TwinID {:3d} = RimVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
#         oMeshSoftBodyRim_Copy.Close()
#         oMeshSoftBodyRim_Copy = None
# 
#         #===2. Iterate through the verts of the newly separated softbody to access the freshly-created custom data layer to obtain ID information that enables us to match the softbody mesh vertices to the main skinned mesh for pinning ===
#         bmSoftBody = self.oMeshSoftBody.Open()
#         oLayRimVerts = bmSoftBody.verts.layers.int[G.C_DataLayer_TwinID]
#         aMapTwinId2VertSoftBody = {}
#         for oVert in bmSoftBody.verts:  ###INFO: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
#             nTwinID = oVert[oLayRimVerts]
#             if nTwinID != 0:
#                 aMapTwinId2VertSoftBody[nTwinID] = oVert.index
#                 #print("TwinID {:3d} = SoftBodyVert {:5d} mat {:} at {:}".format(nTwinID, oVert.index, oVert.link_faces[0].material_index, oVert.co))
#         self.oMeshSoftBody.Close()
# 
#         #===3. With both maps created, bridge them together to a flattened map from softbody mesh to its rim vert ===
#         for nTwinID in aMapTwinId2VertSoftBody:
#             nVertTwinSoftBody = aMapTwinId2VertSoftBody[nTwinID]
#             if nTwinID in aMapTwinId2VertRim:
#                 nVertTwinRim = aMapTwinId2VertRim[nTwinID]
#                 self.aMapRimVerts.append(nVertTwinSoftBody)
#                 self.aMapRimVerts.append(nVertTwinRim)                ####BUG ####DEV: Can fail here... trap to earlier and catch!
#                 #print("TwinID {:3d} = SoftBodyVert {:5d} = RimVert {:5d}".format(nTwinID, nVertTwinSoftBody, nVertTwinRim))
#             else:
#                 G.DumpStr("###ERROR in CSoftBody.SeparateSoftBodyPart() finding nTwinID {} in aMapTwinId2VertRim".format(nTwinID)) 
# 
#         return "OK"     ###TEMP



# #---------------------------------------------------------------------------    CSoftBodyBreast
# 
# class CSoftBodyBreast(CSoftBody):                       # Subclass of CSoftBody to handle special-case breast colliders (to repel cloth)
#         # Highly-specific functionality to breasts because of their need for special-case breast colliders moving with softbody breasts to repel cloth.
# 
#     def __init__(self, oBody, sSoftBodyPart):
#         super(self.__class__, self).__init__(oBody, sSoftBodyPart)      ###INFO: How to call base class ctor
# 
#         self.sNameCollider = sSoftBodyPart + "Col"      # Collider associated with this breast has this simple suffix added
#         self.oMeshColBreast = None                      # The collider mesh for this breast.  Pushes cloth back in Unity runtime
#         self.aMapVertsBodyMorphToBreast = {}            # Map of which 'morph body' vert maps to what breast mesh verts.  Used to traverse verts for breast collider                  
#         self.aColBreastVertSphereRadiusRatio     = array.array('H')      # This array (highly specific to CBreastCol) stores a number from 0-255 to scale the sphere radius (kept in Unity only) used by this collider mesh.  (0 means no sphere created for that vertex)  A maximum of 32 (for both breasts) spheres can be defined
#         self.aColBreastCapsuleSpheres            = array.array('H')      # This array (highly specific to CBreastCol) stores the two vertex IDs of each vertex / sphere that represends the end of each tapered capsule.  These are marked by 'sharp edges' for each capsule
#         self.aColBreastMapSlaveMeshSlaveToMaster = array.array('H')      # This outgoing array stores the map of source vert to destination vert.  Used by Unity to set the slave mesh to the vert position of its master mesh
#         
#         # This Flex mesh takes a small encoded (containing about 32 verts) mesh to generate sphere & capsule collidersX.  This call process which vert will create a sphere collider in PhysX and which edge will generate a capsule colliders (currently used to repell clothing away from breasts)  (Args ex: "BodyA", "WomanA", "Breasts")        ###CHECK: Can capping during breast separation cause problem with collider overlay??
#         sNameSlaveMeshSlave = self.oBody.sMeshSource + "-" + self.sNameCollider + "-Slave"      ###IMPROVE: Create function to construct these names!
#         self.oMeshColBreast = CMesh.Create(sNameSlaveMeshSlave)    
#         
#         #=== Iterate through the verts to assemble the aColBreastVertSphereRadiusRatio array storing the red channel of the vertex color.  (This information stores the relative radius of each vertex sphere with a value of zero meaning no sphere) ===
#         bmBreastCol = self.oMeshColBreast.Open()
#         oLayVertColors = bmBreastCol.loops.layers.color.active        # Obtain reference to bmesh vertex color channel store in loops  ###INFO: 2 defined 'Col' and 'Col.001' with 'Col.001' active and appearing to contain valid data... can this change?? ###CHECK
#         nNumActiveVerts = 0
#         for oVert in bmBreastCol.verts:
#             nVertSphereRadiusRatio = oVert.link_loops[0][oLayVertColors][0]     ###INFO: How to access vert colors
#             if nVertSphereRadiusRatio > 0.1:                         ###KEEP? Setting zero color can be tricky so some threshold??
#                 #print("CBodyColBreast: SphereIndex # {:2} = Vert {:2} = Val: {:2}".format(nNumActiveVerts, oVert.index, nVertSphereRadiusRatio))
#                 nNumActiveVerts += 1
#             else:
#                 nVertSphereRadiusRatio = 0                              # Non collider-related verts get zero strength so they don't generate a sphere collider
#             self.aColBreastVertSphereRadiusRatio.append((int)(255 * nVertSphereRadiusRatio))       # The red vertex color channel (a float for 0 to 1) is multiplied by 255 and sent as a short
#         if nNumActiveVerts != 16:        # Both breasts are limited to 32 so 16 per breast
#             raise Exception("###EXCEPTION: CBodyColBreast_FormColliders() did not find 16 active verts while scanning vertex colors on source breast collider mesh.")
#         
#         nNumCapsules = 0
#         for oEdge in bmBreastCol.edges:
#             if (oEdge.smooth == False):
#                 self.aColBreastCapsuleSpheres.append(oEdge.verts[0].index) 
#                 self.aColBreastCapsuleSpheres.append(oEdge.verts[1].index)
#                 #print("CBodyColBreast: Capsule {:2} found between {:2}-{:2}".format(nNumCapsules, oEdge.verts[0].index, oEdge.verts[1].index))
#                 nNumCapsules += 1
#         if nNumCapsules != 16:           # Both breasts are limited to 32 so 16 per breast
#             raise Exception("###EXCEPTION: CBodyColBreast_FormColliders() didn't find 16 capsules while scanning for sharp edges on source breast collider mesh.")
#         self.oMeshColBreast.Close()
# 
# 
#         #=== Construct our forward map 'self.aMapVertsBodyMorphToBreast' between body morph verts to this softbody.  Needed for collider vert traversal below ===
#         bmSoftBody = self.oMeshSoftBody.Open()
#         oLayVertAssy = bmSoftBody.verts.layers.int[G.C_DataLayer_VertsAssy]
#         for oVert in bmSoftBody.verts:
#             if (oVert[oLayVertAssy] >= G.C_OffsetVertIDs):
#                 nVertMorph = oVert[oLayVertAssy] - G.C_OffsetVertIDs        # Obtain the vertID from the assembled mesh (removing offset added during creation)  ###IMPROVE? Morph instead of Assy name?
#                 self.aMapVertsBodyMorphToBreast[nVertMorph] = oVert.index   # Store our forward map between morph body to breast (for breast collider traveral)
#                 #print(nVertMorph, oVert.index)
#         self.oMeshSoftBody.Close()
#       
#         #=== Iterate through the collider mesh to construct map Unity needs (from info previously calculated in SlaveMesh_DefineMasterSlaveRelationship()) ===
#         bmBreastCol = self.oMeshColBreast.Open()
#         oLaySlaveMeshVerts = bmBreastCol.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
#         for oVert in bmBreastCol.verts:
#             nVertBreastCol = oVert.index                        # The breast collider vert is in a master/slave relationship created at design time with the untouched source body...
#             nVertSource = oVert[oLaySlaveMeshVerts]             #... we obtain the source vert from our breast collider master / slave relationship but...
#             nVertMorph = oBody.aMapVertsSrcToMorph[nVertSource] #... source body has been assembled into morph body so we need to traverse into that but...
#             nVertBreast = self.aMapVertsBodyMorphToBreast[nVertMorph]   #... we need the breast vert so traverse into that!! 
#             self.aColBreastMapSlaveMeshSlaveToMaster.append(nVertBreastCol)
#             self.aColBreastMapSlaveMeshSlaveToMaster.append(nVertBreast)
#             #print(nVertBreastCol, nVertSource, nVertMorph, nVertBreast)
#         self.oMeshColBreast.Close()
#         # Return: The arrays are now defined in this CBody instance (ready for typical pickup via normal array serialization)
# 
# 
#     def Morph_UpdateDependentMeshes(self):
#         CSoftBody.Morph_UpdateDependentMeshes(self)                 # Call base class for usual SoftBody apply.  ###INFO: How to call base class
#         self.oBody.SlaveMesh_ResyncWithMasterMesh(self.sNameCollider)              # Re-sync our collider (which is a slave mesh) back to its master mesh
# 
# 
# 
#     def SerializeCollection_aColBreastVertSphereRadiusRatio(self):
#         return Stream_SerializeCollection(self.aColBreastVertSphereRadiusRatio)
# 
#     def SerializeCollection_aColBreastCapsuleSpheres(self):
#         return Stream_SerializeCollection(self.aColBreastCapsuleSpheres)
# 
#     def SerializeCollection_aColBreastMapSlaveMeshSlaveToMaster(self):
#         return Stream_SerializeCollection(self.aColBreastMapSlaveMeshSlaveToMaster)




#         #=== Vagina has special processing as the complex 3D shape is created in Blender and not on-the-fly from this script ===
#         if (self.bIsVagina == False):
#             #=== Before the collapse to cap the softbody we must remove the info in the custom data layer so new collapse vert doesn't corrupt our rim data ===
#             bpy.ops.mesh.extrude_edges_indiv()          ###INFO: This is the function we need to really extrude!
#             for oVert in bmSoftBody.verts:              # Iterate through all selected verts and clear their 'twin id' field.
#                 if oVert.select == True:
#                     oVert[oLayRimVerts] = 0           ###IMPROVE? Give cap extra geometry for a smooth that will be a better fit than a single center vert??
#             bpy.ops.mesh.edge_collapse()                ###INFO: The collapse will combine all selected verts into one vert at the center
# 
#             #=== Create the 'backmesh' mesh from the cap.  This mesh is used to find Flex particles that should be pinned to the body instead of simulated ===
#             bpy.ops.mesh.select_more()                  # Add the verts immediate to the just-created center vert (the rim verts)
#             bpy.ops.mesh.duplicate()                    # Duplicate the 'backmesh' so we can process it further
#             bpy.ops.mesh.subdivide(number_cuts=4)       # Subdivide it to provided geometry inside the hole.  (Needed so we can find particles inside the center of the hole and not just extremities)
#             bpy.ops.mesh.remove_doubles(threshold=0.02) # Remove verts that are too close together (to speed up particle search)
# 
#         else:
#             bpy.ops.mesh.select_all(action='DESELECT')
#             nVertGrpIndex_DetachPart = self.oMeshSoftBody.GetMesh().vertex_groups.find(G.C_VertGrp_CSoftBody + "Vagina_Backmesh")      ###BUG!!!! _ versus -!!!!!!
#             oVertGroup_DetachPart = self.oMeshSoftBody.GetMesh().vertex_groups[nVertGrpIndex_DetachPart]
#             self.oMeshSoftBody.GetMesh().vertex_groups.active_index = oVertGroup_DetachPart.index
#             bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
# 
#         #=== Finish creating the backmesh from vagina or no-vagina submesh selected above ===
#         bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.  This will become our 'backmesh' mesh use to find pinned particles
#         bpy.ops.object.mode_set(mode='OBJECT')      # Manually going to object to handle tricky split below...
#         bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#         bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
#         self.oMeshSoftBodyRimBackmesh = CMesh(sNameSoftBody + G.C_NameSuffix_RimBackmesh, bpy.context.scene.objects.active, None)  # Connect to the backmesh mesh
#         self.oMeshSoftBodyRimBackmesh.Hide()
#         self.oMeshSoftBody.Close()                  # Close the rim mesh.  ###MOVE? (To FindPinnedFlexParticles()?) 




#     def CreateUnity2BlenderMesh(self, nVerts):
#         """Creates a temporary mesh of 'nVerts' vertices as requested by Unity.  This is then used by Unity to efficently upload to Blender a large amount of verticies for further processing by Blender."""
#         sNameMeshUnity2Blender = self.oMeshSoftBody + G.C_NameSuffix_Unity2Blender          ###MOVE? Only useful for softbodies?
#         DeleteObject(self.oMeshUnity2Blender.GetName())
#         DeleteObject(sNameMeshUnity2Blender)
#         self.oMeshUnity2Blender = None
#         oMesh = bpy.data.meshes.new(sNameMeshUnity2Blender)
#         oMeshO = bpy.data.objects.new(sNameMeshUnity2Blender, oMesh)
#         oMesh.name = oMeshO.name = sNameMeshUnity2Blender       #Ensure we get the name we want!
#         oMesh.name = oMeshO.name = sNameMeshUnity2Blender
#         oScene = bpy.context.scene
#         oScene.objects.link(oMeshO)
#         oScene.objects.active = oMeshO
#         oMeshO.select = True
#         aVerts = []
#         for nVert in range(nVerts):
#             aVerts.append(Vector((0,0,0)))
#         oMesh.from_pydata(aVerts, [], [])
#         oMesh.update()
#         self.oMeshUnity2Blender = CMesh.Create(sNameMeshUnity2Blender, G.C_NodeFolder_Game)     # Store in our member variable as a CMesh so Unity can handshake with as usual       
#         print("CreateUnity2BlenderMesh() created mesh {} with {} verts.".format(sNameMeshUnity2Blender, nVerts))
#         #return oMeshO
#         return "OK"








### Old FlexSkin trying stuff
#             nShrinkDistanceTotal = -G.CGlobals.cm_nFlexParticleSpacing / 2
#             self.oMeshFlexCollider.Open()
#             bpy.ops.mesh.select_all(action='SELECT')
#             bpy.ops.transform.shrink_fatten(value=nShrinkDistanceTotal)
#             VertGrp_SelectVerts(self.oMeshFlexCollider.GetMesh(), "_FlexSkinSmoothArea_Vagina_Opening")
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.vertices_smooth(factor=1.0, repeat=20)      ###TUNE

            
            
#             nSteps = 4
#             nShrinkDistanceTotal = -G.CGlobals.cm_nFlexParticleSpacing / 2
#             nShrinkDistancePerStep = nShrinkDistanceTotal / nSteps
#               
#             self.oMeshFlexCollider.Open()
#             for nStep in range(nSteps):
#                 VertGrp_SelectVerts(self.oMeshFlexCollider.GetMesh(), "_FlexSkinSmoothArea_Vagina_Slit")
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=3)      ###TUNE
#                 bpy.ops.mesh.select_all(action='SELECT')
#                 bpy.ops.transform.shrink_fatten(value=nShrinkDistancePerStep)

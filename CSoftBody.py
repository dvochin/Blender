###NOW: Just split CSoftBody and changed collection serialization
# Softbody rim verts & normals not set... investigate!
# Can't go back and forth
# What about damn temp mesh?
# Then... titty morphing!!! :)









import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

import gBlender
import G
import CBody
import Client






class CSoftBody:
    def __init__(self, oBody, sSoftBodyPart):
        self.oBody              = oBody                     # The back-reference to the owning body.
        self.sSoftBodyPart      = sSoftBodyPart             # The name of the soft body part.  (e.g. "BreastL", "BreastR", "Penis", "VaginaL", "VaginaR")  This is our key in self.oBody.aSoftBodies[self.sSoftBodyPart]
        self.oMeshSoftBody      = None                      # The softbody surface mesh itself.  Visible in Unity and moved by PhysX2 softbody simulation via its internal solid tetramesh.
        self.oMeshSoftBodyRim   = None                      # The 'softbody rim mesh'  Responsible to pin softbody tetraverts to the skinned body so it moves with the body

        self.aMapRimTetravert2Tetravert = array.array('H')  # This array stores pairs of <#RimTetravert, #Tetravert> so Unity can pin the softbody tetraverts from the rim tetravert skinned mesh
        self.aMapRimVerts2Verts         = array.array('H')  # The final flattened map of what verts from the 'detached softbodypart' maps to what vert in the 'skinned main body'  Client needs this to pin the edges of the softbody-simulated part to the main body skinned mesh

        
        print("=== CSoftBody.ctor()  self.oBody = '{}'  self.sSoftBodyPart = '{}' ===".format(self.oBody.sMeshPrefix, self.sSoftBodyPart))
        
        #=== Prepare naming of the meshes we'll create and ensure they are not in Blender ===
        sNameMeshPart = self.oBody.sMeshPrefix + "CSoftBody-" + self.sSoftBodyPart         # Create name for to-be-created detach mesh and open the body mesh
        sNameMeshPartRim = sNameMeshPart + "-Rim"                         # The name of the 'softbody rim' mesh (for pinning softbody to skinned body) 
        gBlender.DeleteObject(sNameMeshPart)
        gBlender.DeleteObject(sNameMeshPartRim)
 
        #=== Obtain the to-be-detached vertex group of name 'self.sSoftBodyPart' from the combo mesh that originally came from the source body ===
        nVertGrpIndex_DetachPart = self.oBody.oMeshBody.vertex_groups.find(G.C_VertGrp_Detach + self.sSoftBodyPart)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
        oVertGroup_DetachPart = self.oBody.oMeshBody.vertex_groups[nVertGrpIndex_DetachPart]
        self.oBody.oMeshBody.vertex_groups.active_index = oVertGroup_DetachPart.index
     
        #=== Open the body's mesh-to-be-split and create a temporary data layer for twin-vert mapping ===
        gBlender.SelectAndActivate(self.oBody.oMeshBody.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bmBody = bmesh.from_edit_mesh(self.oBody.oMeshBody.data)
        oLayVertTwinID = bmBody.verts.layers.int.new(G.C_DataLayer_TwinVert)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
        nNextVertTwinID = 1                 # We set the next twin vert ID to one.  New IDs for all detachable parts will be created from this variable by incrementing.  This will enable each detached part to find what skinned vert from the body it needs to connect to during gameplay.

        #=== Prepare the part to be detached by first obtaining its list of faces ===
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
        bmBody = bmesh.from_edit_mesh(self.oBody.oMeshBody.data)  ###LEARN!!: We must re-obtain new bmesh everytime we re-enter edit mode.  (And of course old bmesh object references are gone but IDs persist!)
        aFacesToSplit = [oFace for oFace in bmBody.faces if oFace.select]  # Obtain array of all faces to separate
     
        #=== Store the boundary edges of the split into the new vertex group so we can provide Client the mapping of split verts between the meshes ===
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.region_to_loop()       # This will select only the edges at the boundary of the cutout polys
        for oEdge in bmBody.edges:          # Iterate over the edges at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut
            if oEdge.select == True:
                if oEdge.is_manifold == False:  # Deselect the edges-on-edge (i.e. natural edge of cloth)
                    oEdge.select_set(False)
     
        #=== Iterate over the split verts to store a uniquely-generated 'twin vert ID' into the custom data layer so we can re-twin the split verts from different meshes after the mesh separate ===
        aVertsBoundary = [oVert for oVert in bmBody.verts if oVert.select]
        for oVert in aVertsBoundary:
            oVert[oLayVertTwinID] = nNextVertTwinID  # These are unique to the whole skinned body so all detached softbody can always find their corresponding skinned body vert for per-frame positioning
            nNextVertTwinID += 1
     
        #=== Reselect the faces again to split the 'detachable softbody' into its own mesh so that it can be sent to softbody/cloth simulation.  ===
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bMeshHasGeometry = False  # Determine if softbody part mesh has any faces
        for oFace in aFacesToSplit:
            oFace.select_set(True)
            bMeshHasGeometry = True
     
        #=== If softbody mesh has no geometry then we don't generate it as client has nothing to render / process for this softbody ===
        if bMeshHasGeometry == False:      ####OBS?
            raise Exception("###ERROR: CSoftBody.ctor() skips creation of softbody '{}' from body '{}' because it has no geometry <<<".format(self.sSoftBodyPart, self.oBody.sMeshPrefix))
     
        #=== Split and separate the softbody from the composite mesh ===
        bpy.ops.mesh.split()        # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
        bpy.ops.mesh.separate()     # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'softbody'
        bpy.ops.object.mode_set(mode='OBJECT')

        #=== Name the newly created mesh as the requested 'detached softbody' ===      
        bpy.context.object.select = False           ###LEARN: Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBody = bpy.context.object                                 # The just-split mesh becomes the softbody mesh! 
        self.oMeshSoftBody.name = self.oMeshSoftBody.data.name = sNameMeshPart  # Name it to our global name scheme
        self.oMeshSoftBody.name = self.oMeshSoftBody.data.name = sNameMeshPart
        
        #=== Cap the body part that is part of the softbody (edge verts from only that body part are now selected)  If this softbody has no body verts (e.g. PenisClothing) then no capping will occur) ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmSoftBody = bmesh.from_edit_mesh(self.oMeshSoftBody.data)
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')  ###BUG?? ###CHECK: Possible that edge collapse could fail depending on View3D mode...
        bpy.ops.mesh.extrude_edges_indiv()      ###LEARN: This is the function we need to really extrude!
        bpy.ops.mesh.edge_collapse()            ###DESIGN ###IMPROVE Do we always cap whatever body part is ripped out?
        for oVert in bmSoftBody.verts:         # The cap vert(s) created will have copied one of the 'VertTwinID'.  Wipe it out to avoid corrupting matching below 
            if oVert.select:
                oVert[oLayVertTwinID] = 0           ###OPT: Iterate through whole mesh to find one selected vert?
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')


        #===== Create the 'Skinned Rim' skinned mesh that Client can use to use 'BakeMesh()' on a heavily-simplified version of the main body mesh that contains only the 'rim' polygons that attach to all the detachable softbody this code separates.  It is this 'Rim' skinned mesh that will 'pin' the softbody tetravert solid to the skinned body === 
        ####DESIGN: Vert topology changes at every split!  MUST map twinID to body verts once all cuts done ###NOW!!!
        #=== Iterate through the verts of the main skinned mesh to select all the twin verts so we can create the rim mesh
        gBlender.SelectAndActivate(self.oBody.oMeshBody.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmBody = bmesh.from_edit_mesh(self.oBody.oMeshBody.data)
        oLayVertTwinID = bmBody.verts.layers.int[G.C_DataLayer_TwinVert]
        for oVert in bmBody.verts:
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                oVert.select_set(True)      # Select this edge boundary vertex for the upcoming code in which we expand the rim selection to create the rim submesh
    
        #=== Select the faces neighboring the twin verts and duplicate them into the new 'rim mesh'
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='EDGE')  # ... With the rim verts selected two loops ago expand these 'boundary verts' into edge mode any edge touching the boundary verts are edges are selected (including non-boundary ones)...
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')  # ... then switch to poly mode to have the smallest set of polygons that have an edge at the boundary are left selected.  These will form their own 'reduced skin mesh' that will be baked at every frame to calculate pin positions
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate()             # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'softbody part'
        bmBody.verts.layers.int.remove(oLayVertTwinID)  # Remove the temp data layer in the skin mesh as the just-separated mesh has the info now...
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== Fetch the just-created 'rim' skinned mesh and set it to its proper name ===
        bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBodyRim = bpy.context.object
        self.oMeshSoftBodyRim.name = self.oMeshSoftBodyRim.data.name = sNameMeshPartRim  ###NOTE: Do it twice to ensure name really sticks  ###WEAK: Wish this was easier to do!
        self.oMeshSoftBodyRim.name = self.oMeshSoftBodyRim.data.name = sNameMeshPartRim
    
        #=== Cleanup the rim mesh by removing all materials ===
        while len(self.oMeshSoftBodyRim.material_slots) > 0:  ###IMPROVE: Find a way to remove doubles while preventing key-not-found errors in twin hunt below??
            bpy.ops.object.material_slot_remove()
        bpy.ops.object.material_slot_add()  # Add a single default material (captures all the polygons of rim) so we can properly send the mesh over (crashes if zero material)
        bpy.ops.object.mode_set(mode='OBJECT')
        gBlender.Cleanup_VertGrp_RemoveNonBones(self.oMeshSoftBodyRim)  # Remove the extra vertex groups that are not skinning related



  
    def ProcessTetraVerts(self, nNumVerts_UnityToBlenderMesh, nDistTetraVertsFromRim):
        "Process the PhysX2-created tetraverts and create softbody rim mesh.  Updates our rim mesh currently containing only rim (for normals).  This mesh will be responsible to 'pin' some softbody tetraverts to the skinned body so softbody doesn't 'fly out'"
        print("-- CSoftBody.ProcessTetraVerts() on body '{}' and softbody '{}' --".format(self.oBody.sMeshPrefix, self.sSoftBodyPart));

        #=== Create a temporary copy of rim mesh so we can transfer weights efficiently from it to new mesh including tetraverts ===
        oMeshSoftBodyRimCopy = gBlender.DuplicateAsSingleton(self.oMeshSoftBodyRim.name, "TEMP_DetachSoftBody", G.C_NodeFolder_Temp, False)

        #=== Create a temporary copy of Unity2Blender mesh so we can trim it to 'nNumVerts_UnityToBlenderMesh' verts ===  
        oMeshUnityToBlenderCopy = gBlender.DuplicateAsSingleton(self.oBody.oMeshUnity2Blender.name, "TEMP_Unity2Blender", G.C_NodeFolder_Temp, False)

        #=== Open the temp mesh Unity requested in CreateTempMesh() and push in a data layer with vert index.  This will prevent us from losing access to Unity's tetraverts as we process this mesh toward the softbody rim ===        
        gBlender.SelectAndActivate(oMeshUnityToBlenderCopy.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bm = bmesh.from_edit_mesh(oMeshUnityToBlenderCopy.data)
        for oVert in bm.verts:
            if (oVert.index >= nNumVerts_UnityToBlenderMesh):
                oVert.select_set(True)
        bpy.ops.mesh.delete(type='VERT')        # Delete all verts from Unity2Blender mesh that are 'extra' (That is only created once with the max # of verts we can ever expect)
        nVertsRimOrig = len(self.oMeshSoftBodyRim.data.vertices)     # Remember how many verts rim had before join (so we can resync below) 
        print("- CSoftBody.ProcessTetraVerts() shifts joined rim verts by {} from inserting Unity tetraverts.".format(nNumVerts_UnityToBlenderMesh))
 
        #=== Create the custom data layer and store vert indices into it === 
        oLayTetraVerts = bm.verts.layers.int.new(G.C_DataLayer_TetraVerts)
        for oVert in bm.verts:
            oVert[oLayTetraVerts] = oVert.index + G.C_OffsetVertIDs    # Apply offset to easily tell real IDs in later loop
        bpy.ops.object.mode_set(mode='OBJECT')

        
        #===== Combine the tetravert-mesh with the rim mesh of that softbody.  We need to isolate the tetraverts close to the rim verts to 'pin' them =====
        ###LEARN: Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh)
        gBlender.SelectAndActivate(oMeshUnityToBlenderCopy.name)             # First select and activate mesh that will be destroyed (temp mesh)
        self.oMeshSoftBodyRim.select = True                         # Now select...
        bpy.context.scene.objects.active = self.oMeshSoftBodyRim    #... and activate mesh that will be kepp (merged into)  (Note that to-be-destroyed mesh still selected!)
        bpy.ops.object.join()                                       #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###LEARN: Existing custom data layer in merged mesh destroyed!!
        oMeshUnityToBlenderCopy = None                              # Above join destroyed the copy mesh so set our variable to None

        #===== Remove the tetraverts that are too far from the rim =====
        #=== Select the rim verts in the joined mesh ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(self.oMeshSoftBodyRim.data)
        oLayTetraVerts = bm.verts.layers.int[G.C_DataLayer_TetraVerts]
        for oVert in bm.verts:
            if (oVert.index > nNumVerts_UnityToBlenderMesh):
                oVert.select_set(True)                      # Select only the verts with no OrigVertID = tetraverts
        #=== Move the rim verts with the close tetraverts some distance so we can quickly separate the tetraverts close to rim verts ===        
        C_TempMove = 10
        bpy.ops.transform.transform(mode='TRANSLATION', value=(0, C_TempMove, 0, 0), proportional='ENABLED', proportional_size=nDistTetraVertsFromRim, proportional_edit_falloff='CONSTANT')  # Move the rim verts with propportional editing so the tetraverts near rim are moved too.  This is how we separate them
        #=== Delete all tetraverts that are too far from rim ===
        bpy.ops.mesh.select_all(action='DESELECT')
        for oVert in bm.verts:  # Select all body verts far from clothing (Separated by translation operation above)                                  
            if oVert.co.z > -C_TempMove / 2:  ###WEAK!! Stupid 90 degree rotation rearing its ugly head again...
                oVert.select_set(True)
        bpy.ops.mesh.delete(type='VERT')  # Delete all tetraverts that were too far from rim.  (These will be softbody-simulated and the others pinned)
        #=== Move back the remaining rim and 'close tetraverts to their original position.  At this point only tetraverts near rim remain ===
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.transform(mode='TRANSLATION', value=(0, -C_TempMove, 0, 0))  # Move the clothing verts with proportional enabled with a constant curve.  This will also move the body verts near any clothing ###TUNE    
        bpy.ops.object.mode_set(mode='OBJECT')
        #=== Skin the rim+tetraverts mesh from original rim mesh.  (So tetraverts are skinned too!)
        oMeshSoftBodyRimCopy.select = True                             # Select the original rim mesh (keeping rim+tetraverts mesh activated)
        bpy.ops.object.vertex_group_transfer_weight()
        nVertsRimJoined = len(self.oMeshSoftBodyRim.data.vertices)     # Remember how many verts rim now has once close tetraverts are kept in
        nShiftAppliedToOrigRimVerts = nVertsRimJoined - nVertsRimOrig   # Calculate the shift applied to orig verts  

        #===== CREATE THE MAP PIN TETRAVERTS TO TETRAVERT MAP =====
        gBlender.SelectAndActivate(self.oMeshSoftBodyRim.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bmRim = bmesh.from_edit_mesh(self.oMeshSoftBodyRim.data)
        oLayTetraVerts = bmRim.verts.layers.int[G.C_DataLayer_TetraVerts]

        #=== Iterate through tetraverts to fill in its map traversal ===
        for oVert in bmRim.verts:                                                                        
            nTetraVertID = oVert[oLayTetraVerts]
            if (nTetraVertID >= G.C_OffsetVertIDs):            # The real tetraverts are over this offset (as created above)
                nTetraVertID -= G.C_OffsetVertIDs              # Retrieve the non-offsetted tetravert
                self.aMapRimTetravert2Tetravert.append(oVert.index)
                self.aMapRimTetravert2Tetravert.append(nTetraVertID)
                #print("RimTetravert {:4d} = Tetravert {:4d}". format(oVert.index, nTetraVertID))
        bpy.ops.object.mode_set(mode='OBJECT')


        #===== CREATE THE TWIN VERT MAPPING =====
        #===1. Iterate over the rim copy vertices, and find the rim vert for every 'twin verts' so next loop can map softbody part verts to rim verts for pinning === 
        gBlender.SelectAndActivate(oMeshSoftBodyRimCopy.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bmRimCopy = bmesh.from_edit_mesh(oMeshSoftBodyRimCopy.data)
        oLayVertTwinID = bmRimCopy.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertRim = {}
        for oVert in bmRimCopy.verts:
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertRim[nTwinID] = oVert.index + nShiftAppliedToOrigRimVerts ###NOTE: Apply shift forced upon rim verts from join with tetra verts above
                #print("TwinID {:3d} = RimVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
        bpy.ops.object.mode_set(mode='OBJECT')
        gBlender.DeleteObject(oMeshSoftBodyRimCopy.name)               # We have no further use for the copied rim mesh

        #===2. Iterate through the verts of the newly separated softbody to access the freshly-created custom data layer to obtain ID information that enables us to match the softbody mesh vertices to the main skinned mesh for pinning ===
        gBlender.SelectAndActivate(self.oMeshSoftBody.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmSoftBody = bmesh.from_edit_mesh(self.oMeshSoftBody.data)
        oLayVertTwinID = bmSoftBody.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertSoftBody = {}
        for oVert in bmSoftBody.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertSoftBody[nTwinID] = oVert.index
                #print("TwinID {:3d} = SoftBodyVert {:5d} mat {:} at {:}".format(nTwinID, oVert.index, oVert.link_faces[0].material_index, oVert.co))
        bpy.ops.object.mode_set(mode='OBJECT')

        #===3. With both maps created, bridge them together to a flattened map from softbody mesh to its rim vert ===
        for nTwinID in aMapTwinId2VertSoftBody:
            nVertTwinSoftBody = aMapTwinId2VertSoftBody[nTwinID]
            if nTwinID in aMapTwinId2VertRim:
                nVertTwinRim = aMapTwinId2VertRim[nTwinID]
                self.aMapRimVerts2Verts.append(nVertTwinSoftBody)
                self.aMapRimVerts2Verts.append(nVertTwinRim)
                #print("TwinID {:3d} = SoftBodyVert {:5d} = RimVert {:5d}".format(nTwinID, nVertTwinSoftBody, nVertTwinRim))
            else:
                G.DumpStr("###ERROR in CSoftBody.SeparateSoftBodyPart() finding nTwinID {} in aMapTwinId2VertRim".format(nTwinID)) 

        return "OK"     ###TEMP


    def SerializeCollection(self, aCollection):         ####MOVE?        
        "Send Unity the requested serialized bytearray of the previously-defined collection"
        oBA = bytearray()
        oBA += struct.pack('H', G.C_MagicNo_TranBegin)  ###LEARN: Struct.Pack args: b=char B=ubyte h=short H=ushort, i=int I=uint, q=int64, Q=uint64, f=float, d=double, s=char[] ,p=PascalString[], P=void*
        gBlender.Stream_SerializeArray(oBA, aCollection.tobytes())
        oBA += struct.pack('H', G.C_MagicNo_TranEnd)
        return oBA
    
    def SerializeCollection_aMapRimVerts2Verts(self):
        return self.SerializeCollection(self.aMapRimVerts2Verts) 

    def SerializeCollection_aMapRimTetravert2Tetravert(self):
        return self.SerializeCollection(self.aMapRimTetravert2Tetravert)
    
    
    
    
#             gBlender.SelectAndActivate(self.oMeshSoftBodyRim.name)
#         for oVert in self.oMeshSoftBodyRim.data.vertices:
#             print("Rim Vert {:3d} at {:}".format(oVert.index, oVert.co))

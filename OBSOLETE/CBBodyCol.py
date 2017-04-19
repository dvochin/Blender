# import bpy
# import sys
# import bmesh
# import array
# import struct
# from math import *
# from mathutils import *
# 
# from gBlender import *
# import G
# import Client
# 
# 
# 
# 
# def CBBodyColCloth_GetMesh(sNameMesh):          ###DESIGN!! ###OPT!!!: Can preprocess the body collider at ship-time and store arrays in file!
#     nPosSuffix = sNameMesh.find(G.C_NameSuffix_BodyColCloth)
#     if nPosSuffix == -1:
#         return "ERROR: CBBodyColCloth_GetMesh() had improperly named mesh '%s' without proper suffix of '%s'" % (sNameMesh, G.C_NameSuffix_BodyColCloth)
#     sNameCharacter = sNameMesh[:nPosSuffix]                 ####SOON: Get rid of this naming SHIT!
#     
#     #=== Obtain source mesh and cleanup ===
#     oMeshBodyColClothO = SelectAndActivate(sNameCharacter + G.C_NameSuffix_BodyColCloth)
#     VertGrp_RemoveNonBones(oMeshBodyColClothO, True)     # Also remove the non-bone extra vert groups so only vert groups meant for skinning remain (to avoid errors during serialization to client)
#     bpy.ops.object.mode_set(mode='EDIT')
#     bm = bmesh.from_edit_mesh(oMeshBodyColClothO.data)
# 
#     #=== Select the edges on the edge so the next loop sending them to Client will ignore them.  Having capsule colliders there provide little value and removing them allows more capsule colliders / eges to be created away from the body collider edge where they do more good ===
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#     bpy.ops.mesh.select_non_manifold(extend=False)
#     
#     #=== Create the 'aEdges' flat array to allow easy creation of capsules (linked to body edges) from spheres (linked to bodycol verts) ===
#     aEdges = array.array('H')
#     nNumCapsuleColliders = 0
#     for oEdge in bm.edges:
#         if oEdge.select:                            # We don't send to client the 'edges on edges' as placing capsule colliders there has little value.  (They are still part of the mesh so their polygons still contribute to accurate normals however...)
#             continue
#         aEdges.append(oEdge.verts[0].index)
#         aEdges.append(oEdge.verts[1].index)
#         nNumCapsuleColliders += 1
# 
#     #=== Create the 'aVertToVerts' flat array to greatly speed up vert-based traversal of mesh in C++ runtime code ===
#     aVertToVerts = array.array('H')
# #     aVertToTris = array.array('H')                ###TODO ###IMPROVE?: Delayed as this is an optimization... do once design stabilizes
#     for oVert in bm.verts:
#         for oEdge in oVert.link_edges:
#             oVertOther = oEdge.other_vert(oVert)
#             aVertToVerts.append(oVertOther.index)
#             oEdge.seam = False                              # While we are iterating over edges also remove seams (no longer relevant now that we're only one material)
# #         aVertToVerts.append(G.C_MagicNo_EndOfFlatGroup)  # End the group with our end-of-group magic number
# #         for oEdge in oVert.link_edges:
# #             oVertOther = oEdge.other_vert(oVert)
# #             aVertToTris.append(oVertOther.index)
# #         aVertToTris.append(G.C_MagicNo_EndOfFlatGroup)  # End the group with our end-of-group magic number
# 
#     #=== Construct the beginning of the outgoing bytearray that will be sent to client so it can receive our mesh ===
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oBA = Client.Unity_GetMesh(oMeshBodyColClothO.name)
# 
#     #=== Send the additional definition arrays we created above ===
#     Stream_SerializeArray(oBA, aEdges.tobytes())
#     Stream_SerializeArray(oBA, aVertToVerts.tobytes())
#     
#     #=== Add another 'end magic number' at the end of our stream to help catch deserialization errors ===
#     oBA += Client.Stream_GetEndMagicNo()
#     
#     #print("\n+++ CBBodyColCloth_GetMesh OK: " + oMeshBodyColClothO.name)
# 
#     return oBA                  # Return carefully-constructed serialized stream of data that client will deserialize to construct its own structures from our info.
# 
#  
# 
# 
# 
# 
# 
# 
# def CBBodyCol_Generate(sNameSrcBody, nNumDesiredCapsuleColliders):       # Called by the client to creates and send a quality decimated body mesh from 'sNameSrcBody' that is optimized to create the desired number of capsule colliders to repel the clothing where it exists around the body.
#     ###BUG!!!: Having bodysuits with some selected verts will cause this to not work as it should!  (Deselect them here?)
#     ###IMPROVE: Remove lower arm for better hand raycast!
#     
#     #bOnlyCreateNearClothing = False         ###OBS: Totally remove as this is just for full body now??
#     
#     #===== Merge body and all clothing into one mesh to enable detection of body verts near clothing via Blender proportional editing =====
#     oMeshBodyOrigO = bpy.data.objects[sNameSrcBody]
#     #if bOnlyCreateNearClothing:
#     #    oMeshClothO = DuplicateAsSingleton(sNameCharacter + G.C_NameSuffix_ClothFit, "TEMP_ClothForBodyCol", G.C_NodeFolder_Game, False)                    ###DESIGN!!! How to specify cloth from client??
#     oMeshBodyColO = DuplicateAsSingleton(oMeshBodyOrigO.name, sNameSrcBody + G.C_NameSuffix_BodyCol, None, False)       ###REVIVE: G.C_NodeFolder_Temp
#     oMeshBodyColO.show_wire = True
#     ###CHECK? del(oMeshBodyColO[G.C_PropArray_MapSharedNormals])      # Source body mesh has shared mesh normals which would make serialization choke on BodyCol as that array is only good for source mesh body.
# 
#     #=== Remove the body mesh's unneeded head, hands and feet from the body to speed up this function ===
#     VertGrp_SelectVerts(oMeshBodyColO, G.C_Area_HeadHandFeet)        # Removes about 68% of the mesh so colliders are allocated where most needed.  (Also greatly speed up function!!)
#     bpy.ops.mesh.delete(type='VERT')
#     VertGrp_SelectVerts(oMeshBodyColO, G.C_VertGrp_CSoftBody + "Breasts")       # If breasts are on this mesh delete them... they are softbody simulated and require special in-PhysX colliders
#     bpy.ops.mesh.delete(type='VERT')
#     VertGrp_SelectVerts(oMeshBodyColO, G.C_VertGrp_CSoftBody + "Penis")         # If penis is on this mesh delete it... it gets its own sophisticated collider chain
#     bpy.ops.mesh.delete(type='VERT')
#     
#     #=== Select all body verts so that we can tell them apart from all the cloth verts after the upcoming join ===    
#     bpy.ops.mesh.select_all(action='SELECT')  
#     bpy.ops.object.mode_set(mode='OBJECT')
# 
#     #=== Join in all the clothing so we can determine body verts nearby clothing ===
#     #if bOnlyCreateNearClothing:
#     #    oMeshClothO.select = True
#     #    bpy.ops.object.join()  # Join the body and all clothing.  Only body verts should be now selected            ###BUG!!!: Having bodysuits with some selected verts will cause this to not work as it should!  (Deselect them here?)
#     #    oMeshClothO = None     # Mesh is gone now so remove reference
#     
#     #=== Cleanup the mesh by removing all vertex groups (reskinned below), modifiers and leaving only the body material ===        ###IMPROVE: Create utility function for cleanup??
#     bpy.ops.object.vertex_group_remove(all=True)
#     sNameTorsoMat = "Torso"
#     if sNameSrcBody[0] != "W":       ###WEAK: Dumb search for different material name on man. 
#         sNameTorsoMat += sNameSrcBody[0]
#     ###############REV oMatBody = oMeshBodyColO.data.materials[sNameTorsoMat] # Before removing materials obtain reference to main body material so we can reinsert it in a few lines...
#     while len(oMeshBodyColO.data.materials) > 0:    # Remove all the materials
#         bpy.ops.object.material_slot_remove()
#     bpy.ops.object.material_slot_add()              # With all materials removed add a single one so all verts go to that one material (gBlender link to clients require at least one material)
#     ###############REV  oMeshBodyColO.material_slots[0].material = oMatBody     # In the re-created slot re-assign the body material so it is the only material there.
#     while len(oMeshBodyColO.modifiers) > 0:         # Remove all the modifiers
#         oMeshBodyColO.modifiers.remove(oMeshBodyColO.modifiers[0])
#     bpy.ops.object.mode_set(mode='EDIT')
#     bm = bmesh.from_edit_mesh(oMeshBodyColO.data)
# 
#     #if bOnlyCreateNearClothing:
#     #    #=== Perform move operation in joined mesh with all clothing selected with proportional editing on (contant curve) ===
#     #    bpy.ops.mesh.select_all(action='INVERT')  # Invert selection to select only clothing.
#     #    C_TempMove = 4
#     #    bpy.ops.transform.transform(mode='TRANSLATION', value=(0, C_TempMove, 0, 0), proportional='ENABLED', proportional_size=.02, proportional_edit_falloff='CONSTANT')  # Move the clothing verts with proportional enabled with a constant curve.  This will also move the body verts near any clothing ###TUNE    
#     #
#     #    #=== With the clothing still selected, delete it to leave only the body ===
#     #    bpy.ops.mesh.delete(type='VERT')
#     #
#     #    #=== Delete all body verts that are too far from clothing ===
#     #    for oVert in bm.verts:  # Select all body verts far from clothing (Separated by translation operation above)                                  
#     #        if oVert.co.z > -C_TempMove / 2:  ###WEAK!! Stupid 90 degree rotation rearing its ugly head again...
#     #            oVert.select_set(True)
#     #    bpy.ops.mesh.delete(type='VERT')  # Delete all body verts that were far from any clothing.
#     #
#     #    #=== Move back the remaining body-near-cloth verts to their original position.  At this point only body verts near clothing remain ===
#     #    bpy.ops.mesh.select_all(action='SELECT')
#     #    bpy.ops.transform.transform(mode='TRANSLATION', value=(0, -C_TempMove, 0, 0))  # Move the clothing verts with proportional enabled with a constant curve.  This will also move the body verts near any clothing ###TUNE    
# 
#     #=== Delete the 'wire edges' (edges with no faces) that above vert delection can create ===
#     bpy.ops.mesh.select_all(action='DESELECT')
#     for oVert in bm.verts:
#         if oVert.is_wire:
#             oVert.select_set(True)
#     bpy.ops.mesh.delete(type='VERT')  # Delete all body verts that were far from any clothing.
# 
#     #=== Merge verts that are right on top of each other to bridge gaps between material seams ===
#     bpy.ops.mesh.select_all(action='SELECT')
#     bpy.ops.mesh.remove_doubles(threshold=0.001)
# 
#     #=== Run the amazing LoopTools relax on the borders to greatly smooth out the jagged border so decimate doesn't allocate too many precious verts to define jagged border ===
#     bpy.ops.mesh.select_non_manifold(extend=False)
#     bpy.ops.mesh.looptools_relax(interpolation='cubic',  regular=True, iterations='5')          # This call is slow but removes high frequency noise without changing shape of curve too much
# 
#     #=== Perform additional smoothing on the edges of the body-verts-near-clothing to prevent decimate to allocate precious verts on a jagged border ===
#     bpy.ops.mesh.select_non_manifold(extend=False)
#     bpy.ops.mesh.select_more()
#     bpy.ops.mesh.vertices_smooth(repeat=2)  ###TUNE
# 
#     #=== Delete the right half of the body (so we can create a symmetrical body collider) ===
#     bpy.ops.mesh.select_all(action='DESELECT')
#     for oVert in bm.verts:                                  
#         if oVert.co.x < 0:
#             oVert.select_set(True)
#     bpy.ops.mesh.delete(type='VERT')  # Delete all body verts that were far from any clothing.
#     bpy.ops.mesh.select_all(action='SELECT')
#     bpy.ops.mesh.quads_convert_to_tris()            ###REVIVE: use_beauty=True
# 
#     #=== Decimate the half of the body with the desired number of edges ===
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oModDecimate = oMeshBodyColO.modifiers.new('DECIMATE', 'DECIMATE')
#     nNumDesiredFaces = (nNumDesiredCapsuleColliders / 2) * G.C_TypicalRatioTrisToEdges / G.C_RatioEstimatedReductionBodyCol
#     nFacesNow = len(oMeshBodyColO.data.polygons)
#     nRatioFacesToDecimate = nNumDesiredFaces / nFacesNow 
#     oModDecimate.ratio = nRatioFacesToDecimate
#     oModDecimate.use_collapse_triangulate = True
#     AssertFinished(bpy.ops.object.modifier_apply(modifier=oModDecimate.name))  ###LEARN: Have to specify 'modifier' or this won't work!        
# 
#     #=== Cleanup the freshly-created decimated mesh by removing verts that are too close to one-another and removing separated geometry ===
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_loose()
#     bpy.ops.mesh.delete(type='VERT')  # Delete all body verts that were far from any clothing.
#     bpy.ops.mesh.select_non_manifold(extend=False)                      # Perform a heavy decimation on the border.
#     bpy.ops.mesh.remove_doubles(threshold=0.03, use_unselected=False)  ###TUNE!
#     bpy.ops.mesh.select_all(action='SELECT')
#     bpy.ops.mesh.remove_doubles(threshold=0.02, use_unselected=False)  ###TUNE!
# 
#     #=== Beautify the mesh so triangle edges can be chosen for less-degenerate geometry ===
#     bpy.ops.mesh.select_all(action='SELECT')
#     bpy.ops.mesh.beautify_fill()
# 
#     #=== Mirror the just-decimated mesh so we obtain a beautiful symmetrical decimation ===
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oModMirrorX = Util_CreateMirrorModifierX(oMeshBodyColO)
#     AssertFinished(bpy.ops.object.modifier_apply(modifier=oModMirrorX.name))        
# 
#     #=== Run the amazing LoopTools relax on the borders to greatly smooth out the jagged border so decimate doesn't allocate too many precious verts to define jagged border ===
# #     bpy.ops.mesh.select_non_manifold(extend=False)        ###IMPROVE?: This can help but it also removes symmetry in some situations where selecting non-manifold also selects polys 
# #     bpy.ops.mesh.looptools_relax(interpolation='cubic',  regular=True, iterations='1')  ###TUNE: makes decimated edge nicer (especially at x=0!), but even 1 iteration seems a bit heavy...
# 
#     #=== Iterate over the non-manifold verts to find those that are attached only to one triangle and delete them ===
#     bpy.ops.object.mode_set(mode='EDIT')
#     bm = bmesh.from_edit_mesh(oMeshBodyColO.data)
#     for nIteration in range(2):             ###TUNE
#         bpy.ops.mesh.select_non_manifold(extend=False)
#         for oVert in bm.verts:                                  
#             if oVert.select and len(oVert.link_faces) > 1:
#                 oVert.select_set(False)
#             if fabs(oVert.co.x) < 0.01:                     # While we're iterating vert move verts that are very close to x=0 to 0 so that they can be merged together in the upcoming remove_doubles()
#                 oVert.co.x = 0
#         bpy.ops.mesh.delete(type='VERT')  # Delete all body verts that were select (too far from any clothing).
# 
#     #=== Merge verts that are too close to one-another another time now that we are mirrored (will merge those we just moved in loop above that were very close) ===
#     bpy.ops.mesh.select_all(action='SELECT')
#     bpy.ops.mesh.remove_doubles(threshold=0.005)        ###TUNE (Small range as this can de-symmetrize our collider mesh...
# 
#     #=== Select the edges on the edge so the next loop sending them to Client will ignore them.  Having capsule colliders there provide little value and removing them allows more capsule colliders / eges to be created away from the body collider edge where they do more good ===
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#     bpy.ops.mesh.select_non_manifold(extend=False)
#     
#     #=== Create the 'aEdges' flat array to allow easy creation of capsules (linked to body edges) from spheres (linked to bodycol verts) ===
#     aEdges = array.array('H')
#     nNumCapsuleColliders = 0
#     for oEdge in bm.edges:
#         if oEdge.select:                            # We don't send to client the 'edges on edges' as placing capsule colliders there has little value.  (They are still part of the mesh so their polygons still contribute to accurate normals however...)
#             continue
#         aEdges.append(oEdge.verts[0].index)
#         aEdges.append(oEdge.verts[1].index)
#         nNumCapsuleColliders += 1
# 
#     #=== Create the 'aVertToVerts' flat array to greatly speed up vert-based traversal of mesh in C++ ===
#     aVertToVerts = array.array('H')
#     for oVert in bm.verts:
#         for oEdge in oVert.link_edges:
#             oVertOther = oEdge.other_vert(oVert)
#             aVertToVerts.append(oVertOther.index)
#             oEdge.seam = False                              # While we are iterating over edges also remove seams (no longer relevant now that we're only one material)
#         aVertToVerts.append(G.C_MagicNo_EndOfFlatGroup)  # End the group with our end-of-group magic number
# 
#     #=== Transfer weights from the source body so that the body collider mesh will move in the shape of the body and properly drive its PhysX colliders as a result.  (Gameplay mode only... ClothFit bodycol derived from full morphed body) ===    
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oMeshBodyOrigO.hide = False            ###LEARN: Mesh MUST be visible for weights to transfer!
#     Util_TransferWeights(oMeshBodyColO, oMeshBodyOrigO)
#     VertGrp_RemoveNonBones(oMeshBodyColO, True)     # Also remove the non-bone extra vert groups so only vert groups meant for skinning remain (to avoid errors during serialization to client)
#     
#     #=== Print stats to see how close we got to the number of desired edges ===
#     print("\n--- CBBodyCol_GetMesh() creates mesh with %d capsule colliders, %d verts, %d edges and %d faces ---" % (nNumCapsuleColliders, len(oMeshBodyColO.data.vertices), len(oMeshBodyColO.data.edges), len(oMeshBodyColO.data.polygons)))
#     if (nNumCapsuleColliders > nNumDesiredCapsuleColliders):
#         print("WARNING: Final capsule collider at %d is greater than number desired %d by %.1f%%" % (nNumCapsuleColliders, nNumDesiredCapsuleColliders, 100 * nNumCapsuleColliders / nNumDesiredCapsuleColliders))
#     else:
#         print("Final capsule collider count at %d is lesser than number desired %d by %.1f%%" % (nNumCapsuleColliders, nNumDesiredCapsuleColliders, 100 * nNumCapsuleColliders / nNumDesiredCapsuleColliders))
# 
#     #=== Store the calculated arrays.  They are now ready to be sent to client in CBBodyCol_GetMesh()
#     oMeshBodyColO['aEdges']         = aEdges.tobytes()
#     oMeshBodyColO['aVertToVerts']   = aVertToVerts.tobytes()
# 
#     #=== Create the aMapToBodyVerts and aMapToBodyVertsOffset arrays that enables us to update the verts of the BodyCol as the source body is morphed ===
# #     aMapToBodyVerts = array.array('H')
# #     aMapToBodyVertsOffset = array.array('f')
# #     for oVert in oMeshBodyColO.data.vertices:
# #         nVertClosest, nDistMin, vecVertClosest = Util_FindClosestVert(oMeshBodyOrigO, oVert.co, .02)       ###TUNE?
# #         if nVertClosest != -1:
# #             vecDiff = oVert.co - vecVertClosest
# #             aMapToBodyVerts         .append(nVertClosest)    
# #             aMapToBodyVertsOffset   .append(-vecDiff[0])        ###WEAK: A poor part of our design shows itself here: As Blender is Z-up and clients are Y-up and we must convert between left hand rule and right hand rule, an unfortunate part is the conversion must invert X for meshes to have the same shape.  We therefore must invert x offset here too...     
# #             aMapToBodyVertsOffset   .append( vecDiff[1])    
# #             aMapToBodyVertsOffset   .append( vecDiff[2])
# #             #print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %6.4f" % (oVert.index, nVertClosest, oVert.co.x, oVert.co.y, oVert.co.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
# #         else:
# #             print("WARNING: CBBodyCol_GetMesh() could not find neighbor vert for ", oVert.index)           ###CHECK: A fatal error if we don't push some placeholder in array?  ###DESIGN!!!
# 
# 
# def CBBodyCol_GetMesh(sNameMesh):       # Called by the client to send a  decimated body mesh generated by CBBodyCol_Generate() above
# 
#     oMeshBodyColO = bpy.data.objects[sNameMesh]
# 
#     #=== Construct the beginning of the outgoing bytearray that will be sent to client so it can receive our mesh ===
#     oBA = Client.Unity_GetMesh(oMeshBodyColO.name)
# 
#     #=== Send the additional definition arrays we created in Generate call ===
#     Stream_SerializeArray(oBA, oMeshBodyColO['aEdges'])
#     Stream_SerializeArray(oBA, oMeshBodyColO['aVertToVerts'])
#     
#     #=== Add another 'end magic number' at the end of our stream to help catch deserialization errors ===
#     oBA += Client.Stream_GetEndMagicNo()
# 
#     return oBA                  # Return carefully-constructed serialized stream of data that client will deserialize to construct its own structures from our info.

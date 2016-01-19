# def OBS_PreviousPairImplementationForBreasts():    ### No longer done in-body but as part of new SlaveMesh_XXX functionality
# 
#     #===== Create the mapping between breast verts and its collider sub-mesh.  At every morph we must set each collider verts to its matching breast vert =====
#     #=== Select the collider sub mesh and obtain its vert indices ===
#     bpy.ops.mesh.select_all(action='DESELECT')
#     oVertGrp_Cldr = oMeshBreastO.vertex_groups["_Area_BreastColL"]
#     oMeshBreastO.vertex_groups.active_index = oVertGrp_Cldr.index
#     bpy.ops.object.vertex_group_select()
#     bmBreast = bmesh.from_edit_mesh(oMeshBreastO.data)
#     aVertsCldrI = [oVert.index for oVert in bmBreast.verts if oVert.select]      # Obtain array of all collider verts (currently selected)
#     bpy.ops.object.mode_set(mode='OBJECT')                                      # FindClosestVert below requires object mode
# 
#     #=== Move the collider verts temporarily so proximity search won't find the same verts ===
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         oVert.co.x += 1.0;
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###LEARN: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
#     bpy.ops.object.mode_set(mode='OBJECT')
# 
#     #=== Find the matching vert between breast and its collider submesh ===
#     print("=== Finding vert-to-vert mapping between breast collider and breast ===")
#     aMapBreastVertToColVerts_Cldr = []              # Create two arrays that will store the map between collider verts and breast verts.
#     aMapBreastVertToColVerts_Breast = []            
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         vecVert = oVert.co.copy()
#         vecVert.x -= 1.0                   # Remove the temp offset we applied in above loop
#         nVertClosest, nDistMin, vecVertClosest = gBlender.Util_FindClosestVert(oMeshBreastO, vecVert, .000001)
#         aMapBreastVertToColVerts_Cldr  .append(nVertCldr)
#         aMapBreastVertToColVerts_Breast.append(nVertClosest)
#         print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %6.4f" % (nVertCldr, nVertClosest, vecVert.x, vecVert.y, vecVert.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
#         #oVert.co = vecVertClosest                               # Set the collider vert exactly on the breast vert
# 
#     #=== Return the collider verts to their original positions ===
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         oVert.co.x -= 1.0;
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###LEARN: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oMeshBreastO["aMapBreastVertToColVerts_Cldr"]   = aMapBreastVertToColVerts_Cldr     # Store our map into breast mesh so ApplyOp can copy breast vert positions to each associated collider vert 
#     oMeshBreastO["aMapBreastVertToColVerts_Breast"] = aMapBreastVertToColVerts_Breast 


### Now class-based with modifiers stored in code
# def Breasts_GetMorphList():         ####OBS??? # Send serialized list of the morph-oriented vertex groups on this mesh.  (Those that can be modified with calls to Breasts_ApplyOp())  ####OBS???
#     oMeshO = bpy.data.objects["Breast"]             ###DESIGN: Use this edit-less technique with bmesh more!! 
#     bm = bmesh.new()                                ###LEARN: How to operate with bmesh without entering edit mode!
#     bm.from_object(oMeshO, bpy.context.scene)       ###DESIGN: Selection of body! 
#     oLayVertGrps = bm.verts.layers.deform.active
#     oBA = bytearray()
# 
#     #=== Iterate through all groups marked as morph groups, calculate their center and send name and center to client ===
#     for oVertGrp in oMeshO.vertex_groups:
#         if oVertGrp.name.startswith(G.C_VertGrp_Morph):
#             sNameMorph = oVertGrp.name[len(G.C_VertGrp_Morph):] 
#             gBlender.Stream_SendStringPascal(oBA, sNameMorph)
#             #=== Calculate the center of this vertex group by iterating over its vertices ===
#             vecCenter = Vector();
#             nVertsInMorphGroup = 0
#             for oVert in bm.verts:
#                 if oVertGrp.index in oVert[oLayVertGrps]:
#                     vecCenter += oVert.co
#                     nVertsInMorphGroup += 1
#             vecCenter /= nVertsInMorphGroup
#             #print("-Morph '{}' at {}".format(sNameMorph, vecCenter))
#             gBlender.Stream_SendVector(oBA, G.VectorB2C(vecCenter))            # We send Blender 3D coord to Client so we must convert space
#     return oBA              # Return raw byte array back to client so it can deserialize our binary message



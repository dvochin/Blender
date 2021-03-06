import bpy
import sys
import bmesh
import struct
import array
##import CBBodyCol
import CBody

from math import *
from mathutils import *

from gBlender import *
import G
import CObject


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BODY CREATION
#---------------------------------------------------------------------------    
####OBS
# def gBL_Body_CreateForMorph(sNameSrcBody, sNameGameBody, sNameGameMorph):     # Ultra-simple vesion of CBody's call to obtain body for morphing
#     #===== Begin the complex task of assembling the requested body by first creating a simple copy of source body for morphing =====    
# 
#     print("\n=== gBL_Body_CreateForMorph() sNameSrcBody:'{}' sNameGameBody:'{}' sNameGameMorph: '{}' ===".format(sNameSrcBody, sNameGameBody, sNameGameMorph))
# 
#     #=== Obtain references to all the source meshes needed ===
#     oMeshComboO = DuplicateAsSingleton(sNameSrcBody, sNameGameMorph, G.C_NodeFolder_Game, False)  ###TODO!!! Rename to MeshCombo??      ###DESIGN: Base skinned mesh on _Morph or virgin body??            
# 
#     #=== Cleanup the skinned mesh and ready it for Unity ===
#     VertGrp_RemoveNonBones(oMeshComboO, True)  # Remove the extra vertex groups that are not skinning related
#     Client_ConvertMeshForUnity(oMeshComboO, True)  # With the skinned body + skinned clothing mesh free of non-bone vertex groups, we can safely limit the # of bones per vertex to the Client limit of 4 and normalize all bone weights ===
# #     bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # Limit mesh to four bones each   ###CHECK: Possible our 'non-bone' vertgrp take info away???
# #     bpy.ops.object.vertex_group_normalize_all(lock_active=False)
#     bpy.ops.object.select_all(action='DESELECT')
# 
#     #=== Create the breast collider mapped to morphing body ===
#     if (sNameSrcBody.startswith('Woman')):    
#         sNamePairedMesh = sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBody"
#         CBBodyCol.SlaveMesh_Create(sNameSrcBody + G.C_NameSuffix_BreastCol + "-Source", sNamePairedMesh)      # Create the 'ToBody' collider straight from the source collider...
#         CBBodyCol.SlaveMesh_DoPairing(sNamePairedMesh, sNameGameMorph, 0.000001)         #... and do the pairing to the morph body so breast verts can follow body verts
# 
#     return ""


# def gBL_Body_Create(sNameGameBody, sNameSrcBody, sSex, sNameSrcGenitals, aCloths):
#     # Important & expensive top-level function that assembles a "BodyX" body the rest of the code will process.  It cobbles together a 'human body' like man, woman, shemale by joining and processing a male/female base mesh and some compatible genital mesh of various designs / topology
#     
#     print("\n=== gBL_Body_Create() NameGameBody:'{}' NameSrcBody:'{}' Sex: '{}'  NameSrcGenitals:'{}'   Cloth:'{}' ===".format(sNameGameBody, sNameSrcBody, sSex, sNameSrcGenitals, aCloths))
# 
#     oMeshBodySrcO = bpy.data.objects[sNameSrcBody]
# 
#     #=== Test to see if the requested body definition matches the cached copy and if so return as we have nothing to do ===
#     #sPropNameSrcBody = sNameGameBody + "-sNameSrcBody"                ####OBS?  Cache of any value??
#     #sPropNameSrcGenitals = sNameGameBody + "-sNameSrcGenitals"
#     #if bpy.context.scene.get(sPropNameSrcBody) == sNameSrcBody and bpy.context.scene.get(sPropNameSrcGenitals) == sNameSrcGenitals:
#     #    return G.DumpStr("gBL_Body_Create(): Returning cached copy.")
#     #bpy.context.scene[sPropNameSrcBody] = sNameSrcBody  # We have to do the work but write the args to possibly avoid doing this again next run
#     #bpy.context.scene[sPropNameSrcGenitals] = sNameSrcGenitals
# 
#     #=== Duplicate the source body (kept in the most pristine condition possible) and delete unwanted parts of its mesh so that we may attach the user-specified compatible meshes in instead ===    
#     oMeshBodyO = DuplicateAsSingleton(sNameSrcBody, sNameGameBody, G.C_NodeFolder_Game, False)  # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
#     sNameVertGroupToCutout = None
#     if sNameSrcGenitals.startswith("Vagina"):  # Woman has vagina and breasts (includes clothing area)
#         sNameVertGroupToCutout = "_Cutout_Vagina"
#     elif sNameSrcGenitals.startswith("Penis"):  # Man & Shemale have penis
#         sNameVertGroupToCutout = "_Cutout_Penis"
#     if sNameVertGroupToCutout is not None:
#         bpy.ops.object.mode_set(mode='EDIT')
#         VertGrp_SelectVerts(oMeshBodyO, sNameVertGroupToCutout)  # This vert group holds the verts that are to be soft-body simulated...
#         bpy.ops.mesh.delete(type='FACE')  # ... and delete the mesh part we didn't want copied to output body
#         bpy.ops.object.mode_set(mode='OBJECT')
# 
#     #=== Import and preprocess the genitals mesh and assemble into this mesh ===
#     oMeshGenitalsO = DuplicateAsSingleton(sNameSrcGenitals, "TEMP_Genitals", G.C_NodeFolder_Game, True)  ###TEMP!! Commit to file-based import soon!
# #     bpy.ops.import_scene.obj(filepath="D:/Src/EroticVR/Unity/Assets/Resources/Textures/Woman/A/Vagina/EroticVR/A/Mesh.obj")        ###HACK!!!: Path & construction of full filename!
# #     oMeshGenitalsO = bpy.context.selected_objects[0]        ###INFO: object importer will deactivate everything and select only the newly imported object
#     ###CHECK: Not needed? bpy.context.scene.objects.active = oMeshGenitalsO
#     bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings
# 
#     #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
#     oMeshBodyO.select = True
#     bpy.context.scene.objects.active = oMeshBodyO
#     bpy.ops.object.join()
#     VertGrp_SelectVerts(oMeshBodyO, sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
#     bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###INFO: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
# 
#     #=== Temporarily rename some vertex groups that we need to preserve intact before they get clobbered by the upcoming call to transfer_weight() (If we didn't do that the quality suffers and several verts in the original don't transfer ===
#     if "_Detach_Breasts" in oMeshBodyO.vertex_groups: 
#         oMeshBodyO.vertex_groups["_Detach_Breasts"].name = "_Detach_Breasts_ORIGINAL"  ###IMPROVE: A bit of a hack workaround but I can't find any easier way to preserve this info...        
# 
#     #=== Reskin the body from the original body mesh now that all body parts have been merged onto the same mesh... This is essential for our previous-unskinned combination mesh (that possibly had a sex change) to regain skinning info from base body so that it can in-turn skin clothing we need to add next.   (Re-skinning is a hugely important benefit that Blender brings us) ===
#     oMeshBodySrcO.select = True
#     oMeshBodySrcO.hide = False  ###INFO: Mesh MUST be visible for weights to transfer!
#     bpy.ops.object.vertex_group_transfer_weight()  ###OPT!! Very expensive call!
# 
#     #=== Now that the expensive weight transfer is done, ditch the vertex groups that are of lesser quality and restore to the ones we saved ===
#     if "_Detach_Breasts" in oMeshBodyO.vertex_groups: 
#         oMeshBodyO.vertex_groups["_Detach_Breasts"].name = "_Detach_Breasts_TRANSFERED"        
#         oMeshBodyO.vertex_groups["_Detach_Breasts_ORIGINAL"].name = "_Detach_Breasts"        
# 
#     #=== Prepare a ready-for-morphing client-side body. This one will be morphed by the user and be the basis for cloth fitting and play mode ===   
#     oMeshMorphO = DuplicateAsSingleton(oMeshBodyO.name, sNameGameBody + G.C_NameSuffix_Morph, G.C_NodeFolder_Game, True)  ###DESIGN!!! ###SOON!!
#     Client_ConvertMeshForUnity(oMeshMorphO, True)  # Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
#     oMeshBodySrcO.hide = True  # Hide back the source body as more realized bodies are now shown.
# 
#     #return G.DumpStr("OK: gBL_Body_CreateMorphBody() NameBaseID:'{}'  NameSrcBody:'{}'  NameSrcGenitals:'{}'".format(sNameBaseID, sNameSrcBody, sNameSrcGenitals))
#     ###DESIGN?? ###CHECK: Remove extra bones from morphing body???
# 
# 
#     ####NOTE: Now merged def gBL_Body_Create(sNameGameBody, sSex, sNameSrcGenitals, aCloths):  
#     ###IMPROVE: Get most of these args from morphed body!?
#     ###IMPROVE!! Detached breasts and penis still contain extra materials & vert groups... clean up?
#     ###HACK!!!!! Breast morphs in this call!  Needs to be broken up and done differently!!
#     ###OBS!?!?!?!: If we always get dynamic clothing ontop of breasts then why the extreme complexity of this function???
# 
#     #=== Assemble the list of meshes we have to create based on the sex of the character ===
#     if sSex == "Woman":      # Woman has vagina and breasts (includes clothing area)
#         aNameChunks = ["Breasts", "VaginaL", "VaginaR"]
#     elif sSex == "Man":       # Shemale has breasts, penis and penis area clothing
#         aNameChunks = ["Penis"]
#     elif sSex == "Shemale":       # Shemale has breasts, and penis
#         aNameChunks = ["Breasts", "Penis"]
# 
# 
#     #===== Begin the complex task of assembling the requested body =====    
#     #=== Obtain references to all the source meshes needed ===
#     oMeshMorphO = SelectObject(sNameGameBody + G.C_NameSuffix_Morph)  # Obtain reference to previously constructed body for morphing
#     sNameBodyRim = sNameGameBody + G.C_NameSuffix_BodyRim
#     DeleteObject(sNameBodyRim)
#     oMeshComboO = DuplicateAsSingleton(oMeshMorphO.name, sNameGameBody + G.C_NameSuffix_BodySkin, G.C_NodeFolder_Game, False)  ###TODO!!! Rename to MeshCombo??      ###DESIGN: Base skinned mesh on _Morph or virgin body??            
#     nBodyMats = len(oMeshComboO.data.materials)  # Before we join additional clothing meshes with to body remember the number of materials so we can easily spot the vertices of clothing in big loop below
# 
# 
#     #=== Prepare the cloth base by duplicating the requested bodysuit and converting for Client ===  ####OBS?  Only if cloth is split for some simulation with breasts soft body
#     for sCloth in aCloths:
#         if sCloth != "" and sCloth != "None":
#             oMeshClothBaseO = DuplicateAsSingleton(sCloth, sNameGameBody + G.C_NameSuffix_ClothBase, G.C_NodeFolder_Game, True)            
#             DuplicateAsSingleton(oMeshClothBaseO.name, sNameGameBody + G.C_NameSuffix_ClothCut, G.C_NodeFolder_Game, True)  ###HACK!: Just to enable gameplay mode all the way to play without going through cloth morph or cloth fit... revisit this crap!            
#             DuplicateAsSingleton(oMeshClothBaseO.name, sNameGameBody + G.C_NameSuffix_ClothFit, G.C_NodeFolder_Game, True)            
#             oMeshClothO = DuplicateAsSingleton(sNameGameBody + G.C_NameSuffix_ClothFit  , "_TEMP_ClothPart-Body", G.C_NodeFolder_Game, True)  ###DESIGN: Pass in cloth by array?  Support array iteration ###DESIGN: ###SOON: This is ALL clothing on the character, not just fit!
#         
#             #=== Remove information from all-cloth Client doesn't need (such as the vertex groups used for border creation) ===
#             SelectObject(oMeshClothO.name)
#             Util_ConvertToTriangles()
#             if bpy.ops.object.vertex_group_remove.poll():
#                 bpy.ops.object.vertex_group_remove(all=True)
#         
#             #=== Split the edges on the all-cloth marked as 'sharp' (such as between border and cloth) to give two verts for each border vert with two different normals ===
#             oModEdgeSplit = oMeshClothO.modifiers.new('EDGE_SPLIT', 'EDGE_SPLIT')
#             oModEdgeSplit.use_edge_sharp = True  # We only want edge split to split edges marked as sharp (done in border creation)
#             oModEdgeSplit.use_edge_angle = False
#             AssertFinished(bpy.ops.object.modifier_apply(modifier=oModEdgeSplit.name))
#             
#             #=== Transfer the skinning information from the skinned body mesh to the clothing.  Some vert groups are useful to move non-simulated area of cloth as skinned cloth, other _Detach_xxx vert groups are to define areas of the cloth that are simulated ===
#             SelectObject(oMeshClothO.name)
#             oMeshMorphO.select = True
#             oMeshMorphO.hide = False  ###INFO: Mesh MUST be visible for weights to transfer!
#             bpy.ops.object.vertex_group_transfer_weight()
#         
#             #=== Join the all-cloth onto the main skinned body to form the composite mesh that currently has all geometry for body and all clothing...  From this composite mesh we separate 'chunks' such as breasts are surrounding clothing, or penis or vagina for non-skinned simulation by the game engine ===
#             SelectObject(oMeshComboO.name)
#             oMeshClothO.select = True
#             bpy.ops.object.join()  # This will join the cloth and its properly-set 'detach chunk' vertex groups to the body with matching chunk vertex groups.
#             oMeshClothO = None  # Past this point clothing mesh doesn't exist... only oMeshComboO which has entire body and all clothing
# 
# 
#     #=== Prepare the composite mesh for 'twin vert' mapping: The map that tells Client what vert from this detached chunk match what vert from the main skinned body ===
#     bpy.ops.object.mode_set(mode='EDIT')
#     bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)  # Create a 'custom data layer' to store unique IDs into mesh vertices so matching parts of the chunks we separate into other meshes can be easily matched to the main skinned mesh (for Client pinning)
#     oLayRimVerts = bmCombo.verts.layers.int.new(G.C_DataLayer_TwinID)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###INFO: This call causes BMesh references to be lost, so do right after getting bmesh reference
#     nNextRimVertID = 1  # We set the next twin vert ID to one.  New IDs for all detachable chunks will be created from this variable by incrementing.  This will enable each detached chunk to find what skinned vert from the body it needs to connect to during gameplay.
#     aaMapTwinId2VertChunk = {}  # Map of maps we use to enable aMapTwinId2VertChunk to traverse the major loop that creates it to another loop at the end that needs it.
# 
# 
#     #===== For woman & vagina, perform pre-processing of the vagina-area of the mesh.  We must split that part of the mesh into the '_Detach_VaginaL' and '_Detach_VaginaR' for the main loop below to properly detach the left&right vagina meshes for proper PhysX softbody processing =====
#     if sSex == "Woman":         ####OBS?? Go for non-softbody vagina now??
#         SelectObject(oMeshComboO.name)
#         bpy.ops.object.mode_set(mode='EDIT')
#         bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
#         nVertGrpIndex_Vagina = oMeshComboO.vertex_groups.find(G.C_VertGrp_Area + "Vagina")  # Find the rough-cut vagina-area part of our combo mesh that previous 'transfer_weight()' has transfered from source skinned body to our combo mesh       
#         if nVertGrpIndex_Vagina == -1:
#             raise Exception("###EXCEPTION: gBL_Body_Create() could not find Vagina vertex group in combo mesh!")
#         oVertGroup_Vagina = oMeshComboO.vertex_groups[nVertGrpIndex_Vagina]
#         oMeshComboO.vertex_groups.active_index = oVertGroup_Vagina.index
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.object.vertex_group_select()
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')  # Expand the rough-cut verts into faces (so any found vert selects any attached face) to avoid cutting away faceless geometry
#         ###bpy.ops.mesh.select_less()                                                      # Select less than original body has as we deliberately overshoot its selection to produce a 'less jagged' result after vertex group transfer between source mesh and our combo mesh
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='VERT')  ###INFO: Changing mode while expanding is an excellent / easy way to smooth out a selection
#         
#         #=== Find the edges that would split the vagina into left and right halves.  To do this we store the edges at the boundary of the entire vagina, we compute the boundary edges on the left side and we subtract the 2nd from the 1st
#         aVertsVagina = [oVert for oVert in bmCombo.verts if oVert.select]  # Store vagina verts for quicker iteration below (True?)
#         bpy.ops.mesh.region_to_loop()  # Select the edges at the boundary of the vagina.
#         aEdgesVaginaBoundary = [oEdge for oEdge in bmCombo.edges if oEdge.select]  # Remember the vagina boundary edges so we can remove them from left-half boundary (thereby leaving only the edges that can split left & right)
#     
#         #=== Unselect the right part of the vagina so we can compute its boundary edges and finally determine the edges between the two halves ===
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#         bpy.ops.mesh.select_all(action='DESELECT')
#         for oVert in aVertsVagina:  # Reselect left vagina half only
#             if oVert.co.x >= 0:
#                 oVert.select_set(True)
#         bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')  ###INFO:  Yes... all these damn mode changes are a must to convert selection from one domain to another!  (Extend in this case a must as we're going from low-order selection (verts) to a higher order (edges)
#         bpy.ops.mesh.region_to_loop()  # Select the edges at the boundary of the left vagina half
#     
#         #=== Remove the edges found at the boundary of the entire Vagina.  This will leave only the edges between the two halves selected
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#         for oEdgeVaginaBoundary in aEdgesVaginaBoundary:
#             oEdgeVaginaBoundary.select_set(False)
#         
#         #=== Create a temporary new vertex group to store the verts of the vagina L/R split (unfortunately mesh.edge_split() loses selection!)  ===
#         bpy.ops.object.mode_set(mode='OBJECT')  # Wished there were a way to create & assign to a vert group without leaving edit mode...
#         aVertsVaginaSplit = [oVert.index for oVert in oMeshComboO.data.vertices if oVert.select]
#         oVertGroup_TempVaginaSplit = oMeshComboO.vertex_groups.new(name="TempVaginaSplit")
#         oVertGroup_TempVaginaSplit.add(index=aVertsVaginaSplit, weight=1.0, type='REPLACE')
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#         bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
#     
#         #=== Split the vagina about its left/right split point and create additional geometry so game runtime has non-empty polygons to fully skin and thereby act as CPinSkinned for the neighboring softbody particles.    
#         bpy.ops.mesh.edge_split()  # Split edges: Each half of the vagina has polygons that go right up to the left/right split point now.
#         bpy.ops.object.vertex_group_select()  # Reselect edges as edge_split() above unfortunately loses selection! (Fortunately vert group expanded to contain the new edges just created)
#         bpy.ops.mesh.vertices_smooth()  # Perform a temporary smooth on the just-opened mesh.  This will pull newly-boundary verts away from each other (toward their closest polygons) so we form a very thin ribbon that will remain on the skinned body to provide anchors for CPinSkinned
#     
#         #=== Deselect the extremities of the just-created mesh hole so we can use 'bridge_edge_loops()' to construct polygons between the just-split meshes ===
#         nVertHighestY = -sys.float_info.max  # Highest Y vert is the vert in the vagina split line that is most toward the navel 
#         nVertLowestZ = sys.float_info.max  # Lowest  Z vert is the vert in the vagina split line that is most toward the anus
#         for oVert in bmCombo.verts:  ###NOTE: Bit of weak code here with this stupid business of having to remove two verts so we can use bridge_edge_loop() but that call is by far the most suitable one as it doesn't damage the UV/material!  (otherwise mesh.fill() would have been far better as it doesn't leave two holes!)  
#             if oVert.select:
#                 if  nVertHighestY < oVert.co.y:
#                     nVertHighestY = oVert.co.y  ###URGENT! This stuff based on vert smooth damages UVs!  Leave it as is and iterate through verts to find their tangent to set their small offset!
#                     oVertHighestY = oVert  ### Also that triangle missing is crap!  Try to fix selection so it's more contiguous
#                 if  nVertLowestZ > oVert.co.z:
#                     nVertLowestZ = oVert.co.z
#                     oVertLowestZ = oVert
#                 if (oVert.co.x > 0):  # Bring the slightly separated verts we split apart with 'vertices_smooth()' above much closer together so we only have a tiny band... just enough to not be zero and have a valid normal
#                     oVert.co.x = 0.000001  # If we go too close normal for these tiny slivers of polygons won't be accurate and mesh will look horrible in that area!
#                 else:
#                     oVert.co.x = -0.000001  ###IMPROVE: Would be nice to fix UVs too 
#         for oEdge in oVertHighestY.link_edges:  ###INFO: Selected higher-order geometry like edges & (even higher) polygons is a huge hassle!  Deselecting verts won't deselect edges & polys as they keep their own independent set
#             oEdge.select_set(False)
#         for oEdge in oVertLowestZ.link_edges:
#             oEdge.select_set(False)
#         bpy.ops.mesh.bridge_edge_loops()  # Finally we can join back the open part of the mesh... ###WEAK: Note that we leave an open face near the two up & down verts we just deselected above!!
#         bpy.ops.mesh.quads_convert_to_tris()  # For some weird reason if we don't tesselate the few new faces we just created the rest of the pipeline won't tesselate before client gets the mesh and it will fail!
#         
#         #=== Determine the left vagina verts first by position, then by removing verts from split point, then expanding one ring of verts (best way I found to quickly tell apart the left/right verts at same position for split point) ===
#         oMeshComboO.vertex_groups.active_index = oVertGroup_Vagina.index  # Reselect all the vagina verts so that we can define the L/R vertex groups that the main loop below needs to properly separate from the body for softbody runtime processing
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.object.vertex_group_select()
#         for oVert in bmCombo.verts:
#             if oVert.select == True and oVert.co.x < 0:
#                 oVert.select_set(False)
#         oMeshComboO.vertex_groups.active_index = oVertGroup_TempVaginaSplit.index  # Deselect the slit verts from the vagina half verts
#         bpy.ops.object.vertex_group_deselect()
#         bpy.ops.mesh.select_more()  # Now that we unselected the split point verts (that have same pos regardless of left/right), select one more ring of verts will select the split point verts on the right side of our mesh part
#         aVertsVaginaL = [oVert.index for oVert in bmCombo.verts if oVert.select]  # Store the indices of the verts so we can define vert group below
#     
#         #=== Do the same for the right vagina verts... Determine the right vagina verts first by position, then by removing verts from split point, then expanding one ring of verts (best way I found to quickly tell apart the left/right verts at same position for split point) ===
#         oMeshComboO.vertex_groups.active_index = oVertGroup_Vagina.index  # Reselect all the vagina verts so that we can define the L/R vertex groups that the main loop below needs to properly separate from the body for softbody runtime processing
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.object.vertex_group_select()
#         for oVert in bmCombo.verts:
#             if oVert.select == True and oVert.co.x > 0:
#                 oVert.select_set(False)
#         oMeshComboO.vertex_groups.active_index = oVertGroup_TempVaginaSplit.index  # Deselect the slit verts from the vagina half verts
#         bpy.ops.object.vertex_group_deselect()
#         bpy.ops.mesh.select_more()  # Now that we unselected the split point verts (that have same pos regardless of left/right), select one more ring of verts will select the split point verts on the right side of our mesh part  (Bit weak to do this but all we have to do is select one less in original body to avoid expanding too much)
#         aVertsVaginaR = [oVert.index for oVert in bmCombo.verts if oVert.select]  # Store the indices of the verts so we can define vert group below
#     
#         #=== Create the vagina left and right vertex groups for the main loop below ===    
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.object.mode_set(mode='OBJECT')  # Wished there were a way to create & assign to a vert group without leaving edit mode...
#         oVertGroup_VaginaL = oMeshComboO.vertex_groups.new(name=G.C_VertGrp_CSoftBody + "VaginaL")
#         oVertGroup_VaginaL.add(index=aVertsVaginaL, weight=1.0, type='REPLACE')
#         oVertGroup_VaginaR = oMeshComboO.vertex_groups.new(name=G.C_VertGrp_CSoftBody + "VaginaR")
#         oVertGroup_VaginaR.add(index=aVertsVaginaR, weight=1.0, type='REPLACE')
#         
#         #=== Remove the temp vertex group... (Keeping it would badly break the skinning info!!) ===
#         oMeshComboO.vertex_groups.active_index = oVertGroup_TempVaginaSplit.index
#         bpy.ops.object.vertex_group_remove()
#         ###CHECK: The abrupt break in geometry around the new collapse point throws off vertex normals for the entire slit...  Does this affect the client??  Do we need to split verts??  (Would that work with softbody??)
# 
#     
#     #===== MAIN SEPERATION PROCESSING FOR EACH 'SEPERABLE CHUNKS' =====  Breasts take ownership of clothing around them to be processed on their mesh as softbody.  Penis and vagina need processing here to to cap, twin and separate
#     for sNameChunk in aNameChunks:
#         print("--- Separating chunk " + sNameChunk)
#         sNamePartChunk = sNameGameBody + G.C_VertGrp_CSoftBody + sNameChunk
#         DeleteObject(sNamePartChunk)
#         SelectObject(oMeshComboO.name)
#         bpy.ops.object.mode_set(mode='EDIT')
#         bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
# 
#         #=== Obtain the 'detach chunks' vertex group from the combo mesh that originally came from the source body.  This 'detach chunk' will be updated for chunks such as breasts to append to it the verts of neighboring clothing so they will also be softbody simulated  ===
#         nVertGrpIndex_DetachChunk = oMeshComboO.vertex_groups.find(G.C_VertGrp_CSoftBody + sNameChunk)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
#         if nVertGrpIndex_DetachChunk == -1:
#             oMeshComboO.vertex_groups.new(name=G.C_VertGrp_CSoftBody + sNameChunk)
#         oVertGroup_DetachChunk = oMeshComboO.vertex_groups[nVertGrpIndex_DetachChunk]
#         oMeshComboO.vertex_groups.active_index = oVertGroup_DetachChunk.index
#     
#         #=== For non-body detach areas such a clothing around breasts and dynamic cloth around penis, refine the clothing area that is be non-skinned / simulated by selecting vertices by pre-defined bounding spheres (set individually for each type) ===
#         if sNameChunk == "Breasts" or sNameChunk == "PenisArea":  # Breasts and PenisArea area are the two 'detach chunk' that can have cloth around them that must take part in external simulation.  'Refine' their selection below...
#             bpy.ops.mesh.select_all(action='DESELECT')
#             bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
#             oCutSphere = bpy.data.objects["CutSphere-" + sNameChunk]  ###CHECK!            ###IMPROVE?: Cut sphere for penis changes with starting position of penis?? (Not if starts straight as soft body!)
#             vecSphereCenterL = oCutSphere.location.copy()  ###INFO: If we don't copy next line moves sphere!!
#             vecSphereCenterR = vecSphereCenterL.copy()  ###INFO: If we don't copy, next line inverts x on both vectors!
#             vecSphereCenterR.x = -vecSphereCenterR.x  # The '2nd' sphere is just the sphere #1 mirrored about x
#             vecSphereCenterC = (vecSphereCenterL + vecSphereCenterR) / 2 
#             nSphereRadius = oCutSphere.dimensions.x / 2
#             bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  ###INFO: If View3D were in any other mode the following code would NOT select!!  WTF???
#             for oVert in bmCombo.verts:
#                 if oVert.link_faces[0].material_index >= nBodyMats:  # We're only interested in non-body verts for cloth area-detection.  (Body already has well formed vert groups for these chunks.)
#                     vecVert = oMeshComboO.matrix_world * oVert.co                                   
#                     vecVertToSphereCenterL = vecVert - vecSphereCenterL
#                     vecVertToSphereCenterR = vecVert - vecSphereCenterR
#                     vecVertToSphereCenterC = vecVert - vecSphereCenterC
#                     if vecVertToSphereCenterL.magnitude < nSphereRadius or vecVertToSphereCenterR.magnitude < nSphereRadius or vecVertToSphereCenterC.magnitude < nSphereRadius:
#                         oVert.select_set(True)
#             bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')  # We expand the selection of verts to faces to ensure we don't cut out verts left hanging by an edge
#             aVertsDetachChunk = [oVert.index for oVert in bmCombo.verts if oVert.select]
#             bpy.ops.object.mode_set(mode='OBJECT')
#             oVertGroup_DetachChunk.add(index=aVertsDetachChunk, weight=0.0, type='REPLACE')  # Add the verts to be detached from cloth to the appropriate detach vert group with weight zero (so it doesn't interfere with bones)
# 
#         #=== Detach the currently-processed 'chunk' from the source composite mesh.  One chunk for each separate softbody/cloth simulation ===
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
#         bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)  ###INFO!!: We must re-obtain new bmesh everytime we re-enter edit mode.  (And of course old bmesh object references are gone but IDs persist!)
#         oLayRimVerts = bmCombo.verts.layers.int[G.C_DataLayer_TwinID]  # Refetch our custom data layer because we exited edit mode...
#         aFacesToSplit = [oFace for oFace in bmCombo.faces if oFace.select]  # Obtain array of all faces to separate
#     
#         #=== Store the boundary edges of the split into the new vertex group so we can provide Client the mapping of split verts between the meshes ===
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#         bpy.ops.mesh.region_to_loop()  # This will select only the edges at the boundary of the cutout polys... including edge of cloth, seams and the (needed) edges that connect split mesh to main mesh
#         for oEdge in bmCombo.edges:  # Iterate over the edges at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut
#             if oEdge.select == True:
#                 if oEdge.is_manifold == False:  # Deselect the edges-on-edge (i.e. natural edge of cloth)
#                     oEdge.select_set(False)
#         ###HACK ###IMPROVE ###DESIGN: Important limitation of the above code appears when attempting to separate Penis at its natural mesh boundary (at the endge of its material)
#         ### Because we need to separate from the Client-ready morphed body, the penis mesh in that mesh is already separated from main skinned mesh at its material boundary...  Making this call's attempt to twin verts impossible.
#         ### A hack was adopted by setting the 'seperatable mesh' of penis one ring of vertices less than its materials, so that this code can twin verts and the runtime to attach softbody penis to skinned main body mesh.
#         ### An improvement could be created to enable traversal of the duplicated verts because of material and properly twin the penis mesh verts to the verts that are really on the skinned body mesh.
#     
#         #=== Iterate over the split verts to store a uniquely-generated 'twin vert ID' into the custom data layer so we can re-twin the split verts from different meshes after the mesh separate ===
#         aVertsBoundary = [oVert for oVert in bmCombo.verts if oVert.select]
#         for oVert in aVertsBoundary:
#             oVert[oLayRimVerts] = nNextRimVertID  # These are unique to the whole skinned body so all detached chunk can always find their corresponding skinned body vert for per-frame positioning
#             nNextRimVertID += 1
#     
#         #=== Reselect the faces again to split the 'detachable chunk' into its own mesh so that it can be sent to softbody/cloth simulation.  ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
#         bChunkMeshHasGeometry = False  # Determine if chunk mesh has any faces
#         for oFace in aFacesToSplit:
#             oFace.select_set(True)
#             bChunkMeshHasGeometry = True
#     
#         #=== If chunk mesh has no geometry then we don't generate it as client has nothing to render / process for this chunk ===
#         if bChunkMeshHasGeometry == False:
#             print("\n>>> GameMode_Play_PrepBody() skips creation of chunk mesh '{}' from body '{}' because it has no geometry <<<".format(sNameChunk, sNameGameBody))
#             continue
#     
#         #=== Split and separate the chunk from the composite mesh ===
#         bpy.ops.mesh.split()  # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
#         bpy.ops.mesh.separate()  # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
#     
#         #===== Post-process the just-detached chunk to calculate the 'twin verts' array between it and the main skinned main body =====
#         #=== Fetch the just-split body part + cloths 'detach chunk' so we can calculate 'matching' information to 'twin' the previously connected verts together (to pin a simulated area of mesh to the skinned mesh) ===    
#         bpy.ops.object.mode_set(mode='OBJECT')
#         bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#         bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
#         oMeshPartChunkO = bpy.context.object 
#         oMeshPartChunkO.name = oMeshPartChunkO.data.name = sNamePartChunk  ###NOTE: Do twice so name sticks!
#         oMeshPartChunkO.name = oMeshPartChunkO.data.name = sNamePartChunk
#         bpy.ops.object.vertex_group_remove(all=True)  # Remove all vertex groups from detached chunk to save memory
#     
#         #=== Iterate through the verts of the newly separated chunk to access the freshly-created custom data layer to obtain ID information that enables us to match the chunk mesh vertices to the main skinned mesh for pinning ===
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#         bmPartChunk = bmesh.from_edit_mesh(oMeshPartChunkO.data)
#         oLayRimVerts = bmPartChunk.verts.layers.int[G.C_DataLayer_TwinID]
#         aMapTwinId2VertChunk = {}
#         for oVert in bmPartChunk.verts:  ###INFO: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
#             nTwinID = oVert[oLayRimVerts]
#             if nTwinID != 0:
#                 aMapTwinId2VertChunk[nTwinID] = oVert.index
#                 if oVert.link_faces[0].material_index < nBodyMats:  # For capping below, select only the twin verts that are on one of the body's original material
#                     oVert.select_set(True)
#                 # print("TwinVert {:3d} = PartVert {:5d} mat {:} at {:}".format(nTwinID, oVert.index, oVert.link_faces[0].material_index, oVert.co))
#         aaMapTwinId2VertChunk[sNameChunk] = aMapTwinId2VertChunk  # Store our result in top-level map so loop near end of this function can finish the work once whole rim has been created.
#         
#         #=== Cap the body part that is part of the chunk (edge verts from only that body part are now selected)  If this chunk has no body verts (e.g. PenisClothing) then no capping will occur) ===
#         bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')  ###BUG?? ###CHECK: Possible that edge collapse could fail depending on View3D mode...
#         bpy.ops.mesh.extrude_edges_indiv()  ###INFO: This is the function we need to really extrude!
#         bpy.ops.mesh.edge_collapse()  ###DESIGN ###IMPROVE Do we always cap whatever body part is ripped out?
#         for oVert in bmPartChunk.verts:  # The cap vert(s) created will have copied one of the 'VertTwinID'.  Wipe it out to avoid corrupting matching below 
#             if oVert.select:
#                 oVert[oLayRimVerts] = 0
#         bpy.ops.mesh.select_all(action='DESELECT')
# 
#         #=== Do the important conversion of the chunk mesh to be renderable by the Client... we're done processing that mesh. ===
#         Client_ConvertMeshForUnity(oMeshPartChunkO, True)
# 
# 
#     #===== Create the 'Skinned Rim' skinned mesh that Client can use to use 'BakeMesh()' on a heavily-simplified version of the main body mesh that contains only the 'rim' polygons that attach to all the detacheable chunks this code separates.  It is this 'Rim' skinned mesh that quickly calculates the position of all the pins and that therfore 'owns' the CPinSkinned and therefore the CPinTetra === 
#     ####DESIGN: Vert topology changes at every split!  MUST map twinID to body verts once all cuts done ###NOW!!!
#     #=== Iterate through the verts of the main skinned mesh (now that all chunks have been removed) to select all the twin verts so we can create the rim mesh
#     SelectObject(oMeshComboO.name)
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#     bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
#     oLayRimVerts = bmCombo.verts.layers.int[G.C_DataLayer_TwinID]
#     for oVert in bmCombo.verts:
#         nTwinID = oVert[oLayRimVerts]
#         if nTwinID != 0:
#             oVert.select_set(True)  # Select this edge boundary vertex for the upcoming code in which we expand the rim selection to create the rim submesh
# 
#     #=== Select the faces neighboring the twin verts and duplicate them into the new 'rim mesh'
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='EDGE')  # ... With the rim verts selected two loops ago expand these 'boundary verts' into edge mode any edge touching the boundary verts are edges are selected (including non-boundary ones)...
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')  # ... then switch to poly mode to have the smallest set of polygons that have an edge at the boundary are left selected.  These will form their own 'reduced skin mesh' that will be baked at every frame to calculate pin positions
#     bpy.ops.mesh.duplicate()
#     bpy.ops.mesh.separate()  # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
#     bmCombo.verts.layers.int.remove(oLayRimVerts)  # Remove the temp data layer in the skin mesh as the just-separated mesh has the info now...
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
# 
#     #=== Fetch the just-created 'rim' skinned mesh and set it to its proper name ===
#     bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#     bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
#     oMeshSkinColSrcO = bpy.context.object 
#     oMeshSkinColSrcO.name = oMeshSkinColSrcO.data.name = sNameBodyRim  ###NOTE: Do it twice to ensure name really sticks  ###WEAK: Wish this was easier to do!
#     oMeshSkinColSrcO.name = oMeshSkinColSrcO.data.name = sNameBodyRim
#     del(oMeshSkinColSrcO[G.C_PropArray_MapSharedNormals])  # Source skinned body has the shared normal array which is not appropriate for rim.  (Serialization would choke)
# 
#     #=== Cleanup the rim mesh by removing all materials ===
#     while len(oMeshSkinColSrcO.material_slots) > 0:  ###IMPROVE: Find a way to remove doubles while preventing key-not-found errors in twin hunt below??
#         bpy.ops.object.material_slot_remove()
#     bpy.ops.object.material_slot_add()  # Add a single default material (captures all the polygons of rim) so we can properly send the mesh over (crashes if zero material)
#     
#     #=== Iterate over the rim vertices, and find the rim vert for every 'twin verts' so next loop can map chunk part verts to rim verts for pinning === 
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bmSkinColSrc = bmesh.from_edit_mesh(oMeshSkinColSrcO.data)
#     oLayRimVerts = bmSkinColSrc.verts.layers.int[G.C_DataLayer_TwinID]
#     aMapTwinId2VertRim = {}
#     for oVert in bmSkinColSrc.verts:
#         nTwinID = oVert[oLayRimVerts]
#         if nTwinID != 0:
#             oVertAdjacent = oVert.link_edges[0].other_vert(oVert)  # Find an 'adjacent vert' to this twin vert so that Client pin has the chance to fully orient the 'Z' of the normal of this pin so 'up' always points toward this adjacent vert (with 'LookAt' function)   ###IMPROVE: Would be nice to return an adjacent vert on boundary edge??
#             aMapTwinId2VertRim[nTwinID] = (oVert.index, oVertAdjacent.index)  # Store both the twin vert and an adjacent vert for this twin
#             # print("TwinVert {:3d} = RimVert {:5d}-{:5d} at {:}".format(nTwinID, oVert.index, oVertAdjacent.index, oVert.co))
#     bpy.ops.object.mode_set(mode='OBJECT')
#     VertGrp_RemoveNonBones(oMeshSkinColSrcO, True)  # Remove the extra vertex groups that are not skinning related
#     
#     #===== Now that rim is fully formed and the aMapTwinId2VertRim fully populated for to find real rim verts for any TwinID we can finally construct the aMapTwinVerts flat array for each detached part.  (each detached part (no matter if its softbody or cloth simulated) will thereby be able to fix its edge verts to the rim correctly during gameplay) (With both the main skinned mesh and the chunk part with the same set of 'twin ID' in their mesh vertices, we can finally match vertex ID of part to vertex ID of skinned main mesh)
#     ###NOTE: This flattened is sent with 1) vertex ID on the separated chunk part, 2) Vertex ID of the 'twin vert' at the same location on the main skinned mesh and 3) an adjacent vert on the skinned mesh to #2 for normal Z-orientation
#     aNameChunksCreated = []  ####OBS? # Append to this list the full names of the chunk meshes this call has created.  Client then fetch each of these in turns via Unity_GetMesh()
#     for sNameChunk in aNameChunks:
#         sNamePartChunk = sNameGameBody + G.C_VertGrp_CSoftBody + sNameChunk
#         if sNamePartChunk not in bpy.data.objects:  # Skip processing of this chunk if it wasn't created above.
#             continue
#         aNameChunksCreated.append(sNamePartChunk)  # Append name to list so client knows this chunk is available for gametime processing
#         oMeshPartChunkO = bpy.data.objects[sNamePartChunk]
#         aMapTwinVerts = array.array('H')  # The final flattened map of what verts from the 'detached chunk part' maps to what vert in the 'skinned main body'  Client needs this to pin the edges of the softbody-simulated part to the main body skinned mesh
#         aMapTwinId2VertChunk = aaMapTwinId2VertChunk[sNameChunk]  # Now that the full rim is known, fetch the map previously created for this chunk earlier in this function in our 'map of maps'
#         print("--- Mapping twinned verts on mesh chunk " + sNameChunk)  # + str(aMapTwinId2VertChunk))
#         # for nTwinID in range(1, len(aMapTwinId2VertChunk) + 1):
#         for nTwinID in aMapTwinId2VertChunk:
#             nVertTwinChunk = aMapTwinId2VertChunk[nTwinID]
#             if nTwinID in aMapTwinId2VertRim:
#                 aRimDef = aMapTwinId2VertRim[nTwinID]
#                 nVertTwinRim = aRimDef[0]
#                 nVertTwinRimAdjacent = aRimDef[1]
#                 aMapTwinVerts.append(nVertTwinChunk)
#                 aMapTwinVerts.append(nVertTwinRim)
#                 aMapTwinVerts.append(nVertTwinRimAdjacent)
#                 # print("TwinVert {:3d} = PartVert {:5d} = RimVert {:5d} & Adj {:5d}".format(nTwinID, nVertTwinChunk, nVertTwinRim, nVertTwinRimAdjacent))
#             else:
#                 G.DumpStr("ERROR in gBL_Body_Create(): Mapping of twin verts from TwinID to RimVert Could not find TwinID {} while processing chunk '{}' on mesh '{}' (Obscure corner-case algorithm error that rest of code can probably recover from...)".format(nTwinID, sNameChunk, oMeshComboO.name))  # Obscure corner case that appears with Vagina L/R... Perhaps because split-point verts are in same position??  Check if this influences the game... 
#         oMeshPartChunkO[G.C_PropArray_MapTwinVerts] = aMapTwinVerts.tobytes()  # Store the output map as an object property for later access when Client requests this part.  (We store as byte array to save memory as its only for future serialization to Client and Blender has no use for this info)
# 
#     #===== Cleanup the main skinned mesh =====
#     VertGrp_RemoveNonBones(oMeshComboO, True)  # Remove the extra vertex groups that are not skinning related
#     Client_ConvertMeshForUnity(oMeshComboO, True)  # With the skinned body + skinned clothing mesh free of non-bone vertex groups, we can safely limit the # of bones per vertex to the Client limit of 4 and normalize all bone weights ===
# #     bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # Limit mesh to four bones each   ###CHECK: Possible our 'non-bone' vertgrp take info away???
# #     bpy.ops.object.vertex_group_normalize_all(lock_active=False)
#     bpy.ops.object.select_all(action='DESELECT')
# 
#     #===== Copy and re-pair the breast collider for women to the newly detached breast mesh =====
#     if (sNameSrcBody.startswith('Woman')):    
#         sNameBreastColToBody    = sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBody"                  # These were generated when morphing body was created and have been moved along morphing body.
#         sNameBreastColToBreasts = sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBreasts"               #... so the just-detached breasts are at the exact same position... but we need to 're-pair' to the just-detached breasts so collider can now moving along with softbody breasts
#         DuplicateAsSingleton(sNameBreastColToBody, sNameBreastColToBreasts, G.C_NodeFolder_Game, True)     # 'ToBody' breast collider already paired to body for static morphing.  Now re-pair a new instance of breast collider onto newly created detached softbody breasts
#         CBBodyCol.SlaveMesh_DoPairing(sNameBreastColToBreasts, sNameGameBody + "_Detach_Breasts", 0.000001)                     # Redo the pairing to the morph body so breast verts can follow body verts
#     
# #     CBBodyCol.SlaveMesh_Define(sNameBreastColToBreasts, sNameGameBody + , sNameMeshOutput, nVertTolerance):
# #     //CBBodyCol.SlaveMesh_Define(sNameSrcBody + "-BreastCol-Source", sNameGameBody + "_Detach_Breasts", sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBreasts", 0.001)
#    
#     #gBL_Util_HideGameMeshes()     ###KEEP???
# 
#     #===== Return success message to client.  It will now request each of the processed meshes this call prepared and ship them to various engines such as softbody, clothing or skinned =====
#     ###OBS? return str(aNameChunksCreated)
#     return ""

def GameMode_ClothCut(sNameBody):  # Prepare for the cloth cut game mode -> Create a duplicate cloth mesh from its source
    DuplicateAsSingleton(sNameBody + G.C_NameSuffix_ClothBase, sNameBody + G.C_NameSuffix_ClothCut, G.C_NodeFolder_Game, True)
    return G.DumpStr("OK: GameMode_ClothCut() copied base '{}' into cut '{}'".format(sNameBody + G.C_NameSuffix_ClothBase, sNameBody + G.C_NameSuffix_ClothCut))

def GameMode_ClothFit(sNameBody):  # Prepare for the cloth fit game mode   
    DuplicateAsSingleton(sNameBody + G.C_NameSuffix_ClothCut, sNameBody + G.C_NameSuffix_ClothFit, G.C_NodeFolder_Game, True)
    return G.DumpStr("OK: GameMode_ClothFit() copied cut '{}' into fit '{}'".format(sNameBody + G.C_NameSuffix_ClothCut, sNameBody + G.C_NameSuffix_ClothFit))

def GameMode_ClothFit_End(sNameBody):  # Cleanup the Flex-simulated cloth.  Assumes Client uploaded its latest verts of this cloth before.
    SelectObject(sNameBody + G.C_NameSuffix_ClothFit)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth_laplacian(repeat=1, lambda_factor=0.005, lambda_border=0.000)  ###TUNE!
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return G.DumpStr("OK: GameMode_ClothFit_End('')".format())



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    UTILITY
#---------------------------------------------------------------------------    

    

def Unity_GetMesh_Array_OBSOLETE(sNameMesh, sNameArray):        #=== Send Unity the requested serialized bytearray of the previously-calculated custom property of mesh 'sNameMesh'
    oBA = CByteArray()

    oMeshO = SelectObject(sNameMesh)
    aArray = oMeshO.get(sNameArray)
    Stream_SerializeArray(oBA, aArray)

    return oBA.CloseArray()
    




def gBL_ReleaseMesh(sNameMesh):  # Release the python-side and blender-c-side structures for this shared mesh
    if sNameMesh in bpy.data.objects: 
        oMeshO = bpy.data.objects[sNameMesh]
        oMeshO.data.tag = False  ###IMPORTANT: Setting 'tag' on the mesh object and causes the next update to invoke our C-code modification of Blender share/unshare mesh memory to Client
        oMeshO.data.use_fake_user = False  ###NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.  Make sure this is off in this context
        oMeshO.data.update(True, True)  ###IMPORTANT: Causes our related Blender C code to kick in by reading the name of our mesh and acting upon the shared and unshared strings to share/unshare mesh memory to Client
        return G.DumpStr("OK: gBL_ReleaseMesh() on mesh '{}' succeeded.".format(sNameMesh))
    else:
        return G.DumpStr("ERROR: gBL_ReleaseMesh() could not find '{}' in scene!".format(sNameMesh))



def gBL_UpdateClientVerts(sNameMesh):  # Update only the Client verts from the Blender verts.  Most of the magic happens in our modified Blender C code while calling update()
    if (sNameMesh not in bpy.data.objects):     ###NOW######BROKEN???
        return G.DumpStr("ERROR: gBL_UpdateClientVerts() cannot find object '" + sNameMesh + "'")
    oMeshO = SelectObject(sNameMesh)
    oMeshO.data.use_fake_user = False  ###NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.  Make sure this is off in this context
    oMeshO.data.update(True, True)  ###IMPORTANT: Our modified Blender C code traps the above flags to update its shared data structures with client...        
    return G.DumpStr("OK: gBL_UpdateClientVerts() has updated Client mesh verts on mesh '{}'".format(sNameMesh))

def gBL_UpdateBlenderVerts(sNameMesh):  # Update the Blender verts from the Client verts.  Most of the magic happens in our modified Blender C code while calling update()
    if (sNameMesh not in bpy.data.objects):
        return G.DumpStr("ERROR: gBL_UpdateBlenderVerts() cannot find object '" + sNameMesh + "'")
    oMeshO = SelectObject(sNameMesh)
    oMeshO.data.use_fake_user = True        ###IMPORTANT: We turn on this flag to indicate to our Blender C code that we LOAD the verts from client (instead of sending arrays to client)  NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.
    oMeshO.data.update(True, True)          ###IMPORTANT: Our modified Blender C code traps the above flags to update its shared data structures with client...        
    oMeshO.data.use_fake_user = False       # Turn off the 'update Blender verts from Client' flag right away as it's created only for this call.
    return G.DumpStr("OK: gBL_UpdateBlenderVerts() has updated Blender mesh verts on mesh '{}'".format(sNameMesh))


###TODO?: Can see shape keys... all in absolute so need diff
# Need all shape keys at zero so we can read one shape key
# Why not 17K mesh???
# Then... store in array for C++, ship, ship head as mesh and morph in C++!  (Also construct struct for nipples!)



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    MAN MESH CLEANUP
#---------------------------------------------------------------------------    
#- From DAZ-exported man (no penis) with 'merge materials with common diffuse' on...
#- Unit scale on bones, then edit the bones and reduce 1/100
#- Unit scale on mesh, then edit the mesh verts and reduce 1/10000
#- Remove extra bones (ik)
#- Keep rotation as is (90x) on both root and mesh (like woman)

def ManCleanup_RemoveExtraMaterials():  # Remove extra materials from DAZ-imported man    
    #Material_Remove("Cornea")
    #Material_Remove("Sclera")
    Material_Remove("EyeSurface")
    #Material_Remove("Iris")
    #Material_Remove("Pupil")
    Material_Remove("Lacrimal")
    Material_Remove("Tear")
    Material_Remove("EyeSocket")
    Material_Remove("Eyebrow")
    Material_Remove("Eyelash")

    
#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CProp-based properties
#---------------------------------------------------------------------------    

# def CProp_PropGet(sNameObject, sNameProp):
#     if sNameObject not in bpy.data.objects:
#         return G.DumpStr("ERROR: CProp_PropGet('{}', '{}') cannot find object {}".format(sNameObject, sNameProp, sNameObject))
#     oObject = bpy.data.objects[sNameObject]
#     return oObject.get(sNameProp)
# 
# def CProp_PropSet(sNameObject, sNameProp, oValue):
#     if sNameObject not in bpy.data.objects:
#         return G.DumpStr("ERROR: CProp_PropSet('{}', '{}', {}) cannot find object {}".format(sNameObject, sNameProp, oValue, sNameObject))
#     oObject = bpy.data.objects[sNameObject]
#     oObject[sNameProp] = oValue
#     return "OK"
    
    
    
#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    TESTS
#---------------------------------------------------------------------------    

#oObjectMeshShapeKeys = None

def Test():
    bpy.ops.mesh.primitive_cube_add()
    return "OK"
    
    







#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    ####MOVE
#---------------------------------------------------------------------------    









###JUNK

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    HEAD PROCESSING
#---------------------------------------------------------------------------    
# def IsolateHead():  ###OBS? # DAZ cannot export only the head if we select the 17K level of detail mesh.  We remove materials and faces we don't need here to leave only the head    
#     Material_Remove("Neck")
#     Material_Remove("Torso")
#     Material_Remove("Nipple")
#     Material_Remove("Hip")
#     Material_Remove("Arm")
#     Material_Remove("Foot")
#     Material_Remove("Forearm")
#     Material_Remove("Hand")
#     Material_Remove("Leg")
#     Material_Remove("Fingernail")
#     Material_Remove("Toenail")
#     Material_Remove("Cornea")
#     Material_Remove("Sclera")
#     Material_Remove("EyeSurface")
#     Material_Remove("Iris")
#     Material_Remove("Pupil")
#     Material_Remove("Lacrimal")
#     Material_Remove("Tear")
#     Material_Remove("EyeSocket")
#     Material_Remove("Eyebrow")
    

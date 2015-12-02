###DISCUSSION: Blender Client-side processing 
### NEXT ### MAN
# _Cutout_Penis group
# which cock?  man crotch much narrower!  Cannot create adaptor!
# Hack remming out shemale
# Problem clearing game meshes (extra prop)

### TODO ###

### LATER ###

### DESIGN ###

### IDEAS ###

### LEARNED ###

### PROBLEMS ###
# How do we extract penis area from penis from obj file?  (only manifold verts?)
#+++ Re-evaluate usage of global scene args like sNameBody... will cause problem with multiple body!!
# Split chunks still have all materials... write utility function to remove unused materials!

### PROBLEMS: ASSETS ###

### PROBLEMS??? ###
    
### WISHLIST ###

import bpy
import sys
import bmesh
import struct
import array
import CBBodyCol
import CBody

from math import *
from mathutils import *

import gBlender
import G



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BODY CREATION
#---------------------------------------------------------------------------    
####OBS
def gBL_Body_CreateForMorph(sNameSrcBody, sNameGameBody, sNameGameMorph):     # Ultra-simple vesion of CBody's call to obtain body for morphing
    #===== Begin the complex task of assembling the requested body by first creating a simple copy of source body for morphing =====    

    print("\n=== gBL_Body_CreateForMorph() sNameSrcBody:'{}' sNameGameBody:'{}' sNameGameMorph: '{}' ===".format(sNameSrcBody, sNameGameBody, sNameGameMorph))

    #=== Obtain references to all the source meshes needed ===
    oMeshComboO = gBlender.DuplicateAsSingleton(sNameSrcBody, sNameGameMorph, G.C_NodeFolder_Game, False)  ###TODO!!! Rename to MeshCombo??      ###DESIGN: Base skinned mesh on _Morph or virgin body??            

    #=== Cleanup the skinned mesh and ready it for Unity ===
    gBlender.Cleanup_VertGrp_RemoveNonBones(oMeshComboO)  # Remove the extra vertex groups that are not skinning related
    Client_ConvertMesh(oMeshComboO, True)  # With the skinned body + skinned clothing mesh free of non-bone vertex groups, we can safely limit the # of bones per vertex to the Client limit of 4 and normalize all bone weights ===
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # Limit mesh to four bones each   ###CHECK: Possible our 'non-bone' vertgrp take info away???
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.select_all(action='DESELECT')

    #=== Create the breast collider mapped to morphing body ===
    if (sNameSrcBody.startswith('Woman')):    
        sNamePairedMesh = sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBody"
        CBBodyCol.PairMesh_Create(sNameSrcBody + G.C_NameSuffix_BreastCol + "-Source", sNamePairedMesh)      # Create the 'ToBody' collider straight from the source collider...
        CBBodyCol.PairMesh_DoPairing(sNamePairedMesh, sNameGameMorph, 0.000001)         #... and do the pairing to the morph body so breast verts can follow body verts

    return ""


def gBL_Body_Create(sNameGameBody, sNameSrcBody, sSex, sNameSrcGenitals, aCloths):
    # Important & expensive top-level function that assembles a "BodyX" body the rest of the code will process.  It cobbles together a 'human body' like man, woman, shemale by joining and processing a male/female base mesh and some compatible genital mesh of various designs / topology
    
    print("\n=== gBL_Body_Create() NameGameBody:'{}' NameSrcBody:'{}' Sex: '{}'  NameSrcGenitals:'{}'   Cloth:'{}' ===".format(sNameGameBody, sNameSrcBody, sSex, sNameSrcGenitals, aCloths))

    oMeshBodySrcO = bpy.data.objects[sNameSrcBody]

    #=== Test to see if the requested body definition matches the cached copy and if so return as we have nothing to do ===
    #sPropNameSrcBody = sNameGameBody + "-sNameSrcBody"                ####OBS?  Cache of any value??
    #sPropNameSrcGenitals = sNameGameBody + "-sNameSrcGenitals"
    #if bpy.context.scene.get(sPropNameSrcBody) == sNameSrcBody and bpy.context.scene.get(sPropNameSrcGenitals) == sNameSrcGenitals:
    #    return G.DumpStr("gBL_Body_Create(): Returning cached copy.")
    #bpy.context.scene[sPropNameSrcBody] = sNameSrcBody  # We have to do the work but write the args to possibly avoid doing this again next run
    #bpy.context.scene[sPropNameSrcGenitals] = sNameSrcGenitals

    #=== Duplicate the source body (kept in the most pristine condition possible) and delete unwanted parts of its mesh so that we may attach the user-specified compatible meshes in instead ===    
    oMeshBodyO = gBlender.DuplicateAsSingleton(sNameSrcBody, sNameGameBody, G.C_NodeFolder_Game, False)  # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
    sNameVertGroupToCutout = None
    if sNameSrcGenitals.startswith("Vagina"):  # Woman has vagina and breasts (includes clothing area)
        sNameVertGroupToCutout = "_Cutout_Vagina"
    elif sNameSrcGenitals.startswith("Penis"):  # Man & Shemale have penis
        sNameVertGroupToCutout = "_Cutout_Penis"
    if sNameVertGroupToCutout is not None:
        bpy.ops.object.mode_set(mode='EDIT')
        gBlender.Util_SelectVertGroupVerts(oMeshBodyO, sNameVertGroupToCutout)  # This vert group holds the verts that are to be soft-body simulated...
        bpy.ops.mesh.delete(type='FACE')  # ... and delete the mesh part we didn't want copied to output body
        bpy.ops.object.mode_set(mode='OBJECT')

    #=== Import and preprocess the genitals mesh and assemble into this mesh ===
    oMeshGenitalsO = gBlender.DuplicateAsSingleton(sNameSrcGenitals, "TEMP_Genitals", G.C_NodeFolder_Game, True)  ###TEMP!! Commit to file-based import soon!
#     bpy.ops.import_scene.obj(filepath="D:/Src/E9/Unity/Assets/Resources/Textures/Woman/A/Vagina/Erotic9/A/Mesh.obj")        ###HACK!!!: Path & construction of full filename!
#     oMeshGenitalsO = bpy.context.selected_objects[0]        ###LEARN: object importer will deactivate everything and select only the newly imported object
    ###CHECK: Not needed? bpy.context.scene.objects.active = oMeshGenitalsO
    bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings

    #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
    oMeshBodyO.select = True
    bpy.context.scene.objects.active = oMeshBodyO
    bpy.ops.object.join()
    gBlender.Util_SelectVertGroupVerts(oMeshBodyO, sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
    bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###LEARN: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    #=== Temporarily rename some vertex groups that we need to preserve intact before they get clobbered by the upcoming call to transfer_weight() (If we didn't do that the quality suffers and several verts in the original don't transfer ===
    if "_Detach_Breasts" in oMeshBodyO.vertex_groups: 
        oMeshBodyO.vertex_groups["_Detach_Breasts"].name = "_Detach_Breasts_ORIGINAL"  ###IMPROVE: A bit of a hack workaround but I can't find any easier way to preserve this info...        

    #=== Reskin the body from the original body mesh now that all body parts have been merged onto the same mesh... This is essential for our previous-unskinned combination mesh (that possibly had a sex change) to regain skinning info from base body so that it can in-turn skin clothing we need to add next.   (Re-skinning is a hugely important benefit that Blender brings us) ===
    oMeshBodySrcO.select = True
    oMeshBodySrcO.hide = False  ###LEARN: Mesh MUST be visible for weights to transfer!
    bpy.ops.object.vertex_group_transfer_weight()  ###OPT!! Very expensive call!

    #=== Now that the expensive weight transfer is done, ditch the vertex groups that are of lesser quality and restore to the ones we saved ===
    if "_Detach_Breasts" in oMeshBodyO.vertex_groups: 
        oMeshBodyO.vertex_groups["_Detach_Breasts"].name = "_Detach_Breasts_TRANSFERED"        
        oMeshBodyO.vertex_groups["_Detach_Breasts_ORIGINAL"].name = "_Detach_Breasts"        

    #=== Prepare a ready-for-morphing client-side body. This one will be morphed by the user and be the basis for cloth fitting and play mode ===   
    oMeshMorphO = gBlender.DuplicateAsSingleton(oMeshBodyO.name, sNameGameBody + G.C_NameSuffix_Morph, G.C_NodeFolder_Game, True)  ###DESIGN!!! ###SOON!!
    Client_ConvertMesh(oMeshMorphO, True)  # Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
    oMeshBodySrcO.hide = True  # Hide back the source body as more realized bodies are now shown.

    #return G.DumpStr("OK: gBL_Body_CreateMorphBody() NameBaseID:'{}'  NameSrcBody:'{}'  NameSrcGenitals:'{}'".format(sNameBaseID, sNameSrcBody, sNameSrcGenitals))
    ###DESIGN?? ###CHECK: Remove extra bones from morphing body???


    ####NOTE: Now merged def gBL_Body_Create(sNameGameBody, sSex, sNameSrcGenitals, aCloths):  
    ###IMPROVE: Get most of these args from morphed body!?
    ###IMPROVE!! Detached breasts and penis still contain extra materials & vert groups... clean up?
    ###HACK!!!!! Breast morphs in this call!  Needs to be broken up and done differently!!
    ###OBS!?!?!?!: If we always get dynamic clothing ontop of breasts then why the extreme complexity of this function???

    #=== Assemble the list of meshes we have to create based on the sex of the character ===
    if sSex == "Woman":      # Woman has vagina and breasts (includes clothing area)
        aNameChunks = ["Breasts", "VaginaL", "VaginaR"]
    elif sSex == "Man":       # Shemale has breasts, penis and penis area clothing
        aNameChunks = ["Penis"]
    elif sSex == "Shemale":       # Shemale has breasts, and penis
        aNameChunks = ["Breasts", "Penis"]


    #===== Begin the complex task of assembling the requested body =====    
    #=== Obtain references to all the source meshes needed ===
    oMeshMorphO = gBlender.SelectAndActivate(sNameGameBody + G.C_NameSuffix_Morph)  # Obtain reference to previously constructed body for morphing
    sNameBodyRim = sNameGameBody + G.C_NameSuffix_BodyRim
    gBlender.DeleteObject(sNameBodyRim)
    oMeshComboO = gBlender.DuplicateAsSingleton(oMeshMorphO.name, sNameGameBody + G.C_NameSuffix_BodySkin, G.C_NodeFolder_Game, False)  ###TODO!!! Rename to MeshCombo??      ###DESIGN: Base skinned mesh on _Morph or virgin body??            
    nBodyMats = len(oMeshComboO.data.materials)  # Before we join additional clothing meshes with to body remember the number of materials so we can easily spot the vertices of clothing in big loop below


    #=== Prepare the cloth base by duplicating the requested bodysuit and converting for Client ===  ####OBS?  Only if cloth is split for some simulation with breasts soft body
    for sCloth in aCloths:
        if sCloth != "" and sCloth != "None":
            oMeshClothBaseO = gBlender.DuplicateAsSingleton(sCloth, sNameGameBody + G.C_NameSuffix_ClothBase, G.C_NodeFolder_Game, True)            
            gBlender.DuplicateAsSingleton(oMeshClothBaseO.name, sNameGameBody + G.C_NameSuffix_ClothCut, G.C_NodeFolder_Game, True)  ###HACK!: Just to enable gameplay mode all the way to play without going through cloth morph or cloth fit... revisit this crap!            
            gBlender.DuplicateAsSingleton(oMeshClothBaseO.name, sNameGameBody + G.C_NameSuffix_ClothFit, G.C_NodeFolder_Game, True)            
            oMeshClothO = gBlender.DuplicateAsSingleton(sNameGameBody + G.C_NameSuffix_ClothFit  , "_TEMP_ClothPart-Body", G.C_NodeFolder_Game, True)  ###DESIGN: Pass in cloth by array?  Support array iteration ###DESIGN: ###SOON: This is ALL clothing on the character, not just fit!
        
            #=== Remove information from all-cloth Client doesn't need (such as the vertex groups used for border creation) ===
            gBlender.SelectAndActivate(oMeshClothO.name)
            gBlender.Util_ConvertToTriangles()
            if bpy.ops.object.vertex_group_remove.poll():
                bpy.ops.object.vertex_group_remove(all=True)
        
            #=== Split the edges on the all-cloth marked as 'sharp' (such as between border and cloth) to give two verts for each border vert with two different normals ===
            oModEdgeSplit = oMeshClothO.modifiers.new('EDGE_SPLIT', 'EDGE_SPLIT')
            oModEdgeSplit.use_edge_sharp = True  # We only want edge split to split edges marked as sharp (done in border creation)
            oModEdgeSplit.use_edge_angle = False
            gBlender.AssertFinished(bpy.ops.object.modifier_apply(modifier=oModEdgeSplit.name))
            
            #=== Transfer the skinning information from the skinned body mesh to the clothing.  Some vert groups are useful to move non-simulated area of cloth as skinned cloth, other _Detach_xxx vert groups are to define areas of the cloth that are simulated ===
            gBlender.SelectAndActivate(oMeshClothO.name)
            oMeshMorphO.select = True
            oMeshMorphO.hide = False  ###LEARN: Mesh MUST be visible for weights to transfer!
            bpy.ops.object.vertex_group_transfer_weight()
        
            #=== Join the all-cloth onto the main skinned body to form the composite mesh that currently has all geometry for body and all clothing...  From this composite mesh we separate 'chunks' such as breasts are surrounding clothing, or penis or vagina for non-skinned simulation by the game engine ===
            gBlender.SelectAndActivate(oMeshComboO.name)
            oMeshClothO.select = True
            bpy.ops.object.join()  # This will join the cloth and its properly-set 'detach chunk' vertex groups to the body with matching chunk vertex groups.
            oMeshClothO = None  # Past this point clothing mesh doesn't exist... only oMeshComboO which has entire body and all clothing


    #=== Prepare the composite mesh for 'twin vert' mapping: The map that tells Client what vert from this detached chunk match what vert from the main skinned body ===
    bpy.ops.object.mode_set(mode='EDIT')
    bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)  # Create a 'custom data layer' to store unique IDs into mesh vertices so matching parts of the chunks we separate into other meshes can be easily matched to the main skinned mesh (for Client pinning)
    oLayVertTwinID = bmCombo.verts.layers.int.new(G.C_DataLayer_TwinVert)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
    nNextVertTwinID = 1  # We set the next twin vert ID to one.  New IDs for all detachable chunks will be created from this variable by incrementing.  This will enable each detached chunk to find what skinned vert from the body it needs to connect to during gameplay.
    aaMapTwinId2VertChunk = {}  # Map of maps we use to enable aMapTwinId2VertChunk to traverse the major loop that creates it to another loop at the end that needs it.


    #===== For woman & vagina, perform pre-processing of the vagina-area of the mesh.  We must split that part of the mesh into the '_Detach_VaginaL' and '_Detach_VaginaR' for the main loop below to properly detach the left&right vagina meshes for proper PhysX softbody processing =====
    if sSex == "Woman":         ####OBS?? Go for non-softbody vagina now??
        gBlender.SelectAndActivate(oMeshComboO.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
        nVertGrpIndex_Vagina = oMeshComboO.vertex_groups.find(G.C_VertGrp_Area + "Vagina")  # Find the rough-cut vagina-area part of our combo mesh that previous 'transfer_weight()' has transfered from source skinned body to our combo mesh       
        if nVertGrpIndex_Vagina == -1:
            raise Exception("ERROR: gBL_Body_Create() could not find Vagina vertex group in combo mesh!")
        oVertGroup_Vagina = oMeshComboO.vertex_groups[nVertGrpIndex_Vagina]
        oMeshComboO.vertex_groups.active_index = oVertGroup_Vagina.index
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')  # Expand the rough-cut verts into faces (so any found vert selects any attached face) to avoid cutting away faceless geometry
        ###bpy.ops.mesh.select_less()                                                      # Select less than original body has as we deliberately overshoot its selection to produce a 'less jagged' result after vertex group transfer between source mesh and our combo mesh
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='VERT')  ###LEARN: Changing mode while expanding is an excellent / easy way to smooth out a selection
        
        #=== Find the edges that would split the vagina into left and right halves.  To do this we store the edges at the boundary of the entire vagina, we compute the boundary edges on the left side and we subtract the 2nd from the 1st
        aVertsVagina = [oVert for oVert in bmCombo.verts if oVert.select]  # Store vagina verts for quicker iteration below (True?)
        bpy.ops.mesh.region_to_loop()  # Select the edges at the boundary of the vagina.
        aEdgesVaginaBoundary = [oEdge for oEdge in bmCombo.edges if oEdge.select]  # Remember the vagina boundary edges so we can remove them from left-half boundary (thereby leaving only the edges that can split left & right)
    
        #=== Unselect the right part of the vagina so we can compute its boundary edges and finally determine the edges between the two halves ===
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        for oVert in aVertsVagina:  # Reselect left vagina half only
            if oVert.co.x >= 0:
                oVert.select_set(True)
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')  ###LEARN:  Yes... all these damn mode changes are a must to convert selection from one domain to another!  (Extend in this case a must as we're going from low-order selection (verts) to a higher order (edges)
        bpy.ops.mesh.region_to_loop()  # Select the edges at the boundary of the left vagina half
    
        #=== Remove the edges found at the boundary of the entire Vagina.  This will leave only the edges between the two halves selected
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        for oEdgeVaginaBoundary in aEdgesVaginaBoundary:
            oEdgeVaginaBoundary.select_set(False)
        
        #=== Create a temporary new vertex group to store the verts of the vagina L/R split (unfortunately mesh.edge_split() loses selection!)  ===
        bpy.ops.object.mode_set(mode='OBJECT')  # Wished there were a way to create & assign to a vert group without leaving edit mode...
        aVertsVaginaSplit = [oVert.index for oVert in oMeshComboO.data.vertices if oVert.select]
        oVertGroup_TempVaginaSplit = oMeshComboO.vertex_groups.new(name="TempVaginaSplit")
        oVertGroup_TempVaginaSplit.add(index=aVertsVaginaSplit, weight=1.0, type='REPLACE')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
    
        #=== Split the vagina about its left/right split point and create additional geometry so game runtime has non-empty polygons to fully skin and thereby act as CPinSkinned for the neighboring softbody tetraverts.    
        bpy.ops.mesh.edge_split()  # Split edges: Each half of the vagina has polygons that go right up to the left/right split point now.
        bpy.ops.object.vertex_group_select()  # Reselect edges as edge_split() above unfortunately loses selection! (Fortunately vert group expanded to contain the new edges just created)
        bpy.ops.mesh.vertices_smooth()  # Perform a temporary smooth on the just-opened mesh.  This will pull newly-boundary verts away from each other (toward their closest polygons) so we form a very thin ribbon that will remain on the skinned body to provide anchors for CPinSkinned
    
        #=== Deselect the extremities of the just-created mesh hole so we can use 'bridge_edge_loops()' to construct polygons between the just-split meshes ===
        nVertHighestY = -sys.float_info.max  # Highest Y vert is the vert in the vagina split line that is most toward the navel 
        nVertLowestZ = sys.float_info.max  # Lowest  Z vert is the vert in the vagina split line that is most toward the anus
        for oVert in bmCombo.verts:  ###NOTE: Bit of weak code here with this stupid business of having to remove two verts so we can use bridge_edge_loop() but that call is by far the most suitable one as it doesn't damage the UV/material!  (otherwise mesh.fill() would have been far better as it doesn't leave two holes!)  
            if oVert.select:
                if  nVertHighestY < oVert.co.y:
                    nVertHighestY = oVert.co.y  ###URGENT! This stuff based on vert smooth damages UVs!  Leave it as is and iterate through verts to find their tangent to set their small offset!
                    oVertHighestY = oVert  ### Also that triangle missing is crap!  Try to fix selection so it's more contiguous
                if  nVertLowestZ > oVert.co.z:
                    nVertLowestZ = oVert.co.z
                    oVertLowestZ = oVert
                if (oVert.co.x > 0):  # Bring the slightly separated verts we split apart with 'vertices_smooth()' above much closer together so we only have a tiny band... just enough to not be zero and have a valid normal
                    oVert.co.x = 0.000001  # If we go too close normal for these tiny slivers of polygons won't be accurate and mesh will look horrible in that area!
                else:
                    oVert.co.x = -0.000001  ###IMPROVE: Would be nice to fix UVs too 
        for oEdge in oVertHighestY.link_edges:  ###LEARN: Selected higher-order geometry like edges & (even higher) polygons is a huge hassle!  Deselecting verts won't deselect edges & polys as they keep their own independent set
            oEdge.select_set(False)
        for oEdge in oVertLowestZ.link_edges:
            oEdge.select_set(False)
        bpy.ops.mesh.bridge_edge_loops()  # Finally we can join back the open part of the mesh... ###WEAK: Note that we leave an open face near the two up & down verts we just deselected above!!
        bpy.ops.mesh.quads_convert_to_tris()  # For some weird reason if we don't tesselate the few new faces we just created the rest of the pipeline won't tesselate before client gets the mesh and it will fail!
        
        #=== Determine the left vagina verts first by position, then by removing verts from split point, then expanding one ring of verts (best way I found to quickly tell apart the left/right verts at same position for split point) ===
        oMeshComboO.vertex_groups.active_index = oVertGroup_Vagina.index  # Reselect all the vagina verts so that we can define the L/R vertex groups that the main loop below needs to properly separate from the body for softbody runtime processing
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        for oVert in bmCombo.verts:
            if oVert.select == True and oVert.co.x < 0:
                oVert.select_set(False)
        oMeshComboO.vertex_groups.active_index = oVertGroup_TempVaginaSplit.index  # Deselect the slit verts from the vagina half verts
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.mesh.select_more()  # Now that we unselected the split point verts (that have same pos regardless of left/right), select one more ring of verts will select the split point verts on the right side of our mesh part
        aVertsVaginaL = [oVert.index for oVert in bmCombo.verts if oVert.select]  # Store the indices of the verts so we can define vert group below
    
        #=== Do the same for the right vagina verts... Determine the right vagina verts first by position, then by removing verts from split point, then expanding one ring of verts (best way I found to quickly tell apart the left/right verts at same position for split point) ===
        oMeshComboO.vertex_groups.active_index = oVertGroup_Vagina.index  # Reselect all the vagina verts so that we can define the L/R vertex groups that the main loop below needs to properly separate from the body for softbody runtime processing
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        for oVert in bmCombo.verts:
            if oVert.select == True and oVert.co.x > 0:
                oVert.select_set(False)
        oMeshComboO.vertex_groups.active_index = oVertGroup_TempVaginaSplit.index  # Deselect the slit verts from the vagina half verts
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.mesh.select_more()  # Now that we unselected the split point verts (that have same pos regardless of left/right), select one more ring of verts will select the split point verts on the right side of our mesh part  (Bit weak to do this but all we have to do is select one less in original body to avoid expanding too much)
        aVertsVaginaR = [oVert.index for oVert in bmCombo.verts if oVert.select]  # Store the indices of the verts so we can define vert group below
    
        #=== Create the vagina left and right vertex groups for the main loop below ===    
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')  # Wished there were a way to create & assign to a vert group without leaving edit mode...
        oVertGroup_VaginaL = oMeshComboO.vertex_groups.new(name=G.C_VertGrp_Detach + "VaginaL")
        oVertGroup_VaginaL.add(index=aVertsVaginaL, weight=1.0, type='REPLACE')
        oVertGroup_VaginaR = oMeshComboO.vertex_groups.new(name=G.C_VertGrp_Detach + "VaginaR")
        oVertGroup_VaginaR.add(index=aVertsVaginaR, weight=1.0, type='REPLACE')
        
        #=== Remove the temp vertex group... (Keeping it would badly break the skinning info!!) ===
        oMeshComboO.vertex_groups.active_index = oVertGroup_TempVaginaSplit.index
        bpy.ops.object.vertex_group_remove()
        ###CHECK: The abrupt break in geometry around the new collapse point throws off vertex normals for the entire slit...  Does this affect the client??  Do we need to split verts??  (Would that work with softbody??)

    
    #===== MAIN SEPERATION PROCESSING FOR EACH 'SEPERABLE CHUNKS' =====  Breasts take ownership of clothing around them to be processed on their mesh as softbody.  Penis and vagina need processing here to to cap, twin and separate
    for sNameChunk in aNameChunks:
        print("--- Separating chunk " + sNameChunk)
        sNamePartChunk = sNameGameBody + G.C_VertGrp_Detach + sNameChunk
        gBlender.DeleteObject(sNamePartChunk)
        gBlender.SelectAndActivate(oMeshComboO.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)

        #=== Obtain the 'detach chunks' vertex group from the combo mesh that originally came from the source body.  This 'detach chunk' will be updated for chunks such as breasts to append to it the verts of neighboring clothing so they will also be softbody simulated  ===
        nVertGrpIndex_DetachChunk = oMeshComboO.vertex_groups.find(G.C_VertGrp_Detach + sNameChunk)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
        if nVertGrpIndex_DetachChunk == -1:
            oMeshComboO.vertex_groups.new(name=G.C_VertGrp_Detach + sNameChunk)
        oVertGroup_DetachChunk = oMeshComboO.vertex_groups[nVertGrpIndex_DetachChunk]
        oMeshComboO.vertex_groups.active_index = oVertGroup_DetachChunk.index
    
        #=== For non-body detach areas such a clothing around breasts and dynamic cloth around penis, refine the clothing area that is be non-skinned / simulated by selecting vertices by pre-defined bounding spheres (set individually for each type) ===
        if sNameChunk == "Breasts" or sNameChunk == "PenisArea":  # Breasts and PenisArea area are the two 'detach chunk' that can have cloth around them that must take part in external simulation.  'Refine' their selection below...
            bpy.ops.mesh.select_all(action='DESELECT')
            bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
            oCutSphere = bpy.data.objects["CutSphere-" + sNameChunk]  ###CHECK!            ###IMPROVE?: Cut sphere for penis changes with starting position of penis?? (Not if starts straight as soft body!)
            vecSphereCenterL = oCutSphere.location.copy()  ###LEARN: If we don't copy next line moves sphere!!
            vecSphereCenterR = vecSphereCenterL.copy()  ###LEARN: If we don't copy, next line inverts x on both vectors!
            vecSphereCenterR.x = -vecSphereCenterR.x  # The '2nd' sphere is just the sphere #1 mirrored about x
            vecSphereCenterC = (vecSphereCenterL + vecSphereCenterR) / 2 
            nSphereRadius = oCutSphere.dimensions.x / 2
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  ###LEARN: If View3D were in any other mode the following code would NOT select!!  WTF???
            for oVert in bmCombo.verts:
                if oVert.link_faces[0].material_index >= nBodyMats:  # We're only interested in non-body verts for cloth area-detection.  (Body already has well formed vert groups for these chunks.)
                    vecVert = oMeshComboO.matrix_world * oVert.co                                   
                    vecVertToSphereCenterL = vecVert - vecSphereCenterL
                    vecVertToSphereCenterR = vecVert - vecSphereCenterR
                    vecVertToSphereCenterC = vecVert - vecSphereCenterC
                    if vecVertToSphereCenterL.magnitude < nSphereRadius or vecVertToSphereCenterR.magnitude < nSphereRadius or vecVertToSphereCenterC.magnitude < nSphereRadius:
                        oVert.select_set(True)
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')  # We expand the selection of verts to faces to ensure we don't cut out verts left hanging by an edge
            aVertsDetachChunk = [oVert.index for oVert in bmCombo.verts if oVert.select]
            bpy.ops.object.mode_set(mode='OBJECT')
            oVertGroup_DetachChunk.add(index=aVertsDetachChunk, weight=0.0, type='REPLACE')  # Add the verts to be detached from cloth to the appropriate detach vert group with weight zero (so it doesn't interfere with bones)

        #=== Detach the currently-processed 'chunk' from the source composite mesh.  One chunk for each separate softbody/cloth simulation ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
        bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)  ###LEARN!!: We must re-obtain new bmesh everytime we re-enter edit mode.  (And of course old bmesh object references are gone but IDs persist!)
        oLayVertTwinID = bmCombo.verts.layers.int[G.C_DataLayer_TwinVert]  # Refetch our custom data layer because we exited edit mode...
        aFacesToSplit = [oFace for oFace in bmCombo.faces if oFace.select]  # Obtain array of all faces to separate
    
        #=== Store the boundary edges of the split into the new vertex group so we can provide Client the mapping of split verts between the meshes ===
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.region_to_loop()  # This will select only the edges at the boundary of the cutout polys... including edge of cloth, seams and the (needed) edges that connect split mesh to main mesh
        for oEdge in bmCombo.edges:  # Iterate over the edges at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut
            if oEdge.select == True:
                if oEdge.is_manifold == False:  # Deselect the edges-on-edge (i.e. natural edge of cloth)
                    oEdge.select_set(False)
        ###HACK ###IMPROVE ###DESIGN: Important limitation of the above code appears when attempting to separate Penis at its natural mesh boundary (at the endge of its material)
        ### Because we need to separate from the Client-ready morphed body, the penis mesh in that mesh is already separated from main skinned mesh at its material boundary...  Making this call's attempt to twin verts impossible.
        ### A hack was adopted by setting the 'seperatable mesh' of penis one ring of vertices less than its materials, so that this code can twin verts and the runtime to attach softbody penis to skinned main body mesh.
        ### An improvement could be created to enable traversal of the duplicated verts because of material and properly twin the penis mesh verts to the verts that are really on the skinned body mesh.
    
        #=== Iterate over the split verts to store a uniquely-generated 'twin vert ID' into the custom data layer so we can re-twin the split verts from different meshes after the mesh separate ===
        aVertsBoundary = [oVert for oVert in bmCombo.verts if oVert.select]
        for oVert in aVertsBoundary:
            oVert[oLayVertTwinID] = nNextVertTwinID  # These are unique to the whole skinned body so all detached chunk can always find their corresponding skinned body vert for per-frame positioning
            nNextVertTwinID += 1
    
        #=== Reselect the faces again to split the 'detachable chunk' into its own mesh so that it can be sent to softbody/cloth simulation.  ===
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bChunkMeshHasGeometry = False  # Determine if chunk mesh has any faces
        for oFace in aFacesToSplit:
            oFace.select_set(True)
            bChunkMeshHasGeometry = True
    
        #=== If chunk mesh has no geometry then we don't generate it as client has nothing to render / process for this chunk ===
        if bChunkMeshHasGeometry == False:
            print("\n>>> GameMode_Play_PrepBody() skips creation of chunk mesh '{}' from body '{}' because it has no geometry <<<".format(sNameChunk, sNameGameBody))
            continue
    
        #=== Split and separate the chunk from the composite mesh ===
        bpy.ops.mesh.split()  # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
        bpy.ops.mesh.separate()  # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
    
        #===== Post-process the just-detached chunk to calculate the 'twin verts' array between it and the main skinned main body =====
        #=== Fetch the just-split body part + cloths 'detach chunk' so we can calculate 'matching' information to 'twin' the previously connected verts together (to pin a simulated area of mesh to the skinned mesh) ===    
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        oMeshPartChunkO = bpy.context.object 
        oMeshPartChunkO.name = oMeshPartChunkO.data.name = sNamePartChunk  ###NOTE: Do twice so name sticks!
        oMeshPartChunkO.name = oMeshPartChunkO.data.name = sNamePartChunk
        bpy.ops.object.vertex_group_remove(all=True)  # Remove all vertex groups from detached chunk to save memory
    
        #=== Iterate through the verts of the newly separated chunk to access the freshly-created custom data layer to obtain ID information that enables us to match the chunk mesh vertices to the main skinned mesh for pinning ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmPartChunk = bmesh.from_edit_mesh(oMeshPartChunkO.data)
        oLayVertTwinID = bmPartChunk.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertChunk = {}
        for oVert in bmPartChunk.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertChunk[nTwinID] = oVert.index
                if oVert.link_faces[0].material_index < nBodyMats:  # For capping below, select only the twin verts that are on one of the body's original material
                    oVert.select_set(True)
                # print("TwinVert {:3d} = PartVert {:5d} mat {:} at {:}".format(nTwinID, oVert.index, oVert.link_faces[0].material_index, oVert.co))
        aaMapTwinId2VertChunk[sNameChunk] = aMapTwinId2VertChunk  # Store our result in top-level map so loop near end of this function can finish the work once whole rim has been created.
        
        #=== Cap the body part that is part of the chunk (edge verts from only that body part are now selected)  If this chunk has no body verts (e.g. PenisClothing) then no capping will occur) ===
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')  ###BUG?? ###CHECK: Possible that edge collapse could fail depending on View3D mode...
        bpy.ops.mesh.extrude_edges_indiv()  ###LEARN: This is the function we need to really extrude!
        bpy.ops.mesh.edge_collapse()  ###DESIGN ###IMPROVE Do we always cap whatever body part is ripped out?
        for oVert in bmPartChunk.verts:  # The cap vert(s) created will have copied one of the 'VertTwinID'.  Wipe it out to avoid corrupting matching below 
            if oVert.select:
                oVert[oLayVertTwinID] = 0
        bpy.ops.mesh.select_all(action='DESELECT')

        #=== Do the important conversion of the chunk mesh to be renderable by the Client... we're done processing that mesh. ===
        Client_ConvertMesh(oMeshPartChunkO, True)


    #===== Create the 'Skinned Rim' skinned mesh that Client can use to use 'BakeMesh()' on a heavily-simplified version of the main body mesh that contains only the 'rim' polygons that attach to all the detacheable chunks this code separates.  It is this 'Rim' skinned mesh that quickly calculates the position of all the pins and that therfore 'owns' the CPinSkinned and therefore the CPinTetra === 
    ####DESIGN: Vert topology changes at every split!  MUST map twinID to body verts once all cuts done ###NOW!!!
    #=== Iterate through the verts of the main skinned mesh (now that all chunks have been removed) to select all the twin verts so we can create the rim mesh
    gBlender.SelectAndActivate(oMeshComboO.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
    oLayVertTwinID = bmCombo.verts.layers.int[G.C_DataLayer_TwinVert]
    for oVert in bmCombo.verts:
        nTwinID = oVert[oLayVertTwinID]
        if nTwinID != 0:
            oVert.select_set(True)  # Select this edge boundary vertex for the upcoming code in which we expand the rim selection to create the rim submesh

    #=== Select the faces neighboring the twin verts and duplicate them into the new 'rim mesh'
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='EDGE')  # ... With the rim verts selected two loops ago expand these 'boundary verts' into edge mode any edge touching the boundary verts are edges are selected (including non-boundary ones)...
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')  # ... then switch to poly mode to have the smallest set of polygons that have an edge at the boundary are left selected.  These will form their own 'reduced skin mesh' that will be baked at every frame to calculate pin positions
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate()  # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
    bmCombo.verts.layers.int.remove(oLayVertTwinID)  # Remove the temp data layer in the skin mesh as the just-separated mesh has the info now...
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    #=== Fetch the just-created 'rim' skinned mesh and set it to its proper name ===
    bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
    bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
    oMeshSkinColSrcO = bpy.context.object 
    oMeshSkinColSrcO.name = oMeshSkinColSrcO.data.name = sNameBodyRim  ###NOTE: Do it twice to ensure name really sticks  ###WEAK: Wish this was easier to do!
    oMeshSkinColSrcO.name = oMeshSkinColSrcO.data.name = sNameBodyRim
    del(oMeshSkinColSrcO[G.C_PropArray_MapSharedNormals])  # Source skinned body has the shared normal array which is not appropriate for rim.  (Serialization would choke)

    #=== Cleanup the rim mesh by removing all materials ===
    while len(oMeshSkinColSrcO.material_slots) > 0:  ###IMPROVE: Find a way to remove doubles while preventing key-not-found errors in twin hunt below??
        bpy.ops.object.material_slot_remove()
    bpy.ops.object.material_slot_add()  # Add a single default material (captures all the polygons of rim) so we can properly send the mesh over (crashes if zero material)
    
    #=== Iterate over the rim vertices, and find the rim vert for every 'twin verts' so next loop can map chunk part verts to rim verts for pinning === 
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bmSkinColSrc = bmesh.from_edit_mesh(oMeshSkinColSrcO.data)
    oLayVertTwinID = bmSkinColSrc.verts.layers.int[G.C_DataLayer_TwinVert]
    aMapTwinId2VertRim = {}
    for oVert in bmSkinColSrc.verts:
        nTwinID = oVert[oLayVertTwinID]
        if nTwinID != 0:
            oVertAdjacent = oVert.link_edges[0].other_vert(oVert)  # Find an 'adjacent vert' to this twin vert so that Client pin has the chance to fully orient the 'Z' of the normal of this pin so 'up' always points toward this adjacent vert (with 'LookAt' function)   ###IMPROVE: Would be nice to return an adjacent vert on boundary edge??
            aMapTwinId2VertRim[nTwinID] = (oVert.index, oVertAdjacent.index)  # Store both the twin vert and an adjacent vert for this twin
            # print("TwinVert {:3d} = RimVert {:5d}-{:5d} at {:}".format(nTwinID, oVert.index, oVertAdjacent.index, oVert.co))
    bpy.ops.object.mode_set(mode='OBJECT')
    gBlender.Cleanup_VertGrp_RemoveNonBones(oMeshSkinColSrcO)  # Remove the extra vertex groups that are not skinning related
    
    #===== Now that rim is fully formed and the aMapTwinId2VertRim fully populated for to find real rim verts for any TwinID we can finally construct the aMapTwinVerts flat array for each detached part.  (each detached part (no matter if its softbody or cloth simulated) will thereby be able to fix its edge verts to the rim correctly during gameplay) (With both the main skinned mesh and the chunk part with the same set of 'twin ID' in their mesh vertices, we can finally match vertex ID of part to vertex ID of skinned main mesh)
    ###NOTE: This flattened is sent with 1) vertex ID on the separated chunk part, 2) Vertex ID of the 'twin vert' at the same location on the main skinned mesh and 3) an adjacent vert on the skinned mesh to #2 for normal Z-orientation
    aNameChunksCreated = []  ####OBS? # Append to this list the full names of the chunk meshes this call has created.  Client then fetch each of these in turns via gBL_GetMesh()
    for sNameChunk in aNameChunks:
        sNamePartChunk = sNameGameBody + G.C_VertGrp_Detach + sNameChunk
        if sNamePartChunk not in bpy.data.objects:  # Skip processing of this chunk if it wasn't created above.
            continue
        aNameChunksCreated.append(sNamePartChunk)  # Append name to list so client knows this chunk is available for gametime processing
        oMeshPartChunkO = bpy.data.objects[sNamePartChunk]
        aMapTwinVerts = array.array('H')  # The final flattened map of what verts from the 'detached chunk part' maps to what vert in the 'skinned main body'  Client needs this to pin the edges of the softbody-simulated part to the main body skinned mesh
        aMapTwinId2VertChunk = aaMapTwinId2VertChunk[sNameChunk]  # Now that the full rim is known, fetch the map previously created for this chunk earlier in this function in our 'map of maps'
        print("--- Mapping twinned verts on mesh chunk " + sNameChunk)  # + str(aMapTwinId2VertChunk))
        # for nTwinID in range(1, len(aMapTwinId2VertChunk) + 1):
        for nTwinID in aMapTwinId2VertChunk:
            nVertTwinChunk = aMapTwinId2VertChunk[nTwinID]
            if nTwinID in aMapTwinId2VertRim:
                aRimDef = aMapTwinId2VertRim[nTwinID]
                nVertTwinRim = aRimDef[0]
                nVertTwinRimAdjacent = aRimDef[1]
                aMapTwinVerts.append(nVertTwinChunk)
                aMapTwinVerts.append(nVertTwinRim)
                aMapTwinVerts.append(nVertTwinRimAdjacent)
                # print("TwinVert {:3d} = PartVert {:5d} = RimVert {:5d} & Adj {:5d}".format(nTwinID, nVertTwinChunk, nVertTwinRim, nVertTwinRimAdjacent))
            else:
                G.DumpStr("ERROR in gBL_Body_Create(): Mapping of twin verts from TwinID to RimVert Could not find TwinID {} while processing chunk '{}' on mesh '{}' (Obscure corner-case algorithm error that rest of code can probably recover from...)".format(nTwinID, sNameChunk, oMeshComboO.name))  # Obscure corner case that appears with Vagina L/R... Perhaps because split-point verts are in same position??  Check if this influences the game... 
        oMeshPartChunkO[G.C_PropArray_MapTwinVerts] = aMapTwinVerts.tobytes()  # Store the output map as an object property for later access when Client requests this part.  (We store as byte array to save memory as its only for future serialization to Client and Blender has no use for this info)

    #===== Cleanup the main skinned mesh =====
    gBlender.Cleanup_VertGrp_RemoveNonBones(oMeshComboO)  # Remove the extra vertex groups that are not skinning related
    Client_ConvertMesh(oMeshComboO, True)  # With the skinned body + skinned clothing mesh free of non-bone vertex groups, we can safely limit the # of bones per vertex to the Client limit of 4 and normalize all bone weights ===
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # Limit mesh to four bones each   ###CHECK: Possible our 'non-bone' vertgrp take info away???
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.select_all(action='DESELECT')

    #===== Copy and re-pair the breast collider for women to the newly detached breast mesh =====
    if (sNameSrcBody.startswith('Woman')):    
        sNameBreastColToBody    = sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBody"                  # These were generated when morphing body was created and have been moved along morphing body.
        sNameBreastColToBreasts = sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBreasts"               #... so the just-detached breasts are at the exact same position... but we need to 're-pair' to the just-detached breasts so collider can now moving along with softbody breasts
        gBlender.DuplicateAsSingleton(sNameBreastColToBody, sNameBreastColToBreasts, G.C_NodeFolder_Game, True)     # 'ToBody' breast collider already paired to body for static morphing.  Now re-pair a new instance of breast collider onto newly created detached softbody breasts
        CBBodyCol.PairMesh_DoPairing(sNameBreastColToBreasts, sNameGameBody + "_Detach_Breasts", 0.000001)                     # Redo the pairing to the morph body so breast verts can follow body verts
    
#     CBBodyCol.PairMesh_Define(sNameBreastColToBreasts, sNameGameBody + , sNameMeshOutput, nVertTolerance):
#     //CBBodyCol.PairMesh_Define(sNameSrcBody + "-BreastCol-Source", sNameGameBody + "_Detach_Breasts", sNameGameBody + G.C_NameSuffix_BreastCol + "-ToBreasts", 0.001)
   
    #gBlender.gBL_Util_HideGameMeshes();     ###KEEP???

    #===== Return success message to client.  It will now request each of the processed meshes this call prepared and ship them to various engines such as softbody, clothing or skinned =====
    ###OBS? return str(aNameChunksCreated)
    return ""

def GameMode_ClothCut(sNameBody):  # Prepare for the cloth cut game mode -> Create a duplicate cloth mesh from its source
    gBlender.DuplicateAsSingleton(sNameBody + G.C_NameSuffix_ClothBase, sNameBody + G.C_NameSuffix_ClothCut, G.C_NodeFolder_Game, True)
    return G.DumpStr("OK: GameMode_ClothCut() copied base '{}' into cut '{}'".format(sNameBody + G.C_NameSuffix_ClothBase, sNameBody + G.C_NameSuffix_ClothCut))

def GameMode_ClothFit(sNameBody):  # Prepare for the cloth fit game mode   
    gBlender.DuplicateAsSingleton(sNameBody + G.C_NameSuffix_ClothCut, sNameBody + G.C_NameSuffix_ClothFit, G.C_NodeFolder_Game, True)
    return G.DumpStr("OK: GameMode_ClothFit() copied cut '{}' into fit '{}'".format(sNameBody + G.C_NameSuffix_ClothCut, sNameBody + G.C_NameSuffix_ClothFit))

def GameMode_ClothFit_End(sNameBody):  # Cleanup the PhysX-simulated cloth.  Assumes Client uploaded its latest verts of this cloth before.
    gBlender.SelectAndActivate(sNameBody + G.C_NameSuffix_ClothFit)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth_laplacian(repeat=1, lambda_factor=0.005, lambda_border=0.000)  ###TUNE!
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return G.DumpStr("OK: GameMode_ClothFit_End('')".format())



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    UTILITY
#---------------------------------------------------------------------------    

def Client_ConvertMesh(oMeshO, bSplitVertsAtUvSeams):  # Convert a Blender mesh so Client can properly display it. Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
    # bSplitVertsAtUvSeams will split verts at UV seams so Unity can properly render.  (Cloth currently unable to simulate this way) ####FIXME ####SOON
    
    #=== Separate all seam edges to create unique verts for each UV coordinate as Client requires ===
    gBlender.SelectAndActivate(oMeshO.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris()  ###DESIGN: Keep here??  ###REVIVE: use_beauty=True 
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(oMeshO.data)          

    if (len(oMeshO.data.edges) == 0):                           # Prevent split of UV if no edges.  (Prevents an error in seams_from_islands() for vert-only meshes (e.g. softbody pinning temp meshes)
        bSplitVertsAtUvSeams = False;

    #=== Iterate through all edges to select only the non-sharp seams (The sharp edges have been marked as sharp deliberately by border creation code).  We need to split these edges so Client-bound mesh can meet its (very inconvenient) one-normal-per-vertex requirement ===
    if (bSplitVertsAtUvSeams == True):
        bpy.ops.uv.seams_from_islands()  # Update the edge flags so all seams are flagged
        for oEdge in bm.edges:
            if oEdge.seam and oEdge.smooth:  ###LEARN: 'smooth' edge = non-sharp edge!
                oEdge.select_set(True)
                #bpy.ops.mesh.edge_split()                ###NOTE: Loses the s

    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')



    #=== Load/create a persistent custom data layer to store the 'SharedNormalID' of duplicated verts accross seams that must have their normal averaged out by Client ===
    ###NOTE: as this call can be called multiple times with the mesh getting its edges split each time that this data layer persists and gets added to at each wave of splits.
    ###NOTE: While this data layer is stored in the mesh to persists between call, the 'aMapSharedNormals' below is recreated from this persistent info each time this function is called so Client receives shared normals that had their edges split accross multiple calls
    ###NOTE: An common/important example is Blender taking the morphed body that was client-ready, and appends clothing & separates parts to have result be client-ready again.   
    if G.C_DataLayer_SharedNormals in bm.verts.layers.int:
        oLayVertSharedNormalID = bm.verts.layers.int[G.C_DataLayer_SharedNormals]
        ###BROKEN nNextSharedNormalID = oMeshO["nNextSharedNormalID"]  # If mesh had existing data layer it also had 'nNextSharedNormalID' stored so we know what next unique ID to assign
    else:
        oLayVertSharedNormalID = bm.verts.layers.int.new(G.C_DataLayer_SharedNormals)
        nNextSharedNormalID = 1
    
    #=== Iterate through the verts that will be split to store into a temp custom data layer a temporary unique ID so that split verts that must have the same normal can be 'twinned' together again so Client can average out their normals
    for oVert in bm.verts:
        if oVert.select:
            oVert[oLayVertSharedNormalID] = nNextSharedNormalID  # Note that we are only assigning new IDs here.  If this call ran before on this mesh, the split verts during that call would have previous IDs in our custom data layer
            nNextSharedNormalID += 1
            
    #=== Split the seam edges so each related polygon gets its own edge & verts.  This way each vert always has one exact UV like Client requires ===
    bpy.ops.mesh.edge_split()                           ###NOTE: Loses selection!
    
    #=== After edge split all verts we have separated can still be 'matched together' by their shared normal ID that has also been duplicated as verts were duplicated === 
    aaSharedNormals = {}  # Create a 'map-of-arrays' that will store the matching vertex indices for each 'shared normals group'.  Done this way because a vert can be split more than once (e.g. at a T between three seams for example)
    for oVert in bm.verts:
        nSharedNormalID = oVert[oLayVertSharedNormalID]
        if nSharedNormalID > 0:  # If this vert has a shared normal ID (from this call or a previous one) the insert it into our map to construct our list of shared normals
            if nSharedNormalID not in aaSharedNormals:  # If our map entry for this group does not exist create an empty array at this map ID so next line will have an array to insert the first item of the group
                aaSharedNormals[nSharedNormalID] = []
            aaSharedNormals[nSharedNormalID].append(oVert.index)  # Append the vert index to this shared normal group.

    #=== 'Flatten' the aaSharedNormals array by separating the groups with a 'magic number' marker.  This enables groups of irregular size to be transfered more efficiently to Client ===
    aMapSharedNormals = array.array('H')  # Array of unsigned shorts.   Client can only process meshes under 64K verts anyways...
    for nSharedNormalID in aaSharedNormals:
        aSharedNormals = aaSharedNormals[nSharedNormalID]
        nCountInThisSharedNormalsGroup = len(aSharedNormals)
        if nCountInThisSharedNormalsGroup > 1:  # Groups can be from size 1 (alone) to about 4 verts sharing the same normal with 2 by far the most frequent.  Don't know why we get about 10% singles tho... Grabbed by groups with 3+??
            for nVertID in aSharedNormals:
                aMapSharedNormals.append(nVertID)
            aMapSharedNormals.append(G.C_MagicNo_EndOfFlatGroup)  # When Client sees this 'magic number' it knows it marks the end of a 'group' and updates the normals for the previous group

    oMeshO[G.C_PropArray_MapSharedNormals] = aMapSharedNormals.tobytes()  # Store this 'ready-to-serialize' array that is sent with all meshes sent to Client so it can fix normals for seamless display 
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    ###BROKEN oMeshO["nNextSharedNormalID"] = nNextSharedNormalID  # Store the last ID used in case this function runs on this mesh again.

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    SUPER PUBLIC -> Global top-level functions exported to Client
#---------------------------------------------------------------------------    

def gBL_GetMesh(sNameMesh):  # Called in the constructor of Unity's important CBMesh constructor to return the mesh (possibly skinned depending on mesh anme) + meta info the class needs to run.
    print("=== gBL_GetMesh() sending mesh '{}' ===".format(sNameMesh))

    oMeshO = gBlender.SelectAndActivate(sNameMesh)
    gBlender.Cleanup_VertGrp_RemoveNonBones(oMeshO)     # Remove the extra vertex groups that are not skinning related from the skinned cloth-part
    Client_ConvertMesh(oMeshO, True)  # Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)

    oMesh = oMeshO.data
    aVerts = oMesh.vertices
    nVerts = len(aVerts)
    # nEdges = len(oMesh.edges)
    nTris = len(oMesh.polygons)  # Prepare() already triangulated so all polygons are triangles
    nMats = len(oMesh.materials)

    #=== Send the 'header' containing a magic number, the number of verts, tris, materials ===
    oBA = bytearray()
    oBA += struct.pack('H', G.C_MagicNo_TranBegin)  ###LEARN: Struct.Pack args: b=char B=ubyte h=short H=ushort, i=int I=uint, q=int64, Q=uint64, f=float, d=double, s=char[] ,p=PascalString[], P=void*
    oBA += struct.pack('i', nVerts)  ###LEARN!!!: Really fucking bad behavior by struct.pack where pack of 'Hi' will give 8 byte result (serialized as both 32-bit) while 'HH' will give 4 bytes (both serialzed as 16-bit)  ###WTF?????
    oBA += struct.pack('i', nTris)
    oBA += struct.pack('B', nMats)
    
    #=== Send our collection of material.  Client will link to the image files to create default materials ===
    for nMat in range(nMats):
        oMat = oMesh.materials[nMat]
        sImgFilepathEnc = "NoTexture"
        if oMat is not None:
            if oMat.name.startswith("Material_"):  # Exception to normal texture-path behavior is for special materials such as 'Material_Invisible'.  Just pass in name of special material and Unity will try to fetch it.  It is assume that Blender and client both define this same material!
                sImgFilepathEnc = oMat.name  ###IMPROVE: Could pass in more <Unity defined Material>' names to pass special colors and materials??
            else:  # For non-special material we pass in texture path.
                oTextureSlot = oMat.texture_slots[0]
                if oTextureSlot:
                    sImgFilepathEnc = oTextureSlot.texture.image.filepath
                    # aSplitImgFilepath = oTextureSlot.texture.image.filepath.rsplit(sep='\\', maxsplit=1)    # Returns a two element list with last being the 'filename.ext' of the image and the first being the path to get there.  We only send Client filename.ext
        gBlender.Stream_SendStringPascal(oBA, sImgFilepathEnc)

    oBA += Stream_GetEndMagicNo()  # Append a 'magic number' to help catch deserialization errors quickly

    #=== Now pass processing to our C Blender code to internally copy the vert & tris of this mesh to shared memory Client can access directly ===
    print("--- gBL_GetMesh() sharing mesh '{}' of {} verts, {} tris and {} mats with bytearray of size {} ---".format(sNameMesh, nVerts, nTris, nMats, len(oBA)))
    oMesh.tag = True                    ###IMPORTANT: Setting 'tag' on the mesh object and causes the next update to invoke our C-code modification of Blender share/unshare mesh memory to Client
    oMesh.use_fake_user = False         ###NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.  Make sure this is off in this context
    oMesh.update(True, True)            ###IMPORTANT: Our modified Blender C code traps the above flags to update its shared data structures with client...        

    return oBA          # Return the bytearray intended for Unity deserialization. 


def gBL_GetMesh_SkinnedInfo(sNameMesh):          #=== Send skinning info to Unity's CBSkin objects  (vertex groups with names so Unity can map blender bones -> existing Client bones)
    print("=== gBL_GetMesh_SkinnedInfo() sending mesh '{}' ===".format(sNameMesh))

    #=== Select mesh and obtain reference to needed mesh members ===
    oMeshO = gBlender.SelectAndActivate(sNameMesh)
    oMesh = oMeshO.data
    aVerts = oMesh.vertices
    nVerts = len(aVerts)
    
    #=== Construct outgoing bytearray Unity can read back ===
    oBA = bytearray()
    oBA += struct.pack('H', G.C_MagicNo_TranBegin)  ###LEARN: Struct.Pack args: b=char B=ubyte h=short H=ushort, i=int I=uint, q=int64, Q=uint64, f=float, d=double, s=char[] ,p=PascalString[], P=void*
    oBA += struct.pack('B', len(oMeshO.vertex_groups))
    for oVertGrp in oMeshO.vertex_groups:
        gBlender.Stream_SendStringPascal(oBA, oVertGrp.name)        
 
    #=== Iterate through each vert to send skinning data.  These should have been trimmed down to four in prepare but Client will decipher and keep the best 4 nonetheless ===
    nErrorsBoneGroups = 0     
    for nVert in range(nVerts):
        aVertGroups = aVerts[nVert].groups
        nVertGroups = len(aVertGroups)
        oBA += struct.pack('B', nVertGroups)
        for oVertGroup in aVertGroups:
            nGrp = oVertGroup.group
            if (nGrp < 0 or nGrp > 255):  ###IMPROVE ###CHECK: Why the heck do we see bones with high numbers?  Blender file corruption it seems...
                G.DumpStr("\n***ERROR: Bones at vert {} with vertgroup {} and weight {}\n".format(nVert, nGrp, oVertGroup.weight))
                oBA += struct.pack('B', 0)  ###CHECK: What to do???
                oBA += struct.pack('f', 0)
                nErrorsBoneGroups = nErrorsBoneGroups + 1
            else:  
                oBA += struct.pack('B', oVertGroup.group)
                oBA += struct.pack('f', oVertGroup.weight)
    oBA += struct.pack('i', nErrorsBoneGroups)
    oBA += Stream_GetEndMagicNo()  # Append a 'magic number' to help catch deserialization errors quickly

    return oBA          # Return the bytearray intended for Unity deserialization. 
    

def gBL_GetMesh_Array(sNameMesh, sNameArray):        #=== Send Unity the requested serialized bytearray of the previously-calculated custom property of mesh 'sNameMesh'
    oBA = bytearray()
    oBA += struct.pack('H', G.C_MagicNo_TranBegin)  ###LEARN: Struct.Pack args: b=char B=ubyte h=short H=ushort, i=int I=uint, q=int64, Q=uint64, f=float, d=double, s=char[] ,p=PascalString[], P=void*

    oMeshO = gBlender.SelectAndActivate(sNameMesh)
    aArray = oMeshO.get(sNameArray)
    gBlender.Stream_SerializeArray(oBA, aArray)
    oBA += Stream_GetEndMagicNo()                   # Append a 'magic number' to help catch deserialization errors quickly

    return oBA
    

def gBL_GetBones(sNameMesh):  # Called by the CBodeEd (Unity's run-in-edit-mode code for CBody) to update the position of the bones for the selected Unity template.  Non destructive call that assumes existing bones are already there with much extra information such as ragdoll colliders, components on bones, etc.)
    # This call only updates bones position and creates bones if they are missing.  Rotation isn't touched and extraneous bones have to be deleted in Unity if needed.
    print("\n=== gBL_GetBones('{}') ===".format(sNameMesh))
    if (sNameMesh not in bpy.data.objects):
        return G.DumpStr("ERROR: gBL_GetBones() cannot find object '" + sNameMesh + "'")

    oMeshO = gBlender.SelectAndActivate(sNameMesh)
    if "Armature" not in oMeshO.modifiers:
        return G.DumpStr("ERROR: gBL_GetBones() cannot find armature modifier for '" + sNameMesh + "'")
    oArmature = oMeshO.modifiers["Armature"].object.data

    #=== Send the 'header' containing a magic number, the number of verts, tris, materials ===
    oBA = bytearray()
    oBA += struct.pack('H', G.C_MagicNo_TranBegin)  ###LEARN: Struct.Pack args: b=char B=ubyte h=short H=ushort, i=int I=uint, q=int64, Q=uint64, f=float, d=double, s=char[] ,p=PascalString[], P=void*

    #=== Send bone tree (without bone positions) Unity needs our order to map to its existing bone which remain the authority ===
    gBlender.Stream_SendBone(oBA, oArmature.bones[0])  # Recursively send the bone tree starting at root node (0)

    oBA += Stream_GetEndMagicNo()  # Append a 'magic number' to help catch deserialization errors quickly
    print("--- gBL_GetBones() returning array of size " + str(len(oBA)))
     
    return oBA  # Return the beginning part of the bytearray intended for client deserialization. 

def Stream_GetEndMagicNo():  # When function based on gBL_SendMesh() is finished it must send a serialized 'end magic number' which this function returns.  All outgoing streams must have this. ===
    return struct.pack('H', G.C_MagicNo_TranEnd)  ###DESIGN: A pain in the ass... revisit??

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
    if (sNameMesh not in bpy.data.objects):
        return G.DumpStr("ERROR: gBL_UpdateClientVerts() cannot find object '" + sNameMesh + "'")
    oMeshO = gBlender.SelectAndActivate(sNameMesh)
    oMeshO.data.use_fake_user = False  ###NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.  Make sure this is off in this context
    oMeshO.data.update(True, True)  ###IMPORTANT: Our modified Blender C code traps the above flags to update its shared data structures with client...        
    return G.DumpStr("OK: gBL_UpdateClientVerts() has updated Client mesh verts on mesh '{}'".format(sNameMesh))

def gBL_UpdateBlenderVerts(sNameMesh):  # Update the Blender verts from the Client verts.  Most of the magic happens in our modified Blender C code while calling update()
    if (sNameMesh not in bpy.data.objects):
        return G.DumpStr("ERROR: gBL_UpdateBlenderVerts() cannot find object '" + sNameMesh + "'")
    oMeshO = gBlender.SelectAndActivate(sNameMesh)
    oMeshO.data.use_fake_user = True        ###IMPORTANT: We turn on this flag to indicate to our Blender C code that we LOAD the verts from client (instead of sending arrays to client)  NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.
    oMeshO.data.update(True, True)          ###IMPORTANT: Our modified Blender C code traps the above flags to update its shared data structures with client...        
    oMeshO.data.use_fake_user = False       # Turn off the 'update Blender verts from Client' flag right away as it's created only for this call.
    return G.DumpStr("OK: gBL_UpdateBlenderVerts() has updated Blender mesh verts on mesh '{}'".format(sNameMesh))


###TODO?: Can see shape keys... all in absolute so need diff
# Need all shape keys at zero so we can read one shape key
# Why not 17K mesh???
# Then... store in array for C++, ship, ship head as mesh and morph in C++!  (Also construct struct for nipples!)



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    HEAD PROCESSING
#---------------------------------------------------------------------------    

def RemoveMatVerts(sNameMaterial):
    oMeshO = bpy.context.object
    
    for oMat in oMeshO.data.materials:
        if oMat.name.find(sNameMaterial) != -1:
            nMatIndex = oMeshO.data.materials.find(oMat.name)
            oMeshO.active_material_index = nMatIndex 
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.material_slot_select()
            bpy.ops.mesh.delete(type='FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.material_slot_remove()
    
    
def IsolateHead():  # DAZ cannot export only the head if we select the 17K level of detail mesh.  We remove materials and faces we don't need here to leave only the head    
    RemoveMatVerts("Neck")
    RemoveMatVerts("Torso")
    RemoveMatVerts("Nipple")
    RemoveMatVerts("Hip")
    RemoveMatVerts("Arm")
    RemoveMatVerts("Foot")
    RemoveMatVerts("Forearm")
    RemoveMatVerts("Hand")
    RemoveMatVerts("Leg")
    RemoveMatVerts("Fingernail")
    RemoveMatVerts("Toenail")
    RemoveMatVerts("Cornea")
    RemoveMatVerts("Sclera")
    RemoveMatVerts("EyeSurface")
    RemoveMatVerts("Iris")
    RemoveMatVerts("Pupil")
    RemoveMatVerts("Lacrimal")
    RemoveMatVerts("Tear")
    RemoveMatVerts("EyeSocket")
    RemoveMatVerts("Eyebrow")
    
#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    MAN MESH CLEANUP
#---------------------------------------------------------------------------    
#- From DAZ-exported man (no penis) with 'merge materials with common diffuse' on...
#- Unit scale on bones, then edit the bones and reduce 1/100
#- Unit scale on mesh, then edit the mesh verts and reduce 1/10000
#- Remove extra bones (ik)
#- Keep rotation as is (90x) on both root and mesh (like woman)

def ManCleanup_RemoveExtraMaterials():  # Remove extra materials from DAZ-imported man    
    #RemoveMatVerts("Cornea")
    #RemoveMatVerts("Sclera")
    RemoveMatVerts("EyeSurface")
    #RemoveMatVerts("Iris")
    #RemoveMatVerts("Pupil")
    RemoveMatVerts("Lacrimal")
    RemoveMatVerts("Tear")
    RemoveMatVerts("EyeSocket")
    RemoveMatVerts("Eyebrow")
    RemoveMatVerts("Eyelash")

    
#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CProp-based properties
#---------------------------------------------------------------------------    

def CProp_PropGet(sNameObject, sNameProp):
    if sNameObject not in bpy.data.objects:
        return G.DumpStr("ERROR: CProp_PropGet('{}', '{}') cannot find object {}".format(sNameObject, sNameProp, sNameObject))
    oObject = bpy.data.objects[sNameObject]
    return oObject.get(sNameProp)

def CProp_PropSet(sNameObject, sNameProp, oValue):
    if sNameObject not in bpy.data.objects:
        return G.DumpStr("ERROR: CProp_PropSet('{}', '{}', {}) cannot find object {}".format(sNameObject, sNameProp, oValue, sNameObject))
    oObject = bpy.data.objects[sNameObject]
    oObject[sNameProp] = oValue
    return "OK"
    
    
#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    MORPH EXTRACTION
#---------------------------------------------------------------------------    


def CMorphChannel_GetMorphVerts(sNameMesh, sNameShapeKey):  # Called by CBMeshMorph to get the morphed verts on a given shape key and a given mesh.  Used to morph non-skinned meshes at runtime such as face eyelids and mouth open/close
    oMeshO = gBlender.SelectAndActivate(sNameMesh)

    #=== Find requested shape key to obtain morph data ===
    if sNameShapeKey in oMeshO.data.shape_keys.key_blocks:  ###NOTROBUST
        oMeshO.active_shape_key_index = oMeshO.data.shape_keys.key_blocks.find(sNameShapeKey)  ###LEARN: How to find a key's index in a collection!
    else:
        return G.DumpStr("ERROR: CMorphChannel_GetMorphVerts() cannot find shape key " + sNameShapeKey);

    #=== Obtain access to shape key vert data ===        
    aKeys = oMeshO.data.shape_keys.key_blocks
    aVertsBakedKeys = aKeys[oMeshO.active_shape_key_index].data  # We obtain the vert positions from the 'baked shape key'
    bm = bmesh.new()  ###LEARN: How to operate with bmesh without entering edit mode!
    bm.from_object(oMeshO, bpy.context.scene)  ###DESIGN: Selection of body! 

    #=== Iterate through all the mesh verts and test all verts that are different for the given shape key so we can serialize its delta data to client
    oBA = bytearray()
    nMorphedVerts = 0
    for oVert in bm.verts:
        vecVert = oVert.co
        vecVertKey = aVertsBakedKeys[oVert.index].co
        if vecVert != vecVertKey:
            vecVertDelta = vecVertKey - vecVert
            # print("{}  #{} = {}".format(nMorphedVerts, oVert.index, vecVertDelta))
            oBA += struct.pack('i', oVert.index);
            gBlender.Stream_SendVector(oBA, vecVertDelta)
            nMorphedVerts += 1

    return oBA;
    
#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    TESTS
#---------------------------------------------------------------------------    

def Test():
    bpy.ops.mesh.primitive_cube_add()
    







#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    ####MOVE
#---------------------------------------------------------------------------    
   
def gBL_Cloth_SplitIntoSkinnedAndSimulated(sNameClothSimulated, sNameClothBase, sNameBody, sVertGrp_ClothSkinArea):
    # Separate 'sNameClothBase' cloth mesh between skinned and simulated parts, calculating the 'twin verts' that will pin the simulated part to the skinned part at runtime

    #=== Obtain reference to the needed meshes and duplicate cloth mesh ===
    oMeshBodyO = gBlender.SelectAndActivate(sNameBody)              # Obtain reference to source body for skin info transferred to skinned part of cloth.
    sNameClothSkinned = sNameClothBase + G.C_NameSuffix_ClothSkinned
    oMeshClothSimO = gBlender.DuplicateAsSingleton(sNameClothBase, sNameClothSimulated, G.C_NodeFolder_Game, True)  # Duplicate the source cloth into our working mesh (that will become our cloth-simulated part)

    #=== Transfer the skinning information from the skinned body mesh to the clothing.  Some vert groups are useful to move non-simulated area of cloth as skinned cloth, other _ClothSkinArea_xxx vert groups are to define areas of the cloth that are skinned and not simulated ===
    gBlender.SelectAndActivate(oMeshClothSimO.name)
    oMeshBodyO.select = True
    oMeshBodyO.hide = False  ###LEARN: Mesh MUST be visible for weights to transfer!
    bpy.ops.object.vertex_group_transfer_weight()

    #=== With the body's skinning info transfered to the cloth, select the the requested vertices contained in the 'skinned verts' vertex group.  These will 'pin' the cloth on the body while the other verts are simulated ===
    bpy.ops.object.mode_set(mode='EDIT')
    nVertGrpIndex_Pin = oMeshClothSimO.vertex_groups.find(sVertGrp_ClothSkinArea)       
    if nVertGrpIndex_Pin == -1:
        raise Exception("ERROR: gBL_Cloth_Create() could not find in skinned body pin vertex group " + sVertGrp_ClothSkinArea)
    oVertGroup_Pin = oMeshClothSimO.vertex_groups[nVertGrpIndex_Pin]
    oMeshClothSimO.vertex_groups.active_index = oVertGroup_Pin.index
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_select()                # To-be-skinned cloth verts are now selected

    #=== Prepare the to-be-split cloth mesh for 'twin vert' mapping: This vert-to-vert map between the skinned part of cloth mesh to simulated-part of cloth mesh is needed by Unity at runtime to 'pin' the edges of the simulated mesh to 'follow' the skinned part 
    bmClothSim = bmesh.from_edit_mesh(oMeshClothSimO.data)          # Create a 'custom data layer' to store unique IDs into mesh vertices so we can find what vert maps to what verts in the two separted meshes
    oLayVertTwinID = bmClothSim.verts.layers.int.new(G.C_PropArray_ClothSkinToSim)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
    aFacesToSplit = [oFace for oFace in bmClothSim.faces if oFace.select]           # Obtain array of all faces to separate so we can select them once edge loop is found

    #=== Determine the edges separating the skinned cloth mesh from the simulated one (removing edge-of-cloth edges) ===
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.region_to_loop()       # This will select only the edges at the boundary of the cutout polys... including edge of cloth, seams and the (needed) edges that connect split mesh to main mesh
    for oEdge in bmClothSim.edges:      # Iterate over the edges at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut
        if oEdge.select == True:
            if oEdge.is_manifold == False:  # Deselect the edges-on-edge (i.e. natural edge of cloth)
                oEdge.select_set(False)

    #=== Setup two maps (that will have the same size) to store for both simulated and skinned cloth parts what 'TwinVertID' maps to simVert / skinVert 
    aTwinIdToVertSim = {}           # Each of these will go from 1..<NumVertIDs> and be used to determine mapping
    aTwinIdToVertSkin = {}

    #=== Iterate over the split verts at the boundary loop to store a uniquely-generated 'twin vert ID' into the custom data layer so we can re-twin the split verts from different meshes after the mesh separate ===
    nNextVertTwinID = 1  
    aVertsBoundary = [oVert for oVert in bmClothSim.verts if oVert.select]              # Create a collection for all the verts on the boundary loop
    for oVert in aVertsBoundary:
        oVert[oLayVertTwinID] = nNextVertTwinID  # These are unique to the whole skinned body so all detached chunk can always find their corresponding skinned body vert for per-frame positioning
        #print("TwinID {:3d} = VertSim {:5d} at {:}".format(nNextVertTwinID, oVert.index, oVert.co))
        nNextVertTwinID += 1
        
    #=== Reselect the to-be-skinned faces again   ===
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bChunkMeshHasGeometry = False   # Determine if chunk mesh has any faces
    for oFace in aFacesToSplit:
        oFace.select_set(True)
        bChunkMeshHasGeometry = True

    #=== If chunk mesh has no geometry then we don't generate it as client has nothing to render / process for this chunk ===
    if bChunkMeshHasGeometry == False:
        print("\n>>> gBL_Cloth_Create() skips the creation of simulated cloth '{}' from body '{}' because it has no geometry to simulate <<<".format(sNameClothSkinned, sNameBody))
        return      ####DESIGN: A fatal failure??

    #=== Split and separate the skinned-part of the cloth from the simulated mesh (twin-vert IDs layer info will be copied to new mesh) ===
    bpy.ops.mesh.split()        # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
    bpy.ops.mesh.separate()     # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'

    #=== Post-process the just-detached chunk to calculate the 'twin verts' array between the skinned-part of cloth to simulated-part of cloth ===
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
    bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
    oMeshClothSkinnedO = bpy.context.object 
    oMeshClothSkinnedO.name = oMeshClothSkinnedO.data.name = sNameClothSkinned  ###NOTE: Do twice so name sticks!
    oMeshClothSkinnedO.name = oMeshClothSkinnedO.data.name = sNameClothSkinned

    #=== Post-process the skinned-part to be ready for Unity ===
    gBlender.Cleanup_VertGrp_RemoveNonBones(oMeshClothSkinnedO)     # Remove the extra vertex groups that are not skinning related from the skinned cloth-part
    Client_ConvertMesh(oMeshClothSkinnedO, False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!                   

    #=== Post-process the simulated-part to be ready for Unity ===
    Client_ConvertMesh(oMeshClothSimO, False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
    bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from detached chunk to save memory

    #=== Serialize the simulated mesh and its important map to be received by Unity's CCloth.  (Skinned part is requested in separate call as a standard skinned mesh) ===
    oBA = gBL_GetMesh(oMeshClothSimO.name, 'NoSkinInfo')               # Serialze the entire mesh (don't send skinning info)


    #===== ASSEMBLE THE TWIN VERT MAPPING =====
    #=== Iterate over the boundary verts of the simulated mesh to find their vertex IDs ===
    gBlender.SelectAndActivate(oMeshClothSimO.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bmMeshClothSim = bmesh.from_edit_mesh(oMeshClothSimO.data)
    oLayVertTwinID = bmMeshClothSim.verts.layers.int[G.C_PropArray_ClothSkinToSim]
    for oVert in bmMeshClothSim.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
        nTwinID = oVert[oLayVertTwinID]
        if nTwinID != 0:
            aTwinIdToVertSim[nTwinID] = oVert.index             # Remember what skin vert this TwinID maps to
            #print("TwinID {:3d} = VertSim {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    #=== Iterate through the boundary verts of the skinned part of the clto to access the freshly-created custom data layer to obtain ID information that enables us to match the skinned mesh vertices to the simulated cloth mesh for pinning ===
    gBlender.SelectAndActivate(oMeshClothSkinnedO.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bmMeshClothSkinned = bmesh.from_edit_mesh(oMeshClothSkinnedO.data)
    oLayVertTwinID = bmMeshClothSkinned.verts.layers.int[G.C_PropArray_ClothSkinToSim]
    for oVert in bmMeshClothSkinned.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
        nTwinID = oVert[oLayVertTwinID]
        if nTwinID != 0:
            aTwinIdToVertSkin[nTwinID] = oVert.index             # Remember what skin vert this TwinID maps to
            #print("TwinID {:3d} = VertSkin {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    #=== Assembled the serializable flat array of twin verts Unity needs to pin simulated cloth to skinned cloth part ===
    aMapTwinVerts = array.array('H')  # The final flattened map of what verts from the 'detached chunk part' maps to what vert in the 'skinned main body'  Client needs this to pin the edges of the softbody-simulated part to the main body skinned mesh
    for nTwinID in range(1, nNextVertTwinID):
        aMapTwinVerts.append(aTwinIdToVertSim [nTwinID])
        aMapTwinVerts.append(aTwinIdToVertSkin[nTwinID])
        #print("nTwinID {:3d} = VertSim {:4d} = VertSkin {:4d}".format(nTwinID, aTwinIdToVertSim[nTwinID], aTwinIdToVertSkin[nTwinID]))
    oMeshClothSimO[G.C_PropArray_ClothSkinToSim] = aMapTwinVerts.tobytes()  # Store the output map as an object property for later access when Client requests this part.  (We store as byte array to save memory as its only for future serialization to Client and Blender has no use for this info)  ###CHECK: We don't need to store?
    gBlender.Stream_SerializeArray(oBA, aMapTwinVerts.tobytes())       # Send the additional flat map we created above


    return oBA;                                                 # De-serialized by Unity's CCloth.  CCloth will requested the skinned mesh as a standard skinned mesh in later separate call




def BodyPrep_StoreOrigVertIDs(sNameMeshOrig):
    "Prepare an original untouched mesh for editing by storing its original vert indices in a custom data layer"
    ####TODO: Merge with other 'prep meshs' calls!
    gBlender.Cleanup_RemoveCustomDataLayers(sNameMeshOrig)          # Remove all layers for a clean start
    oMeshOrig = gBlender.SelectAndActivate(sNameMeshOrig)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(oMeshOrig.data)
    oLayVertsOrig = bm.verts.layers.int.new(G.C_DataLayer_VertsOrig)
    for oVert in bm.verts:
        oVert[oLayVertsOrig] = oVert.index + G.C_OffsetVertIDs          # We apply an offset so we can differentiate between newly added verts 
    bpy.ops.object.mode_set(mode='OBJECT')
   
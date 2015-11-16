#=== Problems ===
# Large vagina cutout means we can't morph body!
#   Find a way to subdivide vanilla mesh?
#   Or... Re-import from DAZ a body with a top-quality vagina mesh?
#   Related: Can we import DAZ meshes and blend them there?
# Assembled mesh can only display one UV at a time?? 

#=== Improve ===
# Store permutations of source body, genitals as cached meshes?  (If quick to do don't bother?)
# Comments for functions using standard """
# user assert!

#=== Strategy ===
# Revisit how meshes and data arrays are sent.  Unity makes call to go to a game mode and pulls what it needs from various classes
# Unify getting arrays from meshes
# Trim out clothing merged with softbody and vagina soft body
# BACKUP THE FUCKING CODE
# Have Unity make calls like (get softbody parts?) and it branches out?

import bpy
import sys
import bmesh
import array
from math import *
from mathutils import *
from bpy.props import *

import gBlender
import SourceReloader
import G
import Border
import Curve
import Cut
import Client
import CBBodyCol
import Breasts
import Penis


class CBody:
    _aBodies = []                      # The global array of bodies.  Unity finds bodies 

    def __init__(self, nBodyID, sMeshSource, sSex, sGenitals):
        CBody._aBodies.append(self)                         # Append ourselves to global array.  The only way Unity can find our instance is through CBody._aBodies[<OurID>]
        self.nBodyID            = nBodyID                   # Our ID is passed in by Blender and remains the only public way to access this instance (e.g. CBody._aBodies[<OurID>])
        self.sMeshSource        = sMeshSource               # The name of the source body mesh (e.g. 'WomanA', 'ManA', etc)
        self.sSex               = sSex                      # The body's sex (one of 'Man', 'Woman' or 'Shemale')
        self.sGenitals          = sGenitals                 # The body's genitals (e.g. 'Vagina-Erotic9-A', 'PenisW-Erotic9-A' etc.)
        self.sMeshPrefix        = "Body" + chr(65 + self.nBodyID) + '-'  # The Blender object name prefix of every submesh (e.g. 'BodyA-Detach-Breasts', etc)
        
        self.oMeshSource        = None                      # The 'source body'.  Never modified in any way
        self.oMeshAssembled     = None                      # The 'assembled mesh'.  Fully assembled with proper genitals.  Basis of oMeshMorph                  
        self.oMeshMorph         = None                      # The 'morphing mesh'.   Orinally copied from oMeshAssembled and morphed to the user's preference.  Basis of oMeshBody
        self.oMeshBody          = None                      # The 'body' skinned mesh.   Orinally copied from oMeshMorph.  Has softbody parts (like breasts and penis) removed. 
        self.oMeshBreasts       = None                      # The 'breasts' softbody-simulated mesh.   Detached from oMeshBody during creation.  
        self.oMeshPenis         = None                      # The 'penis'   softbody-simulated mesh.   Detached from oMeshBody during creation.  
        
        self.aMapVertsOrigToMorph   = {}                    # Map of which original vert maps to what morph/assembled mesh verts.  Used to traverse morphs intended for the source body                  
        
        print("\n=== CBody()  nBodyID:{}  sMeshPrefix:'{}'  sMeshSource:'{}'  sSex:'{}'  sGenitals:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sMeshSource, self.sSex, self.sGenitals))
    
        self.oMeshSource = bpy.data.objects[self.sMeshSource]
    
        #=== Duplicate the source body (kept in the most pristine condition possible) as the assembled body. Delete unwanted parts and attach the user-specified genital mesh instead ===    
        self.oMeshAssembled = gBlender.DuplicateAsSingleton(self.oMeshSource.name, self.sMeshPrefix + "Assembled", G.C_NodeFolder_Game, False)  # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
        sNameVertGroupToCutout = None
        if self.sGenitals.startswith("Vagina"):         # Woman has vagina and breasts
            sNameVertGroupToCutout = "_Cutout_Vagina"
        elif self.sGenitals.startswith("Penis"):        # Man & Shemale have penis
            sNameVertGroupToCutout = "_Cutout_Penis"
        if sNameVertGroupToCutout is not None:
            bpy.ops.object.mode_set(mode='EDIT')
            gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled, sNameVertGroupToCutout)     # This vert group holds the verts that are to be soft-body simulated...
            bpy.ops.mesh.delete(type='FACE')                    # ... and delete the mesh part we didn't want copied to output body
            bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== Import and preprocess the genitals mesh and assemble into this mesh ===
        oMeshGenitalsO = gBlender.DuplicateAsSingleton(self.sGenitals, "TEMP_Genitals", G.C_NodeFolder_Temp, True)  ###TEMP!! Commit to file-based import soon!
        #     bpy.ops.import_scene.obj(filepath="D:/Src/E9/Unity/Assets/Resources/Textures/Woman/A/Vagina/Erotic9/A/Mesh.obj")        ###HACK!!!: Path & construction of full filename!
        #     oMeshGenitalsO = bpy.context.selected_objects[0]        ###LEARN: object importer will deactivate everything and select only the newly imported object
        bpy.context.scene.objects.active = oMeshGenitalsO
        bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings
     
        #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
        self.oMeshAssembled.select = True
        bpy.context.scene.objects.active = self.oMeshAssembled
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')      # Deselect all verts in assembled mesh
        bpy.ops.object.mode_set(mode='OBJECT')
        ####LEARN: Screws up ConvertMesh royally!  self.oMeshAssembled.data.uv_textures.active_index = 1       # Join call above selects the uv texture of the genitals leaving most of the body untextured.  Revert to full body texture!   ###IMPROVE: Can merge genitals texture into body's??
        gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled, sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
        bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###LEARN: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 
        
        #=== Prepare a ready-for-morphing client-side body. This one will be morphed by the user and be the basis for cloth fitting and play mode ===   
        self.oMeshMorph = gBlender.DuplicateAsSingleton(self.oMeshAssembled.name, self.sMeshPrefix + 'BodyMorph', G.C_NodeFolder_Game, True)
        Client.Client_ConvertMesh(self.oMeshMorph, True)  # Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
        ####DEV: BODY only gets converted!


     
        #=== Assemble the 'aMapVertsOrigToMorph' map of mesh verts so we know which source vert goes to what assembled vert ===
        bpy.ops.object.mode_set(mode='EDIT')
        bmMorph = bmesh.from_edit_mesh(self.oMeshMorph.data)
        oLayOrigVertIDs = bmMorph.verts.layers.int[G.C_DataLayer_OrigVertIDs]  # Create a temp custom data layer to store the IDs of each original vert.  This enables future meshes to find the verts in original mesh
        for oVert in bmMorph.verts:
            self.aMapVertsOrigToMorph[oVert[oLayOrigVertIDs]] = oVert.index
            #print("Vert Assembled {:5d} = Source {:5d}".format(oVert.index, oVert[oLayOrigVertIDs]))        
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        self.oMeshSource.hide = True
        self.oMeshAssembled.hide = True
        #self.oMeshMorph.hide = True

#     
#         ####NOTE: Now merged def gBL_Body_Create(sMeshBodyGame, sSex, self.sGenitals, aCloths):  
#         ###IMPROVE: Get most of these args from morphed body!?
#         ###IMPROVE!! Detached breasts and penis still contain extra materials & vert groups... clean up?
#         ###HACK!!!!! Breast morphs in this call!  Needs to be broken up and done differently!!
#         ###OBS!?!?!?!: If we always get dynamic clothing ontop of breasts then why the extreme complexity of this function???
#     
#         #=== Assemble the list of meshes we have to create based on the sex of the character ===
#         if sSex == "Woman":      # Woman has vagina and breasts (includes clothing area)
#             aNameChunks = ["Breasts", "VaginaL", "VaginaR"]
#         elif sSex == "Man":       # Shemale has breasts, penis and penis area clothing
#             aNameChunks = ["Penis"]
#         elif sSex == "Shemale":       # Shemale has breasts, and penis
#             aNameChunks = ["Breasts", "Penis"]
#     
#     
#         #===== Begin the complex task of assembling the requested body =====    
#         #=== Obtain references to all the source meshes needed ===
#         oMeshBodyMorphO = gBlender.SelectAndActivate(sMeshBodyGame + G.C_NameSuffix_BodyMorph)  # Obtain reference to previously constructed body for morphing
#         sNameBodyRim = sMeshBodyGame + G.C_NameSuffix_BodyRim
#         gBlender.DeleteObject(sNameBodyRim)
#         oMeshComboO = gBlender.DuplicateAsSingleton(oMeshBodyMorphO.name, sMeshBodyGame + G.C_NameSuffix_BodySkin, G.C_NodeFolder_Game, False)  ###TODO!!! Rename to MeshCombo??      ###DESIGN: Base skinned mesh on _BodyMorph or virgin body??            
#         nBodyMats = len(oMeshComboO.data.materials)  # Before we join additional clothing meshes with to body remember the number of materials so we can easily spot the vertices of clothing in big loop below
#     
#     
#         #=== Prepare the cloth base by duplicating the requested bodysuit and converting for Client ===  ####OBS?  Only if cloth is split for some simulation with breasts soft body
#         for sCloth in aCloths:
#             if sCloth != "" and sCloth != "None":
#                 oMeshClothBaseO = gBlender.DuplicateAsSingleton(sCloth, sMeshBodyGame + G.C_NameSuffix_ClothBase, G.C_NodeFolder_Game, True)            
#                 gBlender.DuplicateAsSingleton(oMeshClothBaseO.name, sMeshBodyGame + G.C_NameSuffix_ClothCut, G.C_NodeFolder_Game, True)  ###HACK!: Just to enable gameplay mode all the way to play without going through cloth morph or cloth fit... revisit this crap!            
#                 gBlender.DuplicateAsSingleton(oMeshClothBaseO.name, sMeshBodyGame + G.C_NameSuffix_ClothFit, G.C_NodeFolder_Game, True)            
#                 oMeshClothO = gBlender.DuplicateAsSingleton(sMeshBodyGame + G.C_NameSuffix_ClothFit  , "_TEMP_ClothPart-Body", G.C_NodeFolder_Game, True)  ###DESIGN: Pass in cloth by array?  Support array iteration ###DESIGN: ###SOON: This is ALL clothing on the character, not just fit!
#             
#                 #=== Remove information from all-cloth Client doesn't need (such as the vertex groups used for border creation) ===
#                 gBlender.SelectAndActivate(oMeshClothO.name)
#                 gBlender.Util_ConvertToTriangles()
#                 if bpy.ops.object.vertex_group_remove.poll():
#                     bpy.ops.object.vertex_group_remove(all=True)
#             
#                 #=== Split the edges on the all-cloth marked as 'sharp' (such as between border and cloth) to give two verts for each border vert with two different normals ===
#                 oModEdgeSplit = oMeshClothO.modifiers.new('EDGE_SPLIT', 'EDGE_SPLIT')
#                 oModEdgeSplit.use_edge_sharp = True  # We only want edge split to split edges marked as sharp (done in border creation)
#                 oModEdgeSplit.use_edge_angle = False
#                 gBlender.AssertFinished(bpy.ops.object.modifier_apply(modifier=oModEdgeSplit.name))
#                 
#                 #=== Transfer the skinning information from the skinned body mesh to the clothing.  Some vert groups are useful to move non-simulated area of cloth as skinned cloth, other _Detach_xxx vert groups are to define areas of the cloth that are simulated ===
#                 gBlender.SelectAndActivate(oMeshClothO.name)
#                 oMeshBodyMorphO.select = True
#                 oMeshBodyMorphO.hide = False  ###LEARN: Mesh MUST be visible for weights to transfer!
#                 bpy.ops.object.vertex_group_transfer_weight()
#             
#                 #=== Join the all-cloth onto the main skinned body to form the composite mesh that currently has all geometry for body and all clothing...  From this composite mesh we separate 'chunks' such as breasts are surrounding clothing, or penis or vagina for non-skinned simulation by the game engine ===
#                 gBlender.SelectAndActivate(oMeshComboO.name)
#                 oMeshClothO.select = True
#                 bpy.ops.object.join()  # This will join the cloth and its properly-set 'detach chunk' vertex groups to the body with matching chunk vertex groups.
#                 oMeshClothO = None  # Past this point clothing mesh doesn't exist... only oMeshComboO which has entire body and all clothing
#     
#     
#         #=== Prepare the composite mesh for 'twin vert' mapping: The map that tells Client what vert from this detached chunk match what vert from the main skinned body ===
#         bpy.ops.object.mode_set(mode='EDIT')
#         bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)  # Create a 'custom data layer' to store unique IDs into mesh vertices so matching parts of the chunks we separate into other meshes can be easily matched to the main skinned mesh (for Client pinning)
#         oLayVertTwinID = bmCombo.verts.layers.int.new(G.C_DataLayer_TwinVert)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
#         nNextVertTwinID = 1  # We set the next twin vert ID to one.  New IDs for all detachable chunks will be created from this variable by incrementing.  This will enable each detached chunk to find what skinned vert from the body it needs to connect to during gameplay.
#         aaMapTwinId2VertChunk = {}  # Map of maps we use to enable aMapTwinId2VertChunk to traverse the major loop that creates it to another loop at the end that needs it.
#     
#     
#         
#         #===== MAIN SEPERATION PROCESSING FOR EACH 'SEPERABLE CHUNKS' =====  Breasts take ownership of clothing around them to be processed on their mesh as softbody.  Penis and vagina need processing here to to cap, twin and separate
#         for sNameChunk in aNameChunks:
#             print("--- Separating chunk " + sNameChunk)
#             sNamePartChunk = sMeshBodyGame + G.C_VertGrp_Detach + sNameChunk
#             gBlender.DeleteObject(sNamePartChunk)
#             gBlender.SelectAndActivate(oMeshComboO.name)
#             bpy.ops.object.mode_set(mode='EDIT')
#             bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
#     
#             #=== Obtain the 'detach chunks' vertex group from the combo mesh that originally came from the source body.  This 'detach chunk' will be updated for chunks such as breasts to append to it the verts of neighboring clothing so they will also be softbody simulated  ===
#             nVertGrpIndex_DetachChunk = oMeshComboO.vertex_groups.find(G.C_VertGrp_Detach + sNameChunk)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
#             if nVertGrpIndex_DetachChunk == -1:
#                 oMeshComboO.vertex_groups.new(name=G.C_VertGrp_Detach + sNameChunk)
#             oVertGroup_DetachChunk = oMeshComboO.vertex_groups[nVertGrpIndex_DetachChunk]
#             oMeshComboO.vertex_groups.active_index = oVertGroup_DetachChunk.index
#         
#             #=== For non-body detach areas such a clothing around breasts and dynamic cloth around penis, refine the clothing area that is be non-skinned / simulated by selecting vertices by pre-defined bounding spheres (set individually for each type) ===
#             if sNameChunk == "Breasts" or sNameChunk == "PenisArea":  # Breasts and PenisArea area are the two 'detach chunk' that can have cloth around them that must take part in external simulation.  'Refine' their selection below...
#                 bpy.ops.mesh.select_all(action='DESELECT')
#                 bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)
#                 oCutSphere = bpy.data.objects["CutSphere-" + sNameChunk]  ###CHECK!            ###IMPROVE?: Cut sphere for penis changes with starting position of penis?? (Not if starts straight as soft body!)
#                 vecSphereCenterL = oCutSphere.location.copy()  ###LEARN: If we don't copy next line moves sphere!!
#                 vecSphereCenterR = vecSphereCenterL.copy()  ###LEARN: If we don't copy, next line inverts x on both vectors!
#                 vecSphereCenterR.x = -vecSphereCenterR.x  # The '2nd' sphere is just the sphere #1 mirrored about x
#                 vecSphereCenterC = (vecSphereCenterL + vecSphereCenterR) / 2 
#                 nSphereRadius = oCutSphere.dimensions.x / 2
#                 bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  ###LEARN: If View3D were in any other mode the following code would NOT select!!  WTF???
#                 for oVert in bmCombo.verts:
#                     if oVert.link_faces[0].material_index >= nBodyMats:  # We're only interested in non-body verts for cloth area-detection.  (Body already has well formed vert groups for these chunks.)
#                         vecVert = oMeshComboO.matrix_world * oVert.co                                   
#                         vecVertToSphereCenterL = vecVert - vecSphereCenterL
#                         vecVertToSphereCenterR = vecVert - vecSphereCenterR
#                         vecVertToSphereCenterC = vecVert - vecSphereCenterC
#                         if vecVertToSphereCenterL.magnitude < nSphereRadius or vecVertToSphereCenterR.magnitude < nSphereRadius or vecVertToSphereCenterC.magnitude < nSphereRadius:
#                             oVert.select_set(True)
#                 bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')  # We expand the selection of verts to faces to ensure we don't cut out verts left hanging by an edge
#                 aVertsDetachChunk = [oVert.index for oVert in bmCombo.verts if oVert.select]
#                 bpy.ops.object.mode_set(mode='OBJECT')
#                 oVertGroup_DetachChunk.add(index=aVertsDetachChunk, weight=0.0, type='REPLACE')  # Add the verts to be detached from cloth to the appropriate detach vert group with weight zero (so it doesn't interfere with bones)
#     
#             #=== Detach the currently-processed 'chunk' from the source composite mesh.  One chunk for each separate softbody/cloth simulation ===
#             bpy.ops.object.mode_set(mode='EDIT')
#             bpy.ops.mesh.select_all(action='DESELECT')
#             bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
#             bmCombo = bmesh.from_edit_mesh(oMeshComboO.data)  ###LEARN!!: We must re-obtain new bmesh everytime we re-enter edit mode.  (And of course old bmesh object references are gone but IDs persist!)
#             oLayVertTwinID = bmCombo.verts.layers.int[G.C_DataLayer_TwinVert]  # Refetch our custom data layer because we exited edit mode...
#             aFacesToSplit = [oFace for oFace in bmCombo.faces if oFace.select]  # Obtain array of all faces to separate
#         
#             #=== Store the boundary edges of the split into the new vertex group so we can provide Client the mapping of split verts between the meshes ===
#             bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#             bpy.ops.mesh.region_to_loop()  # This will select only the edges at the boundary of the cutout polys... including edge of cloth, seams and the (needed) edges that connect split mesh to main mesh
#             for oEdge in bmCombo.edges:  # Iterate over the edges at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut
#                 if oEdge.select == True:
#                     if oEdge.is_manifold == False:  # Deselect the edges-on-edge (i.e. natural edge of cloth)
#                         oEdge.select_set(False)
#             ###HACK ###IMPROVE ###DESIGN: Important limitation of the above code appears when attempting to separate Penis at its natural mesh boundary (at the endge of its material)
#             ### Because we need to separate from the Client-ready morphed body, the penis mesh in that mesh is already separated from main skinned mesh at its material boundary...  Making this call's attempt to twin verts impossible.
#             ### A hack was adopted by setting the 'seperatable mesh' of penis one ring of vertices less than its materials, so that this code can twin verts and the runtime to attach softbody penis to skinned main body mesh.
#             ### An improvement could be created to enable traversal of the duplicated verts because of material and properly twin the penis mesh verts to the verts that are really on the skinned body mesh.
#         
#             #=== Iterate over the split verts to store a uniquely-generated 'twin vert ID' into the custom data layer so we can re-twin the split verts from different meshes after the mesh separate ===
#             aVertsBoundary = [oVert for oVert in bmCombo.verts if oVert.select]
#             for oVert in aVertsBoundary:
#                 oVert[oLayVertTwinID] = nNextVertTwinID  # These are unique to the whole skinned body so all detached chunk can always find their corresponding skinned body vert for per-frame positioning
#                 nNextVertTwinID += 1
#         
#             #=== Reselect the faces again to split the 'detachable chunk' into its own mesh so that it can be sent to softbody/cloth simulation.  ===
#             bpy.ops.mesh.select_all(action='DESELECT')
#             bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
#             bChunkMeshHasGeometry = False  # Determine if chunk mesh has any faces
#             for oFace in aFacesToSplit:
#                 oFace.select_set(True)
#                 bChunkMeshHasGeometry = True
#         
#             #=== If chunk mesh has no geometry then we don't generate it as client has nothing to render / process for this chunk ===
#             if bChunkMeshHasGeometry == False:
#                 print("\n>>> GameMode_Play_PrepBody() skips creation of chunk mesh '{}' from body '{}' because it has no geometry <<<".format(sNameChunk, sMeshBodyGame))
#                 continue
#         
#             #=== Split and separate the chunk from the composite mesh ===
#             bpy.ops.mesh.split()  # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
#             bpy.ops.mesh.separate()  # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
#         
#             #===== Post-process the just-detached chunk to calculate the 'twin verts' array between it and the main skinned main body =====
#             #=== Fetch the just-split body part + cloths 'detach chunk' so we can calculate 'matching' information to 'twin' the previously connected verts together (to pin a simulated area of mesh to the skinned mesh) ===    
#             bpy.ops.object.mode_set(mode='OBJECT')
#             bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#             bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
#             oMeshPartChunkO = bpy.context.object 
#             oMeshPartChunkO.name = oMeshPartChunkO.data.name = sNamePartChunk  ###NOTE: Do twice so name sticks!
#             oMeshPartChunkO.name = oMeshPartChunkO.data.name = sNamePartChunk
#             bpy.ops.object.vertex_group_remove(all=True)  # Remove all vertex groups from detached chunk to save memory
#         
#             #=== Iterate through the verts of the newly separated chunk to access the freshly-created custom data layer to obtain ID information that enables us to match the chunk mesh vertices to the main skinned mesh for pinning ===
#             bpy.ops.object.mode_set(mode='EDIT')
#             bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#             bmPartChunk = bmesh.from_edit_mesh(oMeshPartChunkO.data)
#             oLayVertTwinID = bmPartChunk.verts.layers.int[G.C_DataLayer_TwinVert]
#             aMapTwinId2VertChunk = {}
#             for oVert in bmPartChunk.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
#                 nTwinID = oVert[oLayVertTwinID]
#                 if nTwinID != 0:
#                     aMapTwinId2VertChunk[nTwinID] = oVert.index
#                     if oVert.link_faces[0].material_index < nBodyMats:  # For capping below, select only the twin verts that are on one of the body's original material
#                         oVert.select_set(True)
#                     # print("TwinVert {:3d} = PartVert {:5d} mat {:} at {:}".format(nTwinID, oVert.index, oVert.link_faces[0].material_index, oVert.co))
#             aaMapTwinId2VertChunk[sNameChunk] = aMapTwinId2VertChunk  # Store our result in top-level map so loop near end of this function can finish the work once whole rim has been created.
#             
#             #=== Cap the body part that is part of the chunk (edge verts from only that body part are now selected)  If this chunk has no body verts (e.g. PenisClothing) then no capping will occur) ===
#             bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')  ###BUG?? ###CHECK: Possible that edge collapse could fail depending on View3D mode...
#             bpy.ops.mesh.extrude_edges_indiv()  ###LEARN: This is the function we need to really extrude!
#             bpy.ops.mesh.edge_collapse()  ###DESIGN ###IMPROVE Do we always cap whatever body part is ripped out?
#             for oVert in bmPartChunk.verts:  # The cap vert(s) created will have copied one of the 'VertTwinID'.  Wipe it out to avoid corrupting matching below 
#                 if oVert.select:
#                     oVert[oLayVertTwinID] = 0
#             bpy.ops.mesh.select_all(action='DESELECT')
#     
#             #=== Do the important conversion of the chunk mesh to be renderable by the Client... we're done processing that mesh. ===
#             Client_ConvertMesh(oMeshPartChunkO, True)


def CBody_Create(nBodyID, sMeshSource, sSex, sGenitals):
    "Proxy for CBody ctor as we can only return primitives back to Unity"
    oBody = CBody(nBodyID, sMeshSource, sSex, sGenitals)
    return str(oBody.nBodyID)           # Strings is one of the only things we can return to Unity

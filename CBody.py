###RESUME:
# Now fucking pos & normal working!!  Trim out the map creation in separation... refactor the map creation in rimming  Cleanup Unity!
# Work on the rim normals and rim pos
# Mesh temp still there!
# Start cleaning up!!!

### Had to disabled stupid normal counter in get mesh... fucking thing obsolete??
# Can now serialzie map!  Change Unity class to the one that bakes and pin tetraverts!
# clean up!!!!!!!

###DEVNOW: CAN FINALLY FUCKING JOIN AND IDENTIFY NEIGHBOR VERTS!  Now delete, map to orig verts, make sure layers ok (no conflict with body layer), the rest of the shit!
### One breast or both??
### Detach twin verts for normals only??
### Store twin verts... rename perhaps??
### Problem with UV maps?  Can remove one?  What about penis / vagina?

#### Can now get skinned breast back to Unity again... Feed tetra verts back to Blender, skin and send new matching skinned mesh (new class!!)

# Feed breasts back to Unity
# Fix softbody serialize
# Feed to PhysX and obtain Tetra mesh
# Feed tetramesh to Blender
# Isolate pinned tetraverts (close to body and ribcage)
# Skin pinned tetraverts (one mesh per softbody (no combination for simplicity)
# Send mesh to Unity with arrays that connect pinned tetraverts to softbody tetraverts
# Ger rid of old pin implementation!
     


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
        self.oMeshFace          = None                      # The 'face mesh'  Simply referenced here to service Unity's request for it  
        self.oMeshTemp          = None                      # The one and only 'temporary mesh'.  Used to pass from Unity to Blender the tetra verts for softbody pinning.  
        self.aMeshSoftBodies    = {}                        # Collection of meshes representing softbody-simulated meshes.  (Contains items such as 'Breasts', 'Penis', 'Vagina', to point to their meshes)
        self.aMeshSoftBodiesRim = {}                        # Collection of meshes representing 'softbody rim meshes.  (Contains items such as 'Breasts', 'Penis', 'Vagina', to point to their meshes)
        
        self.aMapVertsOrigToMorph   = {}                    # Map of which original vert maps to what morph/assembled mesh verts.  Used to traverse morphs intended for the source body                  
        
        print("\n=== CBody()  nBodyID:{}  sMeshPrefix:'{}'  sMeshSource:'{}'  sSex:'{}'  sGenitals:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sMeshSource, self.sSex, self.sGenitals))
    
        self.oMeshSource = bpy.data.objects[self.sMeshSource]
        self.oMeshFace = bpy.data.objects[self.sMeshSource + "-Face"]
    
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
        
        #=== Prepare a ready-for-morphing body for Unity.  Also create the 'body' mesh that will have parts detached from it where softbodies are ===   
        self.oMeshMorph = gBlender.DuplicateAsSingleton(self.oMeshAssembled.name, self.sMeshPrefix + 'BodyMorph',   G.C_NodeFolder_Game, True)
        self.oMeshBody  = gBlender.DuplicateAsSingleton(self.oMeshAssembled.name, self.sMeshPrefix + 'Body',        G.C_NodeFolder_Game, True)



    
    def SeparateSoftBodyPart(self, sNameChunk):
        print("CBody.SeparateSoftBodyPart()  chunk = " + sNameChunk)
     
        nBodyMats = len(self.oMeshBody.data.materials)  ####OBS??? ###DEV Before we join additional clothing meshes with to body remember the number of materials so we can easily spot the vertices of clothing in big loop below
     
        #=== Prepare the composite mesh for 'twin vert' mapping: The map that tells Client what vert from this detached chunk match what vert from the main skinned body ===
        sNamePartChunk = self.sMeshPrefix + "Detach-" + sNameChunk         # Create name for to-be-created detach mesh and open the body mesh
        sNamePartChunkRim = sNamePartChunk + "-Rim"                         # The name of the 'softbody rim' mesh (for pinning softbody to skinned body) 
        gBlender.DeleteObject(sNamePartChunk)
        gBlender.SelectAndActivate(self.oMeshBody.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bmBody = bmesh.from_edit_mesh(self.oMeshBody.data)
        oLayVertTwinID = bmBody.verts.layers.int.new(G.C_DataLayer_TwinVert)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
        nNextVertTwinID = 1                 # We set the next twin vert ID to one.  New IDs for all detachable chunks will be created from this variable by incrementing.  This will enable each detached chunk to find what skinned vert from the body it needs to connect to during gameplay.
 
        #=== Obtain the 'detach chunks' vertex group of name 'sNameChunk' from the combo mesh that originally came from the source body ===
        nVertGrpIndex_DetachChunk = self.oMeshBody.vertex_groups.find(G.C_VertGrp_Detach + sNameChunk)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
        oVertGroup_DetachChunk = self.oMeshBody.vertex_groups[nVertGrpIndex_DetachChunk]
        self.oMeshBody.vertex_groups.active_index = oVertGroup_DetachChunk.index
     
        #=== Prepare the part to be detached by first obtaining its list of faces ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
        bmBody = bmesh.from_edit_mesh(self.oMeshBody.data)  ###LEARN!!: We must re-obtain new bmesh everytime we re-enter edit mode.  (And of course old bmesh object references are gone but IDs persist!)
        oLayVertTwinID = bmBody.verts.layers.int[G.C_DataLayer_TwinVert]  # Refetch our custom data layer because we exited edit mode...
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
        if bChunkMeshHasGeometry == False:      ####OBS?
            raise Exception("###ERROR: SeparateSoftBodyPart() skips creation of chunk mesh '{}' from body '{}' because it has no geometry <<<".format(sNameChunk, self.sMeshPrefix))
     
        #=== Split and separate the chunk from the composite mesh ===
        bpy.ops.mesh.split()        # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
        bpy.ops.mesh.separate()     # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
        bpy.ops.object.mode_set(mode='OBJECT')

        #=== Name the newly created mesh as the requested 'detached chunk' ===      
        bpy.context.object.select = False           ###LEARN: Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        oMeshChunkO = bpy.context.object 
        oMeshChunkO.name = oMeshChunkO.data.name = sNamePartChunk  ###NOTE: Do twice so name sticks!
        oMeshChunkO.name = oMeshChunkO.data.name = sNamePartChunk
        self.aMeshSoftBodies[sNameChunk] = oMeshChunkO          # Store the requested chunk in our collection of softbody meshes so client can easily access 
        
        #=== Iterate through the verts of the newly separated chunk to access the freshly-created custom data layer to obtain ID information that enables us to match the chunk mesh vertices to the main skinned mesh for pinning ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmPartChunk = bmesh.from_edit_mesh(oMeshChunkO.data)
        oLayVertTwinID = bmPartChunk.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertChunk = {}
        for oVert in bmPartChunk.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertChunk[nTwinID] = oVert.index
                if oVert.link_faces[0].material_index < nBodyMats:  # For capping below, select only the twin verts that are on one of the body's original material
                    oVert.select_set(True)
                #print("TwinVert {:3d} = PartVert {:5d} mat {:} at {:}".format(nTwinID, oVert.index, oVert.link_faces[0].material_index, oVert.co))
        ###DEV aaMapTwinId2VertChunk[sNameChunk] = aMapTwinId2VertChunk  # Store our result in top-level map so loop near end of this function can finish the work once whole rim has been created.
         
        #=== Cap the body part that is part of the chunk (edge verts from only that body part are now selected)  If this chunk has no body verts (e.g. PenisClothing) then no capping will occur) ===
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')  ###BUG?? ###CHECK: Possible that edge collapse could fail depending on View3D mode...
        bpy.ops.mesh.extrude_edges_indiv()      ###LEARN: This is the function we need to really extrude!
        bpy.ops.mesh.edge_collapse()            ###DESIGN ###IMPROVE Do we always cap whatever body part is ripped out?
        for oVert in bmPartChunk.verts:         # The cap vert(s) created will have copied one of the 'VertTwinID'.  Wipe it out to avoid corrupting matching below 
            if oVert.select:
                oVert[oLayVertTwinID] = 0           ###OPT: Iterate through whole mesh to find one selected vert?
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')


        #===== Create the 'Skinned Rim' skinned mesh that Client can use to use 'BakeMesh()' on a heavily-simplified version of the main body mesh that contains only the 'rim' polygons that attach to all the detacheable chunks this code separates.  It is this 'Rim' skinned mesh that quickly calculates the position of all the pins and that therfore 'owns' the CPinSkinned and therefore the CPinTetra === 
        ####DESIGN: Vert topology changes at every split!  MUST map twinID to body verts once all cuts done ###NOW!!!
        #=== Iterate through the verts of the main skinned mesh (now that all chunks have been removed) to select all the twin verts so we can create the rim mesh
        gBlender.SelectAndActivate(self.oMeshBody.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmBody = bmesh.from_edit_mesh(self.oMeshBody.data)
        oLayVertTwinID = bmBody.verts.layers.int[G.C_DataLayer_TwinVert]
        for oVert in bmBody.verts:
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                oVert.select_set(True)  # Select this edge boundary vertex for the upcoming code in which we expand the rim selection to create the rim submesh
    
        #=== Select the faces neighboring the twin verts and duplicate them into the new 'rim mesh'
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='EDGE')  # ... With the rim verts selected two loops ago expand these 'boundary verts' into edge mode any edge touching the boundary verts are edges are selected (including non-boundary ones)...
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')  # ... then switch to poly mode to have the smallest set of polygons that have an edge at the boundary are left selected.  These will form their own 'reduced skin mesh' that will be baked at every frame to calculate pin positions
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate()  # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
        bmBody.verts.layers.int.remove(oLayVertTwinID)  # Remove the temp data layer in the skin mesh as the just-separated mesh has the info now...
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== Fetch the just-created 'rim' skinned mesh and set it to its proper name ===
        bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        oMeshChunkRimO = bpy.context.object
        oMeshChunkRimO.name = oMeshChunkRimO.data.name = sNamePartChunkRim  ###NOTE: Do it twice to ensure name really sticks  ###WEAK: Wish this was easier to do!
        oMeshChunkRimO.name = oMeshChunkRimO.data.name = sNamePartChunkRim
        self.aMeshSoftBodiesRim[sNameChunk] = oMeshChunkRimO         # Store the requested chunk rim in our collection of softbody rim meshes so client can easily access 
        ####DEV??? del(oMeshChunkRimO[G.C_PropArray_MapSharedNormals])  # Source skinned body has the shared normal array which is not appropriate for rim.  (Serialization would choke)
    
        #=== Cleanup the rim mesh by removing all materials ===
        while len(oMeshChunkRimO.material_slots) > 0:  ###IMPROVE: Find a way to remove doubles while preventing key-not-found errors in twin hunt below??
            bpy.ops.object.material_slot_remove()
        bpy.ops.object.material_slot_add()  # Add a single default material (captures all the polygons of rim) so we can properly send the mesh over (crashes if zero material)
        
        #=== Iterate over the rim vertices, and find the rim vert for every 'twin verts' so next loop can map chunk part verts to rim verts for pinning === 
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bmSkinColSrc = bmesh.from_edit_mesh(oMeshChunkRimO.data)
        oLayVertTwinID = bmSkinColSrc.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertRim = {}
        for oVert in bmSkinColSrc.verts:
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertRim[nTwinID] = oVert.index
                # print("TwinVert {:3d} = RimVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
        bpy.ops.object.mode_set(mode='OBJECT')
        gBlender.Cleanup_VertGrp_RemoveNonBones(oMeshChunkRimO)  # Remove the extra vertex groups that are not skinning related


        #===== Now that rim is fully formed and the aMapTwinId2VertRim fully populated for to find real rim verts for any TwinID we can finally construct the aMapTwinVerts flat array for each detached part.  (each detached part (no matter if its softbody or cloth simulated) will thereby be able to fix its edge verts to the rim correctly during gameplay) (With both the main skinned mesh and the chunk part with the same set of 'twin ID' in their mesh vertices, we can finally match vertex ID of part to vertex ID of skinned main mesh)
        ###NOTE: This flattened is sent with 1) vertex ID on the separated chunk part, 2) Vertex ID of the 'twin vert' at the same location on the main skinned mesh and 3) an adjacent vert on the skinned mesh to #2 for normal Z-orientation
        aMapTwinVerts = array.array('H')  # The final flattened map of what verts from the 'detached chunk part' maps to what vert in the 'skinned main body'  Client needs this to pin the edges of the softbody-simulated part to the main body skinned mesh
        print("--- Mapping twinned verts on mesh chunk " + sNameChunk)  # + str(aMapTwinId2VertChunk))
        for nTwinID in aMapTwinId2VertChunk:
            nVertTwinChunk = aMapTwinId2VertChunk[nTwinID]
            if nTwinID in aMapTwinId2VertRim:
                nVertTwinRim = aMapTwinId2VertRim[nTwinID]
                aMapTwinVerts.append(nVertTwinChunk)
                aMapTwinVerts.append(nVertTwinRim)
                print("TwinVert {:3d} = PartVert {:5d} = RimVert {:5d}".format(nTwinID, nVertTwinChunk, nVertTwinRim))
            else:
                G.DumpStr("###ERROR in CBody.SeparateSoftBodyPart(): Mapping of twin verts from TwinID to RimVert Could not find TwinID {} while processing chunk '{}' on mesh '{}' (Obscure corner-case algorithm error that rest of code can probably recover from...)".format(nTwinID, sNameChunk, oMeshChunkO.name))  # Obscure corner case that appears with Vagina L/R... Perhaps because split-point verts are in same position??  Check if this influences the game... 
        oMeshChunkO[G.C_PropArray_MapTwinVerts] = aMapTwinVerts.tobytes()  # Store the output map as an object property for later access when Client requests this part.  (We store as byte array to save memory as its only for future serialization to Client and Blender has no use for this info)
     
        return "OK"         ####IMPROVE: Error return through string??




    def CreateTempMesh(self, nVerts):           ###DEV Rename, make sure temp mesh destroyed in Client and released
        "Create a temporary oMesh with 'nVerts' vertices.  Used by Unity to pass Blender a tetramesh for softbody pinning"
        #=== Create the necessary number of verts for the new temp mesh.  (Unity will pass in its verts for us to process) ===
        aVerts = []
        for nVert in range(nVerts):
            aVerts.append((0,0,0))
            
        #=== Create the verts-only mesh with just verts ===
        oMesh = bpy.data.meshes.new("TEMP_MESH")        ###DEV: When to remove?
        oMeshO = bpy.data.objects.new(oMesh.name, oMesh)
        oMeshO.rotation_euler.x = radians(90)          # Rotate temp mesh 90 degrees like every other mesh.  ###IMPROVE: Get rid of 90 rotation EVERYWHERE!!
        bpy.context.scene.objects.link(oMeshO)
        oMesh.from_pydata(aVerts,[],[])
        oMesh.update(calc_edges=True)
        self.oMeshTemp = oMeshO              ###DEV???

        return "OK"     ###TEMP
    
    
    def SoftBody_CreateSoftBodyRimMesh(self, sMeshRim, nDistTetraVertsFromRim):
        "Create the softbody rim mesh from the tetraverts Unity just pushed into our self.oMeshTemp.  Updates rim mesh 'sMeshRim' currently containing only rim.  This mesh will be responsible to 'pin' some softbody tetraverts to the skinned body so softbody doesn't 'fly out'"
        print("-- SoftBody_CreateSoftBodyRimMesh({}) --".format(sMeshRim));

        oMeshChunkO = self.aMeshSoftBodies   [sMeshRim]           # Obtain reference to requested mesh chunk 
        oMeshRimO   = self.aMeshSoftBodiesRim[sMeshRim]           # Obtain reference to requested rim mesh.  (Previous created in CBody.SeparateSoftBodyPart() 
        oMeshRimCopyO = gBlender.DuplicateAsSingleton(oMeshRimO.name, "TEMP_CreateSoftBodyRimMesh", G.C_NodeFolder_Temp, False)     # Create a temp copy of rim mesh so we can transfer weights efficiently from it to new mesh including tetraverts

        #=== Open the temp mesh Unity requested in CreateTempMesh() and push in a data layer with vert index.  This will prevent us from losing access to Unity's tetraverts as we process this mesh toward the softbody rim ===        
        gBlender.SelectAndActivate(self.oMeshTemp.name)
        nVertsTetra = len(self.oMeshTemp.data.vertices)          # Remember how many tetra verts we have so we can tell them apart after join below (vert index won't change, just appends new ones)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bm = bmesh.from_edit_mesh(self.oMeshTemp.data)
 
        #=== Create the custom data layer and store vert indices into it === 
        oLayTetraVerts = bm.verts.layers.int.new(G.C_DataLayer_TetraVerts)        ###DEV!!! Old collection!!!!!!!
        C_OffsetTetraVertIndex = 1000000                # Offset given to IDs pushed into tetravert layer.  To avoid considering 0 as a valid index
        for oVert in bm.verts:
            oVert[oLayTetraVerts] = oVert.index + C_OffsetTetraVertIndex    # Apply offset to easily tell real IDs in later loop
        bpy.ops.object.mode_set(mode='OBJECT')
        
        #===== Combine the tetravert-mesh with the rim mesh of that softbody.  We need to isolate the tetraverts close to the rim verts to 'pin' them =====
        ###LEARN: Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh)
        gBlender.SelectAndActivate(self.oMeshTemp.name)             # First select and activate mesh that will be destroyed (temp mesh)
        oMeshRimO.select = True                                     # Now select...
        bpy.context.scene.objects.active = oMeshRimO                #... and activate mesh that will be kepp (merged into)  (Note that to-be-destroyed mesh still selected!) 
        bpy.ops.object.join()                                       #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??

        #===== Remove the tetraverts that are too far from the rim =====
        #=== Select the rim verts in the joined mesh ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(oMeshRimO.data)
        oLayTetraVerts = bm.verts.layers.int[G.C_DataLayer_TetraVerts]
        for oVert in bm.verts:
            if (oVert.index > nVertsTetra):
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
        oMeshRimCopyO.select = True                             # Select the original rim mesh (keeping rim+tetraverts mesh activated)
        bpy.ops.object.vertex_group_transfer_weight()
        gBlender.DeleteObject(oMeshRimCopyO.name)               # Delete the temporary rim mesh


        #===== Create the 'map pin tetraverts to tetravert' =====
        gBlender.SelectAndActivate(oMeshRimO.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(oMeshRimO.data)
        oLayTetraVerts = bm.verts.layers.int[G.C_DataLayer_TetraVerts]
        aMapRimTetravert2Tetravert = array.array('H')               # This array stores pairs of <#RimTetravert, #Tetravert> so Unity can pin the softbody tetraverts from the rim tetravert skinned mesh

        #=== Iterate through tetraverts to fill in its map traversal ===
        #print("\n=== CreateSoftBodyRimMesh mapping ===");
        for oVert in bm.verts:                                                                        
            nTetraVertID = oVert[oLayTetraVerts]
            if (nTetraVertID >= C_OffsetTetraVertIndex):            # The real tetraverts are over this offset (as created above)
                nTetraVertID -= C_OffsetTetraVertIndex              # Retrieve the non-offsetted tetravert
                aMapRimTetravert2Tetravert.append(oVert.index)
                aMapRimTetravert2Tetravert.append(nTetraVertID)
                #print("RimTetravert {:4d} = Tetravert {:4d}". format(oVert.index, nTetraVertID))
        oMeshRimO['aMapRimTetravert2Tetravert'] = aMapRimTetravert2Tetravert.tobytes()        # Store our map into mesh so Unity can retrieve





        #=== Iterate over the rim vertices, and find the rim vert for every 'twin verts' so next loop can map chunk part verts to rim verts for pinning === 
        oLayVertTwinID = bm.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertRim = {}
        for oVert in bm.verts:
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertRim[nTwinID] = oVert.index
                print("TwinVert {:3d} = RimVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
        bpy.ops.object.mode_set(mode='OBJECT')



        #=== Iterate through the verts of the newly separated chunk to access the freshly-created custom data layer to obtain ID information that enables us to match the chunk mesh vertices to the main skinned mesh for pinning ===
        gBlender.SelectAndActivate(oMeshChunkO.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bmPartChunk = bmesh.from_edit_mesh(oMeshChunkO.data)
        oLayVertTwinID = bmPartChunk.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertChunk = {}
        for oVert in bmPartChunk.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertChunk[nTwinID] = oVert.index
                ####DEV??? if oVert.link_faces[0].material_index < nBodyMats:  # For capping below, select only the twin verts that are on one of the body's original material
                ####    oVert.select_set(True)
                print("TwinVert {:3d} = PartVert {:5d} mat {:} at {:}".format(nTwinID, oVert.index, oVert.link_faces[0].material_index, oVert.co))
        bpy.ops.object.mode_set(mode='OBJECT')


        #===== Now that rim is fully formed and the aMapTwinId2VertRim fully populated for to find real rim verts for any TwinID we can finally construct the aMapTwinVerts flat array for each detached part.  (each detached part (no matter if its softbody or cloth simulated) will thereby be able to fix its edge verts to the rim correctly during gameplay) (With both the main skinned mesh and the chunk part with the same set of 'twin ID' in their mesh vertices, we can finally match vertex ID of part to vertex ID of skinned main mesh)
        ###NOTE: This flattened is sent with 1) vertex ID on the separated chunk part, 2) Vertex ID of the 'twin vert' at the same location on the main skinned mesh and 3) an adjacent vert on the skinned mesh to #2 for normal Z-orientation
        aMapTwinVerts = array.array('H')  # The final flattened map of what verts from the 'detached chunk part' maps to what vert in the 'skinned main body'  Client needs this to pin the edges of the softbody-simulated part to the main body skinned mesh
        for nTwinID in aMapTwinId2VertChunk:
            nVertTwinChunk = aMapTwinId2VertChunk[nTwinID]
            if nTwinID in aMapTwinId2VertRim:
                nVertTwinRim = aMapTwinId2VertRim[nTwinID]
                aMapTwinVerts.append(nVertTwinChunk)
                aMapTwinVerts.append(nVertTwinRim)
                print("TwinVert {:3d} = PartVert {:5d} = RimVert {:5d}".format(nTwinID, nVertTwinChunk, nVertTwinRim))
            else:
                G.DumpStr("###ERROR in CBody.SeparateSoftBodyPart(): Mapping of twin verts from TwinID to RimVert Could not find TwinID {} while processing chunk '{}' on mesh '{}' (Obscure corner-case algorithm error that rest of code can probably recover from...)".format(nTwinID, sMeshRim, oMeshChunkO.name))  # Obscure corner case that appears with Vagina L/R... Perhaps because split-point verts are in same position??  Check if this influences the game... 
        oMeshRimO[G.C_PropArray_MapTwinVerts] = aMapTwinVerts.tobytes()  # Store the output map as an object property for later access when Client requests this part.  (We store as byte array to save memory as its only for future serialization to Client and Blender has no use for this info)




        bpy.ops.object.mode_set(mode='OBJECT')

        return "OK"     ###TEMP
    
    
  
    



def CBody_Create(nBodyID, sMeshSource, sSex, sGenitals):
    "Proxy for CBody ctor as we can only return primitives back to Unity"
    oBody = CBody(nBodyID, sMeshSource, sSex, sGenitals)
    return str(oBody.nBodyID)           # Strings is one of the only things we can return to Unity

def CBody_GetBody(nBodyID):
    "Easy accessor to simplify Unity's access to bodies by ID"
    return CBody._aBodies[nBodyID]










#         #=== Assemble the 'aMapVertsOrigToMorph' map of oMesh verts so we know which source vert goes to what assembled vert ===
#         bpy.ops.oMeshO.mode_set(mode='EDIT')
#         bmMorph = bmesh.from_edit_mesh(self.oMeshMorph.data)
#         oLayOrigVertIDs = bmMorph.verts.layers.int[G.C_DataLayer_OrigVertIDs]  # Create a temp custom data layer to store the IDs of each original vert.  This enables future meshes to find the verts in original oMesh
#         for oVert in bmMorph.verts:
#             self.aMapVertsOrigToMorph[oVert[oLayOrigVertIDs]] = oVert.index
#             #print("Vert Assembled {:5d} = Source {:5d}".format(oVert.index, oVert[oLayOrigVertIDs]))        
#         bpy.ops.oMesh.select_all(action='DESELECT')
#         bpy.ops.oMeshO.mode_set(mode='OBJECT')
#         self.oMeshSource.hide = True
#         self.oMeshAssembled.hide = True
#         #self.oMeshMorph.hide = True



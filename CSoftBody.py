#NOW
#Finally fucking fixed bad problems...
#- Cleanup up as much as possible on both sides
#- We need to remove stuff from remeshed body Flex collider too...
    #- Need to abstract 'removal by area' to a function
#- Then... merge of thick skin into SoftBody class... then vagina... then penetration!





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
import CMesh






class CSoftBody:
    def __init__(self, oBody, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio, bIsFlexSkin):
        self.oBody                  = oBody             # The back-reference to the owning body.
        self.sSoftBodyPart          = sSoftBodyPart     # The name of the soft body part.  (e.g. "BreastL", "BreastR", "Penis", etc)  This is our key in self.oBody.aSoftBodies[self.sSoftBodyPart]
        self.nSoftBodyFlexColliderShrinkRatio  = nSoftBodyFlexColliderShrinkRatio # The multiplier applied to the global G.nFlexParticleSpacing.  Used to 'shrink' the collision meshes from the presentation mesh so that collisions appear to occur on the surface of the visible meshes.
        self.bIsFlexSkin            = bIsFlexSkin       # Important switch of implementation between 'false' which is for body parts like breasts and penis where Flex+Unity generates the solid geometry and 'true' where Blender generates precise 'thick skin' geometry from the presentation mesh itself
        self.oMeshSoftBody          = None              # The softbody surface mesh itself.  Visible in Unity and moved by Flex softbody simulation via its internal solid tetramesh.
        self.oMeshFlexCollider      = None              # The 'collision' mesh is a 'shrunken' version of 'oMeshSoftBody' in order to feed to Flex a smaller mesh so that the appearance mesh can appear to collide much closer to other particles than if collision mesh would be shown to user.   
        self.oMeshSoftBodyRim       = None              # The 'softbody rim mesh'  Responsible to pin softbody tetraverts to the skinned body so it moves with the body
        self.oMeshSoftBodyRim_Orig  = None              # The 'original' 'softbody rim mesh'  (Untouched copy and source of oMeshSoftBodyRim)  Done this way to circumvent problems with data layers being destroyed!
        self.oMeshSoftBodyRimBackplate = None           # The 'backmesh' mesh is a filled-in version of the self.oMeshSoftBodyRim_Orig rim mesh for the purpose of finding Flex tetraverts that should be pinned instead of simulated 
        self.oMeshUnity2Blender     = None              # The 'Unity-to-Blender' mesh created by CreateUnity2BlenderMesh().  Used by Unity to pass in geometry for Blender processing (e.g. Softbody tetravert skinning and pinning)   

        self.aMapPinnedFlexParticles     = None              # This array stores pairs of <#RimTetravert, #Tetravert> so Unity can pin the softbody tetraverts from the rim tetravert skinned mesh
        self.aMapRimVerts2Verts     = None              # The final flattened map of what verts from the 'detached softbodypart' maps to what vert in the 'skinned main body'  Client needs this to pin the edges of the softbody-simulated part to the main body skinned mesh
        #self.aMapRimVerts2SourceVerts   = array.array('H')  # Map of flattened rim verts to source verts.  Allows Unity to properly restore rim normals from the messed-up version that capping induced.

        #=== Specific to bIsFlexSkin softbody variant ===
        self.aShapeVerts            = array.array('I')  # Array of which vert / particle is also a shape
        self.aShapeParticleIndices  = array.array('I')  # Flattened array of which shape match to which particle (as per Flex softbody requirements)
        self.aShapeParticleCutoffs  = array.array('I')  # Cutoff in 'aShapeParticleIndices' between sets defining which particle goes to which shape. 

        
        print("=== CSoftBody.ctor()  oBody = '{}'  sSoftBodyPart = '{}'  bIsFlexSkin = '{}' ===".format(self.oBody.sMeshPrefix, self.sSoftBodyPart, self.bIsFlexSkin))
        
        #=== Prepare naming of the meshes we'll create and ensure they are not in Blender ===
        sNameSoftBody = self.oBody.sMeshPrefix + "SB-" + self.sSoftBodyPart         # Create name for to-be-created detach mesh and open the body mesh
        sNameSoftBodyRim = sNameSoftBody + G.C_NameSuffix_Rim                   # The name of the 'softbody rim' mesh (for pinning softbody to skinned body) 
        gBlender.DeleteObject(sNameSoftBody)
        gBlender.DeleteObject(sNameSoftBodyRim)
 
        #=== Obtain the to-be-detached vertex group of name 'self.sSoftBodyPart' from the combo mesh that originally came from the source body ===
        nVertGrpIndex_DetachPart = self.oBody.oMeshBody.oMeshO.vertex_groups.find(G.C_VertGrp_Detach + self.sSoftBodyPart)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
        oVertGroup_DetachPart = self.oBody.oMeshBody.oMeshO.vertex_groups[nVertGrpIndex_DetachPart]     ###IMPROVE: Use Util_SelectVertGroupVerts() instead?
        self.oBody.oMeshBody.oMeshO.vertex_groups.active_index = oVertGroup_DetachPart.index
     
        #=== Open the body's mesh-to-be-split and create a temporary data layer for twin-vert mapping ===
        bmBody = self.oBody.oMeshBody.Open()
        oLayVertTwinID = bmBody.verts.layers.int.new(G.C_DataLayer_TwinVert)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
        nNextVertTwinID = 1                 # We set the next twin vert ID to one.  New IDs for all detachable parts will be created from this variable by incrementing.  This will enable each detached part to find what skinned vert from the body it needs to connect to during gameplay.

        #=== Prepare the part to be detached by first obtaining its list of faces ===
        bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
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
        self.oBody.oMeshBody.ExitFromEditMode()

        #=== Name the newly created mesh as the requested 'detached softbody' ===      
        bpy.context.object.select = False           ###LEARN: Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBody = CMesh.CMesh(sNameSoftBody, bpy.context.scene.objects.active, None)          # The just-split mesh becomes the softbody mesh! 
        ###NOW#########################bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from detached chunk to save memory
        self.oMeshSoftBody.oMeshO.modifiers.clear()     ###LEARN: How to remove all modifiers (including armature)
        self.oBody.oMeshBody.Close()

        if (self.bIsFlexSkin == False):                 # Non-FlexSkin have their solid geometry created by Flex in Unity and need to be given from Blender a closed mesh (e.g. capped)
            #===== SOFTBODY CAPPING =====        ###DESIGN: Would be an improvement to switch this to 'make face'?
            #=== Cap the body part that is part of the softbody (edge verts from only that body part are now selected) ===
            bmSoftBody = self.oMeshSoftBody.Open()
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')  ###BUG?? ###CHECK: Possible that edge collapse could fail depending on View3D mode...
            oLayVertTwinID = bmSoftBody.verts.layers.int[G.C_DataLayer_TwinVert]

            #=== Before the collapse to cap the softbody we must remove the info in the custom data layer so new collapse vert doesn't corrupt our rim data ===
            bpy.ops.mesh.select_non_manifold()      ###LEARN: Will select the edge of the detached softbody mesh = what we have to collapse to make a solid for Flex
            bpy.ops.mesh.extrude_edges_indiv()          ###LEARN: This is the function we need to really extrude!
            for oVert in bmSoftBody.verts:              # Iterate through all selected verts and clear their 'twin id' field.
                if oVert.select == True:
                    oVert[oLayVertTwinID] = 0           ###IMPROVE? Give cap extra geometry for a smooth that will be a better fit than a single center vert??
            bpy.ops.mesh.edge_collapse()                ###LEARN: The collapse will combine all selected verts into one vert at the center
    
            #=== Create the 'backmesh' mesh from the cap.  This mesh is used to find Flex tetraverts that should be pinned to the body instead of simulated ===
            bpy.ops.mesh.select_more()                  # Add the verts immediate to the just-created center vert (the rim verts)
            bpy.ops.mesh.duplicate()                    # Duplicate the 'backmesh' so we can process it further
            bpy.ops.mesh.subdivide(number_cuts=4)       # Subdivide it to provided geometry inside the hole.  (Needed so we can find tetraverts inside the center of the hole and not just extremities)
            bpy.ops.mesh.remove_doubles(threshold=0.02) # Remove verts that are too close together (to speed up tetravert search)
            bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.  This will become our 'backmesh' mesh use to find pinned tetraverts
            self.oMeshSoftBody.ExitFromEditMode()
            bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
            bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')
            self.oMeshSoftBodyRimBackplate = CMesh.CMesh(sNameSoftBody + G.C_NameSuffix_RimBackplate, bpy.context.scene.objects.active, None)  # Connect to the backmesh mesh
            gBlender.DataLayer_RemoveLayers(self.oMeshSoftBodyRimBackplate.GetName())
            self.oMeshSoftBodyRimBackplate.Hide()
            self.oMeshSoftBody.Close()
    
            #=== Create the 'collision mesh' as a 'shrunken version' of appearance mesh (about vert normals) === ###OBS???
            self.oMeshFlexCollider = CMesh.CMesh.CreateFromDuplicate(self.oMeshSoftBody.oMeshO.name + G.C_NameSuffix_FlexCollider, self.oMeshSoftBody)
            self.oMeshFlexCollider.Open()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.shrink_fatten(value=self.nSoftBodyFlexColliderShrinkRatio * G.CGlobals._nFlexParticleSpacing)      # Shrink presentation mesh by the particle distance multiplied by the shrink ratio provided for this softbody
            self.oMeshFlexCollider.Close()
    
        else:                                           # Flex+Unity generated Flex solid need the presentation mesh to be turned into a solid
            ###NOW###Duplicate! #=== Create the 'collision mesh' as a 'shrunken version' of appearance mesh (about vert normals) === ###OBS???
            self.oMeshFlexCollider = CMesh.CMesh.CreateFromDuplicate(self.oMeshSoftBody.oMeshO.name + G.C_NameSuffix_FlexCollider, self.oMeshSoftBody)

            bmFlexCollider = self.oMeshFlexCollider.Open()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.shrink_fatten(value=G.CGlobals._nFlexParticleSpacing / 2)     ###LEARN: Value is inverse of Blender GUI (positive values shrink in API, expand in GUI)

            gBlender.Util_SelectVertGroupVerts(self.oMeshFlexCollider.oMeshO, "_FlexSkinSmoothArea_Vagina_Opening")
            bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=20)      ###TUNE
            
            gBlender.Util_SelectVertGroupVerts(self.oMeshFlexCollider.oMeshO, "_FlexSkinSmoothArea_Vagina_InnerVerts")
            bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=4)      ###TUNE



            #=== Iterate over all inner verts (every vert except rim) and determine their neighboring verts so we can form Flex arrays for in-game Flex softbody simulation ===
            nVertsOrigMesh = len(bmFlexCollider.verts) 
            for oVert in bmFlexCollider.verts:
                if (oVert.select == True):
                    #=== Mark this vert as an actual shape for Flex simulation (shapes are all verts except rim) ===
                    self.aShapeVerts.append(oVert.index)
                    
                    #=== Determine all the particles that will be included in this Flex softbody shape ===
                    aSetVertsAroundThisVert = set()             ###LEARN: How to operate on a set
                    for oFace in oVert.link_faces:                              # Iterate over every face connected to the vert currently being processed...
                        for oVertAround in oFace.verts:                         #... then iterate through all verts connected to this face to...
                            aSetVertsAroundThisVert.add(oVertAround.index)      #... add that vert to the 'set of all verts connected to oVert' (including oVert)
                            #aSetVertsAroundThisVert.add(oVertAround.index + nVertsOrigMesh)      #... add that vert to the 'set of all verts connected to oVert' (including oVert)

                    #=== Push in the list of particles connected to this shape in the flattened array Flex requires ===
                    for nVert in aSetVertsAroundThisVert:
                        self.aShapeParticleIndices.append(nVert)

                    #=== Push in our split point in self.aShapeParticleIndices so Flex can unflatten the aShapeParticleIndices flat array and properly match what particle connects to which shape === 
                    self.aShapeParticleCutoffs.append(len(self.aShapeParticleIndices))

            #self.FUCK

            #print("\n=== aShapeVerts:\n" + str(self.aShapeVerts))
            #print("\n=== aShapeParticleIndices:\n" + str(self.aShapeParticleIndices))
            #print("\n=== aShapeParticleCutoffs:\n" + str(self.aShapeParticleCutoffs))

#             nShrinkDistanceTotal = -G.CGlobals._nFlexParticleSpacing / 2
#             self.oMeshFlexCollider.Open()
#             bpy.ops.mesh.select_all(action='SELECT')
#             bpy.ops.transform.shrink_fatten(value=nShrinkDistanceTotal)
#             gBlender.Util_SelectVertGroupVerts(self.oMeshFlexCollider.oMeshO, "_FlexSkinSmoothArea_Vagina_Opening")
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.vertices_smooth(factor=1.0, repeat=20)      ###TUNE

            
            ###NOW
            # Flex collider accuracy & performance is super important... so trying to wedge something produced from presentation mesh nice but not essential!
            # Make extensive tests of penetration at various sizes first... then observe behavior of skinned presentation mesh to see if it holds up!
            #NEXT: kludge collision mesh right in woman mesh and create FlexSkin right from that... We still have to glue for normals and pins!
            
            
            
#             nSteps = 4
#             nShrinkDistanceTotal = -G.CGlobals._nFlexParticleSpacing / 2
#             nShrinkDistancePerStep = nShrinkDistanceTotal / nSteps
#               
#             self.oMeshFlexCollider.Open()
#             for nStep in range(nSteps):
#                 gBlender.Util_SelectVertGroupVerts(self.oMeshFlexCollider.oMeshO, "_FlexSkinSmoothArea_Vagina_Slit")
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.select_more()
#                 bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=3)      ###TUNE
#                 bpy.ops.mesh.select_all(action='SELECT')
#                 bpy.ops.transform.shrink_fatten(value=nShrinkDistancePerStep)

            #self.oMeshFlexCollider.Close()








    
        #===== SKINNED RIM CREATION =====
        #=== Create the 'Skinned Rim' skinned mesh that Client can use to use 'BakeMesh()' on a heavily-simplified version of the main body mesh that contains only the 'rim' polygons that attach to all the detachable softbody this code separates.  It is this 'Rim' skinned mesh that will 'pin' the softbody tetravert solid to the skinned body === 
        ####DESIGN: Vert topology changes at every split!  MUST map twinID to body verts once all cuts done ###NOW!!!
        #=== Iterate through the verts of the main skinned mesh to select all the twin verts so we can create the rim mesh
        bmBody = self.oBody.oMeshBody.Open()
        oLayVertTwinID = bmBody.verts.layers.int[G.C_DataLayer_TwinVert]
        for oVert in bmBody.verts:
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                oVert.select_set(True)      # Select this edge boundary vertex for the upcoming code in which we expand the rim selection to create the rim submesh

        #=== Select the faces neighboring the twin verts and duplicate them into the new 'rim mesh'
        ###IMPROVE: Mesh at this point is not triagulated!!  How come??
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')  # With rim verts selected, switch to Face mode with expand to select all faces that use these verts... then switch to poly mode to have the smallest set of polygons that have an edge at the boundary are left selected.  These will form their own 'reduced skin mesh' that will be baked at every frame to calculate pin positions
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.separate()             # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'softbody part'
        bmBody.verts.layers.int.remove(oLayVertTwinID)  # Remove the temp data layer in the skin mesh as the just-separated mesh has the info now...
        self.oBody.oMeshBody.ExitFromEditMode()
            
        #=== Fetch the just-created 'rim' skinned mesh and set it to its proper name ===
        bpy.context.object.select = False  # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
        bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
        self.oMeshSoftBodyRim_Orig = CMesh.CMesh(sNameSoftBodyRim, bpy.context.scene.objects.active, None)
        self.oBody.oMeshBody.Close()
        
        #=== Cleanup the rim mesh by removing all materials ===
        while len(self.oMeshSoftBodyRim_Orig.oMeshO.material_slots) > 0:  ###IMPROVE: Find a way to remove doubles while preventing key-not-found errors in twin hunt below??
            bpy.ops.object.material_slot_remove()           ####DEV: Move?
        bpy.ops.object.material_slot_add()  # Add a single default material (captures all the polygons of rim) so we can properly send the mesh over (crashes if zero material)
        gBlender.Cleanup_VertGrp_RemoveNonBones(self.oMeshSoftBodyRim_Orig.oMeshO, True)  # Remove the extra vertex groups that are not skinning related        ####DEV: Move?
        self.oMeshSoftBodyRim_Orig.Hide()





  
    def ProcessTetraVerts(self, nDistTetraVertsFromRim):
        "Process the Flex-created tetraverts and create softbody rim mesh.  Updates our rim mesh currently containing only rim (for normals).  This mesh will be responsible to 'pin' some softbody tetraverts to the skinned body so softbody doesn't 'fly out'"
        print("-- CSoftBody.ProcessTetraVerts() on body '{}' and softbody '{}' with tetra distance {} --".format(self.oBody.sMeshPrefix, self.sSoftBodyPart, nDistTetraVertsFromRim));

        #=== Create a temporary copy of rim mesh so we can transfer weights efficiently from it to new mesh including tetraverts ===
        ####BUG? Destroy mesh of rim??
        self.oMeshSoftBodyRim = CMesh.CMesh.CreateFromDuplicate("TEMP_SoftBodyRim", self.oMeshSoftBodyRim_Orig)         ###IMPROVE: Name for this softbody and keep?
        oMeshSoftBodyRim_Copy = CMesh.CMesh.CreateFromDuplicate("TEMP_SoftBodyRim_Copy", self.oMeshSoftBodyRim_Orig)
        self.aMapPinnedFlexParticles = array.array('H')  # Blank out the two arrays that must be created everytime this is called
        self.aMapRimVerts2Verts = array.array('H')

        #=== Open the temp mesh Unity requested in CreateTempMesh() and push in a data layer with vert index.  This will prevent us from losing access to Unity's tetraverts as we process this mesh toward the softbody rim ===        
        oMeshUnity2BlenderCOPY = CMesh.CMesh.CreateFromDuplicate("TEMP_Unity2Blender", self.oMeshUnity2Blender)        # Create a temporary copy of Unity2Blender mesh because we need to destroy our copy and Unity owns its copy and must release it on its own
        bmUnity2Blender = oMeshUnity2BlenderCOPY.Open()
        oLayTetraVerts = bmUnity2Blender.verts.layers.int.new(G.C_DataLayer_TetraVerts)
        for oVert in bmUnity2Blender.verts:
            oVert[oLayTetraVerts] = oVert.index + G.C_OffsetVertIDs    # Apply offset to easily tell real IDs in later loop
        oMeshUnity2BlenderCOPY.Close()
        

        #===== Remove the tetraverts that are too far from the rim backmesh =====
        #===== Combine the tetravert-mesh with the rim backmesh mesh of our softbody.  We need to isolate the tetraverts close to the back of the softbody tetraverts to 'pin' them =====
        oMeshSoftBodyRimBackplateCOPY = CMesh.CMesh.CreateFromDuplicate("TEMPFORJOIN-BACKPLATE", self.oMeshSoftBodyRimBackplate)
         
        gBlender.SelectAndActivate(oMeshUnity2BlenderCOPY.GetName())             # First select and activate mesh that will be destroyed (temp mesh)    (Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh))
        oMeshSoftBodyRimBackplateCOPY.oMeshO.hide = False
        oMeshSoftBodyRimBackplateCOPY.oMeshO.select = True                         # Now select...
        bpy.context.scene.objects.active = oMeshSoftBodyRimBackplateCOPY.oMeshO    #... and activate mesh that will be kept (merged into)  (Note that to-be-destroyed mesh still selected!)
        bpy.ops.object.join()                                       #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###LEARN: Existing custom data layer in merged mesh destroyed!!
        oMeshUnity2BlenderCOPY = None                              # Above join destroyed the copy mesh so set our variable to None
        #=== Select the rim verts in the joined mesh ===
        bmRimBackplate = oMeshSoftBodyRimBackplateCOPY.Open()
        oLayTetraVerts = bmRimBackplate.verts.layers.int[G.C_DataLayer_TetraVerts]
        bpy.ops.mesh.select_loose()                             # Select the loose geometry...  (This will only select Unity's tetravert)
        bpy.ops.mesh.select_all(action='INVERT')                #... and invert it (leaving only the backmesh selected (for upcoming nearby selection)
        #=== Move the rim verts with the close tetraverts some distance so we can quickly separate the tetraverts close to rim verts ===        
        C_TempMove = 10             ###SOON ###IMPROVE: Switch to the 'transfer mesh' modifier?
        bpy.ops.transform.transform(mode='TRANSLATION', value=(0, C_TempMove, 0, 0), proportional='ENABLED', proportional_size=nDistTetraVertsFromRim, proportional_edit_falloff='CONSTANT')  # Move the rim verts with propportional editing so the tetraverts near rim are moved too.  This is how we separate them
        #=== Delete all tetraverts that are too far from rim ===
        bpy.ops.mesh.select_all(action='DESELECT')
        for oVert in bmRimBackplate.verts:  # Select all body verts far from clothing (Separated by translation operation above)                                  
            if oVert.co.z > -C_TempMove / 2:  ###WEAK!! Stupid 90 degree rotation rearing its ugly head again...
                oVert.select_set(True)
        bpy.ops.mesh.delete(type='VERT')  # Delete all tetraverts that were too far from rim.  (These will be softbody-simulated and the others pinned)
        #=== Move back the remaining rim and 'close tetraverts to their original position.  At this point only tetraverts near rim remain ===
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.transform.transform(mode='TRANSLATION', value=(0, -C_TempMove, 0, 0))  # Move the clothing verts with proportional enabled with a constant curve.  This will also move the body verts near any clothing ###TUNE
        bpy.ops.mesh.select_all(action='DESELECT')
        #=== Delete the verts of the backmesh... to leave only the 'close tetraverts to the backmesh' that need to be pinned instead of simulated ===
        bpy.ops.mesh.select_loose()                             # Select the loose geometry...  (This will only select Unity's tetravert)
        bpy.ops.mesh.select_all(action='INVERT')                #... and invert it (leaving only the backmesh selected (for upcoming nearby selection)
        bpy.ops.mesh.delete(type='VERT')
        oMeshSoftBodyRimBackplateCOPY.Close()
 
        #===== Combine the tetravert collection of verts with the rim mesh of our softbody.  We need to isolate the tetraverts close to the rim verts to 'pin' them =====
        gBlender.SelectAndActivate(oMeshSoftBodyRimBackplateCOPY.GetName())             # First select and activate mesh that will be destroyed (temp mesh) (Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh))
        self.oMeshSoftBodyRim.oMeshO.hide = False                           # Now select...  ###IMPROVE: Add method to open in this way?
        self.oMeshSoftBodyRim.oMeshO.select = True                          # Now select...
        bpy.context.scene.objects.active = self.oMeshSoftBodyRim.oMeshO     #... and activate mesh that will be kept (merged into)  (Note that to-be-destroyed mesh still selected!)
        bpy.ops.object.join()                                               #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###LEARN: Existing custom data layer in merged mesh destroyed!!  ###LEARN: join is not deterministic in which verts will be first!!
        oMeshSoftBodyRimBackplateCOPY = None                               # Above join destroyed the mesh backmesh so set to none
        #gBlender.Util_PrintMeshVerts("oMeshSoftBodyRim after join", self.oMeshSoftBodyRim.GetName(), G.C_DataLayer_TwinVert)

        #=== Skin the rim+tetraverts mesh from original rim mesh.  (So tetraverts are skinned too!)
        gBlender.Util_TransferWeights(self.oMeshSoftBodyRim.oMeshO, oMeshSoftBodyRim_Copy.oMeshO)      #bpy.ops.object.vertex_group_transfer_weight()
        gBlender.Cleanup_VertGrp_RemoveNonBones(self.oMeshSoftBodyRim.oMeshO, True)        



        #===== CREATE THE MAP OF PINNED FLEX PARTICLES: Responsible to move simulated Flex particles to the position of their coresponding skinned vert  =====
        bmRim = self.oMeshSoftBodyRim.Open()
        oLayTetraVerts = bmRim.verts.layers.int[G.C_DataLayer_TetraVerts]

        #=== Iterate through tetraverts to fill in its map traversal ===
        for oVert in bmRim.verts:                               ###IMPROVE: Code that generates 'aMapPinnedFlexParticles' is duplicate between soft body and cloth... can be merged together?? 
            nTetraVertID = oVert[oLayTetraVerts]
            if (nTetraVertID >= G.C_OffsetVertIDs):            # The real tetraverts are over this offset (as created above)
                nTetraVertID -= G.C_OffsetVertIDs              # Retrieve the non-offsetted tetravert
                self.aMapPinnedFlexParticles.append(oVert.index)
                self.aMapPinnedFlexParticles.append(nTetraVertID)
                #print("RimTetravert {:4d} = Tetravert {:4d}". format(oVert.index, nTetraVertID))
        self.oMeshSoftBodyRim.Close()
        

        #===== CREATE THE TWIN VERT MAPPING: Responsible to 'glue' the simulated edge verts to the main skinned body for 'seamless' appearance =====
        #===1. Iterate over the rim copy vertices, and find the rim vert for every 'twin verts' so next loop can map softbody part verts to rim verts for pinning === 
        bmRimCopy = self.oMeshSoftBodyRim.Open()
        oLayVertTwinID = bmRimCopy.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertRim = {}
        for oVert in bmRimCopy.verts:
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertRim[nTwinID] = oVert.index
                #print("TwinID {:3d} = RimVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
        self.oMeshSoftBodyRim.Close()

        #===2. Iterate through the verts of the newly separated softbody to access the freshly-created custom data layer to obtain ID information that enables us to match the softbody mesh vertices to the main skinned mesh for pinning ===
        bmSoftBody = self.oMeshSoftBody.Open()
        oLayVertTwinID = bmSoftBody.verts.layers.int[G.C_DataLayer_TwinVert]
        aMapTwinId2VertSoftBody = {}
        for oVert in bmSoftBody.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
            nTwinID = oVert[oLayVertTwinID]
            if nTwinID != 0:
                aMapTwinId2VertSoftBody[nTwinID] = oVert.index
                #print("TwinID {:3d} = SoftBodyVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
        self.oMeshSoftBody.Close()

        #===3. With both maps created, bridge them together to a flattened map from softbody mesh to its rim vert ===
        for nTwinID in aMapTwinId2VertSoftBody:
            nVertTwinSoftBody = aMapTwinId2VertSoftBody[nTwinID]
            if nTwinID in aMapTwinId2VertRim:
                nVertTwinRim = aMapTwinId2VertRim[nTwinID]
                #print("TwinID {:3d} = SoftBodyVert {:5d} = RimVert {:5d}".format(nTwinID, nVertTwinSoftBody, nVertTwinRim))
                self.aMapRimVerts2Verts.append(nVertTwinSoftBody)
                self.aMapRimVerts2Verts.append(nVertTwinRim)                ####BUG ####DEV: Can fail here... trap to earlier and catch!
            else:
                G.DumpStr("###ERROR in CSoftBody.SeparateSoftBodyPart() finding nTwinID {} in aMapTwinId2VertRim".format(nTwinID)) 

        return "OK"     ###TEMP


    def CreateMesh_Unity2Blender(self, nVerts):       ###MOVE: Not really related to CBody but is global
        "Create a temporary Unity2Blender with 'nVerts' vertices.  Used by Unity to pass Blender temporary mesh geometry for Blender processing (e.g. Softbody tetramesh pinning)"
        sNameMeshUnity2Blender = self.oMeshSoftBody.GetName() + G.C_NameSuffix_Unity2Blender
        if (self.oMeshUnity2Blender != None):
            self.oMeshUnity2Blender.Destroy()
            self.oMeshUnity2Blender = None
        oMeshD = bpy.data.meshes.new(sNameMeshUnity2Blender)
        oMeshO = bpy.data.objects.new(oMeshD.name, oMeshD)
        print("== CreateMesh_Unity2Blender() for mesh '{}' and verts {} ==".format(sNameMeshUnity2Blender, nVerts));
        oMeshO.rotation_euler.x = radians(90)          # Rotate temp mesh 90 degrees like every other mesh.  ###IMPROVE: Get rid of 90 rotation EVERYWHERE!!
        bpy.context.scene.objects.link(oMeshO)
        aVerts = []
        for nVert in range(nVerts):
            aVerts.append((0,0,0))
        oMeshD.from_pydata(aVerts,[],[])
        oMeshD.update()
        gBlender.SetParent(oMeshO.name, G.C_NodeFolder_Game)
        self.oMeshUnity2Blender = CMesh.CMesh.CreateFromExistingObject(oMeshO.name)     # Store CMesh reference into the member dedicated for this purpose so Unity can access and upload to us via its normal (efficient) channel
        self.oMeshUnity2Blender.SetName(sNameMeshUnity2Blender)     # Ensure we have the name we need. 
        self.oMeshUnity2Blender.bDeleteUponDestroy = True
        self.oMeshUnity2Blender.Hide()
        return "OK"         # Return OK to Unity
    
    
    def Morph_UpdateDependentMeshes(self):
        "Updates this softbody mesh from its source morph body"
        #=== Iterate through this softbody mesh and update our vert position to our corresponding morph source body ===
        bmSoftBody = self.oMeshSoftBody.Open()
        oLayVertAssy = bmSoftBody.verts.layers.int[G.C_DataLayer_VertsAssy]
        aVertsMorph = self.oBody.oMeshMorph.oMeshO.data.vertices
        for oVert in bmSoftBody.verts:
            if (oVert[oLayVertAssy] >= G.C_OffsetVertIDs):
                nVertMorph = oVert[oLayVertAssy] - G.C_OffsetVertIDs        # Obtain the vertID from the assembled mesh (removing offset added during creation)
                oVert.co = aVertsMorph[nVertMorph].co.copy()
        self.oMeshSoftBody.Close()



    def SerializeCollection_aMapRimVerts2Verts(self):               ###IMPROVE: Fanning out by function the best way?
        return gBlender.Stream_SerializeCollection(self.aMapRimVerts2Verts) 

    def SerializeCollection_aMapPinnedFlexParticles(self):
        return gBlender.Stream_SerializeCollection(self.aMapPinnedFlexParticles)

#     def SerializeCollection_aMapRimVerts2SourceVerts(self):
#         return gBlender.Stream_SerializeCollection(self.aMapRimVerts2SourceVerts)



    def SerializeCollection_aShapeVerts(self):
        return gBlender.Stream_SerializeCollection(self.aShapeVerts)
    
    def SerializeCollection_aShapeParticleIndices(self):
        return gBlender.Stream_SerializeCollection(self.aShapeParticleIndices)
            
    def SerializeCollection_aShapeParticleCutoffs(self):
        return gBlender.Stream_SerializeCollection(self.aShapeParticleCutoffs)



















#     def ProcessTetraVerts(self, nNumVerts_UnityToBlenderMesh, nDistTetraVertsFromRim):
#         "Process the Flex-created tetraverts and create softbody rim mesh.  Updates our rim mesh currently containing only rim (for normals).  This mesh will be responsible to 'pin' some softbody tetraverts to the skinned body so softbody doesn't 'fly out'"
#         print("-- CSoftBody.ProcessTetraVerts() on body '{}' and softbody '{}' with tetra distance {} --".format(self.oBody.sMeshPrefix, self.sSoftBodyPart, nDistTetraVertsFromRim));
# 
#         #=== Create a temporary copy of rim mesh so we can transfer weights efficiently from it to new mesh including tetraverts ===
#         ####BUG? Destroy mesh of rim??
#         self.oMeshSoftBodyRim = CMesh.CMesh.CreateFromDuplicate("TEMP_SoftBodyRim", self.oMeshSoftBodyRim_Orig)
#         oMeshSoftBodyRim_Copy = CMesh.CMesh.CreateFromDuplicate("TEMP_SoftBodyRim_Copy", self.oMeshSoftBodyRim_Orig)
# 
#         #=== Create a temporary copy of Unity2Blender mesh so we can trim it to 'nNumVerts_UnityToBlenderMesh' verts ===  
#         self.oMeshUnity2Blender = CMesh.CMesh.CreateFromDuplicate("TEMP_Unity2Blender", self.oMeshUnity2Blender)
#         self.aMapPinnedFlexParticles = array.array('H')  # Blank out the two arrays that must be created everytime this is called
#         self.aMapRimVerts2Verts         = array.array('H')
# 
#         #=== Open the temp mesh Unity requested in CreateTempMesh() and push in a data layer with vert index.  This will prevent us from losing access to Unity's tetraverts as we process this mesh toward the softbody rim ===        
#         bm = self.oMeshUnity2Blender.Open()
#         for oVert in bm.verts:
#             if (oVert.index >= nNumVerts_UnityToBlenderMesh):
#                 oVert.select_set(True)
#         bpy.ops.mesh.delete(type='VERT')        # Delete all verts from Unity2Blender mesh that are 'extra' (That is only created once with the max # of verts we can ever expect)
#         nVertsRimOrig = len(self.oMeshSoftBodyRim.oMesh.data.vertices)     # Remember how many verts rim had before join (so we can resync below) 
#         print("- CSoftBody.ProcessTetraVerts() shifts joined rim verts by {} from inserting Unity tetraverts.".format(nNumVerts_UnityToBlenderMesh))
#  
#         #=== Create the custom data layer and store vert indices into it === 
#         oLayTetraVerts = bm.verts.layers.int.new(G.C_DataLayer_TetraVerts)
#         for oVert in bm.verts:
#             oVert[oLayTetraVerts] = oVert.index + G.C_OffsetVertIDs    # Apply offset to easily tell real IDs in later loop
#         self.oMeshUnity2Blender.Close()
#         
#         #===== Combine the tetravert-mesh with the rim mesh of that softbody.  We need to isolate the tetraverts close to the rim verts to 'pin' them =====
#         ###LEARN: Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh)
#         gBlender.SelectAndActivate(self.oMeshUnity2Blender.GetName())             # First select and activate mesh that will be destroyed (temp mesh)
#         self.oMeshSoftBodyRim.oMesh.select = True                         # Now select...
#         bpy.context.scene.objects.active = self.oMeshSoftBodyRim.oMesh    #... and activate mesh that will be kepp (merged into)  (Note that to-be-destroyed mesh still selected!)
#         bpy.ops.object.join()                                       #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###LEARN: Existing custom data layer in merged mesh destroyed!!
#         self.oMeshUnity2Blender = None                              # Above join destroyed the copy mesh so set our variable to None
# 
#         #===== Remove the tetraverts that are too far from the rim =====
#         #=== Select the rim verts in the joined mesh ===
#         bmRim = self.oMeshSoftBodyRim.Open()
#         oLayTetraVerts = bmRim.verts.layers.int[G.C_DataLayer_TetraVerts]
#         for oVert in bmRim.verts:
#             if (oVert.index > nNumVerts_UnityToBlenderMesh):
#                 oVert.select_set(True)                      # Select only the verts with no OrigVertID = tetraverts
#         #=== Move the rim verts with the close tetraverts some distance so we can quickly separate the tetraverts close to rim verts ===        
#         C_TempMove = 10
#         bpy.ops.transform.transform(mode='TRANSLATION', value=(0, C_TempMove, 0, 0), proportional='ENABLED', proportional_size=nDistTetraVertsFromRim, proportional_edit_falloff='CONSTANT')  # Move the rim verts with propportional editing so the tetraverts near rim are moved too.  This is how we separate them
#         #=== Delete all tetraverts that are too far from rim ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         for oVert in bmRim.verts:  # Select all body verts far from clothing (Separated by translation operation above)                                  
#             if oVert.co.z > -C_TempMove / 2:  ###WEAK!! Stupid 90 degree rotation rearing its ugly head again...
#                 oVert.select_set(True)
#         bpy.ops.mesh.delete(type='VERT')  # Delete all tetraverts that were too far from rim.  (These will be softbody-simulated and the others pinned)
#         #=== Move back the remaining rim and 'close tetraverts to their original position.  At this point only tetraverts near rim remain ===
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.transform.transform(mode='TRANSLATION', value=(0, -C_TempMove, 0, 0))  # Move the clothing verts with proportional enabled with a constant curve.  This will also move the body verts near any clothing ###TUNE
#         bpy.ops.object.mode_set(mode='OBJECT')    
#         #=== Skin the rim+tetraverts mesh from original rim mesh.  (So tetraverts are skinned too!)
#         gBlender.Util_TransferWeights(self.oMeshSoftBodyRim.oMesh, oMeshSoftBodyRim_Copy.oMesh)      #bpy.ops.object.vertex_group_transfer_weight()
#         gBlender.Cleanup_VertGrp_RemoveNonBones(self.oMeshSoftBodyRim.oMesh, True)        
#         nVertsRimJoined = len(self.oMeshSoftBodyRim.oMesh.data.vertices)     # Remember how many verts rim now has once close tetraverts are kept in
#         nShiftAppliedToOrigRimVerts = nVertsRimJoined - nVertsRimOrig   # Calculate the shift applied to orig verts  
#         self.oMeshSoftBodyRim.Close()
# 
#         #===== CREATE THE MAP PIN TETRAVERTS TO TETRAVERT MAP =====
#         bmRim = self.oMeshSoftBodyRim.Open()
#         oLayTetraVerts = bmRim.verts.layers.int[G.C_DataLayer_TetraVerts]
# 
#         #=== Iterate through tetraverts to fill in its map traversal ===
#         for oVert in bmRim.verts:                                                                        
#             nTetraVertID = oVert[oLayTetraVerts]
#             if (nTetraVertID >= G.C_OffsetVertIDs):            # The real tetraverts are over this offset (as created above)
#                 nTetraVertID -= G.C_OffsetVertIDs              # Retrieve the non-offsetted tetravert
#                 self.aMapPinnedFlexParticles.append(oVert.index)
#                 self.aMapPinnedFlexParticles.append(nTetraVertID)
#                 #print("RimTetravert {:4d} = Tetravert {:4d}". format(oVert.index, nTetraVertID))
#         self.oMeshSoftBodyRim.Close()
# 
# 
#         #===== CREATE THE TWIN VERT MAPPING =====
#         #===1. Iterate over the rim copy vertices, and find the rim vert for every 'twin verts' so next loop can map softbody part verts to rim verts for pinning === 
#         bmRimCopy = oMeshSoftBodyRim_Copy.Open()
#         oLayVertTwinID = bmRimCopy.verts.layers.int[G.C_DataLayer_TwinVert]
#         aMapTwinId2VertRim = {}
#         for oVert in bmRimCopy.verts:
#             nTwinID = oVert[oLayVertTwinID]
#             if nTwinID != 0:
#                 aMapTwinId2VertRim[nTwinID] = oVert.index + nShiftAppliedToOrigRimVerts ###NOTE: Apply shift forced upon rim verts from join with tetra verts above
#                 #print("TwinID {:3d} = RimVert {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
#         oMeshSoftBodyRim_Copy.Close()
#         oMeshSoftBodyRim_Copy = None
# 
#         #===2. Iterate through the verts of the newly separated softbody to access the freshly-created custom data layer to obtain ID information that enables us to match the softbody mesh vertices to the main skinned mesh for pinning ===
#         bmSoftBody = self.oMeshSoftBody.Open()
#         oLayVertTwinID = bmSoftBody.verts.layers.int[G.C_DataLayer_TwinVert]
#         aMapTwinId2VertSoftBody = {}
#         for oVert in bmSoftBody.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
#             nTwinID = oVert[oLayVertTwinID]
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
#                 self.aMapRimVerts2Verts.append(nVertTwinSoftBody)
#                 self.aMapRimVerts2Verts.append(nVertTwinRim)                ####BUG ####DEV: Can fail here... trap to earlier and catch!
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
#         super(self.__class__, self).__init__(oBody, sSoftBodyPart)      ###LEARN: How to call base class ctor
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
#         self.oMeshColBreast = CMesh.CMesh.CreateFromExistingObject(sNameSlaveMeshSlave)    
#         
#         #=== Iterate through the verts to assemble the aColBreastVertSphereRadiusRatio array storing the red channel of the vertex color.  (This information stores the relative radius of each vertex sphere with a value of zero meaning no sphere) ===
#         bmBreastCol = self.oMeshColBreast.Open()
#         oLayVertColors = bmBreastCol.loops.layers.color.active        # Obtain reference to bmesh vertex color channel store in loops  ###LEARN: 2 defined 'Col' and 'Col.001' with 'Col.001' active and appearing to contain valid data... can this change?? ###CHECK
#         nNumActiveVerts = 0
#         for oVert in bmBreastCol.verts:
#             nVertSphereRadiusRatio = oVert.link_loops[0][oLayVertColors][0]     ###LEARN: How to access vert colors
#             if nVertSphereRadiusRatio > 0.1:                         ###KEEP? Setting zero color can be tricky so some threshold??
#                 #print("CBodyColBreast: SphereIndex # {:2} = Vert {:2} = Val: {:2}".format(nNumActiveVerts, oVert.index, nVertSphereRadiusRatio))
#                 nNumActiveVerts += 1
#             else:
#                 nVertSphereRadiusRatio = 0                              # Non collider-related verts get zero strength so they don't generate a sphere collider
#             self.aColBreastVertSphereRadiusRatio.append((int)(255 * nVertSphereRadiusRatio))       # The red vertex color channel (a float for 0 to 1) is multiplied by 255 and sent as a short
#         if nNumActiveVerts != 16:        # Both breasts are limited to 32 so 16 per breast
#             raise Exception("ERROR: CBodyColBreast_FormColliders() did not find 16 active verts while scanning vertex colors on source breast collider mesh.")
#         
#         nNumCapsules = 0
#         for oEdge in bmBreastCol.edges:
#             if (oEdge.smooth == False):
#                 self.aColBreastCapsuleSpheres.append(oEdge.verts[0].index) 
#                 self.aColBreastCapsuleSpheres.append(oEdge.verts[1].index)
#                 #print("CBodyColBreast: Capsule {:2} found between {:2}-{:2}".format(nNumCapsules, oEdge.verts[0].index, oEdge.verts[1].index))
#                 nNumCapsules += 1
#         if nNumCapsules != 16:           # Both breasts are limited to 32 so 16 per breast
#             raise Exception("ERROR: CBodyColBreast_FormColliders() didn't find 16 capsules while scanning for sharp edges on source breast collider mesh.")
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
#         CSoftBody.Morph_UpdateDependentMeshes(self)                 # Call base class for usual SoftBody apply.  ###LEARN: How to call base class
#         self.oBody.SlaveMesh_ResyncWithMasterMesh(self.sNameCollider)              # Re-sync our collider (which is a slave mesh) back to its master mesh
# 
# 
# 
#     def SerializeCollection_aColBreastVertSphereRadiusRatio(self):
#         return gBlender.Stream_SerializeCollection(self.aColBreastVertSphereRadiusRatio)
# 
#     def SerializeCollection_aColBreastCapsuleSpheres(self):
#         return gBlender.Stream_SerializeCollection(self.aColBreastCapsuleSpheres)
# 
#     def SerializeCollection_aColBreastMapSlaveMeshSlaveToMaster(self):
#         return gBlender.Stream_SerializeCollection(self.aColBreastMapSlaveMeshSlaveToMaster)




#         #=== Vagina has special processing as the complex 3D shape is created in Blender and not on-the-fly from this script ===
#         if (self.bIsVagina == False):
#             #=== Before the collapse to cap the softbody we must remove the info in the custom data layer so new collapse vert doesn't corrupt our rim data ===
#             bpy.ops.mesh.extrude_edges_indiv()          ###LEARN: This is the function we need to really extrude!
#             for oVert in bmSoftBody.verts:              # Iterate through all selected verts and clear their 'twin id' field.
#                 if oVert.select == True:
#                     oVert[oLayVertTwinID] = 0           ###IMPROVE? Give cap extra geometry for a smooth that will be a better fit than a single center vert??
#             bpy.ops.mesh.edge_collapse()                ###LEARN: The collapse will combine all selected verts into one vert at the center
# 
#             #=== Create the 'backmesh' mesh from the cap.  This mesh is used to find Flex tetraverts that should be pinned to the body instead of simulated ===
#             bpy.ops.mesh.select_more()                  # Add the verts immediate to the just-created center vert (the rim verts)
#             bpy.ops.mesh.duplicate()                    # Duplicate the 'backmesh' so we can process it further
#             bpy.ops.mesh.subdivide(number_cuts=4)       # Subdivide it to provided geometry inside the hole.  (Needed so we can find tetraverts inside the center of the hole and not just extremities)
#             bpy.ops.mesh.remove_doubles(threshold=0.02) # Remove verts that are too close together (to speed up tetravert search)
# 
#         else:
#             bpy.ops.mesh.select_all(action='DESELECT')
#             nVertGrpIndex_DetachPart = self.oMeshSoftBody.oMeshO.vertex_groups.find(G.C_VertGrp_Detach + "Vagina_Backplate")      ###BUG!!!! _ versus -!!!!!!
#             oVertGroup_DetachPart = self.oMeshSoftBody.oMeshO.vertex_groups[nVertGrpIndex_DetachPart]
#             self.oMeshSoftBody.oMeshO.vertex_groups.active_index = oVertGroup_DetachPart.index
#             bpy.ops.object.vertex_group_select()  # Select only the just-updated vertex group of the vertices we need to separate from the composite mesh.
# 
#         #=== Finish creating the backmesh from vagina or no-vagina submesh selected above ===
#         bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.  This will become our 'backmesh' mesh use to find pinned tetraverts
#         bpy.ops.object.mode_set(mode='OBJECT')      # Manually going to object to handle tricky split below...
#         bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#         bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
#         self.oMeshSoftBodyRimBackplate = CMesh.CMesh(sNameSoftBody + G.C_NameSuffix_RimBackplate, bpy.context.scene.objects.active, None)  # Connect to the backmesh mesh
#         self.oMeshSoftBodyRimBackplate.Hide()
#         self.oMeshSoftBody.Close()                  # Close the rim mesh.  ###MOVE? (To ProcessTetraVerts()?) 




#     def CreateUnity2BlenderMesh(self, nVerts):
#         """Creates a temporary mesh of 'nVerts' vertices as requested by Unity.  This is then used by Unity to efficently upload to Blender a large amount of verticies for further processing by Blender."""
#         sNameMeshUnity2Blender = self.oMeshSoftBody + G.C_NameSuffix_Unity2Blender          ###MOVE? Only useful for softbodies?
#         gBlender.DeleteObject(self.oMeshUnity2Blender.GetName())
#         gBlender.DeleteObject(sNameMeshUnity2Blender)
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
#         self.oMeshUnity2Blender = CMesh.CMesh.CreateFromExistingObject(sNameMeshUnity2Blender, G.C_NodeFolder_Game)     # Store in our member variable as a CMesh so Unity can handshake with as usual       
#         print("CreateUnity2BlenderMesh() created mesh {} with {} verts.".format(sNameMeshUnity2Blender, nVerts))
#         #return oMeshO
#         return "OK"



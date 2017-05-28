###REMAINING21: Penis automatic mounting:  May 2017
#--- NOW ---

#--- Fitting to a body instance ---

#--- Mounting to body during body creation ---

#--- Related ---

#--- Design ---
#- Time-consuming process of blending textures assumes a fixed relationship to a body!!  So this means most of penis fitting occurs at ship-time?  DESIGN AROUND THIS!!!
# Currently hard-coding woman mesh and broke its morphing capacity... 
    #- We need to quickly attach from pre-fitted penis in file... how to accomplish this while still allowing body morphs??

#--- Improvements ---
#- Plan ahead for penis morphing and fast in-game updates...
#- Keep in mind for dildo gameplay that the removable part of body is a useful starting point for 'dildo backplate'!

#--- Problems ---

#--- TODO ---
#- Create custom fitter for man mesh when it becomes available.    

#--- Misc ---



import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

import G
from gBlender import *
from CMesh import *




class CPenis():        # CPenis: Oversees 1) Design-time fitting of penis to body mesh. 2) Efficiently joining to a body at runtime 3) Calculating runtime information Unity needs at gameplay
    def __init__(self, oBody):
        self.oBody = oBody                              # Back-reference to the CBody instance that owns / manages us.
        self.oMeshPenisFitted = None                    # The fitted penis.  A modified version of source penis adapted to 'mount' on a given game-time CBody instance.  Must be re-generated everytime source body morphs to ensure a proper mount

        

        print("\n\n\n=============== PENIS MOUNTING PROCEDURE ===============")
        print("\n===== A. PREPARE THE BODY HOLE FOR PENIS INSERTION INTO RIM =====")
        #=== Visualizer Cubes Preparation.  Must run first before entering edit mode ===
        self.oVisualizerCubes = G.CVisualizerCubes(0)       # Utility class to help debug / visualise this complex algorithm.  Set to about 600 to create enough 'visualization cubes' shown about different layers       
        self.C_Layer_RimVertBody  = 9                       ###TODO: Use more layer stuff through codebase = removes clutter!!!
        self.C_Layer_RimVertPenis = 8
        bpy.data.scenes[0].layers[1] = 0            ###LEARN: How to select which layers are shown.  (Must have at least one layer shown at ALL times!)
        bpy.data.scenes[0].layers[0] = 1            ###LEARN: How to hide default layer 0 (show another layer first!)

        #=== Create extra geometry near where the penis will be mounted (the 'mounting hole') ===
        bmBody = self.oBody.oMeshBody.Open()
        oVertGrp_PenisMountingHole = VertGrp_SelectVerts(self.oBody.oMeshBody.GetMesh(), "_CPenis_MountingHole")     # Obtain the area of the body's mesh that we are to replace with a fitted penis
        bpy.ops.mesh.select_more()                  # Select one more ring so the rim gets enough geometry to properly connect to fine-geometry penis
        bpy.ops.mesh.subdivide()

        #=== The above subdivide messed up our vertex group for the mounting hole rim.  Fix it now ===  (Only half the verts are now in group, new ones not)
        VertGrp_SelectVerts(self.oBody.oMeshBody.GetMesh(), oVertGrp_PenisMountingHole.name)
        bpy.ops.mesh.select_more()                  ###LEARN: Trick when half the verts in a ring are selected is to select more and then less = selects all in that ring!
        bpy.ops.mesh.select_less()
        bpy.ops.object.vertex_group_assign()

        #=== Obtain reference to the rim verts ===
        bpy.ops.mesh.region_to_loop()               # Obtain the rim from the mesh (still containing inner part of hole) with region_to_loop()
        bmBody.verts.ensure_lookup_table()
        aVertsBodyRim = [oVert.index for oVert in bmBody.verts if oVert.select]      # Obtain list of all body rim hole verts.  Needed for many iterations
        
        #=== Find the key verts of the rim hole opening.  We need these in 'modify base vert' section below to morph the penis base closer to the rim ===
        vecPenisRimCenter = Vector()
        oVertRimRightmost = None                        # The rim vert with the highest +X coordinate.  Used to re-interpolate penis UVs for re-texturing                        
        nVertRimRightmostX_Max = -999999                # The X coordinates of the rightmost rim vert.  Used to find 'oVertRimRightmost'
        aVertsAtZeroX = []
        for nVertRim in aVertsBodyRim:                  # Iterate through the rim verts to find the verts at X=0.  There should be exactly two: One for top of hole the other for bottom of hole
            oVertRim = bmBody.verts[nVertRim]
            oVertRim.tag = False                        # Make sure each rim vert is untagged (next loop depends on this)
            vecPenisRimCenter += oVertRim.co
            if abs(oVertRim.co.x) < 0.0001:             ###WEAK: Rim verts at rim centers not exactly zero?  WTF happened to body mesh??
                aVertsAtZeroX.append(oVertRim)
            if nVertRimRightmostX_Max < oVertRim.co.x:
                nVertRimRightmostX_Max = oVertRim.co.x
                oVertRimRightmost = oVertRim

        #=== Determine which are the top and bottom rim verts from results of previous loop ===
        if aVertsAtZeroX[0].co.z > aVertsAtZeroX[1].co.z:
            oVertRimTop    = aVertsAtZeroX[0]         
            oVertRimBottom = aVertsAtZeroX[1]
        else:         
            oVertRimTop    = aVertsAtZeroX[1]         
            oVertRimBottom = aVertsAtZeroX[0]
        vecVertRimTop    = oVertRimTop.co.copy()    ###LEARN: copy() is extremely important (data would point to some garbage once owning bmesh goes out of scope!)      
        vecVertRimBottom = oVertRimBottom.co.copy()
        vecPenisRimCenter /= len(aVertsBodyRim)
        vecPenisRimCenter.y -= 0.05                 ###HACK: Hack on center so that it's easier to determine verts toward penis / toward base (give a push forward toward tip) 
        bpy.context.scene.cursor_location = vecPenisRimCenter      
        print("\n=== Center = {}   Top = {}   Bottom = {}  Rightmost {} ===".format(vecPenisRimCenter, vecVertRimTop, vecVertRimBottom, oVertRimRightmost.co))   






        print("\n===== B. CREATE CHAIN OF RIM VERTS IN OUR STRUCTURES =====")
        oLayUV_Body  = bmBody.loops.layers.uv.active                    # Obtain access to the body's UV layer (so we can extract rim vert UVs and set them into penis rim verts)
        oRimVertBodyRoot = CRimVertBody(self, None, oVertRimTop, oVertRimTop.link_loops[0][oLayUV_Body].uv.copy())        # The string starts at the master rim vert (topmost at X=0)
        oRimVertBodyNow = oRimVertBodyRoot                              # Before we iterate set the 'next' as the root because it is the iteration's starting point

        while True:                             # Iterate through circular loop until we reach the node flagged as the last one
            oVertBodyRimNow = bmBody.verts[oRimVertBodyNow.nVertBody]

            for oEdgeToChild in oVertBodyRimNow.link_edges:
                if oEdgeToChild.select:                     # Only edges on the rim are currently selected
                    oVertNext = oEdgeToChild.other_vert(oVertBodyRimNow)
                    if oVertNext.tag == False:                              # Avoid edges that have been tagged as they have been traversed before. (by this loop)
                        if oVertNext.index != oVertRimTop.index:                # Only create a new link if we haven't looped back to starting vert yet
                            vecUV_Body = oVertBodyRimNow.link_loops[0][oLayUV_Body].uv.copy()
                            oRimVertBodyNow = oRimVertBodyNow.SetNext(oEdgeToChild, oVertNext, vecUV_Body)
                            print(oRimVertBodyNow)
                            oVertNext.tag = True                                        # Tag this vert as having been traversed so we don't go back to it.
                        else:                                                           # We've encountered the 'first vert' once again.  End the iteration by...
                            oRimVertBodyNow.bLastInLoop = True                          #... flagging the last node as the last one...
                            oRimVertBodyNow .oRimVertBodyNext = oRimVertBodyRoot        #... and set 'next'     of last  node to first node...
                            oRimVertBodyRoot.oRimVertBodyPrev = oRimVertBodyNow         #... and set 'previous' of first node to last  node...
                            print("- Chaining: linking first {} to last {}".format(oRimVertBodyRoot, oRimVertBodyNow))
                        break                                                           # We have committed to this edge.  Stop iterating through other edges (exit for loop and back into infinite while loop)
            if oRimVertBodyNow.bLastInLoop:
                break
        bmBody = self.oBody.oMeshBody.Close()
        self.oBody.oMeshBody.GetMesh().hide = True

        
        
        
        print("\n===== C. MODIFY THE PENIS BASE VERTS TO BE CLOSER TO BODY'S RIM OPENING =====")
        #=== Move all penis verts so the designated penis master vert coincides with the body's rim master vert (located at X=0 at penis top) ===
        self.oMeshPenisFittedSource = CMesh.CreateFromExistingObject("PenisA")          ###TODO21: A From Unity arg!
        self.oMeshPenisFitted = CMesh.CreateFromDuplicate(self.oBody.oBodyBase.sMeshPrefix + "Penis-Fitted", self.oMeshPenisFittedSource)
        Cleanup_RemoveDoublesAndConvertToTris(0.000001)                         # Convert the penis to tris right away                                                              
        self.oMeshPenisFitted.SetParent(self.oBody.oBodyBase.oNodeRoot.name)    # Reparent fitted penis to unique body we are fitting to

        if oBody.oBodyBase.sMeshSource.find("WomanA") != -1:        
            bmPenis = self.oMeshPenisFitted.Open()
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenis_VertTop")     # Obtain our previously defined top vert.
            oVertPenisTop = Util_GetFirstSelectedVert(bmPenis)
            vecShiftOfAllPenisVerts = vecVertRimTop - oVertPenisTop.co
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.translate(value=vecShiftOfAllPenisVerts)
            bpy.ops.mesh.select_all(action='DESELECT')
    
            #=== Proportionally move the bottom penis vert so that bottom of penis aligns much closer to bottom of rim hole ===
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenis_VertBottom")
            oVertPenisBottom = Util_GetFirstSelectedVert(bmPenis)
            vecShiftBottomVert = vecVertRimBottom - oVertPenisBottom.co
            bpy.ops.transform.translate(value=vecShiftBottomVert, proportional='CONNECTED', proportional_edit_falloff='SMOOTH', proportional_size=0.12)       ###TUNE: proportional size
    
            #=== Proportionally move a small area of verts underneath the scrotum close to base that are just too far from rim ===
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenis_ScrotumBase")
            bpy.ops.transform.translate(value=(0, 0, 0.0046), proportional='ENABLED', proportional_edit_falloff='SMOOTH', proportional_size=0.012)           ###TUNE
    
            #=== Proportionally move the side verts to make them wider (and with a softer angle) to rim edges ===
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenis_BaseSides")
            nRatio = 1.12
            bpy.ops.transform.resize(value=(nRatio, nRatio, nRatio), constraint_orientation='GLOBAL', mirror=False, proportional='CONNECTED', proportional_edit_falloff='SMOOTH', proportional_size=0.032)
            bpy.ops.mesh.select_all(action='DESELECT')

        else:
            raise Exception("###EXCEPTION: Manual morphing procedure not created to modify penis base for a body mesh of type '{}'".format(self.oBody.oBodyBase.sMeshSource))       ###TODO21:!! Man mesh




        
        print("\n===== D. MATCH PENIS RIM VERTS TO BODY RIM VERTS =====")
        #=== Create a KD Tree of all the verts in the penis mounting area.  This tree will be used to rapidly find the closest vert to each vert of our mouting rim ===
        oKDTreePenis = kdtree.KDTree(len(bmPenis.verts))                     ###OPT: Would run a bit faster if we limit KDTree to verts near base
        for oVertPenis in bmPenis.verts:
            oKDTreePenis.insert(oVertPenis.co, oVertPenis.index)
        oKDTreePenis.balance()

        #=== Iterate through all the body rim verts to find their closest penis vert.  As we have a many-to-many between the two rim domains some body rim verts will point to multiple penis rim verts and some body rim verts will have no penis rim verts.  (Next loop choses the closest one)
        dictRimVertPenis = {}                                   # Dictionary of unique penis rim verts.
        oRimVertBodyNow = oRimVertBodyRoot
        while True:
            vecVertPenisClosestToRimVertBody, nVertPenisClosestToRimVertBody, nDist = oKDTreePenis.find(oRimVertBodyNow.vecVertBody)
            oVertPenisRim = bmPenis.verts[nVertPenisClosestToRimVertBody]
            if nDist > 0.05:
                raise Exception("###EXCEPTION: CPenis.ctor() could not find vert near enough to {}.  Closest dist = {}".format(oRimVertBodyNow.vecVertBody, nDist))
            if nVertPenisClosestToRimVertBody in dictRimVertPenis:                      # If a CRimVertPenis instance already exists for this penis rim vert obtain it so we can append this body rim vert to it
                oRimVertPenis = dictRimVertPenis[nVertPenisClosestToRimVertBody] 
            else:                                                                       #... otherwise create a new one and we will map it to this body rim vert (its first)
                oRimVertPenis = CRimVertPenis(self, oVertPenisRim)
                dictRimVertPenis[nVertPenisClosestToRimVertBody] = oRimVertPenis
            oRimVertPenis.RimVertBody_Add(oRimVertBodyNow)                              # Add an additional body rim vert to this penis rim vert.  (We will pick which one is closest in next loop)  This is how we can find best rim-to-rim matches accross our many-to-many relationship between the two domains
            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext




        

        
        print("\n===== F. CREATE VERTEX GROUPS WE WILL NEED FOR GEOMETRY DISSOLUTION =====") 
        #=== Create a new vertex group for the non-manifold penis base.  We will need it later as we delete vertices ===
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
        oVertGrp_PenisBaseNonManifold = self.oMeshPenisFitted.GetMesh().vertex_groups.new("_CPenis_BaseNonManifold") 
        bpy.ops.object.vertex_group_assign()

        #=== Iterate through all the defined penis rim verts and ask them to choose the closest body rim vert ===
        bpy.ops.mesh.select_all(action='DESELECT')
        for nRimVertPenis in dictRimVertPenis:
            oRimVertPenis = dictRimVertPenis[nRimVertPenis]
            oRimVertBody = oRimVertPenis.RimVertBody_FindClosest()
            oRimVertPenis.oVertPenis.select_set(True)                       # Also select so we can define vertex group just below

        #=== Create a new vertex group for the penis rim.  It will be needed later on to easily identify penis rim verts ===
        oVertGrp_PenisRimVerts = self.oMeshPenisFitted.GetMesh().vertex_groups.new("_CPenis_RimVerts") 
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')

        #=== Mark the unused body rim verts from our chain (Those that have no corresponding penis rim vert)  They will be dissolved when we can re-open body mesh ===
        aRimVertBodyToDissolve = []                                     # Remember where they are so we can remove when we re-open body's mesh
        oRimVertBodyNow = oRimVertBodyRoot
        while True:
            if oRimVertBodyNow.oRimVertPenis is None:
                oRimVertBodyNow.oRimVertBodyPrev.oRimVertBodyNext = oRimVertBodyNow.oRimVertBodyNext        #... first link the 'next' pointer of our previous to our next node...
                oRimVertBodyNow.oRimVertBodyNext.oRimVertBodyPrev = oRimVertBodyNow.oRimVertBodyPrev        #... and link the 'previous' pointer of our next node to our previous one.  (Bypassing & unlinking this node in both cases)
                print("- Marked body rim vert for dissolution: {}".format(oRimVertBodyNow))                # Remove this node from doubly-linked list:
                aRimVertBodyToDissolve.append(oRimVertBodyNow)              # Remember it so we can dissolve when we can re-open body mesh
                ###BROKEN: Reinstate facility to change cube color? oRimVertBodyNow.oVisualizerCube.material_slots[0].material = bpy.data.materials['VisualizerCube-GreenDark']   # Change our visualizer color to indicate dissolve
            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext




        print("\n===== G. DISSOLVE EXTRANEOUS PENIS RIM GEOMETRY =====")
        ###NOTE: Key part of algorithm!  What we have to do to form a solid rim border that can separate the good part of the mesh from the throwaway is to iterate through all rim edges and find edges that don't have BMEdge objects between them...
        ###NOTE: For those we dissolve the verts in the way and use 'vert_connect' to properly form a new BMEdge on the appropriate face (Does it properly as it won't introduce non-manifold geometry) 
        bpy.ops.mesh.select_all(action='DESELECT')
        oRimVertBodyNow = oRimVertBodyRoot
        while True:
            print("- Running edge vert dissolve on {}".format(oRimVertBodyNow))
            oRimVertPenis1 = oRimVertBodyNow.oRimVertBodyPrev.oRimVertPenis.oVertPenis 
            oRimVertPenis2 = oRimVertBodyNow.oRimVertPenis.oVertPenis
 
            if True:#oRimVertBodyNow.nRimVertBodyID == 13:
                oEdgeOnRim = bmPenis.edges.get([oRimVertPenis1, oRimVertPenis2])         ###LEARN: How to find an existing edge
                if oEdgeOnRim is None:
                    oRimVertPenis1.select_set(True)
                    oRimVertPenis2.select_set(True)
                    bpy.ops.mesh.shortest_path_select()                     ###LEARN: How to select shortest path
                    oRimVertPenis1.select_set(False)
                    oRimVertPenis2.select_set(False)
                    bpy.ops.mesh.dissolve_verts()                           ###OPT!!!: Runs very slowly but essential.  Can we possibly try to fix mesh after deleting this verts?  (Or UVs too badly damaged after 'make face' again?)
                    print("- Edge vert dissolve: Dissolved verts between {} and {} ".format(oRimVertPenis1, oRimVertPenis2))
                    oRimVertPenis1.select_set(True)
                    oRimVertPenis2.select_set(True)
                    bpy.ops.mesh.vert_connect()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    oEdgeOnRim = bmPenis.edges.get([oRimVertPenis1, oRimVertPenis2])         ###LEARN: How to find an existing edge
                    if oEdgeOnRim is None:
                        print("- ERROR: Edge vert dissolve: Could not connect verts {} and {} ".format(oRimVertPenis1, oRimVertPenis2))

            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext



        
        print("\n===== H. REMOVE UNNEDDED PENIS GEOMETRY =====")
        #=== Starting at the non-manifold penis base edges keep selecting 'more' and de-selecting the rim verts... this will select all geometry we can delete ===         
        bpy.ops.mesh.select_all(action='DESELECT')
        self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisBaseNonManifold.index
        bpy.ops.object.vertex_group_select()
        self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisRimVerts.index
        for n in range(30):
            bpy.ops.object.vertex_group_deselect()      #... and de-selecting rim verts...
            bpy.ops.mesh.select_more()                  #... selecting one more layer of verts...
        bpy.ops.object.vertex_group_deselect()

        #=== Destroy the verts that are past the rim verts and convert to tris once more.  After this we can directly move penis verts to the position of their associated body rim vert as they have the exact same topology ===
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.mesh.select_all(action='DESELECT')



        
        print("\n===== I. MOVE PENIS RIM VERTS TO BODY RIM VERTS =====")
        #=== Move the penis rim verts to their associated body rim verts positions ===
        for nRimVertPenis in dictRimVertPenis:
            oRimVertPenis = dictRimVertPenis[nRimVertPenis]
            oRimVertPenis.oVertPenis.co = oRimVertPenis.oRimVertBody.vecVertBody
            oRimVertPenis.nVertPenis = oRimVertPenis.oVertPenis.index                   # Deleting verts in statement group above changed vertice indexes.  Refresh them so we have valid ones to still find penis rim verts after join below

        #=== Before joining heavily smooth the verts in the area of the joined rim vertices ===            ###TUNE: End-result penis smoothing.
        self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisRimVerts.index
        bpy.ops.object.vertex_group_select()
        for n in range(5):
            bpy.ops.mesh.select_more()                  # Progressively smooth right around (modified rim)...
            bpy.ops.object.vertex_group_deselect()      #... but we never move rim verts themselves!
            bpy.ops.mesh.vertices_smooth(5)             ###TUNE: Smoothing

        #=== Remove all vertex groups and create a new one for CSoftBody implementation to use to create soft body from penis ===
        VertGrp_RemoveAll(self.oMeshPenisFitted.GetMesh())
        oVertGrp_Penis = self.oMeshPenisFitted.GetMesh().vertex_groups.new("_CSoftBody_Penis")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.data.scenes[0].tool_settings.vertex_group_weight = 0        ###CHECK: Make sure this works!
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bmPenis = self.oMeshPenisFitted.Close()


        
        

        print("\n===== J. SKINNING PENIS FROM ORIGINAL BODY =====")
        #=== Transfer skinning info from body to unskinned penis.  This is essential so penis base moves with the body! ===
        Util_TransferWeights(self.oMeshPenisFitted.GetMesh(), self.oBody.oMeshBody.GetMesh(), False)
        VertGrp_RemoveByName(self.oMeshPenisFitted.GetMesh(), oVertGrp_PenisMountingHole.name)      # Weight transfer above also transferred the mounting hole vert group which we don't want
        




        print("\n===== K. PERFORM FINAL CLEANUP BODY AND PENIS MESH BEFORE JOIN ======")
        #=== Cleanup the extraneous materials while keeping the most important one ===        ###OBS: Raw penis from DAZ gets it extra texture removed manually
        #oMatPenisMainMaterial = self.oMeshPenisFitted.GetMeshData().materials["Skin"]       # Before removing all materials obtain reference to the one we need to keep
        #while len(self.oMeshPenisFitted.GetMeshData().materials) > 0:                       # Remove all the materials
        #    bpy.ops.object.material_slot_remove()
        #bpy.ops.object.material_slot_add()
        #self.oMeshPenisFitted.GetMesh().material_slots[0].material = oMatPenisMainMaterial     # In the re-created slot re-assign the body material so it is the only material there.
        
        #=== Refresh the BMVerts we need to dissolve after the next vert delete for mounting hole ===
        bmBody = self.oBody.oMeshBody.Open()
        for oRimVertBodyNow in aRimVertBodyToDissolve:
            oRimVertBodyNow.oVertBody = bmBody.verts[oRimVertBodyNow.nVertBody]     # Update the BMVert from the index all indices are about to become invalid after vert delete below

        #=== Remove the verts inside the penis mounting hole (e.g. finally create the 'hole' needed for penis to weld in) ===
        self.oBody.oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp_PenisMountingHole.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_less()                  # Vertex group contains the rim verts which we want to keep.  Select one vert ring less to select only the inner verts we must delete
        bpy.ops.mesh.delete(type='VERT')            # Delete the mounting area's inner hole.  Penis can now be merged right in place by welding close verts
        
        #=== Dissolve the unused geometry of the body's penis rim.  Leaving them would create holes after join! ===
        bmBody.verts.ensure_lookup_table()
        for oRimVertBodyNow in aRimVertBodyToDissolve:
            oRimVertBodyNow.oVertBody.select_set(True)
            print("- Dissolving marked body rim vert {}".format(oRimVertBodyNow))
        bpy.ops.mesh.dissolve_verts()
        
        #=== Re-triangulate penis mounting hole area ===
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.quads_convert_to_tris()
        bmBody  = self.oBody.oMeshBody.Close()





        print("\n===== L. ATTACH FITTED PENIS TO BODY =====")
        #=== Weld the fitted penis to the prepared body ===
        SelectAndActivate(self.oBody.oMeshBody.GetName())
        self.oMeshPenisTempForJoin = CMesh.CreateFromDuplicate(self.oMeshPenisFitted.GetName() + "-TempForJoin", self.oMeshPenisFitted)
        self.oMeshPenisTempForJoin.GetMesh().select = True
        self.oBody.oMeshBody.GetMesh().select = True
        bpy.context.scene.objects.active = self.oBody.oMeshBody.GetMesh() 

        #=== Join the two meshes and weld the rim verts ===
        bpy.ops.object.join()                       ###LEARN: This will MESS UP all the vertex ID in the body (penis vert IDs will be fine and appear in the order they were in penis)  After this we have to re-obtain our BMVerts by 3D coordinates as even our stored vertex IDs become meaningless
        
        #=== Open body and re-obtain access to the body-side rim verts (previous indices & BMVerts rendered invalid after join above) ===        
        bmBody = self.oBody.oMeshBody.Open()        ###LEARN: We do it this way instead of 'remove_doubles()' as that call will replace about half the body's rim verts with penis rim verts (thereby destroying precious UV & skinning info)
        self.oBody.oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp_PenisMountingHole.index
        bpy.ops.object.vertex_group_select()
        aVertsBodyRim = [oVert for oVert in bmBody.verts if oVert.select]
        bpy.ops.mesh.select_all(action='DESELECT')

        #=== Re-link the penis-side rim verts with their associated body-side rim verts.  (We need to merge them in a controlled manner) ===
        oRimVertBodyNow = oRimVertBodyRoot
        while True:
            oRimVertBodyNow.oRimVertPenis.oVertPenis = bmBody.verts[oRimVertBodyNow.oRimVertPenis.nVertPenis]       # Update BMVert reference (old one destroyed by join above)
            oRimVertBodyNow.oRimVertPenis.vecVertPenis = oRimVertBodyNow.oRimVertPenis.oVertPenis.co                # Update Penis rim vert location (moved to body rim vert above)
            oRimVertBodyNow.oVertBody = None 
            for oVertBodyRim in aVertsBodyRim:                          # Perform a brute-force search through all body-side rim verts to find the one at the 3D location of the known-good penis-side rim vert
                if oVertBodyRim.co == oRimVertBodyNow.vecVertBody:
                    oRimVertBodyNow.oVertBody = oVertBodyRim
                    break 
            if oRimVertBodyNow.oVertBody is None:
                raise Exception("###EXCEPTION: Could not find body rim vert at location {} after join.".format(oRimVertBodyNow.vecVertBody))
            print("- After-join re-link of {} to {}".format(oRimVertBodyNow.oVertBody, oRimVertBodyNow.oRimVertPenis.oVertPenis)) 
            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext

        #=== Create new faces between the two rims.  This will protect both side's information (bones and UVs) ===
        oRimVertBodyNow = oRimVertBodyRoot          ###DESIGN21:!!! Some uncertainty as how to leave the merged meshes...  Keep the faces in gametime body?  Modify softobdy (which version? now or future??)
        while True:
            oFaceBridgeAcrossRims = bmBody.faces.new([oRimVertBodyNow.oVertBody, oRimVertBodyNow.oRimVertPenis.oVertPenis, oRimVertBodyNow.oRimVertBodyPrev.oRimVertPenis.oVertPenis, oRimVertBodyNow.oRimVertBodyPrev.oVertBody])
            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
        bmBody  = self.oBody.oMeshBody.Close()

        
        
        if 0:           ###DESIGN:21!!!: Belongs in this call?  Blender file saved without moving body rim and decimation?  How about penis morphs?
            print("\n===== M. SMOOTH PENIS-TO-BODY RIM AREA =====")
            #=== Smooth the verts in the area of the joined rim vertices ===            ###TUNE: End-result penis smoothing.
            bpy.ops.mesh.vertices_smooth(10)                                            ###DESIGN: Remove this when re-texturing penis??            
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.vertices_smooth(10)            
           
            print("\n===== N. DECIMATE PENIS GEOMETRY =====")
            #=== Decimate the just-attached penis to reduce its vert count to more reasonable levels ===
            VertGrp_SelectVerts(self.oBody.oMeshBody.GetMesh(), oVertGrp_Penis.name)
            bpy.ops.mesh.decimate(ratio=0.17)                               ###TUNE: Decimation ratio!



        
        print("\n===== O. FINISHED! =====")                         # Simple no? :-)
        bpy.context.scene.cursor_location = Vector((0,0,0))         # Return things to default and return
        bpy.ops.object.mode_set(mode='OBJECT')




        


class CRimVertBody():               # CRimVertBody: Helper class to store all information related to a rim vert on the body side
    s_nRimVertBodyID_Next = 0       # Static counter to auto-increment 'self.nRimVertBodyID'
    
    def __init__(self, oPenis, oRimVertBodyPrev, oVertBody, vecUV_Body):
        self.oPenis             = oPenis
        self.oRimVertBodyPrev   = oRimVertBodyPrev      # Our 'previous' CRimVertBody  (The rim vert just prior to us along the rim edge)
        self.oRimVertBodyNext   = None                  # Our 'next'     CRimVertBody  (The rim vert just next  to us along the rim edge) (Set by SetNext())
        self.oVertBody          = oVertBody             # Our BMVert on the body's rim for penis
        self.nVertBody          = self.oVertBody.index  # VertID of this rim vert in body mesh
        self.vecVertBody        = self.oVertBody.co.copy()  # The position of this body rim vert    ###LEARN: copy() hugely important.  (Data would point to garbage when BMesh data falls out of scope!)
        self.vecUV_Body         = vecUV_Body            # The UV coordinate of the body-side rim vert.  Used to set penis-side rim vert UV
        self.nEdgeToChild       = None                  # The edge that links self.nVertBody to self.oRimVertBodyNext.nVertBody (Set by SetNext())  ###OBS?
        self.nLenEdgeToChildLen = None                  # Length of edge between parent and child.  Used to dissolve penis verts that are too close 
        self.oRimVertPenis      = None                  # CRimVertPenis instance assigned to us (closest). Can be None (in areas where more geometry exists on body rim than penis rim)
        self.oVisualizerCube    = None                  # Reference to our 'visualizer cube' that renders in 3D scene where this vertex is.  Essential during development!
        self.bLastInLoop        = False                 # Set to true on the very last node in the loop.  Allows iteration loops to iterate through every node of the loop exactly once   

        self.nRimVertBodyID = CRimVertBody.s_nRimVertBodyID_Next
        CRimVertBody.s_nRimVertBodyID_Next += 1

        self.oVisualizerCube = self.oPenis.oVisualizerCubes.GetCube("RimB{:02d}".format(self.nRimVertBodyID), self.vecVertBody, 'Green', self.oPenis.C_Layer_RimVertBody, True) 

    def SetNext(self, oEdgeToChild, oVertBody, vecUV_Body):             # Sets the one and only child
        self.nEdgeToChild   = oEdgeToChild.index            # Set on the parent edge that was used to find self.oRimVertBodyNext
        self.nLenEdgeToChildLen = oEdgeToChild.calc_length()
        self.oRimVertBodyNext  = CRimVertBody(self.oPenis, self, oVertBody, vecUV_Body)
        return self.oRimVertBodyNext                   # Return child for one-line creation + assignment

    def __str__(self):
        nRimVertPenisID = -1
        if self.oRimVertPenis is not None:
            nRimVertPenisID= self.oRimVertPenis.nRimVertPenisID
        return "[Body #{:2d}  Vert={:5d}  P={:2d}  {:6.3f},{:6.3f},{:6.3f}]".format(self.nRimVertBodyID, self.nVertBody, nRimVertPenisID, self.vecVertBody.x, self.vecVertBody.y, self.vecVertBody.z)



class CRimVertPenis():              # CRimVertPenis: Helper class to store all information related to a rim vert on the penis side
    s_nRimVertPenisID_Next = 0      # Static counter to auto-increment 'self.nRimVertPenisID'
    
    def __init__(self, oPenis, oVertPenis):
        self.oPenis             = oPenis
        self.oVertPenis         = oVertPenis            # Our rim BMVert on penis mesh                
        self.nVertPenis         = oVertPenis.index      # Vertex index of penis.  (Stored so we can still find our vert after join with body)                
        self.vecVertPenis       = self.oVertPenis.co    # Position of our rim vertex on penis mesh
        self.aRimVertBody       = []                    # List that store all CRimVertBody assigned to this penis rim vert in 'RimVertBody_Add()'.  We pick the closest one
        self.oRimVertBody       = None                  # The body rim vert we're assigned to.  Determined in RimVertBody_FindClosest()
        self.oVisualizerCube    = None                  # Reference to our 'visualizer cube' that renders in 3D scene where this vertex is.  Essential during development!   
        
        self.nRimVertPenisID = CRimVertPenis.s_nRimVertPenisID_Next
        CRimVertPenis.s_nRimVertPenisID_Next += 1

    def RimVertBody_Add(self, oRimVertBody):
        self.aRimVertBody.append(oRimVertBody)
        print("{} added link to {}".format(self, oRimVertBody))
        
    def RimVertBody_FindClosest(self):
        nDistMin = 9999999
        for oRimVertBody in self.aRimVertBody:
            nDist = (oRimVertBody.vecVertBody - self.vecVertPenis).length
            if nDistMin > nDist:
                nDistMin = nDist
                self.oRimVertBody = oRimVertBody
        self.oRimVertBody.oRimVertPenis = self              # Link body rim vert to this penis rim vert
        self.aRimVertBody = None                            # Done with collection so destroy to save memory
        self.oVisualizerCube = self.oPenis.oVisualizerCubes.GetCube("RimP{:02d}".format(self.oRimVertBody.nRimVertBodyID), self.vecVertPenis, 'Blue', self.oPenis.C_Layer_RimVertPenis, False)    # Add our visualizer cube 
        print("{}  <==>  {}".format(self, self.oRimVertBody))
        return self.oRimVertBody

    def __str__(self):
        nRimVertBodyID = -1
        if self.oRimVertBody is not None:
            nRimVertBodyID = self.oRimVertBody.nRimVertBodyID
        return "[Penis #{:2d}  Vert={:5d}  B={:2d}]".format(self.nRimVertPenisID, self.oVertPenis.index, nRimVertBodyID)



#- We have a solution on efficiently blending penis textures but:
    #- UV distortion not ok!
        #- Why the heck are the rim UVs so much further that first read??
        #- Definitively a 'clockwise rotation' of rim verts... why??  (Is 2-way many-to-many resolution not working right? (e.g. always picking first or last??)
    #- Need to code the latest manual UV step?  (Or does it make things worse? 
    #- To perform 'second step' of texture edit:
        #- In 'Texture Paint', invoke tool tray -> Tools tab -> Clone brush (NOT from image).  Then in main view Control+LMB on 'good part' of texture and draw on 'bad' part.  Adjust radius with F and strenght to blend! :)
    #- UV re-projection has larger gaps around rim verts... what causes this??
    #- UV re-projection shows around rim verts an odd 'clockwise' rotation of rim verts... what causes this distortion??

        #=== Determine the UV re-interpolation parameters that can convert between penis X,Z 3D coordinates and a UV X,Y ===  (PLACE BEFORE 'CREATE CHAIN OF RIM VERTS IN OUR STRUCTURES')
        #oLayUV_Body  = bmBody.loops.layers.uv.active                    # Obtain access to the body's UV layer (so we can extract rim vert UVs and set them into penis rim verts)
        ###OBS? Turns out the creation of new UV layer is not really needed given texture Blend can be so easily done with Blender's tools...
        #vec2D_Point0 = Vector((oVertRimBottom.co.   x, oVertRimBottom.co.   z))     # Point 0 = bottom center of rim.  (We use the x and z 3D coordinates to 'flatten' them into a 'lookalike UV' projected about Y = 0 plane
        #vec2D_Point1 = Vector((oVertRimRightmost.co.x, oVertRimRightmost.co.z))     # Point 1 = top right of rim.
        #vecUV_Point0 = oVertRimBottom.   link_loops[0][oLayUV_Body].uv.copy()       # UV coordinates of point 0 and point above.
        #vecUV_Point1 = oVertRimRightmost.link_loops[0][oLayUV_Body].uv.copy()
        #vec2D_Span  = vec2D_Point1 - vec2D_Point0 
        #vecUV_Span  = vecUV_Point1 - vecUV_Point0
        #print("=== 3D: {} - {}     UV: {} - {} ===\n".format(vec2D_Point0, vec2D_Point1, vecUV_Point0, vecUV_Point1))
        


#         ###OBS? Turns out the creation of new UV layer is not really needed given texture Blend can be so easily done with Blender's tools...  (PLACE RIGHT BEFORE SKINNING)
#         print("\n===== CREATE NEW UV LAYER FOR RE-TEXTURING =====")
#         #=== Create a new 're-texturing helper' UV map that *greatly* facilitate the process of blending the body's texture onto the penis one ===
#         bpy.ops.mesh.uv_texture_add()                                       # Create a new UV layer to facilitate the blending of the penis textures to the body
#         #bmPenis.loops.layers.uv.active.name = "PenisRetexturing"            ###LEARN: How to create and additional UV layer (will copy first one)  ###IMPROVE: How to name layer??
#         oLayUV_Penis = bmPenis.loops.layers.uv.active                       ###LEARN: How to access the UV copy we just created
#         self.oMeshPenisFitted.GetMeshData().uv_textures.active_index = 0    # Go back to the default UV map.  Leaving active on would cause join with body to have the new layer selected on the whole body! 
# 
#         #=== Iterate through mounting-area penis verts to re-interpolate their UVs to be similar to the UVs of the body rim ===
#         for oVert in bmPenis.verts:
#             vec2D = Vector((oVert.co.x, oVert.co.z))                # Re-interpolate the 'projected' 3D (Flattened about Y=0) toward UV coordinates 
#             vec2D   -= vec2D_Point0                                 # First we remove the 'zero point' from the 'flattened 3D' domain...
#             vec2D.x /= vec2D_Span.x                                 #... then convert 0 - 1 scaling by dividing by the 'flattened 3D' domain span...
#             vec2D.y /= vec2D_Span.y
#             vec2D.x *= vecUV_Span.x                                 #... then convert the 0 - 1 to the UV domain's span...
#             vec2D.y *= vecUV_Span.y 
#             vec2D   += vecUV_Point0                                 #... and finally add the UV-domain starting point. 
#             for oLoop in oVert.link_loops:
#                 oLoop[oLayUV_Penis].uv = vec2D.copy()
#                         
#         #=== Set the UV coordinates of the penis rim verts to the exact UV position of the body rim.  (This greatly facilitates creating a 'texture transfer UV' to blend in textures at the seam) ===
#         for nRimVertPenis in dictRimVertPenis:
#             oRimVertPenis = dictRimVertPenis[nRimVertPenis]
#             vecUV_Body = oRimVertPenis.oRimVertBody.vecUV_Body              # Fetch the previously-obtained UV coordinates for the body-side rim vert (obtained in earlier loop while bmBody was open)
#             for oLoop in oRimVertPenis.oVertPenis.link_loops:               # Store body's rim vert UV into penis rim-vert UV.
#                 oLoop[oLayUV_Penis].uv = vecUV_Body

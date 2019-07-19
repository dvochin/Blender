#===========================================================================
###DOCS24: Penis rig creation - June 2017

#=== REMINDER ===

#=== TODO ===
#- Keep fitted penis once done??
#- Remove old penis vert groups
#- Vert group with #CBody_... rename to _ like the others?
#- Rename file to CPenisFit?

#=== QUESTION ===

#=== PROBLEMS ===
#?- Master mounting vert resolves to 3 verts in re-join because of the creation of extra geometry during procedure.

#=== IMPROVE ===

#=== NEEDS ===

#=== DESIGN ===

#=== WISHLIST ===

#=== PROBLEMS ===

#=== QUESTIONS ===






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



class CPenisFit():        # CPenisFit: Performs design-time fitting of penis to body mesh.  (Once this time-consuming process completes game can attach fitted penis very quickly)
    C_Layer_RimVertBody  = 9                       ###TODO: Use more layer stuff through codebase = removes clutter!!!
    C_Layer_RimVertPenis = 8

    
    def __init__(self, sNameBodySource, sNameBodyDestination):
        self.sNameBodySource        = sNameBodySource       # The name of our source body.  Either "Woman" or "ManRawImport".  Must exist and be properly imported by our body importer
        self.sNameBodyDestination   = sNameBodyDestination  # The name we give the body we create.  Either "Shemale" or "Man"
        self.oSkinMeshGame              = CMesh.AttachFromDuplicate_ByName(sNameBodyDestination + "-Source", sNameBodySource + "-Source")
        self.oMeshPenis             = None                      # The fitted penis.  A modified version of source penis adapted to 'mount' on a given game-time CBody instance.  Must be re-generated everytime source body morphs to ensure a proper mount
        

        print("\n\n\n=============== PENIS MOUNTING PROCEDURE ===============")
        print("\n===== A. PREPARE THE BODY HOLE FOR PENIS INSERTION INTO RIM =====")
        #=== Visualizer Cubes Preparation.  Must run first before entering edit mode ===
        self.oVisualizerCubes = G.CVisualizerCubes(0)       # Utility class to help debug / visualise this complex algorithm.  Set to about 600 to create enough 'visualization cubes' shown about different layers       
        bpy.data.scenes[0].layers[1] = 0            ###INFO: How to select which layers are shown.  (Must have at least one layer shown at ALL times!)
        bpy.data.scenes[0].layers[0] = 1            ###INFO: How to hide default layer 0 (show another layer first!)

        #=== Duplicate the source body's armature object and give it the required name ===
        oArmNode = DuplicateAsSingleton('[' + sNameBodySource + ']', '[' + sNameBodyDestination + ']')
        Util_HideMesh(oArmNode)
        

        #=== Create extra geometry near where the penis will be mounted (the 'mounting hole') ===
        if self.oSkinMeshGame.Open():
            oVertGrp_PenisExtraGeometry = self.oSkinMeshGame.VertGrp_SelectVerts("_CPenisFit_ExtraGeometry")     # Obtain the area of the body's mesh that we are to replace with a fitted penis
            bpy.ops.mesh.select_more()                  # Select one more ring so the rim gets enough geometry to properly connect to fine-geometry penis
            bpy.ops.mesh.subdivide(quadtri=True)
            bpy.ops.mesh.select_less()                  # Fix the extra geometry group by selected twice less and re-assigning
            bpy.ops.mesh.select_less()
            bpy.ops.object.vertex_group_assign()
    
            #=== The above subdivide messed up our vertex group for the mounting hole rim.  Fix it now ===  (Only half the verts are now in group, new ones not)
            oVertGrp_PenisMountingHole = self.oSkinMeshGame.VertGrp_SelectVerts("_CPenisFit_MountingHole", bClearSelection = False)     # Obtain the area of the body's mesh that we are to replace with a fitted penis
            bpy.ops.mesh.select_more()                  ###INFO: Trick when half the verts in a ring are selected is to select more and then less = selects all in that ring!        ###CHECK: Is that really true??
            bpy.ops.mesh.select_less()                  # Fix the important mounting hole vert group by adding to fixed extra geometry group above, selecting more then less.
            bpy.ops.object.vertex_group_assign()
    
    
            
            #=== Obtain reference to the rim verts ===
            bpy.ops.mesh.region_to_loop()               # Obtain the rim from the mesh (still containing inner part of hole) with region_to_loop()
            self.oSkinMeshGame.bm.verts.ensure_lookup_table()
            aVertsBodyRim = [oVert.index for oVert in self.oSkinMeshGame.bm.verts if oVert.select]      # Obtain list of all body rim hole verts.  Needed for many iterations
            
            #=== Find the key verts of the rim hole opening.  We need these in 'modify base vert' section below to morph the penis base closer to the rim ===
            vecPenisRimCenter = Vector()
            oVertRimRightmost = None                        # The rim vert with the highest +X coordinate.  Used to re-interpolate penis UVs for re-texturing                        
            nVertRimRightmostX_Max = sys.float_info.min                # The X coordinates of the rightmost rim vert.  Used to find 'oVertRimRightmost'
            aVertsAtZeroX = []
            for nVertRim in aVertsBodyRim:                  # Iterate through the rim verts to find the verts at X=0.  There should be exactly two: One for top of hole the other for bottom of hole
                oVertRim = self.oSkinMeshGame.bm.verts[nVertRim]
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
            vecVertRimTop    = oVertRimTop.co.copy()    ###INFO: copy() is extremely important (data would point to some garbage once owning bmesh goes out of scope!)      
            vecVertRimBottom = oVertRimBottom.co.copy()
            vecPenisRimCenter /= len(aVertsBodyRim)
            vecPenisRimCenter.y -= 0.05                 ###HACK: Hack on center so that it's easier to determine verts toward penis / toward base (give a push forward toward tip) 
            bpy.context.scene.cursor_location = vecPenisRimCenter      
            print("\n=== Center = {}   Top = {}   Bottom = {}  Rightmost {} ===".format(vecPenisRimCenter, vecVertRimTop, vecVertRimBottom, oVertRimRightmost.co))   
    
    
    
    
    
            print("\n===== B. CREATE CHAIN OF RIM VERTS IN OUR STRUCTURES =====")
            oLayUV_Body  = self.oSkinMeshGame.bm.loops.layers.uv.active                    # Obtain access to the body's UV layer (so we can extract rim vert UVs and set them into penis rim verts)
            oRimVertBodyRoot = CRimVertBody(self, None, oVertRimTop, oVertRimTop.link_loops[0][oLayUV_Body].uv.copy())        # The string starts at the master rim vert (topmost at X=0)
            oRimVertBodyNow = oRimVertBodyRoot                              # Before we iterate set the 'next' as the root because it is the iteration's starting point
            
            while True:                             # Iterate through circular loop until we reach the node flagged as the last one
                oVertBodyRimNow = self.oSkinMeshGame.bm.verts[oRimVertBodyNow.nVertBody]
                print(oRimVertBodyNow)
    
                for oEdgeToChild in oVertBodyRimNow.link_edges:
                    if oEdgeToChild.select and oEdgeToChild.tag:                    # Only iterate into edges that are on the rim that (currently selected) and not traversed (tag = True)    ###CHECK: Why are all edges tagged??  Might have to create a loop above to set them to a deterministic state if this check ever fails
                        oVertNext = oEdgeToChild.other_vert(oVertBodyRimNow)
                        if oVertNext.index != oVertRimTop.index:                # Only create a new link if we haven't looped back to starting vert yet
                            vecUV_Body = oVertBodyRimNow.link_loops[0][oLayUV_Body].uv.copy()
                            oRimVertBodyNow = oRimVertBodyNow.SetNext(oEdgeToChild, oVertNext, vecUV_Body)
                        else:                                                           # We've encountered the 'first vert' once again.  End the iteration by...
                            oRimVertBodyNow.bLastInLoop = True                          #... flagging the last node as the last one...
                            oRimVertBodyNow .oRimVertBodyNext = oRimVertBodyRoot        #... and set 'next'     of last  node to first node...
                            oRimVertBodyRoot.oRimVertBodyPrev = oRimVertBodyNow         #... and set 'previous' of first node to last  node...
                            print("- Chaining: linking first {} to last {}".format(oRimVertBodyRoot, oRimVertBodyNow))
                        oEdgeToChild.tag = False            # Tag this edge as 'traversed' so we don't iterate that way again...
                        break                                                           # We have committed to this edge.  Stop iterating through other edges (exit for loop and back into infinite while loop)
                if oRimVertBodyNow.bLastInLoop:
                    break
            self.oSkinMeshGame.Close(bHide = True)


        
        
        
        print("\n===== C. MODIFY THE PENIS BASE VERTS TO BE CLOSER TO BODY'S RIM OPENING =====")
        #=== Move all penis verts so the designated penis master vert coincides with the body's rim master vert (located at X=0 at penis top) ===
        self.oMeshPenisSource = CMesh.Attach("Penis")                   ###IMPROVE: From argument?  Ok to assume this name?
        self.oMeshPenis = CMesh.AttachFromDuplicate(self.oSkinMeshGame.GetName() + "-Penis-Fitted", self.oMeshPenisSource)
        Cleanup_RemoveDoublesAndConvertToTris(0.000001)                             # Convert the penis to tris right away                                                              
        self.oMeshPenis.SetParent(self.oSkinMeshGame.GetMesh().parent.name)

        #=== Link to our custom armature and set all our meshes to this just-created armature object ===        #?
        bpy.ops.object.modifier_add(type='ARMATURE')
        self.oMeshPenis.  GetMesh().modifiers["Armature"].object = oArmNode       # Set both body and penis to the new armature
        self.oSkinMeshGame.         GetMesh().modifiers["Armature"].object = oArmNode
        self.oSkinMeshGame.         SetParent(oArmNode.name)                                # Set both body and penis as parent of armature Blender node
        self.oMeshPenis.  SetParent(oArmNode.name)


        if self.sNameBodySource != "Woman" and self.sNameBodySource != "ManRawImport": 
            raise Exception("###EXCEPTION: Manual morphing procedure not created to modify penis base for a body mesh of type '{}'".format(self.oSkinMeshGame.GetName()))       ###TODO21:!! Man mesh

        
        if self.oMeshPenis.Open():
            self.oMeshPenis.VertGrp_SelectVerts("_CPenisFit_VertTop")     # Obtain our previously defined top vert.
            oVertPenisTop = Util_GetFirstSelectedVert(self.oMeshPenis.bm)
            vecShiftOfAllPenisVerts = vecVertRimTop - oVertPenisTop.co
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.translate(value=vecShiftOfAllPenisVerts)
            bpy.ops.mesh.select_all(action='DESELECT')
    
            #=== Proportionally move the bottom penis vert so that bottom of penis aligns much closer to bottom of rim hole ===
            self.oMeshPenis.VertGrp_SelectVerts("_CPenisFit_VertBottom")
            oVertPenisBottom = Util_GetFirstSelectedVert(self.oMeshPenis.bm)
            vecShiftBottomVert = vecVertRimBottom - oVertPenisBottom.co
            bpy.ops.transform.translate(value=vecShiftBottomVert, proportional='CONNECTED', proportional_edit_falloff='SMOOTH', proportional_size=0.12)       ###TUNE: proportional size
    
            #=== Proportionally move a small area of verts underneath the scrotum close to base that are just too far from rim ===
            self.oMeshPenis.VertGrp_SelectVerts("_CPenisFit_ScrotumBase")
            bpy.ops.transform.translate(value=(0, 0, 0.0046), proportional='ENABLED', proportional_edit_falloff='SMOOTH', proportional_size=0.012)           ###TUNE
    
            #=== Proportionally move the side verts to make them wider (and with a softer angle) to rim edges ===
            self.oMeshPenis.VertGrp_SelectVerts("_CPenisFit_BaseSides")
            nRatio = 1.12
            bpy.ops.transform.resize(value=(nRatio, nRatio, nRatio), constraint_orientation='GLOBAL', mirror=False, proportional='CONNECTED', proportional_edit_falloff='SMOOTH', proportional_size=0.032)
            bpy.context.scene.cursor_location = Vector((0,0,0))     



        
            print("\n===== D. MATCH PENIS RIM VERTS TO BODY RIM VERTS =====")
            #=== Create a KD Tree of all the verts in the penis mounting area.  This tree will be used to rapidly find the closest vert to each vert of our mouting rim ===
            oKDTreePenis = kdtree.KDTree(len(self.oMeshPenis.bm.verts))                     ###OPT: Would run a bit faster if we limit KDTree to verts near base
            for oVertPenis in self.oMeshPenis.bm.verts:
                oKDTreePenis.insert(oVertPenis.co, oVertPenis.index)
            oKDTreePenis.balance()
    
            #=== Iterate through all the body rim verts to find their closest penis vert.  As we have a many-to-many between the two rim domains some body rim verts will point to multiple penis rim verts and some body rim verts will have no penis rim verts.  (Next loop choses the closest one)
            dictRimVertPenis = {}                                   # Dictionary of unique penis rim verts.
            oRimVertBodyNow = oRimVertBodyRoot
            self.oMeshPenis.bm.verts.ensure_lookup_table()
            while True:
                vecVertPenisClosestToRimVertBody, nVertPenisClosestToRimVertBody, nDist = oKDTreePenis.find(oRimVertBodyNow.vecVertBody)
                oVertPenisRim = self.oMeshPenis.bm.verts[nVertPenisClosestToRimVertBody]
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
            oVertGrp_PenisBaseNonManifold = self.oMeshPenis.GetMesh().vertex_groups.new("_CPenisFit_BaseNonManifold")     ###IMPROVE: Function for new vert groups?
            bpy.ops.object.vertex_group_assign()
    
            #=== Iterate through all the defined penis rim verts and choose the closest body rim vert for each one ===
            bpy.ops.mesh.select_all(action='DESELECT')
            for nRimVertPenis in dictRimVertPenis:
                oRimVertPenis = dictRimVertPenis[nRimVertPenis]
                oRimVertBody = oRimVertPenis.RimVertBody_FindClosest()
                oRimVertPenis.oVertPenis.select_set(True)                       # Also select so we can define vertex group just below
    
            #=== Create a new vertex group for the penis rim.  It will be needed later on to easily identify penis rim verts ===
            oVertGrp_PenisRimVerts = self.oMeshPenis.GetMesh().vertex_groups.new("_CPenis_RimVerts") 
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
     
                oEdgeOnRim = self.oMeshPenis.bm.edges.get([oRimVertPenis1, oRimVertPenis2])         ###INFO: How to find an existing edge
                if oEdgeOnRim is None:
                    oRimVertPenis1.select_set(True)
                    oRimVertPenis2.select_set(True)
                    bpy.ops.mesh.shortest_path_select()                     ###INFO: How to select shortest path
                    oRimVertPenis1.select_set(False)
                    oRimVertPenis2.select_set(False)
                    bpy.ops.mesh.dissolve_verts()                           ###OPT!!!: Runs very slowly but essential.  Can we possibly try to fix mesh after deleting this verts?  (Or UVs too badly damaged after 'make face' again?)
                    print("- Edge vert dissolve: Dissolved verts between {} and {} ".format(oRimVertPenis1, oRimVertPenis2))
                    oRimVertPenis1.select_set(True)
                    oRimVertPenis2.select_set(True)
                    bpy.ops.mesh.vert_connect()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    oEdgeOnRim = self.oMeshPenis.bm.edges.get([oRimVertPenis1, oRimVertPenis2])         ###INFO: How to find an existing edge
                    if oEdgeOnRim is None:
                        print("- ERROR: Edge vert dissolve: Could not connect verts {} and {} ".format(oRimVertPenis1, oRimVertPenis2))
    
                if oRimVertBodyNow.bLastInLoop:
                    break
                oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
    
    
    
            
            print("\n===== H. REMOVE UNNEDDED PENIS GEOMETRY =====")
            #=== Starting at the non-manifold penis base edges keep selecting 'more' and de-selecting the rim verts... this will select all geometry we can delete ===         
            bpy.ops.mesh.select_all(action='DESELECT')
            self.oMeshPenis.GetMesh().vertex_groups.active_index = oVertGrp_PenisBaseNonManifold.index
            bpy.ops.object.vertex_group_select()
            self.oMeshPenis.GetMesh().vertex_groups.active_index = oVertGrp_PenisRimVerts.index
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
            self.oMeshPenis.GetMesh().vertex_groups.active_index = oVertGrp_PenisRimVerts.index
            bpy.ops.object.vertex_group_select()
            for n in range(5):
                bpy.ops.mesh.select_more()                  # Progressively smooth right around (modified rim)...
                bpy.ops.object.vertex_group_deselect()      #... but we never move rim verts themselves!
                bpy.ops.mesh.vertices_smooth(5)             ###TUNE: Smoothing
    
            #=== Remove all vertex groups and create a new one for CSoftBody implementation to use to create soft body from penis ===
            self.oMeshPenis.VertGrp_Remove(r"_CPenisFit_")        #?
            oVertGrp_Penis = self.oMeshPenis.GetMesh().vertex_groups.new(G.C_VertGrp_CSoftBody + "Penis")
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.data.scenes[0].tool_settings.vertex_group_weight = 0        ###CHECK: Make sure this works!
            bpy.ops.object.vertex_group_assign()
            bpy.ops.mesh.select_all(action='DESELECT')
            self.oMeshPenis.Close()

        #=== Switch the penis to its unique material / texture / image so that the starting texture can be modified to uniquely 'blend' this penis texture to this body ===
        aMatSlots = self.oMeshPenis.GetMesh().material_slots
        oMatBase = aMatSlots[0].material
        aMatSlots[0].material = bpy.data.materials[oMatBase.name + "_WomanA"]           ###INFO: Materials / textures / images have already been populated in the .blend file to be able to simply switch materials like this
        
        

        print("\n===== J. SKINNING PENIS FROM ORIGINAL BODY =====")
        #=== Transfer skinning info from body to unskinned penis.  This is essential so penis base moves with the body! ===
        ###OPT ###IMPROVE: We only need skinning info to transfer to the base not the entire shaft!  Can be sped up?
#         self.oMeshPenis.Util_TransferWeights(self.oSkinMeshGame, False)
#         if self.oMeshPenis.Open():
#             self.oMeshPenis.VertGrp_Remove(re.compile(oVertGrp_PenisMountingHole.name), bSelectVerts = True)      # Weight transfer above also transferred the mounting hole vert group which we don't want
#             self.oMeshPenis.Close()
        




        print("\n===== K. PERFORM FINAL CLEANUP BODY AND PENIS MESH BEFORE JOIN ======")
        #=== Cleanup the extraneous materials while keeping the most important one ===        ###OBS: Raw penis from DAZ gets it extra texture removed manually
        #oMatPenisMainMaterial = self.oMeshPenis.GetMeshData().materials["Skin"]       # Before removing all materials obtain reference to the one we need to keep
        #while len(self.oMeshPenis.GetMeshData().materials) > 0:                       # Remove all the materials
        #    bpy.ops.object.material_slot_remove()
        #bpy.ops.object.material_slot_add()
        #self.oMeshPenis.GetMesh().material_slots[0].material = oMatPenisMainMaterial     # In the re-created slot re-assign the body material so it is the only material there.
        
        #=== Refresh the BMVerts we need to dissolve after the next vert delete for mounting hole ===
        if self.oSkinMeshGame.Open(bDeselect = True):
            self.oSkinMeshGame.bm.verts.ensure_lookup_table()
            for oRimVertBodyNow in aRimVertBodyToDissolve:
                oRimVertBodyNow.oVertBody = self.oSkinMeshGame.bm.verts[oRimVertBodyNow.nVertBody]     # Update the BMVert from the index all indices are about to become invalid after vert delete below

            #=== Remove the verts inside the penis mounting hole (e.g. finally create the 'hole' needed for penis to weld in) ===
            self.oSkinMeshGame.GetMesh().vertex_groups.active_index = oVertGrp_PenisMountingHole.index
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_less()                  # Vertex group contains the rim verts which we want to keep.  Select one vert ring less to select only the inner verts we must delete
            bpy.ops.mesh.delete(type='VERT')            # Delete the mounting area's inner hole.  Penis can now be merged right in place by welding close verts
            
            #=== Dissolve the unused geometry of the body's penis rim.  Leaving them would create holes after join! ===
            self.oSkinMeshGame.bm.verts.ensure_lookup_table()
            for oRimVertBodyNow in aRimVertBodyToDissolve:
                if oRimVertBodyNow.oVertBody.is_valid:
                    oRimVertBodyNow.oVertBody.select_set(True)
                else:
                    print(oRimVertBodyNow.oVertBody)
                print("- Dissolving marked body rim vert {}".format(oRimVertBodyNow))
            bpy.ops.mesh.dissolve_verts()
            
            #=== Re-triangulate penis mounting hole area ===
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.select_more()
            bpy.ops.mesh.quads_convert_to_tris()
            self.oSkinMeshGame.Close()


        print("\n===== Z. FINISHED! =====")





    def JoinPenisToBody(self):

        #=== Join fitted and rigged penis with body ===
        self.oMeshPenisWork = CMesh.AttachFromDuplicate(self.oMeshPenis.GetName() + "-TEMPFORJOIN", self.oMeshPenis)
        self.oSkinMeshGame.GetMesh().select = True
        bpy.context.scene.objects.active = self.oSkinMeshGame.GetMesh()
        bpy.ops.object.join()
        self.oMeshPenisWork = None                                                           # Penis mesh just got destroyed by join() above so we clear our reference
        
        #=== Leave only the non-manifold edges selected so bridge_edge_loop() can merge run === 
        print("\n=== Join the fitted-penis to the fitted body mesh together ===") 
        if self.oSkinMeshGame.Open():
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            self.oSkinMeshGame.VertGrp_SelectVerts("_CPenis_Uretra")                                  # Select a vertex group we know exists on the penis side...
            bpy.ops.mesh.select_linked()                                                        #... then select all linked verts so we have all penis verts...
            #oVertGrp_Penis = self.oSkinMeshGame.GetMesh().vertex_groups.new(G.C_VertGrp_CSoftBody + "Penis")       #... but remember the penis verts first        ###IMPROVE: Make call to create vert groups!
            #bpy.ops.object.vertex_group_assign()                                                #... by assigning to a new vert group 
            bpy.ops.mesh.region_to_loop()                                                       #... then ask for the boundaries of all penis verts to leave only the penis-side rim verts
            self.oSkinMeshGame.VertGrp_SelectVerts("_CPenisFit_MountingHole", bClearSelection = False)#... and add to the selection the body-side rim verts.  At this point we have the matching edge rings both selected for bridge_edge_loop() below
            for oEdge in self.oSkinMeshGame.bm.edges:
                if oEdge.select:
                    if oEdge.is_manifold == True:                                   # Only leave the non-manifold edges selected for the bridge_edge_loop() call below.  It *must* have equal # of edges on each side and Blender includes in selection any edges that have both verts selected (e.g. small corner triangles)
                        oEdge.select_set(False)
            bpy.ops.mesh.bridge_edge_loops(type='PAIRS', use_merge=True, merge_factor=0)        ###INFO: An incredibly useful way to connect two meshes.  All other attempts to do via BMesh what this call does miraculously have been disasters!  (e.g. trashes one vert or the other or insanely slow!)
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            self.oSkinMeshGame.Close()        # We must close and re-open the same mesh for the shape key data to fully update itself (needed for next loop)

            
        #=== Iterate throughh all our shape keys / morphs to move the entire penis by the same delta as the difference between the 'master mounting vert' between the 'basis' mesh and each shape key.  This greatly enhances the look of the mesh on morphs that affect the genitals area such as 'Voluptuous' or 'Thin' ===
        print("\n=== Moving penis to fit each shape key ===") 
        if self.oSkinMeshGame.Open():
            oVert_MasterMountingVert_Basis = self.oSkinMeshGame.VertGrp_FindFirstVertInGroup("_CPenisFit_MasterMountingVert")
            nVert_MasterMountingVert = oVert_MasterMountingVert_Basis.index
            vecVert_MasterMountingVert_Basis = oVert_MasterMountingVert_Basis.co.copy() 
            print("Penis master mounting vert {} at {}".format(oVert_MasterMountingVert_Basis, vecVert_MasterMountingVert_Basis))
            
            #=== Select the entire penis (minus the rim).  We will move it for any shape keys that detect a movement on the 'master mounting vert' between basis to each shape key ===
            self.oSkinMeshGame.VertGrp_SelectVerts(G.C_VertGrp_CSoftBody + "Penis")
            
            #=== Iterate through all shape keys to move the penis by the necessary amount ===
            aShapeKeys =  self.oSkinMeshGame.GetMeshData().shape_keys.key_blocks
            nShapeKeys = len(aShapeKeys)
            for nShapeKey in range(nShapeKeys):
                self.oSkinMeshGame.GetMesh().active_shape_key_index = nShapeKey
                oShapeKey = aShapeKeys[nShapeKey]
                aVerts_ShapeKeys = oShapeKey.data
                oVert_MasterMountingVert_ShapeKey = aVerts_ShapeKeys[nVert_MasterMountingVert]
                vecVert_MasterMountingVert_ShapeKey = oVert_MasterMountingVert_ShapeKey.co.copy()
                vecDelta_MasterMountingVert_BasisToShapeKey = vecVert_MasterMountingVert_ShapeKey - vecVert_MasterMountingVert_Basis
                if vecDelta_MasterMountingVert_BasisToShapeKey.length_squared > 0:
                    bpy.ops.transform.translate(value=vecDelta_MasterMountingVert_BasisToShapeKey)
                    print("- Moving penis by {} for shape key '{}'".format(vecDelta_MasterMountingVert_BasisToShapeKey, oShapeKey.name))
                else:
                    print("- No penis movement necessary for shape key '{}'".format(oShapeKey.name))
            self.oSkinMeshGame.GetMesh().active_shape_key_index = 0

            #=== Select the penis rim area and Iterate through all shape keys to smooth the area between the penis and its body mounting area ===
            print("\n=== Smoothing area between penis and body for each shape key ===") 
            self.oSkinMeshGame.VertGrp_SelectVerts(G.C_VertGrp_CSoftBody + "Penis")
            bpy.ops.mesh.region_to_loop()           ###IMPROVE: Use functional rim selection instead?
            for n in range(3):
                bpy.ops.mesh.select_more()
            
            for nShapeKey in range(nShapeKeys):
                self.oSkinMeshGame.GetMesh().active_shape_key_index = nShapeKey
                oShapeKey = aShapeKeys[nShapeKey]
                sNameShapeKey = oShapeKey.name
                aVerts_ShapeKeys = oShapeKey.data
                if sNameShapeKey == "Basis" or sNameShapeKey[:3] == "FBM":              ###WEAK: Assumes we have fully qualified name of morph where FBM = Full Body Morph 
                    print("- Smoothing penis base area for shape key '{}'".format(sNameShapeKey))
                    bpy.ops.mesh.vertices_smooth(factor=1, repeat=5)                    ###INFO: We avoid smoothing shape keys that do not move the penis mounting area as we already smooth 'Basis' and smoothing shape keys that don't move make them 'add up' the adjustment and the sum of several looks bad
                else:
                    print("- Skipping penis base area smoothing for shape key '{}'".format(sNameShapeKey))
            self.oSkinMeshGame.GetMesh().active_shape_key_index = 0           ###IMPROVE: Add this to CMesh.Close()?
            self.oSkinMeshGame.Close(bDeselect = True)

        print("--- Done merging penis to body mesh! ---\n\n") 




        


class CRimVertBody():               # CRimVertBody: Helper class to store all information related to a rim vert on the body side
    s_nRimVertBodyID_Next = 0       # Static counter to auto-increment 'self.nRimVertBodyID'
    
    def __init__(self, oMeshPenis, oRimVertBodyPrev, oVertBody, vecUV_Body):
        self.oMeshPenis         = oMeshPenis
        self.oRimVertBodyPrev   = oRimVertBodyPrev      # Our 'previous' CRimVertBody  (The rim vert just prior to us along the rim edge)
        self.oRimVertBodyNext   = None                  # Our 'next'     CRimVertBody  (The rim vert just next  to us along the rim edge) (Set by SetNext())
        self.oVertBody          = oVertBody             # Our BMVert on the body's rim for penis
        self.nVertBody          = self.oVertBody.index  # VertID of this rim vert in body mesh
        self.vecVertBody        = self.oVertBody.co.copy()  # The position of this body rim vert    ###INFO: copy() hugely important.  (Data would point to garbage when BMesh data falls out of scope!)
        self.vecUV_Body         = vecUV_Body            # The UV coordinate of the body-side rim vert.  Used to set penis-side rim vert UV
        self.nEdgeToChild       = None                  # The edge that links self.nVertBody to self.oRimVertBodyNext.nVertBody (Set by SetNext())  ###OBS?
        self.nLenEdgeToChildLen = None                  # Length of edge between parent and child.  Used to dissolve penis verts that are too close 
        self.oRimVertPenis      = None                  # CRimVertPenis instance assigned to us (closest). Can be None (in areas where more geometry exists on body rim than penis rim)
        self.oVisualizerCube    = None                  # Reference to our 'visualizer cube' that renders in 3D scene where this vertex is.  Essential during development!
        self.bLastInLoop        = False                 # Set to true on the very last node in the loop.  Allows iteration loops to iterate through every node of the loop exactly once   

        self.nRimVertBodyID = CRimVertBody.s_nRimVertBodyID_Next
        CRimVertBody.s_nRimVertBodyID_Next += 1

        self.oVisualizerCube = self.oMeshPenis.oVisualizerCubes.GetCube("RimB{:02d}".format(self.nRimVertBodyID), self.vecVertBody, 'Green', self.oMeshPenis.C_Layer_RimVertBody, True) 

    def SetNext(self, oEdgeToChild, oVertBody, vecUV_Body):             # Sets the one and only child
        self.nEdgeToChild   = oEdgeToChild.index            # Set on the parent edge that was used to find self.oRimVertBodyNext
        self.nLenEdgeToChildLen = oEdgeToChild.calc_length()
        self.oRimVertBodyNext  = CRimVertBody(self.oMeshPenis, self, oVertBody, vecUV_Body)
        return self.oRimVertBodyNext                   # Return child for one-line creation + assignment

    def __str__(self):
        nRimVertPenisID = -1
        if self.oRimVertPenis is not None:
            nRimVertPenisID= self.oRimVertPenis.nRimVertPenisID
        return "[Body #{:2d}  Vert={:5d}  P={:2d}  {:6.3f},{:6.3f},{:6.3f}]".format(self.nRimVertBodyID, self.nVertBody, nRimVertPenisID, self.vecVertBody.x, self.vecVertBody.y, self.vecVertBody.z)



class CRimVertPenis():              # CRimVertPenis: Helper class to store all information related to a rim vert on the penis side
    s_nRimVertPenisID_Next = 0      # Static counter to auto-increment 'self.nRimVertPenisID'
    
    def __init__(self, oMeshPenis, oVertPenis):
        self.oMeshPenis         = oMeshPenis
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
        
    def RimVertBody_FindClosest(self):                  # Find the closest body-side rim vert that connected to us in self.aRimVertBody.  Second step needed to enables closest traversal accross the many-to-many
        nDistMin = sys.float_info.max
        for oRimVertBody in self.aRimVertBody:
            nDist = (oRimVertBody.vecVertBody - self.vecVertPenis).length
            if nDistMin > nDist:
                nDistMin = nDist
                self.oRimVertBody = oRimVertBody
        self.oRimVertBody.oRimVertPenis = self              # Link body rim vert to this penis rim vert
        self.aRimVertBody = None                            # Done with collection so destroy to save memory
        self.oVisualizerCube = self.oMeshPenis.oVisualizerCubes.GetCube("RimP{:02d}".format(self.oRimVertBody.nRimVertBodyID), self.vecVertPenis, 'Blue', self.oMeshPenis.C_Layer_RimVertPenis, False)    # Add our visualizer cube 
        print("{}  <==>  {}".format(self, self.oRimVertBody))
        return self.oRimVertBody

    def __str__(self):
        nRimVertBodyID = -1
        if self.oRimVertBody is not None:
            nRimVertBodyID = self.oRimVertBody.nRimVertBodyID
        return "[Penis #{:2d}  Vert={:5d}  B={:2d}]".format(self.nRimVertPenisID, self.oVertPenis.index, nRimVertBodyID)

















            #aVertsJoinedRim = [oVert.index for oVert in self.oSkinMeshGame.bm.verts if oVert.select]      # Obtain list of just-joined rim verts to survive the trashing our vert groups are going to suffer in blending below  ###IMPROVE: Need to store this in vert group for anything?
            #=== Blend body base bones into penis verts so penis bones blend with body bones ===
#             self.oSkinMeshGame.VertGrp_SelectVerts(oVertGrp_Penis.name)
#             bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=1.0, repeat=8)       ###TUNE:!!!   
#             bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)   # Limit to the four bones Unity can do at runtime.
#             bpy.ops.object.vertex_group_normalize_all(lock_active=False)                ###DESIGN24:! Keep here?  Do at very end?
    
            #=== Smooth the area around the just-joined meshes ===
#             bpy.ops.mesh.region_to_loop()                                           # Right now every penis vert is selected minus the rim.  Get the boundary so we can expand and smooth around
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.vertices_smooth(20)            ###TUNE:!            

        #aVertsJoinedRim = [oVert.index for oVert in self.oSkinMeshGame.bm.verts if oVert.select]      # Obtain list of just-joined rim verts to survive the trashing our vert groups are going to suffer in blending below
        ###IMPROVE: have lost the definition of what verts inside penis but can recover with bpy.ops.object.material_slot_select()  (Or store in array before blend weights above?)

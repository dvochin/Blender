###IMPROVE: Add error check when boolean returns no polys!

import bpy
import sys
import bmesh
from math import *
from mathutils import *

from gBlender import *
import G
import Curve
import Border
import Client

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CLOTH CUTTING
#---------------------------------------------------------------------------    

def Cut_ApplyCuts(sNameClothSource, sNameClothOutput, bCleanupBorders):     ###OBS???
    print("\n======= Cut_ApplyCuts BEGIN =======")

    #=== Prepare for function by extracting needed objects from scene ===
    oMeshO = DuplicateAsSingleton(sNameClothSource, sNameClothOutput, G.C_NodeFolder_Game, True)
    Util_HideMesh(oMeshO)
    oMeshO.hide_render = False
    bpy.ops.object.mode_set(mode='EDIT')
    oCurves = bpy.data.objects[G.C_NodeName_Curve]
    aBorderLocatorVertPos = {}                            # Map of 'locator verts' for each border.  Because boolean destroys most mesh metainfo, we're using the vertex position of one vertex on each border to rebuild the list of verts per border
    
    #=== Iterate through all active curves to obtain their cutters and get them to work cutting the working cloth ===
    print("\n===== Cut_ApplyCuts Phase1: Applying cutters =====")
    for oCurve in oCurves.children:
        if oCurve.hide_render: continue                    ###TEMP ###CHECK: Keep this (useful) technique to disable objects without changing parent??
        Cut_ApplyCut(oMeshO, oCurve, aBorderLocatorVertPos)

    #=== Now that the highly-destructive boolean operations are all done (which prevent any type of mesh meta info from traversing), perform border reconstruction and cleanup ===
    if bCleanupBorders:
        print("\n===== Cut_ApplyCuts Phase2: Cleaning up borders =====")
        for oCurve in oCurves.children:
            if oCurve.hide_render: continue                    ###TEMP ###CHECK: Keep this (useful) technique to disable objects without changing parent??
            Cut_CleanupBorder(oMeshO, oCurve, aBorderLocatorVertPos)      # Prepare the border by cleaning it up toward the final topology that will be used to actually create the border (run after any cloth simulation)
        
    bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)    # Not sure this is really needed but just to make sure... 
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.update()
        
    return G.DumpStr("OK: Cut_ApplyCuts('{}', '{}', Cleanup={} with {} verts and {} faces.".format(sNameClothSource, sNameClothOutput, bCleanupBorders,  len(oMeshO.data.vertices), len(oMeshO.data.polygons)))




###OBS: Revice for flat UV!
def Cut_CleanupBorder(oMeshO, oCurveO, aBorderLocatorVertPos):           # Complex function to perform advanced cleanup of a boolean-cut border.  Border is identified by 'oVertLocatorOnBorder', a 3D coordinate of a vertex known to be on that border.  (Other border verts are located by walking the boundary edges starting from that known vertex)
    #=== This call runs in a loop AFTER Cut_ApplyCut() which performs the destructive boolean operation.  The maximum amount of code is shifted to occur after boolean as in here we can store meta info in the mesh (such as border vertex groups) without boolean destroying it on the next border creation ===
    sCurveName = oCurveO.name
    bSymmetryX = oCurveO.data.splines[0].use_cyclic_u       # Symmetry curves are by definition cyclic (e.g. side curve), non-symmetry (e.g. neck opening) are non-cyclic as their points are mirrored with a mirror modifier
    nSymmetryIterations = bSymmetryX + 1  # The symmetry cutters (e.g. arms and legs) have this set to two so next big loop runs twice for each side
 
    #=== A curve will perform two cuts (for each side of the body) if symmetrical.  This loop iterates once or twice depending on symmetry ===
    for nSymmetryRun in range(nSymmetryIterations):
        sCutName = oCurveO.name
        if nSymmetryIterations > 1:                                 # The name of the cut is suffixed only for symmetrical cuts (e.g. ArmL and ArmR)
            sCutName += G.C_SymmetrySuffixNames[nSymmetryRun]
        vecVertLocatorOnBorderPos = aBorderLocatorVertPos[sCutName]                   # Fetch back the position of the locator vert from the curve name
     
        print("\n\n=== Cut_CleanupAfterCut() Generating cloth border '{}' for mesh '{}' ===".format(sCutName, oMeshO.name))
        oMesh = oMeshO.data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.uv.seams_from_islands()             # Boolean cut even removed UV seams!!  Reconstruct them so this call can safely avoid merging faces accross seams
        bm = bmesh.from_edit_mesh(oMesh)
         
        #=== Before the sophisticated border cleanup, cleanup the 'tiny face slivers with default UVs' the boolean operation created on the border of the cut by using their UV information (in default state) ===
        bpy.ops.mesh.select_all(action='DESELECT')
        oLayUV = bm.loops.layers.uv.active
        for oFace in bm.faces:          # Iterate through all faces and delete those that have 2+ verts with UVs in the 'default' position (either 0 or 1)
            nNumVertsWithDefaultUvInThisFace = 0
            for oLoop in oFace.loops:
                vecUV = oLoop[oLayUV].uv        # Boolean leaves a ton of tiny sliver faces along the cut edge.  Fortunately they all have default UV coordinates and are easy to find!
                if ((vecUV.x == 0 or vecUV.x == 1) and (vecUV.y == 0 or vecUV.y == 1)):
                    nNumVertsWithDefaultUvInThisFace += 1
            if (nNumVertsWithDefaultUvInThisFace >= 2):
                oFace.select_set(True)
        bpy.ops.mesh.delete(type='FACE')            # Delete all 'sliver faces' that boolean created along the new cut border.  As a result we'll be left with the border being a loop of (messy) vertices that are far easier to cleanup!
        bpy.ops.uv.seams_from_islands(mark_seams=True, mark_sharp=False)        # The above deletion of faces with default UVs leaves neighboring edges marked as seams.  Recalc seams from UV islands 
     
        #=== Locate the 'border locator vert' from the 3D coordinates given === (Given as 3D position because of boolean destructive operations made passing by ID or any mesh metainfo impossible)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        oVertLocatorOnBorder = None
        for oVert in bm.verts:                              ###WEAK: Iteration through verts to find position... Can we find a C function to return closest vert more quickly??
            if oVert.co == vecVertLocatorOnBorderPos:
                oVertLocatorOnBorder = oVert
                break
        if oVertLocatorOnBorder == None:
            raise Exception("###EXCEPTION: Cut_CleanupBorder() could not find oVertLocatorOnBorder from position {} on border '{}'".format(vecVertLocatorOnBorderPos, sCurveName))
     
        #=== Obtain the verts of the just-cut border by starting at the 'oVertLocatorOnBorder' locater vert and by 'walking' the mesh along boundary edges ===
        oVertNow = oVertLocatorOnBorder
        while oVertNow.tag == False:
            #print("-CleanupAfterCut() finds border vert %5d" % (oVertNow.index))
            oVertNow.tag = True             # Tag this vert so we know when to stop        ###CHECK: We are tagging verts & edges... untag them to prevent other parts of algorithms to screw up?
            oVertNow.select_set(True)
            oEdgeOnEdge = None
            for oEdge in oVertNow.link_edges:
                if oEdge.is_boundary == True and oEdge.tag == False:
                    oEdgeOnEdge = oEdge
            if oEdgeOnEdge == None:
                raise Exception("###EXCEPTION: Cut_CleanupAfterCut could not iterate through boundary edges while collecting border verts.")
            oEdgeOnEdge.tag = True                      # Tag this edge so we don't traverse it again.
            oVertNow = oEdgeOnEdge.other_vert(oVertNow)
     
        #=== Now that we're past boolean, vertex groups are no longer destroyed so we can (finally) create the heavily-used vertex group for this border (that will also store border lenght information for each border vertex) ===
        oVertGroup_Border = oMeshO.vertex_groups.new(name = G.C_VertGrp_Border + sCutName)      # Create a new vertex group to store only our border verts
        oMeshO.vertex_groups.active_index = oVertGroup_Border.index
        bpy.ops.object.vertex_group_assign()
     
        #=== With the border verts finally in a vertex group our deletion / insertion of verts along the edge behaves a lot more intuitively without us having to manually insert verts in arrays and such (very useful!) ===
        #=== Even with the removal of tiny sliver polys with default UVs gone, there remains several degenerate polys with all verts on the border!  Leaving these would mess up the borders so a simple deletion is appropriate ===
        aVertsBorder = [oVert for oVert in bm.verts if oVert.select]     ###LEARN: vertex_group_assign invalidates any previous BMVert pointer we have!  Have to rebuild from selected!!
        aFacesToDelete = []
        for oVert in aVertsBorder:
            for oFace in oVert.link_faces:        # Iterate through the faces of this border vert to delete those with very high angles
                bAllFaceVertsOnBorder = True
                for oLoop in oFace.loops:
                    if oLoop.vert.select == False:
                        bAllFaceVertsOnBorder = False
                        break
                if bAllFaceVertsOnBorder:
                    #print("Face %5d has all verts on border!" % (oFace.index))
                    aFacesToDelete.append(oFace)            ###WEAK: Does add all polys three times in this array but delete below takes it without complaining...
     
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        for oFace in aFacesToDelete:
            oFace.select_set(True)
        bpy.ops.mesh.delete(type='FACE')            # As the selected faces are so small and MUST be right on the border, a simple deletion won't punch holes in the cloth ###CHECK!
 
    #     #=== Remove the worse of the vertex doubles on the border to help face operation below... A little bit destructive to UVs so only a small amount! ===
    #     aVertsBorder = [oVert for oVert in bm.verts if oVert.select]        ###LEARN: Disabled as our vert inserter / remover code below does this well without UV damage!
    #     bmesh.ops.remove_doubles(bm, verts=aVertsBorder, dist=0.003)                
     
        #=== Iterate through the edges connected to border vertices, and for those that have one vert on border and one vert in-cloth, select those that are too short for further merging ===
        print("== Finding adjacent verts to border that are too close ==") 
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.object.vertex_group_select()
        aVertsBorder = [oVert for oVert in bm.verts if oVert.select]     ###LEARN: vertex_group_assign invalidates any previous BMVert pointer we have!  Have to rebuild from selected!!
        aVertsInClothToDissolve = []
        for oVertBorder in aVertsBorder:
            for oEdgeBorder in oVertBorder.link_edges:
                oVertInCloth = oEdgeBorder.other_vert(oVertBorder)
                if oEdgeBorder.is_boundary == False:
                    nEdgeLen = oEdgeBorder.calc_length()
                    if nEdgeLen < 0.007:              ###TUNE ###IMPROVE: Parameter!!        ###CHECK: Careful with face!  Visualize what it does as if too many faces accross a circular area we get faces around the border!!
                        #print("Near-Border Edge Merge=%5d  Len=%6.4f" % (oEdgeBorder.index, nEdgeLen))
                        aVertsInClothToDissolve.append(oVertInCloth)
     
        #=== Iterate through the verts that are candidates for dissolve to only dissolve those that are not on seams ===    
        bpy.ops.mesh.select_all(action='DESELECT') 
        for oVertInClothToDissolve in aVertsInClothToDissolve:
            bVertOnSeam = False
            for oEdge in oVertInClothToDissolve.link_edges:
                if oEdge.seam:
                    bVertOnSeam = True
                    break
            if bVertOnSeam == False:
                oVertInClothToDissolve.select_set(True)
        bpy.ops.mesh.dissolve_verts()                           ###LEARN: Extremely useful method of removing a superflous vert without damaging UV that is far less risky then making faces out of (potentially large amount) of face contiguity
        bpy.ops.mesh.select_all(action='SELECT')                ###WEAK ###OPT Could select only around border area for re-tesselation... is this much slower for whole mesh??
        bpy.ops.mesh.quads_convert_to_tris()     ###REVIVE: use_beauty=true # Re-tesselate with beauty to really clean up the geometry around the border. With the above call this yields a substantial improvement
     
        #=== With the key re-face operation complete, tag the border verts on seams to prevent UV collapse during the upcoming collapse / subdivide algorithm ===
        bpy.ops.mesh.select_all(action='DESELECT') 
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.object.vertex_group_select()
        for oVertBorder in bm.verts:
            oVertBorder.tag = False
            if oVertBorder.select:
                for oEdge in oVertBorder.link_edges:
                    if oEdge.seam:
                        oVertBorder.tag = True                  ###WEAK? We set tag but never unset... can damage some other part of some algorithm later??
                        break
         
        #=== With the edge faces much cleaner, now iterate through the edges to subdivide the edges that are too long ===
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        for nEdgeSubDivideIteration in range(3):            ###IMPROVE ###CHECK: This half-baked hack of dividing / merging border edges would not have to be if only loop tool's relax could update UVs!!
            bpy.ops.mesh.select_all(action='DESELECT') 
            bpy.ops.object.vertex_group_select()                            ###LEARN: Relying on vert group to automatically update the selection as we insert / remove elements is a real lifesaver!!  (No need to manually insert/remove into arrays as we modify topology!)
            aEdgesBorder = [oEdge for oEdge in bm.edges if oEdge.select] 
            nLenEdgeAvg = 0.0
            nLenEdgeMin =  sys.float_info.max
            nLenEdgeMax = -sys.float_info.max          ###LEARN: float_info.min is essentially zero!
            for oEdge in aEdgesBorder:
                nLenEdge = oEdge.calc_length()
                nLenEdgeAvg = nLenEdgeAvg + nLenEdge
                if nLenEdgeMin > nLenEdge: nLenEdgeMin = nLenEdge
                if nLenEdgeMax < nLenEdge: nLenEdgeMax = nLenEdge
            nLenEdgeAvg /= len(aEdgesBorder)
            nLenEdgeCutoffMax = (nLenEdgeAvg + (nEdgeSubDivideIteration+3)*nLenEdgeMax) / (nEdgeSubDivideIteration+4)      ###TUNE: Currently subdividing edges that are ratio of the way between average and max... ###IMPROVE: Calc standard deviation would be more meaningful!
            #nLenEdgeCutoffMin = (nLenEdgeAvg + (nEdgeSubDivideIteration+6)*nLenEdgeMin) / (nEdgeSubDivideIteration+7)
            nLenEdgeCutoffMin = (nLenEdgeAvg * 0.66)
            #print("\n== Edge refine {} calculated avg edge len={:6.4f}  min={:6.4f}  max={:6.4f}  cutmin={:6.4f}  cutmax={:6.4f}".format(nEdgeSubDivideIteration , nLenEdgeAvg, nLenEdgeMin, nLenEdgeMax, nLenEdgeCutoffMin, nLenEdgeCutoffMax))  
         
            #=== Now that lenghts stats about the border edges has been collected, subdivide those that are on the longer side ===
            aEdgesToSplit = []
            aEdgesToMerge = []
            for oEdge in aEdgesBorder:
                nLenEdge = oEdge.calc_length()
                if nLenEdge > nLenEdgeCutoffMax:
                    #print("+ Subdividing edge {:5d} with length {:6.4f}".format(oEdge.index, nLenEdge))
                    aEdgesToSplit.append(oEdge)
                if nLenEdge < nLenEdgeCutoffMin:
                    if oEdge.verts[0].tag == False and oEdge.verts[1].tag == False:         # Avoid collapsing edges that have a seam vert (would damage UV)
                        #print("- Collapsing  edge {:5d} with length {:6.4f}".format(oEdge.index, nLenEdge))
                        aEdgesToMerge.append(oEdge)                 # We append edges to delete in this array so we can merge them all at once (deleting here would change topology of oMesh.edges requiring slow update call at every collapse
                     
            #=== Collapse and subdivide the edges found in previous loop.  Done separately for efficiency ===
            bmesh.ops.subdivide_edges(bm, edges=aEdgesToSplit, cuts=1, smooth=1.0)
            bmesh.ops.collapse(bm, edges=aEdgesToMerge)
             
        #=== Smooth the border's edge with Loop Tool's brilliant implementation of edge relax.  This implementation does NOT pull border verts toward in-cloth verts as is the only way we have to really clean border!
        print("== Border smoothing ===")           ###IMPROVE: Regular=True with lots of iterations really evens out border but messes up UV... an improvement would be to do it but then adjust UVs after!
        bmesh.update_edit_mesh(oMesh, tessface=True, destructive=True)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.object.vertex_group_select()
        Border.Border_Smooth()                                  ###WEAK: Can substantially push verts around and introduces slight damage along the border.  Adjusting the UVs as vertex are slid along the border would fix this (hopefully LoopTools author can fix his call for this!)
     
        #=== Re-tesselate the border ===                        ###CHECK: Needed here?
        print("== Final tesselation of border ==")
        bpy.ops.mesh.select_more()                              #Select one more of verts so we can tesselate the polys of the border
        bpy.ops.mesh.quads_convert_to_tris()        ###REVIVE: use_beauty=True
        bpy.ops.mesh.select_all(action='DESELECT')
         
        #=== At this point the border's UV has a few disjointed UVs.  Iterate through all border verts to weld the UVs ===
        print("== UV Weld ==")
        bpy.ops.object.vertex_group_select()                            ###LEARN: Above calls results in border selection with missing vertices (where they were inserted) but curiously these are in the vertex group!  So select the vertex group to easily obtain latest collection of border verts!
        aVertsBorder = [oVert for oVert in bm.verts if oVert.select] 
        for oVert in aVertsBorder:
            bVertHasSeam = False
            for oEdge in oVert.link_edges:          # Avoid collapsing UVs on verts connected to edges that are seams
                if oEdge.seam:
                    bVertHasSeam = True
                    break
            if bVertHasSeam == False:
                bmesh.ops.average_vert_facedata(bm, verts=[oVert])          ###LEARN: This is the call to merge UVs at a single vert
     
        #=== We're done smoothing and preparing the border.  Now store length information into our vertex group so that no matter how cloth is deformed during simulation we can recreate the border as originally designed ===
        #=== Obtain the collection of selected edges for iteration and clear the tag flag we need to use in next loop ===
        aVertsBorder = [oVert for oVert in bm.verts if oVert.select]
        for oVertBorder in aVertsBorder:            # First clear the tag flag of all border verts to indicate they haven't been traversed
            oVertBorder.tag = False
            for oEdge in oVertBorder.link_edges:    ###WEAK: Do we need to untag at end of function again??
                oEdge.tag = False                   # Previous code tagged the edges, seize the occasion to untag them
          
        #=== Iterate through the border's base edges to store the cumulative lenght in its associated vertex group ===
        print("== Storing border length information ==")
        oVertNow = aVertsBorder[0]                      ###IMPROVE: Choose vert from spacial positioning instead of this random occurence
        oVertFirst = oVertNow                           # Remember what vert we started so we know when to stop
        oLayVertGrps = bm.verts.layers.deform.active    ###LEARN: From technique at http://www.blender.org/documentation/blender_python_api_2_67_1/bmesh.html
        nLenBorderCumulative = 0.0
        while True:
            oVertNow[oLayVertGrps][oVertGroup_Border.index] = nLenBorderCumulative / G.C_BorderLenIntoVertGrpWeightRatio
            oVertNext = None         
            for oEdgeNow in oVertNow.link_edges:
                if oEdgeNow.select == True:                        ###IMPROVE: Would be better by check to is_boundary or is selected safer??
                    oVertOther = oEdgeNow.other_vert(oVertNow)
                    #=== Calculate the angle between the edge being considered and the cross vector between the vert normal and the edge tangent -> Used to always traverse the border in the direction of the cross vector as border UV application can only service that direction
                    vecVertNormal  = oVertNow.normal
                    vecEdgeTangent = oEdgeNow.calc_tangent(oEdgeNow.link_loops[0])      # Boundary edges only have one loop
                    vecCross = vecVertNormal.cross(vecEdgeTangent)
                    vecEdge = oVertOther.co - oVertNow.co
                    nAngleEdgeToCross = degrees(vecEdge.angle(vecCross))
                    if nAngleEdgeToCross < 90:                          # If the edge being considered is going in the opposite direction of the cross vector we ignore it as border UVs can only create seamless UV mapping going toward the cross vector
                        #print("- Vert {:5d} has angle {:8.4f}".format(oVertNow.index, nAngleEdgeToCross))          
                        oVertNext = oVertOther
                        break
            if oVertNext == None:
                raise Exception("###EXCEPTION: Cut_CleanupBorder() could not iterate through entire border loop while storing border length.")
             
             
            nEdgeLength = oEdgeNow.calc_length()
            #print("- BorderLen: Vert %6d of length %6.4f at %6.4f" % (oVertNow.index, nEdgeLength, nLenBorderCumulative))
            nLenBorderCumulative += nEdgeLength
            oVertNow = oVertNext
            oVertNow.tag = True
            if oVertNow == oVertFirst:          # If we're back at the starting vert, store the last (ie. maximum) lenght in start vert and exit
                #print("- BorderLen: Vert %6d at len %6.4f  (FIRST)" % (oVertNow.index, nLenBorderCumulative))
                oVertNow[oLayVertGrps][oVertGroup_Border.index] = nLenBorderCumulative / G.C_BorderLenIntoVertGrpWeightRatio
                break
     
        #=== Cleanup and return mesh to edit mode ===
        print("----- Cut_CleanupBorder() finishes on border '{}' for mesh '{}' -----".format(sCutName, oMeshO.name))
        bpy.ops.mesh.select_all(action='DESELECT')
        bmesh.update_edit_mesh(oMesh, tessface=True, destructive=True)


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    TOP-LEVEL CLIENT-SIDE CUT REQUESTS
#---------------------------------------------------------------------------    

def gBL_ClothCut_ApplyCut(sNameBody, sNameCurve, nCenterX, nCenterY, nCenterZ):     # Client-side wrapup of Cut_ApplyCut() that apples the given cutter to a virgin new cloth mesh copied from source
    oMeshClothCutO = DuplicateAsSingleton(sNameBody + G.C_NameSuffix_ClothBase, sNameBody + G.C_NameSuffix_ClothCut, G.C_NodeFolder_Game, True)   # Copy the base mesh to reset the cut to start
    oCurveO = bpy.data.objects[sNameCurve]
    aBorderLocatorVertPos = {}
    vecCurveCenterClient = Vector((nCenterX, nCenterY, nCenterZ))
    vecCurveCenter = G.VectorU2B(vecCurveCenterClient)
    Cut_ApplyCut(oMeshClothCutO, oCurveO, vecCurveCenter, aBorderLocatorVertPos)
    Client.Client_ConvertMeshForUnity(oMeshClothCutO, True)                           # Mesh has changed topology, update its state for Client  ###CHECK!!!! Expensive complex call???  Do all of that???
    return G.DumpStr("OK: gBL_Cut_ApplyCut(ClothCut = '[]'  Curve='{}')".format(oMeshClothCutO.name, sNameCurve))

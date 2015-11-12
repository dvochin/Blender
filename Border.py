import bpy
import sys
import bmesh
from math import *
from mathutils import *

import gBlender
import G

G.C_BorderLenIntoVertGrpWeightRatio = 10.0        # Real-world distances are divided by this ratio to store border distances into vert groups for border-lenght storage

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BORDER - GENERATION
#---------------------------------------------------------------------------    

def Border_CreateAll(oMeshO, nBorderWidth, nBorderHeight, nBorderRound, nTargetTextureWidth):
    #=== Test creation of borders ===
    print("\n\n\n===== Border_CreateAll() BEGIN =====")
    oCurves = bpy.data.objects[G.C_NodeName_Curve]
    for oCurveO in oCurves.children:
        if oCurveO.hide_render: continue                    ###TEMP ###CHECK: Keep this (useful) technique to disable objects without changing parent??
        Border_Create(oMeshO, oCurveO, nBorderWidth, nBorderHeight, nBorderRound, nTargetTextureWidth)
    bpy.context.scene.update()
    print("\n----- Border_CreateAll() END -----")



def Border_Create(oMeshO, oCurveO, nBorderWidth, nBorderHeight, nBorderRound, nTargetTextureWidth):
    oMesh = oMeshO.data
    bSymmetryX = oCurveO.get('SymmetryX', False)  # The symmetry cutters (e.g. arms and legs) have this set to two so next big loop runs twice for each side
    nSymmetryIterations = bSymmetryX + 1
    G.C_MatBorder = 1

    for nSymmetryRun in range(nSymmetryIterations):
        sCutName = oCurveO.name
        if nSymmetryIterations > 1:                                 # The name of the cut is suffixed only for symmetrical cuts (e.g. ArmL and ArmR)
            sCutName += C_SymmetrySuffixNames[nSymmetryRun]
        print("\n=== Border_Create() Generating cloth border '{}' for mesh '{}' ===".format(sCutName, oMeshO.name))
    
        oVertGroup_Border = gBlender.Util_SelectVertGroupVerts(oMeshO, G.C_VertGrp_Border + sCutName)
        Border_Smooth()                                     # This mesh comes straight from cloth simulation.  Perform heavy smoothing of the border so that extrusions are not all over the place...
    
        #=== Extrude the border's edge without moving it and remove these new verts from the border vertex group ===    
        bpy.ops.mesh.extrude_edges_indiv()                  ###LEARN: This is the function we need to really extrude!
        bpy.ops.object.vertex_group_remove_from()           # Extrude operation above created a new ring of verts and leaves them as the only selection but added them to the border vertex group.  We remove them so the border group retains only the original (base) verts
        
        #=== Create a temporary new vertex group to store the new ring of vertices for the border extrusion ===
        bpy.ops.object.mode_set(mode='OBJECT')
        oVertGroup_TempBorderExtruded = oMeshO.vertex_groups.new(name="TempBorderExtrude")        # We add a vertex group to store the newly-created extruded verts...
        aVertsSel = [oVert.index for oVert in oMesh.vertices if oVert.select]
        oVertGroup_TempBorderExtruded.add(index=aVertsSel, weight=1.0, type='REPLACE')
        bpy.ops.object.mode_set(mode='EDIT')
    
        #=== Go back to the base border verts and shrink/fatten them in order to give the extruded verts a correct normal we can work with ===
        bpy.ops.mesh.select_all(action='DESELECT')
        oMeshO.vertex_groups.active_index = oVertGroup_Border.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.transform.shrink_fatten(value=-0.000001)        ###LEARN: We move the base border a tiny amount in order for normals of extruded ring to have some area to work with.  (Note that setting this even smaller doesn't work!)
        bpy.ops.mesh.normals_make_consistent(inside=False)      ###LEARN: For the shrink_fatten call above to affect the normals of the new ring we must refresh the normals with this call
        ###LEARN: Extremely weird (but useful) behavior occurs when you extrude a ring of verts but shrink/flatten the preceding (original) ring along its normals -> the normals of the outermost (extruded) ring point alongside the TANGENT of the original verts!
        ### This is useful / needed as when you extrude a ring of edges as the normals and tangents of the outermost edge ring are zero (Blender shows them pointing toward a weird and unrelated (but consistent) way
    
        #=== Now that the extruded rings has normals (that are actually tangents of base ring!!), shrink/fatten it to push the new extruded ring away from the cloth to generate the first (flat) part of the border)
        bpy.ops.mesh.select_all(action='DESELECT')
        oMeshO.vertex_groups.active_index = oVertGroup_TempBorderExtruded.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.transform.shrink_fatten(value=-nBorderWidth)
    
        #=== Now that the base (flat) part of the border has been created, extrude the polys between the two border rings to give the border 'depth' ===
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')        # We go to face mode and expand the verts selected.  This will select all faces that have at least one vert selected...
        bpy.ops.mesh.extrude_region()                  ###LEARN: This is the function we need to really extrude!
        oMeshO.vertex_groups.active_index = oVertGroup_Border.index       # Extrude operation above inserted additional verts into the border vertex group.  Remove these to keep border vertgroup intact!!
        bpy.ops.object.vertex_group_remove_from()                
        bpy.ops.transform.shrink_fatten(value=-nBorderHeight)
        bpy.ops.mesh.normals_make_consistent(inside=False)      # Again we need to recalc the normals for the edge shrink/fatten that follows!
    
        #=== Switch to edge mode (with only the new 'depth' polys selected) to shrink/fatten them along their normal to pull the edges of the border toward the border's core so as to bevel the edges to prevent a totally square look ===
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')        # We go to face mode and expand the verts selected.  This will select all faces that have at least one vert selected...
        bpy.ops.transform.shrink_fatten(value=nBorderRound)
        
        #=== Go back to face with expand on (so we also select the polys at the edge of the border to set a border material and process UVs 
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')        # We go to face mode and expand the verts selected.  This will select all faces that have at least one vert selected...
        oMeshO.active_material_index = G.C_MatBorder      ###WEAK: Assume body suit has 2 materials setup... ###CHECK!
        bpy.ops.object.material_slot_assign()
    
        
        #===== With the border fully created now iterate through the border's polygons and set their UVs =====
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')        # Go to edge mode as we need to select border base edge and iterate through its ring
        bpy.ops.object.vertex_group_select()
        bm = bmesh.from_edit_mesh(oMesh)
        oLayVertGrps = bm.verts.layers.deform.active
        oLayUV = bm.loops.layers.uv.active
        aVertsBorder = [oVert for oVert in bm.verts if oVert.select]
        for oVertBorder in aVertsBorder:            # First clear the tag flag of all border verts to indicate they haven't been traversed
            oVertBorder.tag = False
        
        #=== Iterate through the border vertices to find the vert with min distance and max distance ===
        nDistMin =  sys.float_info.max
        nDistMax = -sys.float_info.max          ###LEARN: float_info.min is essentially zero!
        for oVert in aVertsBorder:
            nDist = oVert[oLayVertGrps][oVertGroup_Border.index]
            if nDistMin > nDist:
                nDistMin = nDist
                oVertMin = oVert
            if nDistMax < nDist:
                nDistMax = nDist
                oVertMax = oVert
        oVertNow = oVertMax                 # We start border iteration from the vert with max border lenght = vert with zero border lenght = vert at begin/end of cycle   ###DESIGN!!! What about non-cyclic borders??
        nDistVertNow = 0                    # oVertNow == oVertMax should have max distance but (as it is also distance zero) we manually set it at begin of loop at zero so loop can correctly select the 2nd vert on border with the 2nd lowest stored border length
    
        #=== Prepare for UV set by scaling the U distances ===
        nSumU = nBorderHeight+nBorderWidth+nBorderHeight
        nRatioBorderUV = nTargetTextureWidth / nSumU                           # We multiply all blender distances for the border by this ratio (for both U and V)
        aFaceStartU = [0, nRatioBorderUV*(nBorderHeight), nRatioBorderUV*(nBorderHeight+nBorderWidth), nTargetTextureWidth]      # Additional 'u' given to each face as we progress from border base to border extremity
        print("== Border_Create() creates border for '%s' of length %6.4f" % (sCutName, nDistMax))
    
        #=== Iterate through the border edges to populate UVs for all polygons created for the border addition ===
        while True:                         # We break right after test fails for next border vert
            #=== Iterate through the edges of this vert to find another vert on border (selected) with a 'stored border lenght' value HIGHER than ours.
            oVertNext = None
            for oEdgeNow in oVertNow.link_edges:
                if oEdgeNow.select == True:
                    oVertSearch = oEdgeNow.other_vert(oVertNow)
                    nDistVertNext = oVertSearch[oLayVertGrps][oVertGroup_Border.index]    # Fetch the pre-calculated cumulative border distance for both verts (stored in vert group as 'weight') ===
                    nDistDelta = nDistVertNext - nDistVertNow
                    if nDistDelta >= 0.5 * nDistMax:    # To handle special cases at loop begining, prevent the first iterations from going to verts that have higher border length but are actually at the other end of the cycle (with very high border lenghts) 
                        continue
                    if nDistVertNext > nDistVertNow:
                        oVertNext = oVertSearch         # We found the next vert with higher border length.  Set it and exit loop (notice that 'oEdgeNow' was correctly set to the edge between 'now' and 'next')
                        break
    
            #=== We exit the loop here if no valid next vert (Done this way because most of the loop requires the border lenght of the 'next' vert) ===
            if oVertNext == None:
                break
        
            #=== Find the loop of this edge attached to a poly that is on the border addition ===
            #print("- Vert %6d -> %6d at dist %6.4f -> %6.4f = %6.4f" % (oVertNow.index, oVertNext.index, nDistVertNow, nDistVertNext, nDistVertNext-nDistVertNow))
            for oLoopFind in oEdgeNow.link_loops:                       # Iterate through loops of this edge to find the 'border base' polygon. (e.g. first poly ring of border addition with edge connected to cloth           
                if (oLoopFind.face.material_index == G.C_MatBorder):      # The border base now has polys on the cloth side and polys on the border addition side, go toward the border which now has well-defined material ID
                    oLoopEdgeRung = oLoopFind
                    break
    
            #=== As we move from base edge toward extremity, all loops of the quads on this 'rung' get their 'v' information from either verts of our current edge ===
            aBaseVertV = []                 ###WEAK: We have to invert these as we're now iterating in reverse... fix that so we can clean up here!!
            if oVertNow == oVertMax:               # If we're the first rung (ie: we're the max lenght / zero length 'start/end cycle vertex') our actual vertex contains the max value (when we wrap around).  But for first rung we override to zero here               
                aBaseVertV.append(0)                
            else:
                aBaseVertV.append(nDistVertNow)             # The first vert with v information is the actual vert associated with our rung edge & loop.  It will service quad loops 0 & 1
            aBaseVertV.append(nDistVertNext)     # The second vert with v information is the next vert on our rung.  It will service quad loops 2 & 3
    
            #=== Iterate from the base (attached to cloth) of this 'rung' of border toward the extremity (boundary edge) along the 'u' direction to set the uvs of all polygons on this 'rung' of the border ===
            oLoopIterRung = oLoopEdgeRung
            nFaceIndexSinceBase = 0                       
            while oLoopIterRung.edge.is_boundary == False:                  # The moment our loop going from base to extremity hits a boundary edge we've traversed all the poly of this 'rung'
                oFace = oLoopIterRung.face                                  # With the 'base poly' we can now push toward the extremity of the border in the 'u' direction
                oFace.select = True
                aLoopIterInFace = oLoopIterRung 
                for nFaceVert in range(4):
                    nFaceVertRot = (nFaceVert + 1) % 4                      ###WEAK: Currently seamless and perfect BUT text appears upside down!!
                    if (nFaceVertRot >= 1 and nFaceVertRot <= 2):
                        nBorderU = aFaceStartU[nFaceIndexSinceBase]
                    else:
                        nBorderU = aFaceStartU[nFaceIndexSinceBase+1]
                    nBorderV = -nRatioBorderUV * G.C_BorderLenIntoVertGrpWeightRatio * aBaseVertV[int(nFaceVertRot/2)]    # The 'v' information of all polys on this rung comes from the 'border base vert' stored in aBaseVertV above.  (First vert services loop 0 & 1, second vert loop 2 & 3)
                    aLoopIterInFace[oLayUV].uv = Vector((nBorderU, nBorderV))
                    aLoopIterInFace = aLoopIterInFace.link_loop_next        # Go to the next loop in this quad (circular fashion)
                
                oLoopIterRung = oLoopIterRung.link_loop_next.link_loop_next  # Every poly here is a quad so we can select the 'other side' of this quad by iterating twice over this poly's loops
                oLoopIterRung = oLoopIterRung.link_loop_radial_next     # Switch to the other face connected to this loop/edge.  This is going toward border addition's extremity
                nFaceIndexSinceBase += 1
    
            #=== For next loop iteration set 'now' to 'next' for both the vertex and the lenght of next vert we fetched earlier    
            oVertNow = oVertNext
            nDistVertNow = nDistVertNext 
        
        #=== Remove the vert group created and exit bmesh ===    
        oMeshO.vertex_groups.active_index = oVertGroup_TempBorderExtruded.index
        bpy.ops.object.vertex_group_remove()            # We don't need the temporary vertex group anymore so remove it
        bmesh.update_edit_mesh(oMesh, tessface=True, destructive=True)

        #=== Select the edges at the base border and mark them as sharp.  This will be used to actually split the border geometry before sending to Client so both sides of border get their own normal ===
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_all(action='DESELECT')
        oMeshO.vertex_groups.active_index = oVertGroup_Border.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.mark_sharp()

        #=== Deselect everything, return to vert mode and exit edit mode ===
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BORDER - UTILITY
#---------------------------------------------------------------------------    

def Border_Smooth():
    #=== Smooth the border's edge with Loop Tool's brilliant implementation of edge relax.  This implementation does NOT pull border verts toward in-cloth verts as is the only way we have to really clean border!
    print("== Smoothing & evening out border ===")                  ###CHECK: Do we smooth BOTH in prepare and do?
    bpy.ops.mesh.looptools_relax(interpolation='cubic',  regular=True, iterations='10')     # Run a heavy cubic followed by a light linear to nicely smooth out border that has just come from cloth simulation      
    bpy.ops.mesh.looptools_relax(interpolation='linear', regular=True, iterations='1')      ###TUNE: Very important call to stabilize border after cloth sim... test!!! 
    ###BUG!: looptools_relax seems to have a problem by compressing one vert of a loop (and expanding a few around)!  What to do??
    ###PROBLEM: Regular=True is soooo nice to have to get regularly spaced border addition but it does mess up the UVs.  Still, perfectly-spaced border root is very important and for now we're tolerating a bit of UV corruption near borders...
    ###BUG: Blender seems to crash often with above call??? 

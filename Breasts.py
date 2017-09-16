import bpy
import sys
import bmesh
import array
import CBody
from math import *
from mathutils import *

from gBlender import *
import G
import Client



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BREAST MORPHING
#---------------------------------------------------------------------------    


def BodyInit_CreateCutoffBreastFromSourceBody(sNameBodySrc):      
    "Separates the left-breast from source mesh and create the important 'blend group' to protect breast border during morph operations as well as the mapping between breast verts to body verts for left&right breasts"

    return          ###BROKEN: New body and focus on blending

    
    ####IMPROVE: One of the 'prepare functions' that only needs to run when source body changes
    sNameBreast = sNameBodySrc + G.C_NameSuffix_Breast
    DeleteObject(sNameBreast)
    #DataLayer_RemoveLayers(oMeshBodyO.name)           # Remove previous custom data layers just to make sure we refer to the right one  ####CHECK!  Can delete something we need???
    
    oMeshBodyO = SelectObject(sNameBodySrc)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

    #=== Create a new data layer to store (before we separate) the original vertex ID (in body) as well as the vertex ID of the corresponding vert in the right breasts ===
    bmBody = bmesh.from_edit_mesh(oMeshBodyO.data)
    oLayBodyVerts = bmBody.verts.layers.int.new(G.C_DataLayer_SourceBreastVerts)      # Each integer in this data layer will store the vertex ID of the left breast in low 16-bits and vert ID of right breast in high 16-bit  ###INFO: Creating this kills our bmesh references!
    bmBody.verts.index_update()

    #=== Capture the vertex sets of both left and right breasts in arrays ===
    oVertGrp_BreastR = oMeshBodyO.vertex_groups["_Detach_BreastR"]              ###CHECK: Was 'Area'
    oMeshBodyO.vertex_groups.active_index = oVertGrp_BreastR.index
    bpy.ops.object.vertex_group_select()
    aVertsBreastR = [oVert for oVert in bmBody.verts if oVert.select]
    bpy.ops.mesh.select_all(action='DESELECT')

    oVertGrp_BreastL = oMeshBodyO.vertex_groups["_Detach_BreastL"]
    oMeshBodyO.vertex_groups.active_index = oVertGrp_BreastL.index
    bpy.ops.object.vertex_group_select()
    aVertsBreastL = [oVert for oVert in bmBody.verts if oVert.select]

    #=== Find the closest vert to every vert in aVerts1 in aVerts2.  Assumes mesh is *mathematically symmetrical*! ===
    aVertsMirrorX = Util_FindClosestMirrorVertInGroups(bmBody, aVertsBreastL, aVertsBreastR)       
    bmBody.verts.index_update()

    #=== Iterate through the left breast vertices to store the original vertex IDs of the corresponding left & right vertices before we separate ===    
    for oVertBreastL in aVertsBreastL:
        oVertBreastL[oLayBodyVerts] = aVertsMirrorX.pop(0).index << 16 | oVertBreastL.index    # Original vert ID of left in low 16 bits, mirror right side vert in high 16-bits
        
    #=== Duplicate and separate the left breast to its own mesh... the custom data layer containing vertex IDs in the original mesh follows ===
    bpy.ops.mesh.duplicate()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.mesh.select_all(action='DESELECT')

    #=== Access the newly separated breast mesh and give it a name ===
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.object.select = False                       # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
    bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
    oMeshBreastO = bpy.context.object 
    oMeshBreastO.name = oMeshBreastO.data.name = sNameBreast
    oMeshBreastO.name = oMeshBreastO.data.name = sNameBreast           ###INFO: Do twice to make absolutely sure name 'takes'  (e.g. other mesh of same name given other name)

    #=== Enter bmesh edit mode on the breast and obtain array of edge verts ===
    bpy.ops.object.mode_set(mode='EDIT')
    aMapDistToEdges, nDistMax_AllInnerVerts = Util_GetMapDistToEdges() 
    bpy.ops.mesh.select_all(action='DESELECT')
    bmBreast = bmesh.from_edit_mesh(oMeshBreastO.data)
#     bpy.ops.mesh.select_non_manifold()
#     aVertsEdge = [oVert for oVert in bmBreast.verts if oVert.select]
#     bpy.ops.mesh.select_all(action='DESELECT')
#     
#     #=== Iterate through all breast verts then to all edge verts to find the minimum distance of all inner verts to the closest edge vert ===
#     nDistMax_AllInnerVerts = -sys.float_info.max
#     aMapDistToEdges = {}
#     for oVertBreastL in bmBreast.verts:
#         nDistMin = sys.float_info.max
#         for oVertEdge in aVertsEdge:
#             vecDiff = oVertEdge.co - oVertBreastL.co
#             nDist = vecDiff.magnitude
#             if (nDistMin > nDist):
#                 nDistMin = nDist
#         aMapDistToEdges[oVertBreastL.index] = nDistMin
#         if nDistMax_AllInnerVerts < nDistMin:
#             nDistMax_AllInnerVerts = nDistMin
#         print("Vert {:5d} = dist {:6.4f}".format(oVertBreastL.index, nDistMin))
#     print("\n-- Calculated breast distance array with max dist %f" % (nDistMax_AllInnerVerts))

    #===== Calculate the distance between breast verts and the nipple vert =====
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    oVertGrp_NippleL = oMeshBreastO.vertex_groups[G.C_VertGrp_Morph + "Nipple"]
    oMeshBreastO.vertex_groups.active_index = oVertGrp_NippleL.index
    bpy.ops.object.vertex_group_select()
    aVertNippleL = [oVertBreastL for oVertBreastL in bmBreast.verts if oVertBreastL.select]
    if len(aVertNippleL) > 1:
        raise Exception("###EXCEPTION: BodyInit_CreateCutoffBreastFromSourceBody(): Too many verts for nipple!")      ###PROBLEM?: Weird bug when generating bodies is some of our vert groups get more verts!  WTF???
    #print("=== Nipple Vert = ", aVertNippleL)
    aMapDistToNipples, aDistToNippleMax = Util_CalcSurfDistanceBetweenTwoVertGroups(bmBreast, bmBreast.verts, aVertNippleL)

    #=== Remove all vertex groups except those related to breast morphing or collider sub-mesh ===
    for oVertGrp in oMeshBreastO.vertex_groups:
        if (oVertGrp.name.startswith(G.C_VertGrp_Morph) == False) and (oVertGrp.name != "_Area_BreastColL"):
            oMeshBreastO.vertex_groups.remove(oVertGrp)

    ####OBS: Breast collider no longer updated in-mesh... Now part of the new SlaveMesh_XXX functionality that 'glues' a mesh to the source body being morphed
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
#         oVert.co.x += 1.0
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###INFO: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
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
#         nVertClosest, nDistMin, vecVertClosest = Util_FindClosestVert(oMeshBreastO, vecVert, .000001)
#         aMapBreastVertToColVerts_Cldr  .append(nVertCldr)
#         aMapBreastVertToColVerts_Breast.append(nVertClosest)
#         print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %6.4f" % (nVertCldr, nVertClosest, vecVert.x, vecVert.y, vecVert.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
#         #oVert.co = vecVertClosest                               # Set the collider vert exactly on the breast vert
# 
#     #=== Return the collider verts to their original positions ===
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         oVert.co.x -= 1.0
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###INFO: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oMeshBreastO["aMapBreastVertToColVerts_Cldr"]   = aMapBreastVertToColVerts_Cldr     # Store our map into breast mesh so ApplyOp can copy breast vert positions to each associated collider vert 
#     oMeshBreastO["aMapBreastVertToColVerts_Breast"] = aMapBreastVertToColVerts_Breast 
    


    #===== Create the 'blended group' that calculate a blended value from 0..1 for each breast vert based on how close/far it is to nipple and breast edge =====
    if G.C_VertGrp_Area_BreastMorph in oMeshBreastO.vertex_groups:
        oGrp = oMeshBreastO.vertex_groups[G.C_VertGrp_Area_BreastMorph]
    else:
        oGrp = oMeshBreastO.vertex_groups.new(name=G.C_VertGrp_Area_BreastMorph)
    bpy.ops.object.mode_set(mode='OBJECT')              # Adding verts to vert group (unfortunately) requires object mode

    for oVertBreast in oMeshBreastO.data.vertices:                 # Iterate through all verts of the mesh to store their distance to the requested vert
        nVertBreast = oVertBreast.index
        nDistToEdge = aMapDistToEdges[nVertBreast] / .07           ###TUNE: In code values from observing stats -> Change code to act in occording with stats!
        if (nDistToEdge > 1):
            nDistToEdge = 1
        nDistToEdge = sin(nDistToEdge*pi/2)          # sin from 0 to pi/2 gives smooth curve from 0 to 1
        nWeight = 1 - (aMapDistToNipples[nVertBreast] / aDistToNippleMax)       ###TUNE: This curve and mechanism to blend dist to nipple and dist to edge!
        nWeight = nWeight * nDistToEdge
        oGrp.add([nVertBreast], nWeight, 'REPLACE')
        #print("-VertGroup vert {:4d} DistNipple {:7.4f} DistEdge {:7.4f} = {:7.4f}".format(nVertBreast, aMapDistToNipples[nVertBreast], aMapDistToEdges[nVertBreast], nWeight))


    #===== Test the mapping between breast verts to body verts... as they just got separated without breast moving, coordinates should still match ===    
    #=== Obtain custom data layer containing the vertIDs of our breast verts into body ===
    bpy.ops.object.mode_set(mode='EDIT')
    bmBreast = bmesh.from_edit_mesh(oMeshBreastO.data)
    oLayBodyVerts = bmBreast.verts.layers.int[G.C_DataLayer_SourceBreastVerts]      # Each integer in this data layer will store the vertex ID of the left breast in low 16-bits and vert ID of right breast in high 16-bit  ###INFO: Creating this kills our bmesh references!
    bmBreast.verts.index_update()

    #=== Iterate through the breast verts, extract the source verts from body from custom data layer, and set the corresponding verts in body ===    
    aVertsBody = oMeshBodyO.data.vertices
    for oVertBreast in bmBreast.verts:
        nVertsEncoded = oVertBreast[oLayBodyVerts] 
        nVertBodyBreastL = (nVertsEncoded & 65535)  
        #nVertBodyBreastR = nVertsEncoded >> 16
        vecVertBreast = oVertBreast.co.copy()
        vecVertBody   = aVertsBody[nVertBodyBreastL].co
        if (vecVertBreast != vecVertBody):
            print("ERROR in breast vertex remapping!  {:5d} != {:5d}".format(oVertBreast.index, nVertBodyBreastL))      ####PROBLEM: Collider verts not matching??  Because of left / right???
    bpy.ops.object.mode_set(mode='OBJECT')
    
    DataLayer_RemoveLayerInt(sNameBodySrc, G.C_DataLayer_SourceBreastVerts)      # Remove the temporary data layer from source body (no longer needed after breast mesh split)

    Util_HideMesh(oMeshBreastO)

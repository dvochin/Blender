import bpy
import sys
import bmesh
import array
import CBody
from math import *
from mathutils import *

import gBlender
import G
import Client



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BREAST MORPHING
#---------------------------------------------------------------------------    


def BodyInit_CreateCutoffBreastFromSourceBody(sNameBodySrc):      
    "Separates the left-breast from source mesh and create the important 'blend group' to protect breast border during morph operations as well as the mapping between breast verts to body verts for left&right breasts"
    
    ####IMPROVE: One of the 'prepare functions' that only needs to run when source body changes
    sNameBreast = sNameBodySrc + G.C_NameSuffix_Breast
    gBlender.DeleteObject(sNameBreast)
    #gBlender.DataLayer_RemoveLayers(oMeshBodyO.name)           # Remove previous custom data layers just to make sure we refer to the right one  ####CHECK!  Can delete something we need???
    
    oMeshBodyO = gBlender.SelectAndActivate(sNameBodySrc)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

    #=== Create a new data layer to store (before we separate) the original vertex ID (in body) as well as the vertex ID of the corresponding vert in the right breasts ===
    bmBody = bmesh.from_edit_mesh(oMeshBodyO.data)
    oLayBodyVerts = bmBody.verts.layers.int.new(G.C_DataLayer_SourceBreastVerts)      # Each integer in this data layer will store the vertex ID of the left breast in low 16-bits and vert ID of right breast in high 16-bit  ###LEARN: Creating this kills our bmesh references!
    bmBody.verts.index_update()

    #=== Capture the vertex sets of both left and right breasts in arrays ===
    oVertGrp_BreastR = oMeshBodyO.vertex_groups["_Area_BreastR"]
    oMeshBodyO.vertex_groups.active_index = oVertGrp_BreastR.index
    bpy.ops.object.vertex_group_select()
    aVertsBreastR = [oVert for oVert in bmBody.verts if oVert.select]
    bpy.ops.mesh.select_all(action='DESELECT')

    oVertGrp_BreastL = oMeshBodyO.vertex_groups["_Area_BreastL"]
    oMeshBodyO.vertex_groups.active_index = oVertGrp_BreastL.index
    bpy.ops.object.vertex_group_select()
    aVertsBreastL = [oVert for oVert in bmBody.verts if oVert.select]

    #=== Find the closest vert to every vert in aVerts1 in aVerts2.  Assumes mesh is *mathematically symmetrical*! ===
    aVertsMirrorX = gBlender.Util_FindClosestMirrorVertInGroups(bmBody, aVertsBreastL, aVertsBreastR)       
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
    oMeshBreastO.name = oMeshBreastO.data.name = sNameBreast           ###LEARN: Do twice to make absolutely sure name 'takes'  (e.g. other mesh of same name given other name)

    #=== Enter bmesh edit mode on the breast and obtain array of edge verts ===
    bpy.ops.object.mode_set(mode='EDIT')
    aMapDistToEdges, nDistMax_AllInnerVerts = gBlender.Util_GetMapDistToEdges() 
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
        raise Exception("ERROR: BodyInit_CreateCutoffBreastFromSourceBody(): Too many verts for nipple!")      ###PROBLEM?: Weird bug when generating bodies is some of our vert groups get more verts!  WTF???
    #print("=== Nipple Vert = ", aVertNippleL)
    aMapDistToNipples, aDistToNippleMax = gBlender.Util_CalcSurfDistanceBetweenTwoVertGroups(bmBreast, bmBreast.verts, aVertNippleL)

    #=== Remove all vertex groups except those related to breast morphing or collider sub-mesh ===
    for oVertGrp in oMeshBreastO.vertex_groups:
        if (oVertGrp.name.startswith(G.C_VertGrp_Morph) == False) and (oVertGrp.name != "_Area_BreastColL"):
            oMeshBreastO.vertex_groups.remove(oVertGrp)


    ####OBS: Breast collider no longer updated in-mesh... Now part of the new PairMesh_XXX functionality that 'glues' a mesh to the source body being morphed
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
#         oVert.co.x += 1.0;
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###LEARN: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
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
#         nVertClosest, nDistMin, vecVertClosest = gBlender.Util_FindClosestVert(oMeshBreastO, vecVert, .000001)
#         aMapBreastVertToColVerts_Cldr  .append(nVertCldr)
#         aMapBreastVertToColVerts_Breast.append(nVertClosest)
#         print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %6.4f" % (nVertCldr, nVertClosest, vecVert.x, vecVert.y, vecVert.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
#         #oVert.co = vecVertClosest                               # Set the collider vert exactly on the breast vert
# 
#     #=== Return the collider verts to their original positions ===
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         oVert.co.x -= 1.0;
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###LEARN: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
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
    oLayBodyVerts = bmBreast.verts.layers.int[G.C_DataLayer_SourceBreastVerts]      # Each integer in this data layer will store the vertex ID of the left breast in low 16-bits and vert ID of right breast in high 16-bit  ###LEARN: Creating this kills our bmesh references!
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
    
    gBlender.DataLayer_RemoveLayerInt(sNameBodySrc, G.C_DataLayer_SourceBreastVerts)      # Remove the temporary data layer from source body (no longer needed after breast mesh split)






#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BREAST COLLIDERS
#---------------------------------------------------------------------------    

def CBodyColBreasts_GetColliderInfo(sNameBreastColMesh):       # Highly-specific function to CBodyColBreasts Unity class that extracts the collider source mesh superimposed on top of the detached softbody breast mesh and return arrays defining the collider source mesh for our runtime PhysX engine.
    # This PhysX mesh takes a small encoded (containing about 32 verts) mesh to generate sphere & capsule collidersX.  This call process which vert will create a sphere collider in PhysX and which edge will generate a capsule colliders (currently used to repell clothing away from breasts)  (Args ex: "BodyA", "WomanA", "Breasts")
    ###CHECK: Can capping during breast separation cause problem with collider overlay??

    oMeshBreastColO = gBlender.SelectAndActivate(sNameBreastColMesh)    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    ####OBS??? #=== Iterate through the verts to assemble the aVertSphereRadiusRatio array storing the red channel of the vertex color.  (This information stores the relative radius of each vertex sphere with a value of zero meaning no sphere) ===
    bm = bmesh.from_edit_mesh(oMeshBreastColO.data)
    oLayVertColors = bm.loops.layers.color.active        # Obtain reference to bmesh vertex color channel store in loops  ###LEARN: 2 defined 'Col' and 'Col.001' with 'Col.001' active and appearing to contain valid data... can this change?? ###CHECK
    nNumActiveVerts = 0
    aVertSphereRadiusRatio = array.array('H')            # This array stores a number from 0-255 to scale the sphere radius (kept in Unity only) used by this collider mesh.  (0 means no sphere created for that vertex)  A maximum of 32 spheres can be defined
    for oVert in bm.verts:
        nVertSphereRadiusRatio = oVert.link_loops[0][oLayVertColors][0]
        if nVertSphereRadiusRatio > 0.1:                         ###KEEP? Setting zero color can be tricky so some threshold??
            #print("CBodyColBreasts: SphereIndex # {:2} = Vert {:2} = Val: {:2}".format(nNumActiveVerts, oVert.index, nVertSphereRadiusRatio))
            nNumActiveVerts += 1
        else:
            nVertSphereRadiusRatio = 0                              # Non collider-related verts get zero strength so they don't generate a sphere collider
        aVertSphereRadiusRatio.append((int)(255 * nVertSphereRadiusRatio))       # The red vertex color channel (a float for 0 to 1) is multiplied by 255 and sent as a short
    if nNumActiveVerts > 32:
        raise Exception("ERROR: CBodyColBreasts_GetColliderInfo() found more than 32 active verts while scanning vertex colors on source collider mesh.  (PhysX cannot process more than 32 cloth-repeling vertices)")
    
    aCapsuleSpheres = array.array('H')                        # This array stores the two vertex IDs of each vertex / sphere that represends the end of each tapered capsule.  These are marked by 'sharp edges' for each capsule
    nNumCapsules = 0
    for oEdge in bm.edges:
        if (oEdge.smooth == False):
            aCapsuleSpheres.append(oEdge.verts[0].index) 
            aCapsuleSpheres.append(oEdge.verts[1].index)
            #print("CBodyColBreasts: Capsule {:2} found between {:2}-{:2}".format(nNumCapsules, oEdge.verts[0].index, oEdge.verts[1].index))
            nNumCapsules += 1
    if nNumCapsules > 32:
        raise Exception("ERROR: CBodyColBreasts_GetColliderInfo() found more than 32 capsules while scanning for sharp edges on source collider mesh.  (PhysX cannot process more than 32 cloth-repeling capsules)")

    bpy.ops.object.mode_set(mode='OBJECT')

    #=== Send the requested arrays to client ===
    print("CBodyColBreasts: Sending {} verts/spheres and {} edges/capsules.".format(len(oMeshBreastColO.data.vertices), nNumCapsules))
    oBA = bytearray()
    gBlender.Stream_SerializeArray(oBA, aVertSphereRadiusRatio.tobytes())
    gBlender.Stream_SerializeArray(oBA, aCapsuleSpheres.tobytes())
    oBA += Client.Stream_GetEndMagicNo();       ###CHECK?
    return oBA                  # Return carefully-constructed serialized stream of data that client will deserialize to construct its own structures from our info.

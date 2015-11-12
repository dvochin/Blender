import bpy
import sys
import bmesh
import struct
import array
from math import *
from mathutils import *

import gBlender
import G



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    PENIS PREPARATION
#---------------------------------------------------------------------------    

def gBL_Penis_CalcColliders(sNameMeshPenis):            # Calculates the dimensions of a single capsule that best represents the penis to PhysX.  This provides critical information during runtime to properly setup penis collision by creating a serie of capsule colliders to properly collider the penis with its environment (vagina, breasts, underwear, legs, etc)
    ###NOTE: This runs after every user morph of the penis for man or shemale.  It is the responsibility of the morpher to keep the penis straight and of capsule shape.  (Bending occurs in PhysX)
    ###NOTE: All calculations are in mesh local space (as this is what Client sees).  *ONLY* the debug markers are converted to global space so the markers are at the right position
    ###NOTE: Naming convention: 'width' of penis is left-to-right = X, 'thickness' is up to down = Y, 'lenght' is forward to back = Z (xyz on unrotated body verts (e.g. body 'lying down on back' in Blender)
    
    ###bpy.ops.mesh.select_non_manifold()
    oMeshPenisO = gBlender.SelectAndActivate(sNameMeshPenis)
    bpy.ops.object.mode_set(mode='EDIT')
    bmPenis = bmesh.from_edit_mesh(oMeshPenisO.data)
    ##aVertsPenis = [oVert for oVert in bmPenis.verts if oVert.select]

    #=== Calculate the center of the penis's verts so we can find middle of the shaft ===    
    vecPenisVertCenter = Vector()
    for oVert in bmPenis.verts:
        vecPenisVertCenter += oVert.co
    vecPenisVertCenter /= len(bmPenis.verts)
    
    #=== Iterate through the verts near the middle of the shaft to calculate the maximum 'width' and 'thickness' of the penis shaft ===  (Note that typically-larger penis head is not included.  It gets its own sphere collider to open vagina further)
    C_PenisShaftArea = 0.05             # Area of the shaft we consider for computing shaft bounds below
    nShaftPosMinZ = vecPenisVertCenter.z + C_PenisShaftArea
    nShaftPosMaxZ = vecPenisVertCenter.z - C_PenisShaftArea
    nMaxAbsWidth = 0                        # We assume penis is centered about x and mostly x-symmetrical.  (Tip will have x at zero!)
    nLengthMaxZ = -sys.float_info.max
    nHeightMinY =  sys.float_info.max
    nHeightMaxY = -sys.float_info.max
    for oVert in bmPenis.verts:
        vecVert = oVert.co
        if vecVert.z < nShaftPosMinZ and vecVert.z > nShaftPosMaxZ:        # We only iterate through the tip-half of the penis while attempting to calculate its 'widht', 'height' and 'depth' (how far away from body)
            nAbsX = fabs(vecVert.x)
            if nMaxAbsWidth < nAbsX:        # 'Thickness' (left to right) is always along x axis
                nMaxAbsWidth = nAbsX
            if nHeightMinY > vecVert.y:     # 'Height' (up to down) is along y axis in non-rotated body (lying down on back) and only calculated near penis shaft
                nHeightMinY = vecVert.y
            if nHeightMaxY < vecVert.y:
                nHeightMaxY = vecVert.y
        if nLengthMaxZ < vecVert.z:         # 'Length' (forward to back) is along Z axis in non-rotated body (lying down on back) and calculated on all verts
            nLengthMaxZ = vecVert.z
                
    #=== Calculate the tip position and radius from the statistics collected above ===
    nHeightY = fabs(nHeightMaxY - nHeightMinY)
    nHeightCenterY = (nHeightMaxY + nHeightMinY) / 2
    nPenisRadius = max(nHeightY/2, nMaxAbsWidth)                  # Radius of tip is the maximum of the width & height
    vecTip   = Vector((0, nHeightCenterY, nLengthMaxZ-nPenisRadius))
    vecShaft = Vector((0, nHeightCenterY, vecPenisVertCenter.z))
    
    #=== Calculate the position of the base of the penis by finding the highest vertex on the penis mesh (MaxY) and extracting its Z position (forward/back) ===
    nHeightMaxY = -sys.float_info.max           # The highest point on penis boundary thus far.
    nDistZatMaxHeightY = 0                      # The 'forward/back' distance at the point found at 'nHeightMaxY'                                                       
    for oVert in bmPenis.verts:                 ###OPT!!!: Expensive that we must iterate through all verts! ###IMPROVE: Can find a way to select in some way so we don't iterate through all??
        vecVert = oVert.co
        if nHeightMaxY < vecVert.y:
            nHeightMaxY = vecVert.y
            nDistZatMaxHeightY = vecVert.z
    vecBase = Vector((0, nHeightCenterY, nDistZatMaxHeightY))

    #=== Deselect, return to object mode and dump debug markers if needed ===
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
#     G.Debug_AddMarker("PenisTip",   "SPHERE", nPenisRadius, oMeshPenisO.matrix_world * vecTip, ((0,0,0)))            # Only the debug markers get converted to global space... Everything else (including what client sees) remain in local space)
#     G.Debug_AddMarker("PenisBase",  "SPHERE", nPenisRadius, oMeshPenisO.matrix_world * vecBase, ((0,0,0)))
#     G.Debug_AddMarker("PenisShaft", "SPHERE", nPenisRadius, oMeshPenisO.matrix_world * vecShaft, ((0,0,0))) 
#     G.Debug_AddMarker("PenisVertCenter",   "SPHERE", .01, oMeshPenisO.matrix_world * vecPenisVertCenter, ((0,0,0)))         
    vecCapsule = vecTip - vecBase
    nPenisLength = vecCapsule.length

    #=== Create a capsule the entire volume of the penis shaft to provide visual feedback to user ===        ###DESIGN: Do we really create this capsule during Client requests??
#     vecCapsuleCenter = (vecTip + vecBase) / 2
#     bpy.ops.mesh.primitive_capsule_add(segments=16, rings=5, radius=nPenisRadius, length=nPenisLength)      
#     oCapsuleO = bpy.context.object
#     sNameCapsule = oMeshPenisO.name + G.C_NameSuffix_PenisShaftCollider
#     gBlender.DeleteObject(sNameCapsule)
#     oCapsuleO.name = oCapsuleO.data.name = sNameCapsule
#     oCapsuleO.name = oCapsuleO.data.name = sNameCapsule
#     oCapsuleO.parent = oMeshPenisO
#     oCapsuleO.location = vecCapsuleCenter
#     #oCapsuleO.rotation_mode = 'XYZ'
#     #oCapsuleO.rotation_euler.x = oMeshPenisO.rotation_euler.x
#     oCapsuleO.draw_type = "WIRE"
#     #oCapsuleO.hide = oCapsuleO.hide_render = True
    
    #=== Format of comma-separated string from gBL_Penis_CalcColliders() is: Penis Radius, Penis Length, Base.y (base 'height'), Base.z (base forward/back), ScaleDampCenter.y, ScaleDampCenter.z, ScaleDampSizeStart, ScaleDampSizeEnd
    oPenisScaleDampCenterStart = bpy.data.objects["PenisScaleDampCenterStart"]
    oPenisScaleDampCenterEnd   = bpy.data.objects["PenisScaleDampCenterEnd"]
    vecScaleDampCenter = oPenisScaleDampCenterStart.location * oMeshPenisO.matrix_world     # oMeshPenisO is (like all client-bound meshes) rotated 90 degrees X, while the penis scale center markers are in global space.  Convert them to local mesh coordinates before sending to client
    sMsgClient = str(nPenisRadius) + ","  + str(nPenisLength) + ","  + str(vecBase.y) + "," + str(vecBase.z) + ","  + str(vecScaleDampCenter.y) + "," + str(vecScaleDampCenter.z) + "," + str(oPenisScaleDampCenterStart.empty_draw_size) + "," + str(oPenisScaleDampCenterEnd.empty_draw_size) 

    print("gBL_Penis_CalcColliders() returns Radius, Length, BaseHeightY, BaseDistZ: " + sMsgClient) 
    return sMsgClient

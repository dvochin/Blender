import bpy
import sys
import bmesh
import struct
import array
from math import *
from mathutils import *

import gBlender
import G

#---------------------------------------------------------------------------    Box Collider Creation From Mesh - Originally for Fluid World

def CreateBoxCollidersFromMesh_All():  ###MOVE
    gBlender.SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)
    
    #=== Convert mesh objects to box colliders and serialize ===
    oNodeFolder = bpy.data.objects["(World)"]
    aObjSrc = [oObj for oObj in oNodeFolder.children if oObj.hide == False]
    for oMeshOrigO in aObjSrc:
        oMeshWorkO = gBlender.DuplicateAsSingleton(oMeshOrigO.name, oMeshOrigO.name + "_TempMesh", None, False)
        bpy.ops.object.convert()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.tris_convert_to_quads()  # Convert the composite mesh into as many quads as possible... quads are a natural fit as we generate 2D rectangle bounds for each fit (tris are too wasteful)    ###IMPROVE: default arguments ok?
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        CreateBoxCollidersFromMesh(oMeshWorkO, oMeshOrigO)
        gBlender.DeleteObject(oMeshWorkO.name)
    
def CreateBoxCollidersFromMesh(oMeshWorkO, oMeshOrigO):  # Break down a mesh into a collection of 2D rectangles that will represent the mesh as plane/box colliders in PhysX
    #=== Obtain bmesh reference to the source mesh so we can iterate through its face and create bounding rotated 2D rectangles for each face ===
    ###BUG?: Code assumes no rotation / scale
    
    C_ColliderThickness = .001
    C_ColliderOvershoot = .001  # Oversize the collider plane to help prevent particles getting through cracks...  This unfortunately makes the convex side of the mesh stick out more...     ###IMPROVE: Expose to GUI??  ###TUNE!!             
    
    print("\n=== CreateBoxCollidersFromMesh('" + oMeshOrigO.name + "') ===")
    bm = bmesh.new()
    bm.from_mesh(oMeshWorkO.data)

    #=== Delete the previous colliders if they exist ===
    sNameCollidersFolder = "Colliders-" + oMeshOrigO.name
    if sNameCollidersFolder in bpy.data.objects:
        oFolderColliders = bpy.data.objects[sNameCollidersFolder]
        oFolderColliders.select = True
        oFolderColliders.hide = False
        for oCol in oFolderColliders.children:
            oCol.select = True
        bpy.ops.object.delete()
    
    #=== Create a subfolder node to store the new collider empties ===
    bpy.ops.object.empty_add(type='CUBE')
    oFolderColliders = bpy.context.object
    oFolderColliders.name = sNameCollidersFolder
    oMeshOrigO.select = True
    bpy.context.scene.objects.active = oMeshOrigO
    bpy.ops.object.parent_set(keep_transform=True)  ###LEARN: keep_transform=True is critical to prevent reparenting from destroying the previously set transform of object!!
    oFolderColliders.hide = True
    
    #=== Iterate through all seperated faces of the mesh to calculate its smallest-possible bounding *plane rectangle* (a rectangular plane oriented like the face of minimum size) ===
    for oFace in bm.faces:
        vecFaceNormal = oFace.normal
        quatFaceNormal = G.C_VectorUp.rotation_difference(vecFaceNormal)  # The quaternion that can rotate a flat plane (lying along x,y with normal toward Z+) toward this face (but still with improper 'twist' that we fix later below)
        matPlaneFaceNormal = quatFaceNormal.to_matrix().to_4x4()  # The matrix to rotate from no rotation to this face normal

        #=== Find the longest edge so we can 'twist' our resultant box to best fit this face's longest edge to yield a smaller possible bounding rectangle around this face ===
        oEdgeLongest = None
        nEdgeLenMax = 0
        for oEdge in oFace.edges:
            nEdgeLen = oEdge.calc_length()
            if nEdgeLenMax < nEdgeLen:
                nEdgeLenMax = nEdgeLen
                oEdgeLongest = oEdge
                
        #=== With the longest edge found, calculate it's 'unrotated' version (that vector on a plane parallel to z=0) to determine the 'twist' between it and the forward vector
        vecVert0 = oEdgeLongest.verts[0].co  
        vecVert1 = oEdgeLongest.verts[1].co  
        vecLongEdge = ((vecVert1 - vecVert0) * matPlaneFaceNormal).normalized()  # This is the long edge vector in the space of the rotated plane
        vecLongEdge.z = 0  # We reset the 'height' of edge vector so as to lie flat along x,y so twist quaternion will only rotate about z
        quatTwistZ = G.C_VectorForward.rotation_difference(vecLongEdge);  # Calculate the quaternion that can take the global forward vector to the rotation of the (flat) long edge...  This is how much we need to 'twist' matPlaneFaceNormal to get matPlaneFaceNormalTwistedZ
        quatFaceNormalTwistedZ = quatFaceNormal * quatTwistZ 
        matPlaneFaceNormalTwistedZ = quatFaceNormalTwistedZ.to_matrix().to_4x4()  # Apply the twist quaternion to the untwisted matrix to get the twisted matrix.  This matrix can now take a flat plane lying on x,y to this face with it being 'twisted' so our long edge is parallel to cardinal axes. (So we can calculate 2D bounds and yield smaller rectangle)
        
        #=== With a properly-twisted matrix calculated that could convert a flat plane to the orientation face, the 'z' coordinate of now become constant and we can calculate in that 'flat local space' the maximum absolute values of x & y to find the extent of the box.  (Note that alls 'z' in that local space should be nearly equal as that plane is supposed to be parallel to z=0)
        nMinX = nMinY = sys.float_info.max
        nMaxX = nMaxY = -sys.float_info.max
        for oVert in oFace.verts:
            vecVert = oVert.co
            vecVertFlat = vecVert * matPlaneFaceNormalTwistedZ  ###NOTE: All vecVertFlat.z should be essentially the same value as we've 'unrotated' the face to lie flat along x,y
            if  nMinX > vecVertFlat.x:
                nMinX = vecVertFlat.x
            if  nMinY > vecVertFlat.y:
                nMinY = vecVertFlat.y
            if  nMaxX < vecVertFlat.x:
                nMaxX = vecVertFlat.x
            if  nMaxY < vecVertFlat.y:
                nMaxY = vecVertFlat.y

        #=== With the 'flat 2d bounds' of the face now determined we can figure out the width and height of the bounding twisted rectangle ===
        nSizeX = (nMaxX - nMinX) + C_ColliderOvershoot  # Add a little extra to size so colliders interleave each other slightly
        nSizeY = (nMaxY - nMinY) + C_ColliderOvershoot
        nExtentX = nSizeX / 2  
        nExtentY = nSizeY / 2
        vecPlaneCenterFlat = Vector(((nMinX + nMaxX) / 2, (nMinY + nMaxY) / 2, vecVertFlat.z))  # ... in addition to its center.  (We the last one of the flat vert.z (they're all the same) as the plane is parallel to z=0))
        vecPlaneCenter = matPlaneFaceNormalTwistedZ * vecPlaneCenterFlat  # Unrotate the place center to the face's rotation so we can obtain the final center of the bounding rectangle
        matPlaneCenter = Matrix.Translation(vecPlaneCenter)
        matPlaneFinalG = matPlaneCenter * matPlaneFaceNormalTwistedZ  # oMeshOrigO.matrix_world *              

        #=== Create the output empty cube that client will load and importer convert into box colliders at the provided empty location / rotation / scale ===
        bpy.ops.object.empty_add(type='CUBE', location=oMeshOrigO.matrix_world * vecPlaneCenter, rotation=matPlaneFinalG.to_euler())
        oPlaneO = bpy.context.object
        oPlaneO.name = "C"  ###IMPROVE: Global rename of colliders
        oPlaneO.parent = oFolderColliders
        oPlaneO.scale = Vector((nExtentX, nExtentY, C_ColliderThickness))

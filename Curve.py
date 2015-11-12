import bpy
import sys
from math import *
from mathutils import *
import struct

import gBlender
import G
import Client

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CURVE: Client-controlled cutting functionality to perform Boolean cuts on clothing meshes.
#---------------------------------------------------------------------------    

def gBL_Curve_Create(sNameCurve, nCurvePts, bSymmetryX):                    # Create a Bezier curve that can be client-controlled to create a cutter mesh and perform boolean cuts on clothing meshes via Cut module.
    gBlender.DeleteObject(sNameCurve)
    bpy.ops.curve.primitive_bezier_curve_add()
    oCurveO = bpy.context.object
    oCurveO.parent = bpy.data.objects[G.C_NodeName_Curve]
    oCurve = oCurveO.data
    oCurveO.name = oCurve.name = sNameCurve
    oCurveO.name = oCurve.name = sNameCurve
    oCurveO.rotation_mode = 'XYZ'
    oCurveO.rotation_euler.x = radians(90)          ###LEARN: How to rotate in eulers
    oCurve.dimensions = "3D"
    oCurve.fill_mode = "FULL"
    oSpline = oCurve.splines[0]
    oSpline.use_cyclic_u = bSymmetryX           # Symmetry curves are by definition cyclic (e.g. side curve), non-symmetry (e.g. neck opening) are non-cyclic as their points are mirrored with a mirror modifier
    oSpline.resolution_u = 8                      ###TODO!!!
    aCurvePts = oSpline.bezier_points
    while len(aCurvePts) < nCurvePts:           # Keep adding points until we have the required number.  Client will adjust the individual point positions in gBL_Curve_UpdateCurvePoint()
        aCurvePts.add()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='SELECT')    # Set all bezier points to 'auto' for (much) easier autofit!
    bpy.ops.curve.handle_type_set()
    bpy.ops.object.mode_set(mode='OBJECT')
    return G.DumpStr("OK: Curve_Create(Name='{}', #Pts={}, Sym={}".format(sNameCurve, nCurvePts, bSymmetryX))

def gBL_Curve_UpdateCurvePoint(sNameBaseCloth, sNameCurve, nPt, x, y, z):
    if sNameCurve not in bpy.data.objects:
        return "ERROR: gBL_Curve_UpdateCurvePoint() could not find curve object '{}'".format(sNameCurve)
    oCurveO = bpy.data.objects[sNameCurve]
    oCurve = oCurveO.data
    oSpline = oCurve.splines[0]
    oCurvePt = oSpline.bezier_points[nPt]
    vecCurvePtBlender = G.VectorC2B(Vector((x, y, z)))        # As we're receiving a 3D vector without going through the conversion to verts done while sending a mesh we must convert the coordinate manually here (and likewise when we obtain coordinate from client)
    oCurvePt.co = vecCurvePtBlender
    
    #=== Calculate the snap position of curve point on current cloth manually to avoid the complete rebuild overhead ===
    oBaseClothO = bpy.data.objects[sNameBaseCloth]                  ###CHECK: For some reason in this context we don't need stupid 90 degree rotation back and forth?  WHY???
    aClosestPtResults = oBaseClothO.closest_point_on_mesh(vecCurvePtBlender)   ###LEARN: This call fails early in blender load process as it complains mesh has no data.  (Forced late update and kludge code!)
    vecCurvePtAdjClient = G.VectorB2C(aClosestPtResults[0])      # Return the adjusted point position in client-space.

    return str(vecCurvePtAdjClient[0]) + "," + str(vecCurvePtAdjClient[1]) + "," + str(vecCurvePtAdjClient[2])      # Return the adjusted position of the just-set point so Client knows where on the cloth the curve point falls. 


def gBL_Curve_Rebuild(sNameBaseCloth, sNameCurve):              # Rebuild the curve & cutter... typically done after client has changed on or more curve points
    if sNameCurve not in bpy.data.objects:          ###DESIGN Need separate call for this or update into only function that uses??
        return "ERROR: gBL_Curve_Rebuild() could not find curve object '{}'".format(sNameCurve)
    oCurveO = bpy.data.objects[sNameCurve]
    
    #=== Create a duplicate of the user's curve and set its parent for cleaner node structure ===
    oCutterO = gBlender.DuplicateAsSingleton(oCurveO.name, oCurveO.name + "-" + G.C_NodeName_Cutter, G.C_NodeFolder_Game, True)
    oCutterO.parent = bpy.data.objects[G.C_NodeName_Cutter]           ###SOON: Curve quality!

    #=== Convert the spline curve to a mesh to 'bake' the few bezier points into a fanned-out version and 'shrinkwrap' to the basis mesh to get much closer to mesh surface than the user's curve === 
    bpy.ops.object.convert(target='MESH')            
    oModShrinkwrap = oCutterO.modifiers.new('SHRINKWRAP', 'SHRINKWRAP')
    oBaseCloth = bpy.data.objects[sNameBaseCloth]
    oModShrinkwrap.target = oBaseCloth 
    gBlender.AssertFinished(bpy.ops.object.modifier_apply(modifier=oModShrinkwrap.name))

    #=== Convert back to a curve so that we can easily display a solid curve by adding a bevel object ===        
    bpy.ops.object.convert(target='CURVE')           # Re-convert to spline now that we have a 'baked' representation with about a hundred vertices.
    bpy.ops.object.mode_set(mode='EDIT')
    for nSmoothIterations in range(20):        ###TUNE     ###LEARN: This is how to smooth a curve!  (Smooth as a mesh makes non-mirror-x centers diverge, and looptools doesn't smooth enough)
        bpy.ops.curve.smooth()
    bpy.ops.object.mode_set(mode='OBJECT')
    oCutter = oCutterO.data
    oCutter.resolution_u = 1
    oCutter.bevel_object = bpy.data.objects[G.C_NodeName_CurveBevelShape]
    
    #=== Add a mirror modifier to the cutter mesh whether the curve is symmetrical or not so user sees cuts for both sides of the body ===
    gBlender.Util_CreateMirrorModifierX(oCutterO)
    bpy.ops.object.select_all(action='DESELECT')
    oCutterO.hide_select = oCutterO.hide_render = True

    oCurveO .update_tag({'DATA'})                ###LEARN!!! How to efficiently update only one object!  ###CHECK: Keep???
    oCutterO.update_tag({'DATA'})

    sMsgClient = "OK: gBL_Curve_Rebuild() on curve '{}'".format(sNameCurve)
    return sMsgClient   #print(sMsgClient);

def gBL_Curve_GetCutterAsMesh(sNameCutterAsMesh):         # Called by Client to force a rebuild of this curve & cutter and create & return a mesh copy of the cutter that can be displayed in Client 
    if sNameCutterAsMesh.startswith(G.C_NamePrefix_CutterAsMesh) == False:
        return "ERROR: gBL_Curve_GetCutterAsMesh() did not receive a cutter refresh request that begins with '{}'".format(G.C_NamePrefix_CutterAsMesh)
    sNameCurve  = sNameCutterAsMesh[len(G.C_NamePrefix_CutterAsMesh):]          # Extract the curve and cutter's object name from the client's request.
    sNameCutter = sNameCurve + "-" + G.C_NodeName_Cutter
    if sNameCurve not in bpy.data.objects:
        return "ERROR: gBL_Curve_GetCutterAsMesh() could not find curve object '{}' from request '{}'".format(sNameCurve, sNameCutterAsMesh)

    gBL_Curve_Rebuild(sNameCurve)              # Rebuild the curve and cutter so we can convert the cutter to a mesh and send to client.         
    oCutterAsMeshO = gBlender.DuplicateAsSingleton(sNameCutter, sNameCutterAsMesh, G.C_NodeFolder_Game, False)        ###DESIGN: Hide source a pain...
    bpy.ops.object.convert()                # Convert to mesh
    oCutterAsMeshO.data.name = oCutterAsMeshO.name    # Set the name of the just-created mesh to the name of the object.
    oCutterAsMeshO.parent = bpy.data.objects[G.C_NamePrefix_CutterAsMesh]     # Set parent to its utility node folder to get it out of the way and to facilitate mass cleanup
    gBlender.Util_ConvertToTriangles()      # Convert to triangles Client needs
    return Client.gBL_GetMesh(oCutterAsMeshO.name, 'NoSkinInfo')

import bpy
import sys
from math import *
from mathutils import *
import struct

import gBlender
import G
import Client
import Cut          ###HACK!!!!!!



###NEXT:
# Finally can create cloth from cutter curves!
# Have to remove center point...run other curves... define what curves are used...  improve access to what curve...etc.


# Weird handles and curves now... not auto?
# Rebuild fails cuz of no name on self.oCurveO?

# Need to create from plain 3D points and also update... without destroying?

# CCurve class.  Owned by its attached CCloth in _aCurves
# CCloth based on body suit, and is cut by collection of curves
# Unity: Merge into normal CCloth with all its baggage? (e.g. skinned half, simulation, etc)... or new class?
#  Benefits: 1-1 relationship between both classes on both sides
# Need a CCurvePt class on both sides?
#  Loaded from just a few points stored in Blender sub-objects (acting as 'recipes')


###DEVNOW: Can finally pin curve points to source body verts...
### MAJOR FUCKUP WITH CURVES, SYMMETRY, REVERS AND FUCKING SHIT!

# How about 'extra points'?
# Need to define center: Appears broken when passing in!

# Now have rudimentary bezier curves doing fairly well.
    # Hack with first point
    # Will be editing via hotspots in Unity... get that geared up!


    # Need some centered (like nipple center)?  Add prop?
    # Really give up on proportional?  How about morphing rig?
# How to order now that we have pins?
# How to handle symmetry
# How to handle bezier curve and parenting
    # Redo current pins to be a type of parent??





class CCurvePt:
    def __init__(self, oCurve):
        self.oCurve = oCurve


class CCurve:
    def __init__(self, oCloth, sName, sType):
        self.oCloth = oCloth
        self.sName = sName
        self.sType = sType
        self.aCurvePts = []
        self.oCurveO = None                             # The actual Blender curve we encapsulate & control
        self.oSpline = None                             # The first (and only) spline of self.oCurveO
        self.oCurveSource = None                        # The curve 'source'.  Hierarchy of Blender empty objects the curve is created from (and updated from)
        
        self.aCurvePts.append(CCurvePt(self))

        self.oCurveSource = bpy.data.objects[sType]         ###DEV

        ######gBL_Curve_Create("Test", True)
        gBlender.DeleteObject(sName)
        bpy.ops.curve.primitive_bezier_curve_add()
        self.oCurveO = bpy.context.object
        self.oCurveO.parent = bpy.data.objects[G.C_NodeName_Curve]
        self.oCurveO.name = self.oCurveO.data.name = sName
        self.oCurveO.name = self.oCurveO.data.name = sName
        self.oCurveO.rotation_mode = 'XYZ'
        #######HACK!!!!! oCurveO.rotation_euler.x = radians(90)          ###LEARN: How to rotate in eulers
        self.oCurveO.data.dimensions = "3D"
        self.oCurveO.data.fill_mode = "FULL"
        self.oSpline = self.oCurveO.data.splines[0]
        self.oSpline.use_cyclic_u = True     ####DEV!!!!           # Symmetry curves are by definition cyclic (e.g. side curve), non-symmetry (e.g. neck opening) are non-cyclic as their points are mirrored with a mirror modifier
        self.oSpline.resolution_u = 24                      ###TODO!!!   # At this point we have a bezier curve with one spline containing two control points

        self.CreateOrUpdateCurve()


    def CreateOrUpdateCurve(self):

        #=== Iterate through all curve points (not duplicate for symmetry) and add to curve
        nPt = 0
        nNumCurvePtsLess1 = len(self.oCurveSource.children) - 1
        for oCurvePtO in self.oCurveSource.children:
            #print("STR", oCurvePtO, oCurvePtO.location)
            oCurvePt = self.EditCurvePoint(nPt, oCurvePtO.location)
            bInvertSymmetrizeBezierAboutX = (nPt == nNumCurvePtsLess1)
            
            if (len(oCurvePtO.children)):                       # Process children of curve points as Bezier
                oCurveBezierO = oCurvePtO.children[0] 
                self.UpdateCurveBezier(oCurvePt, bInvertSymmetrizeBezierAboutX, oCurveBezierO.location.x, oCurveBezierO.location.y, oCurveBezierO.location.z)
            nPt += 1
    
        #=== Now iterate through the curve again in reverse order (without the extremities) to add the symmetry points ===
        for nCurvePt in range(nNumCurvePtsLess1-1, 0, -1):      # Iterates backward without both extremities. Note the weirdness in reverse ranges!
            oCurvePtO = self.oCurveSource.children[nCurvePt]
            #print("REV", oCurvePtO, oCurvePtO.location)
            vecLoc = oCurvePtO.location.copy()
            vecLoc.x = -vecLoc.x                            # Point is for the other side of the body
            oCurvePt = self.EditCurvePoint(nPt, vecLoc)
            nPt += 1
        
        self.RebuildCurve()
        

    def RebuildCurve(self):              # Rebuild the curve & cutter... typically done after client has changed on or more curve points
        #=== Create a duplicate of the user's curve and set its parent for cleaner node structure ===
        oCutterO = gBlender.DuplicateAsSingleton(self.oCurveO.name, self.oCurveO.name + "-" + G.C_NodeName_Cutter, G.C_NodeFolder_Game, True)
        oCutterO.parent = bpy.data.objects[G.C_NodeName_Cutter]           ###SOON: Curve quality!
    
        #=== Convert the spline curve to a mesh to 'bake' the few bezier points into a fanned-out version and 'shrinkwrap' to the basis mesh to get much closer to mesh surface than the user's curve === 
        bpy.ops.object.convert(target='MESH')            
        oModShrinkwrap = oCutterO.modifiers.new('SHRINKWRAP', 'SHRINKWRAP')
        oModShrinkwrap.target = self.oCloth.oMeshClothSource.oMeshO
        gBlender.AssertFinished(bpy.ops.object.modifier_apply(modifier=oModShrinkwrap.name))
    
        #=== Convert back to a curve so that we can easily display a solid curve by adding a bevel object ===        
        bpy.ops.object.convert(target='CURVE')           # Re-convert to spline now that we have a 'baked' representation with about a hundred vertices.
        bpy.ops.object.mode_set(mode='EDIT')
        for nSmoothIterations in range(1):        ###TUNE     ###LEARN: This is how to smooth a curve!  (Smooth as a mesh makes non-mirror-x centers diverge, and looptools doesn't smooth enough)
            bpy.ops.curve.smooth()      #########HACK!!!!!!!!
        bpy.ops.object.mode_set(mode='OBJECT')
        oCutter = oCutterO.data
        oCutter.resolution_u = 1
        oCutter.bevel_object = bpy.data.objects[G.C_NodeName_CurveBevelShape]
        
        #=== Add a mirror modifier to the cutter mesh whether the curve is symmetrical or not so user sees cuts for both sides of the body ===
        gBlender.Util_CreateMirrorModifierX(oCutterO)
        bpy.ops.object.select_all(action='DESELECT')
        oCutterO.hide_select = oCutterO.hide_render = True
    
        self.oCurveO .update_tag({'DATA'})                ###LEARN!!! How to efficiently update only one object!  ###CHECK: Keep???
        oCutterO.update_tag({'DATA'})                   ###CHECK: Keep??
   
        
#     def JUNK(self):
#         gBL_Curve_Rebuild(sNameClothSource, "Test")
#     
#         oMeshO = gBlender.DuplicateAsSingleton(sNameClothSource, sNameClothSource+"-HACK", G.C_NodeFolder_Game, True)
#         oMeshO.hide = oMeshO.hide_render = False
#         aBorderLocatorVertPos = {}                            # Map of 'locator verts' for each border.  Because boolean destroys most mesh metainfo, we're using the vertex position of one vertex on each border to rebuild the list of verts per border
#      
#         oCurveTempl = bpy.data.objects[G.C_NodeName_Curve]
#         Cut.Cut_ApplyCut(oMeshO, oCurveTempl.children[0], Vector((0,0,0)), aBorderLocatorVertPos)


    def EditCurvePoint(self, nPt, vecLocation):
        if (nPt >= len(self.oSpline.bezier_points)):
            self.oSpline.bezier_points.add()                         # Add another control point to the curve
        oCurvePt = self.oSpline.bezier_points[nPt]
        oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'AUTO'     # Curve points are auto until set to free by gBL_Curve_UpdateCurveBezier() 
        vecCurvePtBlender = G.VectorC2B(vecLocation)        # As we're receiving a 3D vector without going through the conversion to verts done while sending a mesh we must convert the coordinate manually here (and likewise when we obtain coordinate from client)
        oCurvePt.co = vecCurvePtBlender
        
        ####DEV!!! === Calculate the snap position of curve point on current cloth manually to avoid the complete rebuild overhead ===
        #oBaseClothO = bpy.data.objects[sNameBaseCloth]                  ###CHECK: For some reason in this context we don't need stupid 90 degree rotation back and forth?  WHY???
        #aClosestPtResults = oBaseClothO.closest_point_on_mesh(vecCurvePtBlender)   ###LEARN: This call fails early in blender load process as it complains mesh has no data.  (Forced late update and kludge code!)
        #vecCurvePtAdjClient = G.VectorB2C(aClosestPtResults[0])      # Return the adjusted point position in client-space.
        
        return oCurvePt

    def UpdateCurveBezier(self, oCurvePt, bInvertSymmetrizeBezierAboutX, x, y, z):
        oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'FREE'
        if (bInvertSymmetrizeBezierAboutX):
            oCurvePt.handle_left  = G.VectorC2B(Vector(( x, y, z)))
            oCurvePt.handle_right = G.VectorC2B(Vector((-x, y, z)))
        else:
            oCurvePt.handle_left  = G.VectorC2B(Vector((-x, y, z)))        # As we're receiving a 3D vector without going through the conversion to verts done while sending a mesh we must convert the coordinate manually here (and likewise when we obtain coordinate from client)
            oCurvePt.handle_right = G.VectorC2B(Vector(( x, y, z)))




def gBL_Curve_HACK():
    oCurves = bpy.data.objects["CURVE_HACK"]
    gBL_Curve_Create("Test", True)
    nPt = 0
    sNameClothSource = "FullShirt"
    
    #=== Iterate through all curve points (not duplicate for symmetry) and add to curve
    nNumCurvePtsLess1 = len(oCurves.children) - 1
    for oCurvePtO in oCurves.children:
        #print("STR", oCurvePtO, oCurvePtO.location)
        oCurvePt = gBL_Curve_AddCurvePoint(sNameClothSource, "Test", nPt, oCurvePtO.location.x, oCurvePtO.location.y, oCurvePtO.location.z)
        bInvertSymmetrizeBezierAboutX = (nPt == nNumCurvePtsLess1)
        if (len(oCurvePtO.children)):                       # Process children of curve points as Bezier
            oCurveBezierO = oCurvePtO.children[0] 
            gBL_Curve_UpdateCurveBezier(oCurvePt, bInvertSymmetrizeBezierAboutX, oCurveBezierO.location.x, oCurveBezierO.location.y, oCurveBezierO.location.z)
        nPt += 1

    #=== Now iterate through the curve again in reverse order (without the extremities) to add the symmetry points ===
    for nCurvePt in range(nNumCurvePtsLess1-1, 0, -1):      # Iterates backward without both extremities. Note the weirdness in reverse ranges!
        oCurvePtO = oCurves.children[nCurvePt]
        #print("REV", oCurvePtO, oCurvePtO.location)
        oCurvePt = gBL_Curve_AddCurvePoint(sNameClothSource, "Test", nPt, -oCurvePtO.location.x, oCurvePtO.location.y, oCurvePtO.location.z)
        nPt += 1
    
    gBL_Curve_Rebuild(sNameClothSource, "Test")

    oMeshO = gBlender.DuplicateAsSingleton(sNameClothSource, sNameClothSource+"-HACK", G.C_NodeFolder_Game, True)
    oMeshO.hide = oMeshO.hide_render = False
    aBorderLocatorVertPos = {}                            # Map of 'locator verts' for each border.  Because boolean destroys most mesh metainfo, we're using the vertex position of one vertex on each border to rebuild the list of verts per border
 
    oCurves = bpy.data.objects[G.C_NodeName_Curve]
    Cut.Cut_ApplyCut(oMeshO, oCurves.children[0], Vector((0,0,0)), aBorderLocatorVertPos)

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CURVE: Client-controlled cutting functionality to perform Boolean cuts on clothing meshes.
#---------------------------------------------------------------------------    

def gBL_Curve_Create(sNameCurve, bSymmetryX):                    # Create a Bezier curve that can be client-controlled to create a cutter mesh and perform boolean cuts on clothing meshes via Cut module.
    gBlender.DeleteObject(sNameCurve)
    bpy.ops.curve.primitive_bezier_curve_add()
    oCurveO = bpy.context.object
    oCurveO.parent = bpy.data.objects[G.C_NodeName_Curve]
    oCurve = oCurveO.data
    oCurveO.name = oCurve.name = sNameCurve
    oCurveO.name = oCurve.name = sNameCurve
    oCurveO.rotation_mode = 'XYZ'
    #######HACK!!!!! oCurveO.rotation_euler.x = radians(90)          ###LEARN: How to rotate in eulers
    oCurve.dimensions = "3D"
    oCurve.fill_mode = "FULL"
    oSpline = oCurve.splines[0]
    oSpline.use_cyclic_u = bSymmetryX           # Symmetry curves are by definition cyclic (e.g. side curve), non-symmetry (e.g. neck opening) are non-cyclic as their points are mirrored with a mirror modifier
    oSpline.resolution_u = 24                      ###TODO!!!   # At this point we have a bezier curve with one spline containing two control points

def gBL_Curve_AddCurvePoint(sNameBaseCloth, sNameCurve, nPt, x, y, z):
    if sNameCurve not in bpy.data.objects:
        return "ERROR: gBL_Curve_AddCurvePoint() could not find curve object '{}'".format(sNameCurve)
    oCurveO = bpy.data.objects[sNameCurve]
    oCurve = oCurveO.data
    oSpline = oCurve.splines[0]
    if (nPt >= len(oSpline.bezier_points)):
        oSpline.bezier_points.add()                         # Add another control point to the curve
    oCurvePt = oSpline.bezier_points[nPt]
    oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'AUTO'     # Curve points are auto until set to free by gBL_Curve_UpdateCurveBezier() 
    vecCurvePtBlender = G.VectorC2B(Vector((x, y, z)))        # As we're receiving a 3D vector without going through the conversion to verts done while sending a mesh we must convert the coordinate manually here (and likewise when we obtain coordinate from client)
    oCurvePt.co = vecCurvePtBlender
    
    #=== Calculate the snap position of curve point on current cloth manually to avoid the complete rebuild overhead ===
    oBaseClothO = bpy.data.objects[sNameBaseCloth]                  ###CHECK: For some reason in this context we don't need stupid 90 degree rotation back and forth?  WHY???
    aClosestPtResults = oBaseClothO.closest_point_on_mesh(vecCurvePtBlender)   ###LEARN: This call fails early in blender load process as it complains mesh has no data.  (Forced late update and kludge code!)
    vecCurvePtAdjClient = G.VectorB2C(aClosestPtResults[0])      # Return the adjusted point position in client-space.
    
    return oCurvePt
    #return str(vecCurvePtAdjClient[0]) + "," + str(vecCurvePtAdjClient[1]) + "," + str(vecCurvePtAdjClient[2])      # Return the adjusted position of the just-set point so Client knows where on the cloth the curve point falls. 

def gBL_Curve_UpdateCurveBezier(oCurvePt, bInvertSymmetrizeBezierAboutX, x, y, z):
    oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'FREE'
    if (bInvertSymmetrizeBezierAboutX):
        oCurvePt.handle_left  = G.VectorC2B(Vector(( x, y, z)))
        oCurvePt.handle_right = G.VectorC2B(Vector((-x, y, z)))
    else:
        oCurvePt.handle_left  = G.VectorC2B(Vector((-x, y, z)))        # As we're receiving a 3D vector without going through the conversion to verts done while sending a mesh we must convert the coordinate manually here (and likewise when we obtain coordinate from client)
        oCurvePt.handle_right = G.VectorC2B(Vector(( x, y, z)))


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
    for nSmoothIterations in range(1):        ###TUNE     ###LEARN: This is how to smooth a curve!  (Smooth as a mesh makes non-mirror-x centers diverge, and looptools doesn't smooth enough)
        bpy.ops.curve.smooth()      #########HACK!!!!!!!!
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
    return Client.gBL_GetMesh(oCutterAsMeshO.name)








###OBS: No longer having parent-child of cloth curve points
# def gBL_Curve_SetPinPositions():
#     oCurves = bpy.data.objects["CURVE_HACK"]
#     oBodySrc = bpy.data.objects["WomanA"]
#     for oCurvePinO in oCurves.children:
#         if (oCurvePinO.name != "Center"):
#             oVertGrp = oBodySrc.vertex_groups["_PinVert_" + oCurvePinO.name]
#             if (oVertGrp != None):
#                 bFound = False
#                 nVertGrpIndex = oVertGrp.index 
#                 for oVert in oBodySrc.data.vertices:
#                     for oVertGrp in oVert.groups:
#                         if oVertGrp.group == nVertGrpIndex:
#                             oCurvePinO.location = oBodySrc.matrix_world * oVert.co
#                             print("Setting Curve Pin: ", oCurvePinO.name, oCurvePinO.location)
#                             bFound = True
#                     if (bFound):
#                         break;
#             else:
#                 print("ERROR: Could not find PinVert for curve pin " + oCurvePinO.name)
#         


#     aCurvePts = oSpline.bezier_points
#     while len(aCurvePts) < nCurvePts:           # Keep adding points until we have the required number.  Client will adjust the individual point positions in gBL_Curve_AddCurvePoint()
#         aCurvePts.add()
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.curve.select_all(action='SELECT')    # Set all bezier points to 'auto' for (much) easier autofit!
#     bpy.ops.curve.handle_type_set()
#     bpy.ops.object.mode_set(mode='OBJECT')
#     return G.DumpStr("OK: Curve_Create(Name='{}', #Pts={}, Sym={}".format(sNameCurve, nCurvePts, bSymmetryX))

#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.curve.handle_type_set(type='FREE_ALIGN')
#         bpy.ops.object.mode_set(mode='OBJECT')

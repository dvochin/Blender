from math import *
import sys

import CObject
import Client
import G
import bmesh
import bpy
from gBlender import *
from mathutils import *
import struct


###NEXT:
# Just about ready to insert into Unity
    # Unity needs to query how many curves and their points
    # Need a CCurve, CCurvePt (hotspots) moving and redrawing their cuttersasmesh!
# Need to separate between updates to cutter curves and the actual cutting
# Graceful update without creating a new cloth!! 
# Fixed mirrored but the 'demo cutter mesh' not mirrored... clarify!
    # Revisit usage of MirroX mod
# WOuld be nice to have cleaner scene start!
# Delete cutter objects upon start of new job
# Beziers still as children or siblings?
# Prevent cutter plane destruction for debugging?
#IDEA: Expose smoothing iterations to Unity for each curve!
#IDEA: Also need to expose mirror!
# Weird handles and curves now... not auto?
# Rebuild fails cuz of no name on self.oCurveO?
# Need to create from plain 3D points and also update... without destroying?
# CCurve class.  Owned by its attached CCloth in _aCurves
# CCloth based on body suit, and is cut by collection of curves
# Unity: Merge into normal CCloth with all its baggage? (e.g. skinned half, simulation, etc)... or new class?
#  Benefits: 1-1 relationship between both classes on both sides
# Need a CCurvePt class on both sides?
#  Loaded from just a few points stored in Blender sub-objects (acting as 'recipes')
###TODO###
# Have to show the whole thing in Unity: Semi-transparent body suit, Cutter curve meshes, Cut cloth
###IDEAS###
# 'Extra cutter points'.  Can be stored in recipe and are define as an interleaving point between two permanent points
class CCurve:
    def __init__(self, oCloth, sType):
        self.oCloth = oCloth
        self.sName = "Curve-" + sType
        self.sType = sType
        #self.bAboutBodyCenter = False   ###NOW<16>  (self.sType.find("-Side") == -1)  ###WEAK!!! ###DEV    # Curve is defined about body center (only points on left are specified, right points derived by symmetry from left points)
        #self.bInvertCutterNormals = False#(self.sType.find("-Bottom") != -1)      ###HACK!!!
        self.oCurveO = None                             # The actual Blender curve we encapsulate & control
        self.oCutterO = None                            # The cutter object (responsible for cutting cloth.  (A mesh-version of oCurveO Bezier curve)
        self.oSpline = None                             # The first (and only) spline of self.oCurveO
        self.nPointIterator = 0                         # Utility variable for curve constructors / updators to define / update their curve point without using by-reference workarounds
        
        DeleteObject(self.sName)       ###LEARN: Previous caused bad blender crash wit17h old bp        # The above caused that bad Blender C++ crash with the 'Gives UnicodeDecodeError: 'utf-8' codec can't decode byte 0xdd in position 0' error
        bpy.ops.curve.primitive_bezier_curve_add()
        self.oCurveO = bpy.context.object
        self.oCurveO.parent = bpy.data.objects[G.C_NodeName_Curve]
        self.oCurveO.name = self.oCurveO.data.name = self.sName
        self.oCurveO.name = self.oCurveO.data.name = self.sName
        self.oCurveO.data.dimensions = "2D"
        self.oCurveO.data.fill_mode = "NONE"
        self.oCurveO.data.extrude = 0.01                # Extrude the curve so that its mesh equivalent can perform a boolean cut on flattened UV cloth mesh
        self.oSpline = self.oCurveO.data.splines[0]
        self.oSpline.use_cyclic_u = True                # Symmetry curves are by definition cyclic (e.g. side curve), non-symmetry (e.g. neck opening) are non-cyclic as their points are mirrored with a mirror modifier
        self.oSpline.resolution_u = 16                  ###TUNE # At this point we have a bezier curve with one spline containing two control points

        #Util_HideMesh(self.oCurveO)


    def SetPoint(self, vecPt):
        self.nPointIterator += 1            # Update our iterator by one.  This call assumes caller reset the iterator just before a sequence of calls
        vec3D = Vector((vecPt.x, vecPt.y, 0))
        #G.Debug_AddMarker("P" + str(nPt), "PLAIN_AXES", 0.01, vec3D, ((0,0,0)))        ###TEMP<17>
        if (self.nPointIterator > len(self.oSpline.bezier_points)):
            self.oSpline.bezier_points.add()                         # Add another control point to the curve
        oCurvePt = self.oSpline.bezier_points[self.nPointIterator-1]
        oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'AUTO'     # Curve points are auto until set to free by gBL_Curve_UpdateCurveBezier() 
        oCurvePt.co = vec3D
        return oCurvePt
    
    def SetPointBeziers(self, sType, x, y):         # Adjusts the bezier handles of the last iterated point set in SetPoint()
        oCurvePt = self.oSpline.bezier_points[self.nPointIterator-1]
        if sType == "C":
            oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'FREE'
            oCurvePt.handle_left  = oCurvePt.co + Vector(( x,  y, 0))
            oCurvePt.handle_right = oCurvePt.co + Vector((-x,  y, 0))
        elif sType == "V":
            oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'ALIGNED'
            oCurvePt.handle_left  = oCurvePt.co + Vector(( x,  y, 0))
            oCurvePt.handle_right = oCurvePt.co + Vector((-x, -y, 0))

    def UpdateCutterCurve(self):
        self.RebuildCurve()             ###TODO<17>: Broken?  ###DESIGN<17>: How to update points?
        

    def RebuildCurve(self):              # Rebuild the curve & cutter... typically done after client has changed on or more curve points
        #=== Create a duplicate of the user's curve and set its parent for cleaner node structure ===
        self.oCutterO = DuplicateAsSingleton(self.oCurveO.name, self.oCurveO.name + "-" + G.C_NodeName_Cutter, G.C_NodeFolder_Game, True)
        self.oCutterO.parent = bpy.data.objects[G.C_NodeName_Cutter]           ###SOON: Curve quality!
        #=== Convert the spline curve to a mesh to 'bake' the few bezier points into a fanned-out version and 'shrinkwrap' to the basis mesh to get much closer to mesh surface than the user's curve === 
        bpy.ops.object.convert(target='MESH')
        

    def CutClothWithCutterCurve(self, oMeshCutCloth, sMirrorX=None):
        #print("-CCurve.CutClothWithCutterCurve() on curve '{}'".format(self.sName))
        G.Dump("CutClothWithCutterCurve: " + oMeshCutCloth.name)
        self.RebuildCurve()     ###CHECK<17>?
        
        #=== Mirror the cutter mesh about X=0.5 if requested (needed for side cuts to enforce symmetry ===
        if sMirrorX == "MirrorX":
            oModMirrorX = Util_CreateMirrorModifierX(self.oCutterO)
            oModMirrorX.mirror_object = bpy.data.objects["EmptyAtZeroPointFiveForClothCutting"]     # Specify empty set to X=0.5 so mirror is done about body center
            AssertFinished(bpy.ops.object.modifier_apply(modifier=oModMirrorX.name))        

        #=== Create a boolean modifier and apply it to remove the extra bit beyond the current cutter ===
        SelectAndActivate(oMeshCutCloth.name, True)
        oModBoolean = oMeshCutCloth.modifiers.new('BOOLEAN', 'BOOLEAN')
        #oModBoolean.solver = "CARVE"                ###LEARN: Older 'CARVE' Boolean Solver appears to destroy all the custom data layers.  BMESH is default but it has problems...  ###DESIGN<17> what to do?
        ###BUG<17>: BMESH cuts sometime don't work
        oModBoolean.object = self.oCutterO
        oModBoolean.operation = 'DIFFERENCE'            ###LEARN: Difference is the one we always want when cutting as the others appear useless!  Note that this is totally influenced by side of cutter normals!!
        AssertFinished(bpy.ops.object.modifier_apply(modifier=oModBoolean.name))  ###LEARN: Have to specify 'modifier' or this won't work!
        
        #=== Boolean cut leaves quads and ngons on the border and triangles give us more control on what to delete -> Triangulate before border cleanup ===
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete_loose()                     # For some reason back cloth leaves loose verts!  Clean with this call
        bpy.ops.mesh.quads_convert_to_tris()            ###CHECK<17>: Needed??
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        Util_HideMesh(self.oCutterO)


# class CCurvePt:        ###DESIGN<17>: Adopt?
#     def __init__(self, sName):
#         self.OBSOLETE()

class CCurveNeck(CCurve):
    def __init__(self, oCloth, sType):
        super(self.__class__, self).__init__(oCloth, sType)
        #--- Unity-public properties ---
        self.oObj = CObject.CObject("Neck Opening Curve Parameters")

        self.oPropUpSeamDist            = self.oObj.PropAdd("UpSeamDist",           "", 0.03, 0.00, 0.5)        ###IMPROVE<17>: extract the max from some seam curves?
        self.oPropUpSeamCurveX          = self.oObj.PropAdd("UpSeamCurveX",         "", 0.00, -0.1, 0.1)
        self.oPropUpSeamCurveY          = self.oObj.PropAdd("UpSeamCurveY",         "", 0.04, 0.0, 0.2)

        self.oPropNeckFrontHeight       = self.oObj.PropAdd("NeckFrontHeight",      "", 0.8, 0.5, 1.0)
        self.oPropNeckFrontCurveX       = self.oObj.PropAdd("NeckFrontCurveX",      "", 0.09, 0.0, 0.2)
        self.oPropNeckFrontCurveY       = self.oObj.PropAdd("NeckFrontCurveY",      "", 0.00, -0.2, 0.2)

        self.oPropNeckBackHeight        = self.oObj.PropAdd("NeckBackHeight",       "", 0.82, 0.5, 1.0)
        self.oPropNeckBackCurveX        = self.oObj.PropAdd("NeckBackCurveX",       "", 0.04, 0.0, 0.2)
        self.oPropNeckBackCurveY        = self.oObj.PropAdd("NeckBackCurveY",       "", 0.00, -0.2, 0.2)

    def UpdateCurvePoints(self, bmCloth3DS):
        #=== Set common variables re-used by points below ===
        nCenterUV = 0.5
        vecSeamPointNeckToArmL = self.oCloth.oClothSrc.aDictSeamCurves["TopL"].GetPosAtSeamChainLength(bmCloth3DS, self.oPropUpSeamDist.PropGet())
        vecSeamPointNeckToArmR = self.oCloth.oClothSrc.aDictSeamCurves["TopR"].GetPosAtSeamChainLength(bmCloth3DS, self.oPropUpSeamDist.PropGet()) ###IMPROVE<17>: Ditch right curves and derive R from L?

        #--- Set point above head (for loop closure) ---        
        self.nPointIterator = 0           # Reset the curve point iterators so calls below always start at point 0
        self.SetPoint(Vector((nCenterUV, 1.1)))
        #--- Set left neck-to-arm seam point ----
        self.SetPoint(vecSeamPointNeckToArmL)
        self.SetPointBeziers("V", self.oPropUpSeamCurveX.PropGet(), self.oPropUpSeamCurveY.PropGet())
        #--- Set front point and beziers----
        self.SetPoint(Vector((nCenterUV, self.oPropNeckFrontHeight.PropGet())))
        self.SetPointBeziers("C", self.oPropNeckFrontCurveX.PropGet(), self.oPropNeckFrontCurveY.PropGet())
        #--- Set right neck-to-arm seam point ----
        self.SetPoint(vecSeamPointNeckToArmR)
        self.SetPointBeziers("V", self.oPropUpSeamCurveX.PropGet(), -self.oPropUpSeamCurveY.PropGet())  # Note negated Y for right-side symmetry to left side
        #--- Cut the front UV flattened mesh ---
        self.CutClothWithCutterCurve(self.oCloth.oMeshO_UVF)

        #--- Set left neck-to-arm seam point ----
        self.nPointIterator = 1
        self.SetPoint(vecSeamPointNeckToArmL)
        self.SetPointBeziers("V", -self.oPropUpSeamCurveX.PropGet(), self.oPropUpSeamCurveY.PropGet())
        #--- Set front point and beziers----
        self.SetPoint(Vector((nCenterUV, self.oPropNeckBackHeight.PropGet())))
        self.SetPointBeziers("C", self.oPropNeckBackCurveX.PropGet(), self.oPropNeckBackCurveY.PropGet())
        #--- Set right neck-to-arm seam point ----
        self.SetPoint(vecSeamPointNeckToArmR)
        self.SetPointBeziers("V", -self.oPropUpSeamCurveX.PropGet(), -self.oPropUpSeamCurveY.PropGet())
        #--- Cut the back UV flattened mesh ----0.03241414141414141414141414141414141414141
        self.CutClothWithCutterCurve(self.oCloth.oMeshO_UVB)


class CCurveSide(CCurve):
    def __init__(self, oCloth, sType):
        super(self.__class__, self).__init__(oCloth, sType)
        #--- Unity-public properties ---
        self.oObj = CObject.CObject("Side Curve Parameters")
        self.oPropUpSeamDist     = self.oObj.PropAdd("UpSeamDist",        "", 0.07, 0.00, 0.5)
        self.oPropUpSeamCurveX   = self.oObj.PropAdd("UpSeamCurveX",      "", 0.01, -0.1, 0.1)
        self.oPropUpSeamCurveY   = self.oObj.PropAdd("UpSeamCurveY",      "", 0.20, 0.0, 0.2)

        self.oPropSideSeamDist   = self.oObj.PropAdd("SideSeamDist",      "", 0.45, 0.00, 1.0)
        self.oPropSideSeamCurveX = self.oObj.PropAdd("SideSeamCurveX",    "",-0.04, -0.1, 0.1)
        self.oPropSideSeamCurveY = self.oObj.PropAdd("SideSeamCurveY",    "", 0.02, -0.1, 0.1)

    def UpdateCurvePoints(self, bmCloth3DS):
        #=== Set common variables re-used by points below ===
        vecSeamPointUpL   = self.oCloth.oClothSrc.aDictSeamCurves["TopL"] .GetPosAtSeamChainLength(bmCloth3DS, self.oPropUpSeamDist.PropGet())
        vecSeamPointUpR   = self.oCloth.oClothSrc.aDictSeamCurves["TopR"] .GetPosAtSeamChainLength(bmCloth3DS, self.oPropUpSeamDist.PropGet()) ###IMPROVE<17>: Ditch right curves and derive R from L?
        vecSeamPointSideL = self.oCloth.oClothSrc.aDictSeamCurves["SideL"].GetPosAtSeamChainLength(bmCloth3DS, self.oPropSideSeamDist.PropGet())
        vecSeamPointSideR = self.oCloth.oClothSrc.aDictSeamCurves["SideR"].GetPosAtSeamChainLength(bmCloth3DS, self.oPropSideSeamDist.PropGet()) ###IMPROVE<17>: Ditch right curves and derive R from L?

        #--- Set two points to the extreme right/left to cut requrested part of arm mesh ---        
        self.nPointIterator = 0
        self.SetPoint(Vector((1.5, -0.5)))
        self.SetPointBeziers("V", 0, 0)
        self.SetPoint(Vector((1.5, 1.5)))
        self.SetPointBeziers("V", 0, 0)
        #--- Set neck-to-arm seam point ----
        self.SetPoint(vecSeamPointUpL)
        self.SetPointBeziers("V", self.oPropUpSeamCurveX.PropGet(), self.oPropUpSeamCurveY.PropGet())
        #--- Set side hand-to-ankle seam point ----
        self.SetPoint(vecSeamPointSideL)
        self.SetPointBeziers("V", self.oPropSideSeamCurveX.PropGet(), self.oPropSideSeamCurveY.PropGet())
        #--- Cut the UV flattened meshes ---
        self.CutClothWithCutterCurve(self.oCloth.oMeshO_UVF, "MirrorX")
        self.CutClothWithCutterCurve(self.oCloth.oMeshO_UVB, "MirrorX")


class CCurveTorsoSplit(CCurve):
    def __init__(self, oCloth, sType):
        super(self.__class__, self).__init__(oCloth, sType)
        #--- Unity-public properties ---
        self.oObj = CObject.CObject("Torso Split Curve Parameters")
        self.oPropUpSeamDist     = self.oObj.PropAdd("UpSeamDist",        "", 0.51, 0.00, 0.1)
        self.oPropUpSeamCurveX   = self.oObj.PropAdd("UpSeamCurveX",      "", 0.10, -0.1, 0.1)
        self.oPropUpSeamCurveY   = self.oObj.PropAdd("UpSeamCurveY",      "", 0.00, -0.1, 0.1)

    def UpdateCurvePoints(self, bmCloth3DS):
        #=== Set common variables re-used by points below ===
        vecSeamPointUpL   = self.oCloth.oClothSrc.aDictSeamCurves["SideL"] .GetPosAtSeamChainLength(bmCloth3DS, self.oPropUpSeamDist.PropGet())
        vecSeamPointUpR   = self.oCloth.oClothSrc.aDictSeamCurves["SideR"] .GetPosAtSeamChainLength(bmCloth3DS, self.oPropUpSeamDist.PropGet()) ###IMPROVE<17>: Ditch right curves and derive R from L?

        #--- Set two points to the extreme right/left to cut requrested part of arm mesh ---        
        self.nPointIterator = 0                 ###IMPROVE<17>: Add property to flip what is removed (top or bottom)
        self.SetPoint(Vector((-0.5, -0.5)))
        #self.SetPointBeziers("V", 0, 0)
        self.SetPoint(Vector((1.5, -0.5)))
        #self.SetPointBeziers("V", 0, 0)
        #--- Set left hand-to-ankle seam point ----
        self.SetPoint(vecSeamPointUpL)
        self.SetPointBeziers("V", self.oPropUpSeamCurveX.PropGet(), self.oPropUpSeamCurveY.PropGet())
        #--- Set right hand-to-ankle seam point ----
        self.SetPoint(vecSeamPointUpR)
        self.SetPointBeziers("V", self.oPropUpSeamCurveX.PropGet(), self.oPropUpSeamCurveY.PropGet())
        #--- Cut the UV flattened meshes ---
        self.CutClothWithCutterCurve(self.oCloth.oMeshO_UVF)
        self.CutClothWithCutterCurve(self.oCloth.oMeshO_UVB)

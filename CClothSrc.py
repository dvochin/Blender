import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

from gBlender import *
import G
import CBody
import CMesh
import Client
import CObject

class CClothSrc:        # CClothSrc: A 'cloth source' is a full-body cloth mesh that is Flex-simulated to adjust to the user-specified body shape.  It forms the base of CCloth cloth meshes that cut parts of this mesh to remove extra fabric as per user-specified cutting curves.
    def __init__(self, oBodyBase, sNameClothSrc):
        print("=== CClothSrc.ctor()  oBodyBase = '{}'  sNameClothSrc = '{}' ===".format(oBodyBase.sMeshPrefix, sNameClothSrc))

        self.oBodyBase              = oBodyBase         # The back-reference to the owning bodybase that owns / manages this instance
        self.sNameClothSrc          = sNameClothSrc     # The Blender name of the mesh we cut from.  (e.g. 'Bodysuit')
        self.oMeshClothSrc          = None              # The runtime source cloth mesh.  Simulated by Flex at runtime to adjust to user's body shape
        self.aDictSeamCurves = {}                       # Collection of seam curves (traverses UV seams during Boolean cutting) 
        self.oTreeKD = None                             # KD tree that speeds up finding verts by position.


        #=== Obtain CMesh reference to our source mesh ===
        self.oMeshClothSrc = CMesh.CMesh.CreateFromExistingObject(self.sNameClothSrc)

        #--- Unity-public properties ===
#         self.oObj = CObject.CObject("Cloth Global Parameters")
#         self.oPropNeckStrapThickness     = self.oObj.PropAdd("NeckStrapThickness",    "", 0.01, 0.001, 0.1) ###TODO<17>

        #===== DEFINE BODYSUIT SEAM CURVES (FOR SEAM TRAVESAL DURING CUTTING) =====
        bmClothSrc = bmesh.new()
        bmClothSrc.from_mesh(self.oMeshClothSrc.GetMesh().data)

        #=== Prepare seam curve definition by identifying seam curve beginnings and ends for KD tree search just below
        oTreeKD = kdtree.KDTree(10)         ###WEAK: Every bodysuit will have 10 seam boundary verts? (one curve from neck to hand upper, one from hand lower to exterior ankle, one from interio ankle to other ankle?
        for oEdge in bmClothSrc.edges:
            if oEdge.seam:                  ###IMPROVE: Call bpy.ops.uv.seams_from_islands() first? 
                for oVert in oEdge.verts:
                    if oVert.is_boundary:
                        oTreeKD.insert(oVert.co, oVert.index)
        oTreeKD.balance()

        #=== Define our six seam curves by searching for the nearest seam curve starting point ===
        CBodySuitSeamCurve.SeamCurve_CreateBothSides("Top",    self.aDictSeamCurves, oTreeKD, self.oMeshClothSrc.GetMesh(), bmClothSrc, Vector((0.07, 0, 1.54)))      ###WEAK: Hardcoded position...
        CBodySuitSeamCurve.SeamCurve_CreateBothSides("Side",   self.aDictSeamCurves, oTreeKD, self.oMeshClothSrc.GetMesh(), bmClothSrc, Vector((0.63, -0.05, 1.40)))
        CBodySuitSeamCurve.SeamCurve_CreateBothSides("Bottom", self.aDictSeamCurves, oTreeKD, self.oMeshClothSrc.GetMesh(), bmClothSrc, Vector((0.02, 0.04, 0.08)))

        
    def DoDestroy(self):
        self.oMeshClothSrc.DoDestroy()      ###DESIGN<17>: This destoys real cloth source permanently!?!?!

        

  
    
class CBodySuitSeamCurvePt:     # CBodySuitSeamCurvePt: A seam point in our parent CBodySuitSeamCurve seam chain.  Used to traverse easily between 3D domain and low and high UV domains
    def __init__(self, nPointOrdinal, oVert, oPtPrev, oMeshO, bm, aLayer3DSUV):
        self.nPointOrdinal = nPointOrdinal          # Our ordering in our parent's collection of seam chain
        self.nVertID = oVert.index                  # Our vertex ID in bodysuit
        self.nDistInChainUV = 0                     # UV distance of this point in the chain from start of chain
        self.nDistToNextPtUv = 0                    # The lenghth of this UV position to our next point (if any so zero for last) 
        self.vecUVL = None                          # Our low  UV coordinate (we have exactly two UVs as we're a seam vert!)  Low  X UV = front of bodysuit cloth
        self.vecUVH = None                          # Our high UV coordinate (we have exactly two UVs as we're a seam vert!)  High X UV = rear  of bodysuit cloth

        #=== Iterate through the UV loops of this vert to find all distinct UV positions.  As this vert is a seam we should always find exactly two distincts UVs ===
        setUniqueUVs = set()
        for oLoop in oVert.link_loops:
            oUV = aLayer3DSUV[oLoop.index]
            vecUV = oUV.uv.freeze()
            setUniqueUVs.add(vecUV)
        if len(setUniqueUVs) != 2:
            raise Exception("###EXCEPTION: CBodySuitSeamCurvePt found seam vert with no dual UVs!")

        #=== Order the distinct UVs by X so the front-side UV chain is always linked with front-side UV positions (and vice-versa for rear of cloth)
        vecUV1 = setUniqueUVs.pop()
        vecUV2 = setUniqueUVs.pop()
        if (vecUV1.x < vecUV2.x):
            self.vecUVL = vecUV1
            self.vecUVH = vecUV2
        else: 
            self.vecUVH = vecUV1
            self.vecUVL = vecUV2

        #=== Calculate the UV distance travelled thus far in this chain ===
        if oPtPrev is not None:
            oPtPrev.nDistToNextPtUv = (self.vecUVL - oPtPrev.vecUVL).length         # Store the length to this point in PREVIOUS point
            self.nDistInChainUV = oPtPrev.nDistInChainUV + oPtPrev.nDistToNextPtUv  # Calculate where we are in our chain

        #print("- SeamCurvePt# {:2d} = {:4d} of len {:3f} at {:3f} = {} - {}".format(self.nPointOrdinal, self.nVertID, self.nDistToNextPtUv, self.nDistInChainUV, self.vecUVL, self.vecUVH))

        
class CBodySuitSeamCurve:       # CBodySuitSeamCurve: a seam chain in source bodysuit cloth.  Contains CBodySuitSeamCurvePt seam points along our chain.  Used to position UV-domain boolean cutting points for UV-based cloth cutting
    def __init__(self, sNameCurve, sSide, oTreeKD, oMeshO, bmCloth3DS, vecLocSearch):       ###TODO<17>: CBodySuit?  Too many args!
        self.sNameCurve = sNameCurve
        self.sSide = sSide
        self.nVertChainStart = 0            # The vert in bodysuit where this seam curve starts.  (Vert is both a boundary vert and on seam)
        self.aChainPts = []                 # Array of CBodySuitSeamCurvePt storing all the info we need for each bodysuit seam vert & UVs
        
        #=== Find the seam curve starting point by searching the KD tree already loaded with bodysuit seam ends ===
        vecLoc, self.nVertChainStart, nDist = oTreeKD.find(vecLocSearch)
        if nDist > 0.1:
            raise Exception("###EXCEPTION: CBodySuitSeamCurve.ctor('{}', '{}') could not find seam curve starting point near enough to {}.  Closest dist = {}".format(sNameCurve, sSide, vecLocSearch, nDist))             
        #print("\nCBodySuitSeamCurve.ctor('{}', '{}') finds chain starting vert {} at dist of {} from starting search position".format(self.sNameCurve, self.sSide, self.nVertChainStart, nDist))

        #=== Initialize for chain lookup loop below ===
        aLayer3DSUV = oMeshO.data.uv_layers.active.data        ###LEARN: How to access UV data
        bmCloth3DS.verts.ensure_lookup_table()
        oVertNow = bmCloth3DS.verts[self.nVertChainStart]
        nVertChainOrdinal = 0
        oPt = CBodySuitSeamCurvePt(nVertChainOrdinal, oVertNow, None, oMeshO, bmCloth3DS, aLayer3DSUV)
        self.aChainPts.append(oPt)

        #=== Reset all the edge tags for next loop ===
        for oEdge in bmCloth3DS.edges:          ###WEAK<17> Why the heck is this required?
            oEdge.tag = False

        #=== Iterate through the seams chain beginning at vert self.nVertChainStart until we reach the end ===
        while oVertNow is not None:
            oVertNext = None
            for oEdge in oVertNow.link_edges:
                if oEdge.seam and (oEdge.tag == False):
                    oEdge.tag = True                        # Tag traversed edges as we go so we never go backward    ###BUG<17>? Screws up future iterations?  reset tags?
                    oVertNext = oEdge.other_vert(oVertNow)
                    nVertChainOrdinal += 1
                    oPt = CBodySuitSeamCurvePt(nVertChainOrdinal, oVertNext, oPt, oMeshO, bmCloth3DS, aLayer3DSUV)
                    self.aChainPts.append(oPt)
                    break
            oVertNow = oVertNext
        #print("CBodySuitSeamCurve '{}' formed with {} points.".format(self.sNameCurve, len(self.aChainPts)))

    def GetPosAtSeamChainLength(self, bmCloth3DS, nLenChain):
        oPtPrev = None
        for oPt in self.aChainPts:
            if (oPt.nDistInChainUV > nLenChain):
                vecThisSegment = oPt.vecUVL - oPtPrev.vecUVL        ###TODO<17>: Array for high/low!
                nLenThisSegment = vecThisSegment.length 
                nLenRemainingForThisSegment = nLenChain - oPtPrev.nDistInChainUV
                nRatioNeededThisSegment = nLenRemainingForThisSegment / nLenThisSegment
                vecToAddThisSegment = vecThisSegment * nRatioNeededThisSegment 
                vecFinal = oPtPrev.vecUVL + vecToAddThisSegment      # Final position is start of previous point + interpolated distance to cover the remain (between two points)   
                #vec3D = Vector((vecFinal.x, vecFinal.y, 0))
                #G.Debug_AddMarker("T", "PLAIN_AXES", 0.005, vec3D, ((0,0,0)))
                #bpy.context.scene.cursor_location = vec3D
                return vecFinal 
                break
            oPtPrev = oPt           # Remember previous point so we can interpolate once we find which two points are closest to required distance
            ###IMPROVE<17>: End of chain test
        raise Exception("###EXCEPTION: CBodySuitSeamCurve.GetPosAtSeamChainLength() could not find position for length ", nLenChain, len(self.aChainPts))
      

    @classmethod
    def SeamCurve_CreateBothSides(cls, sNameCurve, aDictSeamCurves, oTreeKD, oMeshO, bm, vecLocSearch):
        ###OBS<17>? Simplifying assumption where Front / Back are X mirrored and coincident means we no longer need both sides!
        aDictSeamCurves[sNameCurve + "L"] = cls(sNameCurve, 'L', oTreeKD, oMeshO, bm, vecLocSearch)
        vecLocSearch.x = -vecLocSearch.x
        aDictSeamCurves[sNameCurve + "R"] = cls(sNameCurve, 'R', oTreeKD, oMeshO, bm, vecLocSearch)




#     def PrepareClothForGame(self):
#         #=== Post-process the simulated-part to be ready for Unity ===
#         #Client.Client_ConvertMeshForUnity(self.oMeshClothSrc.GetMesh(), False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
# #         SelectAndActivate(self.oMeshClothSrc.GetName())
# #         bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from simulated mesh to save memory
# 
#         return "OK"


# Also... broken UVs... how to fix?  (In later loop after cleanup?)
        ###TODO<16>: Duplicate verts along seams??
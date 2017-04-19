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


class CClothSrc:        # CClothSrc: A 'cloth source' is a full-body cloth mesh that is Flex-simulated to adjust to the user-specified body shape.  It forms the base of CCloth cloth meshes that cut parts of this mesh to remove extra fabric as per user-specified cutting curves.  These are created at Blender launch and are never deleted
    def __init__(self, sNameClothSrc):
        print("=== CClothSrc.ctor()  sNameClothSrc = '{}' ===".format(sNameClothSrc))
        self.sNameClothSrc = sNameClothSrc              # The Blender name of the mesh we cut from.  (e.g. 'Bodysuit')
        self.aDictSeamCurves = {}                       # Collection of seam curves (traverses UV seams during Boolean cutting) 
        self.oTreeKD = None                             # KD tree that speeds up finding verts by position.

        #--- UV-domain related ---
        self.oMeshO_3DS = None                          # The untouched source 3D cloth mesh
        self.oMeshO_UVF = None                          # The front UV cloth source mesh in the UV domain.  CCloth copies from this to apply its cutting curves to generate user-specified cloth.
        self.oMeshO_UVB = None                          # Back version of the above

        #--- Unity-public properties ===
#         self.oObj = CObject.CObject("Cloth Global Parameters")
#         self.oPropNeckStrapThickness     = self.oObj.PropAdd("NeckStrapThickness",    "", 0.01, 0.001, 0.1) ###TODO17:


        #===== CONVERSION TO FLATTENED UV MESH PRIOR TO BOOLEAN CUTS =====
        self.oMeshO_3DS = bpy.data.objects[self.sNameClothSrc]       # The untouched source 3D cloth mesh ###TODO17:?          ###IMPROVE18: Go all the way toward CMesh?
    
        #=== Open bmesh of reference mesh ===
        bm3DS = bmesh.new()                                 ###LEARN: Can't access UV data if we open in edit mode! (Have to open bmesh using from_mesh())
        bm3DS.from_mesh(self.oMeshO_3DS.data)
        aLayer3DSUV = self.oMeshO_3DS.data.uv_layers.active.data        ###LEARN: How to access UV data
        
        #=== Construct a KDTree from source 3D mesh (so we can spacially find verts quickly during UV -> 3D conversion)         
        self.oTreeKD = kdtree.KDTree(len(self.oMeshO_3DS.data.polygons))                       ###LEARN: How to quickly locate spacial data!
        for oPoly in self.oMeshO_3DS.data.polygons:
            aUV = [aLayer3DSUV[nLoopIndex].uv for nLoopIndex in oPoly.loop_indices]     ###LEARN: How to easily traverse array indirection
            vecFaceCenterUV = Vector((0,0,0))
            for oUV in aUV:
                vecFaceCenterUV.x += oUV.x
                vecFaceCenterUV.y += oUV.y
            vecFaceCenterUV /= len(aUV)
            self.oTreeKD.insert(vecFaceCenterUV, oPoly.index)
        self.oTreeKD.balance()
        
        #=== Create two UV-domain mesh (front UV and back UV) so we can cut with a flattened mesh that doesn't move with user morphs ===
        oMesh_UVF = bpy.data.meshes.new(self.sNameClothSrc + "-UVF")
        oMesh_UVB = bpy.data.meshes.new(self.sNameClothSrc + "-UVB")
        self.oMeshO_UVF = bpy.data.objects.new(oMesh_UVF.name, oMesh_UVF)
        self.oMeshO_UVB = bpy.data.objects.new(oMesh_UVB.name, oMesh_UVB)
        bpy.context.scene.objects.link(self.oMeshO_UVF)
        bpy.context.scene.objects.link(self.oMeshO_UVB)
        SetParent(self.oMeshO_UVF.name, self.oMeshO_3DS.name)
        SetParent(self.oMeshO_UVB.name, self.oMeshO_3DS.name)

        #=== Create new layer in new UV mesh so we can store back reference to the reference 3D vert (will be needed by UV -> 3D conversion) ===
        bmUVF = bmesh.new()
        bmUVB = bmesh.new()
        bmUVF.from_mesh(oMesh_UVF)
        bmUVB.from_mesh(oMesh_UVB)
        oLayVertUVF = bmUVF.verts.layers.int.new(G.C_DataLayer_VertsSrc)
        oLayVertUVB = bmUVB.verts.layers.int.new(G.C_DataLayer_VertsSrc)

        #=== Create verts where unique UVs exist.  This will traverse the fact that verts between textures have different UVs === 
        aMapUV2VertNewF = {}                # Temporary unique UVs back to new vert index (temporarily needed in 3D -> UV process)
        aMapUV2VertNewB = {}
        for oFace in bm3DS.faces:
            for oLoop in oFace.loops:
                oUV = aLayer3DSUV[oLoop.index]
                vecUV = oUV.uv.freeze()                 ###LEARN: We must 'freeze' a vector before it can be inserted into a collection (its hash function needs non-mutable value)
                if vecUV not in aMapUV2VertNewF:
                    if vecUV.x < 1:
                        vecUV3D = Vector((vecUV.x, vecUV.y, 0))
                        aMapUV2VertNewF[vecUV] = len(bmUVF.verts)    # We're adding a new vert at this unique UV coordinate, so the vert ID is the number of verts already inseted in the mesh (by this loop)
                        oVertNewF = bmUVF.verts.new(vecUV3D)
                        oVertNewF[oLayVertUVF] = oLoop.vert.index + G.C_OffsetVertIDs      # Store back-reference to the reference vert so we can reconstruct the 3D mesh from the flat UV one. (add offset so default 0 means new vert)
                    else:
                        vecUV3D = Vector((vecUV.x - 1, vecUV.y, 0))     ###NOTE: Note the -1 on x so back cloth is coincident with front in UV domain ###DESIGN17: Keep??
                        aMapUV2VertNewB[vecUV] = len(bmUVB.verts)    # We're adding a new vert at this unique UV coordinate, so the vert ID is the number of verts already inseted in the mesh (by this loop)
                        oVertNewB = bmUVB.verts.new(vecUV3D)
                        oVertNewB[oLayVertUVB] = oLoop.vert.index + G.C_OffsetVertIDs      # Store back-reference to the reference vert so we can reconstruct the 3D mesh from the flat UV one. (add offset so default 0 means new vert)                     
                    
        bmUVF.verts.ensure_lookup_table()              ###LEARN: Added verts, need to run ensure_lookup_table() before we can access bmesh.verts collection
        bmUVB.verts.ensure_lookup_table()
        
        #=== Re-iterate through faces again to create faces in UV-domain mesh ===
        for oFace in bm3DS.faces:
            aVertsNewFaceUV = []
            for oLoop in oFace.loops:
                oUV = aLayer3DSUV[oLoop.index]
                vecUV = oUV.uv.freeze()                 ###LEARN: We must 'freeze' a vector before it can be inserted into a collection (its hash function needs non-mutable value)
                if (vecUV.x < 1):
                    nVertUVF = aMapUV2VertNewF[vecUV]
                    aVertsNewFaceUV.append(bmUVF.verts[nVertUVF])
                else:
                    nVertUVB = aMapUV2VertNewB[vecUV]
                    aVertsNewFaceUV.append(bmUVB.verts[nVertUVB])
            if (vecUV.x < 1):
                bmUVF.faces.new(aVertsNewFaceUV)
            else:
                bmUVB.faces.new(aVertsNewFaceUV)
        
        bmUVF.to_mesh(oMesh_UVF)
        bmUVB.to_mesh(oMesh_UVB)
        Util_HideMesh(self.oMeshO_UVF)
        Util_HideMesh(self.oMeshO_UVB)


        #===== DEFINE BODYSUIT SEAM CURVES (FOR SEAM TRAVESAL DURING CUTTING) =====
        bmClothSrc = bmesh.new()
        bmClothSrc.from_mesh(self.oMeshO_3DS.data)

        #=== Prepare seam curve definition by identifying seam curve beginnings and ends for KD tree search just below
        oTreeKD = kdtree.KDTree(10)         ###WEAK: Every bodysuit will have 10 seam boundary verts? (one curve from neck to hand upper, one from hand lower to exterior ankle, one from interio ankle to other ankle?
        for oEdge in bmClothSrc.edges:
            if oEdge.seam:                  ###IMPROVE: Call bpy.ops.uv.seams_from_islands() first? 
                for oVert in oEdge.verts:
                    if oVert.is_boundary:
                        oTreeKD.insert(oVert.co, oVert.index)
        oTreeKD.balance()

        #=== Define our six seam curves by searching for the nearest seam curve starting point ===
        CBodySuitSeamCurve.SeamCurve_CreateBothSides("Top",    self.aDictSeamCurves, oTreeKD, self.oMeshO_3DS, bmClothSrc, Vector((0.07, 0, 1.54)))      ###WEAK: Hardcoded position...
        CBodySuitSeamCurve.SeamCurve_CreateBothSides("Side",   self.aDictSeamCurves, oTreeKD, self.oMeshO_3DS, bmClothSrc, Vector((0.63, -0.05, 1.40)))
        CBodySuitSeamCurve.SeamCurve_CreateBothSides("Bottom", self.aDictSeamCurves, oTreeKD, self.oMeshO_3DS, bmClothSrc, Vector((0.02, 0.04, 0.08)))

        

class CBodySuitSeamCurve:       # CBodySuitSeamCurve: a seam chain in source bodysuit cloth.  Contains CBodySuitSeamCurvePt seam points along our chain.  Used to position UV-domain boolean cutting points for UV-based cloth cutting
    def __init__(self, sNameCurve, sSide, oTreeKD, oMeshO, bmCloth3DS, vecLocSearch):       ###TODO17: CBodySuit?  Too many args!
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
        for oEdge in bmCloth3DS.edges:          ###WEAK17: Why the heck is this required?
            oEdge.tag = False

        #=== Iterate through the seams chain beginning at vert self.nVertChainStart until we reach the end ===
        while oVertNow is not None:
            oVertNext = None
            for oEdge in oVertNow.link_edges:
                if oEdge.seam and (oEdge.tag == False):
                    oEdge.tag = True                        # Tag traversed edges as we go so we never go backward    ###BUG17:? Screws up future iterations?  reset tags?
                    oVertNext = oEdge.other_vert(oVertNow)
                    nVertChainOrdinal += 1
                    oPt = CBodySuitSeamCurvePt(nVertChainOrdinal, oVertNext, oPt, oMeshO, bmCloth3DS, aLayer3DSUV)
                    self.aChainPts.append(oPt)
                    break
            oVertNow = oVertNext
        #print("CBodySuitSeamCurve '{}' formed with {} points.".format(self.sNameCurve, len(self.aChainPts)))

    def GetPosAtSeamChainLength(self, bmCloth3DS, nLenChain):
        oPtPrev = None
        #print("GetPosAtSeamChainLength() searches for length " + str(nLenChain) + " with chain points: " + str(self.aChainPts))
        for oPt in self.aChainPts:
            if (oPt.nDistInChainUV > nLenChain):
                vecThisSegment = oPt.vecUVL - oPtPrev.vecUVL        ###TODO17: Array for high/low!
                nLenThisSegment = vecThisSegment.length
                if nLenThisSegment == 0:        ### Should not happen! 
                    raise Exception("###EXCEPTION: CBodySuitSeamCurve.GetPosAtSeamChainLength() has zero-length segment on seam curve " + self.sNameCurve)
                nLenRemainingForThisSegment = nLenChain - oPtPrev.nDistInChainUV
                nRatioNeededThisSegment = nLenRemainingForThisSegment / nLenThisSegment
                vecToAddThisSegment = vecThisSegment * nRatioNeededThisSegment 
                vecFinal = oPtPrev.vecUVL + vecToAddThisSegment      # Final position is start of previous point + interpolated distance to cover the remain (between two points)   
                #vec3D = Vector((vecFinal.x, vecFinal.y, 0))
                #G.Debug_AddMarker("T", "PLAIN_AXES", 0.005, vec3D, ((0,0,0)))
                #bpy.context.scene.cursor_location = vec3D
                return vecFinal 
            oPtPrev = oPt           # Remember previous point so we can interpolate once we find which two points are closest to required distance
            ###IMPROVE17: End of chain test
        raise Exception("###EXCEPTION: CBodySuitSeamCurve.GetPosAtSeamChainLength() could not find position for length ", nLenChain, len(self.aChainPts))
      

    @classmethod
    def SeamCurve_CreateBothSides(cls, sNameCurve, aDictSeamCurves, oTreeKD, oMeshO, bm, vecLocSearch):
        ###OBS17:? Simplifying assumption where Front / Back are X mirrored and coincident means we no longer need both sides!
        aDictSeamCurves[sNameCurve + "L"] = cls(sNameCurve, 'L', oTreeKD, oMeshO, bm, vecLocSearch)
        vecLocSearch.x = -vecLocSearch.x
        aDictSeamCurves[sNameCurve + "R"] = cls(sNameCurve, 'R', oTreeKD, oMeshO, bm, vecLocSearch)




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
        vecUV1 = setUniqueUVs.pop().copy()
        vecUV2 = setUniqueUVs.pop().copy()
        if (vecUV1.x < vecUV2.x):
            self.vecUVL = vecUV1
            self.vecUVH = vecUV2
        else: 
            self.vecUVH = vecUV1
            self.vecUVL = vecUV2

        #=== Calculate the UV distance traveled thus far in this chain ===
        if oPtPrev is not None:
            oPtPrev.nDistToNextPtUv = (self.vecUVL - oPtPrev.vecUVL).length         # Store the length to this point in PREVIOUS point
            self.nDistInChainUV = oPtPrev.nDistInChainUV + oPtPrev.nDistToNextPtUv  # Calculate where we are in our chain
            
        #print(self)

    def __expr__(self):          ###LEARN: How to override instance printing  See also __repr__()
        return str(self)
    def __str__(self):          ###LEARN: How to override instance printing  See also __repr__()
        return("- SeamCurvePt# {:3d} = {:4d} at {:3f} = {} - {}".format(self.nPointOrdinal, self.nVertID, self.nDistInChainUV, self.vecUVL, self.vecUVH))

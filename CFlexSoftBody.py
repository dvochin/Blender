#===============================================================================

###DOCS24: Aug 2017 - CFlexSoftBody
# === DEV ===
 
# === NEXT ===
 
# === TODO ===
 
# === LATER ===
 
# === OPTIMIZATIONS ===
 
# === REMINDERS ===
 
# === IMPROVE ===
 
# === NEEDS ===
 
# === DESIGN ===
 
# === QUESTIONS ===
 
# === IDEAS ===
 
# === LEARNED ===
 
# === PROBLEMS ===
 
# === WISHLIST ===


import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

from gBlender import *
from CMesh import *
from CBody import *
import G


class CFlexSoftBody():
    
    def __init__(self, oBody, nSoftBodyID, sNameSoftBody, sNameVertGrp_BoneParent, aListBonesToTakeOver, bPreventInnerParticleCreation = False):
        self.oBody                          = oBody
        self.nSoftBodyID                    = nSoftBodyID
        self.sNameSoftBody                  = sNameSoftBody
        self.sNameVertGrp_BoneParent        = sNameVertGrp_BoneParent
        self.aListBonesToTakeOver           = aListBonesToTakeOver
        self.bPreventInnerParticleCreation  = bPreventInnerParticleCreation
        self.oMeshSoftBody                  = None      # The CMesh created for this softbody shape.  It is sent to Unity and we manage its lifecycle.

        self.aParticleInfo          = CByteArray()      # Serialiazable array of super important particle information.  Tells Unity if a particle is skinned or simulated, what softbody ID it has, what bone it has, etc   
        self.aShapeVerts            = CByteArray()      # Serialiazable array of which vert / particle is also a shape
        self.aShapeParticleIndices  = CByteArray()      # Serialiazable flattened array of which shape match to which particle (as per Flex softbody requirements)
        self.aShapeParticleOffsets  = CByteArray()      # Serialiazable array storing cutoff in 'aShapeParticleIndices' between sets defining which particle goes to which shape. 
        self.aFlatMapBoneIdToShapeId= CByteArray()      # Serialiazable array storing what shapeID each bone has.  Flat map is a simple list of <Bone1>, <Shape1>, <Bone2>, <Shape2>, etc.

        self.oBody.AddSoftBody(self)
    
    def OnModifyParticles(self):
        print("- CFlexSoftBody.OnModifyParticles() called.  Nothing to do in base class")
        
    def DoDestroy(self):
        #=== Destroy the dynamic bones we added to our armature ===
        SelectObject(self.oBody.oArmNode.name) 
        bpy.ops.object.mode_set(mode='EDIT')
        Bones_RemoveBones(self.oBody.oArm, re.compile("\\" + G.C_Prefix_DynBones + self.sNameSoftBody))     ###WEAK: Adding '\' so the '+' is taken literally by regex 
        bpy.ops.object.mode_set(mode='OBJECT')

        #=== Destroy our CMesh ===        
        self.oMeshSoftBody.DoDestroy()


class CFlexSoftBodyPenis(CFlexSoftBody):
    
    def __init__(self, oBody, nSoftBodyID, sNameSoftBody, sNameVertGrp_BoneParent, aListBonesToTakeOver):
        self.vecVertUretra = Vector((0,0,0))
        super(self.__class__, self).__init__(oBody, nSoftBodyID, sNameSoftBody, sNameVertGrp_BoneParent, aListBonesToTakeOver, True)      ###INFO: How to call base class ctor.  Recommended over 'CSoftBodyBase.__init__(oBody, sSoftBodyPart)' (for what reason again??)
        
        
    def OnModifyParticles(self):
        print("- CFlexSoftBodyPenis.OnModifyParticles() called.   Adjusting cap particles")

        #=== Get uretra vertex.  It will locate penis center along its long axis (x, z) and the tip location along y ===
        oMeshBody = self.oBody.oMeshBody
        if self.oBody.oMeshBody.Open():
            oMeshBody.VertGrp_SelectVerts("_CPenis_Uretra")
            for oVert in self.oBody.oMeshBody.bm.verts:             ###OPT:! Sucks we have to iterate through all verts to find one!    ###IMPROVE: Maybe we can implement a 'marking system' in BodyPrep for these special verts so we can find them much more quickly?
                if oVert.select:
                    oVertUretra = oVert
                    break
            self.vecVertUretra = oVertUretra.co.copy()
            self.vecVertUretra.x = 0                     # Make sure we're centered
            self.oBody.oMeshBody.Close()

        #=== Find the closest vert / particle to real uretra and move it ===
        nDistToUretra_Min = sys.float_info.max
        oVertUretra_Closest = None
        if self.oMeshSoftBody.Open():
            for oVert in self.oMeshSoftBody.bm.verts:
                vecDelta = self.vecVertUretra - oVert.co.copy()
                nDistToUretra = vecDelta.magnitude
                if nDistToUretra_Min > nDistToUretra:
                    nDistToUretra_Min = nDistToUretra
                    oVertUretra_Closest = oVert
            #--- Move the uretra particle at the same height as real uretra and centered (where it is at length of penis untouched) --- 
            print("-> CFlexSoftBodyPenis() finds Uretra particle at #{}.".format(oVertUretra_Closest.index))            
            oVertUretra_Closest.co = Vector((0, oVertUretra_Closest.co.y, self.vecVertUretra.z))      ###CHECK: Could conceivably move particle too close to a neighbor and cause softbody instability!
            #--- Flag the uretra ---
            oLayFlexParticleInfo = self.oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
            oVertUretra_Closest[oLayFlexParticleInfo] |= CBody.C_ParticleInfo_BitFlag_Uretra
            self.oMeshSoftBody.Close()




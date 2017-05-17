###TODO: COrificeRig
#- Currently only one bone influence.  Bleed to two bones?
#- How to approach anus hole?
###BUG: Frequently rim 1 verts are set to origin!  WTF??
###BUG: Frequent crash of rig creation!!

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
from CBody import *
from CMesh import *



class COrificeRigVert():        # COrificeRigVert: Represents a vert (Blender) / Flex particle (Unity) in the COrificeRig.  Holds everything we need for Blender and Unity to process Flex collisions on the associated COrificeRig Flex collider mesh
    def __init__(self, nVert, vecLocation):
        self.sName              = "(Uninitialized)"
        self.nVert              = nVert
        self.vecLocation        = vecLocation
        self.vecFromCenter      = Vector((0,0,0))
        self.nAngle             = 0
        self.nDistFromCenter    = 0
        self.nSortedOrdinal     = 0
        self.oBoneEdit          = None
        self.oVertGrp           = None
        self.nVertInFlexCollider = -1                   # Our vert ID in the generated Flex collider
    
    def CalcAngleAndDistance(self, vecCenter):
        self.vecFromCenter      = self.vecLocation - vecCenter
        self.nDistFromCenter    = self.vecFromCenter.length
        self.nAngle             = degrees(atan2(self.vecFromCenter.y, self.vecFromCenter.x))           # Tan(nAngle) = Opp / Adj = y / x so nAngle = atan(y / x)
        if self.nAngle < 0:
            self.nAngle = self.nAngle + 360 

    def Serialize(self, oBA):                       # Serialize all our fields into floats in the supplied CByteArray() for Unity to de-serialize
        oBA.AddVector(self.vecLocation)
    
    def __str__(self):
        return("COrificeRigVert  #{:2d}  nVert={:5d}  Ang={:5.1f}  Dist={:5.3f}  Loc={:6.3f},{:6.3f},{:6.3f}".format(self.nSortedOrdinal, self.nVert, self.nAngle, self.nDistFromCenter, self.vecLocation.x, self.vecLocation.y, self.vecLocation.z))




class COrificeRig():            # COrificeRig: Blender class to modify bones and skinning of a mesh to enable credible penetration during gameplay
    INSTANCE = None             # We're a singleton so set our single instance in our INSTANCE static for convenience once initialized
    s_nRings = 3                # Number of 'rings' defined in the mesh around the orifice hole.  Determines how many rings of geometry the generated Flex collider will have 
    
    def __init__(self, nVertsPerRing, nDistMax, bDebugVisualize = False):
        self.nVertsPerRing   = nVertsPerRing
        self.nDistMax       = nDistMax

        self.vecCenter           = Vector((0,0,0))
        self.nNumOrificeRigVert  = 0
        self.oBoneRoot           = None
        self.aOrificeRigVerts   = []                    # Our collection of 'rings'.  Each slot in 'self.aOrificeRigVerts' is a 'COrificeRigVert[]' that stores the COrificeRigVert for that ring, nAngleID.  Serialized to Unity for create of the Flex collsion rig there
        
        COrificeRig.INSTANCE   = self


        mapOrificeRigVert = {}
        sVertGroupNamePrefix = "_CVagina_Ring"
        nDegreesPerSlice = 360 / self.nVertsPerRing
        

        oMesh = CMesh.CreateFromExistingObject("WomanA")
        SelectAndActivate(oMesh.GetName())
    
        #=== First determine the IMPORTANT center of opening from Ring0.  Central to everything! ===
        VertGrp_SelectVerts(oMesh.GetMesh(), sVertGroupNamePrefix + "0")
        bpy.ops.object.mode_set(mode='OBJECT')
        self.vecCenter = Vector((0,0,0))
        nVertsInOpening = 0
        for oVert in oMesh.GetMesh().data.vertices:
            if oVert.select == True:
                self.vecCenter = self.vecCenter + oVert.co
                nVertsInOpening = nVertsInOpening + 1
        self.vecCenter = self.vecCenter / nVertsInOpening
        print("=== COrificeRig: Center of opening is at " + str(self.vecCenter))
        #bpy.data.objects["Debug-Vagina-Opening-Center"].location = self.vecCenter
    
        #=== Iterate through each ring to pick which vert we want to keep to form the simplified Flex collider mesh from the presentation geometry ===   
        for nRing in range(COrificeRig.s_nRings):
            sVertGroupName = sVertGroupNamePrefix + str(nRing)
            VertGrp_SelectVerts(oMesh.GetMesh(), sVertGroupName)
            bpy.ops.object.mode_set(mode='OBJECT')          ###LEARN: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
    
            self.aOrificeRigVertThisRing = []
            for oVert in oMesh.GetMesh().data.vertices:
                if oVert.select == True:
                    oORV = COrificeRigVert(oVert.index, oVert.co)
                    self.aOrificeRigVertThisRing.append(oORV)
        
            for oORV in self.aOrificeRigVertThisRing:
                oORV.CalcAngleAndDistance(self.vecCenter)
                #print(oORV)
        
            self.aOrificeRigVert = []
            for nSlice in range(self.nVertsPerRing):
                nAngleWanted = nSlice * nDegreesPerSlice
                vecWanted = Vector((0,0))                   # For a vector to express the angle we want so we can use dot-product search
                vecWanted.x = cos(radians(nAngleWanted))    # cos(nAngle) = adj / hyp = x / nRadius so x = nRadius * cos(nAngle)
                vecWanted.y = sin(radians(nAngleWanted))    # sin(nAngle) = opp / hyp = y / nRadius so y = nRadius * sin(nAngle)
                
                oORVClosest = None          
                nAngleDiffClosestThusFar = 180
                for oORV in self.aOrificeRigVertThisRing:
                    vecFromCenter2D = Vector((oORV.vecFromCenter.x, oORV.vecFromCenter.y))        ###WEAK Flatten to 2D.  Find for vagina but anus at an angle would cause distortion!  Better would be for ring to allow for rotation!
                    nAngleDiff = degrees(vecFromCenter2D.angle(vecWanted))
                    if nAngleDiffClosestThusFar > nAngleDiff:
                        nAngleDiffClosestThusFar = nAngleDiff
                        oORVClosest = oORV                        ###BUG?: Algorithm can pick he same vert for multiple slots!
                
                print("- Ring{:1d} OrificeRigVert at angle {:5.1f} chosen to represent angle {:5.1f} with a diff of {:5.2f}".format(nRing, oORVClosest.nAngle, nAngleWanted, nAngleDiffClosestThusFar))            
                self.aOrificeRigVert.append(oORVClosest)          # Chose this OrificeRigVert to participate in our Flex collider
                
            self.aOrificeRigVerts.append(self.aOrificeRigVert)                # Append the fully-formed ring to our matrix of rings
    
    
        #=== Optionally create a Blender-only mesh to visualize the Flex collider in Unity.  (It is a heavily-simplified version of presentation mesh in the orifice area) ===
        if bDebugVisualize:
            sNameMeshUnity2Blender = "COrificeRig_FlexCollider"
            oMeshD = bpy.data.meshes.new(sNameMeshUnity2Blender)
            oMeshO = bpy.data.objects.new(oMeshD.name, oMeshD)
            bpy.context.scene.objects.link(oMeshO)
            aVerts = []
            aFaces = []
            for aOrificeRigVert in self.aOrificeRigVerts:
                for oORV in aOrificeRigVert:
                    oORV.nVertInFlexCollider = len(aVerts) 
                    aVerts.append(oORV.vecLocation)
            
            for nRing in range(COrificeRig.s_nRings-1):
                for nAngle in range(self.nVertsPerRing):
                    nAnglePlus0 = nAngle + 0
                    nAnglePlus1 = nAngle + 1
                    if nAnglePlus1 >= self.nVertsPerRing:
                        nAnglePlus1 = 0
                    oORV00 = self.aOrificeRigVerts[nRing+0][nAnglePlus0]
                    oORV01 = self.aOrificeRigVerts[nRing+0][nAnglePlus1]
                    oORV10 = self.aOrificeRigVerts[nRing+1][nAnglePlus0]
                    oORV11 = self.aOrificeRigVerts[nRing+1][nAnglePlus1]
                    aFace = [oORV00.nVertInFlexCollider, oORV01.nVertInFlexCollider, oORV11.nVertInFlexCollider, oORV10.nVertInFlexCollider]
                    aFaces.append(aFace)
                    
            oMeshD.from_pydata(aVerts, [], aFaces)
            oMeshD.update()
            oMeshO.draw_type = "WIRE"        
            oMeshO.show_wire = oMeshO.show_all_edges = oMeshO.show_x_ray = True
            SetParent(oMeshO.name, G.C_NodeFolder_Temp)
        



    def AdjustAreaSkinWeights(self):
        sNameBoneRoot = "Genitals"
        
        mapOrificeRigVert = {}
    
        oMesh = CMesh.CreateFromExistingObject("WomanA")
        SelectAndActivate(oMesh.GetMesh().name)
#         VertGrp_SelectVerts(oMesh.GetMesh(), "_CVagina_Ring0")
#         bpy.ops.object.mode_set(mode='OBJECT')          ###LEARN: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
#         self.vecCenter = Vector((0,0,0))
#         nVertsInOpening = 0
#         for oVert in oMesh.GetMesh().data.vertices:
#             if oVert.select == True:
#                 oORV = COrificeRigVert(oVert.index, oVert.co)
#                 self.aOrificeRigVert.append(oORV)
#                 self.vecCenter = self.vecCenter + oVert.co
#                 nVertsInOpening = nVertsInOpening + 1
#         self.vecCenter = self.vecCenter / nVertsInOpening
#         bpy.data.objects["Debug-Vagina-Opening-Center"].location = self.vecCenter
#         print("- Center of vagina opening is " + str(self.vecCenter))
#    
#         for oORV in self.aOrificeRigVert:
#             oORV.CalcAngleAndDistance(self.vecCenter)
    
        aOrificeRigVertRing0 = sorted(self.aOrificeRigVerts[0], key=lambda oORV: oORV.nAngle)     ###LEARN: How to sort class instances by a given key
        nSortedOrdinal = 0
        for oORV in aOrificeRigVertRing0:
            mapOrificeRigVert[oORV.nVert] = oORV
            oORV.nSortedOrdinal = nSortedOrdinal                # Remember what sorted ordinal we are
            nSortedOrdinal = nSortedOrdinal + 1
            print(oORV)
        self.nNumOrificeRigVert = nSortedOrdinal
    
    
        
        SelectAndActivate(oMesh.GetMesh().parent.name)                           # Must select armature object... 
        bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
        oArm = oMesh.GetMesh().modifiers["Armature"].object.data
    
    
        #=== Modify the vagina root bone (created during BodyImporter) ===
#         self.oBoneRoot = oArm.edit_bones.new("VaginaBones")
#         self.oBoneRoot.parent = oArm.edit_bones[sNameBoneRoot]                 ###BUG19: What about Anus?
        self.oBoneRoot = oArm.edit_bones["Vagina"]
        self.oBoneRoot.head = self.vecCenter
        self.oBoneRoot.tail = self.vecCenter + Vector((0,0,0.001))            ###DEV19!!!!
        self.oBoneRoot.use_connect = False
        self.oBoneRoot.envelope_distance = self.oBoneRoot.envelope_weight = self.oBoneRoot.head_radius = self.oBoneRoot.tail_radius = 0
        self.oBoneRoot.envelope_distance = 0.001
        self.oBoneRoot = self.oBoneRoot
    
        sNameBonePrefix = "VaginaBone"
        nBone = 0
        for oORV in aOrificeRigVertRing0:
            oORV.sName = sNameBonePrefix + str(nBone).zfill(2)
            oBoneEdit = oArm.edit_bones.new(oORV.sName)
            oBoneEdit.parent = self.oBoneRoot
            oBoneEdit.head = oORV.vecLocation
            oBoneEdit.tail = oORV.vecLocation + Vector((0,0,0.001))                ###LEARN: A bone *must* have different head and tail otherwise it gets deleted without warning = DUMB!
            oBoneEdit.use_connect = False
            oBoneEdit.envelope_distance = oBoneEdit.envelope_weight = oBoneEdit.head_radius = oBoneEdit.tail_radius = 0
            oBoneEdit.envelope_distance = 0.001
            oORV.oBoneEdit = oBoneEdit
            nBone = nBone + 1
    
    
    
        #=== Create the vertex groups to store the new bone weights for vagina radial expansion bones ===
        SelectAndActivate(oMesh.GetName()) 
        oMesh = CMesh.CreateFromExistingObject("WomanA")
    
#         #=== Obtain reference to the vertex groups where we must scale weights down.  These are: Genitals, Anus, pelvis, xThighBend, xThighTwist ===
#         aVertGrpsScaleDownWeights = []
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), sNameBoneRoot))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "Anus"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "pelvis"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "lThighBend"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "rThighBend"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "lThighTwist"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "rThighTwist"))
    
        for oORV in aOrificeRigVertRing0:
            oORV.oVertGrp = oMesh.GetMesh().vertex_groups.new(oORV.sName)
    
    
        #=== Select all vagina verts and iterate through each one to set what bones it belongs to and at what weight ===
        VertGrp_SelectVerts(oMesh.GetMesh(), "_CVagina_Area")
        bpy.ops.object.mode_set(mode='OBJECT')          # We must remain in object mode for bone weight editing!
        bm = oMesh.Open()
    
        #=== Determine the verts within range ===
        aVertsInGroup = [oVert for oVert in bm.verts if oVert.select]
        aVertsInRange = []        
        aVertsInRangeDist = []
        aVertsInRangeOpening = []
        nVertExamined = 0
        
        for oVert in aVertsInGroup:
            vecFromOpeningCenter = oVert.co - self.vecCenter
            nDistApprox = vecFromOpeningCenter.length
            if nDistApprox < self.nDistMax:
                
                nAngle = degrees(atan2(vecFromOpeningCenter.y/1, vecFromOpeningCenter.x))         ###DEV19: Flatten circle??
                if nAngle < 0:
                    nAngle = 360 + nAngle
        
                oORV1 = aOrificeRigVertRing0[len(aOrificeRigVertRing0)-1]     # Our vert opening is last one unless loop below finds lower angle
                for oORV in aOrificeRigVertRing0:
                    if nAngle < oORV.nAngle:
                        oORV1 = oORV
                        break
                oVertOrificeRigVert1 = bm.verts[oORV1.nVert]
                #nDist = Util_CalcSurfDistanceBetweenTwoVerts(bm, oVert, oVertOrificeRigVert1)
                nDist = (oVert.co - oVertOrificeRigVert1.co).length
                aVertsInRange.append(oVert.index)
                aVertsInRangeDist.append(nDist)
                aVertsInRangeOpening.append(oORV1)
        
                nVertExamined = nVertExamined + 1
                if (nVertExamined % 20) == 0:
                    print("- Examined {:4d} verts and found {:4d}".format(nVertExamined, len(aVertsInRange)))
    #             if len(aVertsInRange) > 150:
    #                 break
            
            #else:
            #    print("- Skipping vert " + str(oVert.index))
    
        #=== Iterate through verts in range to set their weights ===
        bpy.ops.object.mode_set(mode='OBJECT')          # We must be in object mode for bone weight editing!
        print("\n===== CREATE VAGINA RADIAL BONES =====")
        for i in range(len(aVertsInRange)):
            nVert = aVertsInRange[i]
            nDist = aVertsInRangeDist[i]
            oORV1 = aVertsInRangeOpening[i]
    
            oVert = oMesh.GetMesh().data.vertices[nVert]
    
    #         vecVertDiff = oVert.co - self.vecCenter
    #         
    #         oORV1 = None
    #         for oORV in aOrificeRigVertRing0:
    #             if nAngle < oORV.nAngle:
    #                 oORV1 = oORV
    #                 break
               
    #         nOrificeRigVert2 = oORV1.nSortedOrdinal + 1
    #         if nOrificeRigVert2 >= len(aOrificeRigVertRing0):             # Wrap around o zero if oORV1 was the last in our sorted array
    #             nOrificeRigVert2 = 0
    #         oORV2 = mapOrificeRigVert[nOrificeRigVert2] 
    
            oVertOrificeRigVert1 = oMesh.GetMesh().data.vertices[oORV1.nVert]
            #nDist = Util_CalcSurfDistanceBetweenTwoVerts(bm, oVert, oVertOrificeRigVert1)
            nDistRatio = nDist / self.nDistMax
            nWeightGoal = (cos(nDistRatio*pi) + 1) / 2             # Convert linear ratio to smooth curve (cos(x) from 0 to pi gives smooth curve) 
    
    #         nAngle1 = oORV1.nAngle                      ###OPT: Really need dual bone weight if we have many bones??
    #         nAngle2 = oORV2.nAngle
    #         if nAngle1 > nAngle2:
    #             nAngle2 = nAngle2 + 360
    #         nAngleDiff = nAngle2 - nAngle1
    # 
    #         nDiffWithAngle1 = nAngle  - nAngle1
    #         nDiffWithAngle2 = nAngle2 - nAngle
    
            #=== Calculate the sum of the weights for the bones we can modify ===
            nWeightSumOfExistingWeCanChange = 0
            for oVertGrpElem in oVert.groups:
                oVertGrp = oMesh.GetMesh().vertex_groups[oVertGrpElem.group]
                if oVertGrp.name.find("Thigh") == -1:
                    nWeightSumOfExistingWeCanChange = nWeightSumOfExistingWeCanChange + oVertGrpElem.weight
            nWeightPossibleToChange = nWeightGoal * nWeightSumOfExistingWeCanChange 
            
            #=== First scale down the weights of the vertex groups already influencing this vertex ===
            nWeightForOtherVertGrpsWeCanChange = 1 - nWeightPossibleToChange
            for oVertGrpElem in oVert.groups:
                oVertGrp = oMesh.GetMesh().vertex_groups[oVertGrpElem.group]
                if oVertGrp.name.find("Thigh") == -1:
                    oVertGrpElem.weight = oVertGrpElem.weight * nWeightForOtherVertGrpsWeCanChange
             
            #nBone2_Remainder = nBone - nBone1
            #nBone1_Remainder = 1 - nBone2_Remainder
            oORV1.oVertGrp.add([nVert], nWeightPossibleToChange, 'ADD')
            #aVertGroups[nBone2].add([nVert], nWeight * nBone2_Remainder, 'ADD')

#             for oVertGrpScaleDown in aVertGrpsScaleDownWeights:
#                 if nVert in oVertGrpScaleDown:
#                     try:
#                         nWeightPrevious = oVertGrpScaleDown.weight(nVert)
#                         nWeightReduced = nWeightPrevious * nWeightForOtherVertGrps 
#                         oVertGrpScaleDown.add([nVert], nWeightReduced, 'REPLACE')
#                     except RuntimeError:                            # weight() returns a RuntimeError if vertex not found in groups ###IMPROVE: Find better way to find vert inclusion!
#                         nWeightPrevious = 0
                
            #print("- Vert#{:5d}   A={:5.1f}   D={:5.3f}   DR={:5.3f}   W={:5.3f}   1={:2d}/{:4.2f}   2={:2d}/{:4.2f}".format(oVert.index, nAngle, nDist, nDistRatio, nWeight, 0, 0, 0, 0))
            
        print("======================================\n")
        #bm = oMesh.Close()



    def Test_MoveBones(self, nRatio):            # from BlenderPanel import *; BoneMove(1)
        # Mandingo has 6" girth = 15.24cm girth = 4.85cm diameter = 2.4cm radius.  Shane Diesel is 7.25" girth = 18.415cm girth = 5.86 cm diam = 2.93 cm radius
        oMeshO = SelectAndActivate("[WomanA]") 
        bpy.ops.object.mode_set(mode='POSE')
    
        for oORV in self.aOrificeRigVerts[0]:          ###DEV19!!!!!!!: Just affect radially from angle (fuck the delta vector!
    #         vecBone = oORV.vecFromCenter * nRatio
    #         vecBone2D = Vector((vecBone.x, 0, -vecBone.y))          ###HACK! Fucked up conversion as pose is zero-based (0 = back to idle pose)... but why the rotation???
            nAngleRad = radians(oORV.nAngle)
            x = nRatio * cos(nAngleRad)            # cos(nAngle) = adj / hyp = x / nRadius so x = nRadius * cos(nAngle)
            y = nRatio * sin(nAngleRad)            # sin(nAngle) = opp / hyp = y / nRadius so y = nRadius * sin(nAngle)
            vecBone2D = Vector((x, 0, -y))
            oBoneIndex = oMeshO.pose.bones.find(oORV.sName)
            oBone = oMeshO.pose.bones[oBoneIndex]                   ###OPT: Could remember bone index?  Can change?
            oBone.location = vecBone2D
            #oBoneEdit.scale = Vector((nRatio, nRatio, nRatio))            ###LEARN: connecting opening vert bones to a centered parents and scaling doesn't work well (doesn't appear to move mesh vertices as moving bones did properly before)
            #print("-Moving bone '{}'".format(oORV.sName))
    
        bpy.ops.object.mode_set(mode='OBJECT')
        oMeshO.hide = True


    def SerializeOrificeRig(self):                          # Serialize our aVertRimInfos into a CByteArray() for Unity to de-serialize
        oBA = CByteArray()
        oBA.AddFloat(COrificeRig.s_nRings)              
        oBA.AddFloat(self.nVertsPerRing)              
        for self.aOrificeRigVert in self.aOrificeRigVerts:
            for oORV in self.aOrificeRigVert:
                oORV.Serialize(oBA)
        return oBA.Unity_GetBytes()

###DOCS24: June 2017 - CHoleRig
# === DEV ===
#- must make woman from woman source?
#- game sourcing from woman and test code woman source??
#- ba-rig reparenting?
#- CHoleRig creation flow assumes CBody... Separate from that so we can have ship-time flow?
#- CHOleRig output needs reparenting... also is it really created at gametime??
#
# === MOVE ===
# Use 'tris to quads' on flex collider so that we can use quads at runtime!
    # Pushing a bit might help?
# Will need to have intelligent fluid cycling once all particles have been exhausted by a cum.  Cannot make it run a long time as it kills performance when more colliders are activated!
    # Make cum more and more transparent, the remove it altogether, reset the colliders and pause the fluid solver until the next cum

#
# === TODO ===
# Verify smooth doesn't screw things up... limit??  normalize??  lock??
# Decimation of vagina inner (and anus!) at ship-time?
    # Need to store stuff in mesh variables?
    # Need to close open vagina inside, get rid of extra geometry, get rid of anus inside, etc... all when we get to ship-time 

# === LATER ===
# 
# === OPTIMIZATIONS ===
# 
# === REMINDERS ===
# 
# === IMPROVE ===
# Currently only one bone influence.  Bleed to two bones?
# Add capacity to use existing bones (or delete entire branch first?)
# 
# === NEEDS ===
# 
# === DESIGN ===
# 
# === QUESTIONS ===
# Converge vagina depth verts into one vert?  (Would it not interfere with penis??)
# 
# === IDEAS ===
# +++ We should start integrating all the collider mesh into one central architecture to unify the resultant as one mesh.  (e.g. integrate special needs of penis, vagina, breasts etc) with links to custom info each type requires
# Could create extra geometry before vert search so we get unique verts
# Spread legs when reskinning vagina!
# 
# === LEARNED ===
# 
# === PROBLEMS ===
# Why all these 'unsharing mesh' from our Blender extension???
# Uretra distorts when stretched... what to do??
# 
# === WISHLIST ===
#- How to approach anus hole?  Mouth?
#

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



class CHoleRigVert():        # CHoleRigVert: Represents a vert (Blender) / Flex particle (Unity) in the CHoleRig.  Holds everything we need for Blender and Unity to process Flex collisions on the associated CHoleRig Flex collider mesh
    def __init__(self, nVert, vecLocation):
        self.sName = CFlexRig.CBodyBase.C_Prefix_DynBone_Vagina + str(nVert).zfill(3)
        self.nVert                  = nVert
        self.vecLocation            = vecLocation
        self.vecFromCenter          = Vector((0,0,0))
        self.nAngle                 = 0
        self.oVertGrp               = None
    
    def CalcAngleAndDistance(self, vecCenter):
        self.vecFromCenter      = self.vecLocation - vecCenter
        self.nDistFromCenter    = self.vecFromCenter.length
        self.nAngle             = degrees(atan2(self.vecFromCenter.y, self.vecFromCenter.x))           # Tan(nAngle) = Opp / Adj = y / x so nAngle = atan(y / x)
        if self.nAngle < 0:
            self.nAngle = self.nAngle + 360
             
    def __str__(self):
        return("CHoleRigVert  '{}' nVert={:5d}  Ang={:5.1f}  Dist={:5.1f}  Loc={:6.3f},{:6.3f},{:6.3f}".format(self.sName, self.nVert, self.nAngle, self.nDistFromCenter, self.vecLocation.x, self.vecLocation.y, self.vecLocation.z))





class CHoleRig():               # CHoleRig: Blender class to modify bones and skinning of a mesh to enable credible penetration during gameplay
    C_NameVertGroup_Vagina      = "_CVagina_Opening"                    # Name of the vertex groups representing the vagina opening verts

    
    def __init__(self, sNameMeshSrc, nDistMax):
        self.oMeshSrc           = CMesh.Create(sNameMeshSrc)
        self.nDistMax           = nDistMax
        
        self.oMeshHoleRig       = None                  # The hole rig mesh we construct and serialize to Unity 
        self.vecCenter          = Vector((0,0,0))
        self.nNumHoleRigVert    = 0
        self.oBoneRoot          = None
        self.aHoleRigVerts      = []                    # List of all the 'ring 0' rig verts that will drive bones.  The value is the original vert position before pull-back
        self.C_FlexParticleRadius = 0.01 * 0.85      ###WEAK24:!!! Copy of Unity's super-important CGame.INSTANCE.particleDistance / 2.  Need to 'pull back' the bones by the particle radius so collisions appear to be made at skin level instead of past it.  Since this value rarely changes this 'copy' is tolerated here but in reality the rig must be redone everytime this value chaanges.  ###TUNE: What ratio?


        
        #===== A. DETERMINE VAGINA OPENING VERTEX POSITIONS =====        
        #=== Remember the position of the ring 0 verts before we pull back.  These will be our bones ===
        bmBody = self.oMeshSrc.Open()
        self.vecCenter = Vector((0,0,0))
        nBoneID = 0
        VertGrp_SelectVerts(self.oMeshSrc.GetMesh(), CHoleRig.C_NameVertGroup_Vagina)
        for oVert in bmBody.verts:
            if oVert.select:
                self.aHoleRigVerts.append(CHoleRigVert(nBoneID, oVert.co.copy()))
                self.vecCenter = self.vecCenter + oVert.co.copy()
                nBoneID += 1
        self.vecCenter /= nBoneID
        bmBody = self.oMeshSrc.Close()

        #=== Calculate angle and distance for each bone (now that center is known) ===        
        for oORV in self.aHoleRigVerts:
            oORV.CalcAngleAndDistance(self.vecCenter)
        



        #===== B. ADD BONES =====        
        #=== Remove bones that start with the specified bone name prefix ===
        oArmObject = self.oMeshSrc.GetMesh().modifiers["Armature"].object
        oArm = oArmObject.data
        Bones_RemoveBonesWithNamePrefix(oArm, CFlexRig.CBodyBase.C_Prefix_DynBone_Vagina)            ###DEV24E: Needed?

        #=== Obtain reference to bones ===
        SelectObject(oArmObject.name)                  # Must select armature object... 
        bpy.ops.object.mode_set(mode='EDIT')                #... and then place it in edit mode for us to be able to view / edit bones
    
        #=== Modify the vagina root bone (created during BodyImporter) ===        ###DEV24:???
#         self.oBoneRoot = oArm.edit_bones.new("+VaginaBones")
#         self.oBoneRoot.parent = oArm.edit_bones[sNameBoneRoot]                 ###BUG19: What about Anus?
        sNameBoneRoot = "Genitals"              ###DEV24:!!! We *must* clarify usage of this bone between Blender and Unity for all 3 sexes!!
        self.oBoneRoot = oArm.edit_bones[sNameBoneRoot]
        self.oBoneRoot.head = self.vecCenter
        self.oBoneRoot.tail = self.vecCenter + Vector((0,0,-0.001))
        self.oBoneRoot.use_connect = False
        self.oBoneRoot.envelope_distance = self.oBoneRoot.envelope_weight = self.oBoneRoot.head_radius = self.oBoneRoot.tail_radius = 0
        self.oBoneRoot.envelope_distance = 0.001
        self.oBoneRoot = self.oBoneRoot
    
        nBone = 0
        for oHoleRigVert in self.aHoleRigVerts:
            oBoneEdit = oArm.edit_bones.new(oHoleRigVert.sName)
            oBoneEdit.parent = self.oBoneRoot
            oBoneEdit.head = oHoleRigVert.vecLocation.copy()
            vecFromCenter = oHoleRigVert.vecLocation- self.vecCenter          # Orient each vagina bone away from its center so runtime PhysX spring joint can spring in the direction of opening
            oBoneEdit.tail = oBoneEdit.head + (vecFromCenter * 0.05)                ###INFO: A bone *must* have different head and tail otherwise it gets deleted without warning = DUMB!
            oBoneEdit.use_connect = False
            oBoneEdit.envelope_weight = oBoneEdit.head_radius = oBoneEdit.tail_radius = 0
            oBoneEdit.envelope_distance = 0.001
            nBone = nBone + 1
    
        
        
        #===== C. SET BONE WEIGHTS ======        ###DEV24F:!!!! use new techniques for smoothing?
        #=== Create the vertex groups to store the new bone weights for vagina radial expansion bones ===
        SelectObject(self.oMeshSrc.GetName()) 
    
        for oHoleRigVert in self.aHoleRigVerts:
            oHoleRigVert.oVertGrp = self.oMeshSrc.GetMesh().vertex_groups.new(oHoleRigVert.sName)

        #=== Select all vagina verts and iterate through each one to set what bones it belongs to and at what weight ===
        VertGrp_SelectVerts(self.oMeshSrc.GetMesh(), "_CVagina_AreaBig")
        bpy.ops.object.mode_set(mode='OBJECT')          # We must remain in object mode for bone weight editing!
        bmBody = self.oMeshSrc.Open()
    
        #=== Determine the verts within range ===
        aVertsInGroup = [oVert for oVert in bmBody.verts if oVert.select]
        aVertsInRange = []              ###IMPROVE:? Three parallel collections?  Use one with a helper object instead?        
        aVertsInRangeDist = []
        aVertsHoleRigVert = []
        
        for oVert in aVertsInGroup:
            vecVert = oVert.co.copy()
            vecFromOpeningCenter = vecVert - self.vecCenter
            nDistApprox = vecFromOpeningCenter.length
            if nDistApprox < self.nDistMax:
                
                nAngle = degrees(atan2(vecFromOpeningCenter.y, vecFromOpeningCenter.x))         ###DEV19: Flatten circle??
                if nAngle < 0:
                    nAngle = 360 + nAngle

                oHoleRigVert_Closest = None     ###DEV24:!!!!! Used to search for entry with one angle smarller... now by closest  self.aHoleRigVerts[len(self.aHoleRigVerts)-1]     # Our vert opening is last one unless loop below finds lower angle
                nAngleDiff_Closest = sys.float_info.max
                for oHoleRigVert in self.aHoleRigVerts:
                    nAngleDiff = abs(nAngle - oHoleRigVert.nAngle)
                    if nAngleDiff_Closest > nAngleDiff:
                        nAngleDiff_Closest = nAngleDiff                    ###BUG24:??? Wrap around 360 bug??
                        oHoleRigVert_Closest = oHoleRigVert
                #oVertHoleRigVert = bmBody.verts[oHoleRigVert_Closest.nVert]
                nDist = (vecVert - oHoleRigVert_Closest.vecLocation).length
                aVertsInRange.append(oVert.index)
                aVertsInRangeDist.append(nDist)
                aVertsHoleRigVert.append(oHoleRigVert_Closest)
        bmBody = self.oMeshSrc.Close()
            
    
        #=== Iterate through verts in range to set their weights ===
        bpy.ops.object.mode_set(mode='OBJECT')          # We must be in object mode for bone weight editing!
        oMesh = self.oMeshSrc.GetMeshData()
        print("\n===== CREATE RADIAL BONES =====")
        for i in range(len(aVertsInRange)):
            nVert = aVertsInRange[i]
            nDist = aVertsInRangeDist[i]
            oHoleRigVert = aVertsHoleRigVert[i]
            oVert = oMesh.vertices[nVert]
            nDistRatio = nDist / self.nDistMax
            nWeightGoal = (cos(nDistRatio*pi) + 1) / 2             # Convert linear ratio to smooth curve (cos(x) from 0 to pi gives smooth curve) 
    
            #=== Calculate the sum of the weights for the bones we can modify ===
            nWeightSumOfExistingWeCanChange = 0
            for oVertGrpElem in oVert.groups:
                oVertGrp = self.oMeshSrc.GetMesh().vertex_groups[oVertGrpElem.group]
                if oVertGrp.name.find("Thigh") == -1:                                           ###WEAK24:!!!! This code crap!  Switch to new smoothing techniques from CBodyBase!!
                    nWeightSumOfExistingWeCanChange = nWeightSumOfExistingWeCanChange + oVertGrpElem.weight
            nWeightPossibleToChange = nWeightGoal * nWeightSumOfExistingWeCanChange 
            
            #=== First scale down the weights of the vertex groups already influencing this vertex ===
            nWeightForOtherVertGrpsWeCanChange = 1 - nWeightPossibleToChange
            for oVertGrpElem in oVert.groups:
                oVertGrp = self.oMeshSrc.GetMesh().vertex_groups[oVertGrpElem.group]
                if oVertGrp.name.find("Thigh") == -1:
                    oVertGrpElem.weight = oVertGrpElem.weight * nWeightForOtherVertGrpsWeCanChange
             
            oHoleRigVert.oVertGrp.add([nVert], nWeightPossibleToChange, 'ADD')
            #print("--Adding vert {} with weight {}".format(nVert, nWeightPossibleToChange))
        
        #=== Smooth bone area we've modified ===
#         bpy.ops.object.mode_set(mode='EDIT')        ###TODO24: ###BROKEN: Messes up vertex groups!  Smoothing done at end of ship-time body prep now!
#         VertGrp_SelectVerts(self.oMeshSrc.GetMesh(), "_CVagina_AreaBig")
#         bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=1.0, repeat=2)       ###TUNE:!!!  ###DEV24:!!!! Keep?  messes up body??  Add normalize after?  NOW SHIP TIME!  Fix at last possible step!!  (Damages other groups!)  ###INFO: vertex_group_smooth() trashes even locked vertex groups!! WTF???    
#         bpy.ops.object.mode_set(mode='OBJECT')
        
        print("- CHoleRig completed successfully.\n")


    def Test_MoveBones(self, nRatio):            # from BlenderPanel import *; BoneMove(1)
        ###BROKEN: Can't move properly now that bones / angles changed.
        # Mandingo has 6" girth = 15.24cm girth = 4.85cm diameter = 2.4cm radius.  Shane Diesel is 7.25" girth = 18.415cm girth = 5.86 cm diam = 2.93 cm radius
        
        oMeshO = SelectObject(self.oMeshSrc.GetMesh().modifiers["Armature"].object.name)      ###INFO: How to obtain parent armature from a mesh!  ###TODO24:!! Implement thorugh codebase! 
        bpy.ops.object.mode_set(mode='POSE')
    
        for oHoleRigVert in self.aHoleRigVerts:     ###DEV19!!!!!!!: Just affect radially from angle (fuck the delta vector!
            # Note: Old approach not based on hole rig pre-calculated vector from center = less precise
            #nAngleRad = radians(oHoleRigVert.nAngle)
            #x = nRatio * cos(nAngleRad)            # cos(nAngle) = adj / hyp = x / nRadius so x = nRadius * cos(nAngle)
            #y = nRatio * sin(nAngleRad)            # sin(nAngle) = opp / hyp = y / nRadius so y = nRadius * sin(nAngle)
            
            vecBone2D = Vector((oHoleRigVert.vecFromCenter.x * nRatio, 0, oHoleRigVert.vecFromCenter.y * nRatio))
            oBoneIndex = oMeshO.pose.bones.find(oHoleRigVert.sName)
            oBone = oMeshO.pose.bones[oBoneIndex]                   ###OPT: Could remember bone index?  Can change?
            oBone.location = vecBone2D
            #oBoneEdit.scale = Vector((nRatio, nRatio, nRatio))            ###INFO: connecting opening vert bones to a centered parents and scaling doesn't work well (doesn't appear to move mesh vertices as moving bones did properly before)
            #print("-Moving bone '{}'".format(oHoleRigVert.sName))
    
        bpy.ops.object.mode_set(mode='OBJECT')
        oMeshO.hide = True


###OBS24: Much better vagina hole collider now integrated into CBodyBase
#     def SerializeHoleRig(self):        # Construct our flattened vert-to-vert array serialized to Unity so it can easily construct its structures without figuring what vert connects to what ===
#         oBA = CByteArray()             # Flattened array of which vert connects to what vert.  
#         bmHoleRig = self.oMeshHoleRig.Open()
#         for oVert1 in bmHoleRig.verts:
#             oBA.AddUShort(oVert1.index)                     # Send the vertex ID...
#             oBA.AddUShort(len(oVert1.link_edges))           #... followed by the number of verts connected to oVert1
#             for oEdge in oVert1.link_edges:                 #... followed by the neighboring verts
#                 oVert2 = oEdge.other_vert(oVert1)
#                 oBA.AddUShort(oVert2.index)
#         bmHoleRig = self.oMeshHoleRig.Close()
#         return oBA.Unity_GetBytes()
        













#         VertGrp_SelectVerts(oMesh.GetMesh(), "_CVagina_Ring0")
#         bpy.ops.object.mode_set(mode='OBJECT')          ###INFO: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
#         self.vecCenter = Vector((0,0,0))
#         nVertsInOpening = 0
#         for oVert in oMesh.GetMeshData().vertices:
#             if oVert.select == True:
#                 oORV = CHoleRigVert(oVert.index, oVert.co.copy())
#                 self.aHoleRigVert.append(oORV)
#                 self.vecCenter = self.vecCenter + oVert.co.copy()
#                 nVertsInOpening = nVertsInOpening + 1
#         self.vecCenter = self.vecCenter / nVertsInOpening
#         bpy.data.objects["Debug-Vagina-Opening-Center"].location = self.vecCenter
#         print("- Center of vagina opening is " + str(self.vecCenter))
#    
#         for oORV in self.aHoleRigVert:
#             oORV.CalcAngleAndDistance(self.vecCenter)


#         #=== Obtain reference to the vertex groups where we must scale weights down.  These are: Genitals, Anus, pelvis, xThighBend, xThighTwist ===
#         aVertGrpsScaleDownWeights = []
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), sNameBoneRoot))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "Anus"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "pelvis"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "lThighBend"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "rThighBend"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "lThighTwist"))
#         aVertGrpsScaleDownWeights.append(VertGrp_FindByName(oMesh.GetMesh(), "rThighTwist"))
    

#oBoneEdit.head = oORV.vecLocation - self.C_FlexParticleRadius * oORV.vecNormal       # Pull back bone from mesh surface the Flex particle distance along surface normal


#         #=== Optionally create a Blender-only mesh to visualize the Flex collider in Unity.  (It is a heavily-simplified version of presentation mesh in the hole area) ===
#         if bDebugVisualize:
#             sNameMeshUnity2Blender = "CHoleRig_FlexCollider"
#             oMeshD = bpy.data.meshes.new(sNameMeshUnity2Blender)
#             oMeshO = bpy.data.objects.new(oMeshD.name, oMeshD)
#             bpy.context.scene.objects.link(oMeshO)
#             aVerts = []
#             aFaces = []
#             for aHoleRigVert in self.aHoleRigVerts:
#                 for oORV in aHoleRigVert:
#                     oORV.nVertInFlexCollider = len(aVerts) 
#                     aVerts.append(oORV.vecLocation)
#             
#             for nRing in range(CHoleRig.s_nRings-1):
#                 for nAngle in range(self.nVertsPerRing):
#                     nAnglePlus0 = nAngle + 0
#                     nAnglePlus1 = nAngle + 1
#                     if nAnglePlus1 >= self.nVertsPerRing:
#                         nAnglePlus1 = 0
#                     oORV00 = self.aHoleRigVerts[nRing+0][nAnglePlus0]
#                     oORV01 = self.aHoleRigVerts[nRing+0][nAnglePlus1]
#                     oORV10 = self.aHoleRigVerts[nRing+1][nAnglePlus0]
#                     oORV11 = self.aHoleRigVerts[nRing+1][nAnglePlus1]
#                     aFace = [oORV00.nVertInFlexCollider, oORV01.nVertInFlexCollider, oORV11.nVertInFlexCollider, oORV10.nVertInFlexCollider]
#                     aFaces.append(aFace)
#                     
#             oMeshD.from_pydata(aVerts, [], aFaces)
#             oMeshD.update()
#             oMeshO.draw_type = "WIRE"        
#             oMeshO.show_wire = oMeshO.show_all_edges = oMeshO.show_x_ray = True
#             SetParent(oMeshO.name, G.C_NodeFolder_Temp)
#         


#         #=== Iterate through each ring to pick which vert we want to keep to form the simplified Flex collider mesh from the presentation geometry ===   
#         for nRing in range(CHoleRig.s_nRings):
#             sVertGroupName = sVertGroupNamePrefix + str(nRing)
#             VertGrp_SelectVerts(self.oMeshHoleRig.GetMesh(), sVertGroupName)
#             bpy.ops.object.mode_set(mode='OBJECT')          ###INFO: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
#     
#             self.aHoleRigVertThisRing = []
#             for oVert in self.oMeshHoleRig.GetMeshData().vertices:
#                 if oVert.select == True:
#                     vecPos = oVert.co.copy() - self.C_FlexParticleRadius * oVert.normal.copy()
#                     oORV = CHoleRigVert(oVert.index, vecPos, oVert.normal.copy())
#                     self.aHoleRigVertThisRing.append(oORV)
#         
#             for oORV in self.aHoleRigVertThisRing:
#                 oORV.CalcAngleAndDistance(self.vecCenter)
#         
#             self.aHoleRigVert = []
#             for nSlice in range(self.nVertsPerRing):
#                 nAngleWanted = nSlice * nDegreesPerSlice
#                 vecWanted = Vector((0,0))                   # For a vector to express the angle we want so we can use dot-product search
#                 vecWanted.x = cos(radians(nAngleWanted))    # cos(nAngle) = adj / hyp = x / nRadius so x = nRadius * cos(nAngle)
#                 vecWanted.y = sin(radians(nAngleWanted))    # sin(nAngle) = opp / hyp = y / nRadius so y = nRadius * sin(nAngle)
#                 
#                 oORVClosest = None          
#                 nAngleDiffClosestThusFar = 180
#                 for oORV in self.aHoleRigVertThisRing:
#                     vecFromCenter2D = Vector((oORV.vecFromCenter.x, oORV.vecFromCenter.y))        ###WEAK Flatten to 2D.  Find for vagina but anus at an angle would cause distortion!  Better would be for ring to allow for rotation!
#                     nAngleDiff = degrees(vecFromCenter2D.angle(vecWanted))
#                     if nAngleDiffClosestThusFar > nAngleDiff:
#                         nAngleDiffClosestThusFar = nAngleDiff
#                         oORVClosest = oORV                        ###BUG?: Algorithm can pick he same vert for multiple slots!
#                 
#                 print("- Ring{:1d} HoleRigVert at angle {:5.1f} chosen to represent angle {:5.1f} with a diff of {:5.2f}".format(nRing, oORVClosest.nAngle, nAngleWanted, nAngleDiffClosestThusFar))            
#                 self.aHoleRigVert.append(oORVClosest)          # Chose this HoleRigVert to participate in our Flex collider
#                 
#             self.aHoleRigVerts.append(self.aHoleRigVert)                # Append the fully-formed ring to our matrix of rings


#        mapHoleRigVert = {}         ###OBS:???  Unused!
#         aHoleRigVertRing0 = sorted(self.aHoleRigVerts[0], key=lambda oORV: oORV.nAngle)     ###INFO: How to sort class instances by a given key
#         nSortedOrdinal = 0
#         for oORV in aHoleRigVertRing0:
#             mapHoleRigVert[oORV.nVert] = oORV
#             oORV.nSortedOrdinal = nSortedOrdinal                        # Remember what sorted ordinal we are
#             nSortedOrdinal = nSortedOrdinal + 1
#             print(oORV)
#         self.nNumHoleRigVert = nSortedOrdinal
    



    
    #         vecVertDiff = oVert.co.copy() - self.vecCenter
    #         oHoleRigVert = None
    #         for oORV in aHoleRigVertRing0:
    #             if nAngle < oORV.nAngle:
    #                 oHoleRigVert = oORV
    #                 break
               
    #         nHoleRigVert2 = oHoleRigVert.nSortedOrdinal + 1
    #         if nHoleRigVert2 >= len(aHoleRigVertRing0):             # Wrap around o zero if oHoleRigVert was the last in our sorted array
    #             nHoleRigVert2 = 0
    #         oORV2 = mapHoleRigVert[nHoleRigVert2] 
    

    #         nAngle1 = oHoleRigVert.nAngle                      ###OPT: Really need dual bone weight if we have many bones??
    #         nAngle2 = oORV2.nAngle
    #         if nAngle1 > nAngle2:
    #             nAngle2 = nAngle2 + 360
    #         nAngleDiff = nAngle2 - nAngle1
    # 
    #         nDiffWithAngle1 = nAngle  - nAngle1
    #         nDiffWithAngle2 = nAngle2 - nAngle


            #nBone2_Remainder = nBone - nBone1
            #nBone1_Remainder = 1 - nBone2_Remainder
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


#         oBA = CByteArray()
#         oBA.AddFloat(CHoleRig.s_nRings)              
#         oBA.AddFloat(self.nVertsPerRing)              
#         for self.aHoleRigVert in self.aHoleRigVerts:
#             for oORV in self.aHoleRigVert:
#                 oORV.Serialize(oBA)
#         return oBA.Unity_GetBytes()






#         ###OBS24: Much better vagina hole collider now integrated into CBodyBase
#         #===== A. CREATE REDUCED-GEOMETRY RIG MESH =====
#         #=== Create the hole rig mesh as a copy of the source body ===
#         print("\n===== CHoleRig() running with nDistMax = {} =====".format(self.nDistMax))        
#         self.oMeshHoleRig = CMesh.CreateFromDuplicate(self.oBody.oBodyBase.sMeshPrefix + "-HoleRig", self.oBody.oBodyBase.oMeshSource)      ###IMPROVE24: Mesh name
#         SelectObject(self.oMeshHoleRig.GetName())
#         bmHoleRig = self.oMeshHoleRig.Open()
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#         
#         #=== Select all the pre-defined rings ===
#         for nRing in range(CHoleRig.s_nRings):
#             sVertGroupName = CHoleRig.C_NameVertGroup_Vagina + str(nRing)
#             VertGrp_AddToSelection(self.oMeshHoleRig.GetMesh(), sVertGroupName)
#             
#         #=== Invert selection and delete all the non-rings edges.  After this only the rings are left ===
#         bpy.ops.mesh.select_all(action='INVERT')
#         bpy.ops.mesh.delete(type='EDGE')
# 
#         #=== Duplicate ring zero and push it upward up the vagina so we have a simplified version of the vagina inside ===
#         oVertGrp_Ring0 = VertGrp_SelectVerts(self.oMeshHoleRig.GetMesh(), CHoleRig.C_NameVertGroup_Vagina + "0")
#         bpy.ops.mesh.looptools_relax(input='selected', interpolation='linear', iterations='5', regular=True)
#         bpy.ops.mesh.looptools_flatten(influence=100, lock_x=False, lock_y=False, lock_z=False, plane='best_fit', restriction='none')
#         bpy.ops.mesh.remove_doubles(threshold=0.0016)               ###TUNE: Important settings that affects how many bones will drive hole expansion
#         bpy.ops.mesh.duplicate_move(MESH_OT_duplicate={"mode":1}, TRANSFORM_OT_translate={"value":(0, 0.001, .015)})
#         bpy.ops.object.vertex_group_remove_from()                       # Remove new duplicate verts from ring 0 vert group
#         
#         #=== The upper part of the outer ring need a heck a lot of smoothing to remove lab folds ===
#         VertGrp_SelectVerts(self.oMeshHoleRig.GetMesh(), "_CVagina_RingSmooth")
#         for nLoop in range(4):
#             bpy.ops.mesh.looptools_relax(input='selected', interpolation='linear', iterations='25', regular=True)
#         bpy.ops.mesh.looptools_flatten(influence=100, lock_x=False, lock_y=False, lock_z=False, plane='best_fit', restriction='none')
# 
#         #=== Subdivide then reduce the geometry of outer right to even out the geometry
#         oVertGrp_Ring1 = VertGrp_SelectVerts(self.oMeshHoleRig.GetMesh(), CHoleRig.C_NameVertGroup_Vagina + "1")
#         bpy.ops.mesh.subdivide(number_cuts=4)
#         bpy.ops.mesh.remove_doubles(threshold=0.0040)               ###TUNE
#         bpy.ops.object.vertex_group_assign()                        # Add the new geometry to ring 1
# 
#         #=== Select all our rings and bridge them.  This will create a coherent and greatly simplified version of the original mesh ===
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.mesh.bridge_edge_loops()                        ###INFO: A powerful and *amazing* ability to quickly create meshes from rings of edges!
# 
# 
#         #=== Remove bones that start with the specified bone name prefix ===
#         oArmObject = self.oMeshHoleRig.GetMesh().modifiers["Armature"].object
#         oArm = oArmObject.data
#         Bones_RemoveBonesWithNamePrefix(oArm, CBodyBase.C_Prefix_DynBone_Vagina)
# 
# 
#         #=== Remember the position of the ring 0 verts before we pull back.  These will be our bones ===
#         VertGrp_SelectVerts(self.oMeshHoleRig.GetMesh(), oVertGrp_Ring0.name)
#         for oVert in bmHoleRig.verts:
#             if oVert.select:
#                 self.aHoleRigVerts.append(CHoleRigVert(oVert.index, oVert.co.copy()))
# 
#         #=== Pull back the verts by the Flex particle radius so gametime collisions appear to be at skin level ===
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.transform.shrink_fatten(value = -self.C_FlexParticleRadius)
#         bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
# 
# 
#         #=== Perform extra smoothing on ring 0 ===
#         VertGrp_SelectVerts(self.oMeshHoleRig.GetMesh(), oVertGrp_Ring0.name)
#         bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)            ###INFO: Loop tool's *awesome* relax function has 'cubic' mode to respect more the curvature.  Linear destroys more but gives smoother results
# 
#         #=== Perform extra smoothing on the capped ring 0 (inside vagina)        
#         VertGrp_SelectVerts(self.oMeshHoleRig.GetMesh(), oVertGrp_Ring0.name)       # We get to new cap verts by selecting both ring 0 and 1 and inverting (cap is the only thing that is left)
#         VertGrp_AddToSelection(self.oMeshHoleRig.GetMesh(), oVertGrp_Ring1.name)
#         bpy.ops.mesh.select_all(action='INVERT')                            # We now have cap selected
#         bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)           ###CHECK24: Caps with a gentle slope inwards... valuable to guide or slow down the penis?
#         bpy.ops.mesh.looptools_relax(input='selected', interpolation='linear', iterations='10', regular=True)           ###CHECK24: Caps with a gentle slope inwards... valuable to guide or slow down the penis?
#         bpy.ops.mesh.select_all(action='SELECT')
#     
#         #=== First determine the IMPORTANT center of opening from Ring0.  Central to everything! ===
#         self.vecCenter = Vector((0,0,0))
#         for oHoleRigVert in self.aHoleRigVerts:
#             self.vecCenter = self.vecCenter + oHoleRigVert.vecLocation
#         self.vecCenter = self.vecCenter / len(self.aHoleRigVerts)
#         self.vecCenter.x = 0                            # Make sure we're centered ###KEEP!?
#         print("- CHoleRig: Center of opening is at " + str(self.vecCenter))
# 
#         #=== Record the *moved* position in our hole rig verts and perform angle-to-center calculation ===
#         bmHoleRig.verts.ensure_lookup_table()
#         for oHoleRigVert in self.aHoleRigVerts:
#             oHoleRigVert.vecLocationMoved = bmHoleRig.verts[oHoleRigVert.nVert].co.copy()
#             oHoleRigVert.CalcAngleAndDistance(self.vecCenter)
#         bmHoleRig = self.oMeshHoleRig.Close()


 
#     def Serialize(self, oBA):                       # Serialize all our fields into floats in the supplied CByteArray() for Unity to de-serialize
#         oBA.AddVector(self.vecLocation)
    

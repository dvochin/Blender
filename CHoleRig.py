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
        self.sName = CBody.CBody.C_Prefix_DynBone_Vagina + str(nVert).zfill(3)
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
    C_NameVertGroup_Vagina      = r"_CVagina_Opening"                    # Name of the vertex groups representing the vagina opening verts

    
    def __init__(self, oMeshSrc, nDistMax):
        self.oMeshSrc           = oMeshSrc
        self.nDistMax           = nDistMax
        
        self.oMeshHoleRig       = None                  # The hole rig mesh we construct and serialize to Unity 
        self.vecCenter          = Vector((0,0,0))
        self.nNumHoleRigVert    = 0
        self.oBoneRoot          = None
        self.aHoleRigVerts      = []                    # List of all the 'ring 0' rig verts that will drive bones.  The value is the original vert position before pull-back
        #self.C_FlexParticleRadius = 0.01 * 0.85      #Copy of Unity's super-important CGame.INSTANCE.particleDistance / 2.  Need to 'pull back' the bones by the particle radius so collisions appear to be made at skin level instead of past it.  Since this value rarely changes this 'copy' is tolerated here but in reality the rig must be redone everytime this value chaanges.  ###TUNE: What ratio?


        
        #===== A. DETERMINE VAGINA OPENING VERTEX POSITIONS =====        
        #=== Remember the position of the ring 0 verts before we pull back.  These will be our bones ===
        print("\n=== CHoleRig() ===")
        if self.oMeshSrc.Open():
            self.vecCenter = Vector((0,0,0))
            nBoneID = 0
            self.oMeshSrc.VertGrp_SelectVerts(CHoleRig.C_NameVertGroup_Vagina)
            for oVert in self.oMeshSrc.bm.verts:
                if oVert.select:
                    self.aHoleRigVerts.append(CHoleRigVert(nBoneID, oVert.co.copy()))
                    self.vecCenter = self.vecCenter + oVert.co.copy()
                    nBoneID += 1
            self.vecCenter /= nBoneID
            self.oMeshSrc.Close()

        #=== Calculate angle and distance for each bone (now that center is known) ===        
        for oORV in self.aHoleRigVerts:
            oORV.CalcAngleAndDistance(self.vecCenter)
        
        #===== B. ADD BONES =====        
        #=== Remove bones that start with the specified bone name prefix ===
        oArmObject = self.oMeshSrc.GetMesh().modifiers["Armature"].object
        oArm = oArmObject.data
        SelectObject(oArmObject.name)               # Must select armature object... 
        bpy.ops.object.mode_set(mode='EDIT')        #... and then place it in edit mode for us to be able to view / edit bones
        sBoneRemoveFilter = "\\" + CBody.CBody.C_Prefix_DynBone_Vagina      ###WEAK: Constant starts with a '+' and because regex chokes on it we must prefix with '\' to indicate it is a literate one (i.e. not regex command)
        Bones_RemoveBones(oArm, re.compile(sBoneRemoveFilter))
    
        #=== Modify the vagina root bone (created during BodyImporter) ===        ###DEV24:???
        sNameBoneRoot = "Genitals"
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
        if self.oMeshSrc.Open():
            #=== Determine the verts within range ===
            self.oMeshSrc.VertGrp_SelectVerts(r"_CVagina_AreaBig")
            aVertsInGroup = [oVert for oVert in self.oMeshSrc.bm.verts if oVert.select]
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
            self.oMeshSrc.Close()
            
    
        #=== Iterate through verts in range to set their weights ===
        bpy.ops.object.mode_set(mode='OBJECT')          # We must be in object mode for bone weight editing!
        oMesh = self.oMeshSrc.GetMeshData()
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
        
        print("--- CHoleRig() completed successfully ---\n")


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

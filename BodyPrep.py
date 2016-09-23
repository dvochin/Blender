###DISCUSSION: 
#=== TODAY ===
#- Need to create new game mode to morph body and re-simulate bodysuit.
    #- Expand CObject and CProp into Blender
    #- CObject has specialized subclasses such as CObjectDynamic and CObjectDynamicShapeKeys
    #- CBody owns a CObjectDynamicShapeKeys and exports to Unity.
    #- Bad naming of root node?
# Remember 90 degree roll applied to both elbows!


#=== PROBLEMS ===
#- Finger and toes have slightly discordant orientations...
#- Feet axis is poor 
#- Neck upper and lower and head should have same orientation?

#=== NEXT ===

#=== TODO ===
#- BUG: Needs pivot mode to be set to 3D cursor!!!!
#- Remove 'EyeMoisture' verts?
#- Have to set eyelashes and cornea transparent: Remove 'use' from textures and have calculate with 
    #- Can export alpha better with different daz export??
#- Do we remove geometry for things we don't use ('eyecover'?)  What to do with eyelashes?
#- Remove geometry on some parts
#- Add geometry for breasts!
#- Retest FBX morph export! 
#- Move to a new file!
#- All lines when wireframe

#=== REMINDERS ===

#=== NEEDS ===
# Need to retain unrestrained flow with raw DAZ imports while having a programmatic modification procedure to make meshes game-ready.
#    - We need to provide more geometry at certain body areas (breasts)
#    - We need to identify groups of vertices from raw DAZ imports. (e.g. to modify mesh)
# Need to expose DAZ-provided morphs to user:
#    - Body shapes are added to the gameready source mesh.
#    - User dials in his shapes, body is refreshed in Unity and Flex collider too (pushing away bodysuit)
# Need to have a bodysuit that morphs according to ANY source body shape changes.  (shape keys, breast adjustments, penis position, etc)
#    - The 'static flex collider' is what makes this possible: a non-remeshed body (pulled back particle distance) that is a partially refined body mesh.  (e.g. not the optimized Flex collider that is remeshed for efficiency) 

#=== DESIGN ===

#=== CONCEPTS ===
# "Original Mesh": Raw import of body mesh from DAZ without mesh modifications.
    # Runs complex FirstImport() calls to perform complex bone adjustments, material tweaks, etc
    # Manually gets a few vertex groups that detail which verts are used to transform toward the 'gameready' source mesh
# "First import": The importation of the very first raw DAZ body.  We have to mark vertices on this mesh as it has none of our useful vertice groups.  Rarely done!!
# "Body Shape imports": Importing a raw DAZ body and adding a 'shape key' for this body's shape
    # Flow that adds geometry for breasts, removes verts for a few materials and adds shape key to 'gameready' source mesh
# "Gameready source mesh": Version of 'Original Mesh' with extra geometry for breasts and a few removed materials.
    #- Contains several shape keys for different morphs exposed to player at gametime (e.g. body weight, breast morphs, etc)
    #- Contains many custom vertex groups that enable the codebase to work (e.g. markings for vagina, breasts, penis area, etc)
# "Runtime Body Conversion": Converts an 'Original Mesh' by modifying and optimizing its geometry for game time

#=== IDEAS ===

#=== QUESTIONS ===
#- Previous implementation maintained vertex ID custom data layers as mesh was modified... keep this?
    #- Rethink the concept of the 'morphing body' and the 'source body'??
#- Previous breast morphing needs heavy pre-computation... Can this be redone by quickly 'walking the quads' to blend to base as we morph?

#=== LEARNED ===

#=== WISHLIST ===

#=== MOVE ===
#- Simplification strategy based on this body prep work:
    #- Remain comitted to the 'body suit' concept: One well-designed mesh covering whole body that is Unity+Flex simulated everytime the user modifies the body's shape
        #- Dynamic clothing is cut from this body suit.
        #- All geograph clothing is moved by the bones / verts of this body suit.
        #- (Additional bodysuits will be created later on for specialized tasks: dresses, bras)
    #- Needs for the automatic geograph cloth importation.
        #- We need a body shape + fitted bodysuit to match the design-time shape of the body the cloth was designed for. (e.g. Skyrim body, DAZ body, etc)
    #- Static Flex colliders are critical...
        #- Q: Are we forced to 'remesh' to re-simulate bodysuit or can we get away with slow moving of the original geometry
    #- Flow to morph clothing:
        #- Import in Unity + Flex the starting-shape body and its fitted bodysuit.
        #- Gradually apply body shape modifications so bodysuit is re-simulated to the new destination shape.
        #-Q: Do we process breast shape separately or as part of one unified Flex body? (-> Flatten breast shape into full Flex body)
        #-Q: How do we process cloth fitting for different penis sizes & position adjustments? (-> Copy simulated penis particles (moved into desired position) into static Flex collider while gradually moving these particles from inside body to destination position)

#=== MISC ===
###NOTE: BUGFIX OF FBX IMPORTER.  Modify the link_hierarchy() function in import_fbx.py to contain the following.  This fixes a crash so FBX import can complete importing DAZ bodies (imported pose still screwed up tho)
#             if self.meshes:
#                 for mesh in self.meshes:
#                     if self not in mesh.armature_setup:                                     ###MOD: Fixes crash during DAZ imports but... full import when it works loads a bad pose that must be cleared
#                         print("###ERROR: FBXImport.link_hierarchy() Could not find " + str(self))
#                         continue
    



import bpy
import sys
import array
import bmesh
import struct
from math import *
from mathutils import *

import G
from gBlender import *

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    FIRST-TIME IMPORT
#---------------------------------------------------------------------------    

def FirstImport_ProcessRawDazImport(sNameDazImportMesh, sNameMeshPrefix):
    #===== DAZ MESH PROCEDURE AFTER RAW DAZ IMPORT =====
    sNameMeshOriginal = sNameMeshPrefix + "-Original"
    oMeshOriginalO = Import_FirstCleanupOfDazImport(sNameDazImportMesh, sNameMeshOriginal)
    
    #=== Remove dumb 90 degree orientation of root node and set scale to unity ===
    oRootNodeO = oMeshOriginalO.parent                    # Mesh root node is parent of the main mesh
    oRootNodeO.name = "[" + sNameMeshPrefix + "]"
    oRootNodeO.name = "[" + sNameMeshPrefix + "]"
    oRootNodeO.rotation_euler.x = 0
    oRootNodeO.scale = Vector((1,1,1))
    
    #=== Obtain reference to armature ===
    oArm = oMeshOriginalO.modifiers["Armature"].object.data
    oArm.name = sNameMeshPrefix + "-Armature"
    
    #=== Rotate the armature bones to nullify node rotation above and rescale to return bones to meter units (and nullify re-scaling above) ===
    SelectAndActivate(oRootNodeO.name, True)           
    bpy.ops.object.mode_set(mode='EDIT')                                        ###LEARN: Modifying armature bones is done by simply editing root node containing armature.
    oArmBones = oArm.edit_bones
    bpy.ops.armature.select_all(action='SELECT')                                ###LEARN: How to select bones... almost like 'mesh'
    Import_RotateAndRescale()
    bpy.ops.armature.select_all(action='DESELECT')

    #=== Reparent nodes with 'chestUpper' as root node ===
    oArmBones['chestUpper'].parent      = None
    oArmBones['chestLower'].parent      = oArmBones['chestUpper']
    oArmBones['abdomenUpper'].parent    = oArmBones['chestLower']
    oArmBones['abdomenLower'].parent    = oArmBones['abdomenUpper']
    oArmBones['hip'].parent             = oArmBones['abdomenLower']
    bpy.ops.object.mode_set(mode='OBJECT')
    #oArmBones.remove(oArmBones['Genesis3FemaleGenitalia'])        # Remove extra bones we don't need

    #=== Verify bone symmetry ===
    FirstImport_VerifyBoneSymmetry(oMeshOriginalO)
    nAdjustments = FirstImport_VerifyBoneSymmetry(oMeshOriginalO)        # Run twice to check if second run had to do anything = bug in the first run!
    if (nAdjustments != 0):
        raise Exception("###EXCEPTION: Could not symmetrize bones!  {} are left!".format(nAdjustments))

    #===== Set bone tail to a reasonable value =====
    SelectAndActivate(oRootNodeO.name, True)
    bpy.ops.object.mode_set(mode='EDIT')                                        ###LEARN: Modifying armature bones is done by simply editing root node containing armature.
    #=== Iterate a first time to set all bone tails half the vector between parent-to-bone ===
    for oBone in oArmBones:
        if (oBone.parent):
            vecParentToBone = oBone.head - oBone.parent.head
            oBone.tail = oBone.head + vecParentToBone * 0.5            # Makes tail of this node protrude a portion of the distance from bone-parent (so it looks nice)
    #=== Iterate a second time to set the tail of non-leaf bones to its last child (to give 'continuity' between the bones')
    aBonesSumOfChildHeadPos = {}                        # Contains a vector that sums up all the child heads for each parent bone
    aBonesCountOfChildBones = {}                        # Contains an int that counts how many children added their head position into aBonesSumOfChildHeadPos
    for oBone in oArmBones:                                                    # Iterate through all bones...
        if (oBone.parent):                                                    # ... and for each bone with a parent...
            if (oBone.parent not in aBonesSumOfChildHeadPos):                # ... create the entries into our dictionary if this parent has not been traversed before...
                aBonesSumOfChildHeadPos[oBone.parent] = Vector((0,0,0))
                aBonesCountOfChildBones[oBone.parent] = 0
            aBonesSumOfChildHeadPos[oBone.parent] += oBone.head.copy()        #... and add this bone's head position to the sum...
            aBonesCountOfChildBones[oBone.parent] += 1                        #... and increment the count.
    #=== Iterate through our map of parents to set the tail to the average of their children's positions ===
    for oBone in aBonesSumOfChildHeadPos:
        vecTail = aBonesSumOfChildHeadPos[oBone] / aBonesCountOfChildBones[oBone]
        oBone.tail = vecTail   

    #=== Ensure key bone chains are properly linked ===  (Loop above sets bone tail to center of average of children.  This is fine for most purposes EXCEPT the key spine bones)
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "chestUpper",   "chestLower")
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "chestLower",   "abdomenUpper")
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "abdomenUpper", "abdomenLower")
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "abdomenLower", "hip")                  ###CHECK: abdomenUpper -> abdomenLower -> hip -> pelvis do a 360 loop!  ###NOW### What to do???
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "hip",          "pelvis")
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "head",         "upperFaceRig")         ###CHECK: Safe to do?  Rotation side to side would be off-angle to what is intuitive.  ###IMPROVE: Manually set tail upward??
    ConnectParentTailToHeadOfMostImportantChild2(oArmBones, "Foot",         "Metatarsals")
    ConnectParentTailToHeadOfMostImportantChild2(oArmBones, "Metatarsals",  "Toe")
    ConnectParentTailToHeadOfMostImportantChild2(oArmBones, "ForearmTwist", "Hand")
    
    #=== Bone chain above fixes a lot of problems but some very short bones still have very poor orientations.  Fix small bones by key bone vectors ===
    OrientSmallBoneFromParents1(oArmBones, "abdomenLower",   "chestUpper", "pelvis")     # abdomentLower -> hip -> pelvis form a 360 loop that horribly corrupt Y-axis twist!  Fix orientation from most important torso chain
    OrientSmallBoneFromParents1(oArmBones, "hip",            "chestUpper", "pelvis")
    OrientSmallBoneFromParents1(oArmBones, "pelvis",         "chestUpper", "pelvis")
    OrientSmallBoneFromParents1(oArmBones, "head",           "neckLower",  "head")        # Make both neck bones and head bone point in the same direction so it's easy to orient head
    OrientSmallBoneFromParents1(oArmBones, "neckUpper",      "neckLower",  "head")
    OrientSmallBoneFromParents1(oArmBones, "neckLower",      "neckLower",  "head")
    OrientSmallBoneFromParents2(oArmBones, "Hand",           "ForearmTwist", "Hand")     # Hand is a very short bone that needs to be based on its parent
    OrientSmallBoneFromParents2(oArmBones, "Toe",            "Metatarsals", "Toe")       # Toe is poorly oriented toward average of toes.  Set orientation like its parent

    #=== Apply manual roll to some bones that would deform very poorly with PhysX's configurable joint limits of only having X axis being assymetrical ===
    ManuallyAdjustRoll2(oArmBones, "ForearmBend", 90)           # Forearm by default has important elbow bend along Z axis (Needs to be on X-axis for assymetrical X-axis with PhysX configurable joint)
    ManuallyAdjustRoll2(oArmBones, "Foot", 25)
    ManuallyAdjustRoll2(oArmBones, "Metatarsals", 17)
    ManuallyAdjustRoll2(oArmBones, "Toe", 17)                   ###IMPROVE: Orient toward up instead of these hardcoded angles!!

    #=== Exit edit mode and hide rig ===
    bpy.ops.object.mode_set(mode='OBJECT')
    oRootNodeO.hide = True
    SelectAndActivate(oMeshOriginalO.name, True)


#---------------------------------------------------------------------------    FIRST-IMPORT BONE ADJUSTERS

def ConnectParentTailToHeadOfMostImportantChild1(oArmBones, sNameBoneParent, sNameBoneChild):      # Ensures a perfectly linked chain of bones by setting a parent's tail to the head of its 'most important' child (e.g. upperChest tail to head of lowerChest)
    oBoneParent = oArmBones[sNameBoneParent]
    oBoneChild  = oArmBones[sNameBoneChild]
    oBoneParent.tail = oBoneChild.head              # Parent will now flow right into its most important child (thereby providing intuitive deformation when rotated)

def ConnectParentTailToHeadOfMostImportantChild2(oArmBones, sNameBoneParent, sNameBoneChild):      # Split the 'ConnectParentTailToHeadOfMostImportantChild1' to both left and right body sides.
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "l"+sNameBoneParent, "l"+sNameBoneChild)
    ConnectParentTailToHeadOfMostImportantChild1(oArmBones, "r"+sNameBoneParent, "r"+sNameBoneChild)

def OrientSmallBoneFromParents1(oArmBones, sNameSmallBone, sNameParent1, sNameParent2):
    oBoneParent1    = oArmBones[sNameParent1]
    oBoneParent2    = oArmBones[sNameParent2]
    oBoneSmall      = oArmBones[sNameSmallBone]
    vecParent = oBoneParent2.head - oBoneParent1.head
    oBoneSmall.tail = oBoneSmall.head + (vecParent * 0.25)      # Set the tail to be starting from the head plus some distance of parent vector 

def OrientSmallBoneFromParents2(oArmBones, sNameSmallBone, sNameParent1, sNameParent2):  # Split the 'OrientSmallBoneFromParents1' to both left and right body sides.
    OrientSmallBoneFromParents1(oArmBones, "l"+sNameSmallBone, "l"+sNameParent1, "l"+sNameParent2)
    OrientSmallBoneFromParents1(oArmBones, "r"+sNameSmallBone, "r"+sNameParent1, "r"+sNameParent2)
    
def ManuallyAdjustRoll1(oArmBones, sNameBone, nRoll):
    oArmBones[sNameBone].roll = radians(nRoll)

def ManuallyAdjustRoll2(oArmBones, sNameBone, nRoll):
    ManuallyAdjustRoll1(oArmBones, "l"+sNameBone,  nRoll)
    ManuallyAdjustRoll1(oArmBones, "r"+sNameBone, -nRoll)
    


#---------------------------------------------------------------------------    LEFT / RIGHT SYMMETRY

def FirstImport_VerifyBoneSymmetry(oMeshBodyO):    
    #=== Iterate through all left bones to see if their associated right bone is positioned properly ===
    print("\n\n=== FirstImport_VerifyBoneSymmetry() ===")
    oArm = oMeshBodyO.modifiers["Armature"].object.data
    SelectAndActivate(oMeshBodyO.parent.name, True)            ###LEARN: Armature editing is done through the mesh's parent object
    oArmBones = oArm.edit_bones    
    nAdjustments = 0
    bpy.ops.object.mode_set(mode='EDIT')                                        ###LEARN: Modifying armature bones is done by simply editing root node containing armature.
    for oBoneL in oArmBones:
        sNameBoneL = oBoneL.name 
        if (sNameBoneL[0] == 'l' and sNameBoneL[1] >= 'A' and sNameBoneL[1] <= 'Z'):            # Test left bone / right bone symmetry
            sNameBoneR = 'r' + sNameBoneL[1:]
            print("--- Testing bone '{}' - '{}' ---".format(sNameBoneL, sNameBoneR))
            oBoneR = oArmBones[sNameBoneR]
            vecBoneL = oBoneL.head.copy()
            vecBoneR = oBoneR.head.copy()
            vecBoneR.x = -vecBoneR.x
            if (vecBoneL != vecBoneR):
                vecDiff = vecBoneR - vecBoneL 
                print("- Bone head mismatch on '{}'  {}   {}   {}  Dist={:6f}".format(sNameBoneL, vecBoneL, vecBoneR, vecDiff, vecDiff.magnitude))
                if (vecDiff.magnitude > 0.0001):
                    print("     ###WARNING: Bone symmetry difference is large!\n")
                vecBoneCenter = (vecBoneL + vecBoneR) / 2 
                oBoneL.head = vecBoneCenter.copy()
                vecBoneCenter.x = -vecBoneCenter.x
                oBoneR.head = vecBoneCenter.copy()
                nAdjustments += 1
        elif (sNameBoneL[0] != 'r' or sNameBoneL[1] < 'A' or sNameBoneL[1] > 'Z'):                # Test that center bones are indeed centered at x = 0
            print("--- Testing center bone '{}' ---".format(sNameBoneL))
            oBoneC = oArmBones[sNameBoneL]
            if (oBoneC.head.x != 0 or oBoneC.tail.x != 0):
                print("- Center bone '{}' has head {} and tail {}".format(sNameBoneL, oBoneC.head, oBoneC.tail))
                oBoneC.head.x = oBoneC.tail.x = 0
                nAdjustments += 1
    bpy.ops.object.mode_set(mode='OBJECT')
    return nAdjustments





#---------------------------------------------------------------------------    IMPORT COMMONS

def Import_FirstCleanupOfDazImport(sNameDazImportMesh, sNameMeshNew):
    #=== Rename, rotate and rescale meshes verts (to nullify node rotation, rescaling above) ===
    sNameDazImportMeshShape = sNameDazImportMesh + ".Shape"
    oMeshImportedO = Import_RenameRotateAndRescaleMesh(sNameDazImportMeshShape, sNameMeshNew)
    oMeshImportedO.show_all_edges = True

    #=== Obtain reference to armature and name properly ===
    oMeshImportedO.modifiers[0].name = "Armature"       # Ensure first modifier is called what we need throughout codebase (FBX sets only one modifier = Armature) 

    #=== Remove the root node's children that are NOT the expected mesh names (Deletes unwanted DAZ nodes) ===
    oRootNodeO = SelectAndActivate(oMeshImportedO.parent.name, True)     # Select parent node (owns the bone rig)
    aNodesToDelete = []
    for oChildNodesO in oRootNodeO.children:
        if oChildNodesO.name != sNameMeshNew:
            DeleteObject(oChildNodesO.name)

    #=== Remove (empty) vertex groups we don't need ===            ###IMPROVE: Genitals too?  ###IMPROVE: Delete all those with zero verts in them?  (slow?)
    SelectAndActivate(oMeshImportedO.name, True)
    Cleanup_VertGrp_Remove(oMeshImportedO, "Genesis3Female")
    Cleanup_VertGrp_Remove(oMeshImportedO, "hip")
    Cleanup_VertGrp_Remove(oMeshImportedO, "lowerFaceRig")
    Cleanup_VertGrp_Remove(oMeshImportedO, "upperFaceRig")
    Cleanup_VertGrp_Remove(oMeshImportedO, "lToe")
    Cleanup_VertGrp_Remove(oMeshImportedO, "rToe")

    #=== Clean up bone weights and vertex groups ===
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)                    ###CHECK!!! Does this lose any information? (for example limb rotation??)
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0, keep_single=False)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
    bpy.ops.object.vertex_group_sort(sort_type='NAME')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    #=== Set the materials to better defaults ===
    for oMat in oMeshImportedO.data.materials:
        oMat.diffuse_intensity = 1
        oMat.specular_intensity = 0

    #=== Clear the pose (FBX import screws that up royally!) ===
    SelectAndActivate(oRootNodeO.name, True)     # Select parent node (owns the bone rig)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')                ###LEARN: How to select bones in pose mode
    bpy.ops.pose.transforms_clear()                         # Clears all the pose transforms so each bone in the default pose returns to the edit bones
    bpy.ops.pose.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    SelectAndActivate(oMeshImportedO.name, True)
    return oMeshImportedO

    
def Import_RenameRotateAndRescaleMesh(sNameMeshOld, sNameMeshNew):
    SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)
    oMeshO = SelectAndActivate(sNameMeshOld, True)
    oMeshO.name = oMeshO.data.name = sNameMeshNew
    oMeshO.name = oMeshO.data.name = sNameMeshNew
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    Import_RotateAndRescale()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return oMeshO

    
def Import_RotateAndRescale():
    bpy.ops.transform.rotate(value=radians(90), axis=(1, 0, 0), constraint_axis=(True, False, False))
    bpy.ops.transform.resize(value=(0.01, 0.01, 0.01))



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BODY SHAPE IMPORT
#---------------------------------------------------------------------------
###TODAY###    
#- Need to properly switch between first run (creating game mesh) and additional runs (adding shape keys)
    #- Need to create basis in first game mesh
#- Add print()
#- How to name shape key??  Dev does it after command??
    #- Way to extract imported filename?
#- Test the whole thing from first import, first game mesh import, additional shape imports...
    #- Refactor with FirstImport, ImportGameMesh ImportShapeKey?
#- What to do with damn materials multuplying?  Redirect new meshes to orig?

def ImportShape_AddImportedBodyToGameBody(sNameDazImportMesh, sNameMeshPrefix):
    #=== Perform the first stage of importation by renaming, rotating and rescaling mesh as we need it.
    oMeshDazImportO = Import_FirstCleanupOfDazImport(sNameDazImportMesh, "TEMP_ImportedMesh")       # Mesh will get manually renamed (if first) or merged as shape key (if not first) of main game mesh
    oRootNodeImportedToDelete = oMeshDazImportO.parent 

    #=== Clean up the armature and the newly imported mesh's parent node (containing armature) === 
    oModArm = oMeshDazImportO.modifiers["Armature"]
    oModArm.object = None                                   # Unlink existing armature modifier to the importated armature (that we're about to delete)
    sNameParent = oMeshDazImportO.parent.name
    oMeshDazImportO.parent = None                           ###LEARN: Must clear parent in sub-nodes before deleting parent or mesh will be inacessible!
    DeleteObject(sNameParent)                               # Remove imported body's parent node (armature)

    #===== Increase breast geometry with a selective subdivide of much of the breast area =====
    #=== First open original mesh to obtain the list of vertices ===
    sNameMeshOriginal = sNameMeshPrefix + "-Original"
    oMeshOriginal = SelectAndActivate(sNameMeshOriginal, True)
    aVertsBreasts = []
    Util_SelectVertGroupVerts(oMeshOriginal, "_ImportGeometryAdjustment-Breasts")
    bpy.ops.object.mode_set(mode='OBJECT')          ###LEARN: Non-bmesh access must read selections this way  ###IMPROVE: Switch to bmesh?
    for oVert in oMeshOriginal.data.vertices:
        if (oVert.select):
            aVertsBreasts.append(oVert.index)
            oVert.select = False
    Util_HideMesh(oMeshOriginal)
    #=== Open the imported mesh to select the same verts.  Original and just-imported mesh are guaranteed to be of the same geometry ===
    oMeshDazImportO = SelectAndActivate(oMeshDazImportO.name, True)
    for nVert in aVertsBreasts:
        oMeshDazImportO.data.vertices[nVert].select = True    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(quadtri=True, quadcorner='INNERVERT', smoothness=1)      # Adds geometry with 'fanout' to border of previous low-geometry.  Also smooths the mesh to take into account new geometry
    bpy.ops.mesh.select_all(action='DESELECT')          ###WEAK: Above will show "Invalid clnors in this fan!" hundreds of time in error output.  As this happens even when invoking subdivide through Blender I think it can be ignored.
    bpy.ops.object.mode_set(mode='OBJECT')

    #=== Remove verts for useless materials ===
    Cleanup_RemoveMaterial(oMeshDazImportO, "EyeMoisture")           # Dumb 'wrapper mesh' to entire eye for moisture!
    
    #=== Reparent to the previously-imported bone rig.  Also set as child node to that same parent ===
    oMeshDazImportO.parent = oMeshOriginal.parent       # Set as child of previously-imported parent (with previously cleaned-up bones)               
    oModArm.object = oMeshOriginal.parent               #bpy.ops.outliner.parent_drop(child=oMeshDazImportO.name, parent=oMeshOriginal.parent.name, type='ARMATURE')  ###NOTE: This is the Blender call when parenting to a rig in the Blender UI... fails with incorect context!

    #=== Delete the imported rig (imported mesh now properly connected to the good rig) ===
    DeleteObject(oRootNodeImportedToDelete.name)

    #===== Rest of shape import depends if there already is a first shape or not... =====
    if sNameMeshPrefix in bpy.data.objects:
        #=== Add a shape key into the gameready mesh of the just-imported mesh ===
        print("\n=== NOTE: ImportShape() finds basis mesh.  Adding imported mesh as a shape key to basis mesh.  Please rename newly-created shapekey.\n")
        oMeshDazImportO = SelectAndActivate(oMeshDazImportO.name, True)
        oMeshGame = bpy.data.objects[sNameMeshPrefix]
        oMeshGame.select = True
        oMeshGame.hide = False
        bpy.context.scene.objects.active = oMeshGame
        bpy.ops.object.join_shapes()
        DeleteObject(oMeshDazImportO.name)        # Imported mesh merged into game mesh as a shape key.  It can now be deleted
        
    else:
        print("\n=== NOTE: ImportShape() did not find basis mesh.  Imported mesh becomes basis mesh.\n")
        #=== Create the basis shape key in the gameready mesh ===
        ###IMPROVE: Automate process of first main mesh creation?  (Have to 1: Create vert group '_ImportGeometryAdjustment-Breasts', 2: Duplicate orig mesh and rename, 
        oMeshDazImportO.name = oMeshDazImportO.data.name = sNameMeshPrefix
        oMeshDazImportO.name = oMeshDazImportO.data.name = sNameMeshPrefix
        bpy.ops.object.shape_key_add(from_mix=False)
    ###TODO: key_blocks["Breasts-Implants"].slider_max

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    RUNTIME BODY CONVERSION
#---------------------------------------------------------------------------    

###TEST: Testing code for bone rotation sent to Unity
# oMeshBodyO = __import__('gBlender').SelectAndActivate("WomanA");
# oArm = oMeshBodyO.modifiers["Armature"].object.data;
# __import__('gBlender').SelectAndActivate(oMeshBodyO.parent.name);
# bpy.ops.object.mode_set(mode='EDIT');
# b = oArm.edit_bones['lThumb1'];
# 
# bpy.data.objects['DummyObject'].location = b.head;
# bpy.data.objects['DummyObject'].rotation_euler = b.matrix.to_euler()
# 
# bpy.data.objects['DummyObject'].rotation_quaternion = b.matrix.to_quaternion()
# 
# 
# 
# bpy.data.objects['DummyObject'].matrix_world = oArm.edit_bones['lThumb2'].matrix
# 
# b = oArm.edit_bones['lForearmTwist'];
# 
# 
# 
# 



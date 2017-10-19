###DISCUSSION: 

###DOCS25: Sept 2017 - Body importer re-design

#- Remove vert groups after? (replace?) 
#- Need to re-assign needed vert groups!!


#----- Morphing definition -----
#- How to encapsulate different levels for each purchased level?
#- How to enforce only one morph at a time in basic modes?



#----- Penis importer -----
#- Have auto-port of vertex groups when an existing 'Penis' mesh exists.
#- Fix body importer to import bones too
    #- Will need to move bones like the mesh itself
        #- But... movement is different for some morphs!  Forced to disregard?
#- Material processing
#- Missing under vein morphs


#- Fix Unity transparency issues with eyes and eyelashes (same with Blender)
#IDEA: Use starting materials to create a 'decimate list' for the simplified body (to save manual time later)




#=== NEXT ===
#- Manually adjust Unity import parameters for each imported file: 4096 bitmap size, Normal for Normal files, etc
###BROKEN: Extra geometry on breasts: rewrite to use _CSoftBody_XXX?

#=== TODO ===
#- Write a function to pass vertex groups from one mesh to another -> Will be needed I'm sure!
#?- BUG: Needs pivot mode to be set to 3D cursor!!!!
#- Add more penis shape keys created from bone modifications
    #- Idea: Smooth to remove some problems before baking?

#?- Need to create new game mode to morph body and re-simulate bodysuit.
    #- Expand CObject and CProp into Blender
    #- CObject has specialized subclasses such as CObjectDynamic and CObjectDynamicShapeKeys
    #- CBody owns a CObjectDynamicShapeKeys and exports to Unity.
    #- Bad naming of root node?

#=== REMINDERS ===
#- Consider adding a penis smoothing command at the tail end of processing to take care of some problems like shortened shaft length

#=== DESIGN ===
#--- NEEDS ---
# Need to retain unrestrained flow with raw DAZ imports while having a programmatic modification procedure to make meshes game-ready.
#    - We need to provide more geometry at certain body areas (breasts)
#    - We need to identify groups of vertices from raw DAZ imports. (e.g. to modify mesh)
# Need to expose DAZ-provided morphs to user:
#    - Body shapes are added to the gameready source mesh.
#    - User dials in his shapes, body is refreshed in Unity and Flex collider too (pushing away bodysuit)
# Need to have a bodysuit that morphs according to ANY source body shape changes.  (shape keys, breast adjustments, penis position, etc)
#    - The 'static flex collider' is what makes this possible: a non-remeshed body (pulled back particle distance) that is a partially refined body mesh.  (e.g. not the optimized Flex collider that is remeshed for efficiency) 

#--- NEEDS2 ---
#- Need to have vertex group traversal from one 'master' body to all the derived ones.
    #- Stamp each imported verts with their original ID
    #- Will need utility to sync up all the custom vertex groups as code develops
    #Q: Do we ditch unused verts right at import of 'gold' body or adopt gold body = DAZ import?
#- Need to find common denominators between man and woman bone rig
    #-Q: DAZ Man can adopt the same bone restraints as woman?
#- Need to provide a default shape that is exactly Victoria 7 so DAZ dynamic clothing can adapt to
#- Need to modify some part of geometry upon import (e.g. extra geometry on breasts)
    #- So... we need an untouched DAZ body to determine which vert or do we count on removal of extra verts to always return same topology?
#- Need to perform expensive processing at this stage to remove it from gametime processing:  Some examples:
    #- Pre-processing for breast morphs

#--- PLANNING ---
#- Remove all that crap about first import / next imports for shape keys -> will now import ALL morphs in one go!
    #- Same with the crappy fixes because of bad pose & orientation -> now into import step
###IDEA: Have penis for shemale pulled from male mesh at default pose
    #- Morphs for penis itself applied at male mesh with body-part all at default
#- Need to convert shemale creation stuff to pull penis directly out of man mesh (after user morphs) instead of separated penis

#=== IDEAS ===

#=== PROBLEMS ===
#- Anus texture problem.  Area is too small for its own texture -> Map into another texture when we improve vagina.
    #- Same with labia texture? (Merge with vagina)
    #- Currently merged the whole crapload into one texture (Anus) -> But do UV remap soon!
        #- Then what do we do about DAZ imports??  Would new UV map break??  (Can we fix problem in DAZ??)
#- What do we do with materials that use twice the same texture?  (One for diffuse and one for transparency??)
#+ Currently the two +VaginaHole-Upper/Lower bones must be defined manually!

#=== QUESTIONS ===
#- Previous breast morphing needs heavy pre-computation... Can this be redone by quickly 'walking the quads' to blend to base as we morph?

#=== LEARNED ===
#- To view DAZ raw bone properties, load and activate a model, go to 'Parameters' tab, select a bone (like 'Left Shin', activate 'Edit mode' (tiny context menu above tab), view properties unde 'Rigging' such as x,y,z Origin, end and Orientation

#=== TEST CODE ===
# oMesh = bpy.data.objects["Woman-Original"]
# oArm = oMesh.modifiers["Armature"].object.data
# oArmBones = oArm.edit_bones
# oMesh = bpy.data.objects["Woman-Original"]; oArm = oMesh.modifiers["Armature"].object.data; oArmBones = oArm.edit_bones
# oMesh = bpy.data.objects["Genesis3Female.Shape"]; oArm = oMesh.modifiers["Genesis3Female"].object.data; oArmBones = oArm.edit_bones

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
    

#=== IMPORT PROCEDURE ===
#=== Instructions for a full import ===
#- DAZ export options must set 'Embed Texture', 'Merge Diffuse and Opacity Textures', 'Merge Clothing into Figure Skeleton', 'Allow Degraded Skinning' and 'Allow Degraded Scaling'.  Everything must be 'baked' except morphs we want imported as shape keys.  Choose FBX 2014 - Binary as format
#- Import the original body by importing FBX body with all options turned off, scale set to '100' (to counter DAZ saving at 0.01)
#- Running the 'Import Original Body'.  It will unpack the textures in the Blend file's 'texture' subdirectory and automatically change its internal filenames, material names, texture names, image names to match
#- Externally rename the texture files in File Explorer as appropriate and relink Blend file to their new names by updating Blender's filename as well.
#- Move the textures to Unity's subfolder and select 'Find missing files' to relink to their final position.
#- Run the 'Synchronize Image Names' so Blender renames textures and images to the image filename.
#- Enter all the needed vertex groups into Original body for _CSoftBody_XXX definitions, _CFlexCollider, _CVagina_xxx, etc
#- Import the 'Source' body via FBX (again with all FBX import options off) and run the'Import Source Body' function


import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

import G
from gBlender import *
from CMesh import *
import CHoleRig


C_CreateBoneRigVisualizer = False       # When true creates a 'bone visualizer rig' that creates a large quantity of visualizer gizmos for each node to precisely visualize the bone rig and its angles (instrumental during development)



class CBodyImporter_Base():          # CBodyImporter_Base: In charge of heavily modifying raw DAZ bodies into a form we can used for further Blender + Unity modifications.  This class is the 'base' and provides common functions for CBodyImporter_Original and CBodyImporter_Source
    def __init__(self, sNameSuffix):
        self.sNameSuffix            = sNameSuffix       # Name suffix appended to our self.oMesh as specified by subclass (either '-Original' or '-Source')
        self.sNamePrefix            = ""                # The prefix we will give this new mesh type.  (Either 'Man' or 'Woman')
        self.sNamePrefix_Daz        = ""                # The name DAZ gives the armature object and the mesh (suffixed with '.Shape')  Like 'Genesis3Female' or 'Genesis3Male'
        self.sNamePrefix_Material   = ""                # The prefix applied to each material (also for texture & image??)
        self.sNameArmatureNode      = ""                # Name given to our armature node.  Always "[" + self.sNamePrefix + "]"
        self.oMesh                  = None              # The mesh this instance processes.  Is the 'original' (untouched) mesh for CBodyImporter_Original subclass and the 'source' mesh (heavily modified) for CBodyImporter_Source subclass 
        self.bIsWoman               = None
        self.bIsMan                 = None

        #=== Detect what type of mesh the user has imported from Daz from the existance of known .  We can process either a "Genesis 3 Male" or "Genesis 3 Female" body ===        
        if "Genesis3Female" in bpy.data.objects:
            self.bIsWoman           = True
            self.bIsMan             = False
            self.sNamePrefix_Daz    = "Genesis3Female"
            self.sNamePrefix        = "Woman"
        elif "Genesis3Male" in bpy.data.objects:
            self.bIsMan             = True
            self.bIsWoman           = False
            self.sNamePrefix_Daz    = "Genesis3Male"
            self.sNamePrefix        = "Man"
        else:
            raise Exception("###EXCEPTION: CBodyImporter.ctor() can't find a raw source mesh to process.")
        self.sNameArmatureNode      = "[" + self.sNamePrefix + "]"
        self.sNamePrefix_Material   = "_" + self.sNamePrefix + "_"              ###INFO: First "_" indicates a material managed by this codebase, second "_" to separate prefix from actual material name

        #=== First-order intialization of the raw DAZ mesh ===
        self.oMesh = CMesh.Attach(self.sNamePrefix_Daz + ".Shape")              # The DAZ exporter appends '.Shape' to the actual body mesh.
        self.oMesh.SetName(self.sNamePrefix + self.sNameSuffix)
        self.oMesh.GetMesh().show_all_edges = True
        SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)
    
        #=== Remove the root node's children that are NOT the expected mesh names (Deletes unwanted DAZ nodes like separated genitals) ===
        oRootNodeO = SelectObject(self.oMesh.GetMesh().parent.name, True)     # Select parent node (owns the bone rig)
        for oChildNodesO in oRootNodeO.children:
            if oChildNodesO.name != self.oMesh.GetName():
                DeleteObject(oChildNodesO.name)

        if self.oMesh.Open():
            bpy.ops.mesh.customdata_custom_splitnormals_clear()         ###INFO:!! Fixes the annoying 'Invalid clnors in this fan!' warnings... See https://blender.stackexchange.com/questions/77332/invalid-clnors-in-this-fan-warning  ###CHECK:!! Are custom loop normal useful for anything?  Placing in this super-important call appropriate for all contexts?  (Can damage some meshes??)
            bpy.ops.mesh.select_all(action='DESELECT')          ###CHECK: No longer required?  What happened to export / import?
            bpy.ops.object.vertex_group_sort(sort_type='NAME')
            self.oMesh.Close()
        
        #=== Lock up all the DAZ vertex groups for protection ===
        self.oMesh.VertGrp_LockUnlock(True, G.C_RexPattern_EVERYTHING)
            
    
    def Materials_MergeSlavesToMasters(self, bDefineResources):
        self.oMesh.Material_Remove("EyeMoisture")       # Completely remove 'EyeMoisture' and associated verts in both original and source bodies.

        #=== Define the map of 'master material' (first in each sub-list) to the 'slave materials (after first in each list).  The verts of each slave material are assigned to the master one (and the slave material is destroyed)        
        mapTexturesToMaterials = [ 
            [ "Arms",           "Fingernails"                           ],
            [ "Legs",           "Toenails"                              ],
            [ "Face",           "Lips",         "Ears",     "EyeSocket" ],
            [ "Mouth",          "Teeth"                                 ],
            [ "Cornea",         "Pupils",       "Sclera",   "Irises"    ],
            [ "Vagina&Rectum",  "Labia Minora", "Torso",    "Anus"      ]      ###TODO25:!!!! Coalescing all genitals texture into one as the insane separation is bad and UVs are aweful!  Redo this crap with new UV mapping and new texture for all genitals area!!  GensMap, d51 / d49=Vagina, d50=Anus ###BROKEN: d49 and d50 are very similar but NOT the same!  One for anus, other for vagina = Will remap anyways!
        ]

        #=== Merge the slave materials into the master ones using the table above ===
        for aTexturesToMaterials in mapTexturesToMaterials:
            sNameMaterialMaster = aTexturesToMaterials[0]
            for sNameMaterialSlave in aTexturesToMaterials[1:]:
                self.oMesh.Material_Remove(sNameMaterialSlave, sNameMaterialDestination = sNameMaterialMaster)

        #=== Unpack all the image files the FBX importer packed into our .blend file to store them in the 'texture' subfolder of this .blend file.  We need to manually rename and merge them ===
        if bDefineResources:
            bpy.ops.file.unpack_all(method='WRITE_LOCAL')
        
        #=== Create a mapping of old image filenames toward those we want ===
        self.Util_PrintMaterialToImageMapping("\n=== Material-to-Image mapping (before auto-mapping) ===")
        mapOldImageNameToNewImageName = [
            ["Torso",       "Torso"],        
            ["Arms",        "Arms"],        
            ["Legs",        "Legs"],        
            ["Face",        "Face"],        
            ["Eyes",        "Eyes"],        
            ["Eyelashes",   "Eyelashes"],        
            ["Mouth",       "Mouth"],        
            ["d51",         "Vagina&Rectum"],          # Image names DAZ to vagina inners   ###HACK: Right now only keeping d50 = Anus to become master texture for genitals area = the least bad one!    
#            ["d50",         "Anus"],          # Image names DAZ gives to vagina outer / labia (Should be different than 'Vagina' maps but too many maps -> will remap UVs anyways!        
#            ["GensMap",     "VaginaArea"],        
#            ["d51",         "VaginaArea"]        
        ]
        
        #=== Automatically rename the old file names to the names we want.  This saves the manual step of having to manually edit Blender's image filepath.  Update as required ===
        ###NOTE: This assumes the user has manually renamed the image files according to this same mapping!
        if bDefineResources:
            for oMat in self.oMesh.GetMeshData().materials:             # Enumerate the current mapping of materia -> texture -> image -> image filepath so user can visualize what material uses what image
                for oTexSlot in oMat.texture_slots:                     # Also iterate through all the textures of this material (and all their related images) to prepend our prefix as well.  (So they don't get deleted by Cleanup call below!)
                    if oTexSlot is not None:
                        oTex = oTexSlot.texture
                        oImg = oTex.image
                        sImageFilename, sImageFilenameExtension = CBodyImporter_Original.Util_ExtractFilenameFromFilepath(oImg.filepath)
                        bFoundMatch = False
                        for aOldImageNameToNewImageName in mapOldImageNameToNewImageName:
                            sNameOld = aOldImageNameToNewImageName[0]
                            sNameNew = aOldImageNameToNewImageName[1]
                            if sImageFilename.find(sNameOld) != -1:
                                print("- Mapped old image filename '{}' ->  \t'{}'".format(sImageFilename, sNameNew))
                                sImageFilename = self.sNamePrefix_Material + sNameNew
                                bFoundMatch = True
                                break
                        if bFoundMatch:
                            ###NOTE: Assemble the filename from 1) the .blend 'texture' subfolder Blender used during unpack above, 2) the prefix underscore to indicate this resource is managed by this codebase, 3) the name of our body sex ('Man', 'Woman'), 4) the separating '_' between sex and resource name, 5) the name of this resource (e.g. 'Torso', 'Arms', 'Legs', etc), 6) a separating '_', 7) the 'texture set suffix' ('A', 'B', 'C'...) and 8) the filename extension
                            oImg.filepath = "//textures/" + sImageFilename + "_A" + sImageFilenameExtension     ###WEAK: Setting all filenames to the 'A' texture set... any value in getting an argument for this??    
                            oMat.name = oTex.name = oImg.name = sImageFilename      # Sync up the material name, the texture name, the image name all to be equal to the image filename -> Four level of indirections all synced up = greatly saves confusion!!
                        else:
                            print("#WARNING: Could not auto-match image filename '{}' to any known symbol.  Manual renaming of this resource will be required!".format(sImageFilename))
        else:           # Not defining resources = Source mesh being imported.  Copy materials from Original mesh into source mesh.  (Old source materials will get deleted in Cleanup call below)
            oMeshOriginal = CMesh.Attach(self.sNamePrefix + "-Original")
            aMatSlots_Original = oMeshOriginal.GetMesh().material_slots
            aMatSlots_Source   =    self.oMesh.GetMesh().material_slots
            if len(aMatSlots_Original) != len(aMatSlots_Source):
                raise Exception("\n###EXCEPTION: Mismatch in material slots between Original and Source meshes!")
            for nMatSlot in range(len(aMatSlots_Original)):
                oMatSlot_Original = aMatSlots_Original[nMatSlot]
                oMatSlot_Source   = aMatSlots_Source  [nMatSlot]
                oMatSlot_Source.material = oMatSlot_Original.material
        
        self.Util_PrintMaterialToImageMapping("\n=== Material-to-Image mapping (after auto-mapping) ===")

        #=== Cleanup the extra materials (created by extra meshes imported by FBX) === 
        Cleanup_MaterialsTexturesImages()               # Any material, texture or image that doesn't start with the "_" prefix gets deleted!



    def Util_PrintMaterialToImageMapping(self, sMsg):
        print(sMsg)
        for oMat in self.oMesh.GetMeshData().materials:             # Enumerate the current mapping of materia -> texture -> image -> image filepath so user can visualize what material uses what image
            for oTexSlot in oMat.texture_slots:                     # Also iterate through all the textures of this material (and all their related images) to prepend our prefix as well.  (So they don't get deleted by Cleanup call below!)
                if oTexSlot is not None:
                    oTex = oTexSlot.texture
                    oImg = oTex.image
                    sImageFilepath = oImg.filepath
                    print("- Mat '{}' -> \tTex '{}' -> \tImg '{}' \tImgFile '{}'".format(oMat.name, oTex.name, oImg.name, sImageFilepath))
        
    @classmethod
    def Util_ExtractFilenameFromFilepath(cls, sFilepath):           ###MOVE:?
        nPosLastSlash = sFilepath.rfind("\\")
        if nPosLastSlash == -1:
            nPosLastSlash = sFilepath.rfind("/")
            if nPosLastSlash == -1:
                raise Exception("\n###EXCEPTION: Util_ExtractFilenameFromFilepath could not find last slash in filepath '{}'".format(sFilepath))
        sImageFilenamePlusExt = sFilepath[nPosLastSlash+1:]
        nPosDot = sImageFilenamePlusExt.rfind(".")
        if nPosDot == -1:
            raise Exception("\n###EXCEPTION: Util_ExtractFilenameFromFilepath could not find extension dot in filepath '{}'".format(sFilepath))
        sFilename           = sImageFilenamePlusExt[:nPosDot]
        sFilenameExtension  = sImageFilenamePlusExt[nPosDot:]
        return sFilename, sFilenameExtension

    #---------------------------------------------------------------------------    IMPORT COMMONS
    def Import_AddBone(self, sNameBoneNew, sNameBoneParent, vecLocation = None):
        oBoneNew = self.oArmBones.new(sNameBoneNew)
        oBoneNew.parent = self.oArmBones[sNameBoneParent]
        if vecLocation is None:
            oBoneNew.use_connect = True
            oBoneNew.head = oBoneNew.parent.tail
        else:
            oBoneNew.use_connect = False
            oBoneNew.head = vecLocation
        oBoneNew.tail = oBoneNew.head + Vector((0,0,0.001))       # We *must* have head <> tail or bone will get deleted without warning by Blender!!
        return oBoneNew
        


    ########################################################################    DAZ IMPORT

    def Bones_DefineFromDazInfo(self):
        #=== Create all the CBone objects from the armature's edit bone rig ===
        bpy.ops.object.mode_set(mode='EDIT')                # *Must* have armature selected and in edit mode to obtain edit bone objects!
        for oBoneO in self.oArmBones:
            oBone = CBone(oBoneO.name)
            if oBoneO.parent is not None:
                oBone.sNameBoneParent = oBoneO.parent.name
            self.mapBones[oBoneO.name] = oBone          # Remember our CBone object for each bone name (e.g. flattened hierarchy)
        bpy.ops.object.mode_set(mode='OBJECT')              # *Must* be in object mode to create bone rig visualizer nodes!
 
        #===== OPTIONALLY CREATE BONE RIG VISUALIZATION OBJECTS =====
        if C_CreateBoneRigVisualizer:
            print("\n\n=== CreateVisibleBoneRig() ===")
            for sNameBone in self.mapBones:                    # Bone visualizer' stuff.  Creates a collection of Blender nodes to perfectly mirror a working bone structure.  Was instrumental in making bone orientation work before Blender's horrible 'roll' problem was fixed!!    
                oBone = self.mapBones[sNameBone]
    
                #=== Create the actual 'fake bone' as an empty with axes.  As this node is the only one oriented and parented to bone chain this is the only one we rotate to simulate rigging ===
                bpy.ops.object.empty_add(type='ARROWS')
                oBone.oRigVis_Bone = bpy.context.object
                oBone.oRigVis_Bone.layers[2] = 1 
                oBone.oRigVis_Bone.empty_draw_size = 0.015
                oBone.oRigVis_Bone.name = "RigVisBone-" + sNameBone
                oBone.oRigVis_Bone.show_x_ray = True
                #oBone.oRigVis_Bone.parent = bpy.data.objects[G.C_NodeFolder_Temp]
                
                #=== Create the 'bone arrow' to visualize proper bone lenght and orientation ===
                oBone.oRigVis_Arrow = DuplicateAsSingleton("BoneArrow", "RigVisArrow-" + sNameBone)
                oBone.oRigVis_Arrow.layers[3] = 1 
                oBone.oRigVis_Arrow.show_x_ray = True
                oBone.oRigVis_Bone.select = True
                bpy.context.scene.objects.active = oBone.oRigVis_Bone
                bpy.ops.object.parent_set(keep_transform=True)          ###INFO: keep_transform=True is critical to prevent reparenting from destroying the previously set transform of object!!
    
                #=== Create the rotation gizmo showing Blender axes orientation ===
                oBone.oRigVis_Axes = DuplicateAsSingleton("Gizmo-Rotate-Blender", "RigVisAxes-" + sNameBone)
                oBone.oRigVis_Axes.layers[4] = 1 
                oBone.oRigVis_Axes.show_x_ray = True
                oBone.oRigVis_Bone.select = True
                bpy.context.scene.objects.active = oBone.oRigVis_Bone
                bpy.ops.object.parent_set(keep_transform=True)
    
                #=== Create the rotation gizmo showing DAZ axes orientation ===
                oBone.oRigVis_AxesDAZ = DuplicateAsSingleton("Gizmo-Rotate-Blender", "RigVisAxesDAZ-" + sNameBone)
                oBone.oRigVis_AxesDAZ.layers[5] = 1 
                oBone.oRigVis_AxesDAZ.show_x_ray = True
                oBone.oRigVis_Bone.select = True
                #bpy.context.scene.objects.active = oBone.oRigVis_Bone
                #bpy.ops.object.parent_set(keep_transform=True)
            print("==============================\n\n")

        #=== Create some 'angle debugger gizmos' to visualize the effects of various rotations ===
        #for n in range(5):
        #    DuplicateAsSingleton("Gizmo-Rotate-Blender", "AngleDebug" + str(n))


        ###NOTE20: DAZ bone structures orients rotation 0,0,0 differently based on which part of the body!  (Hugely confusing and inconvenient)
        # From observation in DAZ derived from setting every bone to 0,0,0 orientation and witnessing how they are oriented the following was observed:
        # Forward/Backward: Foot and descendants, Pectorals, Upper Face Rig descendants ONLY, Eyes, UpperTeeth, LowerJaw and descendants
        # Left/Right: Collar and descendants, Ear
        # All other bones are up/down
        # The following code sequence will flag which bone has which orientation correctly: (must be done in order)
        # - Flag every bone Up/Down
        # - Flag lrFoot and descendants Forward/Backward
        # - Flag lrCollar and descendants Left/Right
        # - Flag Head and descendants Forward/Backward
        # - Flag Head Up/Down
        # - Flag UpperFaceRig Up/Down
        # - Flag lrEars Left/Right
        # - Flag lrPectorals Forward/Backward
 
        print("\n=== Bones_DefineFromDazInfo() ===")
        SelectObject(self.oMesh.GetMesh().parent.name)           
        bpy.ops.object.mode_set(mode='EDIT')                                        ###INFO: Modifying armature bones is done by simply editing root node containing armature.
        self.BoneFix_SetOrientationFlag_RECURSIVE('D', self.oArmBones['hip'])
        self.BoneFix_SetOrientationFlag_RECURSIVE('U', self.oArmBones['abdomenLower'])
        self.BoneFix_SetOrientationFlag_RECURSIVE('F', self.oArmBones['lFoot'])
        self.BoneFix_SetOrientationFlag_RECURSIVE('F', self.oArmBones['rFoot'])
        self.BoneFix_SetOrientationFlag_RECURSIVE('L', self.oArmBones['lCollar'])
        self.BoneFix_SetOrientationFlag_RECURSIVE('R', self.oArmBones['rCollar'])
        self.BoneFix_SetOrientationFlag_RECURSIVE('F', self.oArmBones['head'])
        self.BoneFix_SetOrientationFlag('U', self.oArmBones['head'])                # Manual override of DAZ bones that can't be recursively set
        self.BoneFix_SetOrientationFlag('U', self.oArmBones['upperFaceRig'])
        self.BoneFix_SetOrientationFlag('L', self.oArmBones['lEar'])
        self.BoneFix_SetOrientationFlag('R', self.oArmBones['rEar'])
        self.BoneFix_SetOrientationFlag('F', self.oArmBones['lPectoral'])
        self.BoneFix_SetOrientationFlag('F', self.oArmBones['rPectoral'])
        self.BoneFix_SetOrientationFlag('B', self.oArmBones['lHeel'])
        self.BoneFix_SetOrientationFlag('B', self.oArmBones['rHeel'])
#         self.BoneFix_SetOrientationFlag('U', self.oArmBones['lShldrTwist'])         ###NOTE  While it would be better for Uniti's joint if these were re-oriented to take advantage of min/max on X these six exceptions make these Blender bone 'stick out' (e.g. forward no longer +Y)... What to do if unity needs these different??
#         self.BoneFix_SetOrientationFlag('U', self.oArmBones['rShldrTwist'])
#         self.BoneFix_SetOrientationFlag('U', self.oArmBones['lForearmTwist'])
#         self.BoneFix_SetOrientationFlag('U', self.oArmBones['rForearmTwist'])
#         self.BoneFix_SetOrientationFlag('L', self.oArmBones['lThighTwist'])
#         self.BoneFix_SetOrientationFlag('R', self.oArmBones['rThighTwist'])
        
        

        #===== BEGIN BONE DUMP FROM DAZ TO BLENDER - PROCEDURALLY GENERATED - DO NOT MODIFY =====
        self.Bone_Define("hip", "Hip", "YZX", 16.456575393676758, 0, 105.1781005859375, 1.8248159885406494, 0, 0, 0);
        self.Bone_AddRotation("hip", 'X', "X Rotate", -180, 180);
        self.Bone_AddRotation("hip", 'Y', "Y Rotate", -180, 180);
        self.Bone_AddRotation("hip", 'Z', "Z Rotate", -180, 180);
        self.Bone_Define("pelvis", "Pelvis", "YZX", 19.040145874023438, 0, 107.04229736328125, 1.8734849691390991, 0, 0, 0);
        self.Bone_AddRotation("pelvis", 'X', "Bend", -25, 25);
        self.Bone_AddRotation("pelvis", 'Y', "Twist", -15, 15);
        self.Bone_AddRotation("pelvis", 'Z', "Side-Side", -10, 10);
        self.Bone_Define("lThighBend", "Left Thigh Bend", "YZX", 20.88103675842285, 7.909207820892334, 96.41561889648438, 0.3913818895816803, 0.011287844739854336, 0.08677535504102707, 0.03259831294417381);
        self.Bone_AddRotation("lThighBend", 'X', "Bend", -115, 35);
        self.Bone_AddRotation("lThighBend", 'Z', "Side-Side", -20, 85);
        self.Bone_Define("lThighTwist", "Left Thigh Twist", "YZX", 21.684362411499023, 8.607954025268555, 75.4776382446289, 0.14419420063495636, 0.011287844739854336, 0.08677535504102707, 0.03259831294417381);
        self.Bone_AddRotation("lThighTwist", 'Y', "Twist", -75, 75);
        self.Bone_Define("lShin", "Left Shin", "YZX", 41.59010696411133, 9.492676734924316, 50.20000076293945, -1.350000023841858, 0.07966385036706924, 0.17445161938667297, 0.029293647035956383);
        self.Bone_AddRotation("lShin", 'X', "Bend", -11, 155);
        self.Bone_AddRotation("lShin", 'Y', "Twist", -25, 10);
        self.Bone_AddRotation("lShin", 'Z', "Side-Side", -5, 5);
        self.Bone_Define("lFoot", "Left Foot", "ZYX", 5.808509349822998, 11.607660293579102, 6.819084167480469, -3.9942378997802734, 0.4223427176475525, 0.234667107462883, -0.10411292314529419);
        self.Bone_AddRotation("lFoot", 'X', "Bend", -40, 75);
        self.Bone_AddRotation("lFoot", 'Y', "Side-Side", -25, 10);
        self.Bone_AddRotation("lFoot", 'Z', "Twist", -35, 15);
        self.Bone_Define("lMetatarsals", "Left Metatarsals", "ZYX", 5.808509826660156, 12.979610443115234, 4.568961143493652, 1.1820039749145508, 0.42234253883361816, 0.2346671223640442, -0.10411287844181061);
        self.Bone_AddRotation("lMetatarsals", 'X', "Bend", -12, 12);
        self.Bone_AddRotation("lMetatarsals", 'Z', "Twist", -20, 20);
        self.Bone_Define("lToe", "Left Toes", "ZYX", 6.094308853149414, 14.521349906921387, 1.941066026687622, 6.836697101593018, 0.25531721115112305, 0.25560346245765686, -0.03298526257276535);
        self.Bone_AddRotation("lToe", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("lToe", 'Z', "Twist", -20, 20);
        self.Bone_Define("lSmallToe4", "Left Small Toe 4", "ZYX", 1.228298544883728, 18.13075065612793, 1.588847041130066, 6.828703880310059, 0.5548501014709473, 0.1618567258119583, -0.2721669673919678);
        self.Bone_AddRotation("lSmallToe4", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("lSmallToe4", 'Y', "Side-Side", -10, 20);
        self.Bone_AddRotation("lSmallToe4", 'Z', "Twist", -5, 5);
        self.Bone_Define("lSmallToe4_2", "Left Small Toe 4_2", "ZYX", 1.3389631509780884, 18.331249237060547, 1.1486209630966187, 7.8611931800842285, 0.5548501014709473, 0.1618567258119583, -0.2721669673919678);
        self.Bone_AddRotation("lSmallToe4_2", 'X', "Bend", -30, 40);
        self.Bone_Define("lSmallToe3", "Left Small Toe 3", "ZYX", 1.5903359651565552, 16.682310104370117, 1.9516359567642212, 7.720399856567383, 0.5356007218360901, 0.24195879697799683, -0.2285248190164566);
        self.Bone_AddRotation("lSmallToe3", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("lSmallToe3", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("lSmallToe3", 'Z', "Twist", -5, 5);
        self.Bone_Define("lSmallToe3_2", "Left Small Toe 3_2", "ZYX", 1.6977434158325195, 17.095569610595703, 1.3716609477996826, 9.042989730834961, 0.5356007218360901, 0.24195866286754608, -0.22852468490600586);
        self.Bone_AddRotation("lSmallToe3_2", 'X', "Bend", -30, 50);
        self.Bone_Define("lSmallToe2", "Left Small Toe 2", "ZYX", 2.0303378105163574, 15.677519798278809, 2.329209089279175, 8.46373176574707, 0.49749305844306946, 0.2556433379650116, -0.17001400887966156);
        self.Bone_AddRotation("lSmallToe2", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("lSmallToe2", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("lSmallToe2", 'Z', "Twist", -5, 5);
        self.Bone_Define("lSmallToe2_2", "Left Small Toe 2_2", "ZYX", 2.127910852432251, 16.194700241088867, 1.6442919969558716, 10.214059829711914, 0.49749282002449036, 0.25564324855804443, -0.17001385986804962);
        self.Bone_AddRotation("lSmallToe2_2", 'X', "Bend", -30, 50);
        self.Bone_Define("lSmallToe1", "Left Small Toe 1", "ZYX", 2.30393385887146, 14.117349624633789, 2.440263032913208, 8.861557006835938, 0.42746269702911377, 0.30954381823539734, -0.16733215749263763);
        self.Bone_AddRotation("lSmallToe1", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("lSmallToe1", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("lSmallToe1", 'Z', "Twist", -5, 5);
        self.Bone_Define("lSmallToe1_2", "Left Small Toe 1_2", "ZYX", 2.3962671756744385, 14.822150230407715, 1.8007429838180542, 10.878410339355469, 0.42746251821517944, 0.3095436990261078, -0.16733203828334808);
        self.Bone_AddRotation("lSmallToe1_2", 'X', "Bend", -30, 40);
        self.Bone_Define("lBigToe", "Left Big Toe", "ZYX", 2.585862874984741, 11.740830421447754, 2.3552141189575195, 8.955074310302734, 0.3431497812271118, 0.32818466424942017, -0.14254353940486908);
        self.Bone_AddRotation("lBigToe", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("lBigToe", 'Y', "Side-Side", -15, 10);
        self.Bone_AddRotation("lBigToe", 'Z', "Twist", -5, 5);
        self.Bone_Define("lBigToe_2", "Left Big Toe_2", "ZYX", 2.5847342014312744, 12.588489532470703, 1.6088930368423462, 11.282520294189453, 0.3431495428085327, 0.3281843662261963, -0.14254333078861237);
        self.Bone_AddRotation("lBigToe_2", 'X', "Bend", -30, 60);
        self.Bone_Define("lHeel", "Left Heel", "ZYX", 8.175668716430664, 11.783289909362793, 6.178731918334961, -3.198975086212158, -0.7916287779808044, 0.13166145980358124, 0.13215285539627075);
        self.Bone_AddRotation("lHeel", 'X', "Bend", -30, 20);
        self.Bone_AddRotation("lHeel", 'Y', "Side-Side", -8, 8);
        self.Bone_AddRotation("lHeel", 'Z', "Twist", -15, 15);
        self.Bone_Define("rThighBend", "Right Thigh Bend", "YZX", 20.88103675842285, -7.909207820892334, 96.41561889648438, 0.3913818895816803, 0.011287841945886612, -0.08677535504102707, -0.03259831294417381);
        self.Bone_AddRotation("rThighBend", 'X', "Bend", -115, 35);
        self.Bone_AddRotation("rThighBend", 'Z', "Side-Side", -85, 20);
        self.Bone_Define("rThighTwist", "Right Thigh Twist", "YZX", 21.684362411499023, -8.607954025268555, 75.4776382446289, 0.14419420063495636, 0.011287841945886612, -0.08677535504102707, -0.03259831294417381);
        self.Bone_AddRotation("rThighTwist", 'Y', "Twist", -75, 75);
        self.Bone_Define("rShin", "Right Shin", "YZX", 41.59010696411133, -9.492676734924316, 50.20000076293945, -1.350000023841858, 0.07966383546590805, -0.17445158958435059, -0.02929365262389183);
        self.Bone_AddRotation("rShin", 'X', "Bend", -11, 155);
        self.Bone_AddRotation("rShin", 'Y', "Twist", -10, 25);
        self.Bone_AddRotation("rShin", 'Z', "Side-Side", -5, 5);
        self.Bone_Define("rFoot", "Right Foot", "ZYX", 5.808509349822998, -11.607660293579102, 6.819084167480469, -3.9942378997802734, 0.4223427176475525, -0.234667107462883, 0.10411291569471359);
        self.Bone_AddRotation("rFoot", 'X', "Bend", -40, 75);
        self.Bone_AddRotation("rFoot", 'Y', "Side-Side", -10, 25);
        self.Bone_AddRotation("rFoot", 'Z', "Twist", -15, 35);
        self.Bone_Define("rMetatarsals", "Right Metatarsals", "ZYX", 5.808509826660156, -12.979610443115234, 4.568961143493652, 1.1820039749145508, 0.42234253883361816, -0.2346671223640442, 0.10411287099123001);
        self.Bone_AddRotation("rMetatarsals", 'X', "Bend", -12, 12);
        self.Bone_AddRotation("rMetatarsals", 'Z', "Twist", -20, 20);
        self.Bone_Define("rToe", "Right Toes", "ZYX", 6.094308853149414, -14.521349906921387, 1.941066026687622, 6.836697101593018, 0.25531721115112305, -0.25560346245765686, 0.03298526257276535);
        self.Bone_AddRotation("rToe", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("rToe", 'Z', "Twist", -20, 20);
        self.Bone_Define("rSmallToe4", "Right Small Toe 4", "ZYX", 1.228298544883728, -18.13075065612793, 1.588847041130066, 6.828703880310059, 0.5548501014709473, -0.1618567258119583, 0.2721669673919678);
        self.Bone_AddRotation("rSmallToe4", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("rSmallToe4", 'Y', "Side-Side", -20, 10);
        self.Bone_AddRotation("rSmallToe4", 'Z', "Twist", -5, 5);
        self.Bone_Define("rSmallToe4_2", "Right Small Toe 4_2", "ZYX", 1.3389631509780884, -18.331249237060547, 1.1486209630966187, 7.8611931800842285, 0.5548501014709473, -0.1618567407131195, 0.2721669375896454);
        self.Bone_AddRotation("rSmallToe4_2", 'X', "Bend", -30, 40);
        self.Bone_Define("rSmallToe3", "Right Small Toe 3", "ZYX", 1.5903359651565552, -16.682310104370117, 1.9516359567642212, 7.720399856567383, 0.5356007218360901, -0.24195881187915802, 0.2285248041152954);
        self.Bone_AddRotation("rSmallToe3", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("rSmallToe3", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("rSmallToe3", 'Z', "Twist", -5, 5);
        self.Bone_Define("rSmallToe3_2", "Right Small Toe 3_2", "ZYX", 1.6977434158325195, -17.095569610595703, 1.3716609477996826, 9.042989730834961, 0.5356006622314453, -0.24195867776870728, 0.22852468490600586);
        self.Bone_AddRotation("rSmallToe3_2", 'X', "Bend", -30, 50);
        self.Bone_Define("rSmallToe2", "Right Small Toe 2", "ZYX", 2.0303378105163574, -15.677519798278809, 2.329209089279175, 8.46373176574707, 0.49749305844306946, -0.2556433379650116, 0.17001400887966156);
        self.Bone_AddRotation("rSmallToe2", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("rSmallToe2", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("rSmallToe2", 'Z', "Twist", -5, 5);
        self.Bone_Define("rSmallToe2_2", "Right Small Toe 2_2", "ZYX", 2.127910852432251, -16.194700241088867, 1.6442919969558716, 10.214059829711914, 0.49749279022216797, -0.25564324855804443, 0.17001384496688843);
        self.Bone_AddRotation("rSmallToe2_2", 'X', "Bend", -30, 50);
        self.Bone_Define("rSmallToe1", "Right Small Toe 1", "ZYX", 2.30393385887146, -14.117349624633789, 2.440263032913208, 8.861557006835938, 0.42746269702911377, -0.30954381823539734, 0.16733215749263763);
        self.Bone_AddRotation("rSmallToe1", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("rSmallToe1", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("rSmallToe1", 'Z', "Twist", -5, 5);
        self.Bone_Define("rSmallToe1_2", "Right Small Toe 1_2", "ZYX", 2.3962671756744385, -14.822150230407715, 1.8007429838180542, 10.878410339355469, 0.42746251821517944, -0.3095436990261078, 0.16733203828334808);
        self.Bone_AddRotation("rSmallToe1_2", 'X', "Bend", -30, 40);
        self.Bone_Define("rBigToe", "Right Big Toe", "ZYX", 2.585862874984741, -11.740830421447754, 2.3552141189575195, 8.955074310302734, 0.3431497812271118, -0.32818466424942017, 0.14254353940486908);
        self.Bone_AddRotation("rBigToe", 'X', "Bend", -65, 45);
        self.Bone_AddRotation("rBigToe", 'Y', "Side-Side", -10, 15);
        self.Bone_AddRotation("rBigToe", 'Z', "Twist", -5, 5);
        self.Bone_Define("rBigToe_2", "Right Big Toe_2", "ZYX", 2.5847342014312744, -12.588489532470703, 1.6088930368423462, 11.282520294189453, 0.3431495428085327, -0.3281843662261963, 0.14254333078861237);
        self.Bone_AddRotation("rBigToe_2", 'X', "Bend", -30, 60);
        self.Bone_Define("rHeel", "Right Heel", "ZYX", 8.175668716430664, -11.783289909362793, 6.178731918334961, -3.198975086212158, -0.7916287779808044, -0.13166147470474243, -0.13215285539627075);
        self.Bone_AddRotation("rHeel", 'X', "Bend", -30, 20);
        self.Bone_AddRotation("rHeel", 'Y', "Side-Side", -8, 8);
        self.Bone_AddRotation("rHeel", 'Z', "Twist", -15, 15);
        self.Bone_Define("abdomenLower", "Abdomen Lower", "YZX", 8.103456497192383, 0, 106.9446029663086, 0.3423211872577667, 0, 0, 0);
        self.Bone_AddRotation("abdomenLower", 'X', "Bend", -20, 35);
        self.Bone_AddRotation("abdomenLower", 'Y', "Twist", -15, 15);
        self.Bone_AddRotation("abdomenLower", 'Z', "Side-Side", -15, 15);
        self.Bone_Define("abdomenUpper", "Abdomen Upper", "YZX", 7.532998085021973, 0, 115.0947036743164, 1.5356700420379639, 0, 0, 0);
        self.Bone_AddRotation("abdomenUpper", 'X', "Bend", -25, 40);
        self.Bone_AddRotation("abdomenUpper", 'Y', "Twist", -20, 20);
        self.Bone_AddRotation("abdomenUpper", 'Z', "Side-Side", -24, 24);
        self.Bone_Define("chestLower", "Chest Lower", "YZX", 20.73139190673828, 0, 123, 1.1382969617843628, 0, 0, 0);
        self.Bone_AddRotation("chestLower", 'X', "Bend", -25, 35);
        self.Bone_AddRotation("chestLower", 'Y', "Twist", -12, 12);
        self.Bone_AddRotation("chestLower", 'Z', "Side-Side", -20, 20);
        self.Bone_Define("chestUpper", "Chest Upper", "YZX", 13.440155982971191, 0, 136.07650756835938, -2.479732036590576, 0, 0, 0);
        self.Bone_AddRotation("chestUpper", 'X', "Bend", -15, 15);
        self.Bone_AddRotation("chestUpper", 'Y', "Twist", -10, 10);
        self.Bone_AddRotation("chestUpper", 'Z', "Side-Side", -10, 10);
        self.Bone_Define("lCollar", "Left Collar", "XYZ", 12.724119186401367, 1.6138900518417358, 146.50999450683594, -4.110317230224609, 0.0009373133070766926, 0.06126770004630089, 0.030585339292883873);
        self.Bone_AddRotation("lCollar", 'X', "Twist", -30, 30);
        self.Bone_AddRotation("lCollar", 'Y', "Front-Back", -26, 17);
        self.Bone_AddRotation("lCollar", 'Z', "Bend", -10, 50);
        self.Bone_Define("lShldrBend", "Left Shoulder Bend", "XYZ", 12.618949890136719, 14.845450401306152, 146.39329528808594, -4.8656229972839355, 0.0009215031750500202, -0.029385913163423538, -0.06269227713346481);
        self.Bone_AddRotation("lShldrBend", 'Y', "Front-Back", -110, 40);
        self.Bone_AddRotation("lShldrBend", 'Z', "Bend", -85, 35);
        self.Bone_Define("lShldrTwist", "Left Shoulder Twist", "XYZ", 14.49560546875, 27.416479110717773, 145.5843963623047, -4.549983024597168, 0.0007394360727630556, -0.022418437525629997, -0.06594010442495346);
        self.Bone_AddRotation("lShldrTwist", 'X', "Twist", -95, 80);
        self.Bone_Define("lForearmBend", "Left Forearm Bend", "XZY", 12.209012031555176, 41.84933090209961, 144.84759521484375, -4.676486015319824, 0.001426273607648909, -0.2939295470714569, 0.00963482167571783);
        self.Bone_AddRotation("lForearmBend", 'Y', "Bend", -135, 20);
        self.Bone_Define("lForearmTwist", "Left Forearm Twist", "XZY", 14.429741859436035, 53.450531005859375, 145.1009063720703, -1.1527260541915894, 0.0016623962437734008, -0.2926180064678192, 0.01128092035651207);
        self.Bone_AddRotation("lForearmTwist", 'X', "Twist", -90, 80);
        self.Bone_Define("lHand", "Left Hand", "XYZ", 9.307104110717773, 67.15646362304688, 145.24220275878906, 2.656857967376709, -0.0001347102370345965, -0.017477883026003838, 0.015414240770041943);
        self.Bone_AddRotation("lHand", 'X', "Twist", -10, 10);
        self.Bone_AddRotation("lHand", 'Y', "Side-Side", -28, 30);
        self.Bone_AddRotation("lHand", 'Z', "Bend", -70, 80);
        self.Bone_Define("lThumb1", "Left Thumb 1", "XZY", 4.099705219268799, 68.57206726074219, 144.56500244140625, 4.263713836669922, -0.5664371252059937, -0.9716687202453613, -0.18946903944015503);
        self.Bone_AddRotation("lThumb1", 'X', "Twist", -15, 36);
        self.Bone_AddRotation("lThumb1", 'Y', "Bend", -26, 40);
        self.Bone_AddRotation("lThumb1", 'Z', "Up-Down", -20, 20);
        self.Bone_Define("lThumb2", "Left Thumb 2", "XZY", 2.9811923503875732, 70.79437255859375, 143.82290649414062, 7.599398136138916, -0.6207923293113708, -0.6172209978103638, -0.3551393747329712);
        self.Bone_AddRotation("lThumb2", 'Y', "Bend", -15, 65);
        self.Bone_Define("lThumb3", "Left Thumb 3", "XZY", 2.845970392227173, 73.07376861572266, 142.78619384765625, 9.217140197753906, -0.739614725112915, -0.7967870831489563, -0.22836805880069733);
        self.Bone_AddRotation("lThumb3", 'Y', "Bend", -20, 90);
        self.Bone_Define("lCarpal1", "Left Carpal 1", "XYZ", 7.841163635253906, 67.55667114257812, 145.6717987060547, 3.77862811088562, 0.008941041305661201, -0.25342613458633423, -0.07015495747327805);
        self.Bone_AddRotation("lCarpal1", 'Y', "Side-Side", -3, 4);
        self.Bone_AddRotation("lCarpal1", 'Z', "Bend", -4, 4);
        self.Bone_Define("lIndex1", "Left Index 1", "XYZ", 3.937098741531372, 74.85968017578125, 145.32980346679688, 5.7923688888549805, 0.038289934396743774, -0.16681525111198425, -0.10075650364160538);
        self.Bone_AddRotation("lIndex1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("lIndex1", 'Y', "Side-Side", -18, 12);
        self.Bone_AddRotation("lIndex1", 'Z', "Bend", -90, 50);
        self.Bone_Define("lIndex2", "Left Index 2", "XYZ", 2.087801694869995, 78.73291778564453, 144.96890258789062, 6.3994340896606445, 0.005375184118747711, -0.10030678659677505, -0.10698307305574417);
        self.Bone_AddRotation("lIndex2", 'Z', "Bend", -105, 12);
        self.Bone_Define("lIndex3", "Left Index 3", "XYZ", 2.105318307876587, 80.79827117919922, 144.74349975585938, 6.605408191680908, 0.005562583450227976, -0.08585353940725327, -0.12932321429252625);
        self.Bone_AddRotation("lIndex3", 'Z', "Bend", -90, 20);
        self.Bone_Define("lCarpal2", "Left Carpal 2", "XYZ", 7.778314113616943, 67.82649230957031, 145.6717987060547, 2.898164987564087, 0.003749176161363721, -0.10873045772314072, -0.06886757910251617);
        self.Bone_AddRotation("lCarpal2", 'Y', "Side-Side", -2, 2);
        self.Bone_AddRotation("lCarpal2", 'Z', "Bend", -4, 4);
        self.Bone_Define("lMid1", "Left Mid 1", "XYZ", 4.330451965332031, 75.26304626464844, 145.4989013671875, 3.747955083847046, 0.011134708300232887, -0.07303324341773987, -0.046716734766960144);
        self.Bone_AddRotation("lMid1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("lMid1", 'Y', "Side-Side", -12, 12);
        self.Bone_AddRotation("lMid1", 'Z', "Bend", -95, 50);
        self.Bone_Define("lMid2", "Left Mid 2", "XYZ", 2.5224077701568604, 79.60183715820312, 145.31320190429688, 4.039403915405273, 0.006112358532845974, -0.07866387069225311, -0.1550135314464569);
        self.Bone_AddRotation("lMid2", 'Z', "Bend", -105, 12);
        self.Bone_Define("lMid3", "Left Mid 3", "XYZ", 2.19832444190979, 82.08627319335938, 144.9250946044922, 4.2381272315979, 0.00023900675296317786, -0.01351902075111866, -0.03535434603691101);
        self.Bone_AddRotation("lMid3", 'Z', "Bend", -90, 20);
        self.Bone_Define("lCarpal3", "Left Carpal 3", "XYZ", 7.166591644287109, 67.91168975830078, 145.6717987060547, 1.9040930271148682, -0.0005571676883846521, 0.014986051246523857, -0.07432251423597336);
        self.Bone_AddRotation("lCarpal3", 'Y', "Side-Side", -3, 3);
        self.Bone_AddRotation("lCarpal3", 'Z', "Bend", -4, 4);
        self.Bone_Define("lRing1", "Left Ring 1", "XYZ", 4.025820255279541, 74.79421997070312, 145.4022979736328, 1.8657920360565186, 0.009401836432516575, 0.046217188239097595, -0.08792509883642197);
        self.Bone_AddRotation("lRing1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("lRing1", 'Y', "Side-Side", -12, 12);
        self.Bone_AddRotation("lRing1", 'Z', "Bend", -90, 50);
        self.Bone_Define("lRing2", "Left Ring 2", "XYZ", 2.1871230602264404, 78.80277252197266, 145.07290649414062, 1.6919070482254028, 0.04125627875328064, 0.03300696611404419, -0.09355665743350983);
        self.Bone_AddRotation("lRing2", 'Z', "Bend", -105, 12);
        self.Bone_Define("lRing3", "Left Ring 3", "XYZ", 2.071528911590576, 80.97913360595703, 144.86849975585938, 1.6199480295181274, -0.0008321497007273138, 0.019539307802915573, -0.08512280881404877);
        self.Bone_AddRotation("lRing3", 'Z', "Bend", -90, 20);
        self.Bone_Define("lCarpal4", "Left Carpal 4", "XYZ", 6.580689907073975, 67.91320037841797, 145.6741943359375, 0.9899755716323853, -0.008366146124899387, 0.1708342283964157, -0.09762921929359436);
        self.Bone_AddRotation("lCarpal4", 'Y', "Side-Side", -4, 3);
        self.Bone_AddRotation("lCarpal4", 'Z', "Bend", -4, 4);
        self.Bone_Define("lPinky1", "Left Pinky 1", "XYZ", 2.791006326675415, 74.25045776367188, 144.81500244140625, -0.15924230217933655, 0.015016209334135056, 0.10176001489162445, -0.07678931206464767);
        self.Bone_AddRotation("lPinky1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("lPinky1", 'Y', "Side-Side", -12, 18);
        self.Bone_AddRotation("lPinky1", 'Z', "Bend", -90, 50);
        self.Bone_Define("lPinky2", "Left Pinky 2", "XYZ", 1.682206153869629, 77.02149200439453, 144.61439514160156, -0.4254043996334076, -0.03949618339538574, 0.10789809376001358, -0.06895863264799118);
        self.Bone_AddRotation("lPinky2", 'Z', "Bend", -105, 12);
        self.Bone_Define("lPinky3", "Left Pinky 3", "XYZ", 1.7203006744384766, 78.69294738769531, 144.49949645996094, -0.6014683246612549, -0.07169796526432037, 0.10800378769636154, -0.07309164106845856);
        self.Bone_AddRotation("lPinky3", 'Z', "Bend", -90, 20);
        self.Bone_Define("rCollar", "Right Collar", "XYZ", 12.724119186401367, -1.6138900518417358, 146.50999450683594, -4.110317230224609, 0.0009373133070766926, -0.06126770004630089, -0.030585339292883873);
        self.Bone_AddRotation("rCollar", 'X', "Twist", -30, 30);
        self.Bone_AddRotation("rCollar", 'Y', "Front-Back", -17, 26);
        self.Bone_AddRotation("rCollar", 'Z', "Bend", -50, 10);
        self.Bone_Define("rShldrBend", "Right Shoulder Bend", "XYZ", 12.618949890136719, -14.845450401306152, 146.39329528808594, -4.8656229972839355, 0.0009215031750500202, 0.029385913163423538, 0.06269227713346481);
        self.Bone_AddRotation("rShldrBend", 'Y', "Front-Back", -40, 110);
        self.Bone_AddRotation("rShldrBend", 'Z', "Bend", -35, 85);
        self.Bone_Define("rShldrTwist", "Right Shoulder Twist", "XYZ", 14.49560546875, -27.416479110717773, 145.5843963623047, -4.549983024597168, 0.0007394360727630556, 0.022418437525629997, 0.06594010442495346);
        self.Bone_AddRotation("rShldrTwist", 'X', "Twist", -95, 80);
        self.Bone_Define("rForearmBend", "Right Forearm Bend", "XZY", 12.209012031555176, -41.84933090209961, 144.84759521484375, -4.676486015319824, 0.001426273607648909, 0.2939295470714569, -0.00963482167571783);
        self.Bone_AddRotation("rForearmBend", 'Y', "Bend", -20, 135);
        self.Bone_Define("rForearmTwist", "Right Forearm Twist", "XZY", 14.429741859436035, -53.450531005859375, 145.1009063720703, -1.1527260541915894, 0.0016623957781121135, 0.2926180064678192, -0.01128092035651207);
        self.Bone_AddRotation("rForearmTwist", 'X', "Twist", -90, 80);
        self.Bone_Define("rHand", "Right Hand", "XYZ", 9.307104110717773, -67.15646362304688, 145.24220275878906, 2.656857967376709, -0.00013471022248268127, 0.017477883026003838, -0.015414240770041943);
        self.Bone_AddRotation("rHand", 'X', "Twist", -10, 10);
        self.Bone_AddRotation("rHand", 'Y', "Side-Side", -30, 28);
        self.Bone_AddRotation("rHand", 'Z', "Bend", -80, 70);
        self.Bone_Define("rThumb1", "Right Thumb 1", "XZY", 4.099705219268799, -68.57206726074219, 144.56500244140625, 4.263713836669922, -0.5664371252059937, 0.9716687202453613, 0.18946903944015503);
        self.Bone_AddRotation("rThumb1", 'X', "Twist", -15, 36);
        self.Bone_AddRotation("rThumb1", 'Y', "Bend", -40, 26);
        self.Bone_AddRotation("rThumb1", 'Z', "Up-Down", -20, 20);
        self.Bone_Define("rThumb2", "Right Thumb 2", "XZY", 2.9811923503875732, -70.79437255859375, 143.82290649414062, 7.599398136138916, -0.6207923293113708, 0.6172209978103638, 0.3551393747329712);
        self.Bone_AddRotation("rThumb2", 'Y', "Bend", -65, 15);
        self.Bone_Define("rThumb3", "Right Thumb 3", "XZY", 2.845970392227173, -73.07376861572266, 142.78619384765625, 9.217140197753906, -0.739614725112915, 0.7967870831489563, 0.22836805880069733);
        self.Bone_AddRotation("rThumb3", 'Y', "Bend", -90, 20);
        self.Bone_Define("rCarpal1", "Right Carpal 1", "XYZ", 7.841163635253906, -67.55667114257812, 145.6717987060547, 3.77862811088562, 0.008941040374338627, 0.25342613458633423, 0.07015495747327805);
        self.Bone_AddRotation("rCarpal1", 'Y', "Side-Side", -4, 3);
        self.Bone_AddRotation("rCarpal1", 'Z', "Bend", -4, 4);
        self.Bone_Define("rIndex1", "Right Index 1", "XYZ", 3.937098741531372, -74.85968017578125, 145.32980346679688, 5.7923688888549805, 0.038289934396743774, 0.16681523621082306, 0.10075650364160538);
        self.Bone_AddRotation("rIndex1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("rIndex1", 'Y', "Side-Side", -12, 18);
        self.Bone_AddRotation("rIndex1", 'Z', "Bend", -50, 90);
        self.Bone_Define("rIndex2", "Right Index 2", "XYZ", 2.087801694869995, -78.73291778564453, 144.96890258789062, 6.3994340896606445, 0.005375184118747711, 0.10030678659677505, 0.10698307305574417);
        self.Bone_AddRotation("rIndex2", 'Z', "Bend", -12, 105);
        self.Bone_Define("rIndex3", "Right Index 3", "XYZ", 2.105318307876587, -80.79827117919922, 144.74349975585938, 6.605408191680908, 0.005562582053244114, 0.08585352450609207, 0.12932321429252625);
        self.Bone_AddRotation("rIndex3", 'Z', "Bend", -20, 90);
        self.Bone_Define("rCarpal2", "Right Carpal 2", "XYZ", 7.778314113616943, -67.82649230957031, 145.6717987060547, 2.898164987564087, 0.003749176161363721, 0.10873047262430191, 0.06886757910251617);
        self.Bone_AddRotation("rCarpal2", 'Y', "Side-Side", -2, 2);
        self.Bone_AddRotation("rCarpal2", 'Z', "Bend", -4, 4);
        self.Bone_Define("rMid1", "Right Mid 1", "XYZ", 4.330451965332031, -75.26304626464844, 145.4989013671875, 3.747955083847046, 0.011134708300232887, 0.07303324341773987, 0.046716734766960144);
        self.Bone_AddRotation("rMid1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("rMid1", 'Y', "Side-Side", -12, 12);
        self.Bone_AddRotation("rMid1", 'Z', "Bend", -50, 95);
        self.Bone_Define("rMid2", "Right Mid 2", "XYZ", 2.5224077701568604, -79.60183715820312, 145.31320190429688, 4.039403915405273, 0.006112357135862112, 0.07866384088993073, 0.15501350164413452);
        self.Bone_AddRotation("rMid2", 'Z', "Bend", -12, 105);
        self.Bone_Define("rMid3", "Right Mid 3", "XYZ", 2.19832444190979, -82.08627319335938, 144.9250946044922, 4.2381272315979, 0.00023900675296317786, 0.01351902075111866, 0.03535434603691101);
        self.Bone_AddRotation("rMid3", 'Z', "Bend", -20, 90);
        self.Bone_Define("rCarpal3", "Right Carpal 3", "XYZ", 7.166591644287109, -67.91168975830078, 145.6717987060547, 1.9040930271148682, -0.0005571676883846521, -0.014986051246523857, 0.07432251423597336);
        self.Bone_AddRotation("rCarpal3", 'Y', "Side-Side", -3, 3);
        self.Bone_AddRotation("rCarpal3", 'Z', "Bend", -4, 4);
        self.Bone_Define("rRing1", "Right Ring 1", "XYZ", 4.025820255279541, -74.79421997070312, 145.4022979736328, 1.8657920360565186, 0.009401836432516575, -0.046217188239097595, 0.08792508393526077);
        self.Bone_AddRotation("rRing1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("rRing1", 'Y', "Side-Side", -12, 12);
        self.Bone_AddRotation("rRing1", 'Z', "Bend", -50, 90);
        self.Bone_Define("rRing2", "Right Ring 2", "XYZ", 2.1871230602264404, -78.80277252197266, 145.07290649414062, 1.6919070482254028, 0.04125627875328064, -0.03300696611404419, 0.09355665743350983);
        self.Bone_AddRotation("rRing2", 'Z', "Bend", -12, 105);
        self.Bone_Define("rRing3", "Right Ring 3", "XYZ", 2.071528911590576, -80.97913360595703, 144.86849975585938, 1.6199480295181274, -0.0008321497007273138, -0.019539307802915573, 0.08512280881404877);
        self.Bone_AddRotation("rRing3", 'Z', "Bend", -20, 90);
        self.Bone_Define("rCarpal4", "Right Carpal 4", "XYZ", 6.580689907073975, -67.91320037841797, 145.6741943359375, 0.9899755716323853, -0.008366146124899387, -0.17083421349525452, 0.09762921929359436);
        self.Bone_AddRotation("rCarpal4", 'Y', "Side-Side", -3, 4);
        self.Bone_AddRotation("rCarpal4", 'Z', "Bend", -4, 4);
        self.Bone_Define("rPinky1", "Right Pinky 1", "XYZ", 2.791006326675415, -74.25045776367188, 144.81500244140625, -0.15924230217933655, 0.015016209334135056, -0.10176001489162445, 0.07678931206464767);
        self.Bone_AddRotation("rPinky1", 'X', "Twist", -5, 5);
        self.Bone_AddRotation("rPinky1", 'Y', "Side-Side", -18, 12);
        self.Bone_AddRotation("rPinky1", 'Z', "Bend", -50, 90);
        self.Bone_Define("rPinky2", "Right Pinky 2", "XYZ", 1.682206153869629, -77.02149200439453, 144.61439514160156, -0.4254043996334076, -0.03949618339538574, -0.10789809376001358, 0.06895863264799118);
        self.Bone_AddRotation("rPinky2", 'Z', "Bend", -12, 105);
        self.Bone_Define("rPinky3", "Right Pinky 3", "XYZ", 1.7203006744384766, -78.69294738769531, 144.49949645996094, -0.6014683246612549, -0.07169798016548157, -0.10800378769636154, 0.07309164106845856);
        self.Bone_AddRotation("rPinky3", 'Z', "Bend", -20, 90);
        self.Bone_Define("neckLower", "Neck Lower", "YZX", 3.518533706665039, 0, 154.33250427246094, -3.979177951812744, 0.14821626245975494, 0, 0);
        self.Bone_AddRotation("neckLower", 'X', "Bend", -25, 40);
        self.Bone_AddRotation("neckLower", 'Y', "Twist", -22, 22);
        self.Bone_AddRotation("neckLower", 'Z', "Side-Side", -40, 40);
        self.Bone_Define("neckUpper", "Neck Upper", "YZX", 4.998065948486328, 0, 157.61410522460938, -2, 0.14821626245975494, 0, 0);
        self.Bone_AddRotation("neckUpper", 'X', "Bend", -27, 12);
        self.Bone_AddRotation("neckUpper", 'Y', "Twist", -22, 22);
        self.Bone_AddRotation("neckUpper", 'Z', "Side-Side", -10, 10);
        self.Bone_Define("head", "Head", "YZX", 3.3431077003479004, 0, 162.55020141601562, -1.8405749797821045, 0.012166573666036129, 0, 0);
        self.Bone_AddRotation("head", 'X', "Bend", -27, 25);
        self.Bone_AddRotation("head", 'Y', "Twist", -22, 22);
        self.Bone_AddRotation("head", 'Z', "Side-Side", -20, 20);
        self.Bone_Define("upperTeeth", "Upper Teeth", "ZYX", 2.8515305519104004, 0, 162.66580200195312, 5.914668083190918, 0.01901899464428425, 0.00017782051872927696, 0.0001711820368655026);
        self.Bone_Define("lowerJaw", "Lower Jaw", "ZYX", 9.7243070602417, 0, 164.1132049560547, 0.09420406818389893, 0.41101959347724915, 0, 0);
        self.Bone_AddRotation("lowerJaw", 'X', "Up-Down", -10, 25);
        self.Bone_AddRotation("lowerJaw", 'Y', "Side-Side", -12, 12);
        self.Bone_Define("lowerTeeth", "Lower Teeth", "ZYX", 2.756442070007324, 0, 161.57530212402344, 5.668454170227051, 0.2016846388578415, 0, 0);
        self.Bone_Define("tongue01", "Tongue 01", "ZYX", 1.309515357017517, 0, 160.33929443359375, 3.8582799434661865, -0.7174328565597534, 0, 0);
        self.Bone_AddRotation("tongue01", 'X', "Bend", -10, 10);
        self.Bone_AddRotation("tongue01", 'Y', "Side-Side", -5, 5);
        self.Bone_AddRotation("tongue01", 'Z', "Twist", -5, 5);
        self.Bone_Define("tongue02", "Tongue 02", "ZYX", 1.2032907009124756, 0, 161.2001953125, 4.845032215118408, -0.18292619287967682, 0, 0);
        self.Bone_AddRotation("tongue02", 'X', "Bend", -30, 40);
        self.Bone_AddRotation("tongue02", 'Y', "Side-Side", -25, 25);
        self.Bone_AddRotation("tongue02", 'Z', "Twist", -25, 25);
        self.Bone_Define("tongue03", "Tongue 03", "ZYX", 1.1567679643630981, 0, 161.42430114746094, 6.043644905090332, 0.021806316450238228, 0, 0);
        self.Bone_AddRotation("tongue03", 'X', "Bend", -50, 40);
        self.Bone_AddRotation("tongue03", 'Y', "Side-Side", -25, 25);
        self.Bone_AddRotation("tongue03", 'Z', "Twist", -25, 25);
        self.Bone_Define("tongue04", "Tongue 04", "ZYX", 1.0617824792861938, 0, 161.3990020751953, 7.200136184692383, -0.1196223571896553, 0, 0);
        self.Bone_AddRotation("tongue04", 'X', "Bend", -60, 50);
        self.Bone_AddRotation("tongue04", 'Y', "Side-Side", -25, 25);
        self.Bone_AddRotation("tongue04", 'Z', "Twist", -25, 25);
        self.Bone_Define("lowerFaceRig", "Lower Face Rig", "ZYX", 9.7243070602417, 0, 164.1132049560547, 0.09420406818389893, 0.41101959347724915, 0, 0);
        self.Bone_Define("lNasolabialLower", "Left Nasolabial Lower", "ZYX", 0.7114097476005554, 3.0079760551452637, 159.63450622558594, 6.575894832611084, 0, 0, 0);
        self.Bone_AddRotation("lNasolabialLower", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialLower", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialLower", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rNasolabialLower", "Right Nasolabial Lower", "ZYX", 0.7114097476005554, -3.0079760551452637, 159.63450622558594, 6.575894832611084, 0, 0, 0);
        self.Bone_AddRotation("rNasolabialLower", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialLower", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialLower", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lNasolabialMouthCorner", "Left Nasolabial Mouth Corner", "ZYX", 0.4839259088039398, 4.246739864349365, 161.86219787597656, 6.781796932220459, 0, 0, 0);
        self.Bone_AddRotation("lNasolabialMouthCorner", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialMouthCorner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialMouthCorner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rNasolabialMouthCorner", "Right Nasolabial Mouth Corner", "ZYX", 0.4839259088039398, -4.246739864349365, 161.86219787597656, 6.781796932220459, 0, 0, 0);
        self.Bone_AddRotation("rNasolabialMouthCorner", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialMouthCorner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialMouthCorner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lLipCorner", "Left Lip Corner", "ZYX", 1.0622142553329468, 3.2567989826202393, 161.70790100097656, 7.331605911254883, 0, 0, 0);
        self.Bone_AddRotation("lLipCorner", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lLipCorner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lLipCorner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lLipLowerOuter", "Left Lip Lower Outer", "ZYX", 0.4819846749305725, 2.127608060836792, 161.11720275878906, 8.127138137817383, -0.9668838381767273, 0.047565992921590805, 0.024975232779979706);
        self.Bone_AddRotation("lLipLowerOuter", 'X', "X Rotate", -30, 15);
        self.Bone_AddRotation("lLipLowerOuter", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("lLipLowerOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lLipLowerInner", "Left Lip Lower Inner", "ZYX", 0.7394528985023499, 1.0896719694137573, 160.9405975341797, 8.398041725158691, -0.9231085181236267, 0, 0);
        self.Bone_AddRotation("lLipLowerInner", 'X', "X Rotate", -50, 30);
        self.Bone_AddRotation("lLipLowerInner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lLipLowerInner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("LipLowerMiddle", "Lip Lower Middle", "ZYX", 1.0124406814575195, 0, 160.7050018310547, 8.69250202178955, -0.9078126549720764, 0, 0);
        self.Bone_AddRotation("LipLowerMiddle", 'X', "X Rotate", -50, 30);
        self.Bone_AddRotation("LipLowerMiddle", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("LipLowerMiddle", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rLipLowerInner", "Right Lip Lower Inner", "ZYX", 0.7394528985023499, -1.0896719694137573, 160.9405975341797, 8.398041725158691, -0.9231083989143372, 0, 0);
        self.Bone_AddRotation("rLipLowerInner", 'X', "X Rotate", -50, 30);
        self.Bone_AddRotation("rLipLowerInner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rLipLowerInner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rLipLowerOuter", "Right Lip Lower Outer", "ZYX", 0.4819846749305725, -2.127608060836792, 161.11720275878906, 8.127138137817383, -0.9668838381767273, -0.047565992921590805, -0.024975232779979706);
        self.Bone_AddRotation("rLipLowerOuter", 'X', "X Rotate", -30, 15);
        self.Bone_AddRotation("rLipLowerOuter", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("rLipLowerOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rLipCorner", "Right Lip Corner", "ZYX", 1.0622142553329468, -3.2567989826202393, 161.70790100097656, 7.331605911254883, 0, 0, 0);
        self.Bone_AddRotation("rLipCorner", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rLipCorner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rLipCorner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("LipBelow", "Lip Below", "ZYX", 0.7163888812065125, 0, 159.58799743652344, 8.421598434448242, 0, 0, 0);
        self.Bone_AddRotation("LipBelow", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("LipBelow", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("LipBelow", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("Chin", "Chin", "ZYX", 1.3108594417572021, 0, 158.341796875, 7.4461188316345215, 0.43141621351242065, 0, 0);
        self.Bone_AddRotation("Chin", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("Chin", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("Chin", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lCheekLower", "Left Cheek Lower", "ZYX", 0.5351613759994507, 5.490659236907959, 162.09779357910156, 5.1711320877075195, 0, 0, 0);
        self.Bone_AddRotation("lCheekLower", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lCheekLower", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lCheekLower", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rCheekLower", "Right Cheek Lower", "ZYX", 0.5351613759994507, -5.490659236907959, 162.09779357910156, 5.1711320877075195, 0, 0, 0);
        self.Bone_AddRotation("rCheekLower", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rCheekLower", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rCheekLower", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("BelowJaw", "Below Jaw", "ZYX", 0.5091192126274109, 0, 157.10519409179688, 4.735023021697998, 0, 0, 0);
        self.Bone_AddRotation("BelowJaw", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("BelowJaw", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("BelowJaw", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lJawClench", "Left Jaw Clench", "ZYX", 0.6665099263191223, 6.070786952972412, 161.79580688476562, 0.7882266044616699, 0, 0, 0);
        self.Bone_AddRotation("lJawClench", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lJawClench", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lJawClench", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rJawClench", "Right Jaw Clench", "ZYX", 0.6665099263191223, -6.070786952972412, 161.79580688476562, 0.7882266044616699, 0, 0, 0);
        self.Bone_AddRotation("rJawClench", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rJawClench", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rJawClench", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("upperFaceRig", "Upper Face Rig", "YZX", 3.3431077003479004, 0, 162.55020141601562, -1.8405749797821045, 0.01216657180339098, 0, 0);
        self.Bone_Define("rBrowInner", "Right Brow Inner", "ZYX", 0.2500593960285187, -1.9500000476837158, 170.39999389648438, 8.75, 0, 0, 0);
        self.Bone_AddRotation("rBrowInner", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("rBrowInner", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("rBrowInner", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rBrowMid", "Right Brow Middle", "ZYX", 0.2500305473804474, -3.856626033782959, 170.67059326171875, 8.5, 0, 0, 0);
        self.Bone_AddRotation("rBrowMid", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("rBrowMid", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("rBrowMid", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rBrowOuter", "Right Brow Outer", "ZYX", 0.21863199770450592, -5.4691481590271, 170.07139587402344, 7.250022888183594, 0, 0, 0);
        self.Bone_AddRotation("rBrowOuter", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("rBrowOuter", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("rBrowOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lBrowInner", "Left Brow Inner", "ZYX", 0.2500593960285187, 1.9500000476837158, 170.39999389648438, 8.75, 0, 0, 0);
        self.Bone_AddRotation("lBrowInner", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("lBrowInner", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("lBrowInner", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lBrowMid", "Left Brow Middle", "ZYX", 0.2500305473804474, 3.856626033782959, 170.67059326171875, 8.5, 0, 0, 0);
        self.Bone_AddRotation("lBrowMid", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("lBrowMid", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("lBrowMid", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lBrowOuter", "Left Brow Outer", "ZYX", 0.21863199770450592, 5.4691481590271, 170.07139587402344, 7.250022888183594, 0, 0, 0);
        self.Bone_AddRotation("lBrowOuter", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("lBrowOuter", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("lBrowOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("CenterBrow", "Center Brow", "ZYX", 0.2733675539493561, 0, 170.30999755859375, 9.224088668823242, 0, 0, 0);
        self.Bone_AddRotation("CenterBrow", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("CenterBrow", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("CenterBrow", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("MidNoseBridge", "Middle Nose Bridge", "ZYX", 0.2500259280204773, 0, 168.33999633789062, 9, 0, 0, 0);
        self.Bone_AddRotation("MidNoseBridge", 'X', "X Rotate", -15, 15);
        self.Bone_AddRotation("MidNoseBridge", 'Y', "Y Rotate", -15, 15);
        self.Bone_AddRotation("MidNoseBridge", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lEyelidInner", "Left Eyelid Inner", "ZXY", 2.2130794525146484, 3.265177011489868, 168.6168975830078, 6.2291741371154785, -2.2412730515952717e-7, -0.7187198400497437, 3.141592264175415);
        self.Bone_AddRotation("lEyelidInner", 'X', "X Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidInner", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidInner", 'Z', "Z Rotate", -5, 5);
        self.Bone_Define("lEyelidUpperInner", "Left Eyelid Upper Inner", "ZXY", 1.8798425197601318, 3.260103940963745, 168.63499450683594, 6.243627071380615, -0.22684058547019958, -0.024079158902168274, 0.002742966404184699);
        self.Bone_AddRotation("lEyelidUpperInner", 'X', "X Rotate", -5, 50);
        self.Bone_AddRotation("lEyelidUpperInner", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidUpperInner", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lEyelidUpper", "Left Eyelid Upper", "ZXY", 1.8761602640151978, 3.2906389236450195, 168.63499450683594, 6.243627071380615, -0.22888873517513275, 0, 0);
        self.Bone_AddRotation("lEyelidUpper", 'X', "X Rotate", -5, 50);
        self.Bone_AddRotation("lEyelidUpper", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidUpper", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lEyelidUpperOuter", "Left Eyelid Upper Outer", "ZXY", 1.8780590295791626, 3.3197669982910156, 168.63499450683594, 6.243627071380615, -0.22249114513397217, 0.02607845515012741, -0.0029133029747754335);
        self.Bone_AddRotation("lEyelidUpperOuter", 'X', "X Rotate", -5, 50);
        self.Bone_AddRotation("lEyelidUpperOuter", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidUpperOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lEyelidOuter", "Left Eyelid Outer", "ZXY", 1.6575334072113037, 3.3110098838806152, 168.6168975830078, 6.230000019073486, 4.117511309686961e-7, 1.0797796249389648, 3.141592502593994);
        self.Bone_AddRotation("lEyelidOuter", 'X', "X Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidOuter", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidOuter", 'Z', "Z Rotate", -5, 5);
        self.Bone_Define("lEyelidLowerOuter", "Left Eyelid Lower Outer", "ZXY", 1.841894507408142, 3.3187570571899414, 168.6009979248047, 6.242318153381348, 0.36238130927085876, 0.05027817562222481, 3.141592264175415);
        self.Bone_AddRotation("lEyelidLowerOuter", 'X', "X Rotate", -5, 20);
        self.Bone_AddRotation("lEyelidLowerOuter", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidLowerOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lEyelidLower", "Left Eyelid Lower", "ZXY", 1.873638391494751, 3.2906389236450195, 168.6009979248047, 6.242318153381348, 0.35707077383995056, -1.4179791207880044e-7, 3.141592264175415);
        self.Bone_AddRotation("lEyelidLower", 'X', "X Rotate", -5, 20);
        self.Bone_AddRotation("lEyelidLower", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidLower", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lEyelidLowerInner", "Left Eyelid Lower Inner", "ZXY", 1.8727126121520996, 3.2608959674835205, 168.6009979248047, 6.242318153381348, 0.356175035238266, -0.047430265694856644, 3.141592264175415);
        self.Bone_AddRotation("lEyelidLowerInner", 'X', "X Rotate", -5, 20);
        self.Bone_AddRotation("lEyelidLowerInner", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("lEyelidLowerInner", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rEyelidInner", "Right Eyelid Inner", "ZXY", 2.2130794525146484, -3.265177011489868, 168.6168975830078, 6.2291741371154785, -2.0720160875953297e-7, 0.7187198400497437, -3.141592264175415);
        self.Bone_AddRotation("rEyelidInner", 'X', "X Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidInner", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidInner", 'Z', "Z Rotate", -5, 5);
        self.Bone_Define("rEyelidUpperInner", "Right Eyelid Upper Inner", "ZXY", 1.8798425197601318, -3.260103940963745, 168.63499450683594, 6.243627071380615, -0.22684058547019958, 0.024079158902168274, -0.002742966404184699);
        self.Bone_AddRotation("rEyelidUpperInner", 'X', "X Rotate", -5, 50);
        self.Bone_AddRotation("rEyelidUpperInner", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidUpperInner", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rEyelidUpper", "Right Eyelid Upper", "ZXY", 1.8761602640151978, -3.2906389236450195, 168.63499450683594, 6.243627071380615, -0.22888873517513275, 0, 0);
        self.Bone_AddRotation("rEyelidUpper", 'X', "X Rotate", -5, 50);
        self.Bone_AddRotation("rEyelidUpper", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidUpper", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rEyelidUpperOuter", "Right Eyelid Upper Outer", "ZXY", 1.8780590295791626, -3.3197669982910156, 168.63499450683594, 6.243627071380615, -0.22249114513397217, -0.02607845515012741, 0.0029133029747754335);
        self.Bone_AddRotation("rEyelidUpperOuter", 'X', "X Rotate", -5, 50);
        self.Bone_AddRotation("rEyelidUpperOuter", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidUpperOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rEyelidOuter", "Right Eyelid Outer", "ZXY", 1.6575334072113037, -3.3110098838806152, 168.6168975830078, 6.230000019073486, 3.8966820170571737e-7, -1.0797796249389648, -3.141592502593994);
        self.Bone_AddRotation("rEyelidOuter", 'X', "X Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidOuter", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidOuter", 'Z', "Z Rotate", -5, 5);
        self.Bone_Define("rEyelidLowerOuter", "Right Eyelid Lower Outer", "ZXY", 1.841894507408142, -3.3187570571899414, 168.6009979248047, 6.242318153381348, 0.36238130927085876, -0.05027815327048302, -3.141592264175415);
        self.Bone_AddRotation("rEyelidLowerOuter", 'X', "X Rotate", -5, 20);
        self.Bone_AddRotation("rEyelidLowerOuter", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidLowerOuter", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rEyelidLower", "Right Eyelid Lower", "ZXY", 1.873638391494751, -3.2906389236450195, 168.6009979248047, 6.242318153381348, 0.35707077383995056, 1.4080835342156206e-7, -3.141592264175415);
        self.Bone_AddRotation("rEyelidLower", 'X', "X Rotate", -5, 20);
        self.Bone_AddRotation("rEyelidLower", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidLower", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("rEyelidLowerInner", "Right Eyelid Lower Inner", "ZXY", 1.8727126121520996, -3.2608959674835205, 168.6009979248047, 6.242318153381348, 0.356175035238266, 0.047430265694856644, -3.141592264175415);
        self.Bone_AddRotation("rEyelidLowerInner", 'X', "X Rotate", -5, 20);
        self.Bone_AddRotation("rEyelidLowerInner", 'Y', "Y Rotate", -5, 5);
        self.Bone_AddRotation("rEyelidLowerInner", 'Z', "Z Rotate", -15, 15);
        self.Bone_Define("lSquintInner", "Left Squint Inner", "ZYX", 0.22569246590137482, 2.7382431030273438, 167.3126983642578, 7.686977863311768, 0, 0, 0);
        self.Bone_Define("lSquintOuter", "Left Squint Outer", "ZYX", 0.5476487874984741, 5.060328006744385, 167.62469482421875, 6.95796012878418, 0, 0, 0);
        self.Bone_Define("rSquintInner", "Right Squint Inner", "ZYX", 0.22569246590137482, -2.7382431030273438, 167.3126983642578, 7.686977863311768, 0, 0, 0);
        self.Bone_Define("rSquintOuter", "Right Squint Outer", "ZYX", 0.5476487874984741, -5.060328006744385, 167.62469482421875, 6.95796012878418, 0, 0, 0);
        self.Bone_Define("lCheekUpper", "Left Cheek Upper", "ZYX", 0.743016242980957, 5.464041233062744, 165.6674041748047, 6.802028179168701, 0, 0, 0);
        self.Bone_AddRotation("lCheekUpper", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lCheekUpper", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lCheekUpper", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rCheekUpper", "Right Cheek Upper", "ZYX", 0.743016242980957, -5.464041233062744, 165.6674041748047, 6.802028179168701, 0, 0, 0);
        self.Bone_AddRotation("rCheekUpper", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rCheekUpper", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rCheekUpper", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("Nose", "Nose", "ZYX", 1.0486880540847778, 0, 164.87330627441406, 10.353090286254883, 0, 0, 0);
        self.Bone_AddRotation("Nose", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("Nose", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("Nose", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lNostril", "Left Nostril", "ZYX", 0.4518561065196991, 0.6959270238876343, 164.55279541015625, 9.608484268188477, 0, 0, 0);
        self.Bone_AddRotation("lNostril", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lNostril", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lNostril", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rNostril", "Right Nostril", "ZYX", 0.4518561065196991, -0.6959270238876343, 164.55279541015625, 9.608484268188477, 0, 0, 0);
        self.Bone_AddRotation("rNostril", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rNostril", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rNostril", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lLipBelowNose", "Left Lip Below Nose", "ZYX", 1.3991299867630005, 1.2584940195083618, 163.3365936279297, 8.593252182006836, 0, 0, 0);
        self.Bone_AddRotation("lLipBelowNose", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lLipBelowNose", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lLipBelowNose", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rLipBelowNose", "Right Lip Below Nose", "ZYX", 1.3991299867630005, -1.2584940195083618, 163.3365936279297, 8.593252182006836, 0, 0, 0);
        self.Bone_AddRotation("rLipBelowNose", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rLipBelowNose", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rLipBelowNose", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lLipUpperOuter", "Left Lip Upper Outer", "ZYX", 0.38378599286079407, 2.1024229526519775, 162.0561065673828, 8.528472900390625, 1.0215245485305786, 0, 0);
        self.Bone_AddRotation("lLipUpperOuter", 'X', "X Rotate", -15, 30);
        self.Bone_AddRotation("lLipUpperOuter", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lLipUpperOuter", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lLipUpperInner", "Left Lip Upper Inner", "ZYX", 0.5149399638175964, 1.0935879945755005, 162.243896484375, 8.828822135925293, 0.9985247850418091, -0.0032748221419751644, 0.0017859091749414802);
        self.Bone_AddRotation("lLipUpperInner", 'X', "X Rotate", -30, 50);
        self.Bone_AddRotation("lLipUpperInner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lLipUpperInner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("LipUpperMiddle", "Lip Upper Middle", "ZYX", 0.8173092603683472, 0, 162.52659606933594, 9.211620330810547, 1.069139838218689, 0, 0);
        self.Bone_AddRotation("LipUpperMiddle", 'X', "X Rotate", -30, 50);
        self.Bone_AddRotation("LipUpperMiddle", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("LipUpperMiddle", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rLipUpperInner", "Right Lip Upper Inner", "ZYX", 0.5149399638175964, -1.0935879945755005, 162.243896484375, 8.828822135925293, 0.9985247850418091, 0.0032748221419751644, -0.0017859091749414802);
        self.Bone_AddRotation("rLipUpperInner", 'X', "X Rotate", -30, 50);
        self.Bone_AddRotation("rLipUpperInner", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rLipUpperInner", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rLipUpperOuter", "Right Lip Upper Outer", "ZYX", 0.38378599286079407, -2.1024229526519775, 162.0561065673828, 8.528472900390625, 1.0215245485305786, 0, 0);
        self.Bone_AddRotation("rLipUpperOuter", 'X', "X Rotate", -15, 30);
        self.Bone_AddRotation("rLipUpperOuter", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rLipUpperOuter", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lLipNasolabialCrease", "Left Lip Nasolabial Crease", "ZYX", 1.467089056968689, 2.5486390590667725, 162.84190368652344, 8.593252182006836, 0, 0, 0);
        self.Bone_AddRotation("lLipNasolabialCrease", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lLipNasolabialCrease", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lLipNasolabialCrease", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rLipNasolabialCrease", "Right Lip Nasolabial Crease", "ZYX", 1.467089056968689, -2.5486390590667725, 162.84190368652344, 8.593252182006836, 0, 0, 0);
        self.Bone_AddRotation("rLipNasolabialCrease", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rLipNasolabialCrease", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rLipNasolabialCrease", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lNasolabialUpper", "Left Nasolabial Upper", "ZYX", 0.45008420944213867, 1.6858550310134888, 166.34840393066406, 8.593252182006836, 0, 0, 0);
        self.Bone_AddRotation("lNasolabialUpper", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialUpper", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialUpper", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rNasolabialUpper", "Right Nasolabial Upper", "ZYX", 0.45008420944213867, -1.6858550310134888, 166.34840393066406, 8.593252182006836, 0, 0, 0);
        self.Bone_AddRotation("rNasolabialUpper", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialUpper", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialUpper", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lNasolabialMiddle", "Left Nasolabial Middle", "ZYX", 0.4944377839565277, 2.9282119274139404, 164.4824981689453, 8.229619979858398, 0, 0, 0);
        self.Bone_AddRotation("lNasolabialMiddle", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialMiddle", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("lNasolabialMiddle", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("rNasolabialMiddle", "Right Nasolabial Middle", "ZYX", 0.4944377839565277, -2.9282119274139404, 164.4824981689453, 8.229619979858398, 0, 0, 0);
        self.Bone_AddRotation("rNasolabialMiddle", 'X', "X Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialMiddle", 'Y', "Y Rotate", -30, 30);
        self.Bone_AddRotation("rNasolabialMiddle", 'Z', "Z Rotate", -30, 30);
        self.Bone_Define("lEye", "Left Eye", "ZXY", 1.7230758666992188, 3.290832042694092, 168.6186981201172, 6.201231002807617, 0, 0, 3.141592264175415);
        self.Bone_AddRotation("lEye", 'X', "Up-Down", -30, 30);
        self.Bone_AddRotation("lEye", 'Y', "Side-Side", -30, 40);
        self.Bone_AddRotation("lEye", 'Z', "Twist", -180, 180);
        self.Bone_Define("rEye", "Right Eye", "ZXY", 1.7230758666992188, -3.290832042694092, 168.6186981201172, 6.201231002807617, 0, 0, -3.141592264175415);
        self.Bone_AddRotation("rEye", 'X', "Up-Down", -30, 30);
        self.Bone_AddRotation("rEye", 'Y', "Side-Side", -40, 30);
        self.Bone_AddRotation("rEye", 'Z', "Twist", -180, 180);
        self.Bone_Define("lEar", "Left Ear", "XYZ", 3.376326322555542, 6.891260147094727, 166.63389587402344, -1.2818559408187866, -0.04024370759725571, 1.0422862768173218, -0.07008188962936401);
        self.Bone_AddRotation("lEar", 'X', "Twist", -10, 30);
        self.Bone_AddRotation("lEar", 'Y', "Front-Back", -30, 10);
        self.Bone_AddRotation("lEar", 'Z', "Up-Down", -10, 10);
        self.Bone_Define("rEar", "Right Ear", "XYZ", 3.376326322555542, -6.891260147094727, 166.63389587402344, -1.2818559408187866, -0.04024370759725571, -1.0422862768173218, 0.07008188962936401);
        self.Bone_AddRotation("rEar", 'X', "Twist", -10, 30);
        self.Bone_AddRotation("rEar", 'Y', "Front-Back", -10, 30);
        self.Bone_AddRotation("rEar", 'Z', "Up-Down", -10, 10);
        self.Bone_Define("lPectoral", "Left Pectoral", "ZYX", 29.980724334716797, 3.131735324859619, 131.76783752441406, -7.353381156921387, -0.1652095466852188, 0.36367303133010864, 0.059114307165145874);
        self.Bone_AddRotation("lPectoral", 'X', "Up-Down", -10, 10);
        self.Bone_AddRotation("lPectoral", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("lPectoral", 'Z', "Twist", -15, 15);
        self.Bone_Define("rPectoral", "Right Pectoral", "ZYX", 29.98134994506836, -3.1275274753570557, 131.7674102783203, -7.351889133453369, -0.16520951688289642, -0.36367303133010864, -0.05911429971456528);
        self.Bone_AddRotation("rPectoral", 'X', "Up-Down", -10, 10);
        self.Bone_AddRotation("rPectoral", 'Y', "Side-Side", -10, 10);
        self.Bone_AddRotation("rPectoral", 'Z', "Twist", -15, 15);
        #===== END BONE DUMP =====


        
        #=== Finalize bone rig visualizer by properly re-parenting as per bone hierarchy ===        We must(?) do this once all the nodes are done moving for parenting to work correctly? (Complicated Blender parenting rules with non-obvious child origins!)
        if C_CreateBoneRigVisualizer:
            bpy.ops.object.mode_set(mode='OBJECT')
            for sNameBone in self.mapBones:
                oBone = self.mapBones[sNameBone]
    
                #--- Parent the master empties by parent-child relationship ---            
                if oBone.sNameBoneParent is not None:
                    SelectObject(oBone.oRigVis_Bone.name)
                    oBoneParent = self.mapBones[oBone.sNameBoneParent]
                    oBoneParent.oRigVis_Bone.select = True
                    bpy.context.scene.objects.active = oBoneParent.oRigVis_Bone
                    bpy.ops.object.parent_set(keep_transform=True)  ###INFO: keep_transform=True is critical to prevent reparenting from destroying the previously set transform of object!!


    def Bone_Define(self, sNameBone, sLabelBone, sRotOrderDAZ, nLenBone, OX, OY, OZ, eulX, eulY, eulZ):
        #=== Define the constants we need to convert from DAZ coordinate systems to Blender's === 
        C_DazToBlenderResize = 100                          # Everything is 100 times bigger in DAZ
        PI2 = pi/2                                          # Commonly-used 90 degree rotation        
        eulRotateDazCoordinatesToBlender = Euler((PI2,0,0)) ###NOTE: Note the IMPORTANT top-level 90 degree rotation to Blender's geometry (up is +Z, forward is -Y, left is -X)   Define top-level transform that converts coordinate and angle from Daz to Blende

        #=== Obtain reference to the bone we need to fix ===
        oBone = self.mapBones[sNameBone]
        oBoneO = self.oArmBones[sNameBone]              # Reference to edit bone.  MUST be in edit mode of the armature for this call to work!
        oBoneO.use_connect = False
 
        #=== Coalesce the raw input vector and rotation into their corresponding vectors / orientations ===
        vecBoneOriginDAZ = Vector((OX/C_DazToBlenderResize, OY/C_DazToBlenderResize, OZ/C_DazToBlenderResize))
        eulRotationInputFromDaz = Euler((eulX, eulY, eulZ), sRotOrderDAZ)       ###NOTE: Note the IMPORTANT sRotOrder right from DAZ.  DAZ will switch to five of the 6 permutations of Euler rotation orders for its bones!!    ###NOTE: DAZ Quaternions are USELESS right now... because they are parent/child transformations?  Anyways can make things work if we get its eulers AND the axis order!!   ###INFO: Note that quaternion ctor takes W,X,Y,Z, not X,Y,Z,W!!!
        nLenBone = nLenBone / C_DazToBlenderResize
        
        #=== Right off the top we convert DAZ's coordinate system to Blender to *COMPLETELY* shield Blender code from DAZ's Y-up coordinates.  Fortunately both DAZ and Blender are 'right hand coordinate systems' but DAZ is +Y Up while Blender is +Z Up.  (Unity is +Y Up like DAZ but Left-handed = TOTAL HORSEHIT!!) ===
        vecBoneOriginDAZ.rotate(eulRotateDazCoordinatesToBlender)                
        eulRotationInputFromDaz.rotate(eulRotateDazCoordinatesToBlender)                

        #=== Create the starting DAZ matrix containing bone location and orientation to define our 'unoriented' bone ===
        matTranslationDAZ = Matrix.Translation(vecBoneOriginDAZ)
        matOrientationDAZ = eulRotationInputFromDaz.to_matrix().to_4x4()
        matBoneUnoriented = matTranslationDAZ * matOrientationDAZ               ### LEARN: Note the order matters with matrices!  See https://docs.blender.org/api/2.49/Mathutils-module.html 
         
        #=== Create a rotation that defines the meaning of 'forward' and 'up' for this bone as requested by our 'oBone.sOrientation'   Critical to properly orient its rotation as they are not fully global nor fully local (They are almost global but don't have where they should be oriented) ===
        ###NOTE: For mostly vertical   bones the bone flows from parent to child with +Y and we align +X with global +X (toward left hand) (Z goes either forward or backward) (See https://blender.stackexchange.com/questions/15609/in-which-direction-should-bone-axes-be-oriented)
        ###NOTE: For mostly horizontal bones the bone flows from parent to child with +Y and we align +Z with global +Z (Up)               (X goes either forward or backward, left or right)
        ###===== DAZ BONE OBSERVATIONS =====
        #- Front-facing: X=Up/Down      Y=Left/Right        Z=roll 
        #- Side-facing:  X=roll,        Y=Left/Right        Z=Up/Down
        #- Up-facing:    X=Up/Down      Y=Roll,             Z=Left/Right
        if   oBone.sOrientation == 'L':   eulRotateToBoneForward = Euler((-PI2,-PI2,0))
        elif oBone.sOrientation == 'R':   eulRotateToBoneForward = Euler((-PI2, PI2,0))
        elif oBone.sOrientation == 'F':   eulRotateToBoneForward = Euler((-PI2,pi,0))
        elif oBone.sOrientation == 'B':   eulRotateToBoneForward = Euler((-PI2, 0,0))        
        elif oBone.sOrientation == 'U':   eulRotateToBoneForward = Euler(( 0,0,0))        ###TODO20: REDO THESE COMMENTS! ->  +Y pointing toward body up,      +Z is body forward,  +X pointing toward left hand
        elif oBone.sOrientation == 'D':   eulRotateToBoneForward = Euler((pi,0,0))
        matRotateToBoneForward = eulRotateToBoneForward.to_matrix().to_4x4()

        #=== Create the oriented bone matrix.  It cannot yet be used for the bone as we have to direct it one of six ways (Up, Down, Left, Right, Forward, Backward).  We do this next line === 
        matBone = matBoneUnoriented * matRotateToBoneForward 

        #=== Specify where we want X oriented toward based on bone orientation === Note that +Y *always* flows from the bone parent to the child (Blender requirement that Unity is fine with))  This is to enable Unity's bone to leverage the enhanced flexibility of the X axis with PhysX's D6 configurable joint  (X has different min/max where Y and Z have same min/max)
        if sNameBone.find("ForearmBend") != -1:                         # Exception on elbow:  Set X axis toward body-up so we can use different min/max for X joint to simulate elbow properly!
            vecDesiredX = Vector((0,0,1))                               
#        elif sNameBone.find("ThighTwist") != -1:                        # Exception on ThighTwist:  Set X axis toward body-up so we can use different min/max for X joint to simulate twist properly!
#            vecDesiredX = Vector((0,0,1))                               
        elif sNameBone.find("Thumb") != -1:                             # Exception on all thumb bones:  Keep X assigned to the primary joint bend
            vecDesiredX = Vector((0,0,1))
        elif oBone.sOrientation == 'L' or oBone.sOrientation == 'R':
            vecDesiredX = Vector((0,1,0))
        elif oBone.sOrientation == 'U' or oBone.sOrientation == 'D':
            vecDesiredX = Vector((1,0,0))
        elif oBone.sOrientation == 'F' or oBone.sOrientation == 'B':
            vecDesiredX = Vector((1,0,0))
            

        #=== Iterate through the four possible quadrant orientations about bone axis (Y) to find the bone axis orientation that yields the X axis closest toward where we want it ===        
        nAngleToDesiredX_Lowest = sys.float_info.max
        matBoneRotatedAboutAxisThisQuadrant_Lowest = None
        for nQuadrant in range(4):
            matRotateAboutBoneAxisThisQuadrant = Euler((0,nQuadrant*PI2,0)).to_matrix().to_4x4()
            matBoneRotatedAboutAxisThisQuadrant = matBone * matRotateAboutBoneAxisThisQuadrant
            # self.DEBUG_MoveAndRotateDebugGizmo(1+nQuadrant, "Rot", matBoneRotatedAboutAxisThisQuadrant)
            #--- Calculate where the X-vector ends up at from a quarter-by-quarter rotation around this bone's Y axis
            vecRotatedX = Vector((1,0,0))
            vecRotatedX.rotate(matBoneRotatedAboutAxisThisQuadrant.to_quaternion())
            nAngleToDesiredX = vecDesiredX.angle(vecRotatedX) 
            #--- Remember which of the four rotation yields the smallest angle between the bone's local X axis and where the user wants this X axis facing globally ---
            if nAngleToDesiredX_Lowest > nAngleToDesiredX:
                nAngleToDesiredX_Lowest = nAngleToDesiredX
                matBoneRotatedAboutAxisThisQuadrant_Lowest = matBoneRotatedAboutAxisThisQuadrant
            #    print("-- Angle diff to quadrant {} is {:5.1f} on bone '{}'".format(nQuadrant, degrees(nAngleToDesiredX), oBoneO.name))


        #=== Assign the just-defined matrix to the bone.  This will property set the 'roll' as per our defined rotation without Blender's useless roll 'processing' ===
        oBoneO.matrix = matBoneRotatedAboutAxisThisQuadrant_Lowest.copy()
        oBoneO.length = nLenBone                     # We could probably scale the matrix but this is easier

        #=== Visualize the bone in our external visualizer.  (It alone can show proper bone 'roll') ===
        if C_CreateBoneRigVisualizer:
            oBone.oRigVis_Bone.matrix_world = oBoneO.matrix.copy()
            oBone.oRigVis_Arrow.scale = Vector((nLenBone, nLenBone, nLenBone))          # Set the length of our visulizer arrow
            oBone.oRigVis_AxesDAZ.matrix_world = matBoneUnoriented                      # Manually re-orient the DAZ axes to the DAZ-provided orientation
 
        #=== Compute the DAZ-to-Blender rotation.  This is needed to traverse bone rotations DAZ provides in its domain to the Blender bone domain (where bone axes are re-oriented)
        quatDaz     = matBoneUnoriented.to_quaternion()
        quatBlender = oBoneO.matrix.to_quaternion()
        oBone.matBoneEdit       = oBoneO.matrix.copy()          # Store copy of edit-time bone matrix so we can convert Blender pose to fully-qualified Blender rotation so we can go to DAZ rotation domain and back to Blender
        oBone.matBlenderToDaz   = quatDaz.rotation_difference(quatBlender).to_matrix().to_4x4()         # Remember DAZ-to-Blender and Blender-to-DAZ matrices that can traverse one domain to another
        oBone.matDazToBlender   = quatBlender.rotation_difference(quatDaz).to_matrix().to_4x4()         ###INFO: Note that A.rotation_difference(B) returns a quaternion that can rotate from B to A (not A to B!!) 
 
        #=== Determine the Blender axis & sign from original DAZ axis (as rotated by our oBone re-orientation) ===        (e.g. A DAZ rotation order like "XZY" could become like "YXZ" (dependent on end rotation applied))
        sRotOrderBlender = ""
        for chAxisDAZ in sRotOrderDAZ:
            sAxisBlender, chSign = self.Util_DetermineRotatedAxisFromDazAxis(oBone, chAxisDAZ)
            sRotOrderBlender += sAxisBlender
        oBone.sRotOrder = sRotOrderBlender
        oBoneO["RotOrder"] = oBone.sRotOrder 
 
        print("-Bone '{}'   OR='{}'   ROT='{}'->'{}'  LEN={:5.3f}".format(sNameBone, oBone.sOrientation, sRotOrderDAZ, sRotOrderBlender, nLenBone))    


    def Util_DetermineRotatedAxisFromDazAxis(self, oBone, chAxisDAZ):
        #=== Stuff a vector with '1' at the requested axis to where it ends up in Blender / Unity domain ('X+', 'X-', 'Y+', 'Y-', 'Z+', 'Z-')
        if   chAxisDAZ == 'X':
            vecUnrotated = Vector((1.1,0,0))            # Make unrotated vectors a bit over 1.0 so after rotation to Blender's domain the axis we're trying to find is at least one (to overcome numerical precision problems) 
        elif chAxisDAZ == 'Y': 
            vecUnrotated = Vector((0,1.1,0)) 
        elif chAxisDAZ == 'Z': 
            vecUnrotated = Vector((0,0,1.1))
    
        #=== Rotate the vector as per previously-calculated 'DAZ-to-Blender' matrix and detect where this axis falls in the Blender / Unity domain ===
        vecRotated = vecUnrotated.copy()
        vecRotated.rotate(oBone.matDazToBlender)
        chAxisBlender = "############# ERROR ##############"
        chSign = '+'
        if   abs(vecRotated.x) > 1:                         ###IMPROVE20: Convert names of sRotationDescription that have names like "<Axis> Rotate" to account for axis change
            chAxisBlender = 'X'
            if vecRotated.x < 0:
                chSign = '-'
        elif abs(vecRotated.y) > 1:
            chAxisBlender = 'Y'
            if vecRotated.y < 0:
                chSign = '-'
        elif abs(vecRotated.z) > 1:
            chAxisBlender = 'Z'
            if vecRotated.z < 0:
                chSign = '-'
        return chAxisBlender, chSign
        

    
    def Bone_AddRotation(self, sNameBone, chAxisDAZ, sRotationDescription, nMin, nMax):
        oBone = self.mapBones[sNameBone]
        oBoneO = self.oArmBones[sNameBone]

        #=== Determine the Blender axis & sign from original DAZ axis (as rotated by our oBone re-orientation) ===
        chAxisBlender, chSign = self.Util_DetermineRotatedAxisFromDazAxis(oBone, chAxisDAZ)

        #=== Create a serialization string that will be appended to the possible rotations in this Blender bone object.  This will be sent to Unity when it requests a design-time bone update ===
        sSerializedRotationForUnity = "'{}{}', '{}', '{}', '{}', '{}'".format(chAxisBlender, chSign, chAxisDAZ, sRotationDescription, nMin, nMax)                     ###WEAK20?: Kind of shitty we have to string-pack everything to use existing serialization mechanism but oh well...

        #=== Store everything that Unity needs from this rotation in an additional array element with all fields concatenated in a comma-separated string.         
        if "Rotations" not in oBoneO:
            oBoneO["Rotations"] = [sSerializedRotationForUnity]
        else:
            aRotations = oBoneO["Rotations"]
            aRotations.append(sSerializedRotationForUnity)
            oBoneO["Rotations"] = aRotations 

        print("-- Rot: {}+ -> {}{} on '{}.{}' = {}".format(chAxisDAZ, chAxisBlender, chSign, sNameBone, chAxisDAZ, sSerializedRotationForUnity))



    ########################################################################    UTILITY
    def BoneFix_SetOrientationFlag(self, sOrientation, oBoneO):
        oBone = self.mapBones[oBoneO.name]
        oBone.sOrientation = sOrientation
        #print("- Orient '{}' on bone '{}'".format(sOrientation, oBoneO.name))
        
    def BoneFix_SetOrientationFlag_RECURSIVE(self, sOrientation, oBoneParent):          ###IMPROVE20: Give CBone ability to traverse parent-child bone struture so we don't have to rely on Blender's armature??
        self.BoneFix_SetOrientationFlag(sOrientation, oBoneParent)
        for oBoneO in oBoneParent.children:
            self.BoneFix_SetOrientationFlag_RECURSIVE(sOrientation, oBoneO)

    def DEBUG_MoveAndRotateDebugGizmo(self, nDebugGizmo, sNameGizmo, mat):          # Debug / development function to move a previously-created bone visualizer mesh.  Used to debug angles during development
        oGizmoAngleDebug = bpy.data.objects["AngleDebug" + str(nDebugGizmo)]
        oGizmoAngleDebug.matrix_world = mat
        oGizmoAngleDebug.name = oGizmoAngleDebug.data.name = str(nDebugGizmo) + "-" + sNameGizmo
        oGizmoAngleDebug.show_x_ray = True
        oGizmoAngleDebug.layers[5] = True






    ########################################################################    DEBUG POSING TESTS

    def DEBUG_ShowDazPose(self):
        oRootNodeO = SelectObject(self.oMesh.parent.name) 
        bpy.ops.object.mode_set(mode='POSE')
        
        self.Pose_SetBoneRotation("lThighBend", 'X', "Bend", -115);
        self.Pose_SetBoneRotation("lThighBend", 'Z', "Side-Side", 45);
        self.Pose_SetBoneRotation("lThighTwist", 'Y', "Twist", 57.857147216796875);
        self.Pose_SetBoneRotation("lShin", 'X', "Bend", 155);
        self.Pose_SetBoneRotation("lFoot", 'X', "Bend", 40);
        self.Pose_SetBoneRotation("lHeel", 'X', "Bend", -16);
        self.Pose_SetBoneRotation("rThighBend", 'X', "Bend", -80);
        self.Pose_SetBoneRotation("rThighBend", 'Z', "Side-Side", 15.5);
        self.Pose_SetBoneRotation("rShin", 'X', "Bend", 155);
        self.Pose_SetBoneRotation("rFoot", 'X', "Bend", 40);
        self.Pose_SetBoneRotation("rHeel", 'X', "Bend", -16);
        self.Pose_SetBoneRotation("lCollar", 'X', "Twist", -2.2857141494750977);
        self.Pose_SetBoneRotation("lCollar", 'Y', "Front-Back", -17.19999885559082);
        self.Pose_SetBoneRotation("lCollar", 'Z', "Bend", 39.5);
        self.Pose_SetBoneRotation("lShldrBend", 'Y', "Front-Back", -28.25714111328125);
        self.Pose_SetBoneRotation("lShldrBend", 'Z', "Bend", -76.5);
        self.Pose_SetBoneRotation("lShldrTwist", 'X', "Twist", -31.999998092651367);
        self.Pose_SetBoneRotation("lCarpal1", 'Y', "Side-Side", 2.22666597366333);
        self.Pose_SetBoneRotation("lIndex1", 'X', "Twist", 2.6666669845581055);
        self.Pose_SetBoneRotation("lIndex1", 'Y', "Side-Side", 1);
        self.Pose_SetBoneRotation("lIndex1", 'Z', "Bend", -75.0666732788086);
        self.Pose_SetBoneRotation("lIndex2", 'Z', "Bend", -100);
        self.Pose_SetBoneRotation("lIndex3", 'Z', "Bend", -90);
        self.Pose_SetBoneRotation("lCarpal2", 'Y', "Side-Side", 0.4266667068004608);
        self.Pose_SetBoneRotation("lMid1", 'X', "Twist", -3);
        self.Pose_SetBoneRotation("lMid1", 'Z', "Bend", -77.5999984741211);
        self.Pose_SetBoneRotation("lMid2", 'Z', "Bend", -100);
        self.Pose_SetBoneRotation("lMid3", 'Z', "Bend", -90);
        self.Pose_SetBoneRotation("lCarpal3", 'Y', "Side-Side", -1.440000057220459);
        self.Pose_SetBoneRotation("lRing1", 'X', "Twist", -4.6666669845581055);
        self.Pose_SetBoneRotation("lRing1", 'Z', "Bend", -74.13333129882812);
        self.Pose_SetBoneRotation("lRing2", 'Z', "Bend", -100);
        self.Pose_SetBoneRotation("lRing3", 'Z', "Bend", -90);
        self.Pose_SetBoneRotation("lCarpal4", 'Y', "Side-Side", -3.206666946411133);
        self.Pose_SetBoneRotation("lPinky1", 'X', "Twist", -4.533332824707031);
        self.Pose_SetBoneRotation("lPinky1", 'Y', "Side-Side", -7.400000095367432);
        self.Pose_SetBoneRotation("lPinky1", 'Z', "Bend", -72.26666259765625);
        self.Pose_SetBoneRotation("lPinky2", 'Z', "Bend", -100);
        self.Pose_SetBoneRotation("lPinky3", 'Z', "Bend", -90);
        self.Pose_SetBoneRotation("rCollar", 'X', "Twist", -2.2857141494750977);
        self.Pose_SetBoneRotation("rCollar", 'Y', "Front-Back", 26);
        self.Pose_SetBoneRotation("rCollar", 'Z', "Bend", -50);
        self.Pose_SetBoneRotation("rShldrBend", 'Y', "Front-Back", -40);
        self.Pose_SetBoneRotation("rShldrBend", 'Z', "Bend", 5.214288234710693);
        self.Pose_SetBoneRotation("rShldrTwist", 'X', "Twist", -31.999998092651367);
        self.Pose_SetBoneRotation("rForearmBend", 'Y', "Bend", 135);
        self.Pose_SetBoneRotation("rThumb1", 'X', "Twist", -15);
        self.Pose_SetBoneRotation("rThumb1", 'Y', "Bend", 26);
        self.Pose_SetBoneRotation("rThumb1", 'Z', "Up-Down", -7);
        self.Pose_SetBoneRotation("rThumb2", 'Y', "Bend", 15);
        self.Pose_SetBoneRotation("rThumb3", 'Y', "Bend", 20);
        self.Pose_SetBoneRotation("rCarpal1", 'Y', "Side-Side", 2.450000047683716);
        self.Pose_SetBoneRotation("rIndex1", 'X', "Twist", -2.2950820922851562);
        self.Pose_SetBoneRotation("rIndex1", 'Y', "Side-Side", 9);
        self.Pose_SetBoneRotation("rIndex1", 'Z', "Bend", 40.737709045410156);
        self.Pose_SetBoneRotation("rIndex2", 'Z', "Bend", 46.512290954589844);
        self.Pose_SetBoneRotation("rIndex3", 'Z', "Bend", 40.06338119506836);
        self.Pose_SetBoneRotation("rCarpal2", 'Y', "Side-Side", 0.25);
        self.Pose_SetBoneRotation("rMid1", 'X', "Twist", 2.7092509269714355);
        self.Pose_SetBoneRotation("rMid1", 'Y', "Side-Side", -0.27049195766448975);
        self.Pose_SetBoneRotation("rMid1", 'Z', "Bend", -50);
        self.Pose_SetBoneRotation("rMid2", 'Z', "Bend", -12);
        self.Pose_SetBoneRotation("rMid3", 'Z', "Bend", -20);
        self.Pose_SetBoneRotation("rCarpal3", 'Y', "Side-Side", -1.649999976158142);
        self.Pose_SetBoneRotation("rRing1", 'X', "Twist", 5);
        self.Pose_SetBoneRotation("rRing1", 'Y', "Side-Side", -10.024589538574219);
        self.Pose_SetBoneRotation("rRing1", 'Z', "Bend", -48.114749908447266);
        self.Pose_SetBoneRotation("rRing2", 'Z', "Bend", -12);
        self.Pose_SetBoneRotation("rRing3", 'Z', "Bend", -20);
        self.Pose_SetBoneRotation("rCarpal4", 'Y', "Side-Side", -3);
        self.Pose_SetBoneRotation("rPinky1", 'X', "Twist", 2.008197069168091);
        self.Pose_SetBoneRotation("rPinky1", 'Y', "Side-Side", -18);
        self.Pose_SetBoneRotation("rPinky1", 'Z', "Bend", -32.04917907714844);
        self.Pose_SetBoneRotation("rPinky2", 'Z', "Bend", -12);
        self.Pose_SetBoneRotation("rPinky3", 'Z', "Bend", -20);
        self.Pose_SetBoneRotation("tongue02", 'Y', "Side-Side", -10);
        self.Pose_SetBoneRotation("tongue03", 'Y', "Side-Side", -10);
        self.Pose_SetBoneRotation("tongue04", 'Y', "Side-Side", -10);
        self.Pose_SetBoneRotation("lLipLowerOuter", 'X', "X Rotate", 1.5525480508804321);
        self.Pose_SetBoneRotation("lLipLowerInner", 'X', "X Rotate", -10.394904136657715);
        self.Pose_SetBoneRotation("LipLowerMiddle", 'X', "X Rotate", -10.394904136657715);
        self.Pose_SetBoneRotation("rLipLowerInner", 'X', "X Rotate", -10.394904136657715);
        self.Pose_SetBoneRotation("rLipLowerOuter", 'X', "X Rotate", 1.5525480508804321);
        self.Pose_SetBoneRotation("LipBelow", 'X', "X Rotate", -3);
        self.Pose_SetBoneRotation("Chin", 'X', "X Rotate", -1.5);
        self.Pose_SetBoneRotation("lEyelidUpperInner", 'X', "X Rotate", 29);
        self.Pose_SetBoneRotation("lEyelidUpper", 'X', "X Rotate", 29);
        self.Pose_SetBoneRotation("lEyelidUpperOuter", 'X', "X Rotate", 29);
        self.Pose_SetBoneRotation("lEyelidLowerOuter", 'X', "X Rotate", 6);
        self.Pose_SetBoneRotation("lEyelidLower", 'X', "X Rotate", 6);
        self.Pose_SetBoneRotation("lEyelidLowerInner", 'X', "X Rotate", 6);
        self.Pose_SetBoneRotation("rEyelidUpperInner", 'X', "X Rotate", 29);
        self.Pose_SetBoneRotation("rEyelidUpper", 'X', "X Rotate", 29);
        self.Pose_SetBoneRotation("rEyelidUpperOuter", 'X', "X Rotate", 29);
        self.Pose_SetBoneRotation("rEyelidLowerOuter", 'X', "X Rotate", 6);
        self.Pose_SetBoneRotation("rEyelidLower", 'X', "X Rotate", 6);
        self.Pose_SetBoneRotation("rEyelidLowerInner", 'X', "X Rotate", 6);
        self.Pose_SetBoneRotation("lNostril", 'X', "X Rotate", -0.9969227910041809);
        self.Pose_SetBoneRotation("lNostril", 'Z', "Z Rotate", -5.20615291595459);
        self.Pose_SetBoneRotation("rNostril", 'X', "X Rotate", -0.9969227910041809);
        self.Pose_SetBoneRotation("rNostril", 'Z', "Z Rotate", 5.20615291595459);
        self.Pose_SetBoneRotation("lLipUpperOuter", 'X', "X Rotate", -15);
        self.Pose_SetBoneRotation("lLipUpperInner", 'X', "X Rotate", -30);
        self.Pose_SetBoneRotation("LipUpperMiddle", 'X', "X Rotate", -30);
        self.Pose_SetBoneRotation("rLipUpperInner", 'X', "X Rotate", -30);
        self.Pose_SetBoneRotation("rLipUpperOuter", 'X', "X Rotate", -15);
        self.Pose_SetBoneRotation("lPectoral", 'X', "Up-Down", -1.1377673149108887);
        self.Pose_SetBoneRotation("lPectoral", 'Y', "Side-Side", -4.372766971588135);
        self.Pose_SetBoneRotation("rPectoral", 'X', "Up-Down", -2.7127673625946045);
        self.Pose_SetBoneRotation("rPectoral", 'Y', "Side-Side", 7.012767314910889);        
        
        for sNameBone in self.mapBones:
            self.Pose_FinalizeBoneRotation(sNameBone)


    def Pose_SetBoneRotation(self, sNameBone, chAxisDAZ, sLabel, nValue):
        oBone = self.mapBones[sNameBone]
        chAxisBlender, chSign = self.Util_DetermineRotatedAxisFromDazAxis(oBone, chAxisDAZ)
        if chSign == '-':
            nValue = -nValue
        if   chAxisBlender == 'X':      oBone.vecRotationBuild.x = radians(nValue)
        elif chAxisBlender == 'Y':      oBone.vecRotationBuild.y = radians(nValue)
        elif chAxisBlender == 'Z':      oBone.vecRotationBuild.z = radians(nValue)

     
    def Pose_FinalizeBoneRotation(self, sNameBone):
        ###INFO: quat1.rotate(quat2) interprets quat2 as GLOBAL (not local to quat1.  For a local rotation of quat1 use matrices as illustrated below: 
        #D.objects["S.001"].rotation_quaternion = D.objects["S.000"].rotation_quaternion.rotation_difference(D.objects["S.002"].rotation_quaternion)     # S.001 stores difference quaternion.
        #D.objects["D.002"].matrix_world = D.objects["D.002"].matrix_world * D.objects["S.001"].rotation_quaternion.to_matrix().to_4x4()                 # D.002 gets LOCALLY rotated by difference quaternion 
        oBone = self.mapBones[sNameBone]
        if oBone.sRotOrder is not None and oBone.vecRotationBuild.length > 0:             ###NOTE: Some generated bones not initialized? Fix?
            oRigVisBone = oBone.oRigVis_Bone
            oRigVisBone.rotation_mode = "QUATERNION"

            #=== Convert the requested full rotation to a matrix ===
            eulNewRotation  = Euler(oBone.vecRotationBuild, oBone.sRotOrder)
            quatNewRotation = eulNewRotation.to_quaternion()          
            matNewRotation  = quatNewRotation.to_matrix().to_4x4()

            #=== Set the Blender bones ===
            oBonePoseO = self.oMesh.parent.pose.bones[sNameBone]
            oBonePoseO.rotation_quaternion = quatNewRotation 

            #=== Set the bone visualizer rig: Convert old rotation from Blender to Daz domain, append new rotation, convert back to Blender domain and apply to bone ===            
            quatRotationOld = oRigVisBone.rotation_quaternion                       # Obtain the existing bone rotation quaternion...                ###IMPROVE: Can do local rotations by quaternion multiplications instead of matrix multiplication??
            matRotationOld = quatRotationOld.to_matrix().to_4x4()                   
            matRotationNew = matRotationOld * matNewRotation                     
            oRigVisBone.rotation_quaternion = matRotationNew.to_quaternion()

            print("- PoseB '{}'  O={}   R={}".format(sNameBone, oBone.sRotOrder, eulNewRotation))

            oBone.vecRotationBuild = Vector()           # Rest build vector for next time



class CBone():                      # CBone: Information-storage object used to store everything related to an individual bone as needed during body importer phase
    def __init__(self, sNameBone):
        self.sNameBone = sNameBone
        self.sNameBoneParent = None                     # Name of bone parent.  Used for bone rig visualizer re-parenting
        self.sRotOrder = None                           # DAZ-provided Euler 'rotation order'.  Hugely important to interpret its Eulers (and pose as intended).  A string that looks like "XYZ", "ZXY", "YXZ", etc
        self.matBoneEdit = None                         # Backup of the matrix we stuff for this 'edit bone'.  Used so we can traverse back to Daz-domain and back for pose update
        self.matDazToBlender = None                     # Stores the conversion matrix that can traverse bones from DAZ-domain to Blender-domain (e.g. to traverse the complex bone re-orientation we do during import)  (e.g. This quaternion can rotate oRigVis_AxesDAZ to oRigVis_Axes)
        self.matBlenderToDaz = None                     # Reverse of matDazToBlender
        self.vecRotationBuild = Vector()                # Temporary storage for the X, Y, Z rotations before a fully-qualified Euler can be constructed once all X,Y,Z rotations on a bone are known (needed to account for the various 'sRotOrder' that can exist on a given bone)        
        
        #--- Members related to our (optional) bone rig visualizer. Was instrumental during development ---
        self.oRigVis_Bone           = None              # Bone 'empty'.  Is parent of the other three visualizer nodes and is the one to rotate to simulate bone rig 
        self.oRigVis_Arrow          = None              # Draws a properly-sized arrow and oriented arrow of this oriented bone
        self.oRigVis_Axes           = None              # Draws the Blender-domain 'axes' showing this bone's orientation
        self.oRigVis_AxesDAZ        = None              # Draws the DAZ-domain 'axes' showing this bone's orientation in DAZ








class CBodyImporter_Original(CBodyImporter_Base):       # Perform the first import of a DAZ-based body.  Rarely done!  Mandatory first step before being able to import source bodies.
    INSTANCE = None

    def __init__(self):
        self.oArm                   = None              # The armature itself
        self.oArmNode               = None              # The armature node (Blender object storing the armature = also parent to mesh)
        self.oArmBones              = None              # Edit-time bones from self.oArm armature
        self.mapBones               = {}                # Dictionary of all the CBone objects in our armature.  Key is CBone.sNameBone
        
        print("\n=== CBodyImporter_Original() ===")
        super(self.__class__, self).__init__("-Original")           # Call the base class ctor to perform import steps that are common to both original and source subclasses

        #=== Remove dumb 90 degree orientation of root node and set scale to 1:1.  We do inverse operation at vert level to provide identical results ===
        oRootNodeO = self.oMesh.GetMesh().parent                    # Mesh root node is parent of the main mesh
        oRootNodeO.name = self.sNameArmatureNode
        oRootNodeO.name = self.sNameArmatureNode
        oRootNodeO.rotation_euler.x = 0
        oRootNodeO.scale = Vector((1,1,1))
        
        #=== Obtain reference to armature ===
        self.oMesh.GetMesh().modifiers[0].name = "Armature"         # Ensure first modifier is called what we need throughout codebase (FBX sets only one modifier = Armature)
        self.oArmNode = self.oMesh.GetMesh().modifiers["Armature"].object  
        self.oArm = self.oArmNode.data
        self.oArm.name = self.sNamePrefix + "-Armature"
        self.oArm.name = self.sNamePrefix + "-Armature"
        self.oArm.draw_type = "OCTAHEDRAL"
    
        #=== Remove all shape keys.  '-Original' mesh is only to preserve our custom vertex groups.  Shape keys stored in '-Source' mesh ===
        self.oMesh.ShapeKeys_RemoveAll()
        
        #=== Apply the inverse rotation we did to the root node above.  All this to ensure vertex positions can be read directly as global coordinate without messy conversions ===
        if self.oMesh.Open():
            bpy.ops.transform.rotate(value=radians(90), axis=(1, 0, 0), constraint_axis=(True, False, False))
            bpy.ops.transform.resize(value=(0.01, 0.01, 0.01))
            self.oMesh.Close()

        #=== Adjust bone angle and rolls from our exported DAZ data ===
        SelectObject(oRootNodeO.name, True)           
        bpy.ops.object.mode_set(mode='EDIT')                        ###INFO: Modifying armature bones is done by simply editing root node containing armature.
        bpy.ops.armature.select_all(action='SELECT')                ###INFO: How to select bones... almost like 'mesh'
        bpy.ops.transform.rotate(value=radians(90), axis=(1, 0, 0), constraint_axis=(True, False, False))       # Rotate and rescale the armature bones to nullify node rotation above and rescale to return bones to meter units (and nullify re-scaling above)
        bpy.ops.transform.resize(value=(0.01, 0.01, 0.01))
        bpy.ops.armature.select_all(action='DESELECT')

        #=== Perform the complex process of modifying the bone armature to have compute usable bone bending angles from custom-exported DAZ information ===
        self.oArmBones = self.oArm.edit_bones
        self.Bones_DefineFromDazInfo()
        SelectObject(self.oMesh.GetName())
        
        #=== Merge the overly-detailed materials mapped to the same texture all together ===
        self.Materials_MergeSlavesToMasters(bDefineResources = True)
       
        


mapRawShapeKeyNamesToGametimeMorphs = {     # Maps DAZ unique morph name to morphing information we need at gametime:
    # 1) Morph category, 2) Morph sub-category, 3) Morph name, 4) Morph subscription level, 5), Morph minimum, 6) Morph maximum
    "CTRLFitness":                  ["Body",        "Shape",        "Fitness",              0, -1.0, 1.5],
    "FBMThin":                      ["Body",        "Shape",        "Thin",                 0, -2.0, 1.2],
    "FBMVictoria7":                 ["Body",        "Shape",        "Type 1",               0, -0.5, 1.0],
    "FBMVoluptuous":                ["Body",        "Shape",        "Voluptuous",           0, -1.0, 1.5],
    "PBMBreastsSize":               ["Breasts",     "Shape",        "Size",                 0, -0.5, 4.0],
    "CTRLBreastsImplants":          ["Breasts",     "Shape",        "Implants",             0, -1.0, 5.0],
    "CTRLBreastsNatural":           ["Breasts",     "Shape",        "Natural",              0, -2.0, 2.0],
    "PBMBreastsHeavy":              ["Breasts",     "Shape",        "Heavy",                0, -0.0, 4.0],
    "PBMBreastsShape05":            ["Breasts",     "Shape",        "Shape 1",              0, -0.5, 2.0],
    "PBMBreastsShape08":            ["Breasts",     "Shape",        "Shape 2",              0, -1.0, 4.0],
    "PBMNipples":                   ["Breasts",     "Nipples",      "Nipples",              0, -0.0, 2.0],
    "PBMNipplesDepth":              ["Breasts",     "Nipples",      "Nipple Depth",         0, -0.0, 2.0],
    "PBMNipplesDiameter":           ["Breasts",     "Nipples",      "Nipple Diameter",      0, -0.0, 3.0],
    "PBMNipplesLarge":              ["Breasts",     "Nipples",      "Nipple Large",         0, -0.0, 3.0],
    "PBMNipplesSize":               ["Breasts",     "Nipples",      "Nipple Size",          0, -0.0, 2.0],

    "Shape - Details A":            ["Penis",       "Shape",        "Shaft Wrinkles",       0, -0.0, 2.0],
    "Heavily Wrinkled":             ["Penis",       "Shape",        "Wrinkles",             0, -0.5, 0.5],
    "Super Round Straight":         ["Penis",       "Shape",        "Irregular Shape 1",    0, -3.0, 3.0],
    "Super Straight Alt":           ["Penis",       "Shape",        "Irregular Shape 2",    0, -2.0, 4.0],
    "Shape - Misshapen A":          ["Penis",       "Shape",        "Irregular Shape 3",    0, -0.8, 1.2],
    "UnderBulge":                   ["Penis",       "Shape",        "Base Folds",           0, -1.0, 1.0],

    "Shape - C Cavernosum U":       ["Penis",       "Cavernosum",   "Cavernosum",           0, -0.0, 2.0],
    "Shape - C Cavernosum U Alt":   ["Penis",       "Cavernosum",   "Cavernosum Edges",     0, -0.0, 3.0],

    "Shape - Big Veins":            ["Penis",       "Veins",        "Large Veins",          0, -0.0, 1.0],
    "Prominent Veins":              ["Penis",       "Veins",        "",                     0, -0.0, 1.5],
    "Shape - Veins A":              ["Penis",       "Veins",        "Veins A",              0, -0.0, 3.0],
    "Shape - Veins B":              ["Penis",       "Veins",        "Veins B",              0, -0.0, 2.0],
    "Dorsal Vein C":                ["Penis",       "Veins",        "Dorsal Vein 1",        0, -0.0, 5.0],

    "Glans Size":                   ["Penis",       "Glans",        "",                     0, -0.5, 1.0],
    "Glans Shape A":                ["Penis",       "Glans",        "",                     0, -0.5, 1.5],
    "Glans Shape B":                ["Penis",       "Glans",        "",                     0, -0.5, 1.0],
    "Glans Shape C":                ["Penis",       "Glans",        "",                     0, -0.5, 1.0],

    "Balloon Balls":                ["Penis",       "Scrotum",      "Scrotum Size",         0, -0.5, 1.0],
    "Turkeyneck":                   ["Penis",       "Scrotum",      "Testicle Fold",        0, -0.3, 1.0],
    "Scrotum Wrinkles":             ["Penis",       "Scrotum",      "",                     0, -1.0, 1.0],
    "Testicle Definition":          ["Penis",       "Scrotum",      "Testicles Shape",      0, -0.5, 1.5],
    "No Testicles":                 ["Penis",       "Scrotum",      "No Testicles",         0, -1.0, 1.0],

}

class CBodyImporter_Source(CBodyImporter_Base):
    
    def __init__(self):
        
        print("\n=== CBodyImporter_Source() ===")
        super(self.__class__, self).__init__("-Source")             # Call the base class ctor to perform import steps that are common to both original and source subclasses

        self.oMeshOriginal = CMesh.Attach(self.sNamePrefix + "-Original")       # Obtain access to the original mesh (Original import must have ran before!)

        DeleteObject(self.sNamePrefix_Daz)                          # Delete the just-imported armature object.  We use the armature created in original import step
        self.oMesh.SetParent(self.sNameArmatureNode)                # Reparent the just-imported source mesh to the previously-processed armature node created in 'CBodyImporter_Original' class

        #=== Rotate and rescale all the morphs / shape keys so source mesh is properly oriented in Blender without any node rotation.  We also change their names to human-friendly names ===
        Util_ConvertShapeKeys(self.oMesh, self.sNamePrefix_Daz)

        #=== Connect our mesh to the armature of the '-Original' mesh previously imported ===
        self.oMesh.GetMesh().modifiers[0].name = "Armature"         # Ensure first modifier is called what we need throughout codebase (FBX sets only one modifier = Armature)
        self.oMesh.GetMesh().modifiers["Armature"].object = bpy.data.objects[self.sNameArmatureNode]  

        #=== Copy the vertex groups from the original mesh to the just-imported 'source' one ===  ###NOTE: Note that this procedure CANNOT transfer vertex groups that have verts at exactly 0 weight!!  (Set them to a tiny value like 1e-30 or something)
        Util_CopyVertGroups(self.oMeshOriginal, self.oMesh)        

        #=== Merge the slave materials into the master ones (as we did for the original mesh) ===
        self.Materials_MergeSlavesToMasters(bDefineResources = False)

        #=== Modify the source woman mesh to give it new bones around vagina opening ===         ###DESIGN: Merge CHoleRig here??
        if self.bIsWoman:
            CHoleRig.CHoleRig(self.oMesh, 0.15)

        print("--- CBodyImporter_Source() finishes ---\n")



class CBodyImporter_Penis():
    def __init__(self):
        self.sNamePrefix            = ""                # The prefix we will give this new mesh type.  (Either 'Man' or 'Woman' or 'Penis')
        self.sNamePrefix_Daz        = ""                # The name DAZ gives the armature object and the mesh (suffixed with '.Shape')  Like 'Genesis3Female' or 'Genesis3Male'
        self.sNameArmatureNode      = ""                # Name given to our armature node.  Always "[" + self.sNamePrefix + "]"
        self.oMesh                  = None              # The mesh this instance processes.  Is the 'original' (untouched) mesh for CBodyImporter_Original subclass and the 'source' mesh (heavily modified) for CBodyImporter_Source subclass 

        #=== Detect what type of mesh the user has imported from Daz from the existance of known .  We can process either a "Genesis 3 Male" or "Genesis 3 Female" body ===
        self.sNamePrefix_Daz = "TAB_Gen3M_27097"         
        if self.sNamePrefix_Daz not in bpy.data.objects:
            raise Exception("\n###EXCEPTION: Could not locate a raw DAZ import mesh for penis.  Exiting importer.")
        self.sNamePrefix = "Penis"
        self.sNameArmatureNode = "[" + self.sNamePrefix + "]" 

        #=== First-order intialization of the raw DAZ mesh ===
        self.oMesh = CMesh.Attach(self.sNamePrefix_Daz + ".Shape")
        self.oMesh.SetName(self.sNamePrefix)
        self.oMesh.GetMesh().show_all_edges = True
        SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)

        #=== Copy the vertex groups from our reference mesh so we don't have to re-enter them at every DAZ import! ===  
        oMeshSrc = CMesh.Attach("PenisA-VertGroupReference")
        Util_CopyVertGroups(oMeshSrc, self.oMesh)        

        #=== Remove dumb 90 degree orientation of root node and set scale to 1:1.  We do inverse operation at vert level to provide identical results ===
        oRootNodeO = self.oMesh.GetMesh().parent                    # Mesh root node is parent of the main mesh
        oRootNodeO.name = self.sNameArmatureNode
        oRootNodeO.name = self.sNameArmatureNode
        oRootNodeO.rotation_euler.x = 0
        oRootNodeO.scale = Vector((1,1,1))
    
        #=== Apply the inverse rotation we did to the root node above.  All this to ensure vertex positions can be read directly as global coordinate without messy conversions ===
        if self.oMesh.Open(bSelect = True):
            bpy.ops.mesh.customdata_custom_splitnormals_clear()         ###INFO:!! Fixes the annoying 'Invalid clnors in this fan!' warnings... See https://blender.stackexchange.com/questions/77332/invalid-clnors-in-this-fan-warning  ###CHECK:!! Are custom loop normal useful for anything?  Placing in this super-important call appropriate for all contexts?  (Can damage some meshes??)
            bpy.ops.object.vertex_group_sort(sort_type='NAME')
            self.oMesh.Close(bDeselect = True)
        
        #=== Lock up all the DAZ vertex groups for protection ===
        self.oMesh.VertGrp_LockUnlock(True, G.C_RexPattern_EVERYTHING)
        
        #=== Obtain reference to armature ===
        self.oMesh.GetMesh().modifiers[0].name = "Armature"         # Ensure first modifier is called what we need throughout codebase (FBX sets only one modifier = Armature)
        self.oArmNode = self.oMesh.GetMesh().modifiers["Armature"].object  
        self.oArm = self.oArmNode.data
        self.oArmBones = self.oArm.edit_bones
        self.oArm.name = self.sNamePrefix + "-Armature"
        self.oArm.name = self.sNamePrefix + "-Armature"
        self.oArm.draw_type = "OCTAHEDRAL"
    
        #=== Remove extraneous penis bones ===
        SelectObject(oRootNodeO.name, True)           
        bpy.ops.object.mode_set(mode='EDIT')                        ###INFO: Modifying armature bones is done by simply editing root node containing armature.
        self.oArmBones.remove(self.oArmBones['hip'])                ###NOTE: We must leave the 'pelvis' bone in otherwise scaling of 'shaft1' would not 'blend' the shaft with the base and look horrible
        self.oArmBones.remove(self.oArmBones['abdomenLower'])
        self.oArmBones.remove(self.oArmBones['lThighBend'])
        self.oArmBones.remove(self.oArmBones['lThighTwist'])
        self.oArmBones.remove(self.oArmBones['rThighBend'])
        self.oArmBones.remove(self.oArmBones['rThighTwist'])

        #=== Rescale and rotate the bones to counter the global rotation / rescale we removed above ===        
        bpy.ops.armature.select_all(action='SELECT')                ###INFO: How to select bones... almost like 'mesh'
        bpy.ops.transform.rotate(value=radians(90), axis=(1, 0, 0), constraint_axis=(True, False, False))       # Rotate and rescale the armature bones to nullify node rotation above and rescale to return bones to meter units (and nullify re-scaling above)
        bpy.ops.transform.resize(value=(0.01, 0.01, 0.01))
        SetView3dPivotPointAndTranOrientation('INDIVIDUAL_ORIGINS', 'GLOBAL', True)     ###INFO: How to rotate individual items about their origin
        bpy.ops.transform.rotate(value=radians(90), axis=(1, 0, 0), constraint_axis=(True, False, False))       # Rotate and rescale the bones about themselves so they orient from penis base toward tip
        SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)
        bpy.ops.armature.select_all(action='DESELECT')

        #=== Rotate and rescale all the morphs / shape keys so source mesh is properly oriented in Blender without any node rotation.  We also change their names to human-friendly names ===
        Util_ConvertShapeKeys(self.oMesh, self.sNamePrefix_Daz)

        #=== Remove the extraneous material slots ===
        SelectObject(self.oMesh.GetName())
        self.oMesh.GetMesh().active_material_index = 2
        bpy.ops.object.material_slot_remove()
        self.oMesh.GetMesh().active_material_index = 1
        bpy.ops.object.material_slot_remove()
        self.oMesh.GetMesh().active_material_index = 0

        #=== Set our material to a known one so Penis fitter can override ===
        aMatSlots = self.oMesh.GetMesh().material_slots
        aMatSlots[0].material = bpy.data.materials["_PenisA"]

        #=== Cleanup the extra materials (created by extra meshes imported by FBX) === 
        Cleanup_MaterialsTexturesImages()               # Any material, texture or image that doesn't start with the "_" prefix gets deleted!
        SetView3dPivotPointAndTranOrientation('INDIVIDUAL_ORIGINS', 'GLOBAL', True)     ###INFO: How to rotate individual items about their origin

        #=== Create additional shape keys from the manipulation of bones ===
        self.Util_CreateShapeKeyFromCurrentArmatureShape("Penis_Shaft_Size_0",        -1.0, 1.0, "shaft1",    1.6)        ###TUNE
        self.Util_CreateShapeKeyFromCurrentArmatureShape("Penis_Scrotum_Size_0",      -0.6, 1.0, "scrotum1",  1.8)
        #-- Create a penis lenght morph --  (more involved than a single bone scale)
        SelectObject(self.oArmNode.name)
        bpy.ops.object.mode_set(mode='POSE')
        n = 0.06                                ###TUNE
        self.oArmNode.pose.bones["shaft1"]  .location.y = n / 4     # Shaft1 cannot move as much because of base
        self.oArmNode.pose.bones["shaft2"]  .location.y = n
        self.oArmNode.pose.bones["shaft3"]  .location.y = n
        self.oArmNode.pose.bones["shaft4"]  .location.y = n
        self.oArmNode.pose.bones["foreskin"].location.y = n / 2
        self.oArmNode.pose.bones["glans"]   .location.y = n / 4
        self.Util_CreateShapeKeyFromCurrentArmatureShape("Penis_Shaft_Length_0", -0.3, 1.0)

        #=== Remove the DAZ vertex groups.  They are useless now that we 'baked' all bone modifications into shape keys.  (They would interfere with gametime skinning) ===
        self.oMesh.VertGrp_Remove(G.C_RexPattern_StandardBones)     ###TODO: This makes armature & bones useless.  Remove them too?
        #self.oMeshO.modifiers.remove()

        #=== Return mesh and scene to defaults ===
        SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', True)     ###NOW: Add new armature, turn into fn, test!
        self.oArmNode.select = False
        self.oArmNode.hide = True
        SelectObject(self.oMesh.GetName())

    
    def Util_CreateShapeKeyFromCurrentArmatureShape(self, sNameShapeKey, nShapeKeyMin, nShapeKeyMax, sNameBoneToModify = None, nScaleXYZ = None):       # Creates a new shape key from the current armature rig.  If 'sNameBoneToModify' is specified it will scale it to 'nScaleXYZ' for a one-line command
        #=== Apply a given transformation to a single armature bone ===
        if sNameBoneToModify is not None:
            SelectObject(self.oArmNode.name)
            bpy.ops.object.mode_set(mode='POSE')
            self.oArmNode.pose.bones[sNameBoneToModify].scale = Vector((nScaleXYZ, nScaleXYZ, nScaleXYZ))
            bpy.ops.object.mode_set(mode='OBJECT')

        #=== 'Bake' the current shape of the skinned mesh to a new shape key ===
        SelectObject(self.oMesh.GetName())
        bpy.ops.object.modifier_apply(modifier="Armature", apply_as='SHAPE')
        self.oMesh.Modifier_AddArmature_ArmatureNode(self.oArmNode)     ###NOTE: Above removes the armature.  Recreate a new one with the same armature node as before
        
        #=== Update the parameters of the just-created shape key ===
        aShapeKeys =  self.oMesh.GetMeshData().shape_keys.key_blocks
        oShapeKey_CreatedFromArmature = aShapeKeys["Armature"]          ###NOTE: modifier_apply() above create a new shape key of the same name with each vert positioned as the bones were set when modifier_apply() was called 
        oShapeKey_CreatedFromArmature.name = sNameShapeKey
        oShapeKey_CreatedFromArmature.slider_min = nShapeKeyMin
        oShapeKey_CreatedFromArmature.slider_max = nShapeKeyMax
        SelectObject(self.oArmNode.name)
        
        #=== Reset all the bones to their default position / rotation / scale ===
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.transforms_clear()
        bpy.ops.pose.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')






def Util_CopyVertGroups(oMeshSrc, oMeshDst):       ###MOVE:??
    #=== Copy the vertex groups from the original mesh to the just-imported 'source' one ===  ###NOTE: Note that this procedure CANNOT transfer vertex groups that have verts at exactly 0 weight!!  (Set them to a tiny value like 1e-30 or something)
    print("\n=== Util_CopyVertGroups() ===")
    SelectObject(oMeshDst.GetName())
    oModDataTransfer = oMeshDst.GetMesh().modifiers.new(name="DATA_TRANSFER", type="DATA_TRANSFER")
    oModDataTransfer.object = oMeshSrc.GetMesh()
    oModDataTransfer.use_vert_data = True
    oModDataTransfer.data_types_verts = {'VGROUP_WEIGHTS'}
    bpy.ops.object.datalayout_transfer(modifier="DATA_TRANSFER")
    AssertFinished(bpy.ops.object.modifier_apply(modifier=oModDataTransfer.name, apply_as='DATA'))      ###INFO: How to properly apply a modifier.  Note we must pass in the name!!
    if oMeshDst.Open(bSelect = True):
        bpy.ops.object.vertex_group_clean(group_select_mode='ALL')
        oMeshDst.Close(bDeselect = True)
    print("--- Util_CopyVertGroups() finishes ---\n")

def Util_ConvertShapeKeys(oMesh, sNamePrefix_Daz):     ###MOVE:??
    #=== Create a temporary copy so we can rotate all shape keys 90 degrees ===
    oMeshCopy = CMesh.AttachFromDuplicate(oMesh.GetName() + "-Temp-ShapeKeysRotator", oMesh)
    oMesh.GetMesh().active_shape_key_index = 0
    aShapeKeysS =  oMeshCopy.GetMeshData().shape_keys.key_blocks
    aShapeKeysD = oMesh.GetMeshData().shape_keys.key_blocks
    nShapeKeys = len(aShapeKeysS)
    nVerts = len(oMesh.GetMeshData().vertices)
    nLenNameShapeKeyPrefixToRemove = len(sNamePrefix_Daz) + 2 

    #=== Rotate and rescale all the morphs / shape keys so source mesh is properly oriented in Blender without any node rotation ===
    for nShapeKey in range(nShapeKeys):
        oShapeKeyS = aShapeKeysS[nShapeKey]
        oShapeKeyD = aShapeKeysD[nShapeKey]     
        if nShapeKey > 0:                       # Avoid renaming first shape key (Basis)        ###IMPROVE: Remove common prefix like FBM, PBM, CTRL, etc
            oShapeKeyD.name = oShapeKeyD.name[nLenNameShapeKeyPrefixToRemove:]      # Remove the prefix DAZ exported inserted into the shape key name
        aVerts_ShapeKeysS = oShapeKeyS.data
        aVerts_ShapeKeysD = oShapeKeyD.data
        oShapeKeyS.value = 0
        oShapeKeyD.value = 0
        for nVert in range(nVerts):
            oVertS = aVerts_ShapeKeysS[nVert]
            vecVertSource   = oVertS.co.copy()
            vecVertRotated  = Vector((vecVertSource.x / 100, -vecVertSource.z / 100, vecVertSource.y / 100))        # Rotate 90 degrees about X and reduce scale by 100
            aVerts_ShapeKeysD[nVert].co = vecVertRotated
            nVert += 1
    oMeshCopy = DeleteObject(oMeshCopy.GetName())                   # We are done with our mesh copy and can delete it.

    #=== Fix the 'Basis' shape key by entering and exiting edit mode === 
    SelectObject(oMesh.GetName())
    oMesh.GetMesh().active_shape_key_index = 0
    bpy.ops.object.mode_set(mode='EDIT')                ###NOTE: Shape key rotation / rescaling above has a basis that doesn't 'take' unless we enter and exit edit mode (there is probably a more efficient way to really 'set' it but I don't know what command)  If we don't do this then some meshes (penis) will have a different scaling orientation when we remove all the shape keys!
    bpy.ops.object.mode_set(mode='OBJECT')

    #=== Convert the raw DAZ shape key names into fully-qualified morphing definitions Unity can use at gametime.  Definition string includes morph category, morphing level, morph name, minimum value, maximum value        
    for oShapeKey in aShapeKeysD:
        sNameShapeKey_DAZ = oShapeKey.name
        if sNameShapeKey_DAZ in mapRawShapeKeyNamesToGametimeMorphs:
            aMorphDefinition = mapRawShapeKeyNamesToGametimeMorphs[sNameShapeKey_DAZ]           # 1) Morph category, 2) Morph sub-category, 3) Morph name, 4) Morph subscription level, 5), Morph minimum, 6) Morph maximum
            oShapeKey.slider_min = aMorphDefinition[4]
            oShapeKey.slider_max = aMorphDefinition[5]
            if aMorphDefinition[2] == "":                   # If morph human name empty use the DAZ name instead
                aMorphDefinition[2] = sNameShapeKey_DAZ 
            oShapeKey.name = aMorphDefinition[0] + "_" + aMorphDefinition[1] + "_" + aMorphDefinition[2] + "_" + str(aMorphDefinition[3])       # + "_" + aMorphDefinition[3] + "_" + aMorphDefinition[4]    ###WEAK: Separate the definition fields into one string so Unity can quickly obtain the same information from the morph description string.  (A cheap but flimsy design!) 
            print("- Converted raw DAZ shape key '{}' to Unity morph '{}'".format(sNameShapeKey_DAZ, oShapeKey.name))
        else:
            if sNameShapeKey_DAZ != "Basis":        # Basis is a valid shape key that is deliberately ignored 
                print("#WARNING: CBodyImporter_Source() cannot find mapping for DAZ shape key '{}'".format(sNameShapeKey_DAZ))

        










        #bpy.ops.object.parent_clear(type='CLEAR')       # Unparent and reparent to clear the bad transform between the two
        #oRootNodeO.select = True
        #bpy.context.scene.objects.active = oRootNodeO
        #bpy.context.scene.objects.active = self.oMesh.GetMesh()
        #bpy.ops.object.parent_set(keep_transform=True)        ###INFO: keep_transform=True is critical to prevent reparenting from destroying the previously set transform of object!!
        #bpy.context.scene.objects.active = self.oMesh.GetMesh()

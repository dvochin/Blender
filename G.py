#=============================================================================== COMMON COMMANDS
# CBody.CBody_GetBodyBase(0).aSoftBodies['Breasts'].aMapSavedRimNormals
# from gBlender import *
# DataLayer_EnumerateInt_DEBUG("Woman", "CmdLine")
# bpy.ops.object.mode_set(mode='EDIT')
# bpy.ops.object.mode_set(mode='OBJECT')
# bpy.ops.mesh.select_all(action='SELECT')
# bpy.ops.mesh.select_all(action='DESELECT')
# bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
# bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
# bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
# bm = bmesh.from_edit_mesh(oMeshO.data)
# import bmesh    bm = bmesh.from_edit_mesh(bpy.context.object.data)
# import bmesh    bm = bmesh.new(); bm.from_mesh(bpy.context.object.data)                                       
# oModBoolean = oMeshO.modifiers.new('BOOLEAN', 'BOOLEAN')
# AssertFinished(bpy.ops.object.modifier_apply(modifier=oModBoolean.name))  ###INFO: Have to specify 'modifier' or this won't work!
# aVerts = [oVert for oVert in bmBody.verts if oVert.select]
# aEdges = [oEdge for oEdge in bm.edges if oEdge.select]
# bpy.context.scene.cursor_location = Vector((0,0,0))
# Debug functionality from http://airplanes3d.net/downloads/pydev/pydev-blender-en.pdf
# bm = bmesh.new()                ###IMPROVE: How to edit a bmesh without EDIT / OBJECT switch?
# bm.from_mesh(obj.data)
# bm.to_mesh(obj.data)
# bpy.ops.mesh.select_more() 

#=== Coordinate systems ===
# Right handed: Blender (+Z Up), DAZ (+Y=Up), OpenGL 
# Left  Handed: Unity, 3DXMax, DirectX
# In LH / RH, X = Index, Y = Major, Z = Thumb
# - Y always point from bone head to tail
# - For mostly vertical bones: orient their local x axis towards the global x axis (e.g. torso and legs)  (From https://blender.stackexchange.com/questions/15609/in-which-direction-should-bone-axes-be-oriented)
# - For mostly horizontal bones: orient their local z axis towards their global z axis (e.g. arms)
# https://docs.blender.org/api/blender_python_api_2_72_1/mathutils.html
# Quaternion conversions LHR / RHR: http://stackoverflow.com/questions/18818102/convert-quaternion-representing-rotation-from-one-coordinate-system-to-another    
#- DAZ:        Up = +Y, Left Side of Body = +X, Body forward: +Z
#- Blender:    Up = +Z, Left Side of Body = +X, Body forward: -Y
#- Unity:      Up = +Y, Left Side of Body = -X, Body forward: +Z
#- quatUnity.X   = -quatBlender.X
#- quatUnity.Y   =  quatBlender.Z
#- quatUnity.Z   = -quatBlender.Y
#- quatUnity.W   =  quatBlender.W           (Remember to negate ALL X,Y,Z angles since we're converting accross coordinate systems)
#- quatUnity.X   = -quatDAZ.X
#- quatUnity.Y   =  quatDAZ.Y
#- quatUnity.Z   =  quatDAZ.Z
#- quatUnity.W   =  quatDAZ.W               (Remember to negate ALL X,Y,Z angles since we're converting accross coordinate systems)
#- quatBlender.X =  quatDAZ.X
#- quatBlender.Y = -quatDAZ.Z
#- quatBlender.Z =  quatDAZ.Y
#- quatBlender.W =  quatDAZ.W               (Remember to negate ALL X,Y,Z angles since we're converting accross coordinate systems)

#from inspect import currentframe, getframeinfo
#G.Dump("ConvertBackTo3D: " + str(getframeinfo(currentframe()).lineno))
# vertlist = [elem.index for elem in bm.select_history if isinstance(elem, bmesh.types.BMVert)]
# import bmesh; bm = bmesh.from_edit_mesh(bpy.context.object.data)

#===============================================================================

###DOCSxx: Date - Description
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
import CClothSrc
from math import *
from mathutils import *
from gBlender import *


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    CONSTANTS
#---------------------------------------------------------------------------    

#---------------------------------------------------------------------------    NODE NAME SUFFIX CONSTANTS        ###TODO: Fan out through the code!
###TODO!!!!  Update / redo these and sync with Unity!
C_NameSuffix_Morph      = "-Morph"          # Suffix applied to the mesh used as the source skinned mesh of the character.  It remains untouched
C_NameSuffix_BodySkin       = "-BodySkin"           # Suffix applied to the mesh used as the skinned body during normal gameplay
# C_NameSuffix_BodyCol        = "-BodyCol"            ###BUG! Suffix applied to the coarsely-decimated body meshes that form the basis of collider speres for the creation of capsules used by Flex to repel cloth and fluid
# C_NameSuffix_BodyColCloth   = "-BodyColCloth"       # Suffix applied to the coarsely-decimated body meshes that form the basis of collider speres for the creation of capsules used by Flex to repel cloth and fluid
C_NameSuffix_BodyRim        = "-BodyRim"         ###OBS?? Suffix applied to the 'reduced skinned mesh' that only have the 'rim polygons' to service fast skinning in Client with 'BakeMesh()'
C_NameSuffix_FlexCollider   = "-FlexCollider"      # Suffix applied to the 'shrunken mesh' of CSoftBody to enable Flex soft bodies to collide much closer than the technology allows
C_NameSuffix_ClothBase      = "-ClothBase"          # Suffix applied to the mesh currently used as base for all clothing (e.g. Client-prepared copy of the bodysuit)
C_NameSuffix_ClothCut       = "-ClothCut"           # Suffix applied to the temporary cloth mesh object currently being processed for display by the game ClothCut mode ####OBS??
C_NameSuffix_ClothFit       = "-ClothFit"           # Suffix applied to the mesh currently used for Flex fitting in Cloth Fit game mode (has no border)  ####OBS??
C_NameSuffix_ClothSkinned   = "-ClothSkinned"       # Suffix applied to part of a cloth that is skinned to its owning body (e.g. is not Flex cloth-simulated)
C_NameSuffix_ClothSimulated = "-ClothSimulated"     # Suffix applied to part of a cloth that is Flex simulated (e.g. is not skinned to its owning body)
C_NameSuffix_PenisShaftCollider = "-PenisShaftCollider"# Suffix applied to capsule mesh created by Penis_CalcTipPosAndRadius() to provide visual feedback to penis designer what colliders will be created as well as providing runtime data during construction of penis colliders
# C_NameSuffix_CBBodyColSpheres = "-CBBodyColSpheres" # Suffix applied to CBBodyColSpheres mesh providing source mesh for creation of spheres & capsules used to repel clothing around breasts in Flex.
C_NameSuffix_Rim            = "-Rim"                # Suffix for softbody rim mesh (for game-time normal adjustment)
C_NameSuffix_RimBackmesh    = "-RimBackmesh"        # Suffix for softbody rim backmesh (for particle hunt)
C_NameSuffix_Face           = "-Face"               # Suffix for character face
C_NameSuffix_BreastCol      = "-BreastCol"          # Suffix applied to the breast collider mesh
C_NameSuffix_Breast         = "-Breast"             # Suffix applied to a source body's cutoff breast (for morphing)
C_NameSuffix_CutterPlane    = "-CutterPlane"        # Suffix applied to cloth cutter planes (responsible to slice cloth)
C_NameSuffix_Unity2Blender  = "-Unity2Blender"      # Suffix applied to temporary meshes created to enable Unity to efficiently uploade verts to Blender.

#---------------------------------------------------------------------------    NODE NAME PREFIX CONSTANTS
C_NamePrefix_Body            = "Body"               # Prefix given to a 'body definition' created by gBL_Body_Create() such as "BodyA", "BodyB", etc that represents an abstract man/woman/shemale body that is processed by most of the code.
C_NamePrefix_CutterAsMesh    = "CutterAsMesh"       # Prefix given to meshes created from curves in gBL_GetCutterAsMesh() that converts a curve into a mesh for Unity rendering.  Also has a node folder of the same name to group these up for easy deletion

#---------------------------------------------------------------------------    NODE NAME CONSTANTS
C_NodeName_ClothSource      = "BodySuit"            ###DESIGN ###TEMP: The node used as cloth source (e.g. 'bodysuit')       
C_NodeName_ClothWorkCopy    = "ClothWorkCopy"       ###DESIGN ###TEMP: The node name given to the work-in-progress mesh created by boolean multi-cuts
C_NodeName_Curve            = "Curve"               # Prefix given to all curves the user moves directly -> These are the basis for 'fit curves' that are shrink-wrapped & smoothed derivations of user curves we derive from for cutting
C_NodeName_Cutter           = "Cutter"              # Prefix given to all curves that are shrink-wrapped and smoothed from the curves the user manipulates directly through pins.  The fit curves create the (temporary) cutting mesh used for boolean cuts
C_NodeName_CurveBevelShape  = "CurveBevelShape"     # Flat 2D hexagon shape to give thickness to curves so user can see them easier
C_NodeName_BasePin          = "Base-Pin"            # The pylon-looking mesh that gives user feedback on where the 'pins' can be moved on cloth-cut curves.
C_NodeName_WorldRotate      = "WorldRotate"         # The node with the 90 degree X rotation to convert from Client to Blender space
C_NodeName_Markers          = "(Markers)"           # Node folder for debug markers
C_NodeName_Marker0          = "(Marker0)"           # A 'special marker' having special meaning for the code being developed
C_NodeName_Marker1          = "(Marker1)"           # A 'special marker' having special meaning for the code being developed

#---------------------------------------------------------------------------    NODE NAME FOLDERS: Empty nodes that are meant for Blender file organization
C_NodeFolder_Game           = "(GAME)"              # A node folder containing runtime generated meshes that are meant to be consumed by game client.
C_NodeFolder_Temp           = "(TEMP)"              # Temporary node folder for misc stuff

#---------------------------------------------------------------------------    VERTEX GROUP CONSTANTS        ###CHECK: That these are strictly enforced everywhere to avoid confusion!!
C_VertGrpPrefix_NonBone = "_"              ###NOTE: All non-bone vertex groups MUSt start with '_' so they can be removed before export to Client!
C_VertGrp_Border = "_Border_"        # All vertex groups that contain collection of verts that define an individual border start with this prefix 
C_VertGrp_Morph  = "_Morph_"         # All vertex groups that have identify vertices to be used for morphing areas (when used with proportional editing) start with this
C_VertGrp_CSoftBody = "_CSoftBody_"        # All vertex groups that identify part of the skinned body that are to be 'detached' for softbody processing begin with this prefix.  (Ex: Breasts)
C_VertGrp_Cutout = "_Cutout_"        # All vertex groups that identify vertices that are removed to make way for other mesh parts (such as Vagina mesh area and Penis mesh area) have this prefix.
C_VertGrp_Area   = "_Area_"          # All vertex groups that contain contiguous areas of the mesh (to be used mostly for mesh seperation) start with this.
C_VertGrp_Area_BreastMorph = C_VertGrp_Area + "BreastMorph"     # The name of the vertex group that blends the breasts to give zero weight at border, near zero near border and so on...
# C_Area_HeadHandFeet = C_VertGrp_Area + "HeadHandFeet"   # Vertex group of body that contains all verts of head, hands and feet.  (Used to remove unneeded verts for BodyCol that would slow down its algorithm)

#---------------------------------------------------------------------------    PROPERTY ARRAY CONSTANTS
#C_PropArray_MapTwinVerts        = "aMapTwinVerts"           # Property array stored in Blender objects storing verts that are 'twinned' (e.g. at same position) between two meshes (e.g. body part and main body)
#C_PropArray_MapSharedNormals    = "aMapSharedNormals"       # Property array stored in Blender objects storing serialized array of what verts share the same normal in Client.
#C_PropArray_ClothSkinToSim      = "aMapClothSkinToSim"      # Property array that maps what verts in the skinned-part of a cloth maps to what (identically positioned) vert of the simulated-part of the same cloth.

#---------------------------------------------------------------------------    CUSTOM DATA LAYERS        ###CLEANUP: Update these and remove useless ones
C_DataLayer_VertSrcBody         = "DataLayer_VertSrcBody"       # Data layer to store the source body verts (the untouched vert IDs as they existed in the source body mesh)  Used for traversal between the different vert domains such as soft skin
C_DataLayer_VertsSrc            = "DataLayer_VertsSrc"          # Original vertex indices in untouched original mesh.  Enables traversal to assembled / morph meshes
C_DataLayer_VertsAssy           = "DataLayer_VertsAssy"         # Original vertex indices in assembled body.  Enables traversal of morphs to assembled body to reach detached softbody meshes (e.g. breasts)
C_DataLayer_Particles           = "DataLayer_Particles"         # Data layer storing the mapping between tetra verts close to their rim and original tetra verts
C_DataLayer_FlexParticleInfo    = "DataLayer_FlexParticleInfo"  # Data layer storing the type of Flex particle in the Flex collider mesh.  (Either 'skinned', simulated-surface-with-bone or simulated-inner)
C_DataLayer_TwinID              = "DataLayer_RimVerts"          # Temporary data layer to store twin-vert ID as mesh is split into parts (Used to reconnect verts at the same location from different meshes)  ####CHECK: Names can't be too long to be unique???
C_DataLayer_SplitVertIDs        = "DataLayer_SplitVertIDs"      # Data layer used while preparing a mesh for Client to construct what just-separated verts for Unity rendering
C_DataLayer_SourceBreastVerts   = 'DataLayer_SourceBreastVerts' # Data layer to store the vertIDs of left and right breast verts from cutoff breast
C_DataLayer_SlaveMeshVerts      = 'DataLayer_SlaveMeshVerts'    # Data layer to store the vertIDs of the verts closest to each verts of this mesh

#---------------------------------------------------------------------------    'MAGIC NUMBERS': Arbitrary constants that have special meanings in arrays
C_MagicNo_TranBegin = 0x0B16  # Magic numbers stored as unsigned shorts at the head & tail of every serialization to help sanity checks...         (MUST MATCH Client SIDE!)
C_MagicNo_TranEnd   = 0xB00B
C_MagicNo_EndOfFlatGroup = 65535            # We indicate the 'end of a 'flattened group' with this invalid vertID indicating the end of the current group (for efficient serialization of variable-sized groups)
#C_MagicNo_EndOfArray = 12345                # The end of a serialized array is indicated by this constant (to help catch out-of-sync error during serialization)

#---------------------------------------------------------------------------    MISC CONSTANTS
C_BorderLenIntoVertGrpWeightRatio = 4           ###CHECK ###SOON: Too low for long borders!! (Just to visualize better!) How real-world lenght numbers are stuffed into vertex groups of borders (that only have a 0..1 range)
C_PiDivBy2 = pi/2

# C_BodyCollider_TrimMargin = 0.03               # Extra space given when trimming body collider verts to create body collider fit to a cloth so as to not remove verts too close to cloth
# C_TypicalRatioTrisToEdges = (35034 / (53283-1000))       # Typical ratio of edges to tris for meshes.  Used to estimate how many faces to decimate when we want an approx number of edges (Calculated from Vic42-17K mesh stats)
# C_RatioEstimatedReductionBodyCol = 0.68        # Ratio of reduction body collider edges after it has removed edge triangles, mirrored and deleted the edges-on-edge
# C_MaxSize_BodyColSphere = 0.110                # The maximum radius of body collider spheres (measured by inserting the largest possible sphere inside body without any poke-through 
C_BreastMorphPivotPt = "BreastMorphPivotPt"                                   # Part of name given to reference points used as pivot points for breast morphing

C_VectorUp      = Vector((0, 0,1))              # The 'up vector' in blender is Z+.  This is used to obtain quaternions to rotate this default vector to another vector (e.g. the normal of a cloth polygon)
C_VectorForward = Vector((0,-1,0))              # The 'up vector' in blender is Z+.  This is used to obtain quaternions to rotate this default vector to another vector (e.g. the normal of a cloth polygon)
C_SymmetrySuffixNames = ['L', 'R']              # Suffix given to symmetrical cuts like arms & legs.  Given to vertex groups and node names...  (Left is 'master' and right the 'slave')  

C_OffsetVertIDs = 1000000                       # Offset applied to all vert IDs pushed into mesh.  Used to separate 'real IDs' from new verts which would have zero ID

C_Prefix_DynBones = '+'                         # Prefix applied to all the 'dynamic bones' this class creates.  These bones are assigned to different bone parents as appropriate for each soft body (e.g. Left breast to 'lPectoral' DAZ bone, Penis to 'Genitals' DAZ bone etc)
C_RexPattern_StandardBones = r"^[a-zA-Z]"       # RegEx search pattern to find DAZ-defined bones = They all start wih a lower-case or upper-case letter. (ALL our bones have a prefix like '+', '_', etc)
C_RexPattern_DynamicBones = r"^\+"              # RegEx search pattern to find dynamic bones.  They ALL start with '+'
C_RexPattern_CodebaseBones = r"^_"              # RegEx search pattern to find codebase bones / vertex groups.  They ALL start with '_'
C_RexPattern_EVERYTHING = r""                   # RegEx search pattern that matches everything


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    GLOBAL VARIABLES (MANUALLY SET BY UNITY AT STARTUP)
#---------------------------------------------------------------------------    
class CGlobals:
    cm_nFlexParticleSpacing = 0.02                  # The inter-particular distance Flex uses to keep its particles away from other particles.  Used to 'shrink' our collision meshes so that collisions appear to occur at the surface of the presentation meshes.
    cm_bSkipLongUnnecessaryOps = False                           # When true codebase will skip long-winded unecessary operations (like breast softbodies)
    cm_aClothSources = {}       ###OBS:?
    DEBUG = None                                    # Debug variable used for quick command-line access to DEBUG_xxx functions
    
    @classmethod
    def Initialize(cls, nFlexParticleSpacing, bSkipLongUnnecessaryOps):
        CGlobals.cm_nFlexParticleSpacing = nFlexParticleSpacing       ###DESIGN: Store diameter or radius??
        CGlobals.cm_bSkipLongUnnecessaryOps = bSkipLongUnnecessaryOps
        CGlobals.cm_aClothSources['BodySuit'] = CClothSrc.CClothSrc('BodySuit')            ###IMPROVE: Create function to automatically create all the cloth sources
        return "OK"                     ###IMPROVE: Try to remove need for functions returning a string from gBlender c code!
    
            


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    DUMP LOG FILE FUNCTIONALITY
#---------------------------------------------------------------------------    
g_oFileDump = None  

def Dump(sText):
    global g_oFileDump
    if g_oFileDump is None:
        g_oFileDump = open("C:/Temp/EroticVR-BlenderScriptDumpFile.txt", "w")        ###DESIGN18:!!!  MOVE!!! and work on auto-init!
        g_oFileDump.write("=== EroticVR Blender Script Dump File ===\n")
    g_oFileDump.writelines(sText + "\n")
    g_oFileDump.flush()

#---------------------------------------------------------------------------    COORDINATE CONVERSION    
#---------------------------------------------------------------------------    Converts from Blender 3D space to Client 3D space.  (Blender is right-handed like OpenGL while most Clients (like Unity and DirectX) are left-handed)
#---------------------------------------------------------------------------    ###IMPORTANT: We just negate x here as we assume that ***EVERY MESH IN BLENDER MEANT FOR EXPORT HAS A ROTATION OF 90 DEGREES ON X***  (This is a must to have intuitive interaction of the meshes with the characters standing up and default Blender camera rotation work intuitively.




###NOTE: A vert of x=1, y=2, z=3 in Blender has that vert one meter to the left of the character, two meters behind and three meters above.
###NOTE: In Unity this needs to be x=-1, y=3, z=-2   so xU=-xB, yU=zB, zU=-yB
def VectorB2U(vec):           
    return Vector((-vec[0], vec[2], -vec[1]))      

def VectorU2B(vec):                    # Same as VectorB2U but copied nonetheless for code readability            
    return VectorB2U(vec)      

def VectorB2U4(vec):           
    return Vector((-vec[0], vec[2], -vec[1], vec[3]))      

def VectorU2B4(vec):            
    return VectorB2U4(vec)      

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    DEBUG UTILITIES
#---------------------------------------------------------------------------    

def Debug_AddMarker(sName, sType, nSize, vecPos, eulerRot):
    bpy.ops.object.empty_add(type=sType, location=vecPos, rotation=eulerRot)
    oNodeMarker = bpy.context.object
    oNodeMarker.parent = bpy.data.objects[C_NodeName_Markers]
    oNodeMarker.empty_draw_size = nSize
    oNodeMarker.show_x_ray = True
    if sName != "":
        oNodeMarker.name = sName
        oNodeMarker.show_name = True
    return oNodeMarker
        
def Debug_GetMarker(sName):
    oNodeMarker = bpy.data.objects[sName]
    oNodeMarker.hide = oNodeMarker.hide_select = False
    return oNodeMarker    

def Debug_RemoveMarkers():
    bpy.ops.object.select_all(action='DESELECT')
    oNodeMarkers = bpy.data.objects[C_NodeName_Markers]
    for oNodeMarker in oNodeMarkers.children:
        if (oNodeMarker.name.startswith('(')):
            oNodeMarker.hide = oNodeMarker.hide_select = True
        else:
            oNodeMarker.select = True
    bpy.ops.object.delete()

def DumpStr(sMsg):          # Simple utility dumper that constructs string, prints it to console and returs it (enables one line to dump to console and return)
    print(sMsg)
    return sMsg



#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    VISUALIZER CUBES
#---------------------------------------------------------------------------    

class CVisualizerCubes():           # CVisualizeCubes:  Extremely useful little cubes of different colors that can be moved wherever            ###MOVE21:?
    def __init__(self, nMaxCubes):  # Create a pool of 'visualizer cubes' that we can move to different entities (to visualize the inner working of various algorithms.  MUST be called in object mode
        self.nMaxCubes = nMaxCubes
        self.aCubes = []
        self.nCubeNext = 0          # Index in self.aCubes we will provide in next call to 'GetCube()'
        
        if self.nMaxCubes > 0:
            print("--- CVisualizerCubes creating {} cubes ---".format(self.nMaxCubes))
            oSrcO = SelectObject("VisualizerCube")
            for nCube in range(self.nMaxCubes):     # Create LINKED duplicates (far more efficient than copies!)
                sName = "VisCube{:03d}".format(nCube)
                oObj = bpy.data.objects[oSrcO.name]
                oObj.select = True
                bpy.context.scene.objects.active = oObj ###INFO: How to quickly link-duplicate objects!
                bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked":True, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0)})
                oVisualizerCube= bpy.context.object          # Duplicate above leaves the duplicated object as the context object...
                oVisualizerCube.name = sName
                oVisualizerCube.select = False
                oVisualizerCube.hide = True
                self.aCubes.append(oVisualizerCube)     ###IMPROVE? Blender has support for object that can share the same mesh... would be perfect here!!
        else:
            print("--- CVisualizerCubes deactivated ---")
            
    def GetCube(self, sName, vecLocation, sColor, nLayer, bIsXray, nScale = 1):
        if self.nMaxCubes == 0:     # If globally deactivated return nothing (e.g. not 'debug mode')
            return None
        
        if self.nCubeNext >= self.nMaxCubes:
            print("###ERROR in CVisualizerCubes.GetCube()  Not enough cubes to service request!")
            return None
            #raise Exception("###EXCEPTION in CVisualizerCubes.GetCube()  Not enough cubes to service request!")
        oVisualizerCube = self.aCubes[self.nCubeNext]
        oVisualizerCube.name = oVisualizerCube.name = sName     # Change mesh name too?
        oVisualizerCube.location = vecLocation
        oVisualizerCube.material_slots[0].material = bpy.data.materials['_VisualizerCube-' + sColor]
        oVisualizerCube.hide = False
        oVisualizerCube.show_x_ray = bIsXray
        oVisualizerCube.scale *= nScale              
        oVisualizerCube.layers[nLayer] = 1
        self.nCubeNext += 1
        return oVisualizerCube
        

#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    ###MOVE
#---------------------------------------------------------------------------    


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    BLENDER CONFIGURATION
#---------------------------------------------------------------------------    

###CHECK: Can crash Blender if NDOF not connected??
bpy.context.user_preferences.inputs.ndof_sensitivity = 6
bpy.context.user_preferences.inputs.ndof_orbit_sensitivity = 3
bpy.context.user_preferences.inputs.ndof_deadzone = 0
bpy.context.user_preferences.inputs.ndof_show_guide = True
bpy.context.user_preferences.inputs.ndof_view_navigate_method = 'ORBIT'
bpy.context.user_preferences.inputs.ndof_view_rotate_method = 'TURNTABLE'

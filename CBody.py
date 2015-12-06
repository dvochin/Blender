###RESUME:
## Now have half-baked init destroy with some bug on 2nd init... still temp mesh a problem!
# Now  implement system for all detached parts to update their verts when morph body changed!  (Same with body)
# Create different hotspot for softbodies based on type and game mode (e.g. morph ops there??)

### Razor line between breasts and body now??? WTF went wrong??

# Can now apply breast morphs to morph body...
    # Must now have mecanism to update all body parts (& collider!) once morph body changed
    # Blender pushing into Unity or Unity pulling from Blender?
    # Central mechanism needed once above decision made to 'trickle down'
        # Will have to revisit with colliders!
            # Collider have same ID even with different verts? (e.g. not one-to-one during remap??)

# Implement character editing... with all the normal entities in place?  (softbody, actors, etc) but just 'paused'
# Mesh temp still there!
# Broke breast collider for cloth. fix it!
# Broke cloth body collider?

# One breast or both??
# Problem with UV maps?  Can remove one?  What about penis / vagina?


#=== Problems ===
# Temp mesh and deletion!
# Large vagina cutout means we can't morph body!
#   Find a way to subdivide vanilla mesh?
#   Or... Re-import from DAZ a body with a top-quality vagina mesh?
#   Related: Can we import DAZ meshes and blend them there?
# Assembled mesh can only display one UV at a time?? 

#=== Improve ===
# Store permutations of source body, genitals as cached meshes?  (If quick to do don't bother?)
# Comments for functions using standard """
# user assert!


import bpy
import sys
import bmesh
import array
from math import *
from mathutils import *
from bpy.props import *

import gBlender
import SourceReloader
import G
import CSoftBody
import Border
import Client



class CBody:
    _aBodies = []                       # The global array of bodies.  Unity finds bodies

    def __init__(self, nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts):
        CBody._aBodies.append(self)                         # Append ourselves to global array.  The only way Unity can find our instance is through CBody._aBodies[<OurID>]
        self.nBodyID            = nBodyID                   # Our ID is passed in by Blender and remains the only public way to access this instance (e.g. CBody._aBodies[<OurID>])
        self.sMeshSource        = sMeshSource               # The name of the source body mesh (e.g. 'WomanA', 'ManA', etc)
        self.sSex               = sSex                      # The body's sex (one of 'Man', 'Woman' or 'Shemale')
        self.sGenitals          = sGenitals                 # The body's genitals (e.g. 'Vagina-Erotic9-A', 'PenisW-Erotic9-A' etc.)
        self.sMeshPrefix        = "Body" + chr(65 + self.nBodyID) + '-'  # The Blender object name prefix of every submesh (e.g. 'BodyA-Detach-Breasts', etc)
        
        self.oMeshSource        = None                      # The 'source body'.  Never modified in any way
        self.oMeshAssembled     = None                      # The 'assembled mesh'.  Fully assembled with proper genitals.  Basis of oMeshMorph                  
        self.oMeshMorph         = None                      # The 'morphing mesh'.   Orinally copied from oMeshAssembled and morphed to the user's preference.  Basis of oMeshBody
        self.oMeshBody          = None                      # The 'body' skinned mesh.   Orinally copied from oMeshMorph.  Has softbody parts (like breasts and penis) removed. 
        self.oMeshFace          = None                      # The 'face mesh'  Simply referenced here to service Unity's request for it  
        self.oMeshUnity2Blender = None                      # The 'Unity-to-Blender' mesh.  Used by Unity to pass in geometry for Blender processing (e.g. Softbody tetravert skinning and pinning)   

        self.aSoftBodies        = {}                        # Dictionary of CSoftBody objects representing softbody-simulated meshes.  (Contains items such as "BreastL", "BreastR", "Penis", "VaginaL", "VaginaR", to point to the object responsible for their meshes)
        
        self.aMapVertsSrcToMorph   = {}                    # Map of which original vert maps to what morph/assembled mesh verts.  Used to traverse morphs intended for the source body                  
        
        print("\n=== CBody()  nBodyID:{}  sMeshPrefix:'{}'  sMeshSource:'{}'  sSex:'{}'  sGenitals:'{}' ===".format(self.nBodyID, self.sMeshPrefix, self.sMeshSource, self.sSex, self.sGenitals))
    
        self.oMeshSource = bpy.data.objects[self.sMeshSource]
        self.oMeshFace = bpy.data.objects[self.sMeshSource + "-Face"]
    
        #=== Duplicate the source body (kept in the most pristine condition possible) as the assembled body. Delete unwanted parts and attach the user-specified genital mesh instead ===    
        self.oMeshAssembled = gBlender.DuplicateAsSingleton(self.oMeshSource.name, self.sMeshPrefix + "Assembled", G.C_NodeFolder_Game, False)  # Creates the top-level body object named like "BodyA", "BodyB", that will accept the various genitals we tack on to the source body.
        
        sNameVertGroupToCutout = None
        if self.sGenitals.startswith("Vagina"):         # Woman has vagina and breasts
            sNameVertGroupToCutout = "_Cutout_Vagina"
        elif self.sGenitals.startswith("Penis"):        # Man & Shemale have penis
            sNameVertGroupToCutout = "_Cutout_Penis"
        if sNameVertGroupToCutout is not None:
            bpy.ops.object.mode_set(mode='EDIT')
            gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled, sNameVertGroupToCutout)     # This vert group holds the verts that are to be soft-body simulated...
            bpy.ops.mesh.delete(type='FACE')                    # ... and delete the mesh part we didn't want copied to output body
            bpy.ops.object.mode_set(mode='OBJECT')
    
        #=== Import and preprocess the genitals mesh and assemble into this mesh ===
        oMeshGenitalsO = gBlender.DuplicateAsSingleton(self.sGenitals, "TEMP_Genitals", G.C_NodeFolder_Temp, True)  ###TEMP!! Commit to file-based import soon!
        bpy.context.scene.objects.active = oMeshGenitalsO
        bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings
     
        #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
        self.oMeshAssembled.select = True
        bpy.context.scene.objects.active = self.oMeshAssembled
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')      # Deselect all verts in assembled mesh
        bpy.ops.object.mode_set(mode='OBJECT')

        ####LEARN: Screws up ConvertMesh royally!  self.oMeshAssembled.data.uv_textures.active_index = 1       # Join call above selects the uv texture of the genitals leaving most of the body untextured.  Revert to full body texture!   ###IMPROVE: Can merge genitals texture into body's??
        gBlender.Util_SelectVertGroupVerts(self.oMeshAssembled, sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
        bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###LEARN: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 

        #=== Create the custom data layer storing assembly vert index.  Enables traversal from Assembly / Morph meshes to Softbody parts 
        gBlender.DataLayer_CreateVertIndex(self.oMeshAssembled.name, G.C_DataLayer_VertsAssy)
        
        #=== Prepare a ready-for-morphing body for Unity.  Also create the 'body' mesh that will have parts detached from it where softbodies are ===   
        self.oMeshMorph = gBlender.DuplicateAsSingleton(self.oMeshAssembled.name, self.sMeshPrefix + 'Morph',   G.C_NodeFolder_Game, True)
        self.oMeshBody  = gBlender.DuplicateAsSingleton(self.oMeshAssembled.name, self.sMeshPrefix + 'Body',    G.C_NodeFolder_Game, True)

        #=== Create map of source verts to morph verts ===  (Enables some morphs such as Breast morphs to be applied to morphing mesh)
        gBlender.SelectAndActivate(self.oMeshMorph.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(self.oMeshMorph.data)
        oLayVertsSrc = bm.verts.layers.int[G.C_DataLayer_VertsSrc]
        for oVert in bm.verts:
            nVertOrig = oVert[oLayVertsSrc] - G.C_OffsetVertIDs        # Remove the offset pushed in during creation
            self.aMapVertsSrcToMorph[nVertOrig] = oVert.index       
        bpy.ops.object.mode_set(mode='OBJECT')

        #=== Create the one-and-only 'Unity2Blender' mesh and assign it to static member of CBody === 
        self.oMeshUnity2Blender = self.CreateMesh_Unity2Blender(nUnity2Blender_NumVerts)



    def CreateSoftBody(self, sSoftBodyPart):
        "Create a softbody by detaching sSoftBodyPart verts from game's skinned main body"
        self.aSoftBodies[sSoftBodyPart] = CSoftBody.CSoftBody(self, sSoftBodyPart)        # This will enable Unity to find this instance by our self.sSoftBodyPart key and the body.
        return "OK"


    def CreateMesh_Unity2Blender(self, nVerts):       ###MOVE: Not really related to CBody but is global
        "Create a temporary Unity2Blender with 'nVerts' vertices.  Used by Unity to pass Blender temporary mesh geometry for Blender processing (e.g. Softbody tetramesh pinning)"
        print("== CreateMesh_Unity2Blender({}) ==".format(nVerts));
        #=== Create the requested number of verts ===
        aVerts = []
        for nVert in range(nVerts):
            aVerts.append((0,0,0))
        #=== Create the mesh with verts only ===
        oMeshD = bpy.data.meshes.new(self.sMeshPrefix + "Unity2Blender")
        oMesh = bpy.data.objects.new(oMeshD.name, oMeshD)
        oMesh.name = oMeshD.name
        oMesh.rotation_euler.x = radians(90)          # Rotate temp mesh 90 degrees like every other mesh.  ###IMPROVE: Get rid of 90 rotation EVERYWHERE!!
        bpy.context.scene.objects.link(oMesh)
        oMeshD.from_pydata(aVerts,[],[])
        oMeshD.update(calc_edges=True)
        gBlender.SetParent(oMesh.name, G.C_NodeFolder_Game)
        return oMesh
    
            
   
  
    



def CBody_Create(nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts):
    "Proxy for CBody ctor as we can only return primitives back to Unity"
    oBody = CBody(nBodyID, sMeshSource, sSex, sGenitals, nUnity2Blender_NumVerts)
    return str(oBody.nBodyID)           # Strings is one of the only things we can return to Unity

def CBody_GetBody(nBodyID):
    "Easy accessor to simplify Unity's access to bodies by ID"
    return CBody._aBodies[nBodyID]

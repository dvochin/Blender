###IDEA: Move all client calls to a CMesh instance...
    # Would trap allocation / de-allocation

###NEEDS:
# Create from copy (duplicate)
# Automatic 'slave mesh' functionality.
# Automatic creation of reverse map
# Subclasses to handle special cases?

####IDEA: Really have master / slave?  SoftBody too complex for this?  Or merge SB into this mechanism too?
#self.oMeshMaster = None                 # Our master mesh.  When its vert positions change we have to update ours
#self.aMeshSlaves = {}                   # Dictionary of meshes that are slaves of this instance.  When our vert positions change these must update themselves


import bpy
import sys
import bmesh
import array
from math import *
from mathutils import *
from bpy.props import *

from gBlender import *
import SourceReloader
import G
import Client




class CMesh:
    def __init__(self, sNameMesh, oMeshO, oMeshParent = None):
        ###IMPROVE?  Won't work in CreateFromDuplicate! DeleteObject(sNameMesh)                # Make sure this mesh does not exist already (all given names globally uniqye by design)
        self.oMeshO         = oMeshO
        self.oMeshParent    = oMeshParent          # Our immediate CMesh parent mesh.  The one we update our verts from after morphing ###NOW### Confusion between morphing parent (still used?) and node parent
        self.bDeleteUponDestroy = True             # By default we delete our Blender object when we get destroyed
        self.SetName(sNameMesh)
        self.bmLastOpen = None                      # The last-opened BMesh.
        self.aMapSharedNormals = None               # Shared normals array (computed by ConvertMeshForUnity() to fix normals accross seams
        
#         if (self.oMeshParent != None):         ###DESIGN ###BUG Confusion with node parent and morph parent!!!
#             self.SetParent(self.oMeshParent.GetName())   ###IMPROVE: By CMesh instead of name??
    #def __del__(self):        ###DEV
        ####BROKEN!!!  Game deletes objects even if they are still reference!  e.g. self.oMeshBody sometimes!!!!!!!!
        #if (self.bDeleteUponDestroy):
        #    DeleteObject(self.sNameMesh.name)

    @classmethod
    def CreateFromDuplicate(cls, sNameMesh, oMeshSrc):
        "Create mesh by duplicating oMeshSrc"
        oMesh = DuplicateAsSingleton(oMeshSrc.GetName(), sNameMesh, oMeshSrc.oMeshO.parent.name, False)
        if (oMesh == None):
            raise Exception("###EXCEPTION: CMesh.CreateFromDuplicate() could not duplicate mesh " + oMeshSrc.oMeshO.parent.name)
        oInstance = cls(sNameMesh, oMesh, oMeshSrc)
        oInstance.bDeleteUponDestroy = True
        oMeshSrc.Hide()              ###CHECK
        return oInstance
        
    @classmethod
    def CreateFromExistingObject(cls, sNameMesh, oMeshParent = None):
        "Create mesh from existing object"
        oMesh = bpy.data.objects[sNameMesh]
        if (oMesh == None):
            raise Exception("###EXCEPTION: CMesh.CreateFromExistingObject() could not find mesh " + sNameMesh)
        oInstance = cls(sNameMesh, oMesh, oMeshParent)
        oInstance.bDeleteUponDestroy = False
        return oInstance

    def Open(self):
        SelectAndActivate(self.oMeshO.name)         ###DEV: Best way by name??        ###IMPROVE: Remember hidden flag??
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Make sure we're in vert mode
        self.bmLastOpen = bmesh.from_edit_mesh(self.oMeshO.data)          ###DEV: Store as member?
        self.UpdateBMeshTables()
        return self.bmLastOpen

    def Close(self):
        if (bpy.ops.mesh.select_mode.poll()):
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Try to set vert mode
        if (bpy.ops.mesh.select_all.poll()):
            bpy.ops.mesh.select_all(action='DESELECT')      # Try to deselect all verts
        self.ExitFromEditMode()
        self.Hide()     ###IMPROVE: Update lookup table and verts

    def ExitFromEditMode(self):     # Cleanly exit 'EDIT' mode while updating bmesh.  Dont affect anything else!
        try:
            bmesh.update_edit_mesh(self.oMeshO.data)
        except:
            print("#WARNING#: CMesh.ExitFromEditMode() could not update_edit_mesh() on mesh " + self.GetName())
        self.bmLastOpen = None
        Util_UnselectMesh(self.oMeshO)
        

    def UpdateBMeshTables(self):
        if (self.bmLastOpen != None):
            self.bmLastOpen.verts.index_update()             ###IMPROVE: Also do edges and faces?
            self.bmLastOpen.edges.index_update()
            self.bmLastOpen.faces.index_update()
            self.bmLastOpen.verts.ensure_lookup_table()
            self.bmLastOpen.edges.ensure_lookup_table()
            self.bmLastOpen.faces.ensure_lookup_table()
    
    def Hide(self):
        Util_HideMesh(self.oMeshO)         ###TODO: Merge all that stuff in gBlender into CMesh!

    def SetName(self, sNameMesh):
        self.oMeshO.name = self.oMeshO.data.name = sNameMesh       ###LEARN: We *must* apply name twice to make sure we get this name (Would get something like 'MyName.001' if 'MyName' was already defined
        self.oMeshO.name = self.oMeshO.data.name = sNameMesh

    def GetName(self):
        return self.oMeshO.name 

    def GetMesh(self):
        return self.oMeshO 

    def SetParent(self, sNameParent):           
        SetParent(self.oMeshO.name, sNameParent)       ###MOVE: Merge in here?

    def DoDestroy(self):
        DeleteObject(self.GetName())       ###CHECK
        self.oMeshO = None
        
#    def GetMeshFromUnity(self):     ###DEV???
#        return self.oMeshO
        
        


    def ConvertMeshForUnity(self, bSplitVertsAtUvSeams):  # Convert a Blender mesh so Client can properly display it. Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
        ###IMPROVE: bSplitVertsAtUvSeams obsolete now that we catch?
        # bSplitVertsAtUvSeams will split verts at UV seams so Unity can properly render.  (Cloth currently unable to simulate this way) ####FIXME ####SOON
        
        if (self.aMapSharedNormals is not None):        # Only do once ###WEAK: poor deicsion... set a flag to make clearer?
            return  
        
        #=== Separate all seam edges to create unique verts for each UV coordinate as Client requires ===
        SelectAndActivate(self.oMeshO.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()  ###DESIGN: Keep here??  ###REVIVE: use_beauty=True 
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(self.oMeshO.data)          
    
        if (len(self.oMeshO.data.edges) == 0):                   # Prevent split of UV if no edges.  (Prevents an error in seams_from_islands() for vert-only meshes (e.g. softbody pinning temp meshes)
            bSplitVertsAtUvSeams = False
        if (len(self.oMeshO.material_slots) < 2):                # Prevent split of UV if less than two materials
            bSplitVertsAtUvSeams = False
    
        #=== Iterate through all edges to select only the non-sharp seams (The sharp edges have been marked as sharp deliberately by border creation code).  We need to split these edges so Client-bound mesh can meet its (very inconvenient) one-normal-per-vertex requirement ===
        if (bSplitVertsAtUvSeams == True):
            try:
                bpy.ops.uv.seams_from_islands()  # Update the edge flags so all seams are flagged        ###DESIGN#11: try still needed??
            except:
                print("###ERROR: Exception running 'uv.seams_from_islands'. Continuing.  Error=", sys.exc_info()[0])
            else:
                for oEdge in bm.edges:
                    if oEdge.seam and oEdge.smooth:  ###LEARN: 'smooth' edge = non-sharp edge!
                        oEdge.select_set(True)
    
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    
    
    
        #=== Load/create a persistent custom data layer to store the 'SharedNormalID' of duplicated verts accross seams that must have their normal averaged out by Client ===
        ###TODO#11: Update docs & cleanup!!
        ###NOTE: as this call can be called multiple times with the mesh getting its edges split each time that this data layer persists and gets added to at each wave of splits.
        ###NOTE: While this data layer is stored in the mesh to persists between call, the 'aMapSharedNormals' below is recreated from this persistent info each time this function is called so Client receives shared normals that had their edges split accross multiple calls
        ###NOTE: An common/important example is Blender taking the morphed body that was client-ready, and appends clothing & separates parts to have result be client-ready again.   
        nNextSharedNormalID = 1
        if G.C_DataLayer_SharedNormals in bm.verts.layers.int:
            oLayVertSharedNormalID = bm.verts.layers.int[G.C_DataLayer_SharedNormals]
        else:
            oLayVertSharedNormalID = bm.verts.layers.int.new(G.C_DataLayer_SharedNormals)
            nNextSharedNormalID = 1
        
        #=== Iterate through the verts that will be split to store into a temp custom data layer a temporary unique ID so that split verts that must have the same normal can be 'twinned' together again so Client can average out their normals
        for oVert in bm.verts:
            if oVert.select:
                oVert[oLayVertSharedNormalID] = nNextSharedNormalID  # Note that we are only assigning new IDs here.  If this call ran before on this mesh, the split verts during that call would have previous IDs in our custom data layer
                nNextSharedNormalID += 1
                
        #=== Split the seam edges so each related polygon gets its own edge & verts.  This way each vert always has one exact UV like Client requires ===
        bpy.ops.mesh.edge_split()                           ###NOTE: Loses selection!
        
        #=== After edge split all verts we have separated can still be 'matched together' by their shared normal ID that has also been duplicated as verts were duplicated === 
        aaSharedNormals = {}  # Create a 'map-of-arrays' that will store the matching vertex indices for each 'shared normals group'.  Done this way because a vert can be split more than once (e.g. at a T between three seams for example)
        for oVert in bm.verts:
            nSharedNormalID = oVert[oLayVertSharedNormalID]
            if nSharedNormalID > 0:  # If this vert has a shared normal ID (from this call or a previous one) the insert it into our map to construct our list of shared normals
                if nSharedNormalID not in aaSharedNormals:  # If our map entry for this group does not exist create an empty array at this map ID so next line will have an array to insert the first item of the group
                    aaSharedNormals[nSharedNormalID] = []
                aaSharedNormals[nSharedNormalID].append(oVert.index)  # Append the vert index to this shared normal group.
    
        #=== 'Flatten' the aaSharedNormals array by separating the groups with a 'magic number' marker.  This enables groups of irregular size to be transfered more efficiently to Client ===
        self.aMapSharedNormals = CByteArray()  # Array of unsigned shorts.   Client can only process meshes under 64K verts anyways...
        for nSharedNormalID in aaSharedNormals:
            aSharedNormals = aaSharedNormals[nSharedNormalID]
            nCountInThisSharedNormalsGroup = len(aSharedNormals)
            if nCountInThisSharedNormalsGroup > 1:  # Groups can be from size 1 (alone) to about 4 verts sharing the same normal with 2 by far the most frequent.  Don't know why we get about 10% singles tho... Grabbed by groups with 3+??
                for nVertID in aSharedNormals:
                    self.aMapSharedNormals.AddUShort(nVertID)
                self.aMapSharedNormals.AddUShort(G.C_MagicNo_EndOfFlatGroup)  # When Client sees this 'magic number' it knows it marks the end of a 'group' and updates the normals for the previous group
    
        self.aMapSharedNormals.CloseArray()

        #self.oMeshO[G.C_PropArray_MapSharedNormals] = aMapSharedNormals.tobytes()  # Store this 'ready-to-serialize' array that is sent with all meshes sent to Client so it can fix normals for seamless display 
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
    

    #---------------------------------------------------------------------------    
    #---------------------------------------------------------------------------    SUPER PUBLIC -> Global top-level functions exported to Client
    #---------------------------------------------------------------------------    

    def Unity_GetMesh(self):  # Called in the constructor of Unity's important CBMesh constructor to return the mesh (possibly skinned depending on mesh anme) + meta info the class needs to run.
        ###IMPROVE#11: Rapidly ported... finish integration into CMesh
        print("=== Unity_GetMesh() sending mesh '{}' ===".format(self.GetName()))

        oMeshO = SelectAndActivate(self.GetName())           ###IMPROVE#11: Move all this crap to CMesh and do only once!!
        ###NOW#13: Cleanup_VertGrp_RemoveNonBones(oMeshO, True)     # Remove the extra vertex groups that are not skinning related from the skinned cloth-part
        self.ConvertMeshForUnity(True)  # Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
    
        oMesh = oMeshO.data
        aVerts = oMesh.vertices
        nVerts = len(aVerts)
        # nEdges = len(oMesh.edges)
        nTris = len(oMesh.polygons)  # Prepare() already triangulated so all polygons are triangles
        nMats = len(oMesh.materials)
    
        #=== Send the 'header' containing a magic number, the number of verts, tris, materials ===
        oBA = CByteArray()
        oBA.AddInt(nVerts)  ###LEARN!!!: Really fucking bad behavior by struct.pack where pack of 'Hi' will give 8 byte result (serialized as both 32-bit) while 'HH' will give 4 bytes (both serialzed as 16-bit)  ###WTF?????
        oBA.AddInt(nTris)
        oBA.AddByte(nMats)
        
        #=== Send our collection of material.  Client will link to the image files to create default materials ===
        for nMat in range(nMats):
            oMat = oMesh.materials[nMat]
            sImgFilepathEnc = "NoTexture"
            if oMat is not None:
                if oMat.name.startswith("Material_"):  # Exception to normal texture-path behavior is for special materials such as 'Material_Invisible'.  Just pass in name of special material and Unity will try to fetch it.  It is assume that Blender and client both define this same material!
                    sImgFilepathEnc = oMat.name  ###IMPROVE: Could pass in more <Unity defined Material>' names to pass special colors and materials??
                else:  # For non-special material we pass in texture path.
                    oTextureSlot = oMat.texture_slots[0]
                    if oTextureSlot:
                        sImgFilepathEnc = oTextureSlot.texture.image.filepath
                        # aSplitImgFilepath = oTextureSlot.texture.image.filepath.rsplit(sep='\\', maxsplit=1)    # Returns a two element list with last being the 'filename.ext' of the image and the first being the path to get there.  We only send Client filename.ext
            oBA.AddString(sImgFilepathEnc)
    
    
        #=== Now pass processing to our C Blender code to internally copy the vert & tris of this mesh to shared memory Client can access directly ===
        print("--- Unity_GetMesh() sharing mesh '{}' of {} verts, {} tris and {} mats with bytearray of size {} ---".format(self.GetName(), nVerts, nTris, nMats, len(oBA)))
        oMesh.tag = True                    ###IMPORTANT: Setting 'tag' on the mesh object and causes the next update to invoke our C-code modification of Blender share/unshare mesh memory to Client
        oMesh.use_fake_user = False         ###NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.  Make sure this is off in this context
        oMesh.update(True, True)            ###IMPORTANT: Our modified Blender C code traps the above flags to update its shared data structures with client...        
    
        return oBA.Unity_GetBytes()             # Return the bytearray intended for Unity deserialization. 
    
    
    def Unity_GetMesh_SkinnedInfo(self):          #=== Send skinning info to Unity's CBSkin objects  (vertex groups with names so Unity can map blender bones -> existing Client bones)
        ###IMPROVE#11: Rapidly ported... finish integration into CMesh
        print("=== Unity_GetMesh_SkinnedInfo() sending mesh '{}' ===".format(self.GetName()))
    
        #=== Unity can only process 4 bones per vert max.  Ensure cleanup ===
        oMeshO = SelectAndActivate(self.GetName())
    #     bpy.ops.object.mode_set(mode='EDIT')
    #     bpy.ops.mesh.select_all(action='SELECT')
    #     bpy.ops.object.vertex_group_limit_total(limit=4)
    #     bpy.ops.object.vertex_group_clean(group_select_mode='ALL')    # Clean up empty vert groups new Blender insists on creating during skin transfer
    #     bpy.ops.mesh.select_all(action='DESELECT')
    #     bpy.ops.object.mode_set(mode='OBJECT')
        Cleanup_VertGrp_RemoveNonBones(oMeshO, True)
        
        #=== Select mesh and obtain reference to needed mesh members ===
        oMesh = oMeshO.data
        aVerts = oMesh.vertices
        nVerts = len(aVerts)
    
        #=== Construct outgoing bytearray Unity can read back ===
        oBA = CByteArray()
        oBA.AddByte(len(oMeshO.vertex_groups))
        for oVertGrp in oMeshO.vertex_groups:
            oBA.AddString(oVertGrp.name)        
     
        #=== Iterate through each vert to send skinning data.  These should have been trimmed down to four in prepare but Client will decipher and keep the best 4 nonetheless ===
        nErrorsBoneGroups = 0     
        for nVert in range(nVerts):
            aVertGroups = aVerts[nVert].groups
            nVertGroups = len(aVertGroups)
            oBA.AddByte(nVertGroups)
            for oVertGroup in aVertGroups:
                nGrp = oVertGroup.group
                if (nGrp < 0 or nGrp > 255):  ###IMPROVE ###CHECK: Why the heck do we see bones with high numbers?  Blender file corruption it seems...
                    G.DumpStr("\n***ERROR: Bones at vert {} with vertgroup {} and weight {}\n".format(nVert, nGrp, oVertGroup.weight))
                    oBA.AddByte (0)  ###CHECK: What to do???
                    oBA.AddFloat(0)
                    nErrorsBoneGroups = nErrorsBoneGroups + 1
                else:  
                    oBA.AddByte (oVertGroup.group)
                    oBA.AddFloat(oVertGroup.weight)
        oBA.AddInt(nErrorsBoneGroups)
    
        return oBA.Unity_GetBytes()          # Return the bytearray intended for Unity deserialization. 

        

        
###DESIGN: SlaveMesh functionality needs:
# Only used for breast colliders, various cloth body collider, full body fluid collider
# Always involves a half-of-body source.  Needs to be mirrored before application
# Other possible usage?  Decorations on clothing?  Borders on clothing?
# Mirroring and slaveing can totally be done before game ships.
# Design-time slaveing always done to source body?
    # What about crotch area verts being replaced... can we still service cloth collider??

### Questions:
# Do we merge into CMesh... or subclass CMeshSlave... or none?
# Would be nice if update to parent mesh trickles down to all descendent meshes (including slaveed meshes)
# How do we handle cloth collider with crotch mesh area replaced???
    # Might have to drop that functionality when we get to body morphing from DAZ

### Decisions:
# Slaving defined at game-design-time and information stored in mesh.
# We'll need to clarify the steps to update all the before-game-ship info with one centra call that updates everything!
# Game body creation loads the design-time information to service Unity requests
# Need to piggy-back on normal parent / slave functionality of CMesh... CMeshSlave overrides virtual call to use its mechansim instead
# We'll drop vagina replacement so user can morph.  Cloth collider will work then
    # For Penis replacement we'll need to remove very few verts but penis collider will repel clothing

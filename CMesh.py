###DOCS24: CMesh - CMesh rewrite
# === DEV ===

# === NEXT ===
 
# === TODO ===
#- All fns with rex
 
# === LATER ===
#> gBlender port:
#- Object selection, unselection, deletion, duplication, reparenting
# - Triangle conversion, manifold enforcement
# - Where to put stuff like AssertFinished() that is truly low-level??  G?
# - Override context stuff still needed?
# - Modifier application?
# - Closest vert finding?
# - Old vertgrp stuff
# - Stream and byte arrays
# 
# > Client port
# - All Unity calls map to Client.py -> remap to CBody.py
# - The old gBL_xxx() calls for mesh sharing / release -> Now a CMesh primitive integrated with its preparation / safety checks

# === OPTIMIZATIONS ===
 
# === REMINDERS ===
 
# === IMPROVE ===
#- Need to run ONLY ONCE triangulate (add flag) 
#- Remember our current mode (verts / edges/ faces) and switch as appropriate?
 
# === NEEDS ===
 
# === DESIGN ===
#- Have various subclasses like for skinned meshes?
#- Merge FlexRig into CBody??
 
# === QUESTIONS ===
 
# === IDEAS ===
 
# === LEARNED ===
 
# === PROBLEMS ===
 
# === WISHLIST ===


import bpy
import sys
import bmesh
import array
from math import *
from mathutils import *
from bpy.props import *

from gBlender import *
import G
import Client




class CMesh:
    cm_oMeshOpenedInEditMode = None                       # The one (and only!) CMesh instance that is opened in Edit mode.  Used as a safety check to detect attempts to open multiple CMeshes in Edit mode
    
    def __init__(self, sNameMesh, oMeshO, bDeleteBlenderObjectUponDestroy = False):
        self.oMeshO    = oMeshO
        self.eMeshMode = EMeshMode.Closed  
        self.bDeleteBlenderObjectUponDestroy = bDeleteBlenderObjectUponDestroy  # By default we delete our Blender object when we get destroyed
        self.bm = None                              # The opened BMesh.  Exists only when Open() is called
        self.bRanConvertMeshForUnity = False        # Flag to ensure ConvertMeshForUnity() only runs once
        self.aaSplitVerts = None                    # Map of arrays of verts that have been split to prepare for Unity rendering
        self.aMapSharedNormals = None               # Shared normals array (computed by ConvertMeshForUnity() to fix normals across seams ###OBS:???
        #self.aNormals = None                        # Normals for each vert.  Stored separately because once we split multi-uv verts for Unity each split will have a separate (wrong) normal so we send Unity the just-before-split normal
        self.oMeshSource = None                     # Reference to the 'source mesh' that was used to create this mesh.  Used to extract 'good normals' for Unity as Unity meshes get their verts split at material seams.  Used only by GetNormals()
        if oMeshO.name != sNameMesh:
            self.SetName(sNameMesh)

    #-----------------------------------------------------------------------    CLASS METHODS CREATORS
    @classmethod
    def Attach(cls, sNameMesh, bDeleteBlenderObjectUponDestroy = False):
        "Creates a CMesh instance from an existing object Blender mesh object."
        oMesh = bpy.data.objects[sNameMesh]
        if (oMesh == None):
            raise Exception("###EXCEPTION: CMesh.Create() could not find mesh " + sNameMesh)
        oInstance = cls(sNameMesh, oMesh, bDeleteBlenderObjectUponDestroy)
        return oInstance

    @classmethod        ###DESIGN: Have a version from a CMesh?
    def AttachFromDuplicate(cls, sNameMesh, oMeshSrc):
        "Creates a CMesh instance from the COPY of an existing object Blender mesh object."
        oMesh = DuplicateAsSingleton(oMeshSrc.GetName(), sNameMesh)
        oInstance = cls(sNameMesh, oMesh, bDeleteBlenderObjectUponDestroy = True)   # As we're a duplicate we set the auto-destroy flag to True so Blender object is destroyed we this CMesh instance is destroyed
        return oInstance

    @classmethod
    def AttachFromDuplicate_ByName(cls, sNameMesh, sNameMeshSrc):       ###IMPROVE: Naming of function... merge both into one and analyze arg type?
        "Creates a CMesh instance from the COPY of an existing object Blender mesh object."
        oMeshO = DuplicateAsSingleton(sNameMeshSrc, sNameMesh)
        oInstance = cls(sNameMesh, oMeshO, bDeleteBlenderObjectUponDestroy = True)   # As we're a duplicate we set the auto-destroy flag to True so Blender object is destroyed we this CMesh instance is destroyed
        return oInstance

    
    #-----------------------------------------------------------------------    OPEN / CLOSE
    def Open(self, bOpenInObjectMode = False, bSelect = False, bDeselect = False):
        if self.eMeshMode != EMeshMode.Closed:
            self.THROW_EXCEPTION("Open", "Open() called while CMesh was in '{}' mode!".format(self.eMeshMode))
        
        if bOpenInObjectMode:
            self.MeshMode_Object()
            self.bm = bmesh.new()
            self.bm.from_mesh(self.oMeshO.data)
            self.eMeshMode = EMeshMode.Object
        else:
            if CMesh.cm_oMeshOpenedInEditMode is not None:        
                self.THROW_EXCEPTION("Open", "Open() called while CMesh '{}' was already opened in Edit mode!".format(CMesh.cm_oMeshOpenedInEditMode.GetName()))
            SelectObject(self.oMeshO.name)         ###DEV: Best way by name??        ###IMPROVE: Remember hidden flag??
            self.MeshMode_Edit(bSelect=bSelect, bDeselect=bDeselect)
            self.bm = bmesh.from_edit_mesh(self.oMeshO.data)
            bpy.ops.mesh.reveal()                       ###INFO: How to show all mesh geometry.  (Lots of operations don't operate on hidden geometry!)
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Make sure we're in vert mode
            self.eMeshMode = EMeshMode.Edit
            CMesh.cm_oMeshOpenedInEditMode = self               # Capture our one-and-only-possible instance of a CMesh opened in Edit mode.  Helps trap attempts at multiple edit-mode opens 
        bpy.ops.mesh.customdata_custom_splitnormals_clear()         ###INFO:!! Fixes the annoying 'Invalid clnors in this fan!' warnings... See https://blender.stackexchange.com/questions/77332/invalid-clnors-in-this-fan-warning  ###CHECK:!! Are custom loop normal useful for anything?  Placing in this super-important call appropriate for all contexts?  (Can damage some meshes??)
        return True                         # Always return 'True' so caller can nest its Open() call in an 'if' statement to clearly visualize in the code the fully life-cycle of the BMesn

    def Close(self, bHide = False, bDeselect = True):                         ###TODO19: iterate through code to hide when we need  ###IMPROVE:!!! Remove these damn arguments that you don't know what they do from calling line.  Replace with strings that accepth tihngs like 'HIDE' and 'DESELECT' 
        if self.eMeshMode == EMeshMode.Closed:
            self.THROW_EXCEPTION("Close", "Close() called while it was already in closed mode!")
        if (bpy.ops.mesh.select_mode.poll()):
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Try to set vert mode
        if self.eMeshMode == EMeshMode.Edit:
            if CMesh.cm_oMeshOpenedInEditMode != self: 
                self.THROW_EXCEPTION("Close", "Close() called with another CMesh '{}' opened in Edit mode!".format(CMesh.cm_oMeshOpenedInEditMode.GetName()))
            bmesh.update_edit_mesh(self.oMeshO.data, tessface=True, destructive=True)        ###DEV24:!!!!!!  destructive (boolean) – Use when geometry has been added or removed. (https://docs.blender.org/api/blender_python_api_current/bmesh.html#bmesh.update_edit_mesh)
            self.MeshMode_Object(bDeselect)
            CMesh.cm_oMeshOpenedInEditMode = None       # Release our one-and-only-possible instance of a CMesh opened in Edit mode.  Helps trap attempts at multiple edit-mode opens 
        if self.eMeshMode == EMeshMode.Object:
            self.bm.to_mesh(self.oMeshO.data)   ###INFO: Read on BMesh construction / destruction at https://docs.blender.org/api/blender_python_api_current/bmesh.html#bmesh.update_edit_mesh
        self.eMeshMode = EMeshMode.Closed
        self.bm.free()
        self.bm = None
        if bHide:
            self.Hide()

    def DoDestroy(self):
        if self.eMeshMode != EMeshMode.Closed:
            self.Close()
        if self.bDeleteBlenderObjectUponDestroy:
            DeleteObject(self.GetName())       ###CHECK
        self.oMeshO = None
        return None                 # Return convenience None so caller's variable is cleared in one line

    def Finalize(self):             # Finalize: Algorithm that created this CMesh is done modifying it.  Permanently 'finalize' it to prepare it for Unity
        self.Hide()                 ###TODO24:!!!!!!! 

        
    #-----------------------------------------------------------------------    MODES
    def MeshMode_Object(self, bSelect = False, bDeselect = False):
        if bSelect:
            bpy.ops.mesh.select_all(action='SELECT')
        if bDeselect:
            bpy.ops.mesh.select_all(action='DESELECT')
        MeshMode_Object(self.GetMesh())
    
    def MeshMode_Edit(self, bSelect = False, bDeselect = False):
        MeshMode_Edit(self.GetMesh())       ###TODO: Merge in primitive?
        if bSelect:
            bpy.ops.mesh.select_all(action='SELECT')
        if bDeselect:
            bpy.ops.mesh.select_all(action='DESELECT')
    

    #-----------------------------------------------------------------------    VERTEX GROUPS
    def VertGrp_Remove(self, rexPattern, bSelectVerts = False):          # Removes vert groups that match the 'rexPattern' regex pattern and optionally select them (for deletion / processing by caller?)
        if bSelectVerts:
            self.PrepareForOp()
            bpy.ops.mesh.select_all(action='DESELECT')
        else:
            self.PrepareForOp(bRequiredOpen = False)
            
        for oVertGrp in self.oMeshO.vertex_groups:
            if re.search(rexPattern, oVertGrp.name):
                self.oMeshO.vertex_groups.active_index = oVertGrp.index
                if bSelectVerts:
                    bpy.ops.object.vertex_group_select()
                #print("- VertGrp_Remove('{}' removing vertex group '{}')".format(self.GetName(), oVertGrp.name))
                self.oMeshO.vertex_groups.remove(oVertGrp)
    
    def VertGrp_SelectVerts(self, sNameVertGrp, bDeselect=False, bClearSelection=True, bThrowIfNotFound=True):            # Select all the verts of the specified vertex group 
        self.PrepareForOp()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')        ###DESIGN:!!!! Really force this?  Can remove??

        if bClearSelection:
            if bDeselect:
                bpy.ops.mesh.select_all(action='SELECT')        # If selection clearing is requested and we're unselecting verts start with a fully-selected mesh 
            else: 
                bpy.ops.mesh.select_all(action='DESELECT')      # If selection clearing is requested and we're selecting verts start with a completely unselected mesh
    
        nVertGrpIndex = self.oMeshO.vertex_groups.find(sNameVertGrp)
        if (nVertGrpIndex != -1):
            self.oMeshO.vertex_groups.active_index = nVertGrpIndex
            if bDeselect:
                bpy.ops.object.vertex_group_deselect()
            else:
                bpy.ops.object.vertex_group_select()
            oVertGrp = self.oMeshO.vertex_groups[nVertGrpIndex]
            return oVertGrp 
        else:
            if bThrowIfNotFound:
                self.THROW_EXCEPTION("VertGrp_SelectVerts", "Could not find vertex group '{}'".format(sNameVertGrp))
            else:
                print("#WARNING: VertGrp_SelectVerts() on CMesh '{}' could not find vertex group '{}'.".format(self.GetName(), sNameVertGrp))
                
    def VertGrps_SelectVerts(self, rexPattern, bDeselect=False, bClearSelection=True): 
        self.PrepareForOp()
        if bClearSelection:
            bpy.ops.mesh.select_all(action='DESELECT') 
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')        ###DESIGN:!!!! Really force this?  Can remove??
    
        for oVertGrp in self.oMeshO.vertex_groups:
            if re.search(rexPattern, oVertGrp.name):
                self.oMeshO.vertex_groups.active_index = oVertGrp.index
                if bDeselect:
                    bpy.ops.object.vertex_group_deselect()
                else:
                    bpy.ops.object.vertex_group_select()
                

                
    def VertGrp_LockUnlock(self, bLock, rexPattern = None):
        self.PrepareForOp(bRequiredOpen = False)
        
        if rexPattern is None:
            for oVertGrp in self.oMeshO.vertex_groups:
                oVertGrp.lock_weight = bLock
        else:
            for oVertGrp in self.oMeshO.vertex_groups:
                if re.search(rexPattern, oVertGrp.name):
                    oVertGrp.lock_weight = bLock             ###INFO: Locking vertex groups is *extremely* useful to blend bones!

    def VertGrp_LimitAndNormalize(self, nSmoothLevel = 0):        # Limit than normalize all bones in Flex rig (optional smooth before).  Must be in Edit mode
        self.VertGrp_LockUnlock(False, G.C_RexPattern_EVERYTHING)    ###DESIGN: Keep here?
        bpy.ops.mesh.select_all(action='SELECT')
        if nSmoothLevel > 0:
            bpy.ops.object.vertex_group_smooth(repeat=1, factor=nSmoothLevel)
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)
        bpy.ops.mesh.select_all(action='DESELECT')

    def VertGrp_FindFirstVertInGroup(self, sNameVertGrp):
        self.PrepareForOp(bRequiredOpen = False)
        self.VertGrp_SelectVerts(sNameVertGrp)
        for oVert in self.bm.verts:
            if oVert.select:
                return oVert
        raise Exception("###EXCEPTION: VertGrp_FindFirstVertInGroup() could not find a single vert while searching in vertex group '{}'".format(sNameVertGrp))
        
         

    #---------------------------------------------------------------------------    MATERIALS
    def Material_Remove(self, sNameMaterial, bLeaveVerts = False, sNameMaterialDestination = None):        # Remove material 'sNameMaterial' from mesh (and optionally the associated verts)  If 'sNameMaterialDestination' is set these verts will be assigned to that material (i.e. are merged)
        #print("- CMesh.Material_Remove('{}') attempting to remove material slot '{}' with bLeaveVerts = '{}'".format(self.GetName(), sNameMaterial, bLeaveVerts))
        aMaterials = self.GetMeshData().materials
        nMatSlotID = aMaterials.find(sNameMaterial)            ###LEARN: Search by name using find() the only way to delete materials? 
        if nMatSlotID != -1:
            self.oMeshO.active_material_index = nMatSlotID
            if sNameMaterialDestination is not None:
                print("- Material_Remove() merging slave material '{}' into master material '{}'".format(sNameMaterial, sNameMaterialDestination))
                self.MeshMode_Edit(bDeselect = True)
                bpy.ops.object.material_slot_select()
                nMatSlotID_Destination = aMaterials.find(sNameMaterialDestination)
                if nMatSlotID_Destination == -1:
                    raise Exception("\n###EXCEPTION: Material_Remove() could not find sNameMaterialDestination '{}'.".format(sNameMaterialDestination)) 
                self.oMeshO.active_material_index = nMatSlotID_Destination
                bpy.ops.object.material_slot_assign()
                self.oMeshO.active_material_index = nMatSlotID      # Return material slot selection back to the material slot we need to delete
                self.MeshMode_Object(bDeselect = True)
            else:
                if bLeaveVerts == False:
                    self.MeshMode_Edit()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.material_slot_select()
                    bpy.ops.mesh.delete(type='FACE')
                    self.MeshMode_Object()
            bpy.ops.object.material_slot_remove()
        else:
            print("#WARNING: CMesh.Material_Remove('{}') cannot find material slot '{}'".format(self.GetName(), sNameMaterial))

    def Materials_Remove(self, rexPattern, bLeaveVerts = False):        # Remove from all material (and their associated verts) that starts with 'sNameMaterialPrefix'
        aMaterialSlots = self.GetMesh().material_slots
        aMaterialsToDelete = []
        for oMatSlot in aMaterialSlots:
            if re.search(rexPattern, oMatSlot.name):
                aMaterialsToDelete.append(oMatSlot.name)       # We append to a 'remove collection' because we cannot iterate and remove in the same loop!
        for sNameMat in aMaterialsToDelete:
            self.Material_Remove(sNameMat, bLeaveVerts)        # Not optimal to remove this way but can't find a way to pass in an object that can feed into 'active_material_index' 
        if len(aMaterialSlots) == 0:
            bpy.ops.object.material_slot_add()      # Add a single default material that will captures all the polygons of our mesh.  This is needed so we can properly send the mesh to Unity
    

    #---------------------------------------------------------------------------    SHAPE KEYS
    def ShapeKeys_RemoveAll(self):                        # Remove all the shape keys of the current mesh.
        self.SelectObject()
        bpy.context.object.active_shape_key_index = 1       ###CHECK: cannot remove shape keys if basis is selected!  ###WEAK: 1 might not exist?
        if bpy.ops.object.shape_key_remove.poll():
            bpy.ops.object.shape_key_remove(all=True)
            
    def ShapeKey_Print(self, sSeparator = None):                          # Prints the shape keys to the console (removing the optional sSeparator) in a form that makes it easy to create the mapping Python code
        print("\n=== Dumping shape keys of mesh '{}' ===".format(self.GetName()))
        aShapeKeys = self.GetMeshData().shape_keys.key_blocks
        aShapeKeyNames = []
        for oShapeKey in aShapeKeys:
            sNameShapeKey = oShapeKey.name
            if sSeparator is not None:
                nPosSeparator = sNameShapeKey.find(sSeparator)
                if nPosSeparator != -1:
                    sNameShapeKey = sNameShapeKey[nPosSeparator+len(sSeparator):]
            aShapeKeyNames.append(sNameShapeKey)
        aShapeKeyNames.sort()
        for sNameShapeKey in aShapeKeyNames: 
            print("\t\"{}\":\t\t[\"BBBBBBB\",     \"CCCCCCCC\",      0, -0.0, 1.0],".format(sNameShapeKey))
            
        print("\n--- Done ---")


    #---------------------------------------------------------------------------    DATA LAYERS
    def DataLayer_Create_SimpleVertID(self, sNameDataLayer):        # Create a custom data layer that stores (offsetted) vertex IDs.  This is useful for domain traversal 
        if self.Open():                                             # Store the vert ID into its own data layer.  This way we can always get back the (authoritative) vert ID and always know exactly which vert we're refering to in any vert domain (e.g. mesh parts cut off from source body)
            oLay = self.bm.verts.layers.int.new(sNameDataLayer)
            for oVert in self.bm.verts:    
                oVert[oLay] = oVert.index + G.C_OffsetVertIDs       # Stored vertex IDs are offsetted so the default value of 0 means 'new vert'!
            self.Close()
        return oLay
        
    def DataLayer_SelectMatchingVerts(self, oLay, nValueSearch, nValueMask = 0xFFFFFFFF, bDeselectFirst=True):    # Select verts by a given data layer test
        if bDeselectFirst:                
            bpy.ops.mesh.select_all(action='DESELECT')
        for oVert in self.bm.verts:
            if (oVert[oLay] & nValueMask) == nValueSearch:
                oVert.select_set(True)
    
    def DataLayer_SetValueToSelection(self, oLay, nValue):        # Apply the given value to each selected vert's data layer
        for oVert in self.bm.verts:
            if oVert.select:
                oVert[oLay] = nValue
    
    def DataLayer_PrintMeshVerts(self, sDebugMsg, sNameMesh, sNameLayer=None):  ###OBS?
        print("\n=== PrintMeshVert for mesh '{}' and layer '{}' for '{}'".format(sNameMesh, sNameLayer, sDebugMsg))
        oMeshO = SelectObject(sNameMesh, True)
        bm = bmesh.new()
        bm.from_mesh(oMeshO.data)
        if (sNameLayer != None):
            oLayer = self.bm.verts.layers.int[sNameLayer]
        nLayer = -1
        for oVert in self.bm.verts:
            vecPos = oVert.co
            if (sNameLayer != None):
                nLayer = oVert[oLayer]
            print("- Vert {:4d} = {:8.5f} {:8.5f} {:8.5f}   Layer = {:3d}   Sel = {}".format(oVert.index, vecPos.x, vecPos.y, vecPos.z, nLayer, oVert.select))
        print("==========================\n")
    

    #---------------------------------------------------------------------------    MODIFIERS
    def Modifier_AddArmature(self, oMeshSrcO):        # Adds an armature modifier with the same parent armature as 'oMeshSrcO'
        oModArmature = self.oMeshO.modifiers.new(name="Armature", type="ARMATURE")
        oModArmature.object = oMeshSrcO.modifiers["Armature"].object
    
    def Modifier_AddArmature_ArmatureNode(self, oArmatureNodeO):        # Adds an armature modifier and set its armature node to 'oArmatureNode'
        oModArmature = self.oMeshO.modifiers.new(name="Armature", type="ARMATURE")
        oModArmature.object = oArmatureNodeO
    
    def Modifier_Remesh(self, nOctreeDepth, nRemeshScale):            # Applies a remesh modifier with the given arguments
        self.Modifier_RemoveAll()                   # Remove all the modifiers.  Remesh trashes everything anyways (armature has to be rebuilt)
        VertGrp_RemoveAll(self.oMeshO)              # Remove all vertex groups.  Remesh trashes them all
        oModRemesh = self.oMeshO.modifiers.new(name="REMESH", type="REMESH")  
        oModRemesh.mode = 'SMOOTH'                  # Smooth is the only usable mode.  Sharp generates horrible non-manifold geometry and block is for Minecraft look!
        oModRemesh.octree_depth = nOctreeDepth        
        oModRemesh.scale = nRemeshScale             ###IMPROVE:!! Need to convert remesh arguments based on body height to inter-particular distance 
        oModRemesh.use_remove_disconnected = True
        AssertFinished(bpy.ops.object.modifier_apply(modifier=oModRemesh.name))     ###INFO: This call destroys skinning info / vertex groups
    
    def Modifier_RemoveAll(self):            # Removes all the modifiers
        while len(self.oMeshO.modifiers) > 0:         
            self.oMeshO.modifiers.remove(self.oMeshO.modifiers[0])
    
    
    #---------------------------------------------------------------------------    UTILITIES
    def Util_JoinWithMesh(self, oMeshJoinTargetO):            # Join this mesh with the oMeshJoinTargetO mesh.  This mesh is destroyed by the join (geometry becomes part of 'oMeshJoinTargetO') 
        bpy.ops.object.select_all(action='DESELECT')
        self.oMeshO.hide = False
        self.oMeshO.select = True
        oMeshJoinTargetO.GetMesh().hide = False
        oMeshJoinTargetO.GetMesh().select = True
        bpy.context.scene.objects.active = oMeshJoinTargetO.GetMesh()       ###INFO: How to join two meshes: with both source and target selected, the 'active' one is the target and the non-active one the source (gets destroyed as its geometry becomes part of target)
        bpy.ops.object.join()
        return None                 # Return a convenience none so caller can clear its reference while calling us.
   
    def Util_TransferWeights(self, oMeshSrc, bCleanGroups = True, bAddArmature = False):        # Transfer the skinning information from mesh oMeshSrc to oMeshO
        print("- Util_TransferWeights() begins transferring weights from '{}' to  '{}'".format(oMeshSrc.GetName(), self.GetName()))
        self.SelectObject()
        oMeshSrc.Unhide()
        oModTransfer = self.oMeshO.modifiers.new(name="DATA_TRANSFER", type="DATA_TRANSFER")
        oModTransfer.object = oMeshSrc.GetMesh()
        oModTransfer.use_vert_data = True
        oModTransfer.data_types_verts = { "VGROUP_WEIGHTS" }
        bpy.ops.object.datalayout_transfer(modifier=oModTransfer.name)    ###INFO: Operation acts upon the setting of 
        AssertFinished(bpy.ops.object.modifier_apply(modifier=oModTransfer.name))
        if bCleanGroups:
            bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
            bpy.ops.object.vertex_group_clean(group_select_mode='ALL')    ###INFO: Needs weight mode to work! (???)  ###DESIGN: Keep??
        self.MeshMode_Object()
        if bAddArmature:
            self.Modifier_AddArmature(oMeshSrc.GetMesh())
        print("= Util_TransferWeights() completes.")

    def Util_RemoveNonManifoldGeometry(self):
        #=== Perform a maximum number of attempts at edge collapse-then-dissolve.  This is done to make sure the mesh remains manifold as we shrink ===
        for nRepeat in range(10):                                      ###OPT:!!
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')      # We must deliver to Unity a manifold triangle-only mesh.  Non-manifold verts can hide in n-gons so we must re-triangulate at every change ###OPT:!!
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_non_manifold(extend=True, use_wire=True, use_boundary=True, use_multi_face=True, use_non_contiguous=True, use_verts=True)
            nNumBadVerts = self.oMeshO.data.total_vert_sel
            if nNumBadVerts == 0:
                break
            print("-- Util_RemoveNonManifoldGeometry() completed run #{} and still has {:3d} non-manifold verts".format(nRepeat, nNumBadVerts))
            bpy.ops.mesh.edge_collapse()                    ###INFO: Edge collapse selects geometry it could not process completely... dissolving those verts and then re-triangulating is *very* effective to get to manifold geometry after a shrink
            bpy.ops.mesh.dissolve_verts()                   ###INFO: This statement group greatly helps get a great shrunken mesh!
        if nNumBadVerts > 0: 
            raise Exception("\n\n\n###EXCEPTION: in Util_SafeRemoveDouble for mesh '{}'.   {} non-manifold verts still exist after remove_doubles()!\n\n".format(bpy.context.object.name, nNumBadVerts))
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')      # Dissolving verts above causes n-gons... re-triangulate
        bpy.ops.mesh.select_all(action='DESELECT')
                
    def Util_SafeRemoveDouble(self, nDistRemoveDoubles):                # The super-important safe remove doubles function.  This safe version will clean up horrible degenerate geometry that would cause later code to fail  
        bpy.ops.mesh.remove_doubles(threshold=nDistRemoveDoubles)       #=== First call remove_doubles() on the selection the caller has setup ===
        self.Util_RemoveNonManifoldGeometry()          #=== Perform a maximum number of attempts at edge collapse-then-dissolve.  This is done to make sure the mesh remains manifold as we shrink ===
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')      # Dissolving verts above causes n-gons... re-triangulate
        bpy.ops.mesh.select_all(action='DESELECT')

    
    
    
    
    
    
    #---------------------------------------------------------------------------    ###MOVE
    def SelectObject(self):         
        SelectObject(self.GetName(), bCheckForPresence = True)      ###DESIGN:? Merge base version in?

    def Decimate_MinArea(self, nRatioDecimate, nFaceAreaMin):        # Decimate the mesh to attempt to reach 'nRatioDecimate' verts
        self.PrepareForOp()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        for oFace in self.bm.faces:                         # Select the faces with less area than the specified minimum threshold
            if oFace.calc_area() < nFaceAreaMin:
                oFace.select_set(True)
        bpy.ops.mesh.select_more()              ###CHECK24: Keep??
        bpy.ops.mesh.decimate(ratio=nRatioDecimate)
        #bpy.ops.mesh.quads_convert_to_tris()        ###OPT:!!! Needed??
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')

    def Decimate_All(self, nNumTargetVerts):        # Decimate the mesh to attempt to reach 'nNumTargetVerts' verts
        self.PrepareForOp()
        nRatioDecimate = nNumTargetVerts / len(self.GetMeshData().vertices) 
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.decimate(ratio=nRatioDecimate)
        #bpy.ops.mesh.quads_convert_to_tris()        ###OPT:!!! Needed??
        bpy.ops.mesh.select_all(action='DESELECT')

    def Decimate_VertGrp(self, sNameVertGrp, nRatioDecimate):        # Decimate the mesh to attempt to reach 'nNumTargetVerts' verts
        self.PrepareForOp()
        self.VertGrp_SelectVerts(sNameVertGrp)
        bpy.ops.mesh.decimate(ratio=nRatioDecimate)
        bpy.ops.object.vertex_group_assign()                # Decimate above removes most verts from the vertex group.  As post-decimate vertex groups are currently selected, assign them to the source vertex group 



    
    #---------------------------------------------------------------------------    SAFETY CHECKS
    def SafetyCheck_CheckForManifoldMesh(self, sMsg):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold(extend=True, use_wire=True, use_boundary=True, use_multi_face=True, use_non_contiguous=True, use_verts=True)
        self.SafetyCheck_ThrowExceptionIfVertsSelected(sMsg)
    
    def SafetyCheck_CheckBoneWeighs(self):
        aVertsBad = []
        if self.Open(bOpenInObjectMode = True):
            nErr_NumVertsOverFourBones = 0
            nErr_NumVertsUnderFourBones = 0
            nErr_NumVertsWithBadWeightSum = 0
            for oVertO in self.oMeshO.data.vertices:
                aVertGroups = oVertO.groups
                nVertGroups = len(aVertGroups)
                if nVertGroups != 4:
                    if nVertGroups > 4:
                        nErr_NumVertsOverFourBones += 1
                        aVertsBad.append(oVertO.index)
                    else:
                        nErr_NumVertsUnderFourBones += 1
                nBoneWeight = 0
                for oVertGroup in aVertGroups:
                    nBoneWeight += oVertGroup.weight
                if nBoneWeight < 0.99 or nBoneWeight > 1.01:
                    aVertsBad.append(oVertO.index)
                    nErr_NumVertsWithBadWeightSum += 1
            self.Close()
            
        if nErr_NumVertsOverFourBones > 0 or nErr_NumVertsWithBadWeightSum > 0:
            if self.Open(bDeselect=True):
                self.bm.verts.ensure_lookup_table()
                for nVert in aVertsBad:
                    self.bm.verts[nVert].select_set(True)
                self.THROW_EXCEPTION("SafetyCheck_CheckBoneWeighs", "Found {} verts on mesh over 4 bones and {} verts under 4 bones and {} verts with invalid weight sums.".format(nErr_NumVertsOverFourBones, nErr_NumVertsUnderFourBones, nErr_NumVertsWithBadWeightSum))
        
    def SafetyCheck_ThrowExceptionIfVertsSelected(self, sMsg):
        nNumBadVerts = self.oMeshO.data.total_vert_sel       ###LEARN: How to quickly obtain # of selected verts!        #nNumBadVerts = len([oVert for oVert in self.bm.verts if oVert.select])
        if nNumBadVerts > 0:
            self.THROW_EXCEPTION("SafetyCheck_ThrowExceptionIfVertsSelected", "Verts={}".format(sMsg, nNumBadVerts))
        
    def SafetyCheck_PerformAllTests(self):
        self.SafetyCheck_CheckBoneWeighs()
        self.Open()
        self.SafetyCheck_CheckForManifoldMesh("Non-manifold mesh detected")
        self.Close()
    

    #-----------------------------------------------------------------------    UTILITY
    def PrepareForOp(self, bRequiredOpen = True):
        if self.oMeshO is None:
            self.THROW_EXCEPTION("PrepareForOp", "CMesh has a null oMeshOp!")
        if bRequiredOpen and self.eMeshMode == EMeshMode.Closed:
            self.THROW_EXCEPTION("PrepareForOp", "CMesh was in closed mode while an op requiring an opened mode!")
        
    def UpdateBMeshTables(self):
        if (self.bm != None):
            self.bm.verts.index_update()             ###OPT: Can all of this be too expensive every time we open a mesh?
            self.bm.edges.index_update()
            self.bm.faces.index_update()
            self.bm.verts.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()
            self.bm.faces.ensure_lookup_table()
    
    def THROW_EXCEPTION(self, sFunction, sMsg):     ###TODO:!! Add a global exception handler and hook into that?
        raise Exception("###EXCEPTION in CMesh.{}() on mesh '{}'.   {}".format(sFunction, self.GetName(), sMsg))
        

    #-----------------------------------------------------------------------    UTILITY
    def Hide(self):
        Util_HideMesh(self.oMeshO)         ###TODO: Merge all that stuff in gBlender into CMesh!

    def Unhide(self):
        Util_UnhideMesh(self.oMeshO)

    def SetName(self, sNameMesh):
        self.oMeshO.name = self.oMeshO.data.name = sNameMesh       ###INFO: We *must* apply name twice to make sure we get this name (Would get something like 'MyName.001' if 'MyName' was already defined
        self.oMeshO.name = self.oMeshO.data.name = sNameMesh

    def GetName(self):
        return self.oMeshO.name 

    def GetMesh(self):
        return self.oMeshO 

    def GetMeshData(self):
        return self.oMeshO.data 

    def SetParent(self, sNameParent):           
        SetParent(self.oMeshO.name, sNameParent)       ###MOVE: Merge in here?

    
        
        
        

    #-----------------------------------------------------------------------    UNITY LINK

    def ConvertMeshForUnity(self, bSplitVertsAtUvSeams):  # Convert a Blender mesh so Client can properly display it. Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
        ###IMPROVE: bSplitVertsAtUvSeams obsolete now that we catch?
        ###IMPROVE: Make sure this expensive call can only run ONCE and that it MUST run (before it is sent to Unity)  Unity cannot render multi-material meshes without modifications for shared normals ###CHECK: Maybe recent Unity can?
        # bSplitVertsAtUvSeams will split verts at UV seams so Unity can properly render.  (Cloth currently unable to simulate this way) ####FIXME ####SOON
        if self.bRanConvertMeshForUnity:
            return  
        
        #=== Separate all seam edges to create unique verts for each UV coordinate as Client requires ===
        SelectObject(self.oMeshO.name)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()                       # First un-hide all geometry
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')  ###DESIGN: Keep here? 
        
        ###HACK24:!!!!!!!!! Only do this ONCE!  But where?????
#         if bpy.ops.object.vertex_group_clean.poll():        ###BUG ###DEV24:!!!!!!!!! Run this somewhere fuck!
#             bpy.ops.object.vertex_group_clean(group_select_mode='ALL')    # Clean up empty vert groups new Blender insists on creating during skin transfer
        if bpy.ops.object.vertex_group_limit_total.poll():
            bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # Limit mesh to four bones each   ###CHECK: Possible our 'non-bone' vertgrp take info away???
        if bpy.ops.object.vertex_group_normalize_all.poll():
            bpy.ops.object.vertex_group_normalize_all(lock_active=False)
        
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(self.oMeshO.data)          
    
        if (len(self.oMeshO.data.edges) == 0):                   # Prevent split of UV if no edges.  (Prevents an error in seams_from_islands() for vert-only meshes (e.g. softbody pinning temp meshes)
            bSplitVertsAtUvSeams = False
        if (len(self.oMeshO.material_slots) < 2):                # Prevent split of UV if less than two materials
            bSplitVertsAtUvSeams = False
    
        #=== Iterate through all edges to select only the non-sharp seams (The sharp edges have been marked as sharp deliberately by border creation code).  We need to split these edges so Client-bound mesh can meet its (very inconvenient) one-normal-per-vertex requirement ===
        if (bSplitVertsAtUvSeams == True):
            try:
                bpy.ops.uv.seams_from_islands()  # Update the edge flags so all seams are flagged        ###DESIGN11: try still needed??
            except:
                print("###ERROR: Exception running 'uv.seams_from_islands'. Continuing.  Error=", sys.exc_info()[0])
            else:
                for oEdge in bm.edges:
                    if oEdge.seam and oEdge.smooth:  ###INFO: 'smooth' edge = non-sharp edge!
                        oEdge.select_set(True)
    
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    
    
        
        #=== Load/create a persistent custom data layer to store the 'SplitVertID' of duplicated verts accross seams.  Unity needs these to properly move verts in some situation (like local morphing) ===
        # Iterate through the verts that will be split to store into a temp custom data layer a temporary unique ID so that split verts that must have the same normal can be 'twinned' together again so Client can average out their normals
        oLaySplitVertID = bm.verts.layers.int.new(G.C_DataLayer_SplitVertIDs)
        for oVert in bm.verts:
            if oVert.select:
                oVert[oLaySplitVertID] = oVert.index + G.C_OffsetVertIDs
                
        #=== Split the seam edges so each related polygon gets its own edge & verts.  This way each vert always has one exact UV like Client requires ===
        bpy.ops.mesh.edge_split()                           ###NOTE: Loses selection!
        
        #=== After edge split all verts we have separated can still be 'matched together' by their shared normal ID that has also been duplicated as verts were duplicated === 
        self.aaSplitVerts = {}                              # Create a 'map-of-arrays' that will store the matching vertex indices for each 'shared normals group'.  Done this way because a vert can be split more than once (e.g. at a T between three seams for example)
        for oVert in bm.verts:
            nSplitVertID = oVert[oLaySplitVertID]
            if nSplitVertID >= G.C_OffsetVertIDs:           # If this vert has a shared vert ID then insert it into our map to construct our list of shared normals
                if nSplitVertID not in self.aaSplitVerts:   # If our map entry for this group does not exist create an empty array at this map ID so next line will have an array to insert the first item of the group
                    self.aaSplitVerts[nSplitVertID] = []
                self.aaSplitVerts[nSplitVertID].append(oVert.index)    # Append the vert index to this shared normal group.
    
        #=== 'Flatten' the aaSharedNormals array by separating the groups with a 'magic number' marker.  This enables groups of irregular size to be transfered more efficiently to Client ===
        self.aMapSharedNormals = CByteArray()  # Array of unsigned shorts.   Client can only process meshes under 64K verts anyways...
        for nSharedNormalID in self.aaSplitVerts:
            aSharedNormals = self.aaSplitVerts[nSharedNormalID]
            nCountInThisSharedNormalsGroup = len(aSharedNormals)
            if nCountInThisSharedNormalsGroup > 1:  # Groups can be from size 1 (alone) to about 4 verts sharing the same normal with 2 by far the most frequent.  Don't know why we get about 10% singles tho... Grabbed by groups with 3+??
                for nVertID in aSharedNormals:
                    self.aMapSharedNormals.AddUShort(nVertID)
                self.aMapSharedNormals.AddUShort(G.C_MagicNo_EndOfFlatGroup)  # When Client sees this 'magic number' it knows it marks the end of a 'group' and updates the normals for the previous group
        self.aMapSharedNormals.CloseArray()

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.bRanConvertMeshForUnity = True
    

#     def Unity_GetMeshNormals(self):             # Store the mesh normals and return in a serializable form for Unity.         
#         #=== Store the 'good' normals so Unity can render the multi-material mesh seamlessly with the best normals available (Blender's mesh before splitting verts)
#         if self.oMeshSource is None:            # Codebase MUST have specified the source for this mesh so we can extract valid normals!
#             raise Exception("\n###EXCEPTION: CMesh.Unity_GetMeshNormals() called when self.oMeshSource was not set!")
#         aVerts_SourceMesh = self.oMeshSource.GetMeshData().vertices 
#         if self.Open():
#             oLayVertSrcBody = self.bm.verts.layers.int[G.C_DataLayer_VertSrcBody]
#             self.aNormals = CByteArray()                        # Array of vectors
#             self.bm.verts.ensure_lookup_table()
#             for oVert in self.bm.verts:
#                 nVertSrcBody = oVert[oLayVertSrcBody] - G.C_OffsetVertIDs           ###CHECK: Looks great but is it better to get the normal of the un-split source mesh?
#                 #oVertOther = self.bm.verts[nVertSrcBody]
#                 vecNormal = aVerts_SourceMesh[nVertSrcBody].normal.copy()               
#                 #self.aNormals.AddVector(oVertOther.normal)
#                 self.aNormals.AddVector(vecNormal)
#             self.aNormals.CloseArray()
#             self.Close()
#         return self.aNormals
    
    #---------------------------------------------------------------------------    
    #---------------------------------------------------------------------------    SUPER PUBLIC -> Global top-level functions exported to Client
    #---------------------------------------------------------------------------    

    def Unity_GetMesh(self):  # Called in the constructor of Unity's important CBMesh constructor to return the mesh (possibly skinned depending on mesh anme) + meta info the class needs to run.
        ###IMPROVE11: Rapidly ported... finish integration into CMesh
        print("=== Unity_GetMesh() sending mesh '{}' ===".format(self.GetName()))

        oMeshO = SelectObject(self.GetName())           ###IMPROVE11: Move all this crap to CMesh and do only once!!
        ###NOW13: VertGrp_RemoveNonBones(oMeshO, True)     # Remove the extra vertex groups that are not skinning related from the skinned cloth-part
        self.ConvertMeshForUnity(True)  # Client requires a tri-based mesh and verts that only have one UV. (e.g. no polys accross different seams/materials sharing the same vert)
    
        oMesh = oMeshO.data
        aVerts = oMesh.vertices
        nVerts = len(aVerts)
        # nEdges = len(oMesh.edges)
        nTris = len(oMesh.polygons)  # Prepare() already triangulated so all polygons are triangles
        nMats = len(oMesh.materials)
    
        #=== Send the 'header' containing a magic number, the number of verts, tris, materials ===
        oBA = CByteArray()
        oBA.AddInt(nVerts)  ###INFO!!!: Really fucking bad behavior by struct.pack where pack of 'Hi' will give 8 byte result (serialized as both 32-bit) while 'HH' will give 4 bytes (both serialzed as 16-bit)  ###WTF?????
        oBA.AddInt(nTris)
        nMats = 0                               ###WEAK ###CHECK: How come we have to test for null now?  wtf?
        for oMat in oMesh.materials:
            if oMat is not None:
                nMats += 1
        oBA.AddByte(nMats)
        
        #=== Send our collection of material.  Client will link to the image files to create default materials ===
        for oMat in oMesh.materials:
            if oMat is not None:                ###CHECK: Why can they be null now??
                oBA.AddString(oMat.name)
    
        #=== Now pass processing to our C Blender code to internally copy the vert & tris of this mesh to shared memory Client can access directly ===
        print("--- Unity_GetMesh() sharing mesh '{}' of {} verts, {} tris and {} mats with bytearray of size {} ---".format(self.GetName(), nVerts, nTris, nMats, len(oBA)))
        oMesh.tag = True                    ###IMPORTANT: Setting 'tag' on the mesh object and causes the next update to invoke our C-code modification of Blender share/unshare mesh memory to Client
        oMesh.use_fake_user = False         ###NOTE: We use this mesh flag in our modified Blender C code to indicate 'load verts from client'.  Make sure this is off in this context
        oMesh.update(True, True)            ###IMPORTANT: Our modified Blender C code traps the above flags to update its shared data structures with client...        
    
        return oBA.Unity_GetBytes()             # Return the bytearray intended for Unity deserialization. 
    
    
    def Unity_GetMesh_SkinnedInfo(self):          #=== Send skinning info to Unity's CBSkin objects  (vertex groups with names so Unity can map blender bones -> existing Client bones)
        ###IMPROVE11: Rapidly ported... finish integration into CMesh
        print("=== Unity_GetMesh_SkinnedInfo() sending mesh '{}' ===".format(self.GetName()))
    
        #=== Unity can only process 4 bones per vert max.  Ensure cleanup ===
        oMeshO = SelectObject(self.GetName())
    #     bpy.ops.object.mode_set(mode='EDIT')
    #     bpy.ops.mesh.select_all(action='SELECT')
    #     bpy.ops.object.vertex_group_limit_total(limit=4)
    #     bpy.ops.object.vertex_group_clean(group_select_mode='ALL')    # Clean up empty vert groups new Blender insists on creating during skin transfer
    #     bpy.ops.mesh.select_all(action='DESELECT')
    #     bpy.ops.object.mode_set(mode='OBJECT')
        ###DEV24:????? WTF? VertGrp_RemoveNonBones(oMeshO, True)
        
        #=== Select mesh and obtain reference to needed mesh members ===
        oMesh = oMeshO.data
        aVerts = oMesh.vertices
        nVerts = len(aVerts)
    
        #=== Construct outgoing bytearray Unity can read back ===
        oBA = CByteArray()
        oBA.AddUShort(len(oMeshO.vertex_groups))
        for oVertGrp in oMeshO.vertex_groups:
            oBA.AddString(oVertGrp.name)
            #if oVertGrp.name[0] == '+':
            #    print("- CMesh serializing dynamic bone {}".format(oVertGrp))        
     
        #=== Iterate through each vert to send skinning data.  These should have been trimmed down to four in prepare but Client will decipher and keep the best 4 nonetheless ===
        nErrorsBoneGroups = 0                               ###OPT24:!!! Can we find a way to send this in C++?     
        for nVert in range(nVerts):
            aVertGroups = aVerts[nVert].groups
            nVertGroups = len(aVertGroups)
            oBA.AddByte(nVertGroups)
            for oVertGroup in aVertGroups:
                nGrp = oVertGroup.group
                oBA.AddUShort(oVertGroup.group)
                oBA.AddFloat (oVertGroup.weight)
#                 G.DumpStr("\n***ERROR: Bones at vert {} with vertgroup {} and weight {}\n".format(nVert, nGrp, oVertGroup.weight))
#                 oBA.AddUShort(0)  ###CHECK: What to do???
#                 oBA.AddFloat(0)
#                 nErrorsBoneGroups = nErrorsBoneGroups + 1
#                 DELIBERATE_CRASH()
#                 else:  
        oBA.AddInt(nErrorsBoneGroups)
    
        return oBA.Unity_GetBytes()          # Return the bytearray intended for Unity deserialization. 

        
from enum import Enum #, auto ###IMPROVE: auto() not working??
class EMeshMode(Enum):          ###INFO: Based on technique at https://docs.python.org/3/library/enum.html
    Closed      = 0 #auto()        # CMesh is currently closed.  (BMesh not accessible)
    Edit        = 1 #auto()        # CMesh is open in the (default) edit mode.  (BMesh was created from edit-mode data)
    Object      = 2 #auto()        # CMesh is open in the (unusual) object mode.  (BMesh was created directly from object data, and underlying mesh is not being edited)








    
###DESIGN: SlaveMesh functionality needs: ###OBS??
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




#         if (self.oMeshParent != None):         ###DESIGN ###BUG Confusion with node parent and morph parent!!!
#             self.SetParent(self.oMeshParent.GetName())   ###IMPROVE: By CMesh instead of name??
    #def __del__(self):        ###DEV
        ####BROKEN!!!  Game deletes objects even if they are still reference!  e.g. self.oSkinMeshGame sometimes!!!!!!!!
        #if (self.bDeleteBlenderObjectUponDestroy):
        #    DeleteObject(self.sNameMesh.name)


#     def OpenInObjectMode(self):                      # Obtain a BMesh reference while NOT in Edit mode.  Useful in cases when another BMesh needs to be opened in edit mode (more ops allowed in edit mode)
#         ###BUG:?? OpenInObjectMode() has been observed to result in CORRUPT BMesh data!  (e.g. edges with null verts on one side!!) -> DON"T USE!!
#         if self.bm:                             ###TODO21: Propage this new call throughout codebase
#             raise Exception("###EXCEPTION: CMesh.OpenInObjectMode('{}') called while it was already open!".format(self.oMeshO.name))
#         self.bm = bmesh.new()
#         self.bm.from_mesh(self.oMeshO.data)
#         self.bOpenedInObjectMode = True
#         self.UpdateBMeshTables()
#         return self.bm

#     def ExitFromEditMode(self):     # Cleanly exit 'EDIT' mode while updating bmesh.  Doesn't affect anything else!
#         if self.bOpenedInObjectMode:
#             raise Exception("###EXCEPTION: CMesh.ExitFromEditMode('{}') called from a mesh opened in Object mode!".format(self.oMeshO.name))
# 
#         if self.oMeshO.mode != 'EDIT':      ###INFO: How to detect our mesh mode (OBJECT, EDIT, WEIGHT_PAINT, etc)
#             raise Exception("###EXCEPTION: CMesh.ExitFromEditMode('{}') called while mesh was in mode '{}'!".format(self.oMeshO.name, self.oMeshO.mode))
# 
#         bpy.types.Mesh.calc_tessface()          ###CHECK:!!!!
#         bmesh.update_edit_mesh(self.oMeshO.data)        ###DEV24:!!!!!!  destructive (boolean) – Use when geometry has been added or removed. (https://docs.blender.org/api/blender_python_api_current/bmesh.html#bmesh.update_edit_mesh)
#         self.bm.free()
#         self.bm = None
#         MeshMode_Object(self.oMeshO)


#import SourceReloader
        ###DESIGN:??? self.UpdateBMeshTables()
            #bpy.types.Mesh.calc_tessface()         ###DESIGN:???





           #sImgFilepathEnc = "NoTexture"
            #if oMat is not None:
                #sImgFilepathEnc = oMat.name         ###TODO19: Redo whole material import procedure to require materials to be already present in Unity! (Far easier to get the right look by first depending on Unity's awesome FBX importer!!)
#                 if oMat.name.startswith("Material_"):  # Exception to normal texture-path behavior is for special materials such as 'Material_Invisible'.  Just pass in name of special material and Unity will try to fetch it.  It is assume that Blender and client both define this same material!
#                     sImgFilepathEnc = oMat.name  ###IMPROVE: Could pass in more <Unity defined Material>' names to pass special colors and materials??
#                 else:  # For non-special material we pass in texture path.
#                     oTextureSlot = oMat.texture_slots[0]
#                     if oTextureSlot:
#                         sImgFilepathEnc = oTextureSlot.texture.image.filepath
#                         # aSplitImgFilepath = oTextureSlot.texture.image.filepath.rsplit(sep='\\', maxsplit=1)    # Returns a two element list with last being the 'filename.ext' of the image and the first being the path to get there.  We only send Client filename.ext
#            oBA.AddString(sImgFilepathEnc)
 
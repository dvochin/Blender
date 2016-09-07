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

import gBlender
import SourceReloader
import G
import Client




class CMesh:
    def __init__(self, sNameMesh, oMeshO, oMeshParent = None):
        ###IMPROVE?  Won't work in CreateFromDuplicate! gBlender.DeleteObject(sNameMesh)                # Make sure this mesh does not exist already (all given names globally uniqye by design)
        self.oMeshO         = oMeshO
        self.oMeshParent    = oMeshParent          # Our immediate CMesh parent mesh.  The one we update our verts from after morphing ###NOW### Confusion between morphing parent (still used?) and node parent
        self.bDeleteUponDestroy = True             # By default we delete our Blender object when we get destroyed
        self.SetName(sNameMesh)
        self.bmLastOpen = None                      # The last-opened BMesh.
#         if (self.oMeshParent != None):         ###DESIGN ###BUG Confusion with node parent and morph parent!!!
#             self.SetParent(self.oMeshParent.GetName())   ###IMPROVE: By CMesh instead of name??
    #def __del__(self):        ###DEV
        ####BROKEN!!!  Game deletes objects even if they are still reference!  e.g. self.oMeshBody sometimes!!!!!!!!
        #if (self.bDeleteUponDestroy):
        #    gBlender.DeleteObject(self.oMeshO.name)

    @classmethod
    def CreateFromDuplicate(cls, sNameMesh, oMeshSrc):
        "Create mesh by duplicating oMeshSrc"
        oMesh = gBlender.DuplicateAsSingleton(oMeshSrc.GetName(), sNameMesh, oMeshSrc.oMeshO.parent.name, False)
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
        gBlender.SelectAndActivate(self.oMeshO.name)         ###DEV: Best way by name??        ###IMPROVE: Remember hidden flag??
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
        gBlender.Util_UnselectMesh(self.oMeshO)
        

    def UpdateBMeshTables(self):
        if (self.bmLastOpen != None):
            self.bmLastOpen.verts.index_update()             ###IMPROVE: Also do edges and faces?
            self.bmLastOpen.edges.index_update()
            self.bmLastOpen.faces.index_update()
            self.bmLastOpen.verts.ensure_lookup_table()
            self.bmLastOpen.edges.ensure_lookup_table()
            self.bmLastOpen.faces.ensure_lookup_table()
    
    def Hide(self):
        gBlender.Util_HideMesh(self.oMeshO)         ###TODO: Merge all that stuff in gBlender into CMesh!

    def SetName(self, sNameMesh):
        self.oMeshO.name = self.oMeshO.data.name = sNameMesh       ###LEARN: We *must* apply name twice to make sure we get this name (Would get something like 'MyName.001' if 'MyName' was already defined
        self.oMeshO.name = self.oMeshO.data.name = sNameMesh

    def GetName(self):
        return self.oMeshO.name 

    def SetParent(self, sNameParent):           
        gBlender.SetParent(self.oMeshO.name, sNameParent)       ###MOVE: Merge in here?

    def Destroy(self):
        gBlender.DeleteObject(self.GetName())       ###CHECK
        self.oMeshO = None
        
#    def GetMeshFromUnity(self):     ###DEV???
#        return self.oMeshO
        
        
        
        
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

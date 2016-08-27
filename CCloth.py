import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

import gBlender
import G
import CBody
import CMesh
import Client
import Curve
import Cut

class CCloth:
    def __init__(self, oBody, sNameCloth, sClothType, sNameClothSrc, sVertGrp_ClothSkinArea):
        "Separate cloth mesh between skinned and simulated parts, calculating the 'twin verts' that will pin the simulated part to the skinned part at runtime."
        ####IMPROVE ####DESIGN: Possible to 'group' sVertGrp_ClothSkinArea & sClothType together??
        
        print("=== CCloth.ctor()  oBody = '{}'  sNameCloth = '{}'  sClothType = '{}'  sNameClothSrc = '{}'  sVertGrp_ClothSkinArea = '{}'  ===".format(oBody.sMeshPrefix, sNameCloth, sClothType, sNameClothSrc, sVertGrp_ClothSkinArea))

        self.oBody                  = oBody             # The back-reference to the owning body.
        self.sNameCloth             = sNameCloth;       # The human-readable name of this cloth.  Is whatever Unity wants to set it.  Acts as key in owning CBody.aCloths[]
        self.sClothType             = sClothType        # Is one of { 'Shirt', 'Underwear', etc } and determines the cloth collider mesh source.  Must match previously-defined meshes created for each body!   ###IMPROVE: Define all choices
        self.sNameClothSrc          = sNameClothSrc     # The Blender name of the mesh we cut from.  (e.g. 'Bodysuit')
        self.sVertGrp_ClothSkinArea = sVertGrp_ClothSkinArea    # The name in self.oBody of the vertex group detailing the area where cloth verts are skinned instead of cloth-simulated

        self.oMeshClothSource       = None              # The source cloth mesh.  Kept untouched.
        self.oMeshClothCut          = None              # The source cloth mesh cut from user-supplied cutter curves.  Re-created everytime a cutter curve point moves
        self.oMeshClothSimulated    = None              # The simulated part of the runtime cloth mesh.  Simulated by Flex at runtime.
        self.oMeshClothSkinned      = None              # The skinned part of the runtime cloth mesh.  Skinned at runtime just like its owning skinned body.  (Also responsible to pins simulated mesh)
        ##self.oMeshBodyColCloth      = None              # The 'SlaveMesh' created at design time for this 'sClothType' to repell this cloth from its owning body at runtime.  Simple skinned mesh 
        
        #self.aTwinIdToVertSim = {}                      # Setup two maps (that will have the same size) to store for both simulated and skinned cloth parts what 'TwinVertID' maps to simVert / skinVert           
        #self.aTwinIdToVertSkin = {}                     # Each of these will go from 1..<NumVertIDs> and be used to determine mapping
        #self.aMapClothVertsSimToSkin = array.array('H') # The final flattened map of what verts from the 'simulated cloth verts' to 'skinned cloth vert'.  Unity needs this to pin the edges of the simulated part of the cloth to the skinned part
        self.aMapPinnedFlexParticles = array.array('H') # The final flattened map of what verts from the 'skinned cloth vert' map to which verts in the (untouched) Flex-simulated mesh.  Flex needs this to create extra springs to keep the skinned part close to where it should be on the body!

        self.aCurves = []                               # Array of CCurve objects responsible to cut this cloth as per user directions

        bpy.context.scene.cursor_location = Vector((0,0,0))     # All dependant code requires cursor to be at origin!

        #=== Obtain reference to the needed source mesh ===
        self.oMeshClothSource       = CMesh.CMesh.CreateFromExistingObject(self.sNameClothSrc)       ###DEV: Unique names?

        #=== Register cutting curves from the Blender-stored recipe for this cloth type ===
        oCurveRootO = bpy.data.objects[self.sClothType]         # Our collection of cutter curve definition points is the same as our cloth type (e.g. 'Top', 'Underwear', etc)
        for oCurveO in oCurveRootO.children:
            sNameCurve = oCurveO.name
            self.aCurves.append(Curve.CCurve(self, sNameCurve))

        #=== Delete previous iteration if it exists ===
        sNameClothCut       = self.oBody.sMeshPrefix + self.sNameCloth + "-Cut"
        gBlender.DeleteObject(sNameClothCut)
        

        
    def UpdateCutterCurves(self):
        #===== Iterate through our cutter curves to ask them to update themselves from the (just moved) recipe points =====
        for oCurve in self.aCurves:
            oCurve.UpdateCutterCurve()
        return "OK"


            
    def CutClothWithCutterCurves(self):
        #===== Cut the source cloth (e.g. bodysuit) and remove the extra fabric the user didn't want with the 'cutter curves' =====
        sNameClothCut       = self.oBody.sMeshPrefix + self.sNameCloth + "-Cut"
        self.oMeshClothCut  = CMesh.CMesh.CreateFromDuplicate(sNameClothCut, self.oMeshClothSource)
        for oCurve in self.aCurves:
            bInvertCut = oCurve.sType.find("Top") != -1         ###DEVF ###HACK!!!!  ###IMPROVE: Auto determination of cut possible?  Have to have designer pass in? 
            oCurve.CutClothWithCutterCurve(bInvertCut)
        return "OK"

        
    def PrepareClothForGame(self):
        #===== Prepare the cloth for gaming runtime by separating cut-cloth into skinned and simulated areas =====       
        sNameClothSimulated = self.oBody.sMeshPrefix + self.sNameCloth + "-Simulated"
        sNameClothSkinned   = self.oBody.sMeshPrefix + self.sNameCloth + "-Skinned"
        ###DEVF!!!!!!!!! self.oMeshClothSimulated = CMesh.CMesh.CreateFromDuplicate(sNameClothSimulated, self.oMeshClothCut)     # Simulated mesh is sent to Unity untouched.
        self.oMeshClothSimulated = CMesh.CMesh.CreateFromDuplicate(sNameClothSimulated, self.oMeshClothSource)     # Simulated mesh is sent to Unity untouched.
        self.oMeshClothSimulated.SetParent(G.C_NodeFolder_Game)
    
        #=== Transfer the skinning information from the skinned body mesh to the clothing.  _ClothSkinArea_xxx vert groups are to define various areas of the cloth that are skinned and not simulated ===
        self.oBody.oMeshMorph.oMeshO.hide = False         ###LEARN: Mesh MUST be visible for weights to transfer!
        gBlender.Util_TransferWeights(self.oMeshClothSimulated.oMeshO, self.oBody.oMeshMorph.oMeshO)      ###IMPROVE: Insert apply statement in this function?
    
        #=== With the body's skinning info transfered to the cloth, select the the requested vertices contained in the 'skinned verts' vertex group.  These will 'pin' the cloth on the body while the other verts are simulated ===
        bmClothSim = self.oMeshClothSimulated.Open()
        nVertGrpIndex_Pin = self.oMeshClothSimulated.oMeshO.vertex_groups.find(self.sVertGrp_ClothSkinArea)       
        if nVertGrpIndex_Pin == -1:
            raise Exception("ERROR: CCloth.PrepareClothForGame() could not find in skinned body pin vertex group " + self.sVertGrp_ClothSkinArea)
        oVertGroup_Pin = self.oMeshClothSimulated.oMeshO.vertex_groups[nVertGrpIndex_Pin]
        self.oMeshClothSimulated.oMeshO.vertex_groups.active_index = oVertGroup_Pin.index
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()                # To-be-skinned cloth verts are now selected
    
        #=== Prepare the to-be-split cloth mesh for 'twin vert' mapping: This vert-to-vert map between the skinned part of cloth mesh to simulated-part of cloth mesh is needed by Unity at runtime to 'pin' the edges of the simulated mesh to 'follow' the skinned part 
        oLayVertOrigID = bmClothSim.verts.layers.int.new(G.C_PropArray_ClothSkinToSim)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
    
        #=== Iterate over the to-be-skinned verts to store their vert ID.  When we copy to the skinned mesh and delete the non-skinned area we'll be able to create map between the two meshes ===
        for oVert in bmClothSim.verts:
            if (oVert.select) :
                oVert[oLayVertOrigID] = oVert.index  # Mark the vert layer by its own index so we can retrieve it once verts are perturbed during removal
                #print("- VertID {:4d} at {:}".format(oVert.index, oVert.co))
            else:
                oVert[oLayVertOrigID] = -1
        self.oMeshClothSimulated.Close()

        #=== Create the skinned mesh as a copy of the simulated one (note the twin vert IDs are still present) ===
        self.oMeshClothSkinned = CMesh.CMesh.CreateFromDuplicate(sNameClothSkinned, self.oMeshClothSimulated)     # Skinned mesh is sent to Unity with only skinned part
        self.oMeshClothSkinned.SetParent(G.C_NodeFolder_Game)
            
        #=== Delete the verts in the skinned mesh that are not to be skinned ===
        bmClothSkin = self.oMeshClothSkinned.Open()
        oLayVertOrigID = bmClothSkin.verts.layers.int[G.C_PropArray_ClothSkinToSim]
        for oVert in bmClothSkin.verts:
            if (oVert[oLayVertOrigID] == -1):
                oVert.select_set(True)
        bpy.ops.mesh.delete(type='VERT')

        #=== Create the map between the skinned verts to their equivalent verts in the simulated mesh === 
        for oVert in bmClothSkin.verts:
            self.aMapPinnedFlexParticles.append(oVert.index)
            self.aMapPinnedFlexParticles.append(oVert[oLayVertOrigID])
            #print("- NewVertID {:4d} was {:4d} at {:}".format(oVert.index, oVert[oLayVertOrigID], oVert.co))
        
        #=== Post-process the skinned-part to be ready for Unity ===
        gBlender.Cleanup_VertGrp_RemoveNonBones(self.oMeshClothSkinned.oMeshO, True)     # Remove the extra vertex groups that are not skinning related from the skinned cloth-part
        Client.Client_ConvertMesh(self.oMeshClothSkinned.oMeshO, False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
        self.oMeshClothSkinned.Close()
        
        #=== Post-process the simulated-part to be ready for Unity ===
        Client.Client_ConvertMesh(self.oMeshClothSimulated.oMeshO, False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
        bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from simulated mesh to save memory

        return "OK"
        


        
#     def PrepareClothForGame(self):        ###OBS: Version for separated skinned / simulated clothing mesh tied up at the rim.  (Before Flex skinned-to-slave particles)
#         #===== Prepare the cloth for gaming runtime by separating cut-cloth into skinned and simulated areas =====       
#         sNameClothSimulated = self.oBody.sMeshPrefix + self.sNameCloth + "-Simulated"
#         sNameClothSkinned   = self.oBody.sMeshPrefix + self.sNameCloth + "-Skinned"
# 
#         #=== Duplicate the simulated copy of the mesh (to be modified) ===
#         self.oMeshClothSimulated    = CMesh.CMesh.CreateFromDuplicate(sNameClothSimulated, self.oMeshClothCut)
#         self.oMeshClothSimulated.SetParent(G.C_NodeFolder_Game)
#     
#         #=== Transfer the skinning information from the skinned body mesh to the clothing.  Some vert groups are useful to move non-simulated area of cloth as skinned cloth, other _ClothSkinArea_xxx vert groups are to define areas of the cloth that are skinned and not simulated ===
#         self.oBody.oMeshMorph.oMeshO.hide = False         ###LEARN: Mesh MUST be visible for weights to transfer!
#         gBlender.Util_TransferWeights(self.oMeshClothSimulated.oMeshO, self.oBody.oMeshMorph.oMeshO)
#         gBlender.Cleanup_VertGrp_RemoveNonBones(self.oBody.oMeshMorph.oMeshO, True)
#     
#         #=== With the body's skinning info transfered to the cloth, select the the requested vertices contained in the 'skinned verts' vertex group.  These will 'pin' the cloth on the body while the other verts are simulated ===
#         bmClothSim = self.oMeshClothSimulated.Open()
#         nVertGrpIndex_Pin = self.oMeshClothSimulated.oMeshO.vertex_groups.find(self.sVertGrp_ClothSkinArea)       
#         if nVertGrpIndex_Pin == -1:
#             raise Exception("ERROR: CCloth.PrepareClothForGame() could not find in skinned body pin vertex group " + self.sVertGrp_ClothSkinArea)
#         oVertGroup_Pin = self.oMeshClothSimulated.oMeshO.vertex_groups[nVertGrpIndex_Pin]
#         self.oMeshClothSimulated.oMeshO.vertex_groups.active_index = oVertGroup_Pin.index
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.object.vertex_group_select()                # To-be-skinned cloth verts are now selected
#     
#         #=== Prepare the to-be-split cloth mesh for 'twin vert' mapping: This vert-to-vert map between the skinned part of cloth mesh to simulated-part of cloth mesh is needed by Unity at runtime to 'pin' the edges of the simulated mesh to 'follow' the skinned part 
#         oLayVertOrigID = bmClothSim.verts.layers.int.new(G.C_PropArray_ClothSkinToSim)  # Create a temp custom data layer to store IDs of split verts so we can find twins easily.    ###LEARN: This call causes BMesh references to be lost, so do right after getting bmesh reference
#         aFacesToSplit = [oFace for oFace in bmClothSim.faces if oFace.select]           # Obtain array of all faces to separate so we can select them once edge loop is found
#     
#         #=== Determine the edges separating the skinned cloth mesh from the simulated one (removing edge-of-cloth edges) ===
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#         bpy.ops.mesh.region_to_loop()       # This will select only the edges at the boundary of the cutout polys... including edge of cloth, seams and the (needed) edges that connect split mesh to main mesh
#         for oEdge in bmClothSim.edges:      # Iterate over the edges at the boundary to remove any edge that is 'on the edge' -> This leaves selected only edges that have one polygon in the main mesh and one polygon in the mesh-to-be-cut
#             if oEdge.select == True:
#                 if oEdge.is_manifold == False:  # Deselect the edges-on-edge (i.e. natural edge of cloth)
#                     oEdge.select_set(False)
#     
#     
#         #=== Iterate over the split verts at the boundary loop to store a uniquely-generated 'twin vert ID' into the custom data layer so we can re-twin the split verts from different meshes after the mesh separate ===
#         nNextVertTwinID = 1  
#         aVertsBoundary = [oVert for oVert in bmClothSim.verts if oVert.select]              # Create a collection for all the verts on the boundary loop
#         for oVert in aVertsBoundary:
#             oVert[oLayVertOrigID] = nNextVertTwinID  # These are unique to the whole skinned body so all detached chunk can always find their corresponding skinned body vert for per-frame positioning
#             #print("TwinID {:3d} = VertSim {:5d} at {:}".format(nNextVertTwinID, oVert.index, oVert.co))
#             nNextVertTwinID += 1
#             
#         #=== Reselect the to-be-skinned faces again   ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
#         bChunkMeshHasGeometry = False   # Determine if chunk mesh has any faces
#         for oFace in aFacesToSplit:
#             oFace.select_set(True)
#             bChunkMeshHasGeometry = True
#     
#         #=== If chunk mesh has no geometry then we don't generate it as client has nothing to render / process for this chunk ===
#         if bChunkMeshHasGeometry == False:
#             print("\n>>> CCloth.ctor() skips the creation of cloth '{}' from body '{}' because it has no geometry to simulate <<<".format(self.sNameCloth, self.oBody.sMeshPrefix))
#             return "ERROR"      ####DESIGN: A fatal failure??
#     
#         #=== Split and separate the skinned-part of the cloth from the simulated mesh (twin-vert IDs layer info will be copied to new mesh) ===
#         bpy.ops.mesh.split()        # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
#         bpy.ops.mesh.separate()     # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'chunk'
#         self.oMeshClothSimulated.Close()
#     
#         #=== Post-process the just-detached chunk to calculate the 'twin verts' array between the skinned-part of cloth to simulated-part of cloth ===
#         bpy.context.object.select = False               # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#         bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
#         oMeshClothSkinnedO = bpy.context.object 
#         oMeshClothSkinnedO.name = oMeshClothSkinnedO.data.name = sNameClothSkinned  ###NOTE: Do twice so name sticks!
#         oMeshClothSkinnedO.name = oMeshClothSkinnedO.data.name = sNameClothSkinned
#         self.oMeshClothSkinned = CMesh.CMesh.CreateFromExistingObject(sNameClothSkinned)
#             
#         #=== Post-process the skinned-part to be ready for Unity ===
#         gBlender.Cleanup_VertGrp_RemoveNonBones(self.oMeshClothSkinned.oMeshO, True)     # Remove the extra vertex groups that are not skinning related from the skinned cloth-part
#         Client.Client_ConvertMesh(self.oMeshClothSkinned.oMeshO, False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
#         ####DEV: Done here??                   
#     
#         #=== Post-process the simulated-part to be ready for Unity ===
#         Client.Client_ConvertMesh(self.oMeshClothSimulated.oMeshO, False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
#         bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from detached chunk to save memory
#     
#     
#     
#         #===== ASSEMBLE THE TWIN VERT MAPPING =====
#         #=== Iterate over the boundary verts of the simulated mesh to find their vertex IDs ===
#         bmMeshClothSim = self.oMeshClothSimulated.Open()
#         oLayVertOrigID = bmMeshClothSim.verts.layers.int[G.C_PropArray_ClothSkinToSim]
#         for oVert in bmMeshClothSim.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
#             nTwinID = oVert[oLayVertOrigID]
#             if nTwinID != 0:
#                 self.aTwinIdToVertSim[nTwinID] = oVert.index             # Remember what skin vert this TwinID maps to
#                 #print("TwinID {:3d} = VertSim {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
#         self.oMeshClothSimulated.Close()
#         
#         #=== Iterate through the boundary verts of the skinned part of the clto to access the freshly-created custom data layer to obtain ID information that enables us to match the skinned mesh vertices to the simulated cloth mesh for pinning ===
#         bmMeshClothSkinned = self.oMeshClothSkinned.Open()
#         oLayVertOrigID = bmMeshClothSkinned.verts.layers.int[G.C_PropArray_ClothSkinToSim]
#         for oVert in bmMeshClothSkinned.verts:  ###LEARN: Interestingly, both the set and retrieve list their verts in the same order... with different topology!
#             nTwinID = oVert[oLayVertOrigID]
#             if nTwinID != 0:
#                 self.aTwinIdToVertSkin[nTwinID] = oVert.index             # Remember what skin vert this TwinID maps to
#                 #print("TwinID {:3d} = VertSkin {:5d} at {:}".format(nTwinID, oVert.index, oVert.co))
#         self.oMeshClothSkinned.Close()
#         
#         #=== Assembled the serializable flat array of twin verts Unity needs to pin simulated cloth to skinned cloth part ===
#         for nTwinID in range(1, nNextVertTwinID):
#             self.aMapClothVertsSimToSkin.append(self.aTwinIdToVertSim [nTwinID])
#             self.aMapClothVertsSimToSkin.append(self.aTwinIdToVertSkin[nTwinID])
#             #print("nTwinID {:3d} = VertSim {:4d} = VertSkin {:4d}".format(nTwinID, self.aTwinIdToVertSim[nTwinID], self.aTwinIdToVertSkin[nTwinID]))
# 
# 
#         #===== BODY CLOTH COLLIDER PROCESSING =====
#         #=== Obtain cloth body col mesh to service upcoming Unity requests ===
#         ###DEVF sNameMesh = self.oBody.sMeshSource + "-BodyColCloth-" + self.sClothType + "-Slave"   ###WEAK: Extreme dependency on object naming! 
#         ###DEVF self.oMeshBodyColCloth = CMesh.CMesh.CreateFromExistingObject(sNameMesh)
#         return "OK"



#     def SerializeCollection_aMapClothVertsSimToSkin(self):
#         return gBlender.Stream_SerializeCollection(self.aMapClothVertsSimToSkin)

    def SerializeCollection_aMapPinnedFlexParticles(self):
        return gBlender.Stream_SerializeCollection(self.aMapPinnedFlexParticles)

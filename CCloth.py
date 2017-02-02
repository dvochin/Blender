##DISCUSSION: Cloth revival for new CBodyBase
#=== DESIGN ===
# Rebase approach on UVs of bodysuit
    # Enables clothing recipes to survive morphing bodysuits
    # Makes cutting curves far more accurate
    # Difficulty traversing UV seams however... (for now we can simplify this away be requireing a data point to be on each seam) 
#=== STEPS ===
# Curve source points and bezier handles are entered on a 1-unit square area (equivalent to UV space)
    # Points based on seams are 1 dimentional and start with seam beginning and end at seam end.
    # Points not based on seams are 2D x,y
# Curve is created from source points and bezier handles.
# Curve is 'rasterized' into a few dozen X,Y points in our 1-unit square area.
# Each rasterized point finds the three closest UV points for triangulation below.
# Each of our 'rasterized point' is converted from UV domain to 3D domain via call to mathutils.geometry.barycentric_transform()
    # UV seam traversal is somewhat tricky (to be determined)
# Once the full 3D curve is finalized we invoke either or previous-implementaiton cutter or a new one based on 'vert adjustment' along edges?


#=== IDEAS ===
# KDtree allow rapid search!  Use!! https://www.blender.org/api/blender_python_api_2_73_release/mathutils.kdtree.html

#- Node approach a nightmare?
#- Rebase whole things on Excel-like equations with hierarchy... with data points from marked verts!





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
import CBody
import CMesh
import Client
import Curve
import Cut
import CObject

class CCloth:
    def __init__(self, oBodyBase, sNameCloth, sClothType, sNameClothSrc, sVertGrp_ClothSkinArea):
        "Separate cloth mesh between skinned and simulated parts, calculating the 'twin verts' that will pin the simulated part to the skinned part at runtime."
        ####IMPROVE ####DESIGN: Possible to 'group' sVertGrp_ClothSkinArea & sClothType together??
        
        print("=== CCloth.ctor()  oBodyBase = '{}'  sNameCloth = '{}'  sClothType = '{}'  sNameClothSrc = '{}'  sVertGrp_ClothSkinArea = '{}'  ===".format(oBodyBase.sMeshPrefix, sNameCloth, sClothType, sNameClothSrc, sVertGrp_ClothSkinArea))

        self.oBodyBase              = oBodyBase         # The back-reference to the owning bodybase that owns / manages this instance
        self.sNameCloth             = sNameCloth        # The human-readable name of this cloth.  Is whatever Unity wants to set it.  Acts as key in owning CBody.aCloths[]
        self.sClothType             = sClothType        # Is one of { 'Shirt', 'Underwear', etc } and determines the cloth collider mesh source.  Must match previously-defined meshes created for each body!   ###IMPROVE: Define all choices
        self.sNameClothSrc          = sNameClothSrc     # The Blender name of the mesh we cut from.  (e.g. 'Bodysuit')
        self.sVertGrp_ClothSkinArea = sVertGrp_ClothSkinArea    # The name in self.oBodyBase of the vertex group detailing the area where cloth verts are skinned instead of cloth-simulated

        ###TODO<17>: Merge these vars with new UV code
        
        self.aMapPinnedParticles = CByteArray()         # The final flattened map of what verts from the 'skinned cloth vert' map to which verts in the (untouched) Flex-simulated mesh.  Flex needs this to create extra springs to keep the skinned part close to where it should be on the body!

        self.aCurves = []                               # Array of CCurve objects responsible to cut this cloth as per user directions
        #--- UV-domain related ---
        self.oMeshO_3DS = None          # The untouched source 3D cloth mesh ###TODO<17>?
        self.oMeshO_UVF = None          # The untouched front source cloth mesh with UVs becoming vertex coordinates
        self.oMeshO_UVB = None          # The untouched back  source cloth mesh with UVs becoming vertex coordinates
        self.oMeshO_3DD = None          # The to-be-modified flattened UV cloth mesh suitable for boolean cuts

        self.oMesh_3DD  = None          # The source cut cloth mesh and source of simulated & skinned runtime cloth.  Kept untouched 
        self.oMeshClothCut          = None              # The source cloth mesh cut from user-supplied cutter curves.  Re-created everytime a cutter curve point moves
        self.oMeshClothSimulated    = None              # The simulated part of the runtime cloth mesh.  Simulated by Flex at runtime.
        self.oMeshClothSkinned      = None              # The skinned part of the runtime cloth mesh.  Skinned at runtime just like its owning skinned body.  (Also responsible to pins simulated mesh)

        #--- Unity-public properties ===
        self.oObj = CObject.CObject("Cloth Global Parameters")
        self.oPropNeckStrapThickness     = self.oObj.PropAdd("NeckStrapThickness",    "", 0.01, 0.001, 0.1) ###TODO<17>


        #===== CONVERSION TO FLATTENED UV MESH PRIOR TO BOOLEAN CUTS =====
        ###IMPROVE<17>: Do once at game ship-time?
        self.oMeshO_3DS = bpy.data.objects[self.sNameClothSrc]       # The untouched source 3D cloth mesh ###TODO<17>?
    
        #=== Open bmesh of reference mesh ===
        bm3DS = bmesh.new()                                 ###LEARN: Can't access UV data if we open in edit mode! (Have to open bmesh using from_mesh())
        bm3DS.from_mesh(self.oMeshO_3DS.data)
        aLayer3DSUV = self.oMeshO_3DS.data.uv_layers.active.data        ###LEARN: How to access UV data
        
        #=== Construct a KDTree from source 3D mesh (so we can spacially find verts quickly during UV -> 3D conversion)         
        self.oTreeKD = kdtree.KDTree(len(self.oMeshO_3DS.data.polygons))                       ###LEARN: How to quickly locate spacial data!
        for oPoly in self.oMeshO_3DS.data.polygons:
            aUV = [aLayer3DSUV[nLoopIndex].uv for nLoopIndex in oPoly.loop_indices]     ###LEARN: How to easily traverse array indirection
            vecFaceCenterUV = Vector((0,0,0))
            for oUV in aUV:
                vecFaceCenterUV.x += oUV.x
                vecFaceCenterUV.y += oUV.y
            vecFaceCenterUV /= len(aUV)
            self.oTreeKD.insert(vecFaceCenterUV, oPoly.index)
        self.oTreeKD.balance()
        
        #=== Create two UV-domain mesh (front UV and back UV) so we can cut with a flattened mesh that doesn't move with user morphs ===
        oMesh_UVF = bpy.data.meshes.new("CMeshUV-UVF")
        oMesh_UVB = bpy.data.meshes.new("CMeshUV-UVB")
        self.oMeshO_UVF = bpy.data.objects.new(oMesh_UVF.name, oMesh_UVF)
        self.oMeshO_UVB = bpy.data.objects.new(oMesh_UVB.name, oMesh_UVB)
        bpy.context.scene.objects.link(self.oMeshO_UVF)
        bpy.context.scene.objects.link(self.oMeshO_UVB)
        SetParent(self.oMeshO_UVF.name, G.C_NodeFolder_Game)        ###IMPROVE<17>: body node, cloth?
        SetParent(self.oMeshO_UVB.name, G.C_NodeFolder_Game)

        #=== Create new layer in new UV mesh so we can store back reference to the reference 3D vert (will be needed by UV -> 3D conversion) ===
        bmUVF = bmesh.new()
        bmUVB = bmesh.new()
        bmUVF.from_mesh(oMesh_UVF)
        bmUVB.from_mesh(oMesh_UVB)
        oLayVertUVF = bmUVF.verts.layers.int.new(G.C_DataLayer_VertsSrc)
        oLayVertUVB = bmUVB.verts.layers.int.new(G.C_DataLayer_VertsSrc)

        #=== Create verts where unique UVs exist.  This will traverse the fact that verts between textures have different UVs === 
        aMapUV2VertNewF = {}                # Temporary unique UVs back to new vert index (temporarily needed in 3D -> UV process)
        aMapUV2VertNewB = {}
        for oFace in bm3DS.faces:
            for oLoop in oFace.loops:
                oUV = aLayer3DSUV[oLoop.index]
                vecUV = oUV.uv.freeze()                 ###LEARN: We must 'freeze' a vector before it can be inserted into a collection (its hash function needs non-mutable value)
                if vecUV not in aMapUV2VertNewF:
                    if vecUV.x < 1:
                        vecUV3D = Vector((vecUV.x, vecUV.y, 0))
                        aMapUV2VertNewF[vecUV] = len(bmUVF.verts)    # We're adding a new vert at this unique UV coordinate, so the vert ID is the number of verts already inseted in the mesh (by this loop)
                        oVertNewF = bmUVF.verts.new(vecUV3D)
                        oVertNewF[oLayVertUVF] = oLoop.vert.index + G.C_OffsetVertIDs      # Store back-reference to the reference vert so we can reconstruct the 3D mesh from the flat UV one. (add offset so default 0 means new vert)
                    else:
                        vecUV3D = Vector((vecUV.x - 1, vecUV.y, 0))     ###NOTE: Note the -1 on x so back cloth is coincident with front in UV domain ###DESIGN<17>: Keep??
                        aMapUV2VertNewB[vecUV] = len(bmUVB.verts)    # We're adding a new vert at this unique UV coordinate, so the vert ID is the number of verts already inseted in the mesh (by this loop)
                        oVertNewB = bmUVB.verts.new(vecUV3D)
                        oVertNewB[oLayVertUVB] = oLoop.vert.index + G.C_OffsetVertIDs      # Store back-reference to the reference vert so we can reconstruct the 3D mesh from the flat UV one. (add offset so default 0 means new vert)                     
                    
        bmUVF.verts.ensure_lookup_table()              ###LEARN: Added verts, need to run ensure_lookup_table() before we can access bmesh.verts collection
        bmUVB.verts.ensure_lookup_table()
        
        #=== Re-iterate through faces again to create faces in UV-domain mesh ===
        for oFace in bm3DS.faces:
            aVertsNewFaceUV = []
            for oLoop in oFace.loops:
                oUV = aLayer3DSUV[oLoop.index]
                vecUV = oUV.uv.freeze()                 ###LEARN: We must 'freeze' a vector before it can be inserted into a collection (its hash function needs non-mutable value)
                if (vecUV.x < 1):
                    nVertUVF = aMapUV2VertNewF[vecUV]
                    aVertsNewFaceUV.append(bmUVF.verts[nVertUVF])
                else:
                    nVertUVB = aMapUV2VertNewB[vecUV]
                    aVertsNewFaceUV.append(bmUVB.verts[nVertUVB])
            if (vecUV.x < 1):
                bmUVF.faces.new(aVertsNewFaceUV)
            else:
                bmUVB.faces.new(aVertsNewFaceUV)
        
        bmUVF.to_mesh(oMesh_UVF)
        bmUVB.to_mesh(oMesh_UVB)


        #===== DEV ###MOVE =====
        self.aCurves.append(Curve.CCurveNeck(self, "Neck"))
        self.aCurves.append(Curve.CCurveSide(self, "Side"))
        self.aCurves.append(Curve.CCurveTorsoSplit(self, "TorsoSplit"))

        
    def DoDestroy(self):
        ###TODO<17>
        self.oMeshClothCut.DoDestroy()
        self.oMeshClothSimulated.DoDestroy()
        self.oMeshClothSkinned.DoDestroy()

        
    def UpdateCutterCurves(self):
        #===== Iterate through our cutter curves to ask them to update themselves from the (just moved) recipe points =====
        ###OBS<17>? 
        for oCurve in self.aCurves:
            oCurve.UpdateCutterCurve()
        return "OK"


            
    def CutClothWithCutterCurves(self):
        #===== Cut the source cloth (e.g. bodysuit) and remove the extra fabric the user didn't want with the 'cutter curves' =====
        ###DESIGN<17>: Use CMesh?
        self.oMeshO_UVF_Cut = DuplicateAsSingleton(self.oMeshO_UVF.name, self.oMeshO_UVF.name + "-Cut", G.C_NodeFolder_Game, True)
        self.oMeshO_UVB_Cut = DuplicateAsSingleton(self.oMeshO_UVB.name, self.oMeshO_UVB.name + "-Cut", G.C_NodeFolder_Game, True)
        bmCloth3DS = bmesh.new()
        bmCloth3DS.from_mesh(self.oMeshO_3DS.data)
        for oCurve in self.aCurves:
            oCurve.UpdateCurvePoints(bmCloth3DS)
        self.ConvertBackTo3D()
        return "OK"



    def ConvertBackTo3D(self):      # Convert the UV-domain front and back mesh that was cut via Boolean modifiers back to its original 3D form for in-game rendering ===
        #=== Join the two flat UV meshes into one ===
        SelectAndActivate(self.oMeshO_UVB_Cut.name)         # First select and activate mesh that will be destroyed (temp mesh)    (Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh))
        bpy.ops.transform.translate(value=(1, 0, 0))        # Push the back UV mesh by X+1 to undo the X-1 done during ctor
        self.oMeshO_UVF_Cut.hide = False
        self.oMeshO_UVF_Cut.select = True                         # Now select...
        bpy.context.scene.objects.active = self.oMeshO_UVF_Cut    #... and activate mesh that will be kept (merged into)  (Note that to-be-destroyed mesh still selected!)
        bpy.ops.object.join()                                           #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###LEARN: Existing custom data layer in merged mesh destroyed!!
        self.oMeshO_UVB_Cut = None                               # Above join destroyed the copy mesh so set our variable to None

        #=== Obtain reference to bmeshes for the meshes we need programmatic access to ===
        bmUVF = bmesh.new()     ###IMPROVE<17>: Move to part of CMesh?
        bm3DS = bmesh.new()
        bm3DD = bmesh.new()
        bmUVF.from_mesh(self.oMeshO_UVF_Cut.data)
        bm3DS.from_mesh(self.oMeshO_3DS.data)

        #=== Create new 3D-domain mesh so we can cut with a flattened mesh that doesn't move with user morphs ===
        oMesh3DDD = bpy.data.meshes.new("CMeshUV-3DD")          ###TODO<16>
        self.oMeshO_3DD = bpy.data.objects.new(oMesh3DDD.name, oMesh3DDD)
        bpy.context.scene.objects.link(self.oMeshO_3DD)
        SetParent(self.oMeshO_3DD.name, G.C_NodeFolder_Game)
        self.oMeshO_3DD.location = self.oMeshO_3DS.location       # Set (new mesh) location to same as source 3D mesh.  
        bpy.ops.mesh.uv_texture_add()               # Add the UV layer to new 3D mesh.
        bm3DD.from_mesh(self.oMeshO_3DD.data)

        #=== Create the verts in the destination 3D mesh ===
        aMapVertsUV2Verts3DD = {}
        bm3DS.verts.ensure_lookup_table()
        oLayVert3DF = bmUVF.verts.layers.int[G.C_DataLayer_VertsSrc]
        for oVertUV in bmUVF.verts:
            nVert3D = oVertUV[oLayVert3DF]
            if nVert3D >= G.C_OffsetVertIDs:       # UV vert has back reference to original 3D pointer... so the same vert... just set it back to its original 3D position
                oVert3DS = bm3DS.verts[nVert3D - G.C_OffsetVertIDs]
                vecVert3D = oVert3DS.co
            else:           # Vert has no valid back reference to an original 3D vert so it was therefore created by Boolean cuts... we must interpolate its 3D position
                vecLoc, nPoly, nDist = self.oTreeKD.find(oVertUV.co)                ###LEARN: How to extract multiple arguments out
                oPoly = self.oMeshO_3DS.data.polygons[nPoly]
                aUV = [self.oMeshO_3DS.data.uv_layers.active.data[nLoopIndex].uv for nLoopIndex in oPoly.loop_indices]
                vecUV0 = Vector((aUV[0].x, aUV[0].y, 0))            # Expand 2D UV coordinate into a 3D vector with z = 0 so we can invoke barycentric_transform() below
                vecUV1 = Vector((aUV[1].x, aUV[1].y, 0))
                vecUV2 = Vector((aUV[2].x, aUV[2].y, 0))
                vecPoly0 = self.oMeshO_3DS.data.vertices[oPoly.vertices[0]].co
                vecPoly1 = self.oMeshO_3DS.data.vertices[oPoly.vertices[1]].co
                vecPoly2 = self.oMeshO_3DS.data.vertices[oPoly.vertices[2]].co
                vecVert3D = geometry.barycentric_transform(oVertUV.co, vecUV0, vecUV1, vecUV2, vecPoly0, vecPoly1, vecPoly2)    ###LEARN: How to convert from a point in one triangle space to another triangle space
            aMapVertsUV2Verts3DD[oVertUV.index] = len(bm3DD.verts) 
            bm3DD.verts.new(vecVert3D)
        
        #=== Create the polygons in the destination 3D mesh ===
        bm3DD.verts.ensure_lookup_table()
        for oFace in bmUVF.faces:
            aVertsNewFace3D = []
            for oVert in oFace.verts:
                nVert3DD = aMapVertsUV2Verts3DD[oVert.index]
                oVert3DD = bm3DD.verts[nVert3DD]  
                aVertsNewFace3D.append(oVert3DD)       # Traverse from UV-domain to 3D domain using map we created in loop above
            bm3DD.faces.new(aVertsNewFace3D)
        bm3DD.to_mesh(self.oMeshO_3DD.data)

        #=== Add a UV layer and set it to the positions of the source UV verts ===
        aLayer3DSUV_Dst = self.oMeshO_3DD.data.uv_layers.active.data    #... and obtain a reference to it
        bm3DD.from_mesh(self.oMeshO_3DD.data)
        bmUVF.verts.ensure_lookup_table()
        for oFace in bm3DD.faces:
            for oLoop in oFace.loops:
                oUV = aLayer3DSUV_Dst[oLoop.index].uv
                nVertID = oLoop.vert.index
                oVertUV = bmUVF.verts[nVertID]
                oUV.x = oVertUV.co.x              
                oUV.y = oVertUV.co.y              

        #=== Cleanup the newly generated 3D mesh ===
        bpy.ops.object.mode_set(mode='EDIT')        ###TODO<17>
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.remove_doubles(threshold=0.005)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='1', regular=True)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        #=== Obtain CMesh reference to 3D cloth mesh we just created ===        
        self.oMesh_3DD = CMesh.CMesh.CreateFromExistingObject(self.oMeshO_3DD.name)       ###IMPROVE<17>: Go all on CMesh??
                


    def PrepareClothForGame(self):
        #===== Prepare the cloth for gaming runtime by separating cut-cloth into skinned and simulated areas =====       
        sNameClothSimulated = self.oBodyBase.sMeshPrefix + self.sNameCloth + "-Simulated"
        sNameClothSkinned   = self.oBodyBase.sMeshPrefix + self.sNameCloth + "-Skinned"
        ###DEVF!!!!!!!!! self.oMeshClothSimulated = CMesh.CMesh.CreateFromDuplicate(sNameClothSimulated, self.oMeshClothCut)     # Simulated mesh is sent to Unity untouched.
        self.oMeshClothSimulated = CMesh.CMesh.CreateFromDuplicate(sNameClothSimulated, self.oMesh_3DD)     # Simulated mesh is sent to Unity untouched.
        self.oMeshClothSimulated.SetParent(G.C_NodeFolder_Game)
    
        #=== Transfer the skinning information from the skinned body mesh to the clothing.  _ClothSkinArea_xxx vert groups are to define various areas of the cloth that are skinned and not simulated ===
        self.oBodyBase.oMeshMorphResult.GetMesh().hide = False         ###LEARN: Mesh MUST be visible for weights to transfer!
        Util_TransferWeights(self.oMeshClothSimulated.GetMesh(), self.oBodyBase.oMeshMorphResult.GetMesh())      ###IMPROVE: Insert apply statement in this function?
    
        #=== With the body's skinning info transfered to the cloth, select the the requested vertices contained in the 'skinned verts' vertex group.  These will 'pin' the cloth on the body while the other verts are simulated ===
        bmClothSim = self.oMeshClothSimulated.Open()
        nVertGrpIndex_Pin = self.oMeshClothSimulated.GetMesh().vertex_groups.find(self.sVertGrp_ClothSkinArea)       
        if nVertGrpIndex_Pin == -1:
            raise Exception("###EXCEPTION: CCloth.PrepareClothForGame() could not find in skinned body pin vertex group " + self.sVertGrp_ClothSkinArea)
        oVertGroup_Pin = self.oMeshClothSimulated.GetMesh().vertex_groups[nVertGrpIndex_Pin]
        self.oMeshClothSimulated.GetMesh().vertex_groups.active_index = oVertGroup_Pin.index
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
            self.aMapPinnedParticles.AddUShort(oVert.index)
            self.aMapPinnedParticles.AddUShort(oVert[oLayVertOrigID])
            #print("- NewVertID {:4d} was {:4d} at {:}".format(oVert.index, oVert[oLayVertOrigID], oVert.co))
        
        #=== Post-process the skinned-part to be ready for Unity ===
        Cleanup_VertGrp_RemoveNonBones(self.oMeshClothSkinned.GetMesh(), True)     # Remove the extra vertex groups that are not skinning related from the skinned cloth-part
        #Client.Client_ConvertMeshForUnity(self.oMeshClothSkinned.GetMesh(), False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
        self.oMeshClothSkinned.Close()
        
        #=== Post-process the simulated-part to be ready for Unity ===
        #Client.Client_ConvertMeshForUnity(self.oMeshClothSimulated.GetMesh(), False)                   ###NOTE: Call with 'False' to NOT separate verts at UV seams  ####PROBLEM!!!: This causes UV at seams to be horrible ####SOON!!!
        SelectAndActivate(self.oMeshClothSimulated.GetName())
        bpy.ops.object.vertex_group_remove(all=True)        # Remove all vertex groups from simulated mesh to save memory

        return "OK"

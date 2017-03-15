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
    def __init__(self, oBodyBase, sNameCloth, sClothType, sNameClothSrc):
        "Separate cloth mesh between skinned and simulated parts, calculating the 'twin verts' that will pin the simulated part to the skinned part at runtime."
        
        print("=== CCloth.ctor()  oBodyBase = '{}'  sNameCloth = '{}'  sClothType = '{}'  sNameClothSrc = '{}' ===".format(oBodyBase.sMeshPrefix, sNameCloth, sClothType, sNameClothSrc))

        self.oBodyBase              = oBodyBase         # The back-reference to the owning bodybase that owns / manages this instance
        self.sNameCloth             = sNameCloth        # The human-readable name of this cloth.  Is whatever Unity wants to set it.  Acts as key in owning CBody.aCloths[]
        self.sClothType             = sClothType        # Is one of { 'Shirt', 'Underwear', etc } and determines the cloth collider mesh source.  Must match previously-defined meshes created for each body!   ###IMPROVE: Define all choices
        self.sNameClothSrc          = sNameClothSrc     # The Blender name of the mesh we cut from.  (e.g. 'Bodysuit')
        self.oClothSrc              = G.CGlobals.cm_aClothSources[sNameClothSrc]    # Convenience reference to our cloth source.  We 'cut' from this at every cloth cutting update

        self.aMapPinnedParticles = CByteArray()         # The final flattened map of what verts from the 'skinned cloth vert' map to which verts in the (untouched) Flex-simulated mesh.  Flex needs this to create extra springs to keep the skinned part close to where it should be on the body!

        self.aCurves = []                               # Array of CCurve objects responsible to cut this cloth as per user directions

        #--- UV-domain related ---
        self.oMeshO_UVF = None          # Our copy of our ClothSrc's front UV cloth source mesh. We cut this as per user's cutting curves
        self.oMeshO_UVB = None          # Back version of the above
        self.oMeshO_3DD = None          # The resultant cut cloth back into 3D domain.  This is what is sent to Unity.
        self.oMesh_3DD  = None          # Convenience mesh reference to the above 

        self.oMeshClothSimulated    = None              # The simulated part of the runtime cloth mesh.  Simulated by Flex at runtime.
        self.oMeshClothSkinned      = None              # The skinned part of the runtime cloth mesh.  Skinned at runtime just like its owning skinned body.  (Also responsible to pins simulated mesh)

        #--- Unity-public properties ===
        self.oObj = CObject.CObject("Cloth Global Parameters")
        self.oPropNeckStrapThickness     = self.oObj.PropAdd("NeckStrapThickness",    "", 0.01, 0.001, 0.1) ###TODO<17>

        #=== Create a empty node in game folder where every mesh related to this body will go ===
        self.oNodeRoot = CreateEmptyBlenderNode(self.oBodyBase.sMeshPrefix + "-Cloth-" + self.sNameCloth, self.oBodyBase.oNodeRoot.name)

        #===== Add references to the cutting curves that can cut this cloth =====    ###IMPROVE: More complex cloths will have more complexity here to select which curves...
        self.aCurves.append(Curve.CCurveNeck(self, "Neck"))                 ###TEMP<18>
        self.aCurves.append(Curve.CCurveSide(self, "Side"))
        self.aCurves.append(Curve.CCurveTorsoSplit(self, "TorsoSplit"))

        
    def DoDestroy(self):
        print("=== CCloth.DoDestroy() of cloth '{}'  ===".format(self.sNameCloth))
        DeleteObject(self.oMeshO_UVF.name)
        self.oMeshO_UVF = None
        #DeleteObject(self.oMeshO_UVB.name)  # NOTE: Destroyed during creation process
        DeleteObject(self.oMeshO_3DD.name)
        self.oMeshO_3DD = None
        self.oMeshClothSimulated.DoDestroy()
        self.oMeshClothSimulated = None
        self.oMeshClothSkinned.DoDestroy()
        self.oMeshClothSkinned = None
        DeleteObject(self.oNodeRoot.name)
        self.oNodeRoot = None

        
    def UpdateCutterCurves(self):
        #===== Iterate through our cutter curves to ask them to update themselves from the (just moved) recipe points =====
        ###OBS<17>? 
        for oCurve in self.aCurves:
            oCurve.UpdateCutterCurve()
        return "OK"


            
    def CutClothWithCutterCurves(self):         #===== Cut the source cloth (e.g. bodysuit) and remove the extra fabric the user didn't want with the 'cutter curves' =====        ###DESIGN<17>: Use CMesh?
        #=== Copy our source meshes from our assigned cloth source ===
        self.oMeshO_UVF = DuplicateAsSingleton(self.oClothSrc.oMeshO_UVF.name, self.oNodeRoot.name + "-UVF", self.oNodeRoot.name, False)
        self.oMeshO_UVB = DuplicateAsSingleton(self.oClothSrc.oMeshO_UVB.name, self.oNodeRoot.name + "-UVB", self.oNodeRoot.name, False)

        #=== Iterate through the cutting curves and apply them to the just-copied untouched source mesh.  This will create the resultant mesh in UV-domain (which is then converted back to 3D)
        bmCloth3DS = bmesh.new()
        bmCloth3DS.from_mesh(self.oClothSrc.oMeshO_3DS.data)      # Loop below needs BMesh of source mesh
        for oCurve in self.aCurves:
            oCurve.UpdateCurvePoints(bmCloth3DS)
        self.ConvertBackTo3D()                          # Convert just-cut cloth still in UV-domain back to usable 3D domain
        return "OK"



    def ConvertBackTo3D(self):      # Convert the UV-domain front and back mesh that was cut via Boolean modifiers back to its original 3D form for in-game rendering ===

        #=== Join the two flat UV meshes into one ===
        SelectAndActivate(self.oMeshO_UVB.name)         # First select and activate mesh that will be destroyed (temp mesh)    (Begin procedure to join temp mesh into softbody rim mesh (destroying temp mesh))
        bpy.ops.transform.translate(value=(1, 0, 0))        # Push the back UV mesh by X+1 to undo the X-1 done during ctor
        self.oMeshO_UVF.hide = False
        self.oMeshO_UVF.select = True                         # Now select...
        bpy.context.scene.objects.active = self.oMeshO_UVF    #... and activate mesh that will be kept (merged into)  (Note that to-be-destroyed mesh still selected!)
        bpy.ops.object.join()                                           #... and join the selected mesh into the selected+active one.  Temp mesh has been merged into softbody rim mesh   ###DEV: How about Unity's hold of it??  ###LEARN: Existing custom data layer in merged mesh destroyed!!
        self.oMeshO_UVB = None                               # Above join destroyed the copy mesh so set our variable to None

        #=== Obtain reference to bmeshes for the meshes we need programmatic access to ===
        bmUVF = bmesh.new()     ###IMPROVE<17>: Move to part of CMesh?
        bm3DS = bmesh.new()
        bm3DD = bmesh.new()
        bmUVF.from_mesh(self.oMeshO_UVF.data)
        bm3DS.from_mesh(self.oClothSrc.oMeshO_3DS.data)

        #=== Create new 3D-domain mesh so we can cut with a flattened mesh that doesn't move with user morphs ===
        if self.oMeshO_3DD is not None:
            self.oMeshO_3DD = DeleteObject(self.oMeshO_3DD.name)          # Delete the existing 3DD mesh if it exists.  (This call occurs at every cloth cutting operation)
        oMesh3DDD = bpy.data.meshes.new(self.oNodeRoot.name + "-3DD")
        self.oMeshO_3DD = bpy.data.objects.new(oMesh3DDD.name, oMesh3DDD)
        bpy.context.scene.objects.link(self.oMeshO_3DD)
        SetParent(self.oMeshO_3DD.name, self.oNodeRoot.name)
        self.oMeshO_3DD.location = self.oClothSrc.oMeshO_3DS.location       # Set (new mesh) location to same as source 3D mesh.  
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
                vecLoc, nPoly, nDist = self.oClothSrc.oTreeKD.find(oVertUV.co)                ###LEARN: How to extract multiple arguments out
                oPoly = self.oClothSrc.oMeshO_3DS.data.polygons[nPoly]
                aUV = [self.oClothSrc.oMeshO_3DS.data.uv_layers.active.data[nLoopIndex].uv for nLoopIndex in oPoly.loop_indices]
                vecUV0 = Vector((aUV[0].x, aUV[0].y, 0))            # Expand 2D UV coordinate into a 3D vector with z = 0 so we can invoke barycentric_transform() below
                vecUV1 = Vector((aUV[1].x, aUV[1].y, 0))
                vecUV2 = Vector((aUV[2].x, aUV[2].y, 0))
                vecPoly0 = self.oClothSrc.oMeshO_3DS.data.vertices[oPoly.vertices[0]].co
                vecPoly1 = self.oClothSrc.oMeshO_3DS.data.vertices[oPoly.vertices[1]].co
                vecPoly2 = self.oClothSrc.oMeshO_3DS.data.vertices[oPoly.vertices[2]].co
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
        ###BUG<18>!!!!!: Crashes Blender upon return from this function!  WTF???  Find another alternative to create UV layer
#         aLayer3DSUV_Dst = self.oMeshO_3DD.data.uv_layers.active.data    #... and obtain a reference to it
#         bm3DD.from_mesh(self.oMeshO_3DD.data)
#         bmUVF.verts.ensure_lookup_table()
#         for oFace in bm3DD.faces:
#             for oLoop in oFace.loops:
#                 oUV = aLayer3DSUV_Dst[oLoop.index].uv
#                 nVertID = oLoop.vert.index
#                 oVertUV = bmUVF.verts[nVertID]
#                 oUV.x = oVertUV.co.x              
#                 oUV.y = oVertUV.co.y              

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


    def PrepareClothForGame(self, sVertGrp_ClothSkinArea):
        #===== Prepare the cloth for gaming runtime by separating cut-cloth into skinned and simulated areas.  sVertGrp_ClothSkinArea enables caller to specify which cloth area should be skinned (instead of flex-simulated) =====       
        sNameClothSimulated = self.oNodeRoot.name + "-Simulated"
        sNameClothSkinned   = self.oNodeRoot.name + "-Skinned"
        self.oMeshClothSimulated = CMesh.CMesh.CreateFromDuplicate(sNameClothSimulated, self.oMesh_3DD)     # Simulated mesh is sent to Unity untouched.
        self.oMeshClothSimulated.SetParent(self.oNodeRoot.name)
    
        #=== Transfer the skinning information from the skinned body mesh to the clothing.  _ClothSkinArea_xxx vert groups are to define various areas of the cloth that are skinned and not simulated ===
        self.oBodyBase.oMeshMorphResult.GetMesh().hide = False         ###LEARN: Mesh MUST be visible for weights to transfer!
        Util_TransferWeights(self.oMeshClothSimulated.GetMesh(), self.oBodyBase.oMeshMorphResult.GetMesh())      ###IMPROVE: Insert apply statement in this function?
    
        #=== With the body's skinning info transfered to the cloth, select the the requested vertices contained in the 'skinned verts' vertex group.  These will 'pin' the cloth on the body while the other verts are simulated ===
        bmClothSim = self.oMeshClothSimulated.Open()
        nVertGrpIndex_Pin = self.oMeshClothSimulated.GetMesh().vertex_groups.find(sVertGrp_ClothSkinArea)       # The name in self.oBodyBase of the vertex group detailing the area where cloth verts are skinned instead of cloth-simulated
       
        if nVertGrpIndex_Pin != -1:
            oVertGroup_Pin = self.oMeshClothSimulated.GetMesh().vertex_groups[nVertGrpIndex_Pin]
            self.oMeshClothSimulated.GetMesh().vertex_groups.active_index = oVertGroup_Pin.index
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.vertex_group_select()                # To-be-skinned cloth verts are now selected
        else:
            #raise Exception("###EXCEPTION: CCloth.PrepareClothForGame() could not find in skinned body pin vertex group " + sVertGrp_ClothSkinArea)
            print("###NOTE: CCloth.PrepareClothForGame() could not find in skinned body pin vertex group " + sVertGrp_ClothSkinArea + ".  Proceeding with no skinned cloth area.")
    
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
        self.oMeshClothSkinned.SetParent(self.oNodeRoot.name)
            
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

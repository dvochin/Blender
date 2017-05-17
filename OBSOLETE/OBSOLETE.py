# def OBS_PreviousPairImplementationForBreasts():    ### No longer done in-body but as part of new SlaveMesh_XXX functionality
# 
#     #===== Create the mapping between breast verts and its collider sub-mesh.  At every morph we must set each collider verts to its matching breast vert =====
#     #=== Select the collider sub mesh and obtain its vert indices ===
#     bpy.ops.mesh.select_all(action='DESELECT')
#     oVertGrp_Cldr = oMeshBreastO.vertex_groups["_Area_BreastColL"]
#     oMeshBreastO.vertex_groups.active_index = oVertGrp_Cldr.index
#     bpy.ops.object.vertex_group_select()
#     bmBreast = bmesh.from_edit_mesh(oMeshBreastO.data)
#     aVertsCldrI = [oVert.index for oVert in bmBreast.verts if oVert.select]      # Obtain array of all collider verts (currently selected)
#     bpy.ops.object.mode_set(mode='OBJECT')                                      # FindClosestVert below requires object mode
# 
#     #=== Move the collider verts temporarily so proximity search won't find the same verts ===
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         oVert.co.x += 1.0
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###LEARN: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
#     bpy.ops.object.mode_set(mode='OBJECT')
# 
#     #=== Find the matching vert between breast and its collider submesh ===
#     print("=== Finding vert-to-vert mapping between breast collider and breast ===")
#     aMapBreastVertToColVerts_Cldr = []              # Create two arrays that will store the map between collider verts and breast verts.
#     aMapBreastVertToColVerts_Breast = []            
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         vecVert = oVert.co.copy()
#         vecVert.x -= 1.0                   # Remove the temp offset we applied in above loop
#         nVertClosest, nDistMin, vecVertClosest = Util_FindClosestVert(oMeshBreastO, vecVert, .000001)
#         aMapBreastVertToColVerts_Cldr  .append(nVertCldr)
#         aMapBreastVertToColVerts_Breast.append(nVertClosest)
#         print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %6.4f" % (nVertCldr, nVertClosest, vecVert.x, vecVert.y, vecVert.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
#         #oVert.co = vecVertClosest                               # Set the collider vert exactly on the breast vert
# 
#     #=== Return the collider verts to their original positions ===
#     for nVertCldr in aVertsCldrI:
#         oVert = oMeshBreastO.data.vertices[nVertCldr]
#         oVert.co.x -= 1.0
# 
#     bpy.ops.object.mode_set(mode='EDIT')                    ###LEARN: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oMeshBreastO["aMapBreastVertToColVerts_Cldr"]   = aMapBreastVertToColVerts_Cldr     # Store our map into breast mesh so ApplyOp can copy breast vert positions to each associated collider vert 
#     oMeshBreastO["aMapBreastVertToColVerts_Breast"] = aMapBreastVertToColVerts_Breast 


### Now class-based with modifiers stored in code
# def Breasts_GetMorphList():         ####OBS??? # Send serialized list of the morph-oriented vertex groups on this mesh.  (Those that can be modified with calls to Breasts_ApplyOp())  ####OBS???
#     oMeshO = bpy.data.objects["Breast"]             ###DESIGN: Use this edit-less technique with bmesh more!! 
#     bm = bmesh.new()                                ###LEARN: How to operate with bmesh without entering edit mode!
#     bm.from_object(oMeshO, bpy.context.scene)       ###DESIGN: Selection of body! 
#     oLayVertGrps = bm.verts.layers.deform.active
#     oBA = bytearray()
# 
#     #=== Iterate through all groups marked as morph groups, calculate their center and send name and center to client ===
#     for oVertGrp in oMeshO.vertex_groups:
#         if oVertGrp.name.startswith(G.C_VertGrp_Morph):
#             sNameMorph = oVertGrp.name[len(G.C_VertGrp_Morph):] 
#             Stream_SendStringPascal(oBA, sNameMorph)
#             #=== Calculate the center of this vertex group by iterating over its vertices ===
#             vecCenter = Vector()
#             nVertsInMorphGroup = 0
#             for oVert in bm.verts:
#                 if oVertGrp.index in oVert[oLayVertGrps]:
#                     vecCenter += oVert.co
#                     nVertsInMorphGroup += 1
#             vecCenter /= nVertsInMorphGroup
#             #print("-Morph '{}' at {}".format(sNameMorph, vecCenter))
#             Stream_SendVector(oBA, G.VectorB2U(vecCenter))            # We send Blender 3D coord to Client so we must convert space
#     return oBA              # Return raw byte array back to client so it can deserialize our binary message
















###OBS: Previous implementation of COrificeRig bones being made up by angle instead of being read from a rim of the mesh
#     vecCenter = Vector((0, -0.004, 0.906)) 
#     nBones = 12
#     nDegreesPerBone = 360 / nBones 
# 
#     #=== Create the vertex groups to store the new bone weights for vagina radial expansion bones ===
#     oMesh = CMesh.CMesh.CreateFromExistingObject("WomanA-Original")
# 
#     #=== Obtain reference to vertex group we remove weight from ===
#     nVertGrpIndex = oMesh.GetMesh().vertex_groups.find("_TEST_VAGINA")
#     oMesh.GetMesh().vertex_groups.active_index = nVertGrpIndex
#     oVertGrpAllWeights = oMesh.GetMesh().vertex_groups[nVertGrpIndex]
# 
#     aVertGroups = []
#     for i in range(nBones):
#         nAngle = int(i * nDegreesPerBone)
#         oVertGrp = oMesh.GetMesh().vertex_groups.new(sNamePrefix + str(nAngle).zfill(3))
#         aVertGroups.append(oVertGrp)
#     aBones = []
# 
#     SelectAndActivate(oMesh.GetMesh().parent.name)                           # Must select armature object... 
#     bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
#     oArm = oMesh.GetMesh().modifiers["Armature"].object.data
# 
#     oBoneParent = oArm.edit_bones["pelvis"]
#     for i in range(nBones):
#         nAngle = int(i * nDegreesPerBone)
#         oBoneEdit = oArm.edit_bones.new(sNamePrefix + str(nAngle).zfill(3))
#         oBoneEdit.parent = oBoneParent
#         oBoneEdit.head = vecCenter
#         oBoneEdit.tail = vecCenter + Vector((0,0,0.001))                ###LEARN: A bone *must* have different head and tail otherwise it gets deleted!!
#         oBoneEdit.use_connect = False
#         oBoneEdit.envelope_distance = oBoneEdit.envelope_weight = oBoneEdit.head_radius = oBoneEdit.tail_radius = 0
#         oBoneEdit.envelope_distance = 0.001
#         aBones.append(oBoneEdit)
#          
#     #=== Determine the center of vagina vert ===        
#     SelectAndActivate(oMesh.GetMesh().name)
#     VertGrp_SelectVerts(oMesh.GetMesh(), "_TEST_VAGINA_CENTER")
#     bpy.ops.object.mode_set(mode='OBJECT')          ###LEARN: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
#     nVertCenter = None
#     for oVert in oMesh.GetMesh().data.vertices:
#         if oVert.select == True:
#             nVertCenter = oVert.index
#             print("- Center vert is " + str(nVertCenter))
#             break
#      
#     #=== Select all vagina verts and iterate through each one to set what bones it belongs to and at what weight ===
#     VertGrp_SelectVerts(oMesh.GetMesh(), "_TEST_VAGINA")
#     bpy.ops.object.mode_set(mode='OBJECT')          # We must remain in object mode for bone weight editing!
#     bm = oMesh.Open()
#     oVertCenter = bm.verts[nVertCenter]
# 
#     #=== Determine the verts within range ===
#     aVertsInGroup = [oVert for oVert in bm.verts if oVert.select]
#     aVertsInRange = []        
#     aVertsInRangeDist = []
#     for oVert in aVertsInGroup:
#         nDist = Util_CalcSurfDistanceBetweenTwoVerts(bm, oVert, oVertCenter)
#         if nDist < nDistMax:
#             aVertsInRange.append(oVert.index)
#             aVertsInRangeDist.append(nDist)
#         #else:
#         #    print("- Skipping vert " + str(oVert.index))
# 
#     #=== Iterate through verts in range to set their weights ===
#     bpy.ops.object.mode_set(mode='OBJECT')          # We must be in object mode for bone weight editing!
#     print("\n===== CREATE VAGINA RADIAL BONES =====")
#     for i in range(len(aVertsInRange)):
#         nVert = aVertsInRange[i]
#         nDist = aVertsInRangeDist[i]
#         oVert = oMesh.GetMesh().data.vertices[nVert]
#         vecVertDiff = oVert.co - vecCenter
#         
#         nDistRatio = nDist / nDistMax
#         #nWeight = 1 - nDistRatio
#         nWeight = (cos(nDistRatio*pi) + 1) / 2             # Convert linear ratio to smooth curve (cos(x) from 0 to pi gives smooth curve) 
#         nAngle = degrees(atan2(vecVertDiff.y/1, vecVertDiff.x))
#         if nAngle < 0:
#             nAngle = 360 + nAngle
#         nBone = nAngle / nDegreesPerBone
#         nBone1 = int(nBone)
#         nBone2 = nBone1 + 1
#         if nBone2 >= nBones:
#             nBone2 = 0
#         nBone2_Remainder = nBone - nBone1
#         nBone1_Remainder = 1 - nBone2_Remainder
#         aVertGroups[nBone1].add([nVert], nWeight * nBone1_Remainder, 'ADD')
#         aVertGroups[nBone2].add([nVert], nWeight * nBone2_Remainder, 'ADD')
#         #oVertGrpAllWeights.add([nVert], nWeight, 'SUBTRACT')
#         print("- Vert#{:5d}   A={:5.1f}   D={:5.3f}   DR={:5.3f}   W={:5.3f}   1={:2d}/{:4.2f}   2={:2d}/{:4.2f}".format(oVert.index, nAngle, nDist, nDistRatio, nWeight, nBone1, nBone1_Remainder, nBone2, nBone2_Remainder))
#         
#     print("======================================\n")
#     #bm = oMesh.Close()



                
      















####OBS: Last version of COrificeRig before going to GenX and reading its rim geometry for bones 
# def BoneCreate(nDistMax):
#         #oArm = bpy.context.object.modifiers["Armature"].object.data
# 
#         sNamePrefix = "VaginaBone"
#         vecCenter = Vector((0, -0.004, 0.906)) 
#         nBones = 12
#         nDegreesPerBone = 360 / nBones 
# 
#         #=== Create the vertex groups to store the new bone weights for vagina radial expansion bones ===
#         oMesh = CMesh.CMesh.CreateFromExistingObject("WomanA-Original")
# 
#         #=== Obtain reference to vertex group we remove weight from ===
#         nVertGrpIndex = oMesh.GetMesh().vertex_groups.find("_TEST_VAGINA")
#         oMesh.GetMesh().vertex_groups.active_index = nVertGrpIndex
#         oVertGrpAllWeights = oMesh.GetMesh().vertex_groups[nVertGrpIndex]
# 
#         aVertGroups = []
#         for i in range(nBones):
#             nAngle = int(i * nDegreesPerBone)
#             oVertGrp = oMesh.GetMesh().vertex_groups.new(sNamePrefix + str(nAngle).zfill(3))
#             aVertGroups.append(oVertGrp)
#         aBones = []
# 
#         SelectAndActivate(oMesh.GetMesh().parent.name)                           # Must select armature object... 
#         bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
#         oArm = oMesh.GetMesh().modifiers["Armature"].object.data
# 
#         oBoneParent = oArm.edit_bones["pelvis"]
#         for i in range(nBones):
#             nAngle = int(i * nDegreesPerBone)
#             oBoneEdit = oArm.edit_bones.new(sNamePrefix + str(nAngle).zfill(3))
#             oBoneEdit.parent = oBoneParent
#             oBoneEdit.head = vecCenter
#             oBoneEdit.tail = vecCenter + Vector((0,0,0.001))                ###LEARN: A bone *must* have different head and tail otherwise it gets deleted!!
#             oBoneEdit.use_connect = False
#             oBoneEdit.envelope_distance = oBoneEdit.envelope_weight = oBoneEdit.head_radius = oBoneEdit.tail_radius = 0
#             oBoneEdit.envelope_distance = 0.001
#             aBones.append(oBoneEdit)
#              
#         #=== Determine the center of vagina vert ===        
#         SelectAndActivate(oMesh.GetMesh().name)
#         VertGrp_SelectVerts(oMesh.GetMesh(), "_TEST_VAGINA_CENTER")
#         bpy.ops.object.mode_set(mode='OBJECT')          ###LEARN: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
#         nVertCenter = None
#         for oVert in oMesh.GetMesh().data.vertices:
#             if oVert.select == True:
#                 nVertCenter = oVert.index
#                 print("- Center vert is " + str(nVertCenter))
#                 break
#          
#         #=== Select all vagina verts and iterate through each one to set what bones it belongs to and at what weight ===
#         VertGrp_SelectVerts(oMesh.GetMesh(), "_TEST_VAGINA")
#         bpy.ops.object.mode_set(mode='OBJECT')          # We must remain in object mode for bone weight editing!
#         bm = oMesh.Open()
#         oVertCenter = bm.verts[nVertCenter]
# 
#         #=== Determine the verts within range ===
#         aVertsInGroup = [oVert for oVert in bm.verts if oVert.select]
#         aVertsInRange = []        
#         aVertsInRangeDist = []
#         for oVert in aVertsInGroup:
#             nDist = Util_CalcSurfDistanceBetweenTwoVerts(bm, oVert, oVertCenter)
#             if nDist < nDistMax:
#                 aVertsInRange.append(oVert.index)
#                 aVertsInRangeDist.append(nDist)
#             #else:
#             #    print("- Skipping vert " + str(oVert.index))
# 
#         #=== Iterate through verts in range to set their weights ===
#         bpy.ops.object.mode_set(mode='OBJECT')          # We must be in object mode for bone weight editing!
#         print("\n===== CREATE VAGINA RADIAL BONES =====")
#         for i in range(len(aVertsInRange)):
#             nVert = aVertsInRange[i]
#             nDist = aVertsInRangeDist[i]
#             oVert = oMesh.GetMesh().data.vertices[nVert]
#             vecVertDiff = oVert.co - vecCenter
#             
#             nDistRatio = nDist / nDistMax
#             #nWeight = 1 - nDistRatio
#             nWeight = (cos(nDistRatio*pi) + 1) / 2             # Convert linear ratio to smooth curve (cos(x) from 0 to pi gives smooth curve) 
#             nAngle = degrees(atan2(vecVertDiff.y/1, vecVertDiff.x))
#             if nAngle < 0:
#                 nAngle = 360 + nAngle
#             nBone = nAngle / nDegreesPerBone
#             nBone1 = int(nBone)
#             nBone2 = nBone1 + 1
#             if nBone2 >= nBones:
#                 nBone2 = 0
#             nBone2_Remainder = nBone - nBone1
#             nBone1_Remainder = 1 - nBone2_Remainder
#             aVertGroups[nBone1].add([nVert], nWeight * nBone1_Remainder, 'ADD')
#             aVertGroups[nBone2].add([nVert], nWeight * nBone2_Remainder, 'ADD')
#             #oVertGrpAllWeights.add([nVert], nWeight, 'SUBTRACT')
#             print("- Vert#{:5d}   A={:5.1f}   D={:5.3f}   DR={:5.3f}   W={:5.3f}   1={:2d}/{:4.2f}   2={:2d}/{:4.2f}".format(oVert.index, nAngle, nDist, nDistRatio, nWeight, nBone1, nBone1_Remainder, nBone2, nBone2_Remainder))
#             
#         print("======================================\n")
#         #bm = oMesh.Close()
# 
# def BoneMove(nRadius):
#         sNamePrefix = "VaginaBone"
#         vecCenter = Vector((0, -0.004, 0.906))           ###DEV19: form a class and stuff these as constants!
#         nRadialGrps = 12
#         nDegreesPerRadialGrp = 360 / nRadialGrps 
# 
#         oMeshO = SelectAndActivate("[WomanA]") 
#         bpy.ops.object.mode_set(mode='POSE')
# 
#         oBoneParent = oMeshO.pose.bones["pelvis"]
#         for oBoneEdit in oBoneParent.children:
#             if oBoneEdit.name.find(sNamePrefix) != -1:
#                 nAngle = int(oBoneEdit.name[-3:])              # The last three letters of the bone name is the zero-padded bone angle we need
#                 nAngleRad = radians(nAngle)
#                 x = nRadius * cos(nAngleRad)            # cos(nAngle) = adj / hyp = x / nRadius so x = nRadius * cos(nAngle)
#                 y = nRadius * sin(nAngleRad)            # sin(nAngle) = opp / hyp = y / nRadius so y = nRadius * sin(nAngle)
#                 vecBone = Vector((x, 0, -y))             ###BUG!!! Why the 90 deg rotation?????  ###DEV19!
#                 oBoneEdit.location = vecBone                ###LEARN: How to set a pose bone (oBoneEdit.translate won't work as head/tail is read-only!)
#                 print("-Moving bone '{}'  Angle {:3.0f}  X = {:6.3f}  Y = {:6.3f}".format(oBoneEdit.name, nAngle, x, y))
#         bpy.ops.object.mode_set(mode='OBJECT')
#         oMeshO.hide = True
#         return {"FINISHED"}
#                 
# #if __name__ == "__main__" :
# bpy.utils.register_module(__name__)
#       







        # Find points within a radius of the 3d cursor
#         print("Close points within 0.5 distance")
#         co_find = context.scene.cursor_location
#         for (co, index, dist) in kd.find_range(co_find, 0.5):
#             print("    ", co, index, dist)

        
        
        
#         #=== Obsolete Code to delete edge rings ===
#         oMeshOrificeRig = CMesh.CMesh.CreateFromExistingObject("WomanA.002")     ###HACK!!!!!!
#         bmOrificeRig = oMeshOrificeRig.Open()
#  
#         VertGrp_SelectVerts(oMeshOrificeRig.GetMesh(), "Opening")
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#  
#         aEdgesToDelete = []
#         for oEdge in bmOrificeRig.edges:
#             if (oEdge.select == True):
#                 oEdgeCurrent = oEdge
#                 oFaceCurrent = oEdgeCurrent.link_faces[0]
#                 if (len(oEdgeCurrent.link_faces) != 1):
#                     raise Exception("###EXCEPTION in SelectRing. Starting edge had more than one face!".format(len(oEdgeCurrent.link_faces)))
#  
#                 while (True):
#                     print("Opposite edge search: Looking for opposite of edge {} by avoiding verts {} and {}".format(oEdgeCurrent, oEdgeCurrent.verts[0], oEdgeCurrent.verts[1]))
#                     if (len(oFaceCurrent.edges) != 4):
#                         print("SelectRing: Found a face with {} edges!  Halting this column search.".format(len(oFaceCurrent.edges)))
#                         break
#  
#                     #=== Find the opposite edge to edge 'oEdgeCurrent' on face 'oFaceCurrent' by finding the first edge with two different verts ===
#                     oEdgeOppositeFound = None
#                     for oEdgeOppositeSearch in oFaceCurrent.edges:
#                         if ((oEdgeCurrent.verts[0] != oEdgeOppositeSearch.verts[0]) and (oEdgeCurrent.verts[0] != oEdgeOppositeSearch.verts[1]) and (oEdgeCurrent.verts[1] != oEdgeOppositeSearch.verts[0]) and (oEdgeCurrent.verts[1] != oEdgeOppositeSearch.verts[1])):
#                             print("Opposite edge search:  Found edge {} with vert {} and {}".format(oEdgeOppositeSearch, oEdgeOppositeSearch.verts[0], oEdgeOppositeSearch.verts[1]))
#                             oEdgeOppositeFound = oEdgeOppositeSearch
#                             break
#                     if (oEdgeOppositeFound != None):
#                         oEdgeCurrent = oEdgeOppositeFound
#                     else:
#                         raise Exception("###EXCEPTION in SelectRing: Could not find opposite to edge {}.".format(oEdgeCurrent)) # No reason this would ever happen given that we've just checked above if this face is a quad
#                     aEdgesToDelete.append(oEdgeCurrent)
#                      
#                     #=== Find the other face on edge oEdgeCurrent to continue iteration along the quads ===
#                     if (len(oEdgeCurrent.link_faces) == 2):
#                         if (oFaceCurrent == oEdgeCurrent.link_faces[0]):
#                             oFaceCurrent = oEdgeCurrent.link_faces[1]
#                         else:
#                             oFaceCurrent = oEdgeCurrent.link_faces[0]
#                     else:
#                         print("SelectRing: Edge had {} faces (expected two) = end of ring search for this column.".format(len(oEdgeCurrent.link_faces)))
#                         break
#                          
#  
#         #=== Delete the ring edges tagged above ===
#         bpy.ops.mesh.select_all(action='DESELECT') 
#         for oEdge in aEdgesToDelete:
#             oEdge.select_set(True)
#         #bpy.ops.mesh.delete(type='EDGES')
#              
#         #oMeshOrificeRig.Close()
        
        



# class gBL_apply_morphs(bpy.types.Operator):
#     bl_idname = "gbl.apply_morphs"
#     bl_label = "Apply Morphs"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def call(self, oOp, nVal):
#         nVal = nVal / 100
#         Breasts.Breasts_ApplyMorph('BodyA_Morph', 'WomanA', oOp.sOp, oOp.sVertGrp, oOp.sFrom, oOp.sInfluence, (nVal*oOp.nRatioX, nVal*oOp.nRatioY, nVal*oOp.nRatioZ, 0), None)
#     
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         scn = context.scene
#         for nOp in aMapMorphOps:
#             oOp = aMapMorphOps[nOp]
#             nVal = scn[oOp.sName]
#             self.call(oOp, nVal)
#             
#         return {"FINISHED"}
# 
# 
# 
# 
# 
# 
# aMapMorphOps = {}
# 
# 
# class CMorphOp:       ####DEV  ####CLEANUP  ####SOON: Testing code... Finish it or remove it!
#     def CreateProperty(self, sPropName, nVal, nMin, nMax):        ###MOVE???
#         scene = bpy.context.scene
#         scene['_RNA_UI'] = scene.get('_RNA_UI', {})                         ###LEARN: Technique to add custom properties from http://blenderartists.org/forum/showthread.php?383326-How-to-create-scene-properties-from-a-string-name&p=2950142#post2950142
#         scene[sPropName] = nVal
#         scene['_RNA_UI'][sPropName] = {"name": sPropName, "description": sPropName + " description TODO", "default": nVal, "min": nMin, "max": nMax }      ###IMPROVE: Human name?, Tooltip?        
# 
#     def __init__(self, sName, sOp, sVertGrp, sFrom, sInfluence, nVal, nMin, nMax, nRatioX, nRatioY, nRatioZ):
#         self.sName      = sName
#         self.sOp        = sOp
#         self.sVertGrp   = sVertGrp
#         self.sFrom      = sFrom
#         self.sInfluence = sInfluence
#         self.nVal       = nVal
#         self.nMin       = nMin
#         self.nMax       = nMax
#         self.nRatioX    = nRatioX
#         self.nRatioY    = nRatioY
#         self.nRatioZ    = nRatioZ
#         ###self.oProp      = FloatProperty(name=sName, default=1.0, min=0.5, max=2.5)            ####SOON Put in position from post!
#         #bpy.types.Scene.Op1 = FloatProperty(name="Op1", default=100, min=50, max=2500)
#         self.CreateProperty(self.sName, self.nVal, self.nMin, self.nMax) 
#         aMapMorphOps[sName] = self
# 
# 
# 
# 
# bpy.types.Scene.SizeFromCenterREAL = FloatProperty(name="SizeFromCenterREAL", default=100, min=50, max=2500)
# 
# CMorphOp("SizeCenter",      "RESIZE",       "Nipple", "Center", "Wide",     100,  50, 200, 1, 1, 1)
# CMorphOp("MoveLeftRight",   "TRANSLATION",  "Nipple", "Center", "Wide",       0, -10,  10, 1, 0, 0)           ####HACK: Why 2 not work???: Because of same name!!!!!  Give ops an unique name!
# CMorphOp("MoveUpDown",      "TRANSLATION",  "Nipple", "Center", "Medium",     0, -10,  10, 0, 0, 1)





#===============================================================================
# class gBL_define_breast(bpy.types.Operator):
#     bl_idname = "gbl.define_breast"
#     bl_label = "Define Breast"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         ###oMeshBodyO = SelectAndActivate(G.C_NameBaseCharacter + G.C_NameSuffix_Morph)        ###IMPROVE?
#         ###Breasts.BodyInit_CreateCutoffBreastFromSourceBody(oMeshBodyO)
#         return {"FINISHED"}
# 
# class gBL_perform_breast_op(bpy.types.Operator):
#     bl_idname = "gbl.perform_breast_op"
#     bl_label = "Perform breast op"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         #Breasts.Breasts_ApplyMorph("TRANSLATION", "Nipple", "Top", "Wide", (0,-.03,0,0), None)
#         Breasts.Breasts_ApplyMorph("ROTATION",    "Nipple", "Top", "Wide", -20/57, (1,0,0))
#         #Breasts.Breasts_ApplyMorph("RESIZE",      "Nipple", "Top", "Wide", (1.2,1.2,1.2,0), None)
#         return {"FINISHED"}
# 
# class gBL_update_breast(bpy.types.Operator):
#     bl_idname = "gbl.update_breast"
#     bl_label = "Update Breast"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         ###oMeshBodyO = bpy.data.objects[G.C_NameBaseCharacter + G.C_NameSuffix_Morph]
#         ###Breasts.Breast_ApplyOntoBody(oMeshBodyO)
#         return {"FINISHED"}
#===============================================================================




#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    TEMP CODE
#---------------------------------------------------------------------------    
#         col.operator("gbl.body_create_man")
#         col.operator("gbl.body_create_woman")
#         col.operator("gbl.body_create_shemale")
#         col.operator("gbl.gamemode_play_prepbody")
#         col.operator("gbl.create_body_collider")
#        col.operator("gbl.border_create_all")
#        col.operator("gbl.debug_remove_markers")

        #Penis.gBL_Penis_CalcColliders("PenisM-EroticVR-A-Big")
        #Client.CBMeshMorph_GetMorphVerts('Face', 'Face-MouthOpen')
        #oMeshBodyO = SelectAndActivate("BodyA_Detach_Breasts")
        #oMeshBodyO = SelectAndActivate("WomanA")
        #oBody = CBody(0, 'WomanA', 'Shemale', 'PenisW-EroticVR-A-Big')
        #oBody = CBody(0, 'WomanA', 'Woman', 'Vagina-EroticVR-A', 5000)

        #Client.IsolateHead()
        #print(Client.gBL_GetBones('WomanA'))
        #Client.Client_ConvertMeshForUnity(bpy.data.objects["BodyA_BodyCol"], True)
        #CBBodyCol.SlaveMesh_SetupMasterSlatve("BodyA-BreastCol-ToBody", "BodyA_Morph", 0.000001)
        #CBodyColBreast_GetColliderInfo("")
        #CBody._aBodyBases[0].CreateTempMesh(100)

        #Client.ManCleanup_RemoveExtraMaterials()
        #Client.DumpShapeKey()
        #Client.CreateBoxCollidersFromMesh_All()
        #CBBodyCol.CBBodyColSpheres_GetEncodedMesh("CBBodyColSpheres_Breasts")
        #CBBodyCol.CBBodyColBreasts_PrepareBreastMeshColliderTemplate()
        #CBBodyCol.CBSoftBreasts_GetColliderSourceMeshInfo("BodyA")
        #CBBodyCol.CBBodyCol_Generate("ManA", 1000)
        ##Client.gBL_Cloth_SplitIntoSkinnedAndSimulated("BodySuit-Top_ClothSimulated", "BodySuit-Top", "WomanA", "_ClothSkinnedArea_Top")
        ##Client.Client_ConvertMeshForUnity(SelectAndActivate("WomanA_Morph"), True)
        #CBBodyCol.SlaveMesh_SetupMasterSlave("BodyA-BreastCol-ToBreasts", "BodyA_Detach_Breasts", 0.000001)
        #Breasts.Breasts_ApplyMorph('WomanA', 'WomanA', 'RESIZE', 'Nipple', 'Center', 'Wide', (1.6,1.6,1.6,0), None)

        #CBBodyCol.SlaveMesh_ResyncWithMasterMesh("BodyA-BreastCol-ToBody", "BodyA_Morph")
        #Client.gBL_Body_Create("BodyA", "WomanA", "Woman", "Vagina-EroticVR-A", [])
        #Client.gBL_Body_CreateForMorph("WomanA", "BodyA", "BodyA_Morph")



# class gBL_body_create_man(bpy.types.Operator):
#     bl_idname = "gbl.body_create_man"
#     bl_label = "Create M"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.gBL_Body_CreateMorphBody("A", "ManA", "PenisM-EroticVR-A-Big")
#         Client.gBL_Body_Create("BodyA", "Man", "PenisM-EroticVR-A-Big", [], 1, 0)
#         return {"FINISHED"}
# 
# class gBL_body_create_woman(bpy.types.Operator):
#     bl_idname = "gbl.body_create_woman"
#     bl_label = "Create W"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.gBL_Body_CreateMorphBody("B", "WomanA", "Vagina-EroticVR-A")
#         Client.gBL_Body_Create("BodyB", "Woman", "Vagina-EroticVR-A", ["TiedTop"], 1.3, 0.3)
#         return {"FINISHED"}
# 
# class gBL_body_create_shemale(bpy.types.Operator):
#     bl_idname = "gbl.body_create_shemale"
#     bl_label = "Create S"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.gBL_Body_CreateMorphBody("A", "WomanA", "PenisW-EroticVR-A-Big")
#         ###REV Client.gBL_Body_Create("BodyA", "Shemale", "PenisW-EroticVR-A-Big", ["TiedTop"], 1.3, 0.3)
#         Client.gBL_Body_Create("BodyA", "Shemale", "PenisW-EroticVR-A-Big", [], 1.0, 0.0)
#         return {"FINISHED"}
# 
# class gBL_gamemode_play_prepbody(bpy.types.Operator):
#     bl_idname = "gbl.gamemode_play_prepbody"
#     bl_label = "GameMode_Play_PrepBody"
#     bl_options = {'REGISTER', 'UNDO'}
# 
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         Client.GameMode_Play_PrepBody("BodyA")
#         return {"FINISHED"}
# 
# class gBL_create_body_collider(bpy.types.Operator):
#     bl_idname = "gbl.create_body_collider"
#     bl_label = "Create Body Collider"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         #CBBodyCol.CBBodyCol_GetClothColTris("BodyA_BodyCol", "BodySuit-Top", 0.04)
#         CBBodyCol.CBBodyCol_Generate("BodyA", 3000)
#         return {"FINISHED"}
# 
# class gBL_debug_remove_markers(bpy.types.Operator):
#     bl_idname = "gbl.debug_remove_markers"
#     bl_label = "Remove Markers"
#     bl_options = {'REGISTER', 'UNDO'}
#     def invoke(self, context, event):
#         self.report({"INFO"}, "GBOP: " + self.bl_label)
#         G.Debug_RemoveMarkers()
#         return {"FINISHED"}

###TODO: Blender to Unity morph ops
# Define class and how to serialize to Unity... built in C serializer?
# Build Sliders as in Blender
# Add more properties
# Breast move / down moving out-of-breast verts?
    # Body col and cloth collider has to move too!
        # Map vert to vert and autoadjust?  Or glue in base mesh keeping same verts
# Then... cloth in static mode... sliders with cuts!!









###LEARN: http://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Advanced_Tutorials/Python_Scripting/Addon_Custom_Property 
###LEARN: See also http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Interface
###LEARN: idname_must.be_all_lowercase_and_contain_one_dot

# class Panel_Test(bpy.types.Panel):
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "TOOLS"
#     bl_context = "objectmode"
#     bl_label = "Test Panel"
#   
#     def draw_header(self, context):
#         layout = self.layout
#         layout.label(text="", icon="WORLD")

        #ob = context.object
        #scn = context.scene
        ###BROKEN col.prop(scn, "SizeFromCenter")
        #col.prop(scn, "SizeFromCenterREAL")

        #for nOp in aMapMorphOps:
        #    oOp = aMapMorphOps[nOp]
        #    col.prop(scn, oOp.sName)
        
        #col.operator("gbl.apply_morphs")

        #layout.prop(ob, 'myRnaFloat')












#========================= BODY PREP BONE ROTATION STUFF - April 2017
                






#     ###OBS: Can get quite far by passing matrix.  Based on DAZ's matrix  M = oBone.getWSOrientedBox().transform;  //###LEARN: The members related to the 'oriented box' do pass in seemingly-valid matrices with world-space rotation info.  Unfortunately they still require rotating a 'basis vector' by that angle and for the trouble we're better with well-understood eulers instead!
#     def FixBone_MatrixVersion(self, sNameBone, sLabelBone, nBoneLength, m11, m12, m13, m14, m21, m22, m23, m24, m31, m32, m33, m34):
#         oBone = self.oArmBones[sNameBone]
#         oBone.use_connect = False
#         oBone.use_inherit_rotation = False      ###########
#         oBone.use_inherit_scale = False      ###########
# 
#         M = Matrix([[m11, m12, m13, m14],[m21, m22, m23, m24],[m31, m32, m33, m34],[0,0,0,0]])
#         oBone.matrix = M                # Wrong!  Need to rotate a 'basis vector'... these are all pointing up!
#         oBone.length = nBoneLength



#         if   sRotOrder == 'XYZ':   eulOrientation = Euler((0,0,-pi/2))
#         elif sRotOrder == 'XZY':   eulOrientation = Euler((0,0, pi/2))
#         elif sRotOrder == 'YXZ':   eulOrientation = Euler(( pi/2,0,0))
#         elif sRotOrder == 'YZX':   eulOrientation = Euler((-pi/2,0,0))
#         elif sRotOrder == 'ZXY':   eulOrientation = Euler((0 ,0,0))          # vecBasis below is +Y unit so 'Up' doesn't need to rotate anything
#         elif sRotOrder == 'ZYX':   eulOrientation = Euler((pi,0,0))
#         else: print("\n### ERROR ###\n");


#         global g_set1
#         global g_set2
#         g_set1 = set()
#         g_set2 = set()
#         print(sorted(g_set1))
#         print(sorted(g_set2))






        #=== Convert Euler to Quaternion and calculate bone length ===
        ##quatRot = eulRot.to_quaternion()
        #vecDiff = vecE - vecO
        #nLenBone = vecDiff.length

        #=== Calculate the bone's end (rotated by DAZ-provided Euler above) ===
        #vecAxis = vecBasis.copy()
        #vecAxis.rotate(quatRot)
        #vecTail = vecO + (vecAxis * nLenBone)

        #=== Set the bone origin with the end pointing up and zero roll ===
        ##oBone.head = vecO
        ##oBone.tail = vecO + Vector((0,0,nLenBone))                    ###NOTE: First set bone tail so bone is pointing up then reset the roll... this way when we set bone end to its proper place the roll will change (to some useless value) but still keep bone rotated at a decent angle (not the roll we want however)
        ##oBone.roll = 0 #quatRot.angle                 ###NOTE: Fucking roll is USELESS!  Even a zero value is CRAP unless we set the bone along a cardinal axis, set its roll to zero, orient it correctly while letting its roll go to a garbage value to maintain the orientation

        #=== Rotate the bone to its end orientation.  This modifies oBone. tail and roll ===
        ##oBone.tail = vecTail
        #oBone.rotate(quatRot)
        #oBone.roll = oBone.roll - quatRot.angle

        #####quatRot.rotate(eulOrientation)

#         matBone = Matrix().to_3x3()
#         matBone.rotate(quatRot)
#         matBone = matBone.to_4x4()
#         matBone.translation = vecO
#         oBone.matrix = matBone
#         #oBone.head = vecO
#         #oBone.tail = vecTail
#         #oBone.length = nLenBone
            

        #oBone.use_inherit_rotation = False      ###########
        #oBone.use_inherit_scale = False      ###########




        # Have reasonable angles but no roll!  DAZ can export axis + angle... use that instead of euler?  (Can get rid of starting vectors??)  (WTF quaternions no good???)
        # Then... rotate 90 degrees everything, import to Unity... start thinking about bone boundaries to Unity,  then textures again??
        # Bone rig visualizer accepting for each bone eulerFromDaz.to_quaternion() has what we need.
        # To visualize we need to rotate visualizing bone... but we probably need to rotate that quat instead to be like DAZ
        # Explore DAZ mapping of the bending bones to see how to map.
        # Then export the whole fucking thing to Unity
        # Small problem: heel
        # Can find a way for fucking daz bone roll to get decent value??  wtf????  (set matrix directly?)


            ###OBS: Previous (possibly faulty) rotation analysis based on quaternion rotation difference. (New one by comparing angle difference between global ref vector and rotated one
#         #=== Orient +X toward the requested direction ===  (Note that +Y always flows from the bone parent to the child)  This is to enable Unity's bone to leverage the enhanced flexibility of the X axis with PhysX's D6 configurable joint  (X has different min/max where Y and Z have same min/max)
#         if sNameBone == "lThumb2":
#             self.DEBUG_MoveAndRotateDebugGizmo(0, "Start", matBone)
# 
#         quatOrientationDesired = Euler((0,0,0)).to_quaternion()
#         nAngleToDesiredX_Lowest = sys.float_info.max
#         matBoneRotatedAboutAxisThisQuadrant_Lowest = None
# 
#         for nQuadrant in range(4):
#             matRotateAboutBoneAxisThisQuadrant = Euler((0,nQuadrant*pi/2,0)).to_matrix().to_4x4()
#             matBoneRotatedAboutAxisThisQuadrant = matBone * matRotateAboutBoneAxisThisQuadrant
#             if sNameBone == "lThumb2":
#                 self.DEBUG_MoveAndRotateDebugGizmo(1+nQuadrant, "Rot", matBoneRotatedAboutAxisThisQuadrant)
# 
#             quatOrientationThisQuadrant = matBoneRotatedAboutAxisThisQuadrant.to_quaternion()
#             quatRotateThisQuadrantToDesired = quatOrientationThisQuadrant.rotation_difference(quatOrientationDesired)
#             nAngleToDesiredX = quatRotateThisQuadrantToDesired.angle
#             
#             if nAngleToDesiredX_Lowest > nAngleToDesiredX:
#                 nAngleToDesiredX_Lowest = nAngleToDesiredX
#                 matBoneRotatedAboutAxisThisQuadrant_Lowest = matBoneRotatedAboutAxisThisQuadrant.copy()
# 
#             #if sNameBone == "lThumb2":
#             print("-- Angle diff to quadrant {} is {:5.1f} on bone '{}'".format(nQuadrant, degrees(nAngleToDesiredX), oBone.name))





#         for oBone in self.oArmBones:        
#             oBone.parent = None
#             oBone.use_connect = False
#             oBone.use_inherit_rotation = False
#             oBone.use_inherit_scale = False
#             oBone.use_local_location = False
#             oBone.use_deform = False

#        bpy.ops.object.mode_set(mode='EDIT')
#         global g_bCreateBoneArrow
#         g_bCreateBoneArrow = False
#         for n in range(2):
#             print("\n\n================= RUN " + str(n))
#             if n == 1:
#                 bpy.ops.object.mode_set(mode='OBJECT')
#                 g_bCreateBoneArrow = True


#NOW:# No use trying to get Blender to have DAZ behavior as it forces bone roll to be Y
# Unity doesn't have that limitation so we leave Blender less functional (Just proper bone orientation along Y) but it can't interpret DAZ angles without translation code
# Therefore Unity needs to rotate the bones from DAZ right after it gets them (from DAZ-supplied info)
# - Create a XYZ rotate visualizer with arrow directions so Unity can render colored RGB bones just like DAZ  (Be wary of orientation)
# - Also no need to send complete matrix... harder for Blender to accept them while parented.  Quat fine or back to Euler??
### BONE ROT ALL FUCKED... DO 90 deg right first like old impl.  (Go back to it?)


#     def FixBone(self, sNameBone, sLabelBone, sRotOrder, nLenBone, m11, m12, m13, m14, m21, m22, m23, m24, m31, m32, m33, m34):
#     #def FixBone(self, sNameBone, sLabelBone, sRotOrder, nLenBone, RX, RY, RZ, RW):
#         
#         global g_bCreateBoneArrow
#         
#         #=== Coalesce the input numbers into their corresponding vectors / angles ===
#         C_DazToBlenderResize = 100                          ### Everything 100 times bigger in DAZ        
#         #vecO = Vector((OX/C_DazToBlenderResize, OY/C_DazToBlenderResize, OZ/C_DazToBlenderResize))
#         nLenBone = nLenBone / C_DazToBlenderResize                
#         matDAZ = Matrix(((m11, m12, m13, m14/C_DazToBlenderResize), (m21, m22, m23, m24/C_DazToBlenderResize), (m31, m32, m33, m34/C_DazToBlenderResize), (0,0,0,1)))
#         #quatRot = Quaternion((RW, RX, RY, RZ))
# 
#         #=== Obtain the DAZ-provided 'bone orientation'.  Critical to properly orient its Eulers ===
#         sBoneOrientation = self.mapBoneToOrientation[sNameBone]
#         if   sBoneOrientation == 'L':   eulRotateToBoneForward = Euler((0, pi/2,0))
#         elif sBoneOrientation == 'R':   eulRotateToBoneForward = Euler((0,-pi/2,0))
#         elif sBoneOrientation == 'F':   eulRotateToBoneForward = Euler(( 0,0,0))
#         elif sBoneOrientation == 'B':   eulRotateToBoneForward = Euler((pi,0,0))
#         elif sBoneOrientation == 'U':   eulRotateToBoneForward = Euler((0,  0,0))
#         elif sBoneOrientation == 'D':   eulRotateToBoneForward = Euler((0,-pi,0))
# #         if   sBoneOrientation == 'L':   eulRotateToBoneForward = Euler((0,0,-pi))
# #         elif sBoneOrientation == 'R':   eulRotateToBoneForward = Euler((0,0,0))
# #         elif sBoneOrientation == 'F':   eulRotateToBoneForward = Euler((0,0,-pi/2))
# #         elif sBoneOrientation == 'B':   eulRotateToBoneForward = Euler((0,0, pi/2))
# #         elif sBoneOrientation == 'U':   eulRotateToBoneForward = Euler((0,-pi/2,0))
# #         elif sBoneOrientation == 'D':   eulRotateToBoneForward = Euler((0, pi/2,0))
# #         if   sBoneOrientation == 'L':   eulRotateToBoneForward = Euler((0,0,0))
# #         elif sBoneOrientation == 'R':   eulRotateToBoneForward = Euler((0,0,-pi))
# #         elif sBoneOrientation == 'F':   eulRotateToBoneForward = Euler((0,-pi/2,0))
# #         elif sBoneOrientation == 'B':   eulRotateToBoneForward = Euler((0, pi/2,0))
# #         elif sBoneOrientation == 'U':   eulRotateToBoneForward = Euler((0, 0, pi/2))
# #         elif sBoneOrientation == 'D':   eulRotateToBoneForward = Euler((0, 0,-pi/2))
#         matRotOrientation = eulRotateToBoneForward.to_matrix().to_4x4()
# 
#         #=== Note about mapping of our own 'sBoneOrientation' (generated here from observation in DAZ) and 'sRotOrder' (Provided by DAZ given the angle Euler rotations are applied)  Reveals NO 1:1 RELATIONHIP.  Means we keep using sBoneOrientation to create basis vector!
#         #g_set1.add(sBoneOrientation + "-" + sRotOrder)      ###LEARN: Mapping of sBoneOrientation to sRotOrder ['D-YZX', 'F-ZXY', 'F-ZYX', 'L-XYZ', 'L-XZY', 'R-XYZ', 'R-XZY', 'U-YZX']
#         #g_set2.add(sRotOrder + "-" + sBoneOrientation)      ###LEARN: Mapping of sRotOrder to sBoneOrientation ['XYZ-L', 'XYZ-R', 'XZY-L', 'XZY-R', 'YZX-D', 'YZX-U', 'ZXY-F', 'ZYX-F']
# 
#         
#         #=== Rotate every vector and angle DAZ sends us by 90 degrees about the X axis.  Both DAZ and Blender are 'right hand coodinate systems' but DAZ is +Y Up while Blender is +Z Up ===
#         #eulRotateDazCoordinatesToBlender = Euler((pi/2,0,0))               ###NOTE: Note the IMPORTANT top-level 90 degree rotation to Blender's geometry (up is +Z, forward is -Y, left is -X)   Define top-level transform that converts coordinate and angle from Daz to Blende
#         #matRot = eulRotateDazCoordinatesToBlender.to_matrix().to_4x4()
#         matFinal = matDAZ * matRotOrientation                      ###LEARN: Based on https://docs.blender.org/api/2.49/Mathutils-module.html
# 
#         if g_bCreateBoneArrow:
#             oNewO = DuplicateAsSingleton("BoneArrow", sNameBone)
#             oNewO.matrix_world = matFinal
#             oNewO.scale = Vector((nLenBone,nLenBone,nLenBone))
#             print("-Bone  '{}'  LEN={:5.3f}  '{}'\n{}\n{}".format(sRotOrder, nLenBone, sNameBone, matFinal, oNewO.matrix_world))
#             
#             #=== Visualize the bone in our external visualizer.  (It alone can show proper bone 'roll') ===
#             oNodeBone = bpy.data.objects["Bone-" + oBone.name]
#             oBoneVisualizer = bpy.data.objects["BoneVis-" + oBone.name]
#             oNodeBone.location = vecO
#             oNodeBone.rotation_mode = "QUATERNION"
#             #oNodeBone.rotation_quaternion = oBone.matrix.to_quaternion()
#             oNodeBone.rotation_quaternion = quatRot
#             oBoneVisualizer.scale = Vector((nLenBone, nLenBone, nLenBone))
#             oBoneVisualizer.rotation_euler = eulRotateToBoneForward
#                 
#             return
#         
#         #=== Obtain reference to the bone we need to fix ===
# #         oBone.parent = None
# #         oBone.use_connect = False
# #         oBone.use_inherit_rotation = False
# #         oBone.use_inherit_scale = False
# #         oBone.use_local_location = False
# 
#         #=== Assign the just-defined matrix to the bone.  This will propery set the 'roll' as per our defined rotation without Blender's useless roll 'processing' ===
#         oBone = self.oArmBones[sNameBone]
#         oBone.matrix = matFinal
#         oBone.length = nLenBone                     # We could probably scale the matrix but this is easier
# 
#         #print("-Bone  '{}'  LEN={:5.3f}  '{}'\n{}".format(sRotOrder, nLenBone, sNameBone, matDAZ))    










        ###OBS: Old fake bone roll code No longer pertinent now that we can extract exact DAZ angles and rolls
#         #=== Reparent nodes with 'chestUpper' as root node ===
#         self.oArmBones['chestUpper'].parent      = None
#         self.oArmBones['chestLower'].parent      = self.oArmBones['chestUpper']
#         self.oArmBones['abdomenUpper'].parent    = self.oArmBones['chestLower']
#         self.oArmBones['abdomenLower'].parent    = self.oArmBones['abdomenUpper']
#         self.oArmBones['hip'].parent             = self.oArmBones['abdomenLower']
#         self.oArmBones['lBigToe'].parent         = self.oArmBones['lToe']         # Re-parent all toe bones to Toe so that it can act as master transform in Unity
#         self.oArmBones['rBigToe'].parent         = self.oArmBones['rToe']
#         self.oArmBones['lSmallToe1'].parent      = self.oArmBones['lToe']
#         self.oArmBones['rSmallToe1'].parent      = self.oArmBones['rToe']
#         self.oArmBones['lSmallToe2'].parent      = self.oArmBones['lToe']
#         self.oArmBones['rSmallToe2'].parent      = self.oArmBones['rToe']
#         self.oArmBones['lSmallToe3'].parent      = self.oArmBones['lToe']
#         self.oArmBones['rSmallToe3'].parent      = self.oArmBones['rToe']
#         self.oArmBones['lSmallToe4'].parent      = self.oArmBones['lToe']
#         self.oArmBones['rSmallToe4'].parent      = self.oArmBones['rToe']
#         
#         #=== Verify bone symmetry ===
#         bpy.ops.object.mode_set(mode='OBJECT')
#         self.FirstImport_VerifyBoneSymmetry(self.oMeshOriginalO)
#         nAdjustments = self.FirstImport_VerifyBoneSymmetry(self.oMeshOriginalO)        # Run twice to check if second run had to do anything = bug in the first run!
#         if (nAdjustments != 0):
#             raise Exception("###EXCEPTION: Could not symmetrize bones!  {} are left!".format(nAdjustments))
#     
#     
#         #===== SET BONE TAILS TO A REASONABLE VALUE =====
#         #SelectAndActivate(oRootNodeO.name, True)
#         bpy.ops.object.mode_set(mode='EDIT')                                        ###LEARN: Modifying armature bones is done by simply editing root node containing armature.
#         #=== Iterate a first time to set all bone tails half the vector between parent-to-bone ===
#         for oBoneO in self.oArmBones:
#             if (oBoneO.parent):
#                 vecParentToBone = oBoneO.head - oBoneO.parent.head
#                 oBoneO.tail = oBoneO.head + vecParentToBone * 0.5            # Makes tail of this node protrude a portion of the distance from bone-parent (so it looks nice)
#         #=== Iterate a second time to set the tail of non-leaf bones to its last child (to give 'continuity' between the bones')
#         aBonesSumOfChildHeadPos = {}                        # Contains a vector that sums up all the child heads for each parent bone
#         aBonesCountOfChildBones = {}                        # Contains an int that counts how many children added their head position into aBonesSumOfChildHeadPos
#         for oBoneO in self.oArmBones:                                                    # Iterate through all bones...
#             if (oBoneO.parent):                                                    # ... and for each bone with a parent...
#                 if (oBoneO.parent not in aBonesSumOfChildHeadPos):                # ... create the entries into our dictionary if this parent has not been traversed before...
#                     aBonesSumOfChildHeadPos[oBoneO.parent] = Vector((0,0,0))
#                     aBonesCountOfChildBones[oBoneO.parent] = 0
#                 aBonesSumOfChildHeadPos[oBoneO.parent] += oBoneO.head.copy()        #... and add this bone's head position to the sum...
#                 aBonesCountOfChildBones[oBoneO.parent] += 1                        #... and increment the count.
#         #=== Iterate through our map of parents to set the tail to the average of their children's positions ===
#         for oBoneO in aBonesSumOfChildHeadPos:
#             vecTail = aBonesSumOfChildHeadPos[oBoneO] / aBonesCountOfChildBones[oBoneO]
#             oBoneO.tail = vecTail   
#     
#         #=== Ensure key bone chains are properly linked ===  (Loop above sets bone tail to center of average of children.  This is fine for most purposes EXCEPT the key spine bones)
#         self.ConnectParentTailToHeadOfMostImportantChild1("chestUpper",   "chestLower")
#         self.ConnectParentTailToHeadOfMostImportantChild1("chestLower",   "abdomenUpper")
#         self.ConnectParentTailToHeadOfMostImportantChild1("abdomenUpper", "abdomenLower")
#         self.ConnectParentTailToHeadOfMostImportantChild1("abdomenLower", "hip")                  ###CHECK: abdomenUpper -> abdomenLower -> hip -> pelvis do a 360 loop!  ###NOW### What to do???
#         self.ConnectParentTailToHeadOfMostImportantChild1("hip",          "pelvis")
#         self.ConnectParentTailToHeadOfMostImportantChild1("head",         "upperFaceRig")         ###CHECK: Safe to do?  Rotation side to side would be off-angle to what is intuitive.  ###IMPROVE: Manually set tail upward??
#         self.ConnectParentTailToHeadOfMostImportantChild2("Foot",         "Metatarsals")
#         self.ConnectParentTailToHeadOfMostImportantChild2("Metatarsals",  "Toe")
#         self.ConnectParentTailToHeadOfMostImportantChild2("ForearmTwist", "Hand")
#         
#         #=== Bone chain above fixes a lot of problems but some very short bones still have very poor orientations.  Fix small bones by key bone vectors ===
#         self.OrientSmallBoneFromParents1("abdomenLower",   "chestUpper", "pelvis")     # abdomentLower -> hip -> pelvis form a 360 loop that horribly corrupt Y-axis twist!  Fix orientation from most important torso chain
#         self.OrientSmallBoneFromParents1("hip",            "chestUpper", "pelvis")
#         self.OrientSmallBoneFromParents1("pelvis",         "chestUpper", "pelvis")
#         self.OrientSmallBoneFromParents1("head",           "neckLower",  "head")        # Make both neck bones and head bone point in the same direction so it's easy to orient head
#         self.OrientSmallBoneFromParents1("neckUpper",      "neckLower",  "head")
#         self.OrientSmallBoneFromParents1("neckLower",      "neckLower",  "head")
#         self.OrientSmallBoneFromParents2("Hand",           "ForearmTwist", "Hand")     # Hand is a very short bone that needs to be based on its parent
#         self.OrientSmallBoneFromParents2("Toe",            "Metatarsals", "Toe")       # Toe is poorly oriented toward average of toes.  Set orientation like its parent
#     
#         #=== Apply manual roll to some bones that would deform very poorly with PhysX's configurable joint limits of only having X axis being assymetrical ===
#         self.ManuallyAdjustRoll2("ForearmBend", 90)           # Forearm by default has important elbow bend along Z axis (Needs to be on X-axis for assymetrical X-axis with PhysX configurable joint)
#         self.ManuallyAdjustRoll2("Foot", 25)
#         self.ManuallyAdjustRoll2("Metatarsals", 17)
#         self.ManuallyAdjustRoll2("Toe", 17)                   ###IMPROVE: Orient toward up instead of these hardcoded angles!!


#         SelectAndActivate(self.oMeshOriginalO.parent.name)
#         bpy.ops.object.mode_set(mode='EDIT')
#         for oBoneO in self.oArmBones:
#             oBoneVisualizer = bpy.data.objects["BoneVis-" + oBoneO.name]
#             oBoneO.matrix = oBoneVisualizer.matrix_world
#             oBoneO.length = oBoneVisualizer.scale.x








#            ###OBS: Old implementation where axis entered was DAZ-based  (needed two-way domain traversal)
#             #=== Convert the requested full rotation to a matrix ===
#             eulNewRotationDAZ  = Euler(oBone.vecRotationBuild, oBone.sRotOrder)
#             quatNewRotationDAZ = eulNewRotationDAZ.to_quaternion()          
#             matNewRotationDAZ  = quatNewRotationDAZ.to_matrix().to_4x4()
# 
#             #=== Convert old rotation from Blender to Daz domain, append new rotation, convert back to Blender domain and apply to bone ===            
#             quatRotationOld = oRigVisBone.rotation_quaternion                       # Obtain the existing bone rotation quaternion...                ###IMPROVE: Can do local rotations by quaternion multiplications instead of matrix multiplication??
#             matRotationOld = quatRotationOld.to_matrix().to_4x4()                   #... and convert to its matrix...
#             matRotationOldDaz = matRotationOld * oBone.matBlenderToDaz              #... then convert the existing rotation to Daz-domain...
#             matRotationNewDaz = matRotationOldDaz * matNewRotationDAZ               #... then apply the daz-domain new rotation requested...
#             matRotationNew = matRotationNewDaz * oBone.matDazToBlender              #... then convert form daz-domain back to Blender-domain...
#             oRigVisBone.rotation_quaternion = matRotationNew.to_quaternion()        #... and finally apply the Blender-domain rotation.  Simple no?

            #=== Rotate the Blender pose bone ===
#             if False:
#                 oBonePoseO = self.oMeshOriginalO.parent.pose.bones[sNameBone]            ###IMPROVE20: Find way to directly affect bones.  (They are zero-based so we have to fetch the edit bone world orientation to properly convert to DAZ-domain and back to Blender
#                 matBoneEditRotation = oBone.matBoneEdit.to_quaternion().to_matrix().to_4x4()        ###TODO20: Don't know why this is not working!  Likely we're getting global and local coordinates mixed??
#                 matBoneNew = matRotationNew * matBoneEditRotation.inverted()
#                 ##quatRotationNew = matRotationNew.to_quaternion()
#                 ##quatBoneAtRest = oBone.matBoneEdit.to_quaternion()
#                 ##quatRotationNewLessAtRest = quatRotationNew * quatBoneAtRest.inverted() 
#                 #matBoneAtRest = quatBoneAtRest.to_matrix().to_4x4()
#                 #matRotationBoneNew = matRotationNew * matBoneAtRest.inverted()
#                 oBonePoseO.rotation_quaternion = matBoneNew.to_quaternion() 


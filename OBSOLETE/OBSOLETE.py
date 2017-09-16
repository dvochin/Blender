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
#     bpy.ops.object.mode_set(mode='EDIT')                    ###INFO: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
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
#     bpy.ops.object.mode_set(mode='EDIT')                    ###INFO: For some weird reason the vert push we just did doesn't 'take' unless we enter & exit edit mode!!
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.object.mode_set(mode='OBJECT')
#     oMeshBreastO["aMapBreastVertToColVerts_Cldr"]   = aMapBreastVertToColVerts_Cldr     # Store our map into breast mesh so ApplyOp can copy breast vert positions to each associated collider vert 
#     oMeshBreastO["aMapBreastVertToColVerts_Breast"] = aMapBreastVertToColVerts_Breast 


### Now class-based with modifiers stored in code
# def Breasts_GetMorphList():         ####OBS??? # Send serialized list of the morph-oriented vertex groups on this mesh.  (Those that can be modified with calls to Breasts_ApplyOp())  ####OBS???
#     oMeshO = bpy.data.objects["Breast"]             ###DESIGN: Use this edit-less technique with bmesh more!! 
#     bm = bmesh.new()                                ###INFO: How to operate with bmesh without entering edit mode!
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
















###OBS: Previous implementation of CHoleRig bones being made up by angle instead of being read from a rim of the mesh
#     vecCenter = Vector((0, -0.004, 0.906)) 
#     nBones = 12
#     nDegreesPerBone = 360 / nBones 
# 
#     #=== Create the vertex groups to store the new bone weights for vagina radial expansion bones ===
#     oMesh = CMesh.Create("WomanA-Original")
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
#     SelectObject(oMesh.GetMesh().parent.name)                           # Must select armature object... 
#     bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
#     oArm = oMesh.GetMesh().modifiers["Armature"].object.data
# 
#     oBoneParent = oArm.edit_bones["pelvis"]
#     for i in range(nBones):
#         nAngle = int(i * nDegreesPerBone)
#         oBoneEdit = oArm.edit_bones.new(sNamePrefix + str(nAngle).zfill(3))
#         oBoneEdit.parent = oBoneParent
#         oBoneEdit.head = vecCenter
#         oBoneEdit.tail = vecCenter + Vector((0,0,0.001))                ###INFO: A bone *must* have different head and tail otherwise it gets deleted!!
#         oBoneEdit.use_connect = False
#         oBoneEdit.envelope_distance = oBoneEdit.envelope_weight = oBoneEdit.head_radius = oBoneEdit.tail_radius = 0
#         oBoneEdit.envelope_distance = 0.001
#         aBones.append(oBoneEdit)
#          
#     #=== Determine the center of vagina vert ===        
#     SelectObject(oMesh.GetMesh().name)
#     VertGrp_SelectVerts(oMesh.GetMesh(), "_TEST_VAGINA_CENTER")
#     bpy.ops.object.mode_set(mode='OBJECT')          ###INFO: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
#     nVertCenter = None
#     for oVert in oMesh.GetMeshData().vertices:
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
#         oVert = oMesh.GetMeshData().vertices[nVert]
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



                
      















####OBS: Last version of CHoleRig before going to GenX and reading its rim geometry for bones 
# def BoneCreate(nDistMax):
#         #oArm = bpy.context.object.modifiers["Armature"].object.data
# 
#         sNamePrefix = "VaginaBone"
#         vecCenter = Vector((0, -0.004, 0.906)) 
#         nBones = 12
#         nDegreesPerBone = 360 / nBones 
# 
#         #=== Create the vertex groups to store the new bone weights for vagina radial expansion bones ===
#         oMesh = CMesh.Create("WomanA-Original")
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
#         SelectObject(oMesh.GetMesh().parent.name)                           # Must select armature object... 
#         bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
#         oArm = oMesh.GetMesh().modifiers["Armature"].object.data
# 
#         oBoneParent = oArm.edit_bones["pelvis"]
#         for i in range(nBones):
#             nAngle = int(i * nDegreesPerBone)
#             oBoneEdit = oArm.edit_bones.new(sNamePrefix + str(nAngle).zfill(3))
#             oBoneEdit.parent = oBoneParent
#             oBoneEdit.head = vecCenter
#             oBoneEdit.tail = vecCenter + Vector((0,0,0.001))                ###INFO: A bone *must* have different head and tail otherwise it gets deleted!!
#             oBoneEdit.use_connect = False
#             oBoneEdit.envelope_distance = oBoneEdit.envelope_weight = oBoneEdit.head_radius = oBoneEdit.tail_radius = 0
#             oBoneEdit.envelope_distance = 0.001
#             aBones.append(oBoneEdit)
#              
#         #=== Determine the center of vagina vert ===        
#         SelectObject(oMesh.GetMesh().name)
#         VertGrp_SelectVerts(oMesh.GetMesh(), "_TEST_VAGINA_CENTER")
#         bpy.ops.object.mode_set(mode='OBJECT')          ###INFO: We must return to object mode to be able to read-back the vert select flag! (Annoying!)
#         nVertCenter = None
#         for oVert in oMesh.GetMeshData().vertices:
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
#             oVert = oMesh.GetMeshData().vertices[nVert]
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
#         oMeshO = SelectObject("[WomanA]") 
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
#                 oBoneEdit.location = vecBone                ###INFO: How to set a pose bone (oBoneEdit.translate won't work as head/tail is read-only!)
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
#         oMeshHoleRig = CMesh.Create("WomanA.002")     ###HACK!!!!!!
#         bmHoleRig = oMeshHoleRig.Open()
#  
#         VertGrp_SelectVerts(oMeshHoleRig.GetMesh(), "Opening")
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#  
#         aEdgesToDelete = []
#         for oEdge in bmHoleRig.edges:
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
#         #oMeshHoleRig.Close()
        
        



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
#         scene['_RNA_UI'] = scene.get('_RNA_UI', {})                         ###INFO: Technique to add custom properties from http://blenderartists.org/forum/showthread.php?383326-How-to-create-scene-properties-from-a-string-name&p=2950142#post2950142
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
#         ###oMeshBodyO = SelectObject(G.C_NameBaseCharacter + G.C_NameSuffix_Morph)        ###IMPROVE?
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
        #oMeshBodyO = SelectObject("BodyA_Detach_Breasts")
        #oMeshBodyO = SelectObject("WomanA")
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
        ##Client.Client_ConvertMeshForUnity(SelectObject("WomanA_Morph"), True)
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









###INFO: http://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro/Advanced_Tutorials/Python_Scripting/Addon_Custom_Property 
###INFO: See also http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Interface
###INFO: idname_must.be_all_lowercase_and_contain_one_dot

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
                






#     ###OBS: Can get quite far by passing matrix.  Based on DAZ's matrix  M = oBone.getWSOrientedBox().transform;  //###INFO: The members related to the 'oriented box' do pass in seemingly-valid matrices with world-space rotation info.  Unfortunately they still require rotating a 'basis vector' by that angle and for the trouble we're better with well-understood eulers instead!
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
#         #g_set1.add(sBoneOrientation + "-" + sRotOrder)      ###INFO: Mapping of sBoneOrientation to sRotOrder ['D-YZX', 'F-ZXY', 'F-ZYX', 'L-XYZ', 'L-XZY', 'R-XYZ', 'R-XZY', 'U-YZX']
#         #g_set2.add(sRotOrder + "-" + sBoneOrientation)      ###INFO: Mapping of sRotOrder to sBoneOrientation ['XYZ-L', 'XYZ-R', 'XZY-L', 'XZY-R', 'YZX-D', 'YZX-U', 'ZXY-F', 'ZYX-F']
# 
#         
#         #=== Rotate every vector and angle DAZ sends us by 90 degrees about the X axis.  Both DAZ and Blender are 'right hand coodinate systems' but DAZ is +Y Up while Blender is +Z Up ===
#         #eulRotateDazCoordinatesToBlender = Euler((pi/2,0,0))               ###NOTE: Note the IMPORTANT top-level 90 degree rotation to Blender's geometry (up is +Z, forward is -Y, left is -X)   Define top-level transform that converts coordinate and angle from Daz to Blende
#         #matRot = eulRotateDazCoordinatesToBlender.to_matrix().to_4x4()
#         matFinal = matDAZ * matRotOrientation                      ###INFO: Based on https://docs.blender.org/api/2.49/Mathutils-module.html
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
#         #SelectObject(oRootNodeO.name, True)
#         bpy.ops.object.mode_set(mode='EDIT')                                        ###INFO: Modifying armature bones is done by simply editing root node containing armature.
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


#         SelectObject(self.oMeshOriginalO.parent.name)
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










### Large amount of very difficult code written during penis fitting procedure.  REALLY struggled with this!!
#         for nVertRim in aVertsBodyRim:                      # Iterate through the rim verts to find the verts at X=0.  There should be exactly two: One for top of hole the other for bottom of hole
#             oVertRim = bmBody.verts[nVertRim]
#             vecVertRim = oVertRim.co
#             vecVertPenisClosestToRimVertBody, nVertPenisClosestToRimVertBody, nDist = oKDTreePenis.find(vecVertRim)
#             if nDist > 0.05:
#                 raise Exception("###EXCEPTION: CPenis.MountPenisToBody() could not find vert near enough to {}.  Closest dist = {}".format(vecVertRim, nDist))
#             
#             #=== Obtain reference to the 'closest vert' on penis to this body hole vert ===
#             oVertPenisClosestToRimVertBody = bmPenis.verts[nVertPenisClosestToRimVertBody]
#             oVertPenisClosestToRimVertBody.select_set(True)             ###INFO: BMesh select_set() only appears to work when BMesh created from 'bmesh.from_edit_mesh()'  (not from_mesh())
#             oVertPenisClosestToRimVertBody.co = vecVertRim 
#             
#             #=== Obtain the length of the shortest edge on the hole edge.  We need this to search for penis verts too close below ===
#             nLenEdgeRimSearchDist = sys.float_info.max
#             for oEdge in oVertRim.link_edges:
#                 oVertRimOther = oEdge.other_vert(oVertRim)
#                 if oVertRimOther.index in aVertsBodyRim:
#                     nLenEdgeRimSearchDistNow = oEdge.calc_length()
#                     if nLenEdgeRimSearchDist > nLenEdgeRimSearchDistNow:
#                         nLenEdgeRimSearchDist = nLenEdgeRimSearchDistNow
#             if nLenEdgeRimSearchDist < 0.003:                                     # Make sure we consider removing verts that are at least this close.        ###TUNE
#                 nLenEdgeRimSearchDist = 0.003
#             if nLenEdgeRimSearchDist > 0.0065:                                     # Prevent removing vertices that are too far away
#                 nLenEdgeRimSearchDist = 0.0065
#             #print("- BodyVert Rim={:5}  Pen={:5}  DST={:.5f}  LEN={:.5f}".format(oVertRim.index, nVertPenisClosestToRimVertBody, nDist, nLenEdgeRimSearchDist))
# 
#             #=== Create the dictionary entry for this 'penis vert closest to rim vert'.  We will need it to collapse its 'too close' neighbors later ===
#             dictPenisCollapseVerts[nVertRim] = [oVertPenisClosestToRimVertBody]
#             
#             #=== Accumulate in a set two levels of neighbors around the rim vert.  We need to assemble these in one big set for collapse in loop below ===
#             setVertsTooCloseToRimVertBodys = set()
#             Util_FindCloseVertAlongEdges_RECURSIVE(setVertsTooCloseToRimVertBodys, oVertPenisClosestToRimVertBody, oVertPenisClosestToRimVertBody, nLenEdgeRimSearchDist)
#             #for oVertTooClose in setVertsTooCloseToRimVertBodys:
#             #    setVertsTooCloseToRimVertBodys_All.add(oVertTooClose)
#                 #oVertTooClose.select_set(True)

#         #=== Dissolve verts that are too close to edge mid-points
#         oRimVertBodyPrev = oRimVertBodyRoot
#         oRimVertBodyNow = oRimVertBodyPrev.oRimVertBodyNext
#         while oRimVertBodyNow != None:
#             print(oRimVertBodyPrev, oRimVertBodyNow)
#             if oRimVertBodyPrev.oRimVertPenis != None and oRimVertBodyNow.oRimVertPenis != None:      # Only process edges that have two valid penis verts
#                 vecRimVertPenisPrev = oRimVertBodyPrev.oRimVertPenis.oVertPenis.co 
#                 vecRimVertPenisNext = oRimVertBodyNow.oRimVertPenis.oVertPenis.co
#                 vecEdgeCenter = (vecRimVertPenisPrev + vecRimVertPenisNext) / 2
#                 nLenEdge = (vecRimVertPenisPrev - vecRimVertPenisNext).length 
#     
#                 for oEdge in oRimVertBodyPrev.oRimVertPenis.oVertPenis.link_edges:
#                     oVertToDissolve = oEdge.other_vert(oRimVertBodyPrev.oRimVertPenis.oVertPenis) 
#                     nDistFromEdgeCenter = (oVertToDissolve.co - vecEdgeCenter).length
#                     if nDistFromEdgeCenter < nLenEdge: 
#                         oVertToDissolve.select_set(True)
#     
#                 for oEdge in oRimVertBodyNow.oRimVertPenis.oVertPenis.link_edges:
#                     oVertToDissolve = oEdge.other_vert(oRimVertBodyNow.oRimVertPenis.oVertPenis) 
#                     nDistFromEdgeCenter = (oVertToDissolve.co - vecEdgeCenter).length
#                     if nDistFromEdgeCenter < nLenEdge: 
#                         oVertToDissolve.select_set(True)
#               
#             oRimVertBodyPrev = oRimVertBodyNow 
#             oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
#         bpy.ops.object.vertex_group_deselect()

#         #=== Destroy verts that are further from the rim verts ===
#         oRimVertBodyNow = oRimVertBodyRoot
#         while True:
#             print("- Rim vert destroy on {}".format(oRimVertBodyNow))
#             oVertPenis = oRimVertBodyNow.oRimVertPenis.oVertPenis
#             nDistRimCenterToRimVert = (vecPenisRimCenter - oVertPenis.co).length + 0.001        ###HACK21:!!!!!!! 
# 
#             for (vecVertClose, nVertClose, nDist) in oKDTreePenis.find_range(oVertPenis.co, 0.007):             ###TODO21:!!! Duplicate code!        ###IMPROVE: Edge lenght in loop strcutre!
#                 oVertClose = bmPenis.verts[nVertClose]
#                 if oVertClose.index not in dictRimVertPenis:             # Avoid penis rim verts
#                     nDistRimCenterToCloseVert = (vecPenisRimCenter - vecVertClose).length
#                     if nDistRimCenterToCloseVert > nDistRimCenterToRimVert: 
#                         self.oVisualizerCubes.GetCube("VertOut{:02d}-{}".format(oVertClose.index, nVertClose),  oVertClose.co, "Red", self.C_Layer_VertRemoved, True)
#                         oVertClose.select_set(True)
#  
#             if oRimVertBodyNow.bLastInLoop:
#                 break
#             oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
# 
#         #=== Destroy the verts that are past the rim verts and edge midpoints.  This makes it possible to form clean edges featuring only the rim verts and makes it possible to separate the parts of the penis mesh we want to keep and which part to throw away ===
#         bpy.ops.mesh.delete(type='VERT')
# 
# 
#         #=== Construct faces between the rim verts where no edges exist ===    Vert deletion above destroyed edges (and faces) that reached inside the geometry we want to keep.  Re-create faces on all rim edges that have no common edge
#         oRimVertBodyNow = oRimVertBodyRoot
#         while True:
#             oVertPenisPrev = oRimVertBodyNow.oRimVertBodyPrev.oRimVertPenis.oVertPenis 
#             oVertPenisNow  = oRimVertBodyNow.oRimVertPenis.oVertPenis
# 
#             if oVertPenisNow .is_valid == False:
#                 raise Exception("\n###ERROR: Invalid vert1 {}".format(oVertPenisNow))
#             if oVertPenisPrev.is_valid == False:
#                 raise Exception("\n###ERROR: Invalid vert2 {}".format(oVertPenisPrev))
# 
#             oEdgeOnRim = bmPenis.edges.get([oVertPenisPrev, oVertPenisNow])         ###INFO: How to find an existing edge
#             if oEdgeOnRim == None:                 
#                 oEdgeOnRim = bmPenis.edges.new([oVertPenisPrev, oVertPenisNow])     ###INFO: How to create a new edge between two verts
#                 print("- Edge created between {} and {} ".format(oVertPenisPrev, oVertPenisNow))
#                 
#             if oRimVertBodyNow.bLastInLoop:
#                 break
#             oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
# 
# 
# 
#         #=== Starting at the non-manifold penis base edges keep selecting 'more' and de-selecting the rim verts... this will select all geometry we can delete ===         
#         bpy.ops.mesh.select_all(action='DESELECT')
#         self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisBaseNonManifold.index
#         bpy.ops.object.vertex_group_select()
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')            ###INFO: Expanding by faces doesn't go through simple edges! 
#         self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisRimVerts.index
#         for n in range(30):
#             bpy.ops.object.vertex_group_deselect()      #... and de-selecting rim verts...
#             bpy.ops.mesh.select_more()                  #... selecting one more layer of verts...
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT') 
#         bpy.ops.object.vertex_group_deselect()


#         #=== Destroy verts that are further from the midpoint of each rim edge ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         oRimVertBodyNow = oRimVertBodyRoot
#         while True:
#             print("- Mid-edge vert destroy on {}".format(oRimVertBodyNow))
#             oRimVertPenis1 = oRimVertBodyNow.oRimVertBodyPrev.oRimVertPenis.oVertPenis 
#             oRimVertPenis2 = oRimVertBodyNow.oRimVertPenis.oVertPenis
# 
#             if True:#oRimVertBodyNow.nRimVertBodyID == 13:
#                 oEdgeOnRim = bmPenis.edges.get([oRimVertPenis1, oRimVertPenis2])         ###INFO: How to find an existing edge
#                 if oEdgeOnRim == None:                 
#                     oRimVertPenis1.select_set(True)
#                     oRimVertPenis2.select_set(True)
#                     bpy.ops.mesh.shortest_path_select()
#                     oRimVertPenis1.select_set(False)
#                     oRimVertPenis2.select_set(False)
#                     bpy.ops.mesh.delete(type='VERT')
#                     #bpy.ops.mesh.dissolve_verts()
#                     print("- Edge dissolved verts between {} and {} ".format(oRimVertPenis1, oRimVertPenis2))
# 
#                     oEdgeOnRim = bmPenis.edges.get([oRimVertPenis1, oRimVertPenis2])         ###INFO: How to find an existing edge
#                     if oEdgeOnRim == None:                 
#                         oEdgeOnRim = bmPenis.edges.new([oRimVertPenis1, oRimVertPenis2])     ###INFO: How to create a new edge between two verts
#                         print("- Edge created between {} and {} ".format(oRimVertPenis1, oRimVertPenis2))
# 
#             if oRimVertBodyNow.bLastInLoop:
#                 break
#             oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
            

#         #=== Destroy verts that are further from the midpoint of each rim edge ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         oRimVertBodyNow = oRimVertBodyRoot
#         while True:
#             print("- Mid-edge vert destroy on {}".format(oRimVertBodyNow))
#             vecRimVertPenisPrev = oRimVertBodyNow.oRimVertBodyPrev.oRimVertPenis.oVertPenis.co 
#             vecRimVertPenisNext = oRimVertBodyNow.oRimVertPenis.oVertPenis.co
#             vecEdgeCenter = (vecRimVertPenisPrev + vecRimVertPenisNext) / 2
#             nLenEdge = (vecRimVertPenisPrev - vecRimVertPenisNext).length 
#             nLenEdgeSearchDistance = (nLenEdge / 2)                         # Search distance is half the edge length (search from rim verts itself in loop below)
#             nDistRimCenterToEdgeCenter = (vecPenisRimCenter - vecEdgeCenter).length 
# 
#             self.oVisualizerCubes.GetCube("EdgeCenter{:02d}".format(oRimVertBodyNow.nRimVertBodyID),  vecEdgeCenter, "Yellow", self.C_Layer_EdgeCenters, True)
#             for (vecVertClose, nVertClose, nDist) in oKDTreePenis.find_range(vecEdgeCenter, nLenEdgeSearchDistance):      ###INFO: How to find a range of verts in a KDTree ###SOURCE:https://docs.blender.org/api/blender_python_api_2_71_release/mathutils.kdtree.html
#                 oVertClose = bmPenis.verts[nVertClose]
#                 if oVertClose.index not in dictRimVertPenis:             # Avoid penis rim verts
#                     nDistRimCenterToCloseVert = (vecPenisRimCenter - vecVertClose).length
#                     #print("-- Close to {} = vert {:5d} at dist {:.4f} / {:.4f} {:4.0f}%".format(oRimVertBodyNow, nVertClose, nDistRimCenterToCloseVert, nDistRimCenterToEdgeCenter, 100 * nDistRimCenterToCloseVert / nDistRimCenterToEdgeCenter))
#                     if nDistRimCenterToCloseVert > nDistRimCenterToEdgeCenter: 
#                         self.oVisualizerCubes.GetCube("EdgeOut{:02d}-{}".format(oRimVertBodyNow.nRimVertBodyID, nVertClose),  vecVertClose, "Orange", self.C_Layer_EdgeRemoved, True)
#                         print("= Destroying vert {}".format(oVertClose))
#                         oVertClose.select_set(True)
#                     else:
#                         self.oVisualizerCubes.GetCube("EdgeIn{:02d}-{}".format(oRimVertBodyNow.nRimVertBodyID, nVertClose),  vecVertClose, "Pink", 6, True)
#             if oRimVertBodyNow.bLastInLoop:
#                 break
#             oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext


#             for oEdge in oVertPenis.link_edges:
#                 oVertOther = oEdge.other_vert(oVertPenis)
#                 if oVertOther.index not in dictRimVertPenis:             # Avoid penis rim verts
#                     nDistRimCenterToOtherVert = (vecPenisRimCenter - oVertOther.co).length
#                     if nDistRimCenterToOtherVert > nDistRimCenterToRimVert:
#                         self.oVisualizerCubes.GetCube("VertOut{:02d}-{}".format(oVertPenis.index, nVertClose),  oVertOther.co, "Red", self.C_Layer_VertRemoved, True)
#                         oVertOther.select_set(True)
 


# #         #=== Dissolve inner penis verts that are too close to penis rim verts.  (inner = toward penis rim center) Dissolving them will make the rim verts have edges between one another when we re-triangulate ===
# #         bpy.ops.mesh.select_all(action='DESELECT')
# #         aVertsPastRimToDestroy = []
# #         for nRimVertPenis in dictRimVertPenis:
# #             oRimVertPenis = dictRimVertPenis[nRimVertPenis]
# #             oRimVertBody  = oRimVertPenis.oRimVertBody
# #             nDistCenterToRimVertBody = (vecPenisRimCenter - oRimVertPenis.oVertPenis.co).length 
# #             for oEdge in oRimVertPenis.oVertPenis.link_edges:
# #                 oVertToDissolve = oEdge.other_vert(oRimVertPenis.oVertPenis) 
# #                 if oVertToDissolve.index not in dictRimVertPenis:
# #                     nDistCenterToOtherVert = (vecPenisRimCenter - oVertToDissolve.co).length
# #                     if nDistCenterToOtherVert < nDistCenterToRimVertBody:                      
# #                         if oEdge.calc_length() < oRimVertBody.nLenEdgeToChildLen:
# #                             oVertToDissolve.select_set(True)
# #                     else:
# #                         aVertsPastRimToDestroy.append(oVertToDissolve)      # Vert is away from rim verts (toward non-manifold base edge verts) = tag for deletion in next loop
# # #                 if oEdge.calc_length() < oRimVertBody.nLenEdgeToChildLen:
# # #                     oVertToDissolve = oEdge.other_vert(oRimVertPenis.oVertPenis) 
# # #                     if oVertToDissolve.index not in dictRimVertPenis:
# # #                         nDistCenterToOtherVert = (vecPenisRimCenter - oVertToDissolve.co).length
# # #                         if nDistCenterToOtherVert < nDistCenterToRimVertBody:                      
# # #                             oVertToDissolve.select_set(True)
# # #                         else:
# # #                             aVertsPastRimToDestroy.append(oVertToDissolve)      # Vert is away from rim verts (toward non-manifold base edge verts) = tag for deletion in next loop
# 
#         xxxxxxxxxxxxxxxxxxxx
# 
# 
# 
#         bpy.ops.mesh.dissolve_verts()                   # Dissolve the verts that are too close to rim verts (and toward rim center).
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.mesh.quads_convert_to_tris()
#         bpy.ops.mesh.select_all(action='DESELECT')


                
                
                #bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
                #oEdgeOnRim.select_set(True)
                #oVertPenisNow .select_set(True)
                #oVertPenisPrev.select_set(True)
                
#                 bHasEdgeBetweenRimVerts = False
#                 for oEdge in oVertPenisNow.link_edges:
#                     oVertOther = oEdge.other_vert(oVertPenisNow)
#                     if oVertOther == oVertPenisPrev:                # The 'Now' vert has an edge that connects it to the 'Prev' vert = This edge is ready for joining and no face creation is needed below
#                         bHasEdgeBetweenRimVerts = True
#                         break               
#             
#             if bHasEdgeBetweenRimVerts == False:                    # There are no edges (or faces) between the 'Prev' and 'Next' rim verts.  Find a vertex they share in common and create a face there
#                 print("- Face creation on {}".format(oRimVertBodyNow))
#                 if oVertPenisNow.is_valid and oVertPenisPrev.is_valid:
#                     oVertPenisNow .select_set(True)
#                     oVertPenisPrev.select_set(True)
#                     bpy.ops.mesh.select_more()
#                     bpy.ops.mesh.edge_face_add()
#                     bpy.ops.mesh.select_all(action='DESELECT')
#                 else:
#                     print("###ERROR: Invalid vert in {} or {}".format(oVertPenisNow, oVertPenisPrev))


#         #=== Destroy verts that are further from the rim verts ===
#         oRimVertBodyNow = oRimVertBodyRoot
#         while True:
#             print("- Rim vert destroy on {}".format(oRimVertBodyNow))
#             oVertPenis = oRimVertBodyNow.oRimVertPenis.oVertPenis
#             nDistRimCenterToRimVert = (vecPenisRimCenter - oVertPenis.co).length 
# 
#             for oEdge in oVertPenis.link_edges:
#                 oVertOther = oEdge.other_vert(oVertPenis)
#                 if oVertOther.index not in dictRimVertPenis:             # Avoid penis rim verts
#                     nDistRimCenterToOtherVert = (vecPenisRimCenter - oVertOther.co).length
#                     if nDistRimCenterToOtherVert > nDistRimCenterToRimVert:
#                         self.oVisualizerCubes.GetCube("VertOut{:02d}-{}".format(oVertPenis.index, nVertClose),  oVertOther.co, "Red", 5, True)
#                         oVertOther.select_set(True)
# 
#             if oRimVertBodyNow.bLastInLoop:
#                 break
#             oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext



#         #=== Move the penis rim verts - and their neighbors - to their positions.  This will not only move the rim verts but also their neighbors much closer to where they should go ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         for n in range(1):                                                              ###OPT:!!! EXPENSIVE ###KEEP??
#             for oVertPenisRim in mapPenisRimToBodyRim:
#                 oVertBodyRim = mapPenisRimToBodyRim[oVertPenisRim]
#                 vecTranslation = oVertBodyRim.co - oVertPenisRim.co 
#                 oVertPenisRim.select_set(True)
#                 bpy.ops.transform.translate(value=vecTranslation, proportional='ENABLED', proportional_edit_falloff='SPHERE', proportional_size=0.01)           ###TUNE
#                 oVertPenisRim.select_set(False)
#         for oVertPenisRim in mapPenisRimToBodyRim:                  # Now move the rim verts exactly where they should be.  Neighbors are now closer
#             oVertBodyRim = mapPenisRimToBodyRim[oVertPenisRim]
#             oVertPenisRim.co = oVertBodyRim.co


#         #=== Select the 'chosen closest penis rim verts' so we can smooth neighboring verts closer to the body rim.  Also store them in their own vertex group ===
#         aVertPenisRim = []
#         for nVertPenisClosestToRimVertBody in mapPenisVertToRimVertBody:
#             oVertPenisRim = bmPenis.verts[nVertPenisClosestToRimVertBody] 
#             aVertPenisRim.append(oVertPenisRim)
#             oVertPenisRim.select_set(True)
#         oVertGrp_PenisRimVerts = self.oMeshPenisFitted.GetMesh().vertex_groups.new("_CPenis_RimVerts") 
#         bpy.ops.object.vertex_group_assign()
# 
#         #=== Move the vertices around the 'closest penis rim verts' so neighbors get much closer to body rim (so we can dissolve them)
#         for n in range(5):
#             bpy.ops.mesh.select_more()
#         bpy.ops.object.vertex_group_deselect()
#         bpy.ops.mesh.vertices_smooth(10)            
            






#         mapPenisVertToRimVertBody = {}                          # Map that collects for each penis vert which rim vert report as being 'closest'.  As we have a many-to-many we go the inverse way in the next loop to find those that are truly 'closest possible matches'
#         for nVertRim in aVertsBodyRim:                      # Iterate through the rim verts to find the verts at X=0.  There should be exactly two: One for top of hole the other for bottom of hole
#             oVertRim = bmBody.verts[nVertRim]
#             vecVertRim = oVertRim.co
#             vecVertPenisClosestToRimVertBody, nVertPenisClosestToRimVertBody, nDist = oKDTreePenis.find(vecVertRim)
#             if nDist > 0.05:
#                 raise Exception("###EXCEPTION: CPenis.ctor() could not find vert near enough to {}.  Closest dist = {}".format(vecVertRim, nDist))
#             if nVertPenisClosestToRimVertBody not in mapPenisVertToRimVertBody: 
#                 mapPenisVertToRimVertBody[nVertPenisClosestToRimVertBody] = []
#             mapPenisVertToRimVertBody[nVertPenisClosestToRimVertBody].append(nVertRim) 
# 
#         #=== Iterate through the 'closest penis verts' to find the corresponding closest rim vert (flagged in its dictionary entry in loop above).  This is to find the closest match in the 'many to many' mapping that exists between the two rims ===
#         mapPenisRimToBodyRim = {}                                       # Map that traverses between the chosen penis rim verts to their corresponding body rim verts
#         mapBodyRimToPenisRim = {}                                       # Map that traverses between the body rim verts and their corresponding chosen penis rim verts
#         for nVertPenisClosestToRimVertBody in mapPenisVertToRimVertBody: 
#             aListOfRimVerts = mapPenisVertToRimVertBody[nVertPenisClosestToRimVertBody]
#             oVertPenisClosestToRimVertBody = bmPenis.verts[nVertPenisClosestToRimVertBody]
#             oRimVertBody_Closest = None
#             nDistMin = sys.float_info.max
#             for nRimVert in aListOfRimVerts:
#                 oRimVertBody = bmBody.verts[nRimVert]
#                 nDist = (oVertPenisClosestToRimVertBody.co - oRimVertBody.co).length
#                 if nDistMin > nDist:
#                     nDistMin = nDist
#                     oRimVertBody_Closest = oRimVertBody
#             print("-- Closest Rim={:5d}   Penis={:5d}  Dist={:.4f}  {}".format(oRimVertBody_Closest.index, nVertPenisClosestToRimVertBody, nDistMin, oRimVertBody_Closest.tag))
#             oRimVertBody_Closest.tag = True                         # Tag the closest rim vert has having been 'used'.  This is so we can collapse the unused ones in next loop to avoid gaps in the two meshes
#             #oVertPenisClosestToRimVertBody.co = oRimVertBody_Closest.co         # Set the position of the 'closest' penis vert to the position if its closest rim vert.
#             mapPenisRimToBodyRim[oVertPenisClosestToRimVertBody] = oRimVertBody_Closest 
#             mapBodyRimToPenisRim[oRimVertBody_Closest] = oVertPenisClosestToRimVertBody

#         #=== Identify the rim verts that had no 'closest penis vert' mapped to them.  We will need to dissolve them to avoid leaving holes in the joined meshes ===
#         aRimVertsToDissolve = []                  
#         for nVertRim in aVertsBodyRim:                      # Iterate through the rim verts to find the verts at X=0.  There should be exactly two: One for top of hole the other for bottom of hole
#             oVertRim = bmBody.verts[nVertRim]
#             if oVertRim.tag == False:
#                 aRimVertsToDissolve.append(nVertRim)
#                 print("-- Unused Rim Vert: {:5d}".format(oVertRim.index))

        #FUCK!!!!!!!
        # really close with the rewrite!  New code truly matches accross many-to-many but having serious problems properly collapsing the verts that should be removed on penis!
        # It would be helpful to move verts around chosen ones closer but that is expensive.
        # Edge dissove doesn't appear to work well!  What we need is to compare each vert around the penis rim vert to see if they are too close to the rim somewhere... (including middle points!)
        # But we need to dissolve verts!




#         #=== Fix the penis vertex groups after vertex weld ===
#         oVertGrp_Penis = VertGrp_SelectVerts(self.oBody.oMeshBody.GetMesh(), oVertGrp_Penis.name)
#         self.oBody.oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp_PenisMountingHole.index
#         bpy.ops.object.vertex_group_select()
#         self.oBody.oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp_Penis.index
#         bpy.ops.object.vertex_group_assign()            # Append rim to penis vertex group so now it is complete
# 
#         #=== Fix the penis rim vertex groups after vertex weld ===
#         bpy.ops.mesh.region_to_loop()                   # With entire penis selected this call returns only the rim
#         self.oBody.oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp_PenisMountingHole.index
#         bpy.ops.object.vertex_group_assign()










#         #=== Merge vertices ===  DOES NOT WORK!  (Pelvis loses info!)
#         oRimVertBodyNow = oRimVertBodyRoot
#         while True:
#             bpy.ops.mesh.select_all(action='DESELECT')
#             oRimVertBodyNow.oVertBody.select_set(True)
#             oRimVertBodyNow.oRimVertPenis.oVertPenis.select_set(True)
#             bpy.context.scene.cursor_location = oRimVertBodyNow.oVertBody.co 
#             bpy.ops.mesh.merge(type='CURSOR', uvs=False)
#             #bpy.ops.mesh.merge(type='FIRST', uvs=True)
#             if oRimVertBodyNow.bLastInLoop:
#                 break
#             oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext


            #oEdgeBridgeAcrossRims = bmBody.edges.new([oRimVertBodyNow.oVertBody, oRimVertBodyNow.oRimVertPenis.oVertPenis])
            #oRimVertBodyNow.oRimVertPenis.oVertPenis.select_set(True)
            #oRimVertBodyNow.oVertBody.select_set(True)
            #bpy.context.scene.cursor_location = oRimVertBodyNow.oVertBody.co 
            #bpy.ops.mesh.merge(type='CURSOR', uvs=True)
            #bpy.ops.mesh.merge(type='FIRST', uvs=True)

        #bpy.ops.mesh.bridge_edge_loops()





















###OVERFLOW: From CFlexRig
        #=======  FLEX RIG FINALIZATION =======
        #=== Re-open almost-complete Flex rig to perform final decimation around the borders of the softbodies that were detached & re-attached ===
#         self.oMeshRig_Softbodies.bm = self.oMeshRig_Softbodies.Open()            ###WEAK: This statement group is a bit of a hack.  We can do better by putting a bigger effort to reliably get all the rim verts (they were damaged by earlier decimation)
#         oLayFlexParticleInfo = self.oMeshRig_Softbodies.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]       
#         for oVert in self.oMeshRig_Softbodies.bm.verts:
#             nParticleType = oVert[oLayFlexParticleInfo] & CFlexRig.C_ParticleInfo_Mask_Type
#             #if nParticleType == CFlexRig.C_ParticleType_SkinnedBackplateRim or nParticleType == CFlexRig.C_ParticleType_SkinnedBackplate or nParticleType == CFlexRig.C_ParticleType_SimulatedSurface:
#             if (nParticleType & CFlexRig.C_ParticleInfo_BitTest_IsSimulated) == 0:
#                 oVert.select_set(True)
#         bpy.ops.mesh.remove_doubles(threshold=CFlexRig.C_FlexParticleSpacing * 1.0, use_unselected=True)     ###TUNE: How much?    ###BUG: How about bones we created???  Destroy id to bone!
#         self.oMeshRig_Softbodies.bm = self.oMeshRig_Softbodies.Close()
       
#         #=== Decimate all the 'simulated inner' for all the softbodies so that no vert / particle is closer than Flex particle distance === 
#         aParticlesSimulatedInner = [oVert for oVert in self.oMeshRig_Softbodies.bm.verts if oVert[oLayFlexParticleInfo] & CFlexRig.C_ParticleInfo_Mask_Type == CFlexRig.C_ParticleType_SimulatedInner]
#         for nRepeat in range(5):                              ###INFO: bpy.ops.mesh.remove_doubles with use_unselected=True will NOT do all the verts!  Has to run several times!!! WTF??
#             bpy.ops.mesh.select_all(action='DESELECT')
#             for oVert in aParticlesSimulatedInner:
#                 if oVert.is_valid:                      # Some get destroyed at each operation.  Guard against this
#                     oVert.select_set(True) 
#             bpy.ops.mesh.remove_doubles(threshold=CFlexRig.C_FlexParticleSpacing, use_unselected=True)      ###IMPROVE: Wished there were a way to obtain the result of an op
# 
#         #=== Space out the inner Flex particles away from each other ===
#         bpy.ops.mesh.select_all(action='DESELECT')
#         for oVert in aParticlesSimulatedInner:
#             if oVert.is_valid:
#                 oVert.select_set(True) 
#         bpy.ops.mesh.remove_doubles(threshold=CFlexRig.C_FlexParticleSpacing)



#         oVertGrp = oMeshBody.GetMesh().vertex_groups["_CSoftBody_BreastL"]
#         oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp.index                  ###INFO: How to activate a vertex group by name
#         bpy.ops.object.vertex_group_select()        



#         #=== Perform smoothing of non DAZ bones (our dynamic bones only) ===
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.object.vertex_group_smooth(repeat=1, factor=0.5)
# 
#         #=== Perform global normalization and limiting on ALL bones ===
#         VertGrp_LockUnlock(oMeshBody.GetMesh(), False)              # Unlock our vertex groups so we can fully normalize and limit weights
#         bpy.ops.object.vertex_group_normalize_all(lock_active=False)
#         bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)   # Limit to the four bones Unity can do at runtime.



       #DataLayer_SelectMatchingVerts(oMeshSoftBody.bm, oLayFlexParticleInfo, CFlexRig.C_ParticleType_SimulatedSurface| nSoftBodyID_BitShifted)



        #VertGrp_Remove(oMeshBody.GetMesh(), sNameBoneParent)            # Completely remove the vertex group this softbody is supposed to take over (This leaves more verts that can have our 4-bone maximum at full intensity during gameplay for smoothest possible skinning)
        #=== Clear softbody from DAZ groups.  We need entire bandwidth for four well-defined bones.  Blending to these is done is Finalize ===
#        bmBody = oMeshBody.Open()           ###########KEEP HERE?  In finalize?
#        VertGrp_SelectVerts(oMeshBody.GetMesh(), sNameSoftBodyVertGroup)
#         VertGrp_RemoveVertsFromGroup(oMeshBody.GetMesh(), "chestLower")
#         VertGrp_RemoveVertsFromGroup(oMeshBody.GetMesh(), "chestUpper")
#         VertGrp_RemoveVertsFromGroup(oMeshBody.GetMesh(), "lCollar")
#         VertGrp_RemoveVertsFromGroup(oMeshBody.GetMesh(), "rCollar")
#         VertGrp_RemoveVertsFromGroup(oMeshBody.GetMesh(), "_CSoftBody_BreastL")      ########WTF red??
#         VertGrp_RemoveVertsFromGroup(oMeshBody.GetMesh(), "_CSoftBody_BreastR")
#         VertGrp_RemoveVertsFromGroup(oMeshBody.GetMesh(), "_CSoftBody_Penis")
#        bmBody = oMeshBody.Close()


#         #=== Expand the vertex groups that were damaged into our softbody verts.  This will make it possible for normalize below to smooth things over properly ===
#         for sBoneNeedingSmoothing in self.setBonesNeedingSmoothing:
#             print("- Finalize() smoothing '{}'".format(sBoneNeedingSmoothing))
#             oVertGrp = oMeshBody.GetMesh().vertex_groups[sBoneNeedingSmoothing]
#             oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp.index                 ###INFO: How to activate a vertex group by name
#             bpy.ops.object.vertex_group_smooth(factor=0.5, repeat=2, expand=1)              ###TUNE ###INFO: repeat=1 doesn't appear to do anything!



#         #=== Ensure that all vertices in presentation mesh are skinned ===
#         bmBody = oMeshBody.Open()
#         bpy.ops.mesh.select_ungrouped()
#         SafetyCheck_ThrowExceptionIfVertsSelected(bmBody, "Mesh has verts that are not into any vertex groups (ie. unskinned)")
#         bmBody = oMeshBody.Close()


#         #=== Limit than normalize the rig weights ===        
#         VertGrp_LockUnlock(self.oMeshRig_Softbodies.GetMesh(), False, G.C_RexPattern_EVERYTHING)          # Unlock ALL our vertex groups so we can fully normalize and limit weights
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
#         bpy.ops.object.vertex_group_normalize_all(lock_active=False)




        #VertGrp_SelectVerts(self.oMeshBodySimplified_TEMP.GetMesh(), "#HACK_Keep")        ###DESIGN24: Value in this approach to trimming source mesh?
        #bpy.ops.mesh.select_all(action='INVERT')
        #bpy.ops.mesh.delete(type='VERT')


#         bmFlexTriCol_Body_Fluid = self.oMeshFlexTriCol_BodyFluid.Open()        # Not required so remmed out
#         Util_RemoveNonManifoldGeometry(bmFlexTriCol_Body_Fluid)
#         bmFlexTriCol_Body_Fluid = self.oMeshFlexTriCol_BodyFluid.Close()


#         bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=False, use_multi_face=False, use_non_contiguous=False, use_verts=False)
#         bpy.ops.mesh.delete(type='EDGE')
#         bpy.ops.mesh.select_all(action='DESELECT')        
#         bpy.ops.mesh.select_non_manifold()
#         for nRepeat in range(3):
#             bpy.ops.mesh.edge_face_add()


        #===== CREATE FLEX MAIN SCENE COLLIDER =====
        #=== It is created from the just-finished Flex Fluid collider with the softbody verts removed ===    
#         self.oMeshFlexTriCol_BodyMain = CMesh.CreateFromDuplicate(self.oBody.oBodyBase.sMeshPrefix + "CFlexRig-FlexTriCol_Body_Main2", self.oMeshFlexTriCol_BodyFluid)
#         bmFlexTriCol_Body_Main = self.oMeshFlexTriCol_BodyMain.Open()
#         VertGrp_RemoveAndSelect_RegEx(self.oMeshFlexTriCol_BodyMain.GetMesh(), G.C_RexPattern_DynamicBones)
#         bpy.ops.mesh.select_more()
#         bpy.ops.mesh.delete(type='FACE')
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
#         bmFlexTriCol_Body_Main = self.oMeshFlexTriCol_BodyMain.Close()



#         #=== Select everything EXCEPT all possible softbodies.  (These get decimated separately) ===
#         self.oMeshRig_Softbodies.bm = self.oMeshRig_Softbodies.Open() 
#         VertGrp_SelectVerts(self.oMeshRig_Softbodies.GetMesh(), "#CFlexRig_SafeVertsForShrink", bDeselect=True)
#         VertGrp_SelectVerts(self.oMeshRig_Softbodies.GetMesh(), "_CSoftBody_Penis",   bDeselect=True, bThrowIfNotFound=False)      ###WEAK: We hardcode what not to decimate even though we don't know the softbody we need to process yet... chicken and egg situation.
#         VertGrp_SelectVerts(self.oMeshRig_Softbodies.GetMesh(), "_CSoftBody_BreastL", bDeselect=True, bThrowIfNotFound=False)
#         VertGrp_SelectVerts(self.oMeshRig_Softbodies.GetMesh(), "_CSoftBody_BreastR", bDeselect=True, bThrowIfNotFound=False)
# 
#         #=== Perform a HEAVY decimation from our currently high-res shrunken body mesh so that we have verts / particles that are at the legal particle spacing that MUST be respected for Flex to work at runtime ===
#         Util_SafeRemoveDouble(self.oMeshRig_Softbodies.bm, CFlexRig.C_FlexParticleSpacing * CFlexRig.C_RatioSpacingMult_BodyShrink)
#         self.oMeshRig_Softbodies.bm = self.oMeshRig_Softbodies.Close() 



#             #=== Do the important & expensive full-body shrink operation ===
#             nIterations = CFlexRig.C_NumIterationsForFullBodyShrink
#             nDistShrink = CFlexRig.C_FlexParticleSpacing / 2 * CFlexRig.C_RatioSpacingMult_MeshShrink       # Our shrink distance is the Flex particle radius (so collisions appear at skin-depth) but adjusted by a multiplier for best effect in game (it is beneficial to have colliders stick out of the skin a bit because collisions are 'soft') 
#             self.WorkerFunction_DoSafeShrink(self.oMeshFlexTriCol_BodyMain, nDistShrink, nIterations, CFlexRig.C_RemoveDoublesDistDuringShrink)
#             
#             #=== Ensure that there are no non-manifold verts on the smooth verts ===
#             if self.bPerformSafetyChecks:
#                 self.oMeshFlexTriCol_BodyMain.SafetyCheck_CheckForManifoldMesh("Smooth rig mesh has non-manifold geometry")      # If this fails we need to refine shrinking algorithm that ran above


        #=== Set all the vertices of flex rig to 'skinned' by default.  (Softbody verts / particles will override) ===
#         DataLayer_RemoveLayers(self.oMeshRig_Softbodies.GetName())
#         if self.oMeshRig_Softbodies.Open(): 
#             oLayFlexParticleInfo = self.oMeshRig_Softbodies.bm.verts.layers.int.new(G.C_DataLayer_FlexParticleInfo)          # Create the important 'ParticleInfo' custom data layer to store much info on each particle including the type of Flex particle each vert in Unity represents (e.g. 'skinned', simulated-surface-with-bone, simulated-inner, etc)
#             for oVert in self.oMeshRig_Softbodies.bm.verts:
#                 oVert[oLayFlexParticleInfo] = CFlexRig.C_ParticleType_Skinned           # Skinned particles have no SoftBodyID and no BoneID
#             self.oMeshRig_Softbodies.Close() 



        #=== Separate the 'Flex Triangle Collider' representing this body's shape in Flex.  This is what repels softbodies, cloth, fluids from non-softbody areas === #@        
#         if self.oMeshRig_Softbodies.Open():
#             oLayFlexParticleInfo = self.oMeshRig_Softbodies.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
#             DataLayer_SelectMatchingVerts(self.oMeshRig_Softbodies.bm, oLayFlexParticleInfo, CFlexRig.C_ParticleType_Skinned, CFlexRig.C_ParticleInfo_Mask_Type)
#             bpy.ops.mesh.select_mode(use_extend=False, use_expand=True, type='FACE')        # Above only selects verts, expand to faces so we can separate4
#             bpy.ops.mesh.select_less()                  # Select one less because of expansion in switch to face-select mode and one less again so we don't conflict with softbodies
#             bpy.ops.mesh.select_less()
#             bpy.ops.mesh.separate(type='SELECTED')      # Separate into another mesh.
#             bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#             self.oMeshRig_Softbodies.Close()
#         bpy.context.object.select = False           # Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#         bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')
#         self.oMeshFlexTriCol_BodyMain = CMesh(self.oBody.oBodyBase.sMeshPrefix + "CFlexRig-BodyMain", bpy.context.scene.objects.active, None)

        #=== Perform post-processing exception on vagina hole rig.  (It requires 100% bone weight on single bones) ===        ###DESIGN24: Invoke this in a callback to a derived class instead?
#         if self.oBody.oBodyBase.sSex == "Woman":        #@        ###IMPROVE: Should ask for test 'HasVagina()' from CBodyBase instead
#             if self.oMeshFlexTriCol_BodyMain.Open():
#                 self.oMeshFlexTriCol_BodyMain.VertGrp_LockUnlock(False, G.C_RexPattern_EVERYTHING)
#                 aVertGroupsWithOnlyOneBone = [CFlexRig.C_Prefix_DynBone_VaginaHole + "Upper", CFlexRig.C_Prefix_DynBone_VaginaHole + "Lower"]
#                 for sNameVertGroupWithOnlyOneBone in aVertGroupsWithOnlyOneBone:
#                     self.oMeshFlexTriCol_BodyMain.VertGrp_SelectVerts(sNameVertGroupWithOnlyOneBone)
#                     bpy.ops.object.vertex_group_remove_from(use_all_groups=True)
#                     bpy.ops.object.vertex_group_assign()
#                     bpy.ops.object.vertex_group_levels(offset=1)
#                 self.oMeshFlexTriCol_BodyMain.Close()




            ###OBS:?? No longer replace penis cap particles??
#         #=== Get uretra vertex.  It will locate penis center along its long axis (x, z) and the tip location along y ===
#         oMeshBody = self.oFlexRig.oBody.oMeshBody
#         if self.oFlexRig.oBody.oMeshBody.Open():
#             oMeshBody.VertGrp_SelectVerts("_CPenis_Uretra")
#             for oVert in self.oFlexRig.oBody.oMeshBody.bm.verts:             ###OPT:! Sucks we have to iterate through all verts to find one!    ###IMPROVE: Maybe we can implement a 'marking system' in BodyPrep for these special verts so we can find them much more quickly?
#                 if oVert.select:
#                     oVertUretra = oVert
#             self.vecVertUretra = oVertUretra.co.copy()
#             self.vecVertUretra.x = 0                     # Make sure we're centered
#             self.oFlexRig.oBody.oMeshBody.Close()
# 
#         #=== Erase all penis Flex rig verts that are too close to uretra particle ===
#         if oMeshSoftBody.Open(bDeselect = True):
#             for oVert in oMeshSoftBody.bm.verts:
#                 vecDelta = self.vecVertUretra - oVert.co.copy()
#                 if vecDelta.magnitude < CFlexRig.C_FlexParticleSpacing * 1.70:           # Approximate distance we need to delete previously-constructed Flex particle
#                     oVert.select_set(True)
#             bpy.ops.mesh.delete(type='VERT')
#     
#             #=== Create five particles at the penis tip as closely as we can in pyramid formation.  These tightly-placed will be responsible to penetrate other softbodies ===
#             aVertsCap = [] 
#             nFlexColRadius = (CFlexRig.C_FlexParticleSpacing / 2) * 1.0001      # Making distance a bit further apart so our cap particles are not swallowed by future remove_doubles()
#             nOffsetY = nFlexColRadius * 1.5                        # NOTE: This constant was obtained by placing four spheres as equal radius flat on the ground and measuring the height a fifth sphere could be placed on top without touching.  Together these form the tightest 5 particles that are legal under Flex 
#             aVertsCap.append(oMeshSoftBody.bm.verts.new(self.vecVertUretra))
#             aVertsCap.append(oMeshSoftBody.bm.verts.new(self.vecVertUretra + Vector(( nFlexColRadius, nOffsetY,  nFlexColRadius))))
#             aVertsCap.append(oMeshSoftBody.bm.verts.new(self.vecVertUretra + Vector(( nFlexColRadius, nOffsetY, -nFlexColRadius))))
#             aVertsCap.append(oMeshSoftBody.bm.verts.new(self.vecVertUretra + Vector((-nFlexColRadius, nOffsetY,  nFlexColRadius))))
#             aVertsCap.append(oMeshSoftBody.bm.verts.new(self.vecVertUretra + Vector((-nFlexColRadius, nOffsetY, -nFlexColRadius))))
#             
#             #=== Flag the new vertices / particles so Unity will recognize them as simulated surface ===
#             oLayFlexParticleInfo = oMeshSoftBody.bm.verts.layers.int[G.C_DataLayer_FlexParticleInfo]
#             for oVert in aVertsCap:
#                 oVert[oLayFlexParticleInfo] = CFlexRig.C_ParticleType_SimulatedSurface | self.nSoftBodyID << CFlexRig.C_ParticleInfo_BitShift_SoftBodyID
#             oMeshSoftBody.Close()










###OBS: CBody overflow removed Aug 2017



















    

#     def CreateSoftBodySkin(self, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio, nHoleRadius):
#         "Create a softbody skin by detaching sSoftBodyPart verts from game's skinned main body"
#         self.aSoftBodies[sSoftBodyPart] = CSoftBody.CSoftBodySkin(self, sSoftBodyPart, nSoftBodyFlexColliderShrinkRatio, nHoleRadius)  # This will enable Unity to find this instance by our self.sSoftBodyPart key and the body.
#         return "OK"


#     def Morph_UpdateDependentMeshes(self):
#         "Update all the softbodies connected to this body.  Needed after an operation on self.oMeshMorph"
#         for oSoftBody in self.aSoftBodies.values():
#             oSoftBody.Morph_UpdateDependentMeshes()
   
   
#     def CreateFlexRig(self, nDistFlexColliderShrinkMult):
#         "Called by Unity when all soft body parts have been removed from self.oMeshBody.  Creates the gametime Flex collider."
#         
#         print("=== CBody.CreateFlexRig()  on '{}' ===".format(self.oBodyBase.sMeshPrefix))
#         #=== Start the Flex collider from the current self.oMeshBody.  (It just had all softbody bits removed) ===
#         self.oMeshFlexCollider = CMesh.CreateFromDuplicate(self.oBodyBase.sMeshPrefix + 'FlexCollider' , self.oMeshBody)
#         oMeshFlexCollider = self.oMeshFlexCollider.GetMesh()
#         
#         #=== Simplify the mesh so remesh + shrink below work better (e.g. remove teeth, eyes, inside of ears & nostrils, etc) ===
#         ###TODO15: Cleanup mesh!
# 
#         #=== Gut the mesh's armature, vertex groups, materials, etc as it has to be reskined after the remesh ===
#         #oMeshFlexCollider.modifiers.remove(oMeshFlexCollider.modifiers['Armature'])     ###INFO: How to remove a modifier by name
#         bpy.ops.object.vertex_group_remove(all=True)
#         Cleanup_RemoveMaterials(self.oMeshFlexCollider.GetMesh())
# 
#         #=== Remesh the Flex collider mesh so that it has particles spaced evenly to efficiently repell other Flex objects ===
#         oModRemesh = oMeshFlexCollider.modifiers.new(name="REMESH", type="REMESH")  ###OPT!!! Expensive operation!  Can design this away from init flow??
#         oModRemesh.mode = 'SMOOTH'
#         oModRemesh.octree_depth = 7         ###IMPROVE15: Need to convert remesh arguments based on body height to inter-particular distance
#         ###DEV23:!!!!!!!! oModRemesh.scale = 0.90 
#         oModRemesh.scale = 0.40 
#         oModRemesh.use_remove_disconnected = True
#         AssertFinished(bpy.ops.object.modifier_apply(modifier=oModRemesh.name))     # This call destroys skinning info / vertex groups
# 
#         #=== Transfer the skinning information from the body back to the just remeshed flex collider mesh ===
#         Util_TransferWeights(oMeshFlexCollider, self.oMeshBody.GetMesh())
#         
#         #=== Now that we have re-skinned we can 'shrink' the collision mesh to compensate for the Flex inter-particle distance ===
#         self.oMeshFlexCollider.Open()
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.transform.shrink_fatten(value=G.CGlobals.cm_nFlexParticleSpacing * nDistFlexColliderShrinkMult)
#         self.oMeshFlexCollider.Close()
#         
#         return "OK"         # Called from Unity so we must return something it can understand
        
        
        
    
    
    #---------------------------------------------------------------------------    BREASTS

#     def Breasts_ApplyMorph(self, sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue, vecOpAxis):
#         "Apply a breast morph operation onto this body"
#         ###DESIGN: Design decisions needed on what to do in Client and what in Blender as considerable shift is possible...
#         
#         sOpName = sOpMode + "_" + sOpArea + "_" + sOpPivot + "_" + sOpRange  ####PROBLEM!!!!  Not specialized enough for all cases (add extra params)
#         self.oMeshSrcBreast.Open()
#         bpy.ops.object.mode_set(mode='OBJECT')
#     
#         #=== If a previous shape key for our operation exists we must delete it in order to guarantee that we can undo our previous ops and keep our op from influencing the other ops and keep everything 'undoable' ===
#         if self.oMeshSrcBreast.GetMeshData().shape_keys is None:  # Add the 'basis' shape key if shape_keys is None
#             bpy.ops.object.shape_key_add(from_mix=False)
#         if sOpName in self.oMeshSrcBreast.GetMeshData().shape_keys.key_blocks:
#             self.oMeshSrcBreast.GetMesh().active_shape_key_index = self.oMeshSrcBreast.GetMeshData().shape_keys.key_blocks.find(sOpName)  ###INFO: How to find a key's index in a collection!
#             bpy.ops.object.shape_key_remove()
#         for oShapeKey in self.oMeshSrcBreast.GetMeshData().shape_keys.key_blocks:  # Disable the other shape keys so our operation doesn't bake in their modifications 
#             oShapeKey.value = 0
#     
#         #=== Create a unique shape key to this operation to keep this transformation orthogonal from the other so we can change it later or remove it regardless of transformations that occur after ===
#         bpy.ops.object.mode_set(mode='EDIT')
#         oShapeKey = self.oMeshSrcBreast.GetMesh().shape_key_add(name=sOpName)  ###TODO: Add shape key upon first usage so we remain orthogonal and unable to touch-up our own modifications.
#         self.oMeshSrcBreast.GetMesh().active_shape_key_index = self.oMeshSrcBreast.GetMeshData().shape_keys.key_blocks.find(sOpName)  ###INFO: How to find a key's index in a collection!
#         self.oMeshSrcBreast.GetMesh().active_shape_key.vertex_group = G.C_VertGrp_Area_BreastMorph  ###TODO: Finalize the name of the breast vertex groups 
#         oShapeKey.value = 1
#         
#         #=== Set the cursor to the pivot point requested ===               ###TODO: Set view as cursor and proper axis coordinates!!
#         sBreastMorphPivotPt = G.C_BreastMorphPivotPt + "-" + sOpPivot
#         if sBreastMorphPivotPt not in bpy.data.objects:
#             return "ERROR: Could not find BreastMorphPivotPt = " + sBreastMorphPivotPt 
#         oBreastMorphPivotPt = bpy.data.objects[sBreastMorphPivotPt] 
#         SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', False)
#         bpy.context.scene.cursor_location = oBreastMorphPivotPt.location
#     
#         if sOpRange == "Wide":  ###TUNE
#             nOpSize = 0.4
#         elif sOpRange == "Medium":
#             nOpSize = 0.2
#         elif sOpRange == "Narrow":
#             nOpSize = 0.1
#         else:
#             return "ERROR: Breasts_ApplyMorph() could not decode sOpRange " + sOpRange
#     
#         #=== Select the verts from predefined vertex groups that is to act as the center of the proportional transformation that is about to be executed ===
#         sVertGrpName = G.C_VertGrp_Morph + sOpArea
#         nVertGrpIndex = self.oMeshSrcBreast.GetMesh().vertex_groups.find(sVertGrpName)
#         if (nVertGrpIndex == -1):
#             return "ERROR: Breasts_ApplyMorph() could not find point op area (vertex group) '" + sVertGrpName + "'"
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')  # Make sure we're in vert mode
#         self.oMeshSrcBreast.GetMesh().vertex_groups.active_index = nVertGrpIndex
#         bpy.ops.object.vertex_group_select()
#     
#         ###NOTE: Important coordinate conversion done in Client on a case-by-case for move/rotate/scale...  (Coordinates we receive here a purely Blender global with our z-up)  
#         aContextOverride = AssembleOverrideContextForView3dOps()  ###IMPORTANT: For view3d settings to be active when this script code is called from the context of Client we *must* override the context to the one interactive Blender user uses.
#         if sOpMode == 'ROTATION':
#             aResult = bpy.ops.transform.rotate(aContextOverride, value=vecOpValue, axis=vecOpAxis, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')  ###SOON?: Why only x works and bad axis??
#         else:        
#             aResult = bpy.ops.transform.transform(aContextOverride, mode=sOpMode, value=vecOpValue, proportional='ENABLED', proportional_size=nOpSize, proportional_edit_falloff='SMOOTH')    
#         self.oMeshSrcBreast.Close()
#     
#         sResult = aResult.pop()
#         if (sResult != 'FINISHED'):
#             sResult = "ERROR: Breasts_ApplyMorph() transform operation did not succeed: " + sResult
#             print(sResult)
#             return sResult
#     
#         for oShapeKey in self.oMeshSrcBreast.GetMeshData().shape_keys.key_blocks:  # Re-enable all modifications now that we've commited our transformation has been isolated to just our shape key 
#             oShapeKey.value = 1
#     
#         sResult = "OK: Breasts_ApplyMorph() applying op '{}' on area '{}' with pivot '{}' and range '{}' with {}".format(sOpMode, sOpArea, sOpPivot, sOpRange, vecOpValue)
#         self.Breast_ApplyMorphOntoMorphBody()  ####OPT: Don't need to apply everytime!  Only when batch is done!  # Apply the breasts onto the current body morph character... ####IMPROVE? Pass in name in arg?
#         print(sResult)
#         return sResult
# 
# 
#     def Breast_ApplyMorphOntoMorphBody(self):
#         "Apply a breast morph operation onto this body's morphing body (and update the dependant softbodies)"
# 
#         aVertsBodyMorph = self.oMeshMorph.GetMeshData().vertices
#     
#         #=== 'Bake' all the shape keys in their current position into one and extract its verts ===
#         SelectObject(self.oMeshSrcBreast.GetName())
#         aKeys = self.oMeshSrcBreast.GetMeshData().shape_keys.key_blocks
#         bpy.ops.object.shape_key_add(from_mix=True)  ###INFO: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)
#         nKeys = len(aKeys)
#         aVertsBakedKeys = aKeys[nKeys - 1].data  # We obtain the vert positions from the 'baked shape key'
#     
#         #=== Obtain custom data layer containing the vertIDs of our breast verts into body ===
#         bmBreast = self.oMeshSrcBreast.Open()
#         oLayBodyVerts = bmBreast.verts.layers.int[G.C_DataLayer_SourceBreastVerts]  # Each integer in this data layer stores the vertex ID of the left breast in low 16-bits and vert ID of right breast in high 16-bit  ###INFO: Creating this kills our bmesh references!
#         bmBreast.verts.index_update()
#     
#         #=== Iterate through the breast verts, extract the source verts from body from custom data layer, and set the corresponding verts in body ===
#         for oVertBreast in bmBreast.verts:
#             nVertsEncoded = oVertBreast[oLayBodyVerts]  ####DEV ####HACK!!!
#             nVertBodyBreastL = self.aMapVertsSrcToMorph[(nVertsEncoded & 65535)]  # Breast has been defined from original body.  Map our verts to the requested morphing body  
#             nVertBodyBreastR = self.aMapVertsSrcToMorph[nVertsEncoded >> 16]
#             vecVert = aVertsBakedKeys[oVertBreast.index].co.copy()
#             aVertsBodyMorph[nVertBodyBreastL].co = vecVert
#             vecVert.x = -vecVert.x
#             aVertsBodyMorph[nVertBodyBreastR].co = vecVert
#         self.oMeshSrcBreast.ExitFromEditMode()
#         
#         #=== Delete the 'baked' shape key we created above ===
#         self.oMeshSrcBreast.GetMesh().active_shape_key_index = nKeys - 1
#         bpy.ops.object.shape_key_remove()
#         self.oMeshSrcBreast.Close()
# 
#         #=== Make sure the change we just did to the morphing body propagates to all dependent meshes ===
#         self.Morph_UpdateDependentMeshes()
# 
# 
#     
# 
#     #---------------------------------------------------------------------------    SLAVE MESH
#     def SlaveMesh_ResyncWithMasterMesh(self, sTypeOfSlaveMesh):  ###DEVO?
#         "Set the positions of the slave mesh verts to the positions of their coresponding verts in the master mesh (always self.oMeshMorph)"
#         # Uses information previously stored in sNameSlaveMeshSlave by SlaveMesh_DefineMasterSlaveRelationship() at design time  sTypeOfSlaveMesh is like 'BreastCol', 'BodyCol', 'ClothColTop', etc
#     
#         sNameSlaveMeshSlave = self.oBodyBase.sMeshSource + "-" + sTypeOfSlaveMesh + "-Slave"  ###IMPROVE: Create a function that assembles this name!
#     
#         oMeshSlaveO = SelectObject(sNameSlaveMeshSlave)
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#     
#         #=== Retreive the previously-calculated information from our custom data layers ===
#         bm = bmesh.from_edit_mesh(oMeshSlaveO.data)  ###NOW### Need a matching update_edit_mesh()!!!! 
#         oLaySlaveMeshVerts = bm.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
#         
#         #=== Iterate through the slave mesh, find the corresponding vert in the morph body (going through map from source mesh to morph mesh) and set slave vert
#         aVertsMorph = self.oMeshMorph.GetMeshData().vertices
#         for oVert in bm.verts:
#             nVertSource = oVert[oLaySlaveMeshVerts]  # Master/Slave relationship setup with master as source body...
#             nVertMorph = self.aMapVertsSrcToMorph[nVertSource]  # ... but we need to set our verts to morphing body!  Use the map we have for this purpose
#             oVert.co = aVertsMorph[nVertMorph].co.copy()
#     
#         bpy.ops.object.mode_set(mode='OBJECT')
#         bpy.ops.object.select_all(action='DESELECT')
#         Util_HideMesh(oMeshSlaveO)
#     
#         return ""

    ###DEV
#     def SlaveMesh_GetVertMapSlaveToMaster(self, sNameMeshSlave):    # Return the map of vert-to-vert to Unity so it can restore slave-mesh verts to position of master-mesh verts.  SlaveMesh_DefineMasterSlaveRelationship() must have been called before this function
#         #=== Open the mesh and obtain BMesh and previously-constructed map in custom properties ===
#         oMeshSlaveO = SelectObject(sNameMeshSlave)
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_all(action='DESELECT')
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
#         bm = bmesh.from_edit_mesh(oMeshSlaveO.data)
#         bm.verts.index_update()
#         oLaySlaveMeshVerts = bm.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
#         aMapSlaveMeshSlaveToMaster = array.array('H')                           # This outgoing array stores the map of source vert to destination vert.  Used by Unity to set the slave mesh to the vert position of its master mesh
#      
#         #=== Iterate through the mesh to construct outgoing map from info previously calculated in SlaveMesh_DefineMasterSlaveRelationship() ===     
#         for oVertBM in bm.verts:
#             aMapSlaveMeshSlaveToMaster.append(oVertBM.index)
#             aMapSlaveMeshSlaveToMaster.append(oVertBM[oLaySlaveMeshVerts])
#         bpy.ops.object.mode_set(mode='OBJECT')
#         bpy.ops.object.select_all(action='DESELECT')
#      
#         #=== Send outgoing map back to Unity so it can set slave mesh to master mesh at gametime ===
#         oBA = CByteArray()
#         Stream_SerializeArray(oBA, aMapSlaveMeshSlaveToMaster.tobytes())
#         return oBA.CloseArray()

    ###BROKEN: Related to vert traversal from source to morph body, or to destination softbody??
#     def SlaveMesh_CreateMappingArrayForUnity(self, oMeshSlave):    
#         "Create the vert-to-vert map Unity needs so it can restore slave-mesh verts to position of master-mesh verts.  SlaveMesh_DefineMasterSlaveRelationship() must have been called before this function"
#         ###DEV: Untested / unused?  ###OBS???
# 
#         #=== Open the mesh and obtain BMesh and previously-constructed map in custom properties ===
#         bm = oMeshSlave.Open()
#         bm.verts.index_update()
#         oLaySlaveMeshVerts = bm.verts.layers.int[G.C_DataLayer_SlaveMeshVerts]
#         aMapSlaveMeshSlaveToMaster = array.array('H')                           # This outgoing array stores the map of source vert to destination vert.  Used by Unity to set the slave mesh to the vert position of its master mesh
#      
#         #=== Iterate through the mesh to construct outgoing map from info previously calculated in SlaveMesh_DefineMasterSlaveRelationship() ===     
#         for oVertBM in bm.verts:
#             nVertSlave = oVertBM.index
#             nVertMorph  = self.aMapVertsSrcToMorph[nVertSlave]     #... but we need to set our verts to morphing body!  Use the map we have for this purpose
#             aMapSlaveMeshSlaveToMaster.append(nVertSlave)
#             aMapSlaveMeshSlaveToMaster.append(oVertBM[oLaySlaveMeshVerts])
#         bm = oMeshSlave.Close()
# 
#         return aMapSlaveMeshSlaveToMaster


#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    SLAVE MESH
#---------------------------------------------------------------------------    

###DISCUSSION: SlaveMesh
# ? Update GetVertMap()
# ? Currently applied to orig vert... integrate with mechanism to drill-down?
###DEVO???
# def SlaveMesh_DefineMasterSlaveRelationship(sNameBodySrc, sTypeOfSlaveMesh, nVertTolerance, bMirror=True, bSkin=False):  ####DEV: An init call
#     "Create a master / slave relationship so the slave mesh can follow the vert position of master mesh at runtime.  Only invoked at design time.  Stores its information in mesh custom layer"
#     # sNameBodySrc is like 'WomanA', 'ManA'.  sTypeOfSlaveMesh is like 'BreastCol', 'BodyCol', 'ClothColTop', etc
#     # bMirror is set for most colliders but NOT for breast (as each collider is handled separately)
#     # (Used by breast colliders, cloth colliders, etc so they can update themselves when the source body has been morphed at runtime by the user)
# 
#     print("\n=== SlaveMesh_DefineMasterSlaveRelationship() sNameBodySrc: '{}'  sTypeOfSlaveMesh: '{}' ===".format(sNameBodySrc, sTypeOfSlaveMesh))
#     
#     sNameSlaveMeshSource = sNameBodySrc + "-" + sTypeOfSlaveMesh + "-Source"  # This is the design-time mesh.  It only has half the body and is mirrored to create the Slave mesh.
#     sNameSlaveMeshSlave = sNameBodySrc + "-" + sTypeOfSlaveMesh + "-Slave"  # This is the mesh that will be compled to the master mesh so we can mo
#     
#     #=== Copy the source mesh to a new mesh that will represent both left & right side of the body ===
#     DataLayer_RemoveLayers(sNameSlaveMeshSource)  # Design-time mesh should not have any layers.
#     oMeshO = DuplicateAsSingleton(sNameSlaveMeshSource, sNameSlaveMeshSlave, None, True)  # Create the mirrored mesh.  This is the one that will store the SlaveMesh info and be used for processing
# 
#     #=== 'Mirror' the source mesh so it represents both the left and right side of the body.  (Source only has left) ===
#     if (bMirror):
#         oModMirrorX = Util_CreateMirrorModifierX(oMeshO)
#         AssertFinished(bpy.ops.object.modifier_apply(modifier=oModMirrorX.name))
#     
#     #=== Create mirrored mesh copy and fetch bmesh for editing ===
#     oMeshCopyO = DuplicateAsSingleton(sNameSlaveMeshSlave, sNameSlaveMeshSlave + "_TEMPCOPY_SlaveMesh", G.C_NodeFolder_Temp, False)  # Create a temporary copy of mesh to be slaved so we can edit as we go
#     oMeshMasterO = SelectObject(sNameBodySrc)
#     oMeshSlaveO = SelectObject(sNameSlaveMeshSlave)
#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='DESELECT')
#     bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
# 
#     #=== Create a new data layer to store the mapping between each vert to the closest vert found in sNameBodySrc ===
#     bm = bmesh.from_edit_mesh(oMeshSlaveO.data)
#     oLaySlaveMeshVerts = bm.verts.layers.int.new(G.C_DataLayer_SlaveMeshVerts)
#     bm.verts.index_update()
#     bm.verts.ensure_lookup_table()  ###TODO Needed in later versions of Blender!
#     
#     #=== Find the matching vert between master mesh and its to-be-slaved mesh ===
#     # print("=== Finding vert-to-vert mapping between master and slave meshes ===")
#     for oVert in oMeshCopyO.data.vertices:  # We iterate through copy mesh because Util_FindClosestVert() below must operate in object mode and we need to store info in the source mesh
#         nVert = oVert.index
#         vecVert = oVert.co.copy()
#         nVertClosest, nDistMin, vecVertClosest = Util_FindClosestVert(oMeshMasterO, vecVert, nVertTolerance)
#         if nVertClosest != -1:
#             # print("%3d -> %5d  %6.3f,%6.3f,%6.3f  ->  %6.3f,%6.3f,%6.3f = %8.6f" % (nVert, nVertClosest, vecVert.x, vecVert.y, vecVert.z, vecVertClosest.x, vecVertClosest.y, vecVertClosest.z, nDistMin))
#             oVertBM = bm.verts[nVert]  # Obtain reference to our vert's through bmesh
#             oVertBM.co = vecVertClosest  # Set the source mesh vert exactly at the position of the closest vert on target mesh
#             oVertBM[oLaySlaveMeshVerts] = nVertClosest  # S tore the index of the closest vert in target mesh
#         else:
#             print("###WARNING: Vert %3d @  (%6.3f,%6.3f,%6.3f) was not found!" % (nVert, vecVert.x, vecVert.y, vecVert.z))
#     
#     #=== Close the mesh and delete copy ====
#     bpy.ops.object.mode_set(mode='OBJECT')
#     DeleteObject(oMeshCopyO.name)  # Delete the temporary mesh  ###PROBLEM!!! When Unity calls this DeleteObject destroys two meshes!!!
# 
#     #=== Skin the slave mesh to the original mesh if required ===    
#     if (bSkin):  ###IMPROVE: Remove existing skin info?
#         oMeshSlaveO = SelectObject(sNameSlaveMeshSlave)
#         oMeshSourceO = bpy.data.objects[sNameBodySrc]
#         Util_HideMesh(oMeshSourceO)
#         Util_TransferWeights(oMeshSlaveO, oMeshSourceO)  # bpy.ops.object.vertex_group_transfer_weight()
#     
#     bpy.ops.object.select_all(action='DESELECT')
#     Util_HideMesh(oMeshO)






###OBS: Stuff in ctor of CBody
        ###OBS?
#         sNameVertGroupToCutout = None
#         if self.sGenitals.startswith("Vagina"):         # Woman has vagina and breasts
#             print("###### VAGINA CUTOUT BROKEN!!!")     ###NOW### Repair to old vagina being out-of-main body?
#             ###BROKEN!!!!!!! sNameVertGroupToCutout = "_Cutout_Vagina"
#         elif self.sGenitals.startswith("Penis"):        # Man & Shemale have penis
#             sNameVertGroupToCutout = "_Cutout_Penis"
#         if sNameVertGroupToCutout is not None:
#             bpy.ops.object.mode_set(mode='EDIT')
#             VertGrp_SelectVerts(self.oMeshAssembled.GetMesh(), sNameVertGroupToCutout)     # This vert group holds the verts that are to be soft-body simulated...
#             bpy.ops.mesh.delete(type='FACE')                    # ... and delete the mesh part we didn't want copied to output body
#             bpy.ops.object.mode_set(mode='OBJECT')
#     
#         #=== Import and preprocess the genitals mesh and assemble into this mesh ===
#         if (self.sGenitals.startswith("Vagina") == False):      ###V ###CHECK!!!
#             oMeshGenitalsSource = CMesh.Create(self.sGenitals)          ###WEAK: Create another ctor?
#             oMeshGenitals = CMesh.CreateFromDuplicate("TEMP_Genitals", oMeshGenitalsSource)
#             bpy.context.scene.objects.active = oMeshGenitals.GetMesh()
#             bpy.ops.object.shade_smooth()  ###IMPROVE: Fix the diffuse_intensity to 100 and the specular_intensity to 0 so in Blender the genital texture blends in with all our other textures at these settings
#          
#             #=== Transfer weight from body to add-on genitals ===
#             Util_TransferWeights(oMeshGenitals.GetMesh(), self.oMeshSource.GetMesh())      #bpy.ops.object.vertex_group_transfer_weight()
#          
#             #=== Join the genitals  with the output main body mesh and weld vertices together to form a truly contiguous mesh that will be lated separated by later segments of code into various 'detachable parts' ===           
#             self.oMeshAssembled.GetMesh().select = True
#             bpy.context.scene.objects.active = self.oMeshAssembled.GetMesh()
#             bpy.ops.object.join()                   ###IMPROVE: Make into a function?
#             bpy.ops.object.mode_set(mode='EDIT')
#             bpy.ops.mesh.select_all(action='SELECT')      # Deselect all verts in assembled mesh
#             bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###INFO: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 
#             bpy.ops.mesh.select_all(action='DESELECT')      # Deselect all verts in assembled mesh
#             bpy.ops.object.mode_set(mode='OBJECT')

        ####INFO: Screws up ConvertMeshForUnity royally!  self.oMeshAssembled.data.uv_textures.active_index = 1       # Join call above selects the uv texture of the genitals leaving most of the body untextured.  Revert to full body texture!   ###IMPROVE: Can merge genitals texture into body's??
        ###VertGrp_SelectVerts(self.oMeshAssembled.GetMesh(), sNameVertGroupToCutout)  # Reselect the just-removed genitals area from the original body, as the faces have just been removed this will therefore only select the rim of vertices where the new genitals are inserted (so that we may remove_doubles to merge only it)
        # bpy.ops.mesh.remove_doubles(threshold=0.000001, use_unselected=True)  ###CHECK: We are no longer performing remove_doubles on whole body (Because of breast collider overlay)...  This ok??   ###INFO: use_unselected here is very valuable in merging verts we can easily find with neighboring ones we can't find easily! 

        #=== Create the custom data layer storing assembly vert index.  Enables traversal from Assembly / Morph meshes to Softbody parts 
        ###BROKEN11: DataLayer_CreateVertIndex(self.oMeshAssembled.GetName(), G.C_DataLayer_VertsAssy)
        

        #=== Create map of source verts to morph verts ===  (Enables some morphs such as Breast morphs to be applied to morphing mesh)
        ###OBS??
#         bmMorph = self.oMeshMorph.Open()
#         oLayVertsSrc = bmMorph.verts.layers.int[G.C_DataLayer_VertsSrc]
#         for oVert in bmMorph.verts:
#             if (oVert[oLayVertsSrc] >= G.C_OffsetVertIDs):
#                 nVertOrig = oVert[oLayVertsSrc] - G.C_OffsetVertIDs        # Remove the offset pushed in during creation
#                 self.aMapVertsSrcToMorph[nVertOrig] = oVert.index       
#         self.oMeshMorph.Close()

        #=== Create our own local copy of the breast mesh for breast morphs ===
        ###OBS
#         if (sSex != "Man"):
#             oMeshSrcBreast = CMesh.Create(self.oBodyBase.sMeshSource + "-Breast")          ###WEAK: Create another ctor?
#             self.oMeshSrcBreast = CMesh.CreateFromDuplicate(self.oBodyBase.sMeshPrefix + "Breast", oMeshSrcBreast)        
#             self.oMeshSrcBreast.SetParent(G.C_NodeFolder_Game)
#             self.oMeshSrcBreast.Hide()    
# 
#         nSize = 1.75
#         self.Breasts_ApplyMorph('RESIZE', 'Nipple', 'Center', 'Wide', (nSize,nSize,nSize,0), None)     ###NOW###  ###HACK!



#     def OnChangeBodyMode(self, sBodyBaseMode):  # Blender-side equivalent of Unity's CBodyBase.OnChangeBodyMode().  Switches between configure / play mode for this body.
#         if (sBodyBaseMode == self.sBodyBaseMode):
#             return
#         print("--- CBodyBase '{}' going from mode '{}' to mode '{}' ---".format(self.sMeshPrefix, self.sBodyBaseMode, sBodyBaseMode))
#         self.sBodyBaseMode = sBodyBaseMode
#         
#         if (self.sBodyBaseMode == "MorphBody"):         # If we enter MorphBody mode and body is created destory it
#             if (self.oBody != None):
#                 self.oBody = self.oBody.DoDestroy()     # Destroy the entire gametime body... lots of meshes!
#         elif (self.sBodyBaseMode == "CutCloth"):
#             if (self.oBody != None):
#                 self.oBody = self.oBody.DoDestroy()     # Destroy the entire gametime body... lots of meshes!
#         elif (self.sBodyBaseMode == "Play"):
#             if (self.oBody == None):
#                 self.oBody = CBody(self)                # Create a game-time body.  Expensive operation!
#         else:
#             raise Exception("###EXCEPTION in CBodyBase.OnChangeBodyMode().  Unrecognized body mode " + sBodyBaseMode)
#         return "OK"  # Unity called so we must return something it recognizes like a string ###IMPROVE: Remove this dumb requirement and transfer null too!
















###OBS: In old CBody
###LAST: Can now have Unity-2-Blender morph flow...
# Moving breasts down cause morph result mesh to break at seams... because of split of verts for Unity.
    # Does latest Unity still need that??  Can it have double UVs?
    # Could also import body via FBX and just move verts?  (Would be pain in the ass with detached parts tho)
# Develop pipe to absorb all the morphs into one body shareable with Unity...
# Can either create a new body at every refresh or copy verts every time??  (Could also improve this with a new C++ pipe for shape key block sharing??)
# Also need to serialize CObject get/set and create panel in Unity :)
#        bpy.ops.object.shape_key_add(from_mix=True)         ###INFO: How to 'bake' the current shape key mix into one.  (We delete it at end of this function)



#    bm.verts.index_update()
#    bm.verts.ensure_lookup_table()        ###TODO Needed in later versions of Blender!


### Breast colliders should be in game subfolder!
### UV seams now visible in Unity!
    # Keep extra arg in Client_ConvertMeshForUnity()?
### What is wrong with fucking names?
### Hotspots and breast morphs only in design mode.
### Start working on cloth cutting?
### Unity shows Unity2Blender mesh!
### Apply push-like functionality to keep body col on body verts.

# Missing vert on cloth body collider... can cause problem?
### Had to disable breast colliders because of inter-breast collision!  Define groups!

###BUGS
# ? Some weird shimmer around rim!

###IDEAS
# Two breasts now, have to have entity to manage both (e.g. hotspot, etc)>

###OLD
# Now  implement system for all detached parts to update their verts when morph body changed!  (Same with body)
# Create different hotspot for softbodies based on type and game mode (e.g. morph ops there??)

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












#         #=== Update the bone positions from particle to shape position ===  (We need for envelopes to work properly to re-skin with bones set to particle position but Unity needs shape position for much faster performance.  Convert here)
#         SelectObject(self.oArmNode.name)                          # Must select armature Blender object to modify 'edit_bones' collection...
#         bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
#         for nParticleBoneID in aMapBoneNewPos:
#             vecShapeCenter = aMapBoneNewPos[nParticleBoneID]
#             sNameBone = G.C_Prefix_DynBones + str(nParticleBoneID)
#             oBone = self.oArm.edit_bones[sNameBone]
#             oBone.head = vecShapeCenter
#             oBone.tail = oBone.head - Vector((0,0.001,0))
#         bpy.ops.object.mode_set(mode='OBJECT')



#import Client
#import CFlexSkin
#import CHoleRig
#import CSoftBody
#import CCloth
#import CClothSrc

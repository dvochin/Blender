# ###NOW### OBS!  Merge?
# 
# #- Init
# #  - We don't need to cap and create backmesh
# #  - Constructor for FlexSkin does everything...  separates, produces rim, thickens the mesh, creates its array for Unity to download 
# #- Improve: Current FlexSkin based on distance search... replace with geometry search with 'get more'
# #- IDEA to find close geometry to any vert: Expand selection to faces then convert to vert sel again!
# #- Remember: pass in particle spacing!
# #- From Unity for FlexSkin: call ctor, obtain presentation mesh and FlexSkin arrays and complete.
#     #- The bits about FindPinnedFlexParticles skipped.
# #- Remove old FlexSkin files everywhere
# 
# import bpy
# import sys
# import bmesh
# import array
# import struct
# from math import *
# from mathutils import *
# from bpy.props import *
# 
# from gBlender import *
# import G
# import CBody
# from CMesh import *
# 
# 
# 
# class CFlexSkin:        ###OBS: Now part of CSoftBody
#     def __init__(self, oBody, sFlexSkinPart, nParticlesPerShape):
#         self.oBody                  = oBody             # The back-reference to the owning body.
#         self.sFlexSkinPart          = sFlexSkinPart     # The name of the soft body part.  (e.g. "BreastL", "BreastR", "Penis")  This is our key in self.oBody.aSoftBodies[self.sFlexSkinPart]
#         self.oMeshFlexSkin          = None              # The flexskin surface mesh itself.  Visible in Unity and moved by Flex flexskin simulation via its internal solid tetramesh.
#         self.aShapeVerts            = CByteArray()      # Array of which vert / particle is also a shape
#         self.aShapeParticleIndices  = CByteArray()      # Flattened array of which shape match to which particle (as per Flex softbody requirements)
#         self.aShapeParticleCutoffs  = CByteArray()      # Cutoff in 'aShapeParticleIndices' between sets defining which particle goes to which shape. 
# 
#         print("=== CFlexSkin.ctor()  self.oBody = '{}'  self.sFlexSkinPart = '{}'  ===".format(self.oBody.oBodyBase.sMeshPrefix, self.sFlexSkinPart))
#         
#         #=== Prepare naming of the meshes we'll create and ensure they are not in Blender ===
#         sNameFlexSkin = self.oBody.oBodyBase.sMeshPrefix + "FS-" + self.sFlexSkinPart         # Create name for to-be-created detach mesh and open the body mesh
#         DeleteObject(sNameFlexSkin)
#  
# #         #=== Obtain the to-be-detached vertex group of name 'self.sFlexSkinPart' from the combo mesh that originally came from the source body ===
# #         nVertGrpIndex_DetachPart = self.oBody.oMeshBody.GetMesh().vertex_groups.find(G.C_VertGrp_CSoftBody + self.sFlexSkinPart)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
# #         oVertGroup_DetachPart = self.oBody.oMeshBody.GetMesh().vertex_groups[nVertGrpIndex_DetachPart]
# #         self.oBody.oMeshBody.GetMesh().vertex_groups.active_index = oVertGroup_DetachPart.index
# #         self.oBody.oMeshBody.Open()
# #         bpy.ops.object.vertex_group_select()    # Select only the verts that are to be separated from skinned body to form the new flexskin
# # 
# #         #=== Split and separate the flexskin from the composite mesh ===
# #         bpy.ops.mesh.split()        # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
# #         bpy.ops.mesh.separate()     # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'flexskin'
# #         bpy.ops.object.mode_set(mode='OBJECT')      ###LEARN: Manually going to object to handle tricky split below...
# # 
# #         #=== Name the newly created mesh as the requested 'detached flexskin' ===      
# #         bpy.context.object.select = False           ###LEARN: Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
# #         bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
# #         self.oMeshFlexSkin = CMesh.CMesh(sNameFlexSkin, bpy.context.scene.objects.active, None)          # The just-split mesh becomes the flexskin mesh! 
# 
# 
# 
#         self.oMeshFlexSkin = CMesh.CreateFromExistingObject(self.sFlexSkinPart)      ###HACK!!!! 
#         bmFlexSkin = self.oMeshFlexSkin.Open()
# 
#         #=== Iterate through all verts to populate either aShapeVerts or aShapeParticleIndices collections for Unity ===
#         for oVertShape in bmFlexSkin.verts:
#             if oVertShape.select == True:                            # Iterate through all shapes to find the closest particles to form a runtime softbody connection too
#                 #print("--- FlexSkin shape {:3d} ---".format(oVertShape.index))
#                 self.aShapeVerts.AddInt(oVertShape.index)
#                 
#                 #=== Find the 'nParticlesPerShape' closest verts/particles to each shape === 
#                 aDistToVert = []
#                 for oVertParticle in bmFlexSkin.verts:
#                     aDistToVert.append((oVertParticle.index, (oVertShape.co - oVertParticle.co).length_squared)) 
#                 aDistToVertSorted = sorted(aDistToVert, key=lambda JustAName: JustAName[1])     ###LEARN: How to sort by value.  See https://wiki.python.org/moin/HowTo/Sorting
#                 aDistToVertSortedTrimmed = aDistToVertSorted[:nParticlesPerShape]       # Trim to just the # of (closest) particles/verts we need for this shape 
#                 
#                 #=== Push in the list of particles connected to this shape in the flattened array Flex requires ===
#                 for oVertAndDist in aDistToVertSortedTrimmed:
#                     self.aShapeParticleIndices.AddInt(oVertAndDist[0])
#                     #print("-- Shape {:3d} to Part {:3d} -  Dist {:6f}".format(oVertShape.index, oVertAndDist[0], oVertAndDist[1]))
#                     
#                 #=== Push in our split point in self.aShapeParticleIndices so Flex can unflatten the aShapeParticleIndices flat array and properly match what particle connects to which shape === 
#                 self.aShapeParticleCutoffs.AddInt(len(self.aShapeParticleIndices))
#         
#         self.aShapeVerts.CloseArray()
#         self.aShapeParticleIndices.CloseArray()
#         self.aShapeParticleCutoffs.CloseArray() 
# 
#         self.oMeshFlexSkin.Close()
# 
# 
#     def DoDestroy(self):
#         self.oMeshFlexSkin.DoDestroy()
       

#     def SerializeCollection_aShapeVerts(self):
#         return Stream_SerializeCollection(self.aShapeVerts)
#     
#     def SerializeCollection_aShapeParticleIndices(self):
#         return Stream_SerializeCollection(self.aShapeParticleIndices)
#             
#     def SerializeCollection_aShapeParticleCutoffs(self):
#         return Stream_SerializeCollection(self.aShapeParticleCutoffs)
            
            
            
            
            
            
            
            
# class CFlexSkin_OBSOLETE:
#     ###OBSOLETE: Old attempt to drive vagina verts directly from triangulated springs: Looked bad because verts get all crunched together
#     
#     def __init__(self, oBody, sFlexSkinPart):
#         self.oBody                  = oBody             # The back-reference to the owning body.
#         self.sFlexSkinPart          = sFlexSkinPart     # The name of the soft body part.  (e.g. "BreastL", "BreastR", "Penis")  This is our key in self.oBody.aSoftBodies[self.sFlexSkinPart]
#         self.oMeshFlexSkin          = None              # The flexskin surface mesh itself.  Visible in Unity and moved by Flex flexskin simulation via its internal solid tetramesh.
#         self.aShapeVerts             = array.array('H')  # Blank outgoing serializable array of edge verts (used to manually set simulated verts to match normal and position of main-body mesh)
#         self.aShapeParticleIndices          = array.array('H')  # Blank outgoing serializable array of non-edge verts (used to drive Flex-simulated particles via a 1:1 spring to skinned particles)
# 
#         print("=== CFlexSkin.ctor()  self.oBody = '{}'  self.sFlexSkinPart = '{}'  ===".format(self.oBody.oBodyBase.sMeshPrefix, self.sFlexSkinPart))
#         
#         #=== Prepare naming of the meshes we'll create and ensure they are not in Blender ===
#         sNameFlexSkin = self.oBody.oBodyBase.sMeshPrefix + "FS-" + self.sFlexSkinPart         # Create name for to-be-created detach mesh and open the body mesh
#         DeleteObject(sNameFlexSkin)
#  
#         #=== Obtain the to-be-detached vertex group of name 'self.sFlexSkinPart' from the combo mesh that originally came from the source body ===
#         nVertGrpIndex_DetachPart = self.oBody.oMeshBody.GetMesh().vertex_groups.find(G.C_VertGrp_CSoftBody + self.sFlexSkinPart)  # vertex_group_transfer_weight() above added vertex groups for each bone.  Fetch the vertex group for this detach area so we can enhance its definition past the bone transfer (which is much too tight)     ###DESIGN: Make area-type agnostic
#         oVertGroup_DetachPart = self.oBody.oMeshBody.GetMesh().vertex_groups[nVertGrpIndex_DetachPart]
#         self.oBody.oMeshBody.GetMesh().vertex_groups.active_index = oVertGroup_DetachPart.index
#         self.oBody.oMeshBody.Open()
#         bpy.ops.object.vertex_group_select()    # Select only the verts that are to be separated from skinned body to form the new flexskin
# 
#         #=== Split and separate the flexskin from the composite mesh ===
#         bpy.ops.mesh.split()        # 'Split' the selected polygons so both 'sides' have verts at the border and form two submesh
#         bpy.ops.mesh.separate()     # 'Separate' the selected polygon (now with their own non-manifold edge from split above) into its own mesh as a 'flexskin'
#         bpy.ops.object.mode_set(mode='OBJECT')      ###LEARN: Manually going to object to handle tricky split below...
# 
#         #=== Name the newly created mesh as the requested 'detached flexskin' ===      
#         bpy.context.object.select = False           ###LEARN: Unselect the active object so the one remaining selected object is the newly-created mesh by separate above
#         bpy.context.scene.objects.active = bpy.context.selected_objects[0]  # Set the '2nd object' as the active one (the 'separated one')        
#         self.oMeshFlexSkin = CMesh.CMesh(sNameFlexSkin, bpy.context.scene.objects.active, None)          # The just-split mesh becomes the flexskin mesh! 
# 
#      
#         #===== Process the just-separated flexskin by finding edge and non-edge verts for Unity =====
#         #=== Isolate the boundary verts so we can tell Unity which non-edge verts to Flex-simulate and which edge verts to use for edge position / normal for seamless connection with main skinned body ===
#         bmFlexSkin = self.oMeshFlexSkin.Open()
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
#         bpy.ops.mesh.select_all(action='SELECT')
#         bpy.ops.mesh.region_to_loop()       # This will select only the edges at the boundary of the cutout polys
#         bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
# 
#         #=== Iterate through all verts to populate either aShapeVerts or aShapeParticleIndices collections for Unity ===
#         for oVert in bmFlexSkin.verts:
#             if oVert.select == True:
#                 self.aShapeVerts.append(oVert.index)
#                 #print("- FlexSkin vert {:4d} on EDGE".format(oVert.index))
#             else:
#                 self.aShapeParticleIndices.append(oVert.index)
#                 #print("- FlexSkin vert {:4d} on NON EDGE".format(oVert.index))
#                 
#         self.oMeshFlexSkin.Close()
# 
# 
#     def SerializeCollection_aVertsEdge(self):
#         return Stream_SerializeCollection(self.aShapeVerts)
#     
#     def SerializeCollection_aVertsNonEdge(self):
#         return Stream_SerializeCollection(self.aShapeParticleIndices)
#                         
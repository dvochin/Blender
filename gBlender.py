###NEW16:
# Could use layers.shape to obtain shape key pos?  See https://www.blender.org/api/blender_python_api_2_63_2/bmesh.html4
	# Can also use from_mesh(mesh, use_shape_key=False, shape_key_index=0) ??



### NEXT ###
### Reconsider these other 'GetMesh' functions.  Always call getMesh and get extra arrays in a common method!!!

### TODO ###
# Proportional editing has the 'connected mode' that goes from edge distance!!!
	# REWRITE breast morph!! Do we really need all that complexity???
# Use '-' throughout!

### LATER ###
# Annoying to have to reboot blender and Client at each run... boost memory handles freed??

### PROBLEMS ###
# Boolean cuts the other way if center causes mesh to rebuild normals differently is too high
	# Auto-detect when 'bad border vertices' for each cutter remain after boolean cut and flip!

### PROBLEMS ASSETS ###
#+ Bones are still 100x!  Keep em like this???
#- Yellow tint on body ridiculous... rebalance colors and reblend cock
# Eyelashes not transparent hidden
#bpy.ops.mesh.symmetry_snap()		 ###LEARN: This call instrumental in fixing mesh imperfections from DAZ... integrate it in flow as we get closer to DAZ imports
# Note that code won't work if most source meshes have hidden geometry... force unhide all throughout??

### PROBLEMS? ###
#? Cooked cloth still contains vertex groups!
# Still get small holes in capping of penis... Enough to throw off Flex tetra creation?
#? Penis at rotation x = 0.	 OK???
# 3DView MUST be called with rotate about 3D cursor with it at origin... iterate through view3d to fix this!  (Probably other settings as well!)
# Problem with penis vert groups! Selects a bunch extra -> Fixed by sorting verts!!
#? Problem upon dll start with boost shared memory assertion only in DEBUG???
#? Rethink deletion: Blender gets python command, deletes blender object, our C++ code deletes shared mem, etc
#? CBMesh objects created from Client are highly transient??
	
### IDEAS ###
# See bmesh.select_mode, select_flush() and select_flush_mode()!!!
# def v3d_refresh(ctx): for a in ctx.window.screen.areas: if a.type == 'VIEW_3D': for r in a.regions: r.tag_redraw() a.tag_redraw()
# Consider ditching all skinning info on all meshes (including intermediate bodies) and re-skin by proximity on source DAZ body at the very last step
# For access to DAZ's morphing library (useful for face!) it would be great to be able to map their verts to our own modified ones by our own algorithm
#+++ Density of all colliders in Flex should apply what we learned between cloth and colliders??? +++
# Different colors for each curve pins & curves
#- For easier straps: Implement a 'repel' feature where user-placed verts of current spline will 'push' verts of other splines?
# For body collider also ship to Flex some 'bone-based' rough collider for the arms, legs and neck to act as a failsafe when the accurate colliders fail

### DISCUSSION ###
#+ For clothing, ditching half, fixing mesh at x=0, mirror and then edit would enable fast morphing of body + clothing!
	# All this morphing of cloth with body is of limited use however as we have 2 cloth sims!
		# We have far superior solution with clothing sim during morph... also having to force bodysuits to be mirrored is much too limiting!
#+ Proportional connected editing amazing!!	 Can morph tits increadibly well!  Can also morph clothing around breasts IF it is mirrored geometry (much too limiting for us!)
	# We must however also morph the original body or else excessive changes in chapes will introduce skinning errors (for example under breast fold)
		# So we must now modify body original at runtime to succesfully morph!!	 Have to create yet-another mesh copy!!
#+ Live unwrap: changing seams changes UVs!!!

### DESIGN ###
# Do we trim verts on useless material on base woman or not??
# Place to enter border GUI info... and save where??
	# Border global settings with a % override for individual borders...
# Cloth fitting and applying border after?
	# Do we revive Flex cloth fit??
# Make sure all calls from client begin with gBL_

### LEARN ###
# Procedure to transfer a texture from one UV set to another. (From technique adapted from http://vimeo.com/15223387)		

### WISHLIST ###
# Now that pins are created from curve it would be nice to specify # of points on curve!



import bpy
import sys
import array
import bmesh
import struct
from math import *
from mathutils import *

import G
import Curve
import SourceReloader
import Breasts
import CBody

#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	GLOBAL VARIABLES
#---------------------------------------------------------------------------	

g_aSharedMeshes = {}			###OBS? Important map of string-to-bmesh object to hold the important bmesh reference for all bmesh requested by Client in Unity_GetMesh() until released by gBL_ReleaseMesh()

#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	TOP LEVEL
#---------------------------------------------------------------------------	

def gBL_Initialize():		###OBS17: !!
	print("\n********** gBL_Initialize **********")
	###DESIGN: Debug flag of any use??? bpy.types.Scene.IsDebuggable = bpy.props.BoolProperty(name="IsDebuggable", default=False)


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	UTILITIES
#---------------------------------------------------------------------------	

#---------------------------------------------------------------------------	COMMON OPERATIONS
def SelectAndActivate(sNameObject, bCheckForPresence=True):	 #=== Goes to object mode, deselects everything, selects and activates object with name 'sNameObject'
	if bpy.ops.object.mode_set.poll():			###LEARN: In some situations we cannot change mode (like when selecting a linked object from another file)
		bpy.ops.object.mode_set(mode='OBJECT')	###BUG: Deselect below won't unselect hidden objects!  WTF???
	bpy.context.scene.objects.active = None		###CHECK!!! 
	bpy.ops.object.select_all(action='DESELECT')###LEARN: Good way to select and activate the right object for ops... ***IMPROVE: Possible??
	oObj = None
	if sNameObject in bpy.data.objects:			###LEARN: How to test if an object exists in Blender
		oObj = bpy.data.objects[sNameObject]
		oObj.hide_select = False				###LEARN: We can't select it if hide_select is set!
		oObj.hide = False
		oObj.select = True
		bpy.context.scene.objects.active = oObj
		if bpy.ops.object.mode_set.poll():
			bpy.ops.object.mode_set(mode='OBJECT')
	else:
		if (bCheckForPresence):
			raise Exception("###EXCEPTION: SelectAndActivate() cannot find object '{}'".format(sNameObject))
	return oObj

def DeleteObject(sNameObject):
	#if (oObj != None):
	#	print("<<< Deleting object '{}' >>>".format(sNameObject))
	#bpy.ops.object.delete(use_global=True)		###BUGFIXED!!! Frequently causes memory corruption on code called from Unity or Blender console... adopt a more gentle way to delete?  (queue up or just rename to temp names?)
	if sNameObject in bpy.data.objects:			###LEARN: This is by *far* the best way to delete in Blender!!
		oObj = bpy.data.objects[sNameObject]
		bpy.data.scenes[0].objects.unlink(oObj)
		bpy.data.objects.remove(oObj)
	return None				# Return convenient None so we can set owning variable in one line

def DuplicateAsSingleton(sSourceName, sNewName, sNameParent, bHideSource):
	#print("-- DuplicateAsSingleton  sSourceName '{}'  sNewName '{}'  sNameParent '{}'".format(sSourceName, sNewName, sNameParent))
	DeleteObject(sNewName)
	
	oSrcO = SelectAndActivate(sSourceName, False)
	if oSrcO is None:
		raise Exception("###EXCEPTION: DuplicateAsSingleton() could not select object '{}'".format(sSourceName))
	bpy.ops.object.duplicate()
	oNewO = bpy.context.object		  # Duplicate above leaves the duplicated object as the context object...
	oSrcO.select = False		   #... but source object is still left selected.  Unselect it now to leave new object the only one selected and active.
	oNewO.name = oNewO.data.name = sNewName				###CHECK: Do we really want to enforce name this way?  Can have side effects?  Should display error??
	oNewO.name = oNewO.data.name = sNewName
	oNewO.hide = oNewO.hide_select = False
	if (bHideSource):
		Util_HideMesh(oSrcO)
	if (sNameParent != None):
		SetParent(oNewO.name, sNameParent)
	return oNewO

def SetParent(sNameObject, sNameParent):
	oChildO = SelectAndActivate(sNameObject, False)
	if sNameParent is not None:							# 'store' the new object at the provided location in Blender's nodes
		if sNameParent not in bpy.data.objects:
			raise Exception("###EXCEPTION: SetParent() could not locate parent node " + sNameParent)
		oChildO.parent = bpy.data.objects[sNameParent]		   ###LEARN: Parenting an object this way would reset the transform applied to object = disaster!  ###CHECK  No longer valid?
# 		oParentO = bpy.data.objects[sNameParent]		###CHECK: Ok now?
# 		oParentO.hide = oParentO.hide_select = False
# 		oParentO.select = True
# 		bpy.context.scene.objects.active = oParentO
# 		bpy.ops.object.parent_set(keep_transform=True)		###LEARN: keep_transform=True is critical to prevent reparenting from destroying the previously set transform of object!!
# 		bpy.context.scene.objects.active = bpy.data.objects[sNameObject]
# 		oParentO.select = False				  
# 		oParentO.hide = oParentO.hide_select = True			###WEAK: Show & hide of parent to enable reparenting... (lose previous state of parent but OK for folder nodes made up of 'empty'!)

def CreateEmptyBlenderNode(sNameNode, sNameParent):			# Create an empty Blender object (a hidden cube in this case) as a child of 'sNameParent'.  Used to create a useful hierarchy in Blender's outliner so tons of unrelated objects don't have to be under the same parent
	bpy.ops.object.empty_add(type='CUBE', radius=0.01)		# Create an empty we will reparent to game folder
	oNodeNew = bpy.context.object						 	# Obtain reference empty we just created above
	oNodeNew.parent = bpy.data.objects[sNameParent]			# Set as child of game folder
	oNodeNew.name = sNameNode	   							# Name it (twice so it sticks) 
	oNodeNew.name = sNameNode
	oNodeNew.location = Vector((0, 0, 0))				 	# Set it to origin 
	bpy.context.scene.objects.active = None					###LEARN: If we don't deactivate it, copies will also copy this object!
	bpy.ops.object.select_all(action='DESELECT')
	oNodeNew.hide = oNodeNew.hide_render = oNodeNew.hide_select = True  # Hide & deactivate it in every way
	return oNodeNew

	 
def AssertFinished(sResultFromOp):	###IMPROVE: Use this much more!
	if (sResultFromOp != {'FINISHED'}):
		raise Exception("###EXCEPTION: Operation returned: ", sResultFromOp)


#---------------------------------------------------------------------------	VIEW 3D
def GetView3dSpace():						   # Returns the first 3dView.	Important to set parameters of the view such as pivot_point
	for oWindow in bpy.context.window_manager.windows:			###IMPROVE: Find way to avoid doing four levels of traversals at every request!!
		oScreen = oWindow.screen
		for oArea in oScreen.areas:
			if oArea.type == 'VIEW_3D':
				for oSpace in oArea.spaces:
					if oSpace.type == 'VIEW_3D':
						return oSpace
	raise Exception("###EXCEPTION: in GetView3dRegion().  Could not find View3D space!")

def SetView3dPivotPointAndTranOrientation(sPivotPointType, sTranOrientation, bResetCursor):		  # Set the first VIEW_3D space to 'sPivotPointType'  (Must be one of 'BOUNDING_BOX_CENTER', 'CURSOR', 'INDIVIDUAL_ORIGINS', 'MEDIAN_POINT', 'ACTIVE_ELEMENT') and sTranOrientation on of 'GLOBAL', 'LOCAL', 'NORMAL', 'GIMBAL', 'VIEW'
	oSpace = GetView3dSpace()						###WEAK: Sets the first one... but if multiple 3D_VIEW are defined do we need to set all? (Which one is code using in this case?  Last user-activated one??)
	oSpace.pivot_point = sPivotPointType			###TODO ###SOON: Insert this everywhere!!
	oSpace.transform_orientation = sTranOrientation
	if bResetCursor:
		bpy.context.scene.cursor_location = Vector((0,0,0))


def AssembleOverrideContextForView3dOps():
	#=== Iterates through the blender GUI's windows, screens, areas, regions to find the View3D space and its associated window.  Populate an 'aContextOverride context' that can be used with bpy.ops that require to be used from within a View3D (like most addon code that runs of View3D panels)
	# Tip: If your operator fails the log will show an "PyContext: 'xyz' not found".  To fix stuff 'xyz' into the override context and try again!
	for oWindow in bpy.context.window_manager.windows:			###IMPROVE: Find way to avoid doing four levels of traversals at every request!!
		oScreen = oWindow.screen
		for oArea in oScreen.areas:
			if oArea.type == 'VIEW_3D':							###LEARN: Frequently, bpy.ops operators are called from View3d's toolbox or property panel.	 By finding that window/screen/area we can fool operators in thinking they were called from the View3D!
				for oRegion in oArea.regions:
					if oRegion.type == 'WINDOW':				###LEARN: View3D has several 'windows' like 'HEADER' and 'WINDOW'.	Most bpy.ops require 'WINDOW'
						#=== Now that we've (finally!) found the damn View3D stuff all that into a dictionary bpy.ops operators can accept to specify their context.  I stuffed extra info in there like selected objects, active objects, etc as most operators require them.	(If anything is missing operator will fail and log a 'PyContext: error on the log with what is missing in context override) ===
						aContextOverride = {'window': oWindow, 'screen': oScreen, 'area': oArea, 'region': oRegion, 'scene': bpy.context.scene, 'edit_object': bpy.context.edit_object, 'active_object': bpy.context.active_object, 'selected_objects': bpy.context.selected_objects}	# Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
						#print("-AssembleOverrideContextForView3dOps() created override context: ", aContextOverride)
						return aContextOverride
	raise Exception("###EXCEPTION: AssembleOverrideContextForView3dOps() could not find a VIEW_3D with WINDOW region to create override context to enable View3D operators.  Operator cannot function.")


#---------------------------------------------------------------------------	MESH CONVERSION
def Util_ConvertToTriangles():	   # Triangulate the selected mesh so Client only sees triangles (the only thing it can render).  We keep normal preservation on ===
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.quads_convert_to_tris()		###REVIVE: use_beauty=true 
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.object.mode_set(mode='OBJECT')


#---------------------------------------------------------------------------	FINDING VERTS
def Util_FindClosestVert(oMeshO, vecVert, nTolerance):		# Attempts to find the closest vert to 'vecVert' by using 'closest_point_on_mesh()'
	###BUG?  Many uses of this function sabotaged because of flaws in closest_point_on_mesh()!  Will find a vert up to .015 away (1.5cm!)  (Still present in latest Blender?)
	###LEARN: Alternatives at http://blenderartists.org/forum/archive/index.php/t-229112.html
	oMesh = oMeshO.data
	aClosestPtResults = oMeshO.closest_point_on_mesh(vecVert, nTolerance)		 # Return (location, normal, face index)  ###LEARN: Must be called in object mode (unfortunately) or we'll get an error "object has no mesh data"!
	bFound = aClosestPtResults[0]			###NOTE: Returns (result, location, normal, index)
	nPolyClosest = aClosestPtResults[3]
	if bFound == False:
		###PROBLEM: closest_point_on_mesh() has been shown to FAIL finding mesh containg verts that were clearly at a searched-for position!
		#=== Try to find vert in a brute-force iteration... SLOW!!! ===
		for oVert in oMesh.vertices:
			nDist = (vecVert - oVert.co).magnitude		###OPT: MagnitudeSqr for performance??
			if (nDist <= nTolerance):					###IMPROVE?: Return the closest one, not just the first within tolerance?
				print("NOTE: Util_FindClosestVert() could not efficiently find vert close to {}.  Found vert at {} through slow implementation at distance {}".format(vecVert, oVert.co, nDist))
				return oVert.index, nDist, oVert.co
		print("WARNING: Util_FindClosestVert() could not find vert close to {} at tolerance {}".format(vecVert, nTolerance))
		bpy.context.scene.cursor_location = oMeshO.matrix_world * vecVert	###LEARN: How to convert from local vert to global.
		return -1, -1, None						# Could not find through slow approach either... return 'not found'
	
	#print(type(nPolyClosest), nPolyClosest, aClosestPtResults)
	
	oPolyClosest = oMesh.polygons[nPolyClosest]
	nDistMin = sys.float_info.max
	for nVert in oPolyClosest.vertices:
		oVert = oMesh.vertices[nVert]
		nDist = (vecVert - oVert.co).magnitude		###OPT: MagnitudeSqr for performance??
		if nDistMin > nDist:
			nDistMin = nDist
			nVertClosest = nVert
			vecVertClosest = oVert.co
	return nVertClosest, nDistMin, vecVertClosest

def Util_FindClosestMirrorVertInGroups(bm, aVerts1, aVerts2):			# Find the closest vert to every vert in aVerts1 in aVerts2.  Assumes mesh is mathematically symmetrical
	aVertsMirrorX = []
	for oVert1 in aVerts1:
		vecVertMirrorX = oVert1.co.copy()
		vecVertMirrorX.x = -vecVertMirrorX.x
		nDistMin = sys.float_info.max
		oVertClosest = None
		for oVert2 in aVerts2:
			nDist = (oVert2.co - vecVertMirrorX).length_squared			###LEARN: Faster equivalent than 'magnitude' as we don't really need sqrt()
			if nDistMin > nDist:
				nDistMin = nDist
				oVertClosest = oVert2
		aVertsMirrorX.append(oVertClosest)
		if nDistMin > 0.000001:
			print("-WARNING: Vert {:5d} has MirrorX at {:5d} with tolerance {:7.6f}".format(oVert1.index, oVertClosest.index, nDistMin))
	return aVertsMirrorX


#---------------------------------------------------------------------------	VERT CALCULATIONS
def Util_CalcSurfDistanceBetweenTwoVertGroups(bm, aVerts1, aVerts2):	 # Calculates the minimum surface distance between the verts in aVerts1 and the verts in aVerts2
	aDistToCenters = {}
	nDistMax_All = 0
	for oVert1 in aVerts1:				   # Iterate through all verts of the mesh to store their distance to the requested vert
		nDistPathMin = sys.float_info.max
		for oVert2 in aVerts2:			   # Iterate through all center verts to see which is closest to nVert
			nDistPath = Util_CalcSurfDistanceBetweenTwoVerts(bm, oVert1, oVert2)
			if (nDistPathMin > nDistPath):
				nDistPathMin = nDistPath
		aDistToCenters[oVert1.index] = nDistPathMin
		#print("- Vert {:5d} has min surf dist {:7.4f}".format(oVert1.index, nDistPathMin))
		if (nDistMax_All < nDistPathMin):
			nDistMax_All = nDistPathMin
	bpy.ops.mesh.select_all(action='DESELECT')
	print("--- Util_CalcSurfDistanceBetweenTwoVertGroups() updated surface distance array with max distance {:6.4f} ---".format(nDistMax_All))
	return aDistToCenters, nDistMax_All
	

def Util_CalcSurfDistanceBetweenTwoVerts(bm, oVert1, oVert2):		 # Returns the surface distance using 'select_vertex_path' ###MOVE: To utility?
	if (oVert1.index == oVert2.index):
		return 0
	bpy.ops.mesh.select_all(action='DESELECT')
	oVert1.select_set(True)
	oVert2.select_set(True)
	bpy.ops.mesh.shortest_path_select()
	aEdgesOnPath = [oEdge for oEdge in bm.edges if oEdge.select]		###OPT!!: Slow!
	nDistPath = 0
	for oEdge in aEdgesOnPath:		  # Iterate through the edges of the shortest path to add the lenght of each edge
		nDistEdge = oEdge.calc_length()
		nDistPath = nDistPath + nDistEdge
	#print("Vert {:5d} to vert {:5d} surface dist = {:6.4f}".format(oVert1.index, oVert2.index, nDistPath))
	return nDistPath	

#---------------------------------------------------------------------------	MISC
def Util_CreateMirrorModifierX(oMeshO):
	oModMirror = oMeshO.modifiers.new(name="MIRROR", type="MIRROR")
	oModMirror.use_x = True
	oModMirror.use_mirror_merge = True				###IMPROVE: Set range of mirror merge??
	oModMirror.use_mirror_vertex_groups = False
	return oModMirror
			
def Util_TransferWeights(oMeshO, oMeshSrcO):		# Transfer the skinning information from mesh oMeshSrcO to oMeshO
	SelectAndActivate(oMeshO.name, True)
	oMeshSrcO.hide = False			###BUG on hide??
	oModTransfer = oMeshO.modifiers.new(name="DATA_TRANSFER", type="DATA_TRANSFER")
	oModTransfer.object = oMeshSrcO
	oModTransfer.use_vert_data = True
	oModTransfer.data_types_verts = { "VGROUP_WEIGHTS" }
	bpy.ops.object.datalayout_transfer(modifier=oModTransfer.name)	###LEARN: Operation acts upon the setting of 
	AssertFinished(bpy.ops.object.modifier_apply(modifier=oModTransfer.name))
	bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
	bpy.ops.object.vertex_group_clean(group_select_mode='ALL')	# Clean up empty vert groups new Blender insists on creating during skin transfer  ###LEARN: Needs weight mode to work!
	bpy.ops.object.mode_set(mode='OBJECT')
			
def Util_GetMapDistToEdges():			# Returns a map of distances of all manifold verts to non-manifold (edge) verts.  used by Breast and Penis mesh preparation to form a 'scaling ratio array' to dampen scaling of verts around the edges of the mesh
	#=== Enter bmesh edit mode and obtain array of edge verts ===
	bm = bmesh.from_edit_mesh(bpy.context.object.data)				# We assume mesh is already selected, activated and in edit mode
	bpy.ops.mesh.select_non_manifold()
	aVertsEdge = [oVert for oVert in bm.verts if oVert.select]
	bpy.ops.mesh.select_all(action='DESELECT')
	
	#=== Iterate through all mesh verts then to all edge verts to find the minimum distance of all inner verts to the closest edge vert ===
	nDistMax_AllInnerVerts = -sys.float_info.max
	aMapDistToEdges = {}
	for oVert in bm.verts:
		nDistMin = sys.float_info.max
		for oVertEdge in aVertsEdge:
			vecDiff = oVertEdge.co - oVert.co
			nDist = vecDiff.magnitude
			if (nDistMin > nDist):
				nDistMin = nDist
		aMapDistToEdges[oVert.index] = nDistMin
		if nDistMax_AllInnerVerts < nDistMin:
			nDistMax_AllInnerVerts = nDistMin
		#print("Vert {:5d} = dist {:6.4f}".format(oVert.index, nDistMin))
	#print("Util_GetMapDistToEdges Calculated mesh distance array with max dist %f" % (nDistMax_AllInnerVerts))

	return aMapDistToEdges, nDistMax_AllInnerVerts		###WEAK: Only one consumer of this call now (Breast) -> move back??

def Util_UnselectMesh(oMeshO):
	if bpy.ops.object.mode_set.poll():
		bpy.ops.object.mode_set(mode='OBJECT')

def Util_HideMesh(oMeshO):
	Util_UnselectMesh(oMeshO)
	oMeshO.select = False			###LEARN: We *must* unselect an object before hiding as group unselect wont unselect those (causing problems with duplication) 
	if (bpy.context.scene.objects.active == oMeshO):
		bpy.context.scene.objects.active = None
	oMeshO.hide = True

def gBL_Util_RemoveGameMeshes():
	print("<<<<< gBL_Util_RemoveGameMeshes() removing game meshes...>>>>>")
	oNodeFolderGame = bpy.data.objects[G.C_NodeFolder_Game]
	for oNodeO in oNodeFolderGame.children:
		DeleteObject(oNodeO.name)			 

def gBL_Util_HideGameMeshes():
	print("<<< gBL_Util_RemoveGameMeshes() removing game meshes...>>>")
	oNodeFolderGame = bpy.data.objects[G.C_NodeFolder_Game]
	for oNodeO in oNodeFolderGame.children:
		Util_HideMesh(oNodeO)
	#bpy.data.objects["WomanA" + G.C_NameSuffix_Face].hide = False			###HACK
					
def Util_RemoveProperty(o, sNameProp):		# Safely removes a property from an object.
    if sNameProp in o:
        del o[sNameProp]
    
def Util_PrintMeshVerts(sDebugMsg, sNameMesh, sNameLayer=None):
	print("\n=== PrintMeshVert for mesh '{}' and layer '{}' for '{}'".format(sNameMesh, sNameLayer, sDebugMsg))
	oMeshO = SelectAndActivate(sNameMesh, True)
	bm = bmesh.new()
	bm.from_mesh(oMeshO.data)
	if (sNameLayer != None):
		oLayer = bm.verts.layers.int[sNameLayer]
	nLayer = -1
	for oVert in bm.verts:
		vecPos = oVert.co
		if (sNameLayer != None):
			nLayer = oVert[oLayer]
		print("- Vert {:4d} = {:8.5f} {:8.5f} {:8.5f}   Layer = {:3d}   Sel = {}".format(oVert.index, vecPos.x, vecPos.y, vecPos.z, nLayer, oVert.select))
	print("==========================\n")


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	CLEANUP
#---------------------------------------------------------------------------	

def Cleanup_RemoveDoublesAndConvertToTris(nDoubleThreshold, bSelectEverything = True, bOpen = True, bClose = True):			# Removes double verts on a whole mesh.
	if bOpen:
		bpy.ops.object.mode_set(mode='EDIT')
	if bSelectEverything:
		bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.quads_convert_to_tris()									###DESIGN: Keep in here??
	bpy.ops.mesh.remove_doubles(threshold=nDoubleThreshold, use_unselected=True)		###LEARN: 'use_unselected' not doing anything!!
	if bSelectEverything:
		bpy.ops.mesh.select_all(action='DESELECT')
	if bClose:
		bpy.ops.object.mode_set(mode='OBJECT')

def Cleanup_RemoveDoublesAndConvertToTrisAndNonManifold(nRepeats, nDoubleThreshold, nEdgesThreshold):	 ###OBS? Our most important (and simplest) cleaning technique... used throughout to prevent boolean from failing!
	print("- Cleanup_RemoveDoublesAndConvertToTris with {} threshold, {}  edge hunt and {} repeats.".format(nDoubleThreshold, nEdgesThreshold, nRepeats))
	for nRepeat in range(nRepeats):	 # Do this cleanup a few times as each time the non-manifold edges clear up without us needing to go near inside verts...
		bpy.ops.mesh.select_non_manifold(extend=False)	# Select the edges of the cloth...
		bpy.ops.mesh.edges_select_(ness=radians(nEdgesThreshold))  ###TUNE: Quite aggressive angle!
		bpy.ops.mesh.remove_doubles(threshold=nDoubleThreshold, use_unselected=False)  ###TUNE: Aggressive remove double!	 # Remove some of the worst small details caused by cuts.  Bigger than 0.0025 and we start damaging open edges!

def Cleanup_RemoveDegenerateFaces(oObj, nCuttoffAngle):	 ###OBS? Removes faces with tiny angles in them -> likely degenerate faces that can throw off boolean
	SelectAndActivate(oObj.name)
	nDeletedFaces = 0
	Cleanup_RemoveDoublesAndConvertToTris(0.003)				###TUNE: Remove the worst of the super-close geometry to help remove degenerate stuff from boolean cuts

	###NOTE: Used to have this in remove doubles! bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	
	aVerts = oObj.data.vertices
	for oPoly in oObj.data.polygons:
		aVertPolys = []
		for nRepeat in range(2):  # Add vertices twice to the array so next loop can easily roll around to calculate angles...
			for nVert in oPoly.vertices:
				aVertPolys.append(aVerts[nVert].co)
		
		for nVert in range(len(oPoly.vertices)):
			vec10 = aVertPolys[nVert + 1] - aVertPolys[nVert + 0]
			vec12 = aVertPolys[nVert + 1] - aVertPolys[nVert + 2]
			nAngle = vec10.angle(vec12) * 180 / pi
			if (nAngle < nCuttoffAngle):
				oPoly.select = True
				print("--- Deleted face with angle: {:4.2f} and area: {:6.2f}".format(nAngle, 1000000 * oPoly.area))
				nDeletedFaces = nDeletedFaces + 1
				break
			
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.delete(type='FACE')
	bpy.ops.mesh.select_loose(extend=False)
	bpy.ops.mesh.delete(type='FACE')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
	bpy.ops.object.mode_set(mode='OBJECT')
	print("-- Cleanup_RemoveDegenerateFaces with angle {} deleted {} faces".format(nCuttoffAngle, nDeletedFaces))

def Cleanup_DecimateEdges(oObj, nness, nRatioOfFacesToKeep):  ###OBS? ###IMPROVE: Good concept but won't help boolean like merge_double approach!!
	SelectAndActivate(oObj.name)
	
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_non_manifold(extend=False)	# Select the edges of the cloth...
	bpy.ops.mesh.edges_select_(ness=radians(nness))	 ###TUNE: Quite aggressive angle!
	bpy.ops.mesh.select_more()
	oVertGroup_Decimate = oObj.vertex_groups.new(name="DECIMATE")
	bpy.ops.object.vertex_group_assign(new=False)
	bpy.ops.object.mode_set(mode='OBJECT')
	
	oObj.update_from_editmode()	 ###LEARN 2.67+!
	nFacesSelected = len([oPoly for oPoly in oObj.data.polygons if oPoly.select])  ###LEARN: Shortest line to iterate through a set and do something...
	nFacesInSelToRemove = int(nFacesSelected * (1 - nRatioOfFacesToKeep))
	nFaces = len(oObj.data.polygons)
	nRatioFacesToKeepOverTotal = (nFaces - nFacesInSelToRemove) / nFaces
	 
	oModCleanup_Decimate = oObj.modifiers.new('DECIMATE', 'DECIMATE')
	oModCleanup_Decimate.ratio = nRatioFacesToKeepOverTotal
	oModCleanup_Decimate.vertex_group = oVertGroup_Decimate.name
	oModCleanup_Decimate.use_collapse_triangulate = True  ###CHECK: Triangulate as this is what Client needs?
	AssertFinished(bpy.ops.object.modifier_apply(modifier=oModCleanup_Decimate.name))
	print("- Cleanup_DecimateEdges to remove {} faces from selected {} from total {} for ratio of {} results in mesh with {} faces".format(nFacesInSelToRemove, nFacesSelected, nFaces, nRatioFacesToKeepOverTotal, oModCleanup_Decimate.face_count))

	oObj.vertex_groups.remove(oVertGroup_Decimate)
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='DESELECT') 
	bpy.ops.object.mode_set(mode='OBJECT')

def VertGrp_RemoveNonBones(oMeshO, bCleanUpBones):	 # Remove non-bone vertex groups so skinning normalize & fix below will not be corrupted by non-bone vertex groups  ###IMPROVE: Always clean (remove arg?)
	if (len(oMeshO.vertex_groups) == 0):
		return
	aVertGrpToRemove = []
	for oVertGrp in oMeshO.vertex_groups:
		if oVertGrp.name[0] == G.C_VertGrpPrefix_NonBone:  # Any vertex groups that starts with '_' is a non-bone and has no value for Client
			aVertGrpToRemove.append(oVertGrp)
	for oVertGrp in aVertGrpToRemove:
		oMeshO.vertex_groups.remove(oVertGrp)
	if (bCleanUpBones):
		#bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
		bWasHidden = oMeshO.hide
		if (bWasHidden):
			Util_HideMesh(oMeshO)
		oMeshO.hide = False
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_all(action='SELECT')
		bpy.ops.object.vertex_group_clean(group_select_mode='ALL')	# Clean up empty vert groups new Blender insists on creating during skin transfer
		bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # Limit mesh to four bones each   ###CHECK: Possible our 'non-bone' vertgrp take info away???
		bpy.ops.object.vertex_group_normalize_all(lock_active=False)
		bpy.ops.mesh.select_all(action='DESELECT')
		bpy.ops.object.mode_set(mode='OBJECT')
		if (bWasHidden):
			gBL_Util_Hide(oMeshO)
		
def Cleanup_RemoveMaterials(oMeshO):		# Remove all materials from mesh (to save memory)
	while len(oMeshO.material_slots) > 0:
		bpy.ops.object.material_slot_remove()
	bpy.ops.object.material_slot_add()  	# Add a single default material (captures all the polygons of rim) so we can properly send the mesh over (crashes if zero material)

def Cleanup_RemoveMaterial(oMeshO, sNameMaterialPrefix):		# Remove from oMeshO all material (and their associated verts) that starts with 'sNameMaterialPrefix'
	for oMat in oMeshO.data.materials:
		if oMat.name.startswith(sNameMaterialPrefix):
			nMatIndex = oMeshO.data.materials.find(oMat.name)
			oMeshO.active_material_index = nMatIndex 
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_all(action='DESELECT')
			bpy.ops.object.material_slot_select()
			bpy.ops.mesh.delete(type='FACE')
			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.material_slot_remove()




#---------------------------------------------------------------------------	VertGrp Functions: Helper functions centered on Vertex Groups

def VertGrp_FindByName(oMeshO, sNameVertGrp): 
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)			###LEARN: Can also find directly by oMeshO.vertex_groups[sNameVertGrp] !!! 
	if (nVertGrpIndex != -1):
		oVertGrp = oMeshO.vertex_groups[nVertGrpIndex]
		return oVertGrp 
	else:
		raise Exception("\n###EXCEPTION: VertGrp_FindByName() could not find vert group '{}' in mesh '{}'".format(sNameVertGrp, oMeshO.name))

def VertGrp_SelectVerts(oMeshO, sNameVertGrp, bUnselect=False):			# Select all the verts of the specified vertex group 
	#=== Obtain access to mesh in edit mode, deselect and go into vert mode ===
	###SelectAndActivate(oMeshO.name)			 ###IMPROVE? Select fist??  ###IMPROVE: Move into CMesh!
	bpy.ops.object.mode_set(mode='EDIT')
	if bUnselect == False:
		bpy.ops.mesh.select_all(action='DESELECT') 
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')		 # We go to face mode and expand the verts selected.  This will select all faces that have at least one vert selected...

	#=== Find the requested vertex group and select its vertices ===
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)
	if (nVertGrpIndex != -1):
		oMeshO.vertex_groups.active_index = nVertGrpIndex
		if bUnselect:
			bpy.ops.object.vertex_group_deselect()
		else:
			bpy.ops.object.vertex_group_select()
		oVertGrp = oMeshO.vertex_groups[nVertGrpIndex]
		return oVertGrp 
	else:
		raise Exception("\n###EXCEPTION: VertGrp_SelectVerts() could not find vert group '{}' in mesh '{}'".format(sNameVertGrp, oMeshO.name))

def VertGrp_Remove(oMeshO, sNameVertGrp):			# Removes vertex group 'sNameVertGrp' from specified mesh.  Assumes mesh is selected and opened in edit mode
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)
	if (nVertGrpIndex == -1):
		return "ERROR: VertGrp_Remove() could not find vertex group '" + sNameVertGrp + "'"
	oMeshO.vertex_groups.active_index = nVertGrpIndex
	bpy.ops.object.vertex_group_remove()



#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	STREAM / SERIALIZATION
#---------------------------------------------------------------------------	

def Stream_SerializeArray(oBA, oArray):				 # Serialize an array to client by first sending the length and then the data.	The other side is supposed to know how many bytes each of our array element takes and deserialize the proper number of bytes
	if oArray is not None:
		oBA += struct.pack('L', len(oArray))				# It is assumed that oArray is a bytearray
		oBA += oArray
		###IMPROVE? oBA += G.C_MagicNo_EndOfArray
	else:		 
		oBA += struct.pack('L', 0)

def Stream_SerializeCollection(aCollection):		
	"Send Unity the requested serialized bytearray of the previously-defined collection"
	oBA = CByteArray()
	Stream_SerializeArray(oBA, aCollection.tobytes())
	return oBA.CloseArray()


#---------------------------------------------------------------------------	CByteArray: abstraction of bytearray		###MOVE? To own file?

class CByteArray(bytearray):
	def __init__(self):			###LEARN: Struct.Pack args: b=char B=ubyte h=short H=ushort, i=int I=uint, q=int64, Q=uint64, f=float, d=double, s=char[] ,p=PascalString[], P=void*
		self.bClosed = False
		self.AddUShort(G.C_MagicNo_TranBegin)  
	
	def CloseArray(self):
		if self.bClosed == False:			# Add trailing magic number when array requested from Unity.
			self.AddUShort(G.C_MagicNo_TranEnd)  
			self.bClosed = True;
		return self

	def AddShort(self, nVal):
		if nVal > 32767:
			raise Exception("CByteArray.AddShort() gets out of range value!")
		self += struct.pack('h', nVal)
	
	def AddUShort(self, nVal):
		if nVal > 65535:
			raise Exception("CByteArray.AddUShort() gets out of range value!")
		self += struct.pack('H', nVal)
	
	def AddInt(self, nVal):
		self += struct.pack('i', nVal)

	def AddUInt(self, nVal):
		self += struct.pack('I', nVal)
	
	def AddFloat(self, nVal):
		self += struct.pack('f', nVal)
	
	def AddByte(self, nVal):
		if nVal > 255:
			raise Exception("CByteArray.AddByte() gets out of range value!")
		self += struct.pack('B', nVal)

	def AddVector(self, vec):
		self += struct.pack('fff', vec.x, vec.y, vec.z)
	
	def AddQuaternion(self, quat):
		self += struct.pack('ffff', quat.x, quat.y, quat.z, quat.w)
	
	def AddString(self, sContent):	 ###LEARN: Proper way to pack Pascal string
		sContentEncoded = sContent.encode()
		nLenEncoded = len(sContentEncoded) + 1
		if nLenEncoded > 255:
			raise Exception("Error in CByteArray.AddString().  String '{}' is too long at {} characters".format(sContent, nLenEncoded))
		self += struct.pack(str(nLenEncoded) + 'p', sContentEncoded)  ###LEARN: First P = Pascal string = first byte of it is lenght < 255 rest are chars

	def AddBone(self, oBone):				# Recursive function that sends a bone and the tree of bones underneath it in 'breadth first search' order.	 Information sent include bone name, position and number of children.
		self.AddString(oBone.name)		# Precise opposite of this function found in Unity's CBodeEd.ReadBone()
		self.AddVector(G.VectorB2C(oBone.head))	# Obtain the bone head and convert to client-space (LHS/RHS conversion)		 ###LEARN: 'head' appears to give weird coordinates I don't understand... head_local appears much more reasonable! (tail is the 'other end' of the bone (the part that rotates) while head is the pivot point we need
		self.AddQuaternion(oBone.matrix.to_quaternion())	# Send the bone orientation quaternion.  Needed to properly rotate bones about the axis they were designed for.  ###IMPROVE: Not rotated for Unity axis!  HOW??
		print("-AddBone '{}'   {}   {}".format(oBone.name, oBone.head, oBone.matrix.to_quaternion()))
		self.AddByte(len(oBone.children))
		for oBoneChild in oBone.children:
			self.AddBone(oBoneChild)

	def Unity_GetBytes(self):			# Called from Unity to get a bytearray that Unity can de-serialize.  
		self.CloseArray()				# Close array first (adds end magic number)
		#print(self)
		return self


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	SCENE EVENT HANDLERS
#---------------------------------------------------------------------------	
###OBS??
def Event_OnLoad(scene):			 # Runs on scene_update_post when the user has changed the scene and we need to update our state
	gBL_Initialize()
	
def Event_OnSceneUpdate(scene):				# Runs on scene_update_post when the user has changed the scene and we need to update our state
	print("Event_OnSceneUpdate???")
	


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------		DATA LAYERS	
#---------------------------------------------------------------------------	

def DataLayer_RemoveLayers(sNameObject):				  # Debug cleanup function that removes the custom data layers that can pile up on objects as various functions that create them crash.
	"Remove all int and float custom data layer from mesh"
	oMeshO = SelectAndActivate(sNameObject)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMeshO.data)
	while len(bm.verts.layers.int) > 0:
		oLayer = bm.verts.layers.int[0]
		print("DataLayer: Removing int layer '{}' from mesh '{}'".format(oLayer.name, sNameObject))
		bm.verts.layers.int.remove(oLayer)
	while len(bm.verts.layers.float) > 0:
		oLayer = bm.verts.layers.float[0]
		print("DataLayer: Removing float layer '{}' from mesh '{}'".format(oLayer.name, sNameObject))
		bm.verts.layers.float.remove(oLayer)
	bpy.ops.object.mode_set(mode='OBJECT')

def DataLayer_RemoveLayerInt(sNameObject, sNameLayer):
	"Remove int custom data layer from mesh"
	oMeshO = SelectAndActivate(sNameObject)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMeshO.data)
	if (sNameLayer in bm.verts.layers.int):
		print("DataLayer: Removing int layer '{}' from mesh '{}'".format(sNameLayer, sNameObject))
		bm.verts.layers.int.remove(bm.verts.layers.int[sNameLayer])
# 	for nLayer in range(len(bm.verts.layers.int)):						###IMPROVE? Can select without iteration?
# 		oLayer = bm.verts.layers.int[nLayer]
# 		if (oLayer.name == sNameLayer):
# 			bm.verts.layers.int.remove(oLayer)
# 			return
	bpy.ops.object.mode_set(mode='OBJECT')

def DataLayer_EnumerateInt_DEBUG(sNameObject, sMessage):
	"Enumerate int custom data layers (for debugging)"
	print("--- DataLayer_EnumerateInt_TEMP() at '{}' ---".format(sMessage))
	oMeshO = SelectAndActivate(sNameObject)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMeshO.data)
	for nLayer in range(len(bm.verts.layers.int)):
		oLayer = bm.verts.layers.int[nLayer]
		print("DataLayer:  Mesh '{}'  #{}  Layer '{}'".format(sNameObject, nLayer, oLayer.name))
	bpy.ops.object.mode_set(mode='OBJECT')


def DataLayer_CreateVertIndex(sNameMesh, sNameLayer):
	"Prepare an original untouched mesh for editing by storing its original vert indices in a custom data layer"
	DataLayer_RemoveLayerInt(sNameMesh, sNameLayer)
	oMesh = SelectAndActivate(sNameMesh)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMesh.data)
	print("DataLayer: Creating int layer '{}' on mesh '{}'".format(sNameLayer, sNameMesh))
	oLayVertsSrc = bm.verts.layers.int.new(sNameLayer)
	for oVert in bm.verts:
		oVert[oLayVertsSrc] = oVert.index + G.C_OffsetVertIDs          # We apply an offset so we can differentiate between newly added verts 
	bpy.ops.object.mode_set(mode='OBJECT')


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	####MOVE?
#---------------------------------------------------------------------------	

def Body_InitialPrep(sNameSource):
	"Intial prep for a freshly-imported body.  (Only needs to run once after import)"
	#DataLayer_EnumerateInt_DEBUG(sNameSource, "Body_InitialPrep() BEGIN")
	DataLayer_RemoveLayers(sNameSource)							# Remove all custom data layers
	DataLayer_CreateVertIndex(sNameSource, G.C_DataLayer_VertsSrc)		# Create the VertSrc data layer so we can go from virgin source body to assembled / morph bodies
	#DataLayer_EnumerateInt_DEBUG(sNameSource, "Body_InitialPrep() END")
	Breasts.BodyInit_CreateCutoffBreastFromSourceBody(sNameSource)		# Create the cutoff breast needed for breast morph ops. 
	###SOON: Port all the prep stuff to this top-level call!

# 	#===== BREAST DESIGN-TIME INITIALIZATION =====
# 	#=== Create the right-breast collider from the (authoritative) left breast === 
# 	oMeshBreastRO = DuplicateAsSingleton(sNameSource + "-BreastLCol-Source", sNameSource + "-BreastRCol-Source", None, False)
# 	for oVert in oMeshBreastRO.data.vertices:			# Invert the left breast collider verts to create right collider
# 		oVert.co.x = -oVert.co.x
# 	bpy.ops.object.mode_set(mode='EDIT')
# 	bpy.ops.mesh.select_all(action='SELECT')
# 	bpy.ops.mesh.normals_make_consistent()				# Above inverted the normals.  Recalculate them
# 	bpy.ops.mesh.select_all(action='DESELECT')
# 	bpy.ops.object.mode_set(mode='OBJECT')

# 	#=== Define both breast colliders ===
# 	CBody.SlaveMesh_DefineMasterSlaveRelationship("WomanA", "BreastLCol", 0.000001, bMirror=False, bSkin=False)
# 	CBody.SlaveMesh_DefineMasterSlaveRelationship("WomanA", "BreastRCol", 0.000001, bMirror=False, bSkin=False)
# 
# 	#===== Define cloth colliders =====			###IMPROVE: Auto-generate these from a naming pattern??
# 	CBody.SlaveMesh_DefineMasterSlaveRelationship("WomanA", "BodyColCloth-Top", 0.000001, bMirror=True, bSkin=True)


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	APP GLOBAL TOP LEVEL
#---------------------------------------------------------------------------	

####OBS?
bpy.app.handlers.load_post.clear()
bpy.app.handlers.load_post.append(Event_OnLoad)
bpy.app.handlers.scene_update_post.clear()
#bpy.app.handlers.scene_update_post.append(Event_OnSceneUpdate)		 ###DESIGN ###IMPROVE Turn on/off this expensive polling only when needed?

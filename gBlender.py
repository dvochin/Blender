### NEXT ###
###BUG!!!!: Can not find a single vert on detached breasts!  (Even if it's there!) WHY???
# Fucking get naming of bodies straight throughout!!
#Can fucking finally regen body col... why broken?
#- Problem with versions... too old, too new, for vert transfer and use_beauty!
#- Had to rem out during bodycol creation torso mat!
#- What happented to all the mats in earlier stage?
#- Use-beauty changed things??
#- Why was man with bodycol???
# Remember: code that extracts breasts: now have colliders out of mesh!
### Reconsider these other 'GetMesh' functions.  Always call getMesh and get extra arrays in a common method!!!

### TODO ###
# Proportional editing has the 'connected mode' that goes from edge distance!!!
	# REWRITE breast morph!! Do we really need all that complexity???
# Use '-' throughout!

### LATER ###
# Annoying to have to reboot blender and Client at each run... boost memory handles freed??

### PROBLEMS ###
# Bodycol issues with penis for shemale... what to do???
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
# BodyCol later decimation can flip normals???
# Still get small holes in capping of penis... Enough to throw off PhysX tetra creation?
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
#+++ Density of all colliders in PhysX should apply what we learned between cloth and colliders??? +++
# Different colors for each curve pins & curves
#- For easier straps: Implement a 'repel' feature where user-placed verts of current spline will 'push' verts of other splines?
# For body collider also ship to PhysX some 'bone-based' rough collider for the arms, legs and neck to act as a failsafe when the accurate colliders fail

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
	# Do we revive PhysX cloth fit??
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


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	GLOBAL VARIABLES
#---------------------------------------------------------------------------	

g_aSharedMeshes = {}			###OBS? Important map of string-to-bmesh object to hold the important bmesh reference for all bmesh requested by Client in gBL_GetMesh() until released by gBL_ReleaseMesh()

#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	TOP LEVEL
#---------------------------------------------------------------------------	

def gBL_Initialize():
	print("\n********** gBL_Initialize **********")
	###DESIGN: Debug flag of any use??? bpy.types.Scene.IsDebuggable = bpy.props.BoolProperty(name="IsDebuggable", default=False)


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	UTILITIES
#---------------------------------------------------------------------------	

#---------------------------------------------------------------------------	COMMON OPERATIONS
def SelectAndActivate(sNameObject):	 #=== Goes to object mode, deselects everything, selects and activates object with name 'sNameObject'
	if bpy.ops.object.mode_set.poll():			###LEARN: In some situations we cannot change mode (like when selecting a linked object from another file)
		bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')###LEARN: Good way to select and activate the right object for ops... ***IMPROVE: Possible??
	oObj = None
	if sNameObject in bpy.data.objects:			###LEARN: How to test if an object exists in Blender
		oObj = bpy.data.objects[sNameObject]
		oObj.hide_select = False				###LEARN: We can't select it if hide_select is set!
		oObj.hide = oObj.hide_select = False	###CHECK: Keep?
		oObj.select = True
		bpy.context.scene.objects.active = oObj
		if bpy.ops.object.mode_set.poll():
			bpy.ops.object.mode_set(mode='OBJECT')
	#else:		###IMPROVE?
	#	raise Exception("ERROR: SelectAndActivate() cannot find object '{}'".format(sNameObject))
	return oObj

def DeleteObject(sNameObject):
	#print("DeleteObject: " + sNameObject)
	SelectAndActivate(sNameObject)
	bpy.ops.object.delete(use_global=True)

def DuplicateAsSingleton(sSourceName, sNewName, sNameParent, bHideSource):
	DeleteObject(sNewName)
	oSrcO = SelectAndActivate(sSourceName)
	if oSrcO is None:
		raise Exception("ERROR: DuplicateAsSingleton() could not select object '{}'".format(sSourceName))
	bpy.ops.object.duplicate()
	oNewO = bpy.context.object		  # Duplicate above leaves the duplicated object as the context object...
	oSrcO.select = False		   #... but source object is still left selected.  Unselect it now to leave new object the only one selected and active.
	oNewO.name = oNewO.data.name = sNewName				###CHECK: Do we really want to enforce name this way?  Can have side effects?  Should display error??
	oNewO.name = oNewO.data.name = sNewName
	oNewO.hide = oNewO.hide_render = oNewO.hide_select = False
	oSrcO.hide = bHideSource		   ###CHECK: oSrcO.hide_render	Do we hide here or in caller if required??
	if sNameParent is not None:							# 'store' the new object at the provided location in Blender's nodes
		if sNameParent not in bpy.data.objects:
			raise Exception("ERROR: DuplicateAsSingleton() could not locate parent node " + sNameParent)
		###oNewO.parent = bpy.data.objects[sNameParent]		   ###LEARN: Parenting an object this way would reset the transform applied to object = disaster!  (Client-side meshes lose their 90 deg orientation and become 100x bigger!)
		oParentO = bpy.data.objects[sNameParent]
		oParentO.hide = oParentO.hide_select = False
		oParentO.select = True
		bpy.context.scene.objects.active = oParentO
		bpy.ops.object.parent_set(keep_transform=True)		###LEARN: keep_transform=True is critical to prevent reparenting from destroying the previously set transform of object!!
		bpy.context.scene.objects.active = oNewO
		oParentO.select = False				  
		oParentO.hide = oParentO.hide_select = True			###WEAK: Show & hide of parent to enable reparenting... (lose previous state of parent but OK for folder nodes made up of 'empty'!)
	return oNewO
	 
def AssertFinished(sResultFromOp):	###IMPROVE: Use this much more!
	if (sResultFromOp != {'FINISHED'}):
		raise Exception("*Err: Operation returned: ", sResultFromOp)


#---------------------------------------------------------------------------	VIEW 3D
def GetView3dSpace():						   # Returns the first 3dView.	Important to set parameters of the view such as pivot_point
	for oWindow in bpy.context.window_manager.windows:			###IMPROVE: Find way to avoid doing four levels of traversals at every request!!
		oScreen = oWindow.screen
		for oArea in oScreen.areas:
			if oArea.type == 'VIEW_3D':
				for oSpace in oArea.spaces:
					if oSpace.type == 'VIEW_3D':
						return oSpace
	raise Exception("ERROR: in GetView3dRegion().  Could not find View3D space!")

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
	raise Exception("ERROR: AssembleOverrideContextForView3dOps() could not find a VIEW_3D with WINDOW region to create override context to enable View3D operators.  Operator cannot function.")


#---------------------------------------------------------------------------	MESH CONVERSION
def Util_ConvertToTriangles():	   # Triangulate the selected mesh so Client only sees triangles (the only thing it can render).  We keep normal preservation on ===
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.quads_convert_to_tris()		###REVIVE: use_beauty=true 
	bpy.ops.mesh.select_all(action='DESELECT')
	bpy.ops.object.mode_set(mode='OBJECT')


#---------------------------------------------------------------------------	FINDING VERTS
def Util_FindClosestVert(oMeshO, vecVert, nTolerance):		# Attempts to find the closest vert to 'vecVert' by using 'closest_point_on_mesh()'
	###BUG: Many uses of this function sabotaged because of flaws in closest_point_on_mesh()!  Will find a vert up to .015 away (1.5cm!)
	oMesh = oMeshO.data
	aClosestPtResults = oMeshO.closest_point_on_mesh(vecVert, nTolerance)		 # Return (location, normal, face index)  ###LEARN: Must be called in object mode (unfortunately) or we'll get an error "object has no mesh data"!
	nPolyClosest = aClosestPtResults[2]
	if nPolyClosest == -1:
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
		print("- Vert {:5d} has min surf dist {:7.4f}".format(oVert1.index, nDistPathMin))
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
	aEdgesOnPath = [oEdge for oEdge in bm.edges if oEdge.select]
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
			
def Util_SelectVertGroupVerts(oMeshO, sNameVertGrp):			# Select all the verts of the specified vertex group 
	#=== Obtain access to mesh in edit mode, deselect and go into vert mode ===
	###SelectAndActivate(oMeshO.name)			 ###IMPROVE? Select fist??
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='DESELECT') 
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')		 # We go to face mode and expand the verts selected.  This will select all faces that have at least one vert selected...

	#=== Find the requested vertex group and select its vertices ===
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)
	if (nVertGrpIndex != -1):
		oMeshO.vertex_groups.active_index = nVertGrpIndex
		bpy.ops.object.vertex_group_select()
		oVertGrp = oMeshO.vertex_groups[nVertGrpIndex]
		return oVertGrp 
	else:  
		print("WARNING: Util_SelectVertGroupVerts() could not find vert group '{}' in mesh '{}'".format(sNameVertGrp, oMeshO.name))
		return None

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

def gBL_Util_RemoveGameMeshes():
	print("gBL_Util_RemoveGameMeshes() removing game meshes...")
	oNodeFolderGame = bpy.data.objects[G.C_NodeFolder_Game]
	for oNodeO in oNodeFolderGame.children:
		DeleteObject(oNodeO.name)			 

def gBL_Util_HideGameMeshes():
	print("gBL_Util_RemoveGameMeshes() removing game meshes...")
	oNodeFolderGame = bpy.data.objects[G.C_NodeFolder_Game]
	for oNodeO in oNodeFolderGame.children:
		oNodeO.hide = oNodeO.hide_render = True
	bpy.data.objects["WomanA" + G.C_NameSuffix_Face].hide = False			###HACK
	###BROKEN bpy.data.objects["ManA" + G.C_NameSuffix_Face].hide = False
	bpy.data.objects["WomanA" + G.C_NameSuffix_BodyCol].hide = True
	###BROKEN bpy.data.objects["ManA" + G.C_NameSuffix_BodyCol].hide = True
					
def Util_RemoveProperty(o, sNameProp):		# Safely removes a property from an object.
    if sNameProp in o:
        del o[sNameProp]
    



#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	CLEANUP
#---------------------------------------------------------------------------	

def Cleanup_RemoveDoubles(nRepeats, nDoubleThreshold, nEdgesThreshold):	 ###OBS? Our most important (and simplest) cleaning technique... used throughout to prevent boolean from failing!
	print("- Cleanup_RemoveDoubles with {} threshold, {}  edge hunt and {} repeats.".format(nDoubleThreshold, nEdgesThreshold, nRepeats))
	for nRepeat in range(nRepeats):	 # Do this cleanup a few times as each time the non-manifold edges clear up without us needing to go near inside verts...
		bpy.ops.mesh.select_non_manifold(extend=False)	# Select the edges of the cloth...
		bpy.ops.mesh.edges_select_(ness=radians(nEdgesThreshold))  ###TUNE: Quite aggressive angle!
		bpy.ops.mesh.remove_doubles(threshold=nDoubleThreshold, use_unselected=False)  ###TUNE: Aggressive remove double!	 # Remove some of the worst small details caused by cuts.  Bigger than 0.0025 and we start damaging open edges!
				   
def Cleanup_RemoveDegenerateFaces(oObj, nCuttoffAngle):	 ###OBS? Removes faces with tiny angles in them -> likely degenerate faces that can throw off boolean
	SelectAndActivate(oObj.name)
	nDeletedFaces = 0
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.quads_convert_to_tris()		###REVIVE: use_beauty=true 
	bpy.ops.mesh.remove_doubles(threshold=0.003, use_unselected=False)	###TUNE: Remove the worst of the super-close geometry to help remove degenerate stuff from boolean cuts
	bpy.ops.mesh.select_all(action='DESELECT') 
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	bpy.ops.object.mode_set(mode='OBJECT')
	
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

def Cleanup_RemoveCustomDataLayers(sNameObject):				  # Debug cleanup function that removes the custom data layers that can pile up on objects as various functions that create them crash.
	oMeshO = SelectAndActivate(sNameObject)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMeshO.data)
	while len(bm.verts.layers.int) > 0:
		oLayer = bm.verts.layers.int[0]
		print("Cleanup_RemoveCustomDataLayers() removed int layer " + oLayer.name)
		bm.verts.layers.int.remove(oLayer)
	while len(bm.verts.layers.float) > 0:
		oLayer = bm.verts.layers.float[0]
		print("Cleanup_RemoveCustomDataLayers() removed float layer " + oLayer.name)
		bm.verts.layers.float.remove(oLayer)
	bpy.ops.object.mode_set(mode='OBJECT')

def Cleanup_RemoveCustomDataLayerInt(sNameObject, sNameLayer):				  # Debug cleanup function that removes the 'sNameLayer' custom data layers from sNameObject
	oMeshO = SelectAndActivate(sNameObject)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMeshO.data)
	if (sNameLayer in bm.verts.layers.int):
		bm.verts.layers.int.remove(bm.verts.layers.int[sNameLayer])
# 	for nLayer in range(len(bm.verts.layers.int)):						###IMPROVE? Can select without iteration?
# 		oLayer = bm.verts.layers.int[nLayer]
# 		if (oLayer.name == sNameLayer):
# 			bm.verts.layers.int.remove(oLayer)
# 			return;
	bpy.ops.object.mode_set(mode='OBJECT')

def Cleanup_VertGrp_RemoveNonBones(oMeshO):	 # Remove non-bone vertex groups so skinning normalize & fix below will not be corrupted by non-bone vertex groups
	aVertGrpToRemove = []
	for oVertGrp in oMeshO.vertex_groups:
		if oVertGrp.name[0] == G.C_VertGrpPrefix_NonBone:  # Any vertex groups that starts with '_' is a non-bone and has no value for Client
			aVertGrpToRemove.append(oVertGrp)
	for oVertGrp in aVertGrpToRemove:
		oMeshO.vertex_groups.remove(oVertGrp) 


#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	STREAM / SERIALIZATION
#---------------------------------------------------------------------------	

def Stream_SendVector(oBA, vec):  ###LEARN: Proper way to pack Pascal string
	oBA += struct.pack('fff', vec[0], vec[1], vec[2])  ###IMPROVE: Can safely send whole array?

def Stream_SendStringPascal(oBA, sContent):	 ###LEARN: Proper way to pack Pascal string
	sContentEncoded = sContent.encode()
	oBA += struct.pack(str(len(sContentEncoded) + 1) + 'p', sContentEncoded)  ###LEARN: First P = Pascal string = first byte of it is lenght < 255 rest are chars

def Stream_SerializeArray(oBA, oArray):				 # Serialize an array to client by first sending the length and then the data.	The other side is supposed to know how many bytes each of our array element takes and deserialize the proper number of bytes
	if oArray is not None:
		oBA += struct.pack('L', len(oArray))				# It is assumed that oArray is a bytearray
		oBA += oArray
		###IMPROVE? oBA += G.C_MagicNo_EndOfArray
	else:		 
		oBA += struct.pack('i', 0)

def Stream_SendBone(oBA, oBone):				# Recursive function that sends a bone and the tree of bones underneath it in 'breadth first search' order.	 Information sent include bone name, position and number of children.
	Stream_SendStringPascal(oBA, oBone.name)		# Precise opposite of this function found in Unity's CBodeEd.ReadBone()
	vecBone = G.VectorB2C(oBone.head_local)				  # Obtain the bone head and convert to client-space (LHS/RHS conversion)		 ###LEARN: 'head' appears to give weird coordinates I don't understand... head_local appears much more reasonable! (tail is the 'other end' of the bone (the part that rotates) while head is the pivot point we need
	Stream_SendVector(oBA, vecBone)
	oBA += struct.pack('B', len(oBone.children))
	for oBoneChild in oBone.children:
		Stream_SendBone(oBA, oBoneChild)



#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	SCENE EVENT HANDLERS
#---------------------------------------------------------------------------	

def Event_OnLoad(scene):			 # Runs on scene_update_post when the user has changed the scene and we need to update our state
	gBL_Initialize()
	
def Event_OnSceneUpdate(scene):				# Runs on scene_update_post when the user has changed the scene and we need to update our state
	print("Event_OnSceneUpdate???")
	
#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	APP GLOBAL TOP LEVEL
#---------------------------------------------------------------------------	

bpy.app.handlers.load_post.clear()
bpy.app.handlers.load_post.append(Event_OnLoad)
bpy.app.handlers.scene_update_post.clear()
#bpy.app.handlers.scene_update_post.append(Event_OnSceneUpdate)		 ###DESIGN ###IMPROVE Turn on/off this expensive polling only when needed?

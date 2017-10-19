###DOCS24: Aug 2017 - SoftBody rewrite - Blender-side

#--- CBodyBase separated by softbody ---
#- Broken moving of bones to shape center... do in Unity?
#- SoftBodyID extraneous now in info??

#--- CBodyBase review ---
#- Update Unity flags!
#- Port any fn accessing bm
#- Scan through again
	#- Any step during sb rejoin can be trimmed?
#- Could remove vert groups for fingers and toes?
#- Name of special vert grps like vagina collider
#- Find one vert in cmesh

#- Push safety checks into Finalize()
#- Dick mount poor
#- Still some small faces on main scene body col

#--- CMesh port ---
#- Finalize()
	#- Move limit and normalize there? 
#- Move in old gBL crap for comm layer
	#- Need recompile of C++ apps?
#- Reroute all of Unity toward CBody file!
#- Uretra pos & emitter! 
# Study sel history got neat results once https://docs.blender.org/api/blender_python_api_current/bmesh.types.html#bmesh.types.BMEditSelSeq
#- Shrunken smooth joins between big boobs because of manifold fix... Can be improved??
	
	
#--- Vagina penetration ---
#- For vagina opening... try particles in the fluid scene (to take advantage of our detailed penis collider!)
#++ Need trigger to on/off vagina bones and reset bone pos to prevent corruption
	#- Vagina damping would be nice but it moves sluggishly when body is moving rapidly...
		#+ If we implement an 'off' / kinematic mode then this problem goes away!!
#++ Appearance!!
#+ Vagina bone kinematic a pain
#- Reduce number of bones!
#- Need precise vagina hole scaling from penis radius
	#- How to get penis radius?  (Wait until full penis implementation?) 
#- Dynamic bone parents proper?
#- Penis tip cap opens too early... adjust vagina bone radius? (reduces smoothness!)
	#- As an alternative it Would be nice to 'push into' body the vagina bones but unfortunately bone roll doesn't allow us
	#- Same with using capsule colliders for vagina bones = bone roll is garbage!
	#- Could back up the tip particles however...
#- Move CHoleRig toward ship-time & Body Prep!
#- Unity needs to adjust vagina for dick size by scaling bones.  Not just for hole but opening as well! = smooth bones
#- Expand safety checks to all-in-one
#	   is_editmode = (ob.mode == 'EDIT')#		if is_editmode:#			bpy.ops.object.mode_set(mode='OBJECT', toggle=False)



# === DEV ===
#- Start looking at Blender-side penis code to see what is obsolete and how we can integrate
	#- Will need to define an U&B CFlexRig_XYZ softbody that traps extra info between U&B (e.g. penis uretra pos, vagina info, etc)
#- Will need to create new class for each softbody to hold info and perform extra processing (e.g. penis and vagina)
	#- These classes can tune the functioning of the main algorithm by setting their values

# === NEXT ===
#- Errors with bunch of extra bones in Unity

# === TODO ===
#- Fix rig material to something nicer than pink

# === LATER ===
#- Offer Unity more options to control Flex rig construction... like avoiding safety checks etc.
#- Consider destroying extra meshes when Finalize() completes?  (unless debug mode)  (Use CMesh auto delete when auto out of scope (trap gc)?)

# === MOVE ===
#- Will need to have different areas of softbodies: like balls
#- Huge mess with fluid collider class and new main scene one: converge into one?  rethink!
#- Had to create a new +Penis bone... need to put in importer flow?  (Or create in CBodyBase?)
#- Make most utility functions accept regex filters!

# === OPTIMIZATIONS ===
#- To speed things up, remove unneeded part of geometry such as eyes, teeth, eyebrows, fingers, toes, nostrils, etc 
	#- Would be beneficial to be able to select verts by bone and material (to trim unneeded body verts during flex body collider creation)

# === REMINDERS ===
#- VaginaBones taken out... need diff naming for these bones (special type of dynamic bone?)
#- Make Breast subdivide permanent by inserting in body import!
#- Remember to redefine breasts geometry in importer!
#- Remember that game body still doesn't have its own armature!
#- Had to disable vert group clean at morph result mesh for CHoleRig to work... how come it worked before??
#- Remember to add "+VaginaBone_Rig_Upper" to chestLower and  "+VaginaBone_Rig_Lower" to Genitals in BodyImport!

# === IMPROVE ===
#- Unity requires a final rotation to convert from shape natural orientation to bone... re-orient Blender bone to remove this need.
#- Penis inner verts for thick penises: Would they improve anything?
	#- Inner verts when possible would make it so vanilla algorithm can use the center vert for a better soft body simulation?
	#- Idea: Penis superclass can re-interpret distances from vert to vert to 'squash' along girth
#- Penis links cannot reach across...  Need to override search for this to work
#- Fine penis rim causing lots of links... simplify?  
#- Would be nice in Unity visualizer to have primary particle highlighted in a shape
#- Start filling in hard-to-tell params in fully-qualified mode
#- Need to finalize prefix on bone names!
	#- Added the new bone prefix '#' for the penis bone place holder... '#' = Placeholder weight (with 100% weight at every verts meant to be consumed by CBodyBase?)
#- Check possible for rig-under-construction to weld between breasts when too close together?
#- Add a debug check that visualizes edge lengths that are too small
#-? Enhance DEV_PreventRemoveDoublesDuringShrink to add more faces like under breasts, etc
#- We can probably find a bone orientation that gets ride of nasty runtime bone re-orientation in Unity Update()
#- Rename every function that Unity calls directly with the Unity_ prefix!
# Can improve decimate after remesh by dissolving faces with very small areas
#- Blender's load performance is much better when not showing materials!

# === NEEDS ===

# === DESIGN ===
#- Need to redesign U + B understanding of what a softbody is, who decides who they are (Blender) and how adapts to what it receives (Unity)
#- Finalize decisions on bone names, what parent they have, etc
	#- #CFlexRig_SafeVertsForShrink??

# === QUESTIONS ===

# === IDEAS ===
#- Remesh may be able to produce less degenerate geometry during important full body shrink?
#- Remember Blender has 'Decimate Geometry' instead of remove_doubles...  Unfortunately it requires a ratio as opposed to an edge length
#- Try 'Degenerate Dissolve'!

# === LEARNED ===
#- Inertia Bias is SUPER IMPORTANT to stabilize tip rotation problem!
	#- Why the fuck did it use to have problem now problem gone?!?!
#- vertex_group_smooth() trashes even locked vertex groups!! WTF?!?!?!
#- Using 'dir(oPythonObject)' enables us to view all its methods (including hidden ones)
#- # the script equivalent of the F key: bmesh.ops.contextual_create(bm, geom=selected_faces)
#- update_edit_mesh() is used a LOT in code!  Investigate!!
#- When you add or alter edges or polygons you need to use object.data.update() to see the changes in the 3dview. (https://blender.stackexchange.com/questions/55484/when-to-use-bmesh-update-edit-mesh-and-when-mesh-update)	
	#- oMeshD.update() updates 3D view when a bmesh has modified mesh (e.g. selection) 
#--- When modeling in blender there are certain assumptions made about the state of the mesh.
#- hidden geometry isn’t selected.
#- when an edge is selected, its vertices are selected too.
#- when a face is selected, its edges and vertices are selected.
#- duplicate edges / faces don’t exist.
#- faces have at least 3 vertices.
#-vertlist = [elem.index for elem in bm.select_history if isinstance(elem, bmesh.types.BMVert)]
#- Ctrl + Alt + Z for undo history!!
#- Eclipse: Ctrl+Shift+L list keys!
#- bpy.context.object.update_from_editmode() # Loads edit-mode data into object data
# def enum(*args):            ###INFO: How to have variable arguments!!
#     ###INFO: How to use: eGender = G.enum('MALE', 'FEMALE', 'N_A'); eGender.FEMALE would return '1'
#     mapEnums = dict(zip(args, range(len(args))))       ###INFO: Based on technique at http://pythoncentral.io/how-to-implement-an-enum-in-python/   See also https://docs.python.org/3/library/enum.html
#     return type('Enum', (), mapEnums)                   ###INFO: WTF does this do?  Appears central to this technique's enum magic!
# dissolve_degenerate
#def dump(obj, level=0):    for attr in dir(obj):       if hasattr( obj, "attr" ):           print( "obj.%s = %s" % (attr, getattr(obj, attr)))       else:            print( attr )
# total_vert_sel counts # of verts! 

# === PROBLEMS ===
#- Serializing bones TWICE!!  Rethink dynamic bone serialization.  Unity CBody does once ASAP?
#- Parts of arm removed by aggressive safe remove doubles!!
#- Vert groups for breasts not equal
#?- How come some shapes have 3-4 links???
#- Likely problem on breasts close together
#-? Some simulated surface too close (even with rim fix) but looks pretty good in Unity!
#- Rim verts are heavily jagged... would benefit to expand?
#- Still part of rig mesh that are useless (e.g. vagina, anus, mouth?)
#- Penis decimation will probably wipe key verts like Uretra, etc.  need to preserve those!
#- Ship-time CHoleRig trashes _DEV_VaginaHoleRemove!
#- Source reloading / revert sometimes appears to fail misteriously... maybe order of files matter?  Do twice??

# === WISHLIST ===









#======================================================================================================================
###NEW16:
###OBS: Cleanup!!

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
#bpy.ops.mesh.symmetry_snap()		 ###INFO: This call instrumental in fixing mesh imperfections from DAZ... integrate it in flow as we get closer to DAZ imports
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
# There's a nice attribute called select_history in the bmesh module (https://blender.stackexchange.com/questions/1412/efficient-way-to-get-selected-vertices-via-python-without-iterating-over-the-en)
	# Read https://blender.stackexchange.com/questions/69796/selection-history-from-shortest-path
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
# 'Vertex Selection Masking' in 'Weight Painting' mode enables smoothing to be performed there... and select verts!

### WISHLIST ###
# Now that pins are created from curve it would be nice to specify # of points on curve!



import bpy
import sys
import array
import bmesh
import struct
from math import *
from mathutils import *
import re

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
def DeselectEverything():		# Clears selection and active object in scene
	if bpy.ops.object.mode_set.poll():					###INFO: In some situations we cannot change mode (like when selecting a linked object from another file)
		bpy.ops.object.mode_set(mode='OBJECT')
	bpy.context.scene.objects.active = None				###INFO: How to activate / de-activate objects
	for oSelected in bpy.context.selected_objects:		###INFO: How to safely de-select objects (including hidden ones!)
		bWasHidden = oSelected.hide		
		if bWasHidden:
			oSelected.hide = False		###WEAK: Has been shown to NOT work when parent object / armature hidden... so this code in some (all?) contexts does not work!  Reducing usage of hiding for now...
		oSelected.select = False 
		#if bWasHidden:
		#	oSelected.hide = True
	#bpy.ops.object.select_all(action='DESELECT')


def SelectObject(sNameObject, bCheckForPresence=True):	 #=== Goes to object mode, deselects everything, selects and activates object with name 'sNameObject'
	DeselectEverything()	
	oObj = None
	if sNameObject in bpy.data.objects:			###INFO: How to test if an object exists in Blender
		oObj = bpy.data.objects[sNameObject]
		oObj.hide_select = False				###INFO: We can't select it if hide_select is set!
		oObj.hide = False
		oObj.select = True
		bpy.context.scene.objects.active = oObj
# 		if bpy.ops.object.mode_set.poll():
# 			bpy.ops.object.mode_set(mode='OBJECT')
	else:
		if (bCheckForPresence):
			raise Exception("###EXCEPTION: SelectObject() cannot find object '{}'".format(sNameObject))
	return oObj

def DeleteObject(sNameObject):
	#if (oObj != None):
	#	print("<<< Deleting object '{}' >>>".format(sNameObject))
	#bpy.ops.object.delete(use_global=True)		###BUGFIXED!!! Frequently causes memory corruption on code called from Unity or Blender console... adopt a more gentle way to delete?  (queue up or just rename to temp names?)
	if sNameObject in bpy.data.objects:			###INFO: This is by *far* the best way to delete in Blender!!
		oObj = bpy.data.objects[sNameObject]
		bpy.data.scenes[0].objects.unlink(oObj)
		bpy.data.objects.remove(oObj)
	return None				# Return convenient None so we can set owning variable in one line

def DuplicateAsSingleton(sSourceName, sNewName, sNameParent = None, bHideSource = True, bLinked = False):
	#print("-- DuplicateAsSingleton  sSourceName '{}'  sNewName '{}'  sNameParent '{}'".format(sSourceName, sNewName, sNameParent))
	DeleteObject(sNewName)
	
	oSrcO = SelectObject(sSourceName, False)
	if oSrcO is None:
		raise Exception("###EXCEPTION: DuplicateAsSingleton() could not select object '{}'".format(sSourceName))
	if bLinked:
		bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked":True, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0)})
	else:
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
	oChildO = SelectObject(sNameObject, False)
	if sNameParent is not None:							# 'store' the new object at the provided location in Blender's nodes
		if sNameParent not in bpy.data.objects:
			raise Exception("###EXCEPTION: SetParent() could not locate parent node " + sNameParent)
		oChildO.parent = bpy.data.objects[sNameParent]		   ###INFO: Parenting an object this way would reset the transform applied to object = disaster!  ###CHECK  No longer valid?
# 		oParentO = bpy.data.objects[sNameParent]		###CHECK: Ok now?
# 		oParentO.hide = oParentO.hide_select = False
# 		oParentO.select = True
# 		bpy.context.scene.objects.active = oParentO
# 		bpy.ops.object.parent_set(keep_transform=True)		###INFO: keep_transform=True is critical to prevent reparenting from destroying the previously set transform of object!!
# 		bpy.context.scene.objects.active = bpy.data.objects[sNameObject]
# 		oParentO.select = False				  
# 		oParentO.hide = oParentO.hide_select = True			###WEAK: Show & hide of parent to enable reparenting... (lose previous state of parent but OK for folder nodes made up of 'empty'!)

def CreateEmptyBlenderNode(sNameNode, sNameParent, nRadius=0.01):			# Create an empty Blender object (a hidden cube in this case) as a child of 'sNameParent'.  Used to create a useful hierarchy in Blender's outliner so tons of unrelated objects don't have to be under the same parent
	bpy.ops.object.empty_add(type='CUBE', radius=nRadius)		# Create an empty we will reparent to game folder
	oNodeNew = bpy.context.object						 	# Obtain reference empty we just created above
	oNodeNew.parent = bpy.data.objects[sNameParent]			# Set as child of game folder
	oNodeNew.name = sNameNode	   							# Name it (twice so it sticks) 
	oNodeNew.name = sNameNode
	oNodeNew.location = Vector((0, 0, 0))				 	# Set it to origin 
	bpy.context.scene.objects.active = None					###INFO: If we don't deactivate it, copies will also copy this object!
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
			if oArea.type == 'VIEW_3D':							###INFO: Frequently, bpy.ops operators are called from View3d's toolbox or property panel.	 By finding that window/screen/area we can fool operators in thinking they were called from the View3D!
				for oRegion in oArea.regions:
					if oRegion.type == 'WINDOW':				###INFO: View3D has several 'windows' like 'HEADER' and 'WINDOW'.	Most bpy.ops require 'WINDOW'
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
	###INFO: Alternatives at http://blenderartists.org/forum/archive/index.php/t-229112.html
	oMesh = oMeshO.data
	aClosestPtResults = oMeshO.closest_point_on_mesh(vecVert, nTolerance)		 # Return (location, normal, face index)  ###INFO: Must be called in object mode (unfortunately) or we'll get an error "object has no mesh data"!
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
		bpy.context.scene.cursor_location = oMeshO.matrix_world * vecVert	###INFO: How to convert from local vert to global.
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
			nDist = (oVert2.co - vecVertMirrorX).length_squared			###INFO: Faster equivalent than 'magnitude' as we don't really need sqrt()
			if nDistMin > nDist:
				nDistMin = nDist
				oVertClosest = oVert2
		aVertsMirrorX.append(oVertClosest)
		if nDistMin > 0.000001:
			print("-WARNING: Vert {:5d} has MirrorX at {:5d} with tolerance {:7.6f}".format(oVert1.index, oVertClosest.index, nDistMin))
	return aVertsMirrorX

def Util_GetFirstSelectedVert(bm):		# Returns the first selected vertex of BMesh bm
	###IMPROVE: Wished there was a way to mark verts and not have to iterate through all of them to find the right one!
	for oVert in bm.verts:								 
		if oVert.select:
			return oVert
	raise Exception("###EXCEPTION: Util_GetFirstSelectedVert() could not a selected vertex!")

# def Util_CountNumSelectedVerts(bm):
#	return oMeshO.total_vert_sel
# 	return len([oVert for oVert in bm.verts if oVert.select])		   ###OPT:!!!! Can find a faster way than full iteration?? Geez!!
	

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

def MeshMode_Object(oMeshO):			###DEV24:!!! Expand into smart mode switch!
	if oMeshO.mode != 'OBJECT':
		bpy.ops.object.mode_set(mode='OBJECT')

def MeshMode_Edit(oMeshO):
	if oMeshO.mode != 'EDIT':
		bpy.ops.object.mode_set(mode='EDIT')

def Util_HideMesh(oMeshO):
	MeshMode_Object(oMeshO)
	oMeshO.select = False			###INFO: We *must* unselect an object before hiding as group unselect wont unselect those (causing problems with duplication) 
	if (bpy.context.scene.objects.active == oMeshO):
		bpy.context.scene.objects.active = None
	oMeshO.hide = True

def Util_UnhideMesh(oMeshO):
	oMeshO.hide = False

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
	#bpy.data.objects["Woman" + G.C_NameSuffix_Face].hide = False			###HACK
					
def Util_RemoveProperty(o, sNameProp):		# Safely removes a property from an object.
	if sNameProp in o:
		del o[sNameProp]





#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	CLEANUP
#---------------------------------------------------------------------------	

def Cleanup_RemoveDoublesAndConvertToTris(nDoubleThreshold, bSelectEverything = True, bOpen = True, bClose = True):			# Removes double verts on a whole mesh.
	if bOpen:
		bpy.ops.object.mode_set(mode='EDIT')
	if bSelectEverything:
		bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.quads_convert_to_tris()									###DESIGN: Keep in here??
	bpy.ops.mesh.remove_doubles(threshold=nDoubleThreshold, use_unselected=True)		###INFO: 'use_unselected' not doing anything!!
	if bSelectEverything:
		bpy.ops.mesh.select_all(action='DESELECT')
	if bClose:
		bpy.ops.object.mode_set(mode='OBJECT')

###OBS?
# def Cleanup_RemoveDoublesAndConvertToTrisAndNonManifold(nRepeats, nDoubleThreshold, nEdgesThreshold):	 ###OBS? Our most important (and simplest) cleaning technique... used throughout to prevent boolean from failing!
# 	print("- Cleanup_RemoveDoublesAndConvertToTris with {} threshold, {}  edge hunt and {} repeats.".format(nDoubleThreshold, nEdgesThreshold, nRepeats))
# 	for nRepeat in range(nRepeats):	 # Do this cleanup a few times as each time the non-manifold edges clear up without us needing to go near inside verts...
# 		bpy.ops.mesh.select_non_manifold(extend=False)	# Select the edges of the cloth...
# 		bpy.ops.mesh.edges_select_(ness=radians(nEdgesThreshold))  ###TUNE: Quite aggressive angle!
# 		bpy.ops.mesh.remove_doubles(threshold=nDoubleThreshold, use_unselected=False)  ###TUNE: Aggressive remove double!	 # Remove some of the worst small details caused by cuts.  Bigger than 0.0025 and we start damaging open edges!

def Cleanup_RemoveDegenerateFaces(oObj, nCuttoffAngle):	 ###OBS? Removes faces with tiny angles in them -> likely degenerate faces that can throw off boolean
	SelectObject(oObj.name)
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
	SelectObject(oObj.name)
	
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_non_manifold(extend=False)	# Select the edges of the cloth...
	bpy.ops.mesh.edges_select_(ness=radians(nness))	 ###TUNE: Quite aggressive angle!
	bpy.ops.mesh.select_more()
	oVertGroup_Decimate = oObj.vertex_groups.new(name="DECIMATE")
	bpy.ops.object.vertex_group_assign(new=False)
	bpy.ops.object.mode_set(mode='OBJECT')
	
	oObj.update_from_editmode()	 ###INFO 2.67+!
	nFacesSelected = len([oPoly for oPoly in oObj.data.polygons if oPoly.select])  ###INFO: Shortest line to iterate through a set and do something...
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

def Cleanup_MaterialsTexturesImages():
	print("\n===== Cleanup_MaterialsTexturesImages() =====")
	
	#=== Remove the duplicate materials the FBX importer created for the source body import ===		###MOVE??
	print("\n=== Removing duplicate materials ===")
	for oMat in bpy.data.materials:						 ###INFO: All materials, textures, images that do not begin with "_" are considered transient are can be safely deleted (Code that needs to persist materials, textures or images will prefix them with "_")
		if oMat.name[0] != "_":
			print("- Deleting material '{}'".format(oMat.name))
			bpy.data.materials.remove(oMat)

	#=== Remove the duplicate textures the FBX importer created for the source body import ===
	print("\n=== Removing duplicate textures ===")
	for oTex in bpy.data.textures:
		if oTex.name[0] != "_":
			print("- Deleting texture '{}'".format(oTex.name))
			bpy.data.textures.remove(oTex)
	
	#=== Remove the duplicate images the FBX importer created for the source body import ===
	print("\n=== Removing duplicate images ===")
	for oImg in bpy.data.images:
		if oImg.name[0] != "_":
			print("- Deleting image '{}'".format(oImg.name))
			bpy.data.images.remove(oImg)

	#=== Enumerating duplicate materials ===
	print("\n=== Enumerating duplicate materials ===")
	for oMat in bpy.data.materials:						 ###INFO: All materials, textures, images that do not begin with "_" are considered transient are can be safely deleted (Code that needs to persist materials, textures or images will prefix them with "_")
		if oMat.name.find(".") != -1:
			print("#WARNING: Found duplicate material '{}'!".format(oMat.name))
			#bpy.data.materials.remove(oMat)		# User must manually fix this to avoid mesh losing a material
	
	print("--- Cleanup_MaterialsTexturesImages() finishes ---\n")

	


#---------------------------------------------------------------------------	VertGrp Functions: Helper functions centered on Vertex Groups

def VertGrp_FindByName(oMeshO, sNameVertGrp, bThrowIfNotFound = True): 
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)			###INFO: Can also find directly by oMeshO.vertex_groups[sNameVertGrp] !!! 
	if (nVertGrpIndex != -1):
		oVertGrp = oMeshO.vertex_groups[nVertGrpIndex]
		return oVertGrp 
	else:
		if bThrowIfNotFound:
			raise Exception("\n###EXCEPTION: VertGrp_FindByName() could not find vert group '{}' in mesh '{}'".format(sNameVertGrp, oMeshO.name))

def VertGrp_SelectVerts(oMeshO, sNameVertGrp, bDeselect=False, bThrowIfNotFound=True):			# Select all the verts of the specified vertex group 
	#=== Obtain access to mesh in edit mode, deselect and go into vert mode ===
	###SelectObject(oMeshO.name)			 ###IMPROVE? Should make sure we're select fist but this call is makes too many things happen for here!  ###IMPROVE: Move into CMesh!
	if oMeshO.mode != 'EDIT':				###IMPROVE: Develop smart mode switch functions!
		bpy.ops.object.mode_set(mode='EDIT')
	if bDeselect == False:								# Unselect everything unless this is an deselect action ###DESIGN:!!! Bad & limiting design... remove!
		bpy.ops.mesh.select_all(action='DESELECT') 
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')		###DESIGN:!!!! Really force this?  Can remove??

	#=== Find the requested vertex group and select its vertices ===
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)
	if (nVertGrpIndex != -1):
		oMeshO.vertex_groups.active_index = nVertGrpIndex
		if bDeselect:
			bpy.ops.object.vertex_group_deselect()
		else:
			bpy.ops.object.vertex_group_select()
		oVertGrp = oMeshO.vertex_groups[nVertGrpIndex]
		return oVertGrp 
	else:
		sMsg = "\n###ERROR: VertGrp_SelectVerts() could not find vert group '{}' in mesh '{}'\n".format(sNameVertGrp, oMeshO.name)
		if bThrowIfNotFound:
			raise Exception(sMsg)
#		else:		###DESIGN: Consider printing if not found?
#			print(sMsg)

def VertGrp_AddToSelection(oMeshO, sNameVertGrp):		# Adds to selection the specified vertex groups.  Assume mesh already in edit mode 
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)		###OBS: Replace with regex version
	if (nVertGrpIndex != -1):
		oMeshO.vertex_groups.active_index = nVertGrpIndex
		bpy.ops.object.vertex_group_select()
		oVertGrp = oMeshO.vertex_groups[nVertGrpIndex]
		return oVertGrp 
	else:
		raise Exception("\n###EXCEPTION: VertGrp_SelectVerts() could not find vert group '{}' in mesh '{}'".format(sNameVertGrp, oMeshO.name))

def VertGrp_AddToSelection_RegEx(oMeshO, rexPattern):		# Adds to selection the specified vertex groups.  Assume mesh already in edit mode 
	for oVertGrp in oMeshO.vertex_groups:
		if re.search(rexPattern, oVertGrp.name):
			oMeshO.vertex_groups.active_index = oVertGrp.index
			bpy.ops.object.vertex_group_select()

def VertGrp_RemoveAll(oMeshO):
	for oVertGrp in oMeshO.vertex_groups:
		oMeshO.vertex_groups.remove(oVertGrp)
	
def VertGrp_RemoveByNameInv(oMeshO, sNameSearchPattern):		# Removes vert groups that do NOT have 'sNameSearchPattern' in their name
	for oVertGrp in oMeshO.vertex_groups:
		if oVertGrp.name.find(sNameSearchPattern) == -1:
			oMeshO.vertex_groups.remove(oVertGrp)
	
def VertGrp_RemoveVertsFromGroup(oMeshO, sNameVertGrp):			# Removes currently selected vertices from group vertex group 'sNameVertGrp' from specified mesh.  Assumes mesh is selected and opened in edit mode
	nVertGrpIndex = oMeshO.vertex_groups.find(sNameVertGrp)
	if (nVertGrpIndex == -1):
		print("\n\n###ERROR: VertGrp_RemoveVertsFromGroup() could not find vertex group '" + sNameVertGrp + "'")
		return
	oMeshO.vertex_groups.active_index = nVertGrpIndex
	bpy.ops.object.vertex_group_remove_from()

def VertGrp_RemoveNonBones(oMeshO, bCleanUpBones=False):	 # Remove non-bone vertex groups so skinning normalize & fix below will not be corrupted by non-bone vertex groups  ###IMPROVE: Always clean (remove arg?)
	if (len(oMeshO.vertex_groups) == 0):
		return
	aVertGrpToRemove = []
	for oVertGrp in oMeshO.vertex_groups:
		if oVertGrp.name[0] == G.C_VertGrpPrefix_NonBone:  # Any vertex groups that starts with '_' is a non-bone and has no value for Client
			aVertGrpToRemove.append(oVertGrp)
	for oVertGrp in aVertGrpToRemove:
		oMeshO.vertex_groups.remove(oVertGrp)
# 	if (bCleanUpBones):			###DEV24:!!! ###DESIGN:!!!!!!!!
# 		#bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
# 		bWasHidden = oMeshO.hide
# 		if (bWasHidden):
# 			Util_HideMesh(oMeshO)
# 		oMeshO.hide = False
# 		bpy.ops.object.mode_set(mode='EDIT')
# 		bpy.ops.mesh.select_all(action='SELECT')
# 		bpy.ops.object.vertex_group_clean(group_select_mode='ALL')	# Clean up empty vert groups new Blender insists on creating during skin transfer
# 		bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)  # Limit mesh to four bones each   ###CHECK: Possible our 'non-bone' vertgrp take info away???
# 		bpy.ops.object.vertex_group_normalize_all(lock_active=False)
# 		bpy.ops.mesh.select_all(action='DESELECT')
# 		bpy.ops.object.mode_set(mode='OBJECT')
# 		if (bWasHidden):
# 			gBL_Util_Hide(oMeshO)





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
	def __init__(self):			###INFO: Struct.Pack args: b=char B=ubyte h=short H=ushort, i=int I=uint, q=int64, Q=uint64, f=float, d=double, s=char[] ,p=PascalString[], P=void*
		self.bClosed = False
		self.AddUShort(G.C_MagicNo_TranBegin)
	
	def CloseArray(self):
		if self.bClosed == False:			# Add trailing magic number when array requested from Unity.
			self.AddUShort(G.C_MagicNo_TranEnd)  
			self.bClosed = True;
		return self
	
# 	def GetNumberOfArrayElements(self):			###IMPROVE: Create a reliable 'GetNumberOfArrayElements() function?
# 		return self.nTimesAddFunctionCalled			# This only returns the 'number an AddXXX() function was called.  Assumes you added always the same data for this value to make sense to the caller! 

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

	def AddVector(self, vecBlender):			###IMPORTANT: This is the ONE place where we convert all vectors to traverse coordinate systems from Blender to Unity ###CHECK:!!!!!
		vecUnity = G.VectorB2U(vecBlender)
		self += struct.pack('fff', vecUnity.x, vecUnity.y, vecUnity.z)
	
	def AddQuaternion(self, quat):
		self += struct.pack('ffff', quat.x, quat.y, quat.z, quat.w)
	
	def AddString(self, sContent):	 ###INFO: Proper way to pack Pascal string
		sContentEncoded = sContent.encode()
		nLenEncoded = len(sContentEncoded) + 1
		if nLenEncoded > 255:
			raise Exception("Error in CByteArray.AddString().  String '{}' is too long at {} characters".format(sContent, nLenEncoded))
		self += struct.pack(str(nLenEncoded) + 'p', sContentEncoded)  ###INFO: First P = Pascal string = first byte of it is lenght < 255 rest are chars

	def AddBone(self, oBone):				# Recursive function that sends a bone and the tree of bones underneath it in 'breadth first search' order.	 Information sent include bone name, position and number of children.
		#print("- AddBone '{}'  P={}   Q={}".format(oBone.name, oBone.head, oBone.matrix.to_quaternion()))
		self.AddString(oBone.name)			# Precise opposite of this function found in Unity's CBodeEd.ReadBone()
		self.AddVector(oBone.head)	# Obtain the bone head and convert to client-space (LHS/RHS conversion)		 ###INFO: 'head' appears to give weird coordinates I don't understand... head_local appears much more reasonable! (tail is the 'other end' of the bone (the part that rotates) while head is the pivot point we need

		#=== Send the quaternion as an axis vector for easier Blender-to-Unity domain traversal via well-understood vectors ===
		quatBlender = oBone.matrix.to_quaternion()
		self.AddVector(quatBlender.axis)
		self.AddFloat(-quatBlender.angle)			###NOTE20:!!! We send the INVERSE of the angle of axis-angle as (by observation) the non-inverse appears all wrong.  (Inversing all angles looks great)

		if "RotOrder" in oBone:
			self.AddString(oBone["RotOrder"])
		else:		
			self.AddString("XYZ")		###NOTE: Doesn't matter what we send on generated bones... They are never rotated anyways!
		if "Rotations" in oBone:
			self.AddByte(len(oBone["Rotations"]))
			for sRotationSerialization in oBone["Rotations"]:
				self.AddString(sRotationSerialization)
		else:
			self.AddByte(0)

		self.AddUShort(len(oBone.children))
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
	oMeshO = SelectObject(sNameObject)
	bpy.ops.object.mode_set(mode='EDIT')		###IMPROVE:!!!!!! Rewrite all this mode-switch code into a wrapper function that senses the current mode and switches to the desired mode!!!
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
	oMeshO = SelectObject(sNameObject)
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
	oMeshO = SelectObject(sNameObject)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMeshO.data)
	for nLayer in range(len(bm.verts.layers.int)):
		oLayer = bm.verts.layers.int[nLayer]
		print("DataLayer:  Mesh '{}'  #{}  Layer '{}'".format(sNameObject, nLayer, oLayer.name))
	bpy.ops.object.mode_set(mode='OBJECT')


def DataLayer_CreateVertIndex(sNameMesh, sNameLayer):
	"Prepare an original untouched mesh for editing by storing its original vert indices in a custom data layer"
	DataLayer_RemoveLayerInt(sNameMesh, sNameLayer)
	oMesh = SelectObject(sNameMesh)
	bpy.ops.object.mode_set(mode='EDIT')
	bm = bmesh.from_edit_mesh(oMesh.data)
	print("DataLayer: Creating int layer '{}' on mesh '{}'".format(sNameLayer, sNameMesh))
	oLayVertsSrc = bm.verts.layers.int.new(sNameLayer)
	for oVert in bm.verts:
		oVert[oLayVertsSrc] = oVert.index + G.C_OffsetVertIDs          # We apply an offset so we can differentiate between newly added verts 
	bpy.ops.object.mode_set(mode='OBJECT')

#---------------------------------------------------------------------------	BONES
def Bones_RemoveBones(oArm, rexPattern):		# Armature node object MUST be selected and in edit mode!	
	print("=== Bones_RemoveBones('{}', '{}') ===".format(oArm.name, rexPattern))
	if len(oArm.edit_bones) == 0:				# If armature object is not selected and opened in edit mode, edit_bones will be empty!
		raise Exception("\n###EXCEPTION: Bones_RemoveBones() has zero edit_bones!  Selected and opened in edit mode??")
	aBonesToDelete = []
	for oBone in oArm.edit_bones:
		if re.search(rexPattern, oBone.name):
			aBonesToDelete.append(oBone)
	for oBone in aBonesToDelete:
		print("- Removing bone '{}'".format(oBone.name))
		oArm.edit_bones.remove(oBone)
		

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
# 	CBody.SlaveMesh_DefineMasterSlaveRelationship("Woman", "BreastLCol", 0.000001, bMirror=False, bSkin=False)
# 	CBody.SlaveMesh_DefineMasterSlaveRelationship("Woman", "BreastRCol", 0.000001, bMirror=False, bSkin=False)
# 
# 	#===== Define cloth colliders =====			###IMPROVE: Auto-generate these from a naming pattern??
# 	CBody.SlaveMesh_DefineMasterSlaveRelationship("Woman", "BodyColCloth-Top", 0.000001, bMirror=True, bSkin=True)


###OBS: Recursive search through BMesh topology... replaced by KDTree but can still be useful in some cases?
# def Util_FindCloseVertAlongEdges_RECURSIVE(setVertsTooCloseToRimVertBodys, oVertRoot, oVert, nDistMax):
#     # Recursive function used in penis fitting algorithm.  Traverses the mesh geometry around 'oVertRoot' to insert into 'setVertsTooCloseToRimVertBodys' the verts within 'nDistMax' distance
#     for oEdge in oVert.link_edges:
#         oVertNeighbor = oEdge.other_vert(oVert)
#         if oVertNeighbor not in setVertsTooCloseToRimVertBodys:                    # Avoid verts that have already been traversed
#             if oVertNeighbor.select == False:                           # Avoid verts that are selected (they are the ones at root of this search)
#                 vecRootToThisVert = oVertNeighbor.co - oVertRoot.co 
#                 nLenRootToThisVert = vecRootToThisVert.length
#                 if nLenRootToThisVert < nDistMax:                       # Avoid verts that are too far from root 
#                     setVertsTooCloseToRimVertBodys.add(oVertNeighbor)
#                     #print("-- Vert {:5d} gets {:5d} at dist {:.5f} of {:.5f}".format(oVertRoot.index, oVertNeighbor.index, nLenRootToThisVert, nDistMax))
#                     Util_FindCloseVertAlongEdges_RECURSIVE(setVertsTooCloseToRimVertBodys, oVertRoot, oVertNeighbor, nDistMax)     # Recursively call self on this neighboring vert so we recursively find ALL verts within 'nDistMax' of 'oVertRoot'

#---------------------------------------------------------------------------	
#---------------------------------------------------------------------------	APP GLOBAL TOP LEVEL
#---------------------------------------------------------------------------	

####OBS?
bpy.app.handlers.load_post.clear()
bpy.app.handlers.load_post.append(Event_OnLoad)
bpy.app.handlers.scene_update_post.clear()
#bpy.app.handlers.scene_update_post.append(Event_OnSceneUpdate)		 ###DESIGN ###IMPROVE Turn on/off this expensive polling only when needed?

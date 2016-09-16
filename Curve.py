import bpy
import sys
import bmesh
from math import *
from mathutils import *
import struct

from gBlender import *
import G
import Client



###NEXT:
# Just about ready to insert into Unity
    # Unity needs to query how many curves and their points
    # Need a CCurve, CCurvePt (hotspots) moving and redrawing their cuttersasmesh!



# Need to separate between updates to cutter curves and the actual cutting
# Graceful update without creating a new cloth!! 

# Fixed mirrored but the 'demo cutter mesh' not mirrored... clarify!
    # Revisit usage of MirroX mod
# WOuld be nice to have cleaner scene start!
# Delete cutter objects upon start of new job
# Beziers still as children or siblings?
# Prevent cutter plane destruction for debugging?
#IDEA: Expose smoothing iterations to Unity for each curve!
#IDEA: Also need to expose mirror!

# Weird handles and curves now... not auto?
# Rebuild fails cuz of no name on self.oCurveO?

# Need to create from plain 3D points and also update... without destroying?

# CCurve class.  Owned by its attached CCloth in _aCurves
# CCloth based on body suit, and is cut by collection of curves
# Unity: Merge into normal CCloth with all its baggage? (e.g. skinned half, simulation, etc)... or new class?
#  Benefits: 1-1 relationship between both classes on both sides
# Need a CCurvePt class on both sides?
#  Loaded from just a few points stored in Blender sub-objects (acting as 'recipes')

###TODO###
# Have to show the whole thing in Unity: Semi-transparent body suit, Cutter curve meshes, Cut cloth


###IDEAS###
# 'Extra cutter points'.  Can be stored in recipe and are define as an interleaving point between two permanent points




class CCurve:
    def __init__(self, oCloth, sType):
        self.oCloth = oCloth
        self.sName = "Curve-" + sType
        self.sType = sType
        self.bAboutBodyCenter = (self.sType.find("-Side") == -1)  ###WEAK!!! ###DEV    # Curve is defined about body center (only points on left are specified, right points derived by symmetry from left points)
        self.bInvertCutterNormals = False#(self.sType.find("-Bottom") != -1)      ###HACK!!!
        self.oCurveO = None                             # The actual Blender curve we encapsulate & control
        self.oCutterO = None                            # The cutter object (responsible for cutting cloth and based on oCurveO)
        self.oCutterAsMeshO = None                      # The 'cutter as mesh' representing this curve as a visible mesh in Unity
        self.oSpline = None                             # The first (and only) spline of self.oCurveO
        self.oCurveSource = None                        # The curve 'source'.  Hierarchy of Blender empty objects the curve is created from (and updated from)
        self.oCurveCenterPt = None                      # The center point of the curve.  Used to define important cutter center.
        
        self.oCurveSource = bpy.data.objects[sType]     # Obtain reference to the root object containing the recipe this curve is based on

        DeleteObject(self.sName)       ###LEARN: Previous caused bad blender crash with old bp        # The above caused that bad Blender C++ crash with the 'Gives UnicodeDecodeError: 'utf-8' codec can't decode byte 0xdd in position 0' error
        bpy.ops.curve.primitive_bezier_curve_add()
        self.oCurveO = bpy.context.object
        self.oCurveO.parent = bpy.data.objects[G.C_NodeName_Curve]
        self.oCurveO.name = self.oCurveO.data.name = self.sName
        self.oCurveO.name = self.oCurveO.data.name = self.sName
        self.oCurveO.rotation_mode = 'XYZ'
        #OLD oCurveO.rotation_euler.x = radians(90)          ###LEARN: How to rotate in eulers
        self.oCurveO.data.dimensions = "3D"
        self.oCurveO.data.fill_mode = "FULL"
        self.oSpline = self.oCurveO.data.splines[0]
        self.oSpline.use_cyclic_u = True     ####DEV!!!!           # Symmetry curves are by definition cyclic (e.g. side curve), non-symmetry (e.g. neck opening) are non-cyclic as their points are mirrored with a mirror modifier
        self.oSpline.resolution_u = 24                      ###TODO!!!   # At this point we have a bezier curve with one spline containing two control points

        #=== Hide our yet-unformed curve and delete previous iteration of cutter plane ===
        Util_HideMesh(self.oCurveO)
        DeleteObject(self.oCurveO.name + G.C_NameSuffix_CutterPlane)


    def UpdateCutterCurve(self):
        #=== Iterate through all curve points (not duplicate for symmetry) and add to curve
        bpy.context.scene.cursor_location = Vector((0,0,0))     # All dependant code requires cursor to be at origin!
        
        nPt = 0
        nNumCurvePtsLess1 = len(self.oCurveSource.children) - 1
        for oCurvePtO in self.oCurveSource.children:
            #print("CurveDev Pt: ", oCurvePtO, oCurvePtO.location)
            if (oCurvePtO.name.find("-Center") != -1):
                self.oCurveCenterPt = oCurvePtO
                print("Center " + oCurvePtO.name + " at " + str(oCurvePtO.location))
            else:
                oCurvePt = self.EditCurvePoint(nPt, oCurvePtO.location)
                if (len(oCurvePtO.children)):                       # Process children of curve points as Bezier
                    oCurveBezierO = oCurvePtO.children[0] 
                    bInvertSymmetrizeBezierAboutX = (nPt == nNumCurvePtsLess1)
                    self.UpdateCurveBezier(oCurvePt, bInvertSymmetrizeBezierAboutX, oCurveBezierO.location.x, oCurveBezierO.location.y, oCurveBezierO.location.z)
                nPt += 1
    
        #=== Now iterate through the curve again in reverse order if mirrored (without the extremities) to add the symmetry points ===
        if self.bAboutBodyCenter:
            for nCurvePt in range(nNumCurvePtsLess1-1, 1, -1):      # Iterates backward without both extremities. Note the weirdness in reverse ranges!
                oCurvePtO = self.oCurveSource.children[nCurvePt]
                if (oCurvePtO.name.find("-Center") == -1):
                    #print("CurveDev Pt REV:", oCurvePtO, oCurvePtO.location)
                    vecLoc = oCurvePtO.location.copy()
                    vecLoc.x = -vecLoc.x                            # Point is for the other side of the body
                    oCurvePt = self.EditCurvePoint(nPt, vecLoc)
                    nPt += 1
            
        self.RebuildCurve()
        

    def RebuildCurve(self):              # Rebuild the curve & cutter... typically done after client has changed on or more curve points
        bpy.context.scene.cursor_location = Vector((0,0,0))     # All dependant code requires cursor to be at origin!

        #=== Create a duplicate of the user's curve and set its parent for cleaner node structure ===
        self.oCutterO = DuplicateAsSingleton(self.oCurveO.name, self.oCurveO.name + "-" + G.C_NodeName_Cutter, G.C_NodeFolder_Game, True)
        self.oCutterO.parent = bpy.data.objects[G.C_NodeName_Cutter]           ###SOON: Curve quality!
    
        #=== Convert the spline curve to a mesh to 'bake' the few bezier points into a fanned-out version and 'shrinkwrap' to the basis mesh to get much closer to mesh surface than the user's curve === 
        bpy.ops.object.convert(target='MESH')            
        oModShrinkwrap = self.oCutterO.modifiers.new('SHRINKWRAP', 'SHRINKWRAP')
        oModShrinkwrap.target = self.oCloth.oMeshClothSource.oMeshO
        AssertFinished(bpy.ops.object.modifier_apply(modifier=oModShrinkwrap.name))
    
        #=== Convert back to a curve so that we can easily display a solid curve by adding a bevel object ===        
        bpy.ops.object.convert(target='CURVE')           # Re-convert to spline now that we have a 'baked' representation with about a hundred vertices.
        bpy.ops.object.mode_set(mode='EDIT')
        for nSmoothIterations in range(5):        ###TUNE     ###LEARN: This is how to smooth a curve!  (Smooth as a mesh makes non-mirror-x centers diverge, and looptools doesn't smooth enough)
            bpy.ops.curve.smooth()
        bpy.ops.object.mode_set(mode='OBJECT')
        self.oCutterO.data.resolution_u = 1
          
#         #=== Create the 'CutterAsMesh' version rendered in Unity to represent our cutter curve ===
#         self.oCutterAsMeshO = DuplicateAsSingleton(self.oCutterO.name, self.oCutterO.name + "-CutterAsMesh", None, False)        ###DESIGN: Hide source a pain...
#         self.oCutterAsMeshO.parent = bpy.data.objects["CutterAsMesh"]
#         self.oCutterAsMeshO.data.bevel_object = bpy.data.objects[G.C_NodeName_CurveBevelShape]
#         bpy.ops.object.convert()                # Convert to mesh
# 
#         #=== Add a mirror modifier to the cutter mesh whether the curve is symmetrical or not so user sees cuts for both sides of the body ===
#         if (self.bAboutBodyCenter == False):         ###DEVNOW!!!  Mirror all fucked up!
#             oModMirrorX = Util_CreateMirrorModifierX(self.oCutterAsMeshO)
#             AssertFinished(bpy.ops.object.modifier_apply(modifier=oModMirrorX.name))        
#         Util_ConvertToTriangles()      # Convert to triangles Client needs
        
   

    def EditCurvePoint(self, nPt, vecLocation):
        if (nPt >= len(self.oSpline.bezier_points)):
            self.oSpline.bezier_points.add()                         # Add another control point to the curve
        oCurvePt = self.oSpline.bezier_points[nPt]
        oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'AUTO'     # Curve points are auto until set to free by gBL_Curve_UpdateCurveBezier() 
        vecCurvePtBlender = vecLocation  ###DEV!!: G.VectorC2B(vecLocation)        # As we're receiving a 3D vector without going through the conversion to verts done while sending a mesh we must convert the coordinate manually here (and likewise when we obtain coordinate from client)
        oCurvePt.co = vecCurvePtBlender
        
        ####DEV!!! === Calculate the snap position of curve point on current cloth manually to avoid the complete rebuild overhead ===
        #oBaseClothO = bpy.data.objects[sNameBaseCloth]                  ###CHECK: For some reason in this context we don't need stupid 90 degree rotation back and forth?  WHY???
        #aClosestPtResults = oBaseClothO.closest_point_on_mesh(vecCurvePtBlender)   ###LEARN: This call fails early in blender load process as it complains mesh has no data.  (Forced late update and kludge code!)
        #vecCurvePtAdjClient = G.VectorB2C(aClosestPtResults[0])      # Return the adjusted point position in client-space.
        
        return oCurvePt

    def UpdateCurveBezier(self, oCurvePt, bInvertSymmetrizeBezierAboutX, x, y, z):
        oCurvePt.handle_left_type = oCurvePt.handle_right_type = 'FREE'
        if (bInvertSymmetrizeBezierAboutX):
            oCurvePt.handle_left  = Vector(( x, y, z))     ###G.VectorC2B(
            oCurvePt.handle_right = Vector((-x, y, z))
        else:
            oCurvePt.handle_left  = Vector((-x, y, z))        # As we're receiving a 3D vector without going through the conversion to verts done while sending a mesh we must convert the coordinate manually here (and likewise when we obtain coordinate from client)
            oCurvePt.handle_right = Vector(( x, y, z))


    def CutClothWithCutterCurve(self, bInvertCut):
        bpy.context.scene.cursor_location = Vector((0,0,0))     # All dependant code requires cursor to be at origin!

        #=== Obtain parameters stored in curve object on how to perform cut ===
        oMeshO = self.oCloth.oMeshClothCut.oMeshO           ###CLEANUP: From port... make a more natural integration with class!!
        oMesh = oMeshO.data
        oCurveO = self.oCutterO             ###DEV: Curve = cutter??
        vecCurveCenter = self.oCurveCenterPt.location
        bCutAboutLeftAndRight = (self.bAboutBodyCenter == False)          # Curves that are defined around body center (e.g. neck opening, bottom opening, etc) only need one cut (different than arm left and right, leg left and right, etc)
        aBorderLocatorVertPos = {}                      ###OBSOLETE?
        
        ###OLD bCutAboutLeftAndRight = oCurveO.data.splines[0].use_cyclic_u       # Symmetry curves are by definition cyclic (e.g. side curve), non-symmetry (e.g. neck opening) are non-cyclic as their points are mirrored with a mirror modifier
        nSymmetryIterations = bCutAboutLeftAndRight + 1  # The symmetry cutters (e.g. arms and legs) have this set to two so next big loop runs twice for each side
        ###OLD vecCurveCenter = oCurveO.matrix_world * vecCurveCenter      # Curve is rotated 90 degrees like every other object, convert location of center to its local coordinates so all points on cutter mesh live in the same spacial coordinate system
    
        #=== Iterate once or twice through all our pins depending if we're a symmetry or not ===
        for nSymmetryRun in range(nSymmetryIterations):
            #=== Determine the full 'cut name' by adding the L/R suffix if this is a symmetry curve
            sCutName = oCurveO.name
            if nSymmetryIterations > 1:                                 # The name of the cut is suffixed only for symmetrical cuts (e.g. ArmL and ArmR)
                sCutName += G.C_SymmetrySuffixNames[nSymmetryRun]
            print("== ApplyCut() on mesh '{}' cut '{}' bAboutBodyCenter = {} bInvertCutterNormals = {}".format(oMeshO.name, sCutName, self.bAboutBodyCenter, self.bInvertCutterNormals))
    
            #=== Create a temporary duplicate of the 'presentation curve' and remove its spline bevel so it becomes a usable flat curve again ===
            ###DEVF: Need to delete first??
            oCutterBooleanO = DuplicateAsSingleton(oCurveO.name, oCurveO.name + G.C_NameSuffix_CutterPlane, None, False)
            oCutterBooleanO.parent = bpy.data.objects["CutterPlanes"]        ###WEAK
            oCutterBooleanO.data.bevel_object = None            # Remove the bevel object of the spline that was used to render with 'thickness' where the cut is to occur
            oCutterBooleanO.draw_type = "WIRE"
            oCutterBooleanO.show_all_edges = True
            
            #=== Remove the mirror modifier from the cutter if we're a mirror-x as we need to run the cut twice with single cutters in order to properly prepare each individual border ===
            if bCutAboutLeftAndRight:       ###CHECK: Needed?
                while(len(oCutterBooleanO.modifiers) > 0):
                    oCutterBooleanO.modifiers.remove(oCutterBooleanO.modifiers[0])

            #=== Set the cutter's origin to the user-supplied center point and resize all border points so that all points of the curve are outside the mesh to be cut ===
            aContextOverride = AssembleOverrideContextForView3dOps()    ###IMPORTANT: For view3d settings to be active when this script code is called from the context of Client we *must* override the context to the one interactive Blender user uses.
            SetView3dPivotPointAndTranOrientation('CURSOR', 'GLOBAL', False)
            bpy.context.scene.cursor_location = vecCurveCenter      # Now set the fit curve origin to the user-supplied center for this user curve.  (This will therefore set the normals of each vertex on the curve to go from origin to each vertex = perfect for us to project out of cloth with shrink/fatten
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.select_all(action='SELECT')
            bpy.ops.transform.resize(aContextOverride, value=(1.2,1.2,1.2))
            bpy.ops.curve.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
    
            #=== Convert the curve into a mesh, extrude the mesh's points and collapse them to a single vertex to meet at center to form faces for boolean ===
            bpy.ops.object.convert(target='MESH')               # Convert to a mesh            
            oCutterBoolean = oCutterBooleanO.data
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.extrude_edges_indiv()          ###LEARN: extrude_vertices_move() only moves verts with no edges around -> useless!
            bpy.ops.mesh.merge(type='CURSOR')           ###CHECK: Was not working before??
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent()          # Update the normals to present unified normals (very important) for boolean
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.scene.cursor_location = Vector((0,0,0))
            
            ###CHECK === Mirrored cutters may not have their first and last points exactly at x=0 even if clients specifies these as points (errors inserted when curve is converted??)  Anyways we ensure a watertight cutting mesh with remove_doubles to cover this case but a better fix would be to fix the curve!
            if bCutAboutLeftAndRight == False:          ###NEEDED?
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles(threshold=0.005)  
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
            
            ###CHECK: merge to center above does this ok???    
            oCutterBoolean.vertices[len(oCutterBoolean.vertices) - 1].co = vecCurveCenter  # The added central 'collapse' point (currently at center of border verts) needs to be moved to our center pin ===  # Workaround to bpy.ops.mesh.merge not reliably merging to cursor -> fetch the last vert (the one that just merged) and move it to where it needs to be... 
    
            #=== If this is the 2nd 'symmetry run' invert the cutter about X to cut the other side of body and inver the normals ===
            if (nSymmetryRun > 0):                                    
                oCutterBooleanO.scale.x *= -1
                self.InvertNormals()
                
            if (self.bInvertCutterNormals):     ###PROBLEM?  The two inversions can interfere with one another??                                    
                self.InvertNormals()
            
    
            #=== Create a boolean modifier and apply it to remove the extra bit beyond the current cutter ===
            SelectAndActivate(oMeshO.name)
            oModBoolean = oMeshO.modifiers.new('BOOLEAN', 'BOOLEAN')
            oModBoolean.object = oCutterBooleanO
            if (bInvertCut):
                oModBoolean.operation = 'INTERSECT'            ###LEARN: Difference is the one we always want when cutting as the others appear useless!  Note that this is totally influenced by side of cutter normals!!
            else:
                oModBoolean.operation = 'DIFFERENCE'            ###LEARN: Difference is the one we always want when cutting as the others appear useless!  Note that this is totally influenced by side of cutter normals!!
            #self.HALT
            AssertFinished(bpy.ops.object.modifier_apply(modifier=oModBoolean.name))  ###LEARN: Have to specify 'modifier' or this won't work!
            oCutterBooleanO.scale.x *= -1                            # Revert the cutter back to non-inverted if inverted for 2nd 'symmetry' run above
            
            #=== Boolean cut basically destroyed all info such as vert groups, vertID, vert and edge data... anything we could use to store what verts were assigned to each border ===
            #=== In order to overcome this boolean destruction of most mesh data, we remember for each border the coordinates of one vertex on that border so that we may later rebuild the list of vert for all borders ===
            #=== Our first step is to start from the center vert, walk the first edge of that vert to find a vertex on the new border, store its position in aBorderLocatorVertPos and delete the (unwanted) mesh cutter central vert ===
            ###LEARN: Applying boolean modifier will destroy the mesh's vertex groups, the IDs of verts and probably edges and polys, vert attribs like bevel_weight, edges attribs like crease and bevel_weight BUT keeps face material!!
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(oMesh)
            bm.verts.ensure_lookup_table()
            oVertMeshCutterCenter = bm.verts[len(bm.verts) - 1]             # The boolean cut has created an a vert where the cutter center vert was.  We don't need our cloth as solid so we delete the center vert' (still at 3d cursor) and remove it to restore the cloth mesh to non-solid  ###CHECK: We are assuming (so far so good) that the collapsed vert is the last one in the cloth.
            oEdgeFirst = oVertMeshCutterCenter.link_edges[0]                # Select the first edge of that central vert to point the way toward a vert on the border
            oVertLocatorOnBorder = oEdgeFirst.other_vert(oVertMeshCutterCenter) # Obtain reference to the other side of that 'first edge'.  The 3D coordinate of that 'special vert' will act as the key to rebuild the list of verts for this border once all the highly-destructive boolean operations have been done for all borders on this mesh
            oVertMeshCutterCenter.select = True                             # Select the unwanted central vert...
            bpy.ops.mesh.delete(type='VERT')                                # And delete it.  We now have non-manifold border we must cleanup!
            #print("-Cut: Locator Vert for border {} at {} and index {}".format(oCurveO.name, oVertLocatorOnBorder.co, oVertLocatorOnBorder.index))
            aBorderLocatorVertPos[sCutName] = oVertLocatorOnBorder.co.copy()    # Store for this border the 3D coordinates of this 'border locator vert' so we can reconstruct what verts form each border after all destructive boolean ops have occured.

            Util_HideMesh(oCutterBooleanO)
            
        #=== Boolean cut leaves quads and ngons on the border and triangles give us more control on what to delete -> Triangulate before border cleanup ===
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()        ###REVIVE: use_beauty=True
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        #=== Hide back internal objects to avoid cluttering display ===
        Util_HideMesh(self.oCutterO)


    def InvertNormals(self):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()  
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        





#---------------------------------------------------------------------------    
#---------------------------------------------------------------------------    ###OBS
#---------------------------------------------------------------------------    

# def gBL_Curve_GetCutterAsMesh(sNameCutterAsMesh):         # Called by Client to force a rebuild of this curve & cutter and create & return a mesh copy of the cutter that can be displayed in Client 
#     if sNameCutterAsMesh.startswith(G.C_NamePrefix_CutterAsMesh) == False:
#         return "ERROR: gBL_Curve_GetCutterAsMesh() did not receive a cutter refresh request that begins with '{}'".format(G.C_NamePrefix_CutterAsMesh)
#     sNameCurve  = sNameCutterAsMesh[len(G.C_NamePrefix_CutterAsMesh):]          # Extract the curve and cutter's object name from the client's request.
#     sNameCutter = sNameCurve + "-" + G.C_NodeName_Cutter
#     if sNameCurve not in bpy.data.objects:
#         return "ERROR: gBL_Curve_GetCutterAsMesh() could not find curve object '{}' from request '{}'".format(sNameCurve, sNameCutterAsMesh)
# 
#     gBL_Curve_Rebuild(sNameCurve)              # Rebuild the curve and cutter so we can convert the cutter to a mesh and send to client.         
#     oCutterAsMeshO = DuplicateAsSingleton(sNameCutter, sNameCutterAsMesh, G.C_NodeFolder_Game, False)        ###DESIGN: Hide source a pain...
#     bpy.ops.object.convert()                # Convert to mesh
#     oCutterAsMeshO.data.name = oCutterAsMeshO.name    # Set the name of the just-created mesh to the name of the object.
#     oCutterAsMeshO.parent = bpy.data.objects[G.C_NamePrefix_CutterAsMesh]     # Set parent to its utility node folder to get it out of the way and to facilitate mass cleanup
#     Util_ConvertToTriangles()      # Convert to triangles Client needs
#     return Client.gBL_GetMesh(oCutterAsMeshO.name)




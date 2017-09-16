#===========================================================================
###DOCS24: Penis rig creation - June 2017

#=== DEV ===
#- Modify tip to have the last slice bones
#- Non bones on some particles (e.g. tip most, last slice?)  Test after Unity

#- Tip being a real bone causes big problems... make non-bone?
#- wtf bones at beginning??
#- Remove guide path?  Favor penetration funnel?
#- Penis rig needs deletion of old Penis bones before re-run.  Write helper! 
#- Rig now takes super long... can improve?
#- Concept of real bones and fake bones, real slice and fake?
#- Change constants to be class-based

###PROBLEM: Full fit and rig must be done from base woman to own clean shemale mesh... some manual re-parenting now required!!

#- Removed the tipmost bones as they were too finely spaced and not contributing in Unity... but now Unity no longer has info for flex collider!  
    #- Could create fake bones?  Or store their info for access on demand?
#- Problem with cock participating in body's flex collider -> it must have its own!
#- Root penis bones in Unity all screwed up!
#- Problem with dynamic bones!  Can't change [WomanA].  Must change copy!!
#- Now need to serialize all the bones (more than 255 now?) and create Penis structure as we go.
    #- Runtime code for CBSkin sends flattened name list then vert weights... not hierarachy... change so we get hierarchy too?
#- Annoyting to have to create shape keys to run in game
#- Uretra = Penis-I.  J is useless... fix this?
#- Work out what to send Unity... Can it just read everything it needs from the bones??
#- Do we still need _CSoftBody_Penis???  Remove then
#- Unity needs easy access to uretra position!
#?- Penis bone hierachy is off by one... rotating a central bone looks weird.
#- Finalize # of slices...
    #- Revis this 'add one stuff'
#- Need to re-blend texture?
#- Finalize # of slices
#- Tune bone envelope size!
#- How to tell Unity penis diameter?
#- We don't really need PhysX bones at tip like that... just for Flex and fluid collider.  Keep anyway?
#- Crappy implementation for very last '+1' slice... needed for the position but what about these bones??


#=== TODO ===
#- Really crappy arguments being fed into CPenisRig.  Need to better 'glue' CPenisFit and CPenisRig
    #- Belong in different files as one is ship-time only?
#- Base not right... needs to go under balls at weird angle.  (Does it matter?  Will we every move any bone in slice A?)
#- Scrotum parent of penisa?
#- Finalize bone names!
#- Need to smooth around rim after rig runs?
#- Need to specify man / shemale in arguments for proper node naming

#=== QUESTION ===
#+ What to do with new bones?  Send them at design time or at play time as extras???  Make a permanent part of bone rig?
#- Only send Unity our structure and it makes up mesh, bones, etc?
    #- Then what about skinned mesh assignment to our many bones?
#- Our helper structures are hardly useful... keep?
#- Currently center vert is parent of the verts around it... Does rotation make sense about its position?  shift by one?  
#- Does this work properly on small penis?
    #- Keep in mind absolute definition of scrotum base

#=== PROBLEMS ===
#? The cavity under glans makes closest vert search too much on one side.  A problem?
#- tip slice center way too far!
#- Useless vert groups left over once we normalize (zero-weight vert groups removed!)

#=== IMPROVE ===
#- Scrotum very basic.  improve its bones?
#- Rotate about base could use work... a better center?
    #+ Revise bone position of each slice master bone!! (Shift it toward base somewhat??)

#=== NEEDS ===
#- Have its own (separate) flex collider and repell fluid particles
#- Have PhysX bones and capsule colliders for raycasting and repelling of PhysX shapes (fingers, arms, etc)
#- Enable user control to bend penis as needed (curvature and at base)
#- Enable 'penis growth' via Flex shape expansion
#- Be repelled by other Flex particles (self's kinematic torso & leg particles) and two-way repelling of clothing.

#=== DESIGN ===
# Penis rig is formed of CPenisRigSlice and CPenisRigSliceVerts:
#- CPenisRigSlice cuts up penis at a given length to form 8 CPenisRigSliceVerts and once center vert
#- The octagon is 'fitted' to the closest vert at that slice position.
#- Center verts will from where the PhysX bones are.  This center vert is also the 'root bone' of each of the edge vert bones

#=== WISHLIST ===
#- Create a 'visualization mesh'? 

#=== PROBLEMS ===















###DOCS21: Penis automatic mounting:  May 2017 
#=== DEV ===
#- Really crapped out the invoke flow and the calling arguments to everything here... re-connect to top level properly!

#=== DESIGN ===
#- Currently game fed a manually cooked version.  Need to automate all this!!  (Breaks flow from CBody()
    #- Currently hard-coding woman mesh and broke its morphing capacity... 
#+++ Currently CPenisFit is generating a new woman because its geometry has changed around penis hole.  It is super unfortunate we have to store this... enable this mesh version to be created from stock woman at gametime?
#- Need to completely revising entire flow of design-to-gametime penis
    #- What occurs at ship time... Do we fit once for male and female all possible morphing bodies?  Do we include fit in player's codebase?
        #- Time-consuming manual process of blending textures assumes a fixed relationship to a body!!  So this means most of penis fitting occurs at ship-time?  DESIGN AROUND THIS!!!
    #- What occurs during body morphing:
        #- It would be super positive to have ONE fitted penis per sex that can quickly adapt to any morph
    #- Define how we morph penis and how we morph body.
        #- Do we create new bones everytime or re-place bones created at ship-time?
        #- Does Unity get penis bones in its image or imported at all body imports?

#=== QUESTIONS ===
#- Are there any Blender-side design requirements for dildo functionality?  (Currently planning to be the same Blender-side as attached to body but we just don't render the body in Unity and attach a 'dildo mount')
#- What about decimation?  How does that fit in?
#- Removed smoothing code at end of fit... put it back in??  (Was interfering with manual re-texturing but looked nicer!) -> Put in CPenisRig?
#- Any considerations in regards to mounting close to vagina (for flow with CHoleRig?)

#=== IMPROVE ===

#=== PERFORMANCE ===
#- We only need skinning info to transfer to the base not the entire shaft!  Can be sped up?

#=== PROBLEMS ===
#- We had a problem with non-symmetrical dissolution of extra body-side rim verts.  I ended up reducing the area of geometry subdivision to not create super-fine body-side geometry under penis to solve this but there is still a problem with the code if there is finer body-side rim geometry than penis-side

#=== TODO ===
#- Create custom fitter for man mesh when it becomes available.    








import bpy
import sys
import bmesh
import array
import struct
from math import *
from mathutils import *
from bpy.props import *

import G
from gBlender import *
from CMesh import *



class CPenisFit():        # CPenisFit: Performs design-time fitting of penis to body mesh.  (Once this time-consuming process completes game can attach fitted penis very quickly)
    C_Layer_RimVertBody  = 9                       ###TODO: Use more layer stuff through codebase = removes clutter!!!
    C_Layer_RimVertPenis = 8

    
    def __init__(self, oMeshBody):
        self.oMeshBody = oMeshBody                      # Back-reference to the mesh body we have to fit to
        self.oMeshPenisFitted = None                    # The fitted penis.  A modified version of source penis adapted to 'mount' on a given game-time CBody instance.  Must be re-generated everytime source body morphs to ensure a proper mount
        

        print("\n\n\n=============== PENIS MOUNTING PROCEDURE ===============")
        print("\n===== A. PREPARE THE BODY HOLE FOR PENIS INSERTION INTO RIM =====")
        #=== Visualizer Cubes Preparation.  Must run first before entering edit mode ===
        self.oVisualizerCubes = G.CVisualizerCubes(0)       # Utility class to help debug / visualise this complex algorithm.  Set to about 600 to create enough 'visualization cubes' shown about different layers       
        bpy.data.scenes[0].layers[1] = 0            ###INFO: How to select which layers are shown.  (Must have at least one layer shown at ALL times!)
        bpy.data.scenes[0].layers[0] = 1            ###INFO: How to hide default layer 0 (show another layer first!)

        #=== Duplicate the woman's armature object and give it the '[ShemaleA]' name        
        oArmNode_Shemale = DuplicateAsSingleton('[WomanA]', '[ShemaleA]')       ###DESIGN24: Version A in there??  keep these damn versions??  ###DESIGN24:!!!! What about man??

        #=== Create extra geometry near where the penis will be mounted (the 'mounting hole') ===
        bmBody = self.oMeshBody.Open()
        oVertGrp_PenisExtraGeometry = VertGrp_SelectVerts(self.oMeshBody.GetMesh(), "_CPenis_ExtraGeometry")     # Obtain the area of the body's mesh that we are to replace with a fitted penis
        bpy.ops.mesh.select_more()                  # Select one more ring so the rim gets enough geometry to properly connect to fine-geometry penis
        bpy.ops.mesh.subdivide(quadtri=True)
        bpy.ops.mesh.select_less()                  # Fix the extra geometry group by selected twice less and re-assigning
        bpy.ops.mesh.select_less()
        bpy.ops.object.vertex_group_assign()

        #=== The above subdivide messed up our vertex group for the mounting hole rim.  Fix it now ===  (Only half the verts are now in group, new ones not)
        oVertGrp_PenisMountingHole = VertGrp_AddToSelection(self.oMeshBody.GetMesh(), "_CPenis_MountingHole")     # Obtain the area of the body's mesh that we are to replace with a fitted penis
        bpy.ops.mesh.select_more()                  ###INFO: Trick when half the verts in a ring are selected is to select more and then less = selects all in that ring!        ###CHECK: Is that really true??
        bpy.ops.mesh.select_less()                  # Fix the important mounting hole vert group by adding to fixed extra geometry group above, selecting more then less.
        bpy.ops.object.vertex_group_assign()


        
        #=== Obtain reference to the rim verts ===
        bpy.ops.mesh.region_to_loop()               # Obtain the rim from the mesh (still containing inner part of hole) with region_to_loop()
        bmBody.verts.ensure_lookup_table()
        aVertsBodyRim = [oVert.index for oVert in bmBody.verts if oVert.select]      # Obtain list of all body rim hole verts.  Needed for many iterations
        
        #=== Find the key verts of the rim hole opening.  We need these in 'modify base vert' section below to morph the penis base closer to the rim ===
        vecPenisRimCenter = Vector()
        oVertRimRightmost = None                        # The rim vert with the highest +X coordinate.  Used to re-interpolate penis UVs for re-texturing                        
        nVertRimRightmostX_Max = sys.float_info.min                # The X coordinates of the rightmost rim vert.  Used to find 'oVertRimRightmost'
        aVertsAtZeroX = []
        for nVertRim in aVertsBodyRim:                  # Iterate through the rim verts to find the verts at X=0.  There should be exactly two: One for top of hole the other for bottom of hole
            oVertRim = bmBody.verts[nVertRim]
            oVertRim.tag = False                        # Make sure each rim vert is untagged (next loop depends on this)
            vecPenisRimCenter += oVertRim.co
            if abs(oVertRim.co.x) < 0.0001:             ###WEAK: Rim verts at rim centers not exactly zero?  WTF happened to body mesh??
                aVertsAtZeroX.append(oVertRim)
            if nVertRimRightmostX_Max < oVertRim.co.x:
                nVertRimRightmostX_Max = oVertRim.co.x
                oVertRimRightmost = oVertRim

        #=== Determine which are the top and bottom rim verts from results of previous loop ===
        if aVertsAtZeroX[0].co.z > aVertsAtZeroX[1].co.z:
            oVertRimTop    = aVertsAtZeroX[0]         
            oVertRimBottom = aVertsAtZeroX[1]
        else:         
            oVertRimTop    = aVertsAtZeroX[1]         
            oVertRimBottom = aVertsAtZeroX[0]
        vecVertRimTop    = oVertRimTop.co.copy()    ###INFO: copy() is extremely important (data would point to some garbage once owning bmesh goes out of scope!)      
        vecVertRimBottom = oVertRimBottom.co.copy()
        vecPenisRimCenter /= len(aVertsBodyRim)
        vecPenisRimCenter.y -= 0.05                 ###HACK: Hack on center so that it's easier to determine verts toward penis / toward base (give a push forward toward tip) 
        bpy.context.scene.cursor_location = vecPenisRimCenter      
        print("\n=== Center = {}   Top = {}   Bottom = {}  Rightmost {} ===".format(vecPenisRimCenter, vecVertRimTop, vecVertRimBottom, oVertRimRightmost.co))   






        print("\n===== B. CREATE CHAIN OF RIM VERTS IN OUR STRUCTURES =====")
        oLayUV_Body  = bmBody.loops.layers.uv.active                    # Obtain access to the body's UV layer (so we can extract rim vert UVs and set them into penis rim verts)
        oRimVertBodyRoot = CRimVertBody(self, None, oVertRimTop, oVertRimTop.link_loops[0][oLayUV_Body].uv.copy())        # The string starts at the master rim vert (topmost at X=0)
        oRimVertBodyNow = oRimVertBodyRoot                              # Before we iterate set the 'next' as the root because it is the iteration's starting point

        while True:                             # Iterate through circular loop until we reach the node flagged as the last one
            oVertBodyRimNow = bmBody.verts[oRimVertBodyNow.nVertBody]

            for oEdgeToChild in oVertBodyRimNow.link_edges:
                if oEdgeToChild.select:                     # Only edges on the rim are currently selected
                    oVertNext = oEdgeToChild.other_vert(oVertBodyRimNow)
                    if oVertNext.tag == False:                              # Avoid edges that have been tagged as they have been traversed before. (by this loop)
                        if oVertNext.index != oVertRimTop.index:                # Only create a new link if we haven't looped back to starting vert yet
                            vecUV_Body = oVertBodyRimNow.link_loops[0][oLayUV_Body].uv.copy()
                            oRimVertBodyNow = oRimVertBodyNow.SetNext(oEdgeToChild, oVertNext, vecUV_Body)
                            print(oRimVertBodyNow)
                            oVertNext.tag = True                                        # Tag this vert as having been traversed so we don't go back to it.
                        else:                                                           # We've encountered the 'first vert' once again.  End the iteration by...
                            oRimVertBodyNow.bLastInLoop = True                          #... flagging the last node as the last one...
                            oRimVertBodyNow .oRimVertBodyNext = oRimVertBodyRoot        #... and set 'next'     of last  node to first node...
                            oRimVertBodyRoot.oRimVertBodyPrev = oRimVertBodyNow         #... and set 'previous' of first node to last  node...
                            print("- Chaining: linking first {} to last {}".format(oRimVertBodyRoot, oRimVertBodyNow))
                        break                                                           # We have committed to this edge.  Stop iterating through other edges (exit for loop and back into infinite while loop)
            if oRimVertBodyNow.bLastInLoop:
                break
        bmBody = self.oMeshBody.Close()
        self.oMeshBody.GetMesh().hide = True

        
        
        
        print("\n===== C. MODIFY THE PENIS BASE VERTS TO BE CLOSER TO BODY'S RIM OPENING =====")
        #=== Move all penis verts so the designated penis master vert coincides with the body's rim master vert (located at X=0 at penis top) ===
        self.oMeshPenisFittedSource = CMesh.Create("PenisA")          ###TODO21: A From Unity arg!
        self.oMeshPenisFitted = CMesh.CreateFromDuplicate(self.oMeshBody.GetName() + "-Penis-Fitted", self.oMeshPenisFittedSource)
        Cleanup_RemoveDoublesAndConvertToTris(0.000001)                             # Convert the penis to tris right away                                                              
        self.oMeshPenisFitted.SetParent(self.oMeshBody.GetMesh().parent.name)       ###DEV24:!!!!!! Reparent fitted penis to unique body we are fitting to

        #=== Link to our custom armature and set all our meshes to this just-created armature object ===
        bpy.ops.object.modifier_add(type='ARMATURE')
        self.oMeshPenisFitted.  GetMesh().modifiers["Armature"].object = oArmNode_Shemale       # Set both body and penis to the new armature
        self.oMeshBody.         GetMesh().modifiers["Armature"].object = oArmNode_Shemale
        self.oMeshBody.         SetParent(oArmNode_Shemale.name)                                # Set both body and penis as parent of armature Blender node
        self.oMeshPenisFitted.  SetParent(oArmNode_Shemale.name)


        if self.oMeshBody.GetName().find("ShemaleA") != -1:        
            bmPenis = self.oMeshPenisFitted.Open()
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenisFit_VertTop")     # Obtain our previously defined top vert.
            oVertPenisTop = Util_GetFirstSelectedVert(bmPenis)
            vecShiftOfAllPenisVerts = vecVertRimTop - oVertPenisTop.co
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.transform.translate(value=vecShiftOfAllPenisVerts)
            bpy.ops.mesh.select_all(action='DESELECT')
    
            #=== Proportionally move the bottom penis vert so that bottom of penis aligns much closer to bottom of rim hole ===
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenisFit_VertBottom")
            oVertPenisBottom = Util_GetFirstSelectedVert(bmPenis)
            vecShiftBottomVert = vecVertRimBottom - oVertPenisBottom.co
            bpy.ops.transform.translate(value=vecShiftBottomVert, proportional='CONNECTED', proportional_edit_falloff='SMOOTH', proportional_size=0.12)       ###TUNE: proportional size
    
            #=== Proportionally move a small area of verts underneath the scrotum close to base that are just too far from rim ===
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenisFit_ScrotumBase")
            bpy.ops.transform.translate(value=(0, 0, 0.0046), proportional='ENABLED', proportional_edit_falloff='SMOOTH', proportional_size=0.012)           ###TUNE
    
            #=== Proportionally move the side verts to make them wider (and with a softer angle) to rim edges ===
            VertGrp_SelectVerts(self.oMeshPenisFitted.GetMesh(), "_CPenisFit_BaseSides")
            nRatio = 1.12
            bpy.ops.transform.resize(value=(nRatio, nRatio, nRatio), constraint_orientation='GLOBAL', mirror=False, proportional='CONNECTED', proportional_edit_falloff='SMOOTH', proportional_size=0.032)
            bpy.ops.mesh.select_all(action='DESELECT')

        else:
            raise Exception("###EXCEPTION: Manual morphing procedure not created to modify penis base for a body mesh of type '{}'".format(self.oMeshBody.GetName()))       ###TODO21:!! Man mesh




        
        print("\n===== D. MATCH PENIS RIM VERTS TO BODY RIM VERTS =====")
        #=== Create a KD Tree of all the verts in the penis mounting area.  This tree will be used to rapidly find the closest vert to each vert of our mouting rim ===
        oKDTreePenis = kdtree.KDTree(len(bmPenis.verts))                     ###OPT: Would run a bit faster if we limit KDTree to verts near base
        for oVertPenis in bmPenis.verts:
            oKDTreePenis.insert(oVertPenis.co, oVertPenis.index)
        oKDTreePenis.balance()

        #=== Iterate through all the body rim verts to find their closest penis vert.  As we have a many-to-many between the two rim domains some body rim verts will point to multiple penis rim verts and some body rim verts will have no penis rim verts.  (Next loop choses the closest one)
        dictRimVertPenis = {}                                   # Dictionary of unique penis rim verts.
        oRimVertBodyNow = oRimVertBodyRoot
        while True:
            vecVertPenisClosestToRimVertBody, nVertPenisClosestToRimVertBody, nDist = oKDTreePenis.find(oRimVertBodyNow.vecVertBody)
            oVertPenisRim = bmPenis.verts[nVertPenisClosestToRimVertBody]
            if nDist > 0.05:
                raise Exception("###EXCEPTION: CPenis.ctor() could not find vert near enough to {}.  Closest dist = {}".format(oRimVertBodyNow.vecVertBody, nDist))
            if nVertPenisClosestToRimVertBody in dictRimVertPenis:                      # If a CRimVertPenis instance already exists for this penis rim vert obtain it so we can append this body rim vert to it
                oRimVertPenis = dictRimVertPenis[nVertPenisClosestToRimVertBody] 
            else:                                                                       #... otherwise create a new one and we will map it to this body rim vert (its first)
                oRimVertPenis = CRimVertPenis(self, oVertPenisRim)
                dictRimVertPenis[nVertPenisClosestToRimVertBody] = oRimVertPenis
            oRimVertPenis.RimVertBody_Add(oRimVertBodyNow)                              # Add an additional body rim vert to this penis rim vert.  (We will pick which one is closest in next loop)  This is how we can find best rim-to-rim matches accross our many-to-many relationship between the two domains
            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext



        

        
        print("\n===== F. CREATE VERTEX GROUPS WE WILL NEED FOR GEOMETRY DISSOLUTION =====") 
        #=== Create a new vertex group for the non-manifold penis base.  We will need it later as we delete vertices ===
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
        oVertGrp_PenisBaseNonManifold = self.oMeshPenisFitted.GetMesh().vertex_groups.new("_CPenisFit_BaseNonManifold") 
        bpy.ops.object.vertex_group_assign()

        #=== Iterate through all the defined penis rim verts and ask them to choose the closest body rim vert ===
        bpy.ops.mesh.select_all(action='DESELECT')
        for nRimVertPenis in dictRimVertPenis:
            oRimVertPenis = dictRimVertPenis[nRimVertPenis]
            oRimVertBody = oRimVertPenis.RimVertBody_FindClosest()
            oRimVertPenis.oVertPenis.select_set(True)                       # Also select so we can define vertex group just below

        #=== Create a new vertex group for the penis rim.  It will be needed later on to easily identify penis rim verts ===
        oVertGrp_PenisRimVerts = self.oMeshPenisFitted.GetMesh().vertex_groups.new("_CPenis_RimVerts") 
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')

        #=== Mark the unused body rim verts from our chain (Those that have no corresponding penis rim vert)  They will be dissolved when we can re-open body mesh ===
        aRimVertBodyToDissolve = []                                     # Remember where they are so we can remove when we re-open body's mesh
        oRimVertBodyNow = oRimVertBodyRoot
        while True:
            if oRimVertBodyNow.oRimVertPenis is None:
                oRimVertBodyNow.oRimVertBodyPrev.oRimVertBodyNext = oRimVertBodyNow.oRimVertBodyNext        #... first link the 'next' pointer of our previous to our next node...
                oRimVertBodyNow.oRimVertBodyNext.oRimVertBodyPrev = oRimVertBodyNow.oRimVertBodyPrev        #... and link the 'previous' pointer of our next node to our previous one.  (Bypassing & unlinking this node in both cases)
                print("- Marked body rim vert for dissolution: {}".format(oRimVertBodyNow))                # Remove this node from doubly-linked list:
                aRimVertBodyToDissolve.append(oRimVertBodyNow)              # Remember it so we can dissolve when we can re-open body mesh
                ###BROKEN: Reinstate facility to change cube color? oRimVertBodyNow.oVisualizerCube.material_slots[0].material = bpy.data.materials['VisualizerCube-GreenDark']   # Change our visualizer color to indicate dissolve
            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext





        print("\n===== G. DISSOLVE EXTRANEOUS PENIS RIM GEOMETRY =====")
        ###NOTE: Key part of algorithm!  What we have to do to form a solid rim border that can separate the good part of the mesh from the throwaway is to iterate through all rim edges and find edges that don't have BMEdge objects between them...
        ###NOTE: For those we dissolve the verts in the way and use 'vert_connect' to properly form a new BMEdge on the appropriate face (Does it properly as it won't introduce non-manifold geometry) 
        bpy.ops.mesh.select_all(action='DESELECT')
        oRimVertBodyNow = oRimVertBodyRoot
        while True:
            print("- Running edge vert dissolve on {}".format(oRimVertBodyNow))
            oRimVertPenis1 = oRimVertBodyNow.oRimVertBodyPrev.oRimVertPenis.oVertPenis 
            oRimVertPenis2 = oRimVertBodyNow.oRimVertPenis.oVertPenis
 
            if True:#oRimVertBodyNow.nRimVertBodyID == 13:
                oEdgeOnRim = bmPenis.edges.get([oRimVertPenis1, oRimVertPenis2])         ###INFO: How to find an existing edge
                if oEdgeOnRim is None:
                    oRimVertPenis1.select_set(True)
                    oRimVertPenis2.select_set(True)
                    bpy.ops.mesh.shortest_path_select()                     ###INFO: How to select shortest path
                    oRimVertPenis1.select_set(False)
                    oRimVertPenis2.select_set(False)
                    bpy.ops.mesh.dissolve_verts()                           ###OPT!!!: Runs very slowly but essential.  Can we possibly try to fix mesh after deleting this verts?  (Or UVs too badly damaged after 'make face' again?)
                    print("- Edge vert dissolve: Dissolved verts between {} and {} ".format(oRimVertPenis1, oRimVertPenis2))
                    oRimVertPenis1.select_set(True)
                    oRimVertPenis2.select_set(True)
                    bpy.ops.mesh.vert_connect()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    oEdgeOnRim = bmPenis.edges.get([oRimVertPenis1, oRimVertPenis2])         ###INFO: How to find an existing edge
                    if oEdgeOnRim is None:
                        print("- ERROR: Edge vert dissolve: Could not connect verts {} and {} ".format(oRimVertPenis1, oRimVertPenis2))

            if oRimVertBodyNow.bLastInLoop:
                break
            oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext



        
        print("\n===== H. REMOVE UNNEDDED PENIS GEOMETRY =====")
        #=== Starting at the non-manifold penis base edges keep selecting 'more' and de-selecting the rim verts... this will select all geometry we can delete ===         
        bpy.ops.mesh.select_all(action='DESELECT')
        self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisBaseNonManifold.index
        bpy.ops.object.vertex_group_select()
        self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisRimVerts.index
        for n in range(30):
            bpy.ops.object.vertex_group_deselect()      #... and de-selecting rim verts...
            bpy.ops.mesh.select_more()                  #... selecting one more layer of verts...
        bpy.ops.object.vertex_group_deselect()

        #=== Destroy the verts that are past the rim verts and convert to tris once more.  After this we can directly move penis verts to the position of their associated body rim vert as they have the exact same topology ===
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.mesh.select_all(action='DESELECT')



        
        print("\n===== I. MOVE PENIS RIM VERTS TO BODY RIM VERTS =====")
        #=== Move the penis rim verts to their associated body rim verts positions ===
        for nRimVertPenis in dictRimVertPenis:
            oRimVertPenis = dictRimVertPenis[nRimVertPenis]
            oRimVertPenis.oVertPenis.co = oRimVertPenis.oRimVertBody.vecVertBody
            oRimVertPenis.nVertPenis = oRimVertPenis.oVertPenis.index                   # Deleting verts in statement group above changed vertice indexes.  Refresh them so we have valid ones to still find penis rim verts after join below

        #=== Before joining heavily smooth the verts in the area of the joined rim vertices ===            ###TUNE: End-result penis smoothing.
        self.oMeshPenisFitted.GetMesh().vertex_groups.active_index = oVertGrp_PenisRimVerts.index
        bpy.ops.object.vertex_group_select()
        for n in range(5):
            bpy.ops.mesh.select_more()                  # Progressively smooth right around (modified rim)...
            bpy.ops.object.vertex_group_deselect()      #... but we never move rim verts themselves!
            bpy.ops.mesh.vertices_smooth(5)             ###TUNE: Smoothing

        #=== Remove all vertex groups and create a new one for CSoftBody implementation to use to create soft body from penis ===
        VertGrp_RemoveByNameInv(self.oMeshPenisFitted.GetMesh(), "_CPenis_")
        oVertGrp_Penis = self.oMeshPenisFitted.GetMesh().vertex_groups.new("_CSoftBody_Penis")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.data.scenes[0].tool_settings.vertex_group_weight = 0        ###CHECK: Make sure this works!
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bmPenis = self.oMeshPenisFitted.Close()


        
        

        print("\n===== J. SKINNING PENIS FROM ORIGINAL BODY =====")
        #=== Transfer skinning info from body to unskinned penis.  This is essential so penis base moves with the body! ===
        ###OPT ###IMPROVE: We only need skinning info to transfer to the base not the entire shaft!  Can be sped up?
        Util_TransferWeights(self.oMeshPenisFitted.GetMesh(), self.oMeshBody.GetMesh(), False)
        VertGrp_RemoveAndSelect_RegEx(self.oMeshPenisFitted.GetMesh(), oVertGrp_PenisMountingHole.name)      # Weight transfer above also transferred the mounting hole vert group which we don't want

        




        print("\n===== K. PERFORM FINAL CLEANUP BODY AND PENIS MESH BEFORE JOIN ======")
        #=== Cleanup the extraneous materials while keeping the most important one ===        ###OBS: Raw penis from DAZ gets it extra texture removed manually
        #oMatPenisMainMaterial = self.oMeshPenisFitted.GetMeshData().materials["Skin"]       # Before removing all materials obtain reference to the one we need to keep
        #while len(self.oMeshPenisFitted.GetMeshData().materials) > 0:                       # Remove all the materials
        #    bpy.ops.object.material_slot_remove()
        #bpy.ops.object.material_slot_add()
        #self.oMeshPenisFitted.GetMesh().material_slots[0].material = oMatPenisMainMaterial     # In the re-created slot re-assign the body material so it is the only material there.
        
        #=== Refresh the BMVerts we need to dissolve after the next vert delete for mounting hole ===
        bmBody = self.oMeshBody.Open()
        for oRimVertBodyNow in aRimVertBodyToDissolve:
            oRimVertBodyNow.oVertBody = bmBody.verts[oRimVertBodyNow.nVertBody]     # Update the BMVert from the index all indices are about to become invalid after vert delete below

        #=== Remove the verts inside the penis mounting hole (e.g. finally create the 'hole' needed for penis to weld in) ===
        self.oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp_PenisMountingHole.index
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_less()                  # Vertex group contains the rim verts which we want to keep.  Select one vert ring less to select only the inner verts we must delete
        bpy.ops.mesh.delete(type='VERT')            # Delete the mounting area's inner hole.  Penis can now be merged right in place by welding close verts
        
        #=== Dissolve the unused geometry of the body's penis rim.  Leaving them would create holes after join! ===
        bmBody.verts.ensure_lookup_table()
        for oRimVertBodyNow in aRimVertBodyToDissolve:
            oRimVertBodyNow.oVertBody.select_set(True)
            print("- Dissolving marked body rim vert {}".format(oRimVertBodyNow))
        bpy.ops.mesh.dissolve_verts()
        
        #=== Re-triangulate penis mounting hole area ===
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.quads_convert_to_tris()
        bmBody  = self.oMeshBody.Close()




        
        print("\n===== Z. FINISHED! =====")                         # Simple no? :-)
        bpy.context.scene.cursor_location = Vector((0,0,0))         # Return things to default and return
        bpy.ops.object.mode_set(mode='OBJECT')




        


class CRimVertBody():               # CRimVertBody: Helper class to store all information related to a rim vert on the body side
    s_nRimVertBodyID_Next = 0       # Static counter to auto-increment 'self.nRimVertBodyID'
    
    def __init__(self, oPenis, oRimVertBodyPrev, oVertBody, vecUV_Body):
        self.oPenis             = oPenis
        self.oRimVertBodyPrev   = oRimVertBodyPrev      # Our 'previous' CRimVertBody  (The rim vert just prior to us along the rim edge)
        self.oRimVertBodyNext   = None                  # Our 'next'     CRimVertBody  (The rim vert just next  to us along the rim edge) (Set by SetNext())
        self.oVertBody          = oVertBody             # Our BMVert on the body's rim for penis
        self.nVertBody          = self.oVertBody.index  # VertID of this rim vert in body mesh
        self.vecVertBody        = self.oVertBody.co.copy()  # The position of this body rim vert    ###INFO: copy() hugely important.  (Data would point to garbage when BMesh data falls out of scope!)
        self.vecUV_Body         = vecUV_Body            # The UV coordinate of the body-side rim vert.  Used to set penis-side rim vert UV
        self.nEdgeToChild       = None                  # The edge that links self.nVertBody to self.oRimVertBodyNext.nVertBody (Set by SetNext())  ###OBS?
        self.nLenEdgeToChildLen = None                  # Length of edge between parent and child.  Used to dissolve penis verts that are too close 
        self.oRimVertPenis      = None                  # CRimVertPenis instance assigned to us (closest). Can be None (in areas where more geometry exists on body rim than penis rim)
        self.oVisualizerCube    = None                  # Reference to our 'visualizer cube' that renders in 3D scene where this vertex is.  Essential during development!
        self.bLastInLoop        = False                 # Set to true on the very last node in the loop.  Allows iteration loops to iterate through every node of the loop exactly once   

        self.nRimVertBodyID = CRimVertBody.s_nRimVertBodyID_Next
        CRimVertBody.s_nRimVertBodyID_Next += 1

        self.oVisualizerCube = self.oPenis.oVisualizerCubes.GetCube("RimB{:02d}".format(self.nRimVertBodyID), self.vecVertBody, 'Green', self.oPenis.C_Layer_RimVertBody, True) 

    def SetNext(self, oEdgeToChild, oVertBody, vecUV_Body):             # Sets the one and only child
        self.nEdgeToChild   = oEdgeToChild.index            # Set on the parent edge that was used to find self.oRimVertBodyNext
        self.nLenEdgeToChildLen = oEdgeToChild.calc_length()
        self.oRimVertBodyNext  = CRimVertBody(self.oPenis, self, oVertBody, vecUV_Body)
        return self.oRimVertBodyNext                   # Return child for one-line creation + assignment

    def __str__(self):
        nRimVertPenisID = -1
        if self.oRimVertPenis is not None:
            nRimVertPenisID= self.oRimVertPenis.nRimVertPenisID
        return "[Body #{:2d}  Vert={:5d}  P={:2d}  {:6.3f},{:6.3f},{:6.3f}]".format(self.nRimVertBodyID, self.nVertBody, nRimVertPenisID, self.vecVertBody.x, self.vecVertBody.y, self.vecVertBody.z)



class CRimVertPenis():              # CRimVertPenis: Helper class to store all information related to a rim vert on the penis side
    s_nRimVertPenisID_Next = 0      # Static counter to auto-increment 'self.nRimVertPenisID'
    
    def __init__(self, oPenis, oVertPenis):
        self.oPenis             = oPenis
        self.oVertPenis         = oVertPenis            # Our rim BMVert on penis mesh                
        self.nVertPenis         = oVertPenis.index      # Vertex index of penis.  (Stored so we can still find our vert after join with body)                
        self.vecVertPenis       = self.oVertPenis.co    # Position of our rim vertex on penis mesh
        self.aRimVertBody       = []                    # List that store all CRimVertBody assigned to this penis rim vert in 'RimVertBody_Add()'.  We pick the closest one
        self.oRimVertBody       = None                  # The body rim vert we're assigned to.  Determined in RimVertBody_FindClosest()
        self.oVisualizerCube    = None                  # Reference to our 'visualizer cube' that renders in 3D scene where this vertex is.  Essential during development!   
        
        self.nRimVertPenisID = CRimVertPenis.s_nRimVertPenisID_Next
        CRimVertPenis.s_nRimVertPenisID_Next += 1

    def RimVertBody_Add(self, oRimVertBody):
        self.aRimVertBody.append(oRimVertBody)
        print("{} added link to {}".format(self, oRimVertBody))
        
    def RimVertBody_FindClosest(self):                  # Find the closest body-side rim vert that connected to us in self.aRimVertBody.  Second step needed to enables closest traversal accross the many-to-many
        nDistMin = sys.float_info.max
        for oRimVertBody in self.aRimVertBody:
            nDist = (oRimVertBody.vecVertBody - self.vecVertPenis).length
            if nDistMin > nDist:
                nDistMin = nDist
                self.oRimVertBody = oRimVertBody
        self.oRimVertBody.oRimVertPenis = self              # Link body rim vert to this penis rim vert
        self.aRimVertBody = None                            # Done with collection so destroy to save memory
        self.oVisualizerCube = self.oPenis.oVisualizerCubes.GetCube("RimP{:02d}".format(self.oRimVertBody.nRimVertBodyID), self.vecVertPenis, 'Blue', self.oPenis.C_Layer_RimVertPenis, False)    # Add our visualizer cube 
        print("{}  <==>  {}".format(self, self.oRimVertBody))
        return self.oRimVertBody

    def __str__(self):
        nRimVertBodyID = -1
        if self.oRimVertBody is not None:
            nRimVertBodyID = self.oRimVertBody.nRimVertBodyID
        return "[Penis #{:2d}  Vert={:5d}  B={:2d}]".format(self.nRimVertPenisID, self.oVertPenis.index, nRimVertBodyID)


























class CPenisRigSlice():              # CPenisRigSlice: These slices form '8-sided polygons that slice penis to form coherent collider... This helper class to store CPenisRigSliceVerts representing penis surface bones, flex particles, flex shapes and flex fluid collider verts.
    
    def __init__(self, nSliceIndex, vecVertSlice):
        self.nSliceIndex    = nSliceIndex           # Our index / ordinal along penis.  0 = base, last = tip
        self.vecVertSlice   = vecVertSlice          # The position at the center of this slice (close to penis center)
        self.aSliceVerts    = {}                    # Dictionary of our slice verts

    def AddSliceVert(self, nSliceVertIndex, vecVertSliceVert):
        oRigSliceVert = CPenisRigSliceVert(self, nSliceVertIndex, vecVertSliceVert)
        self.aSliceVerts[nSliceVertIndex] = oRigSliceVert
        return oRigSliceVert

    def __str__(self):
        return "[RigSlice #{:2d}  Y={:5d}]".format(self.nSliceIndex, self.nY)


class CPenisRigSliceVert():              # CPenisRigSliceVert: Helper class that representing penis surface bones, flex particles, flex shapes and flex fluid collider verts
    
    def __init__(self, oRigSlice, nSliceVertIndex, vecVertSliceVert):
        self.oRigSlice          = oRigSlice         # Our owning penis slice
        self.nSliceVertIndex    = nSliceVertIndex   # Index / ordinal of this instance inside self.oRigSlice.aSliceVerts[]
        self.sNameBone          = "{}{}{}".format(CPenisRig.C_BonePrefix, chr(65+self.oRigSlice.nSliceIndex), chr(65+self.nSliceVertIndex))
        self.vecVertSliceVert   = vecVertSliceVert  # Our vert position

    def __str__(self):
        return "[RigSliceVert #{:2d}  X={:5d}  Z={:5d}]".format(self.nSliceVertIndex, self.nX, self.nZ)



class CPenisRig():        # CPenisRig
    C_BonePrefix = "+Penis-"           # Prefix to all the bones we're creating.  The prefixing '+' means it's a 'dynamic bone' that our skinning info pipe transfers with more information (than design-time defined 'static bones')
    C_FlexParticleRadius = 0.01        ###WEAK24:!!! Copy of Unity's super-important CGame.INSTANCE.particleDistance / 2.  Need to 'pull back' the bones by the particle radius so collisions appear to be made at skin level instead of past it.  Since this value rarely changes this 'copy' is tolerated here but in reality the rig must be redone everytime this value chaanges.
    C_NumVertsPerSlice = 8             # Number of verts per slice = multi-sided polygon each slice.  Must cover the entire penis in Flex particles for good collisions
    C_RadiusRoughPolygon = 0.04        # Radius of rough polygon formed around penis.  Each vert will snap to closest penis vert
    C_RatioEnvelopeToBone = 0.90       # Ratio of bone envelop to bone head/tail (e.g. leave 90% most of the 'size we want' to envelope is ratio of 0.90

    def __init__(self, sNamePenisFitted, sNameBodyToFit):
        ###DEV24: self.oBody = oBody                                # Back-reference to the CBody instance that owns / manages us.
        oVisualizerCubes = G.CVisualizerCubes(0)                    # Utility class to help debug / visualise this complex algorithm.  Set to about 600 to create enough 'visualization cubes' shown about different layers       
        self.nSlices = 0                        # Number of slices to the penis.  Calculated from penis lenght and Flex particle distance to cover the whole penis (for good collisions during penetration)

        
        #===== A. OBTAIN ACCESS TO KEY PENIS VERTS =====
        #=== Get uretra vertex.  It will locate penis center along its long axis (x, z) and the tip location along y.  It will be our last 'slice' === 
        oPenisSource = CMesh.Create(sNamePenisFitted)
        oPenis = CMesh.CreateFromDuplicate(sNamePenisFitted + "_TEMP", oPenisSource)
        bmPenis = oPenis.Open()
        oVertGrp_Uretra = VertGrp_SelectVerts(oPenis.GetMesh(), "_CPenis_Uretra")
        for oVert in bmPenis.verts:             ###OPT:! Sucks we have to iterate through all verts to find one!
            if oVert.select:
                oVertUretra = oVert
        vecVertPenisCenter = oVertUretra.co.copy()
        vecVertPenisCenter.x = 0                     # Make sure we're centered

        #=== Get tip-most vertex.  We need an accurate length to properly space out slices.  This is where the 'tip particle' will go to make penetration possible at game-time === 
        oVertGrp_PenisTip = VertGrp_SelectVerts(oPenis.GetMesh(), "_CPenis_Tip")
        aVertsPenisTip = []
        for oVert in bmPenis.verts:             ###IMPROVE: Write helper function for this?
            if oVert.select:                    ###WEAK: Group contains 4-6 verts for the last slice.  We take the first one as 'good enough'
                oVertTip = oVert
                aVertsPenisTip.append(oVert)
        vecVertPenisTip = oVertTip.co.copy()
        vecVertPenisTip.z = vecVertPenisCenter.z    # Farthest vert on penis is too high.  Set the tip to be at uretra-height.
        vecVertPenisTip.x = 0                       # Make sure we're centered

        #=== Get the most forward vert at penis base.  This will be the beginning of the first 'slice' ===          ###DESIGN24: Really at this super-far connection point?  Go closer to shaft?? 
        oVertGrp_MountingHole = VertGrp_SelectVerts(oPenis.GetMesh(), "_CSoftBody_Penis")                   ####DEV24: Problem? Slightly messed up vert group!
        bpy.ops.mesh.region_to_loop()
        nVertBaseTopCenterY_Min = sys.float_info.max
        for oVert in bmPenis.verts:
            if oVert.select:
                nVertBaseTopCenterY = oVert.co.y
                if nVertBaseTopCenterY_Min > nVertBaseTopCenterY:
                    nVertBaseTopCenterY_Min = nVertBaseTopCenterY
                    oVertBaseCenter = oVert
        vecVertBaseCenter = oVertBaseCenter.co.copy()                   ###INFO:!!!! Damn this fucking problem of forgetting copy() causes problems!!  REMEMBER to ALWAYS copy() information out of object refernces because they will quickly point to garbage when ref changes!
        vecVertBaseCenter.x = 0                 # Make sure we're centered



        #===== B. CREATE SLICES AND SLICE VERTS =====
        #=== Generate penis KD Tree to speed up upcoming spacial vert searches ===
        oVertGrp_MountingHole = VertGrp_SelectVerts(oPenis.GetMesh(), "_CSoftBody_Penis")                   ####DEV24: Problem? Slightly messed up vert group!
        aVertsPenis = [oVert for oVert in bmPenis.verts if oVert.select]      # Obtain list of all the penis verts
        oKDTreePenis = kdtree.KDTree(len(aVertsPenis))                     
        for oVertPenis in aVertsPenis:
            oKDTreePenis.insert(oVertPenis.co, oVertPenis.index)
        oKDTreePenis.balance()

        #=== Generate verts for each slice ===
        nLenPenisShaft = vecVertBaseCenter.y - vecVertPenisTip.y
        self.nSlices = (int)(nLenPenisShaft / (2 * CPenisRig.C_FlexParticleRadius) + 0.5)  
        nLenPerSlice = nLenPenisShaft / (self.nSlices)
        nAnglePerSliceVert = 2 * pi / CPenisRig.C_NumVertsPerSlice
        print("CPenisRig() - Penis shaft length={:3f}   #Slices={}   LenPerSlice={:3f}".format(nLenPenisShaft, self.nSlices, nLenPerSlice))

        #=== Iterate through each slice and each vert for each slice to create our helper classes ===
        aRigPenisSlices = []
        for nSlice in range(self.nSlices):
            nSlicePosY = vecVertBaseCenter.y - nSlice * nLenPerSlice
            vecVertSlice = Vector((vecVertPenisCenter.x, nSlicePosY, vecVertPenisCenter.z))
            oRigSlice = CPenisRigSlice(nSlice, vecVertSlice)
            aRigPenisSlices.append(oRigSlice)
            nSlicePosY_Adjustment = 0
            if nSlice == self.nSlices-1:
                nSlicePosY_Adjustment = -0.3 * nLenPerSlice           ###DEV24: Keep??  ###HACK24: Manually move search vert a bit further so closest verts are closer to penis tip (because of penis tip angle)
            for nSliceVert in range(CPenisRig.C_NumVertsPerSlice):
                nAngle = nSliceVert * nAnglePerSliceVert
                x = vecVertPenisCenter.x + CPenisRig.C_RadiusRoughPolygon * sin(nAngle)
                z = vecVertPenisCenter.z + CPenisRig.C_RadiusRoughPolygon * cos(nAngle)
                if nSlice == 0:
                    nSlicePosY_Adjustment = 0.019 - 0.75 * CPenisRig.C_RadiusRoughPolygon * cos(nAngle)       ###HACK24: Manually move search vert under scrotum for base bones.  We need to pass scrotum and must form slice 0 at an angle
                vecVertSliceVert = Vector((x, nSlicePosY + nSlicePosY_Adjustment, z))
                vecVertPenisClosest, nVertPenisClosest, nDist = oKDTreePenis.find(vecVertSliceVert)     #- Find closest penis vert around each edge vert
                vecVertPenisClosestPulledBack = Vector()
                vecVertPenisClosestPulledBack.x = vecVertPenisClosest.x - CPenisRig.C_FlexParticleRadius * sin(nAngle)            # 'Pull back' the flex particle radius from the bone position (so collisions occur at skin leve during gameplay)
                vecVertPenisClosestPulledBack.y = vecVertPenisClosest.y
                vecVertPenisClosestPulledBack.z = vecVertPenisClosest.z - CPenisRig.C_FlexParticleRadius * cos(nAngle)
                oSliceVert = oRigSlice.AddSliceVert(nSliceVert, vecVertPenisClosestPulledBack)     ###DEV24: Not fully integrated... keep helper classes?
                oVisCube = oVisualizerCubes.GetCube("P" + oSliceVert.sNameBone, vecVertSliceVert, 'Red', 1, False, 3) 
                oVisCube = oVisualizerCubes.GetCube("C" + oSliceVert.sNameBone, vecVertPenisClosestPulledBack, 'Green', 1, False, 3)
                
        #=== Add additional 'penis tip' slice verts to the last slice to keep expanding penetration past tip-most particle created in next group below ===
        oRigSlice = CPenisRigSlice(self.nSlices, vecVertPenisTip)       ###DEV24:!!!!!!!!!!  What pos?
        aRigPenisSlices.append(oRigSlice)
        nSliceVerts_LastSlice = 0   #CPenisRig.C_NumVertsPerSlice                     # Already this many verts in this last slice... we add more to it.
#         VertGrp_SelectVerts(oPenis.GetMesh(), oVertGrp_PenisTip.name)
#         for oVert in aVertsPenisTip:
#             vecVert = oVert.co - (oVert.normal * CPenisRig.C_FlexParticleRadius * 0.5)       # Pull back the last slice verts partly off their position but inward part of the particle distance (so they protrude out of penis tip a bit a bit to facilitate penetration along with tip-most particle below)
#             oRigSlice.AddSliceVert(nSliceVerts_LastSlice, vecVert)
#             nSliceVerts_LastSlice += 1
            
        #=== Create the 'tip-most' particle at the very tip of the penis.  This one sticks out more out of penis to enable penetration with a single particle ===
        oRigSlice.AddSliceVert(nSliceVerts_LastSlice, vecVertPenisTip - Vector((0, CPenisRig.C_FlexParticleRadius, 0)))     ###DEV24:!!!!!! pos ok??
        bmPenis = oPenis.Close()                 # Close the mesh so we can now create new penis bones
        


        #===== C. CREATE BONES =====
        #=== Obtain access to armature ===
        oParentArmature = SelectObject(oPenis.GetMesh().parent.name)            # Must select armature object...  ###IMPROVE: Use new method with 'oPenis.GetMesh().modifiers["Armature"].object'? 
        bpy.ops.object.mode_set(mode='EDIT')                            #... and then place it in edit mode for us to be able to view / edit bones
        oArm = oPenis.GetMesh().modifiers["Armature"].object.data
        oBoneRigSliceNow = oArm.edit_bones["Genitals"]                  ###IMPROVE: Would be nice to delete bone hierarchy so this code never creates duplicate
        
        #=== Remove bones that start with the specified bone name prefix ===
        Bones_RemoveBonesWithNamePrefix(oArm, CPenisRig.C_BonePrefix)
            
        #=== Create new penis bones for the shaft ===
        for oRigSlice in aRigPenisSlices:                     ###CHECK24: Uretra gets no surrounding bones ###DESIGN24: But what about collider??
            oBoneRigSlice = oArm.edit_bones.new("{}{}".format(CPenisRig.C_BonePrefix, chr(65+oRigSlice.nSliceIndex)))
            oBoneRigSlice.parent = oBoneRigSliceNow
            oBoneRigSlice.head = oRigSlice.vecVertSlice
            oBoneRigSlice.tail = oBoneRigSlice.head - Vector((0,0.001,0))                ###INFO: A bone *must* have different head and tail otherwise it gets deleted without warning = DUMB!
            oBoneRigSlice.use_connect = False
            oBoneRigSlice.envelope_distance = oBoneRigSlice.envelope_weight = oBoneRigSlice.head_radius = oBoneRigSlice.tail_radius = 0

            for nSliceVert in range(len(oRigSlice.aSliceVerts)):
                oRigSliceVert = oRigSlice.aSliceVerts[nSliceVert]
                nDistBone = nLenPerSlice                                                ###TUNE:!!!
                oBoneRigSliceVert = oArm.edit_bones.new(oRigSliceVert.sNameBone)
                oBoneRigSliceVert.parent = oBoneRigSlice
                oBoneRigSliceVert.head = oRigSliceVert.vecVertSliceVert
                oBoneRigSliceVert.tail = oBoneRigSliceVert.head - Vector((0,0.001,0))       ###IMPROVE: Tail along same vector?
                oBoneRigSliceVert.use_connect = False
                oBoneRigSliceVert.envelope_weight = 1
                oBoneRigSliceVert.envelope_distance = nDistBone * CPenisRig.C_RatioEnvelopeToBone     ###NOTE: 'envelope distance does not appear to work as we want (e.g. setting head_radius and tail_radius ot zero and our radius in envelope_distance -> head and tail get set to that value!)
                oBoneRigSliceVert.head_radius = oBoneRigSliceVert.tail_radius = nDistBone * (1 - CPenisRig.C_RatioEnvelopeToBone)
            oBoneRigSliceNow = oBoneRigSlice
        
        #=== Create bone for scrotum ===                                ###IMPROVE: Scrotum very preliminary.  improve with one for each ball?  More than one bone down?
        nDistBone = 0.063
        oBoneRigScrotum = oArm.edit_bones.new(CPenisRig.C_BonePrefix + "Scrotum")
        oBoneRigScrotum.parent = oArm.edit_bones[CPenisRig.C_BonePrefix + "A"]                     # Would be better to access by variable...
        oBoneRigScrotum.head = vecVertBaseCenter + Vector((0,0.0181,-0.150))    ###HACK: Scrotum center position approximated from a large penis.  Would not fit a small penis well... ###IMPROVE: Scan penis verts to determine scrotum center 
        oBoneRigScrotum.tail = oBoneRigScrotum.head - Vector((0,0,-0.001))
        oBoneRigScrotum.use_connect = False
        oBoneRigScrotum.envelope_weight = 1
        oBoneRigScrotum.envelope_distance = nDistBone * CPenisRig.C_RatioEnvelopeToBone
        oBoneRigScrotum.head_radius = oBoneRigScrotum.tail_radius = nDistBone * (1 - CPenisRig.C_RatioEnvelopeToBone)       ###INFO: How to setup an effective bone bleed.  Blender doesn't seem to like it when we set head_radius / tail_radius too small
    
        #=== Un-parent and re-parent with envelope weights to automatically assign bone weights via the bone envelope we just defined ===
        bpy.ops.object.mode_set(mode='OBJECT')
        SelectObject(oPenis.GetName())
        VertGrp_RemoveAll(oPenis.GetMesh())                                # Remove all vextex groups before envelope re-weight
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')                ###INFO: How to un-parent.
        oParentArmature.select = True
        bpy.context.scene.objects.active = oParentArmature
        bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')                     ###INFO: How to re-parent  ###INFO: How to re-weight an entire mesh by envelope
        SelectObject(oPenis.GetName())
        oParentArmature.hide = True
        VertGrp_RemoveByNameInv(oPenis.GetMesh(), CPenisRig.C_BonePrefix)                 # Keep only the bones vertex groups we just created
        
        #=== Perform initial bone limiting and normalization ===
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)   # Limit to the four bones Unity can do at runtime.
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)                ###DESIGN24:! Keep here?  Do at very end?
        bpy.ops.object.mode_set(mode='OBJECT')



        #===== D. JOIN MESHES TOGETHER =====     
        #=== Join fitted and rigged penis with body ===
        SelectObject(sNameBodyToFit)
        oBodyToFitToSource  = CMesh.Create(sNameBodyToFit)
        oBodyToFitTo = CMesh.CreateFromDuplicate("ShemaleA", oBodyToFitToSource)        ###DESIGN24: Where we create mesh ###TODO24: Male mesh and arguments!!
        oPenis.GetMesh().select = True                                          ###INFO: How to join two meshes easily
        bpy.ops.object.join()
        oPenis = None                                                           # Penis mesh just got destroyed by join() above so we clear our reference
        
        #=== Leave only the non-manifold edges selected so bridge_edge_loop() can merge run === 
        bmBodyToFit = oBodyToFitTo.Open()
        VertGrp_SelectVerts(oBodyToFitTo.GetMesh(), CPenisRig.C_BonePrefix + "Scrotum")            # Select a group we knows exists on penis-side...
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.mesh.select_linked()                                            # ... then select all linked verts so we have all penis verts...
        oVertGrp_Penis = oBodyToFitTo.GetMesh().vertex_groups.new("_CSoftBody_Penis")       #... but remember the penis verts first        ###IMPROVE: Make call to create vert groups!
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.region_to_loop()                                           # ... then ask for the boundaries of all penis verts to leave only the penis-side rim verts
        VertGrp_AddToSelection(oBodyToFitTo.GetMesh(), "_CPenis_MountingHole")  # ... and add to the selection the body-side rim verts.  At this point we have the matching edge rings both selected for bridge_edge_loop() below
        for oEdge in bmBodyToFit.edges:
            if oEdge.select:
                if oEdge.is_manifold == True:                                   # Only leave the non-manifold edges selected for the bridge_edge_loop() call below.  It *must* have equal # of edges on each side and Blender includes in selection any edges that have both verts selected (e.g. small corner triangles)
                    oEdge.select_set(False)
        bpy.ops.mesh.bridge_edge_loops(type='PAIRS', use_merge=True, merge_factor=0)        ###INFO: An incredibly useful way to connect two meshes.  All other attempts to do via BMesh what this call does miraculously have been disasters!  (e.g. trashes one vert or the other or insanely slow!)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        #aVertsJoinedRim = [oVert.index for oVert in bmBodyToFit.verts if oVert.select]      # Obtain list of just-joined rim verts to survive the trashing our vert groups are going to suffer in blending below  ###IMPROVE: Need to store this in vert group for anything?

        #=== Blend body base bones into penis verts so penis bones blend with body bones ===
        VertGrp_SelectVerts(oBodyToFitTo.GetMesh(), oVertGrp_Penis.name)
        bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=1.0, repeat=8)       ###TUNE:!!!   
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)   # Limit to the four bones Unity can do at runtime.
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)                ###DESIGN24:! Keep here?  Do at very end?

        #=== Smooth the area around the just-joined meshes ===        
        bpy.ops.mesh.region_to_loop()                                           # Right now every penis vert is selected minus the rim.  Get the boundary so we can expand and smooth around
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.vertices_smooth(20)            ###TUNE:!            
        bmBodyToFit = oBodyToFitTo.Close()
        #aVertsJoinedRim = [oVert.index for oVert in bmBodyToFit.verts if oVert.select]      # Obtain list of just-joined rim verts to survive the trashing our vert groups are going to suffer in blending below
        ###IMPROVE: have lost the definition of what verts inside penis but can recover with bpy.ops.object.material_slot_select()  (Or store in array before blend weights above?)
    























#- We have a solution on efficiently blending penis textures but:
    #- UV distortion not ok!
        #- Why the heck are the rim UVs so much further that first read??
        #- Definitively a 'clockwise rotation' of rim verts... why??  (Is 2-way many-to-many resolution not working right? (e.g. always picking first or last??)
    #- Need to code the latest manual UV step?  (Or does it make things worse? 
    #- To perform 'second step' of texture edit:
        #- In 'Texture Paint', invoke tool tray -> Tools tab -> Clone brush (NOT from image).  Then in main view Control+LMB on 'good part' of texture and draw on 'bad' part.  Adjust radius with F and strenght to blend! :)
    #- UV re-projection has larger gaps around rim verts... what causes this??
    #- UV re-projection shows around rim verts an odd 'clockwise' rotation of rim verts... what causes this distortion??

        #=== Determine the UV re-interpolation parameters that can convert between penis X,Z 3D coordinates and a UV X,Y ===  (PLACE BEFORE 'CREATE CHAIN OF RIM VERTS IN OUR STRUCTURES')
        #oLayUV_Body  = bmBody.loops.layers.uv.active                    # Obtain access to the body's UV layer (so we can extract rim vert UVs and set them into penis rim verts)
        ###OBS? Turns out the creation of new UV layer is not really needed given texture Blend can be so easily done with Blender's tools...
        #vec2D_Point0 = Vector((oVertRimBottom.co.   x, oVertRimBottom.co.   z))     # Point 0 = bottom center of rim.  (We use the x and z 3D coordinates to 'flatten' them into a 'lookalike UV' projected about Y = 0 plane
        #vec2D_Point1 = Vector((oVertRimRightmost.co.x, oVertRimRightmost.co.z))     # Point 1 = top right of rim.
        #vecUV_Point0 = oVertRimBottom.   link_loops[0][oLayUV_Body].uv.copy()       # UV coordinates of point 0 and point above.
        #vecUV_Point1 = oVertRimRightmost.link_loops[0][oLayUV_Body].uv.copy()
        #vec2D_Span  = vec2D_Point1 - vec2D_Point0 
        #vecUV_Span  = vecUV_Point1 - vecUV_Point0
        #print("=== 3D: {} - {}     UV: {} - {} ===\n".format(vec2D_Point0, vec2D_Point1, vecUV_Point0, vecUV_Point1))
        


#         ###OBS? Turns out the creation of new UV layer is not really needed given texture Blend can be so easily done with Blender's tools...  (PLACE RIGHT BEFORE SKINNING)
#         print("\n===== CREATE NEW UV LAYER FOR RE-TEXTURING =====")
#         #=== Create a new 're-texturing helper' UV map that *greatly* facilitate the process of blending the body's texture onto the penis one ===
#         bpy.ops.mesh.uv_texture_add()                                       # Create a new UV layer to facilitate the blending of the penis textures to the body
#         #bmPenis.loops.layers.uv.active.name = "PenisRetexturing"            ###INFO: How to create and additional UV layer (will copy first one)  ###IMPROVE: How to name layer??
#         oLayUV_Penis = bmPenis.loops.layers.uv.active                       ###INFO: How to access the UV copy we just created
#         self.oMeshPenisFitted.GetMeshData().uv_textures.active_index = 0    # Go back to the default UV map.  Leaving active on would cause join with body to have the new layer selected on the whole body! 
# 
#         #=== Iterate through mounting-area penis verts to re-interpolate their UVs to be similar to the UVs of the body rim ===
#         for oVert in bmPenis.verts:
#             vec2D = Vector((oVert.co.x, oVert.co.z))                # Re-interpolate the 'projected' 3D (Flattened about Y=0) toward UV coordinates 
#             vec2D   -= vec2D_Point0                                 # First we remove the 'zero point' from the 'flattened 3D' domain...
#             vec2D.x /= vec2D_Span.x                                 #... then convert 0 - 1 scaling by dividing by the 'flattened 3D' domain span...
#             vec2D.y /= vec2D_Span.y
#             vec2D.x *= vecUV_Span.x                                 #... then convert the 0 - 1 to the UV domain's span...
#             vec2D.y *= vecUV_Span.y 
#             vec2D   += vecUV_Point0                                 #... and finally add the UV-domain starting point. 
#             for oLoop in oVert.link_loops:
#                 oLoop[oLayUV_Penis].uv = vec2D.copy()
#                         
#         #=== Set the UV coordinates of the penis rim verts to the exact UV position of the body rim.  (This greatly facilitates creating a 'texture transfer UV' to blend in textures at the seam) ===
#         for nRimVertPenis in dictRimVertPenis:
#             oRimVertPenis = dictRimVertPenis[nRimVertPenis]
#             vecUV_Body = oRimVertPenis.oRimVertBody.vecUV_Body              # Fetch the previously-obtained UV coordinates for the body-side rim vert (obtained in earlier loop while bmBody was open)
#             for oLoop in oRimVertPenis.oVertPenis.link_loops:               # Store body's rim vert UV into penis rim-vert UV.
#                 oLoop[oLayUV_Penis].uv = vecUV_Body







###OBS: Old end of CPenisFit to glue to body.  We now have much better with bridge_edge_loops()!!
#         if 0:       ###DEV24:!!! Need to break this up and have game glue an already-fitted penis!
#             print("\n===== L. ATTACH FITTED PENIS TO BODY =====")
#             #=== Weld the fitted penis to the prepared body ===
#             SelectObject(self.oMeshBody.GetName())
#             self.oMeshPenisTempForJoin = CMesh.CreateFromDuplicate(self.oMeshPenisFitted.GetName() + "-TempForJoin", self.oMeshPenisFitted)
#             self.oMeshPenisTempForJoin.GetMesh().select = True
#             self.oMeshBody.GetMesh().select = True
#             bpy.context.scene.objects.active = self.oMeshBody.GetMesh() 
#     
#             #=== Join the two meshes and weld the rim verts ===
#             bpy.ops.object.join()                       ###INFO: This will MESS UP all the vertex ID in the body (penis vert IDs will be fine and appear in the order they were in penis)  After this we have to re-obtain our BMVerts by 3D coordinates as even our stored vertex IDs become meaningless
#             
#             #=== Open body and re-obtain access to the body-side rim verts (previous indices & BMVerts rendered invalid after join above) ===        
#             bmBody = self.oMeshBody.Open()        ###INFO: We do it this way instead of 'remove_doubles()' as that call will replace about half the body's rim verts with penis rim verts (thereby destroying precious UV & skinning info)
#             self.oMeshBody.GetMesh().vertex_groups.active_index = oVertGrp_PenisMountingHole.index
#             bpy.ops.object.vertex_group_select()
#             aVertsBodyRim = [oVert for oVert in bmBody.verts if oVert.select]
#             bpy.ops.mesh.select_all(action='DESELECT')
#     
#             #=== Re-link the penis-side rim verts with their associated body-side rim verts.  (We need to merge them in a controlled manner) ===
#             oRimVertBodyNow = oRimVertBodyRoot
#             while True:
#                 oRimVertBodyNow.oRimVertPenis.oVertPenis = bmBody.verts[oRimVertBodyNow.oRimVertPenis.nVertPenis]       # Update BMVert reference (old one destroyed by join above)
#                 oRimVertBodyNow.oRimVertPenis.vecVertPenis = oRimVertBodyNow.oRimVertPenis.oVertPenis.co                # Update Penis rim vert location (moved to body rim vert above)
#                 oRimVertBodyNow.oVertBody = None 
#                 for oVertBodyRim in aVertsBodyRim:                          # Perform a brute-force search through all body-side rim verts to find the one at the 3D location of the known-good penis-side rim vert
#                     if oVertBodyRim.co == oRimVertBodyNow.vecVertBody:
#                         oRimVertBodyNow.oVertBody = oVertBodyRim
#                         break 
#                 if oRimVertBodyNow.oVertBody is None:
#                     raise Exception("###EXCEPTION: Could not find body rim vert at location {} after join.".format(oRimVertBodyNow.vecVertBody))
#                 print("- After-join re-link of {} to {}".format(oRimVertBodyNow.oVertBody, oRimVertBodyNow.oRimVertPenis.oVertPenis)) 
#                 if oRimVertBodyNow.bLastInLoop:
#                     break
#                 oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
#     
#             #=== Create new faces between the two rims.  This will protect both side's information (bones and UVs) ===
#             oRimVertBodyNow = oRimVertBodyRoot          ###DESIGN21:!!! Some uncertainty as how to leave the merged meshes...  Keep the faces in gametime body?  Modify softobdy (which version? now or future??)
#             while True:
#                 oFaceBridgeAcrossRims = bmBody.faces.new([oRimVertBodyNow.oVertBody, oRimVertBodyNow.oRimVertPenis.oVertPenis, oRimVertBodyNow.oRimVertBodyPrev.oRimVertPenis.oVertPenis, oRimVertBodyNow.oRimVertBodyPrev.oVertBody])
#                 if oRimVertBodyNow.bLastInLoop:
#                     break
#                 oRimVertBodyNow = oRimVertBodyNow.oRimVertBodyNext
#             bmBody  = self.oMeshBody.Close()




###MOVE: Smoothing and decimate code.  Belongs at gametime!
#         if 0:           ###DESIGN:21!!!: Belongs in this call?  Blender file saved without moving body rim and decimation?  How about penis morphs?
#             print("\n===== M. SMOOTH PENIS-TO-BODY RIM AREA =====")
#             #=== Smooth the verts in the area of the joined rim vertices ===            ###TUNE: End-result penis smoothing.
#             bpy.ops.mesh.vertices_smooth(10)                                            ###DESIGN: Remove this when re-texturing penis??            
#             bpy.ops.mesh.select_more()
#             bpy.ops.mesh.vertices_smooth(10)            
#            
#             print("\n===== N. DECIMATE PENIS GEOMETRY =====")
#             #=== Decimate the just-attached penis to reduce its vert count to more reasonable levels ===
#             VertGrp_SelectVerts(self.oMeshBody.GetMesh(), oVertGrp_Penis.name)
#             bpy.ops.mesh.decimate(ratio=0.17)                               ###TUNE: Decimation ratio!


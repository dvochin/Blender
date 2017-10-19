import bpy
import sys
# import bmesh
#import array
# import struct
# from math import *
# from mathutils import *
# from bpy.props import *
# 
# from gBlender import *
# import G
# from CBody import *
# from CMesh import *


#C_PropFlag_ = 1

class CObject():
    cm_oObjectMeshShapeKeys_HACK = None

    def __init__(self, sNameObject):
        self.sNameObject    = sNameObject
        self.aProps         = {}
        
    def PropAdd(self, sName, sDescription, nValue, nMin, nMax):
        self.aProps[sName] = oProp = CProp(self, sName, sDescription, nValue, nMin, nMax)
        #print("[PropAdd for '{}' added property '{}'".format(self.sNameObject, sName))
        return oProp

    def PropFind(self, sName):
        if (sName in self.aProps):
            return self.aProps[sName]
        else:
            raise Exception("\n###ERROR: CObject '{}' could not find property '{}'.\n".format(self.sNameObject, sName))

    def PropFindByOrdinal(self, nPropOrdinal):
        nProp = 0
        for sPropKey in self.aProps:
            if (nProp == nPropOrdinal):
                return self.aProps[sPropKey]
            nProp += 1
        raise Exception("\n###ERROR: CObject.PropFindByOrdinal() could not find property ordinal {}.\n".format(self.sNameObject, nPropOrdinal))

    def PropGet(self, sName):
        return self.PropFind(sName).PropGet()

    def PropGetString(self, sName):                 # Version callable from Unity ###IMPROVE: Add ability of gBlender to send ints?
        return str(self.PropGet(sName))            

    def PropSet(self, sName, nValueNew):
        return self.PropFind(sName).PropSet(nValueNew)

    def PropSetString(self, sName, nValueNew):      # Version callable from Unity
        return str(self.PropSet(sName, nValueNew))

    def Serialize(self):            # Serialize CObject members to Unity for remote manipulation through its own CObject implementation
        return "['{}', '{}']".format(self.sNameObject, len(self.aProps))       ###WEAK: Would crash if name has "'" 

    def SerializeProp(self, nPropOrdinal):      # Serialize CObject members to Unity for remote manipulation through its own CObject implementation
        oProp = self.PropFindByOrdinal(nPropOrdinal)
        return oProp.Serialize() 


class CObjectMeshShapeKeys(CObject):
    def __init__(self, sName, sNameMesh):
        super(self.__class__, self).__init__(sName)
        self.oMeshO = bpy.data.objects[sNameMesh]
        
        if self.oMeshO.data.shape_keys is None:
            print("###WARNING: Mesh has no shape keys.  Cancelling access to morph properties in CObjectMeshShapeKeys.")
            return
        
        self.oMeshShapeKeyBlocks = self.oMeshO.data.shape_keys.key_blocks

        #=== Populate our properties with our mesh shape keys ===
        for oShapeKey in self.oMeshShapeKeyBlocks:
            if oShapeKey.name != "Basis":
                self.PropAdd(oShapeKey.name, "Description for " + oShapeKey.name, oShapeKey.value, oShapeKey.slider_min, oShapeKey.slider_max)

#         #=== Sort the shape keys by name ===
#         aShapeKeys_Sorted = []
#         for oShapeKey in self.oMeshShapeKeyBlocks:
#             if oShapeKey.name != "Basis":
#                 aShapeKeys_Sorted.append(oShapeKey.name)
#         aShapeKeys_Sorted.sort()
# 
#         #=== Populate our properties with our mesh shape keys ===
#         for sNameShapeKey in aShapeKeys_Sorted:
#             oShapeKey = self.oMeshShapeKeyBlocks[sNameShapeKey]
#             self.PropAdd(oShapeKey.name, "Description for " + oShapeKey.name, oShapeKey.value, oShapeKey.slider_min, oShapeKey.slider_max)


        #self.PropAdd("Breasts-Implants", 123)
        #self.PropAdd("Breasts-Nipple", 234)
        #self.PropSet("Breasts-Implants", 4.0)
        #print("Property = " + str(self.PropGet("Breasts-Implants")))
        #print(self.Serialize())
        #print(self.SerializeProp(0))
        #print(self.SerializeProp(1))
        
    def PropGet(self, sName):
        oProp = self.PropFind(sName)
        oProp.nValue = self.oMeshShapeKeyBlocks[oProp.sName].value
        return oProp.nValue

    def PropSet(self, sName, nValueNew):                ###OPT:!!! It is highly inneficient to update mesh shape key at every update!!  Consider 'caching' the properties in Unity and setting all at once when changing game mode!  
        oProp = self.PropFind(sName)
        nValueNew = oProp.PropSet(nValueNew)
        self.oMeshShapeKeyBlocks[oProp.sName].value = nValueNew
        nValueNew = self.oMeshShapeKeyBlocks[oProp.sName].value
        return nValueNew
       

        
class CProp():
    def __init__(self, oObject, sName, sDescription, nValue, nMin, nMax):
        self.oObject        = oObject
        self.sName          = sName
        self.sDescription   = sDescription
        self.nValue         = nValue
        self.nMin           = nMin
        self.nMax           = nMax
        #self.eFlags         = eFlags
        
    def PropGet(self):
        #print("[PropGet '{}' = {:3f}]".format(self.sName, self.nValue))
        return self.nValue

    def PropSet(self, nValueNew):
        nValueNew = self.PropClamp(nValueNew)
        #print("[PropSet '{}' = {:3f}]".format(self.sName, nValueNew))
        self.nValue = nValueNew
        return self.nValue
    
    def PropClamp(self, nValueNew):
        if nValueNew < self.nMin:
            nValueNew = self.nMin
        if nValueNew > self.nMax:
            nValueNew = self.nMax
        return nValueNew
    
    def Serialize(self):
        return "['{}', '{}', '{}', '{}', '{}']".format(self.sName, self.sDescription, self.nValue, self.nMin, self.nMax)     ###NOTE: Separated by ', ' and each field by '' as needed by Unity's SplitCommaSeparatedPythonListOutput 
        
    
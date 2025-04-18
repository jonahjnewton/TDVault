import os
import shutil
from maya import cmds

def exampleOverride():
    """
    Example function to demonstrate how to create a USD override layer and add a reference to it.
    
    This function creates a Maya USD stage with an override layer for a set asset,
    which has a sub-asset (setPieceTest01) already referenced in it.
    The function also demonstrates how to add versioned references to a sub-asset (setPieceTest02) 
    to the layer.

    You can find the output of this function in the usd_overrides directory (with some transform overrides 
    applied to show how an artist's edits are applied).
    """

    # Create a Maya USD stage with an override layer for a
    mayaProxyShape_node, layer = createOverrideLayer("setTest01", "./setTest01.usda")

    # Add another reference of setPieceTest01 to the layer (once is already in the set)
    # This will be added at the path /setTest01/setPieceTest01_002
    setPieceTest01_path = "./setPieceTest01.usda"
    setPieceTest01_name = "setPieceTest01"
    addNewSubAssetReferenceToLayer(layer, layer.GetDefaultPrim().pathString, setPieceTest01_name, setPieceTest01_path)

    # Add one reference of setPieceTest02 to the layer (a new sub-asset)
    # This will be added at the path /setTest01/setPieceTest02_001
    setPieceTest02_path = "./setPieceTest02.usda"
    setPieceTest02_name = "setPieceTest02"
    addNewSubAssetReferenceToLayer(layer, layer.GetDefaultPrim().pathString, setPieceTest02_name, setPieceTest02_path)

def createOverrideLayer(asset_name, asset_path):
        """
        Create a Maya USD layer with an override layer, referencing an asset. 
        This is used to non-destructively make edits (or add references to new sub-assets)
        without modifying the original USD layer.
        Args:
            asset_name (str): The name of the asset.
            asset_path (str): The filepath to the USD layer for the asset.
        Returns:
            tuple: The mayaUsdProxyShape node and layer created in it.
        """
        import mayaUsd.ufe as mayaUsdUfe #import this at runtime because otherwise maya crashes on startup

        node = cmds.createNode('mayaUsdProxyShape', name=asset_name)
        node_long = cmds.ls(node, long=True)[0]
        
        # Create override folder if it doesn't exist
        usd_overrides_path = "/".join(os.path.dirname(cmds.file(q=True, sn=True)))+"/usd_overrides"
        if(not os.path.exists(usd_overrides_path)):
            os.mkdir(usd_overrides_path)

        stage = mayaUsdUfe.getStage(node_long)

        # Create a new versioned override layer
        override_path = usd_overrides_path+"/"+asset_name+"_override_v"+str(findLatestOverrideVersion(asset_name)+1).zfill(3)+".usda"
        
        layer = stage.CreateNew(override_path)
        asset_sdf_path = "/"+asset_name

        # Reference the asset at the root of the override layer
        xform = layer.DefinePrim(asset_sdf_path, 'Xform')
        xform.GetReferences().AddReference(asset_path)
        layer.SetDefaultPrim(layer.GetPrimAtPath(asset_sdf_path))
        layer.GetRootLayer().Save()
        
        cmds.setAttr(node + ".filePath", override_path, type="string")
        cmds.connectAttr("time1.outTime", node + ".time")
        return node, layer

def addNewSubAssetReferenceToLayer(layer, default_prim_path, asset_name, asset_path):
        """
        Add a new versioned sub-asset reference to the layer.
        This allows multiple references to the same asset in one layer. (e.g. through tk-multi-loader2)
        Args:
            layer (UsdStage): The USD stage to add the reference to.
            default_prim_path (str): The default prim path for the layer.
            asset_name (str): The name of the asset.
            asset_path (str): The path to the USD layer for the asset.
        Returns:
            str: The Sdf path to the new versioned asset in the layer.
        """

        asset_name_versioned = asset_name + "_" + str(getAssetCountInStage(asset_name,default_prim_path, layer) + 1).zfill(3)
        file_dag_path = f"{default_prim_path}/{asset_name_versioned}"
        xform = layer.DefinePrim(file_dag_path, 'Xform')

        xform.GetReferences().AddReference(asset_path)
        layer.GetRootLayer().Save()
        return file_dag_path

def getAssetCountInStage(self, default_prim_path, asset_name, layer):
    """
    Get the number of versions of the asset in the stage.
    This is used to determine the next version number for the asset.
    Args:
        default_prim_path (str): The default prim path for the layer.
        asset_name (str): The name of the asset.
        layer (UsdStage): The USD stage to check for the asset.
        Returns:
            int: The number of versions of the asset in the stage.
    """

    # Get any asset with the same name and count the versions, then return the highest version
    count = 0
    found = True

    while found == True:
        prim = layer.GetPrimAtPath(default_prim_path+"/"+asset_name + "_" + str(count+1).zfill(3))

        if("invalid null prim" in str(prim)):
            found = False
        else:
            count = count + 1
    return count

def saveUSDOverrideEdits():
    """
    This function saves the current USD override edits for Maya USD stages to new versioned USD files.
    It checks if the override layer is dirty and saves it to a new file in the usd_overrides directory.
    This function could be added to Maya's kBeforeSave callback to automatically save the overrides when the scene is saved.

    import maya.OpenMaya as api
    api.MSceneMessage.addCallback(api.MSceneMessage.kBeforeSave, saveUSDOverrideEdits)
    """
    #import this at runtime because otherwise maya crashes on startup
    import mayaUsd.ufe as mayaUsdUfe 

    usd_overrides_path = "/".join(os.path.dirname(cmds.file(q=True, sn=True)))+"/usd_overrides"
    for n in cmds.ls(type="mayaUsdProxyShape"):
        stage = mayaUsdUfe.getStage(cmds.ls(n, long=True)[0])
        overrideLayer = stage.GetRootLayer()

        if(overrideLayer.dirty and not cmds.getAttr(n+".filePath").startswith(usd_overrides_path)):
            override_path = usd_overrides_path+"/"+n.split("|")[-1]+"_override_v"+str(findLatestOverrideVersion(n.split("|")[-1])+1).zfill(3)+".usd"
            overrideLayer.Export(override_path)
            cmds.setAttr(n + ".filePath", override_path, type="string")
            print(n + " USD layer was dirty - saved new version of overrides")

def findLatestOverrideVersion(asset_name):
    """
    Find the latest version of the USD override for the given asset name.
    """
    usd_overrides_path = "/".join(os.path.dirname(cmds.file(q=True, sn=True)))+"/usd_overrides"
    try:
        if(not os.path.exists(usd_overrides_path)):
            os.mkdir(usd_overrides_path)
        
        current_versions = [x for x in os.listdir(usd_overrides_path) if asset_name+"_override" in x]

        max_version = 0
        for path in current_versions:
            max_version = max(max_version, int(path.split(".usd")[-2][-3:]))

        return max_version

    except Exception as e:
        print(e)

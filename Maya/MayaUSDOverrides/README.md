# Saving Override Edits to a USD Stage with Maya USD

At the UTS Animal Logic Academy, I wrote a pipeline that utilised Maya USD to allow for set assembly and set dressing/layout overrides to be published down the pipe while leaving the original set USD untouched, but there are some quirks.
## Problem
Maya USD stores edits to USD stages in memory while you have the Maya scene open. You can see these layers within the [USD Layer Editor](https://help.autodesk.com/view/MAYAUL/2025/ENU/?guid=GUID-4FAD73CA-E775-4009-9DCB-3BC6792C465E) in Maya. 

However when closing the scene, the edits to USD stages must either be applied to the referenced stages or discarded.
- Maya does have the option to save edits to USD stages within the Maya scene; however, if the edits total to more than 2GB of data, any further edits will be discarded. Not viable for pipeline use.
## Solution
To get around this, we can create a new USD layer that references the USD we wish to edit, and apply overrides to this new USD layer instead. We can even set up a callback to run on scene save to version these override files, so we can go back to a previous version if need be (e.g. with Flow Production Tracking).

### Creating the override layer
The logic for the `mayaUsdProxyShape` and override layer creation can be found in the `createOverrideLayer()` function within [`MayaUSDOverrides.py`](./MayaUSDOverrides.py)
```
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
        
        # Create override layer for layout set overrides/to combine fx set layers
        usd_overrides_path = "/".join(cmds.file(q=True, sn=True).split("/")[0:-2])+"/usd_overrides"
        if(not os.path.exists(usd_overrides_path)):
            os.mkdir(usd_overrides_path)

        #node = cmds.ls(asset_name, long=True)[0]
        stage = mayaUsdUfe.getStage(node_long)

        # Create a new versioned override layer
        override_path = usd_overrides_path+"/"+asset_name+"_override_v"+str(findLatestOverrideVersion(asset_name)+1).zfill(3)+".usda"
        
        layer = stage.CreateNew(override_path)
        asset_sdf_path = "/"+asset_name

        xform = layer.DefinePrim(asset_sdf_path, 'Xform')
        xform.GetReferences().AddReference(asset_path)
        layer.SetDefaultPrim(layer.GetPrimAtPath(asset_sdf_path))
        layer.GetRootLayer().Save()
       ts 
        cmds.setAttr(node + ".filePath", override_path, type="string")
        cmds.connectAttr("time1.outTime", node + ".time")
        return node, layer
```

### Adding new sub-assets (set-dressing)
The logic for adding multiple versions of a sub-asset can be found in `addNewSubAssetReferenceToLayer()` within [`MayaUSDOverrides.py`](./MayaUSDOverrides.py)

```
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
```

### Version control with override layers (saving the edits non-destructively)
When saving the Maya scene, a callback checks for any dirty USD stages (USD stages with edits) in the scene, and versions up the dirty stages. It then updates the filepaths for the dirty stage's `mayaUsdProxyShape` to point to the newly saved version.
* The logic for this callback can be found in the `saveUSDOverrideEdits()` function within [`MayaUSDOverrides.py`](./MayaUSDOverrides.py)
```
def saveUSDOverrideEdits():
    """
    This function saves the current USD override edits for Maya USD stages to new versioned USD files.
    It checks if the override layer is dirty and saves it to a new file in the usd_overrides directory.
    This function could be added to Maya's kBeforeSave callback to automatically save the overrides when the scene is saved.

    import maya.OpenMaya as api
    api.MSceneMessage.addCallback(api.MSceneMessage.kBeforeSave, saveUSDOverrideEdits)
    """
    import mayaUsd.ufe as mayaUsdUfe #import this at runtime because otherwise maya crashes on startup
    usd_overrides_path = "/".join(cmds.file(q=True, sn=True).split("/")[0:-2])+"/usd_overrides"
    for n in cmds.ls(type="mayaUsdProxyShape"):
        stage = mayaUsdUfe.getStage(cmds.ls(n, long=True)[0])
        overrideLayer = stage.GetRootLayer()
        if(overrideLayer.dirty and not cmds.getAttr(n+".filePath").startswith(usd_overrides_path)):
            override_path = usd_overrides_path+"/"+n.split("|")[-1]+"_override_v"+str(findLatestOverrideVersion(n.split("|")[-1])+1).zfill(3)+".usd"
            overrideLayer.Export(override_path)
            cmds.setAttr(n + ".filePath", override_path, type="string")
            print(n + " USD layer was dirty - saved new version of overrides")
```

### Example
An example layer created with these functions can be found in [usd_overrides/setTest01_override_v001.usda](./usd_overrides/setTest01_override_v001.usda)

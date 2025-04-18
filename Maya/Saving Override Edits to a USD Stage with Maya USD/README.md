## Saving Override Edits to a USD Stage with Maya USD

# Saving Override Edits to a USD Stage with Maya USD

At the UTS Animal Logic Academy, I wrote a pipeline that utilised Maya USD to allow for set assembly and set dressing/layout overrides to be published down the pipe while leaving the original set USD untouched, but there are some quirks.
## Problem
Maya USD stores edits to USD stages in memory while you have the Maya scene open. You can see these layers within the [USD Layer Editor](https://help.autodesk.com/view/MAYAUL/2025/ENU/?guid=GUID-4FAD73CA-E775-4009-9DCB-3BC6792C465E) in Maya. 

However when closing the scene, the edits to USD stages must either be applied to the referenced stages or discarded.
- Maya does have the option to save edits to USD stages within the Maya scene; however, if the edits total to more than 2GB of data, any further edits will be discarded. Not viable for pipeline use.
## Solution
To get around this, we can create a new USD layer that references the USD we wish to edit, and apply overrides to this new USD layer instead. We can even set up an onSave callback to version these override files, so we can go back to a previous version if need be (e.g. with Flow Production Tracking).

- The logic for the `mayaUsdProxyShape` and override layer creation can be found in the `createOverrideLayer()` function within `MayaUSDOverrides.py`
- The logic for adding multiple versions of one asset can be found in `addNewSubAssetReferenceToLayer()` within `MayaUSDOverrides.py`

When saving the Maya scene, a callback checks for any dirty USD stages (USD stages with edits) in the scene, and versions up the dirty stages. It then updates the filepaths for the dirty stage's `mayaUsdProxyShape` to point to the newly saved version.
* The logic for this callback can be found in the `saveUSDOverrideEdits()` function within `MayaUSDOverrides.py`
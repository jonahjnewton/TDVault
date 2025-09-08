---
layout: post
title: Creating/Pasting Nodes in a Floating Layer in Katana
---
When creating a node in Foundry's Katana through the Tab menu (or pasting a node), the node enters a "floating" state which allows the user to place the node wherever they like.

When creating a node (or pasting a node) programatically in Katana, the node is placed directly into the scene graph.

You can replicate the "floating" functionality programmatically by getting the Node Graph's Tab object and using the `prepareFloatingLayerWithPasteBounds` and `enableFloatingLayer` functions.
  
```python
# This first line pastes a node based on an xmlTree.
# This could also simply be a new node made with NodegraphAPI.CreateNode()
newNode = KatanaFile.Paste(xmlTree, NodegraphAPI.GetRootNode())[0]

nodeGraphTab = UI4.App.Tabs.FindTopTab('Node Graph')
nodeGraphTab.prepareFloatingLayerWithPasteBounds([newNode])
nodeGraphTab.enableFloatingLayer()
```

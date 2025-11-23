---
layout: post
title: Katana Scripting - Creating/Pasting Nodes in a Floating Layer
description: Katana Scripting - When creating a node in Katana through the Tab menu, the node enters a floating state in which the user can place the node wherever they like
---
Katana scripting is commonplace for surfacing/lighting artists in the post-production industry, who just want to create tools which are easy to use and intuitive for themselves and their peers. 

When creating a node in Foundry's Katana through the Tab menu (or pasting a node), the node enters a "floating" state which allows the user to place the node wherever they like. When creating a node (or pasting a node) programatically in Katana, however, the node is placed directly into the scene graph.

You can replicate the "floating" functionality programmatically by getting the Node Graph's Tab object and using the `prepareFloatingLayerWithPasteBounds` and `enableFloatingLayer` functions.
  
```python
# This first line pastes a node based on an xmlTree.
# This could also simply be a new node made with NodegraphAPI.CreateNode()
newNode = KatanaFile.Paste(xmlTree, NodegraphAPI.GetRootNode())[0]

nodeGraphTab = UI4.App.Tabs.FindTopTab('Node Graph')
nodeGraphTab.prepareFloatingLayerWithPasteBounds([newNode])
nodeGraphTab.enableFloatingLayer()
```

At the moment, this method isn't shown in the Katana scripting documentation, so I hope this helps you create some nice user-friendly workflows within your Katana scripting!

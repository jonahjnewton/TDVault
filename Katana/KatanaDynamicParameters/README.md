---
layout: post
title: Programatically Editing Dynamic Parameters in Katana
---
Updating [dynamic parameters](https://learn.foundry.com/katana/dev-guide/Scripting/WorkingWithNodes/Parameters/DynamicParameters.html) in Katana programatically can be a bit complicated - and can act differently when Katana is open in a GUI vs when running renders in batch mode from a command line (such as on a render farm). 

An example of a dynamic parameter can be seen in Katana's **[RenderOutputDefine](https://learn.foundry.com/katana/content/rg/3d_nodes/renderoutputdefine.html)** node. When setting the `locationType` parameter to `file`, a new `renderLocation` parameter is created.

The following functions are very useful in managing these parameters:
## checkDynamicParameters
```python
node = NodegraphAPI.GetNode("RenderOutputDefine1")
node.checkDynamicParameters()
```

When a dynamic parameter is due to be updated when the GUI is not running (when running Katana in batch/script mode), since many of Katana's events which cause nodes to be reevaluated won't be registered (such as UI redraw events), we need to manually tell the node to check if any dynamic parameters need updating and update them before performing any actions on the dynamic parameters.

## ProcessAllEvents
  
```python
from Katana import Utils
Utils.EventModule.ProcessAllEvents()
```

When a node wants to create a dynamic parameter while the user is viewing that node, it schedules an event to update the UI with this new parameter. 

Let's once use the example of a script that allows a user to auto-set an expression for the output location of a **RenderOutputDefine** node. 
* By default, `locationType` is set to local, which means we can't set a location for the render. 
* When we set `locationType` to `file` with Python to create the `renderLocation` parameter, if the user is currently viewing the parameters of the node, we won't be able to access this dynamically created parameter until the UI redraw event runs. 
* So, we need to call `Utils.EventModule.ProcessAllEvents()` before continuing with our code to add a parameter expression.

## Example

```python
from Katana import Utils

node = NodegraphAPI.GetNode("RenderOutputDefine1")
node.getParameter("args.renderSettings.outputs.outputName.rendererSettings.locationType.value").setValue("file",0)

# Tells Katana to check all dynamic parameters that need to be updated on the node
node.checkDynamicParameters()

# Tells Katana to run all pending events (including any update events) before continuing
Utils.EventModule.ProcessAllEvents()

node.getParameter("args.renderSettings.outputs.outputName.rendererSettings.renderLocation.value").setExpression("myExpression()")
```
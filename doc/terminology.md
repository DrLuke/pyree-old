# Terminology
This document outlines the terminology and their meaning used in this project

## Sheet
A sheet is a network of nodes. Once a sheet is opened, you can edit the nodes contained in the sheet. A sheet can have inputs and outputs, and can be included from within another sheet.  
On a technical level a sheet is stored as a json file.

## Scene
A scene is a Sheet with an Init-Node and a Loop-Node. Each project has a 

## Node
A node is a box with inputs and outputs. You can connect multiple Nodes together to create functionality.  
Most nodes have an incoming and outbound exec input/output. The exec links will determine the order of execution of the nodes.  
Nodes without exec links can be regarded as getter functions.

### Init-Node
This is a special node that fires once upon program start and then never again. Use it to initialize things.

### Loop-Node
This is a special node that fires once for every frame. Use it to render your visuals.

## Link
A link connects two nodes. The starting- end endpoint of a link has to be of the same type.
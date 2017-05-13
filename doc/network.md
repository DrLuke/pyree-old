# Network
This document outlines the network protocol used by Pyree.

## TCP
Main communication happens by exchanging json objects via TCP. Every object must contain the following keys:

#### `msgid (int)`
Unique message ID generated with the python 3 [uuid library](https://docs.python.org/3/library/uuid.html#uuid.uuid4), and then [converted](https://docs.python.org/3/library/uuid.html#uuid.UUID.int) to an integer.  
It is used to correspond a reply to an initial request.+

#### `msgtype (string)`
The type of message this is. Depending on the type of the message, it gets decoded differently.

The following types exist:
* `control`
* `sheetdelta`
* `nodedata`
* `request`


## Message types
Each message must only be of one type. For each type there is a different set of keys that must be present:

### `control`
This message type is meant for sending control commands to the worker, like pause or resume, or which sheet to run on which display.

### `sheetdelta`
Changes of sheets get transferred with this command. To save bandwidth and unnecessary information transfer, all node data is limited to the module name and it's links.
Each node is responsible for transferring any extra data it requires.
#### `sheet (int)`
ID of the sheet that this delta is applying to.
#### `addedNodes (object)`
Object containing all nodes that have been newly added to a sheet.
#### `changedNodes (object)`
Object containing all nodes that have changed on a sheet.
#### `removedNodes(object)`
Object containing all nodes that have been removed from a sheet.

## UDP Broadcast
UDP Broadcast is used exclusively to discover new workers in the network. It has the following keys:

#### `ip (string)`
IP address of the broadcasting entity
#### `port (int)`
Port on which the tcp socket is listening



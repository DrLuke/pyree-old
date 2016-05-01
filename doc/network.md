# Network
This document outlines the network protocol used by gpnshader.

## Bare Essentials
Communication happens by exchanging json schemas via TCP. Every schema must contain the following keywords in the topmost object:

### `msgid (int)`
Unique message ID generated with the python 3 [uuid library](https://docs.python.org/3/library/uuid.html#uuid.uuid1), and then [converted](https://docs.python.org/3/library/uuid.html#uuid.UUID.int) to an integer.  
The msgid can be used to reference messages in a reply to commands. This way even delayed replies can still be correlated with the original request. This in turn means that all messages that expect a reply must store their original request for a reasonable amount of time (e.g. 1 minute).

### `status (string)`
The status of a message is a quick way to indicate success or failure of anything. Valid values for status are:  
* `ok`: Used to indicate that no problems are present, everything is fine.
* `error`: Something went wrong, check `message` for a human readable errormessage.
* `command`: This message is a command and thus must have the `command` and `monitor` keywords set to valid values.

## Additional Keywords

### `refid (int)`
A msgid this message is a reply to.

### `message (string)`
A human readable string containing information about the status of things. This could, for example, tell the user why something failed.

### `command (object)`
This is an object that will be passed to the correct glfw-object in the worker. The command object MUST contain a `monitor (string)` keyword so that the worker knows which monitor the command goes to.

## Command Types
This segment describes 

### Worker Commands
Json Schemas exchanges between the controller and worker that are meant directly for the Worker. An example for such a message would be a request to list all availabe monitors.

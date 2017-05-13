





class WorkerHandler():
    def __init__(self):
        self.glfwWorkers = {}

    def run(self):
        """Main loop"""
        # TODO: Read socket connections
        # TODO: Decode messages

    def decodeMessage(self, msg):
        pass

    def passSheetDelta(self, msg):
        for worker in self.glfwWorkers.values():
            worker.decodeSheetdelta(msg)


class glfwWorker():
    """GLFW instance for each display"""
    def __init__(self):
        self.sheetdata = {}

        self.sheetObjects = {}

    def decodeSheetdelta(self, msg):
        sheetid = msg["sheet"]
        if not sheetid in self.sheetdata:
            self.sheetdata[sheetid] = {}
        for nodeid in msg["added"]:
            self.sheetdata[sheetid][nodeid] = msg["added"][nodeid]
        for nodeid in msg["changed"]:
            self.sheetdata[sheetid][nodeid] = msg["added"][nodeid]
        for nodeid in msg["deleted"]:
            del self.sheetdata[sheetid][nodeid]

        self.updateSheetObjects()

    def updateSheetObjects(self):
        for sheetId in self.sheetdata:
            if not sheetId in self.sheetObjects:
                self.sheetObjects[sheetId] = {}
            for nodeId in self.sheetdata[sheetId]:
                if nodeId not in self.sheetObjects[sheetId]:
                    pass    # TODO: Create object from node.modulename
                else:
                    pass    # TODO: Update all IO connections on existing objects
            for nodeId in self.sheetObjects:
                if not nodeId in self.sheetdata[sheetId]:
                    del self.sheetObjects[nodeId]



if __name__ == "__main__":
    wh = WorkerHandler()

    while True:
        wh.run()


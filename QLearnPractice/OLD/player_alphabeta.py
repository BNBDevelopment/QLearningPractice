import collections
import copy
import datetime

max_move_count = 24
current_move_count = 0
playerColor = 0
komi = 2.5
max_depth = 14

previousBoard = "" #how game looks after your last move
currentBoard = "" #home game looks after opponent's last move

#for testing
allNodesGeneratedAllTime = 0

class AlphaBetaNode:
    state = ""
    parent = None
    children = set()
    value = 0
    alpha = 0
    beta = 0
    childThisNodeWouldChoose = None
    depth = 0

    def getState(self):
        return self.state
    def setState(self, updatedState):
        self.state = updatedState
    def getParent(self):
        return self.parent
    def setParent(self, parentNode):
        self.parent = parentNode
    def getChildren(self):
        return self.children
    def setChildren(self,childrenSet):
        self.children = childrenSet
    def getChild(self,childToFind):
        return self.children.get(childToFind)
    def addChild(self,childToAdd):
        self.children.add(childToAdd)
    def getValue(self):
        return self.value
    def setValue(self, val):
        self.value = val
    def getAlpha(self):
        return self.alpha
    def setAlpha(self, val):
        self.alpha = val
    def getDepth(self):
        return self.depth
    def setDepth(self, val):
        self.depth = val
    def getBeta(self):
        return self.beta
    def setBeta(self, val):
        self.beta = val
    def getChildThisNodeWouldChoose(self):
        return self.childThisNodeWouldChoose
    def setChildThisNodeWouldChoose(self, chosen):
        self.childThisNodeWouldChoose = chosen

    def createDuplicate(self):
        newNode = AlphaBetaNode()
        newNode.setAlpha(copy.deepcopy(self.alpha))
        newNode.setBeta(copy.deepcopy(self.beta))
        newNode.setValue(copy.deepcopy(self.value))
        newNode.setState(copy.deepcopy(self.state))
        newNode.setDepth(copy.deepcopy(self.depth))
        newNode.setChildren(self.children)
        newNode.setParent(self.parent)
        newNode.setChildThisNodeWouldChoose(self.childThisNodeWouldChoose)

        return newNode

    def __str__(self):
        return str(self.state)
    def __repr__(self):
        return str(self.state)
    def __hash__(self):
        return hash(self.state)
    def __eq__(self, other):
        if isinstance(other, AlphaBetaNode):
            return self.state == other.state
        else:
            return False
    def __ne__(self, other):
        return (not self.__eq__(other))

def processInput():
        with open("../input.txt", 'r+') as inputFile:
            for lineNumber, lineText in enumerate(inputFile):
                lineText = lineText.rstrip()
                if lineNumber == 0:
                    global playerColor
                    playerColor = int(lineText)
                    print("Setting player color to: " + str(playerColor))
                if lineNumber >= 1 and lineNumber < 6:
                    global previousBoard
                    previousBoard = previousBoard + lineText
                if lineNumber >= 6 and lineNumber < 11:
                    global currentBoard
                    currentBoard = currentBoard + lineText

        with open("../moveCountFile.txt", 'r') as moveCountFile:
            countLine = moveCountFile.readline()
            global current_move_count
            current_move_count = int(countLine.strip())
        moveCountFile.close()

        inputFile.close()
        print("currentboard: " + currentBoard)

def createOutput(myMoveStateActionPair):
    stateAndAction = myMoveStateActionPair.split(",")

    inputFile = open("../output.txt", "w")
    print("output index: " + stateAndAction[1])
    if stateAndAction[1] == "PASS":
        inputFile.write("PASS")
    else:
        myMoveX = int(stateAndAction[1]) % 5
        myMoveY = int(stateAndAction[1]) // 5
        #in i(row),j(column) format
        print("My move...\t i(row): " + str(myMoveY) + "\t j(column): " + str(myMoveX))
        inputFile.write(str(myMoveY) + "," + str(myMoveX))
    inputFile.close()

def evaluateBoard(nextMoveGameBoard):
    global current_move_count
    isEndGame = False
    if previousBoard == currentBoard and currentBoard == nextMoveGameBoard:
        print("After making our move, we have two passes in a row - GAME OVER!")
        isEndGame = True
    elif current_move_count + 1 >= max_move_count:
        print("After making our move, we have reached the max number of moves - GAME OVER!")
        isEndGame = True

    blackScore = nextMoveGameBoard.count("1")
    whiteScore = nextMoveGameBoard.count("2") + komi


    return isEndGame, whiteScore, blackScore

def getAllPotentialNextStates(myalphabetaNode):
    stateToExamine = myalphabetaNode.getState()

    #validNextActions = ["PASS"]
    validNextStates = [copy.deepcopy(myalphabetaNode)] #Passing - no update to gameboard

    for index, char in enumerate(list(stateToExamine)):
        if char == "0":
            successorState = copy.deepcopy(stateToExamine)
            successorState = successorState[:index] + str(playerColor) + successorState[index+1:]

            #print("potentialSucesorState:" + str(successorState))
            if passesLibertyRuleCheck(successorState, index) and passesKoRuleCheck(successorState):
                nodeToAdd = AlphaBetaNode()
                nodeToAdd.setState(successorState)
                nodeToAdd.setParent(myalphabetaNode)
                nodeToAdd.setValue(evaluateBoard(successorState))
                validNextStates.append(nodeToAdd)
                #validNextActions.append(index)

    return set(validNextStates)#, validNextActions

def passesLibertyRuleCheck(successorGameBoardToCheck,index):
    #if we were to place the tile and there is an adjacent (up,down,right,left) free space, then it's valid
    northPointIndex = index - 5
    eastPointIndex = index + 1
    southPointIndex = index + 5
    westPointIndex = index - 1
    if (northPointIndex >= 0 and northPointIndex < 5 and successorGameBoardToCheck[northPointIndex] == 0) or \
            (eastPointIndex >= 0 and eastPointIndex < 5 and successorGameBoardToCheck[eastPointIndex] == 0) or \
            (southPointIndex >= 0 and southPointIndex < 5 and successorGameBoardToCheck[southPointIndex] == 0) or \
            (westPointIndex >= 0 and westPointIndex < 5 and successorGameBoardToCheck[westPointIndex] == 0):
        return True
    else:
        #FIX
        #TODO: Now we need to check if placing the tile opens up space by capturing enemy pieces
        return True

def passesKoRuleCheck(successorGameBoardToCheck):
    if previousBoard != successorGameBoardToCheck:
        #print("Passed KO Rule!")
        return True
    #Our chosen move is brings us to a loop - we would make the board look like it did after our last move! Illegal by Ko rule!
    #print("FAILED KO Rule!")
    return False















def absEvaluateBoard(nextMoveGameBoard):
    global current_move_count
    isEndGame = False
    if previousBoard == currentBoard and currentBoard == nextMoveGameBoard:
        print("After making our move, we have two passes in a row - GAME OVER!")
        isEndGame = True
    elif current_move_count + 1 >= max_move_count:
        print("After making our move, we have reached the max number of moves - GAME OVER!")
        isEndGame = True

    blackScore = nextMoveGameBoard.count("1")
    whiteScore = nextMoveGameBoard.count("2") + komi

    totalScore = 0
    global playerColor
    if playerColor == 1:
        totalScore = blackScore - whiteScore
    else:
        totalScore = whiteScore - blackScore
    return isEndGame, totalScore

def getMaxValueChildAndStoreAll(someNode, layerStorageNodes, DFSQueue, depth):
    stateToExamine = someNode.getState()

    passNode = someNode.createDuplicate()
    validNextStateNodes = set()
    validNextStateNodes.add(passNode)

    #Default is pass - can we find a better move?
    maxValue = passNode.getValue()
    maxNode = passNode

    if depth % 2 == 1: #MIN PARENT #odd value, so its our move, so parent was their move
        moveColor = playerColor
    else:
        if playerColor == 1:
            moveColor = 2
        else:
            moveColor = 1

    additionalNodesGeneratedCount = 0
    for index, char in enumerate(list(stateToExamine)):
        if char == "0":
            successorState = copy.deepcopy(stateToExamine)
            successorState = successorState[:index] + str(moveColor) + successorState[index+1:]

            if passesLibertyRuleCheck(successorState, index) and passesKoRuleCheck(successorState):
                #boardValue = evaluateBoard(successorState)[1] #CHECK

                nodeToAdd = AlphaBetaNode()
                nodeToAdd.setState(successorState)
                nodeToAdd.setParent(someNode)
                #nodeToAdd.setValue(boardValue) #CHECK
                nodeToAdd.setAlpha(someNode.getAlpha())
                nodeToAdd.setBeta(someNode.getBeta())
                nodeToAdd.setDepth(someNode.getDepth() + 1)

                #if node is not in layerStorage OR
                #if depth of found node in layerStorage <= nodeToAdd then we want to update it in our table
                layerStorageNodes[nodeToAdd.getState()] = nodeToAdd
                someNode.addChild(nodeToAdd)

                if nodeToAdd.getValue() >= maxValue:
                    maxValue = nodeToAdd.getValue()
                    maxNode = nodeToAdd

                additionalNodesGeneratedCount = additionalNodesGeneratedCount + 1
                global allNodesGeneratedAllTime
                allNodesGeneratedAllTime = allNodesGeneratedAllTime + 1
                DFSQueue[nodeToAdd] = successorState

    if maxNode != passNode:
        DFSQueue.move_to_end(maxNode)

def updateParent(someNode, depth, DFSQueue):
    print("Updating parent of: " + str(someNode))
    parent = someNode.getParent()
    print("parent: " + str(parent))

    if depth % 2 == 1: #MIN PARENT #odd value, so its our move, so parent was their move
        parentValue = min(parent.getValue(), someNode.getValue())
        #print("TESTING1: " + str(parentValue))
        #print("TESTING2: " + str(parent.getAlpha()))
        if parentValue < parent.getAlpha():
            print("MIN node pruning!")
            #print("DFSQueue: " + str(DFSQueue))
            parent.setValue(parentValue)
            #TODO: remove all of alpha's children from the list of nodes to explore and RETURN
            for child in parent.getChildren():
                if child in DFSQueue:
                    print("Removing: " + str(child))
                    del DFSQueue[child]

        parentBeta = min(parent.getBeta(), parentValue)
        parent.setBeta(parentBeta)

    if depth % 2 == 0: #MAX PARENT #even value, so its their move, so parent was our move
        parentValue = max(parent.getValue(), someNode.getValue())
        if parentValue >= parent.getBeta():
            print("MAX node pruning!")
            #print("DFSQueue: " + str(DFSQueue))
            parent.setValue(parentValue)
            #TODO: remove all of alpha's children from the list of nodes to explore and RETURN
            for child in parent.getChildren():
                if child in DFSQueue:
                    print("Removing: " + str(child))
                    del DFSQueue[child]

        parentAlpha = max(parent.getAlpha(), parentValue)
        parent.setAlpha(parentAlpha)


def decideGameMove():
    global max_depth
    global currentBoard

    inputNode = AlphaBetaNode()
    inputNode.setParent(None)
    inputNode.setState(currentBoard)
    inputNode.setDepth(1)
    inputNode.setAlpha(1)
    inputNode.setBeta(1)

    layerStorageNodes = {}

    DFSQueue = collections.OrderedDict()
    DFSQueue[inputNode] = inputNode.getState()

    depth = 0
    while len(DFSQueue) > 0:
        workingNode = DFSQueue.popitem()[0]
        print("workingNode: " + str(workingNode))
        depth = workingNode.getDepth()



        print("DEPTH: " + str(depth))
        if depth == max_depth:
            #so we have a leaf tnode
            #evaluateLeafNode
            #get leafnode parents
            workingNode.setValue(evaluateBoard(workingNode.getState())[1])
            updateParent(workingNode, depth, DFSQueue)
            #send alpha, beta, val up to parent
        else:
            # determine here if we should explore the children of this node or not
            getMaxValueChildAndStoreAll(workingNode, layerStorageNodes, DFSQueue, depth)






if __name__ == '__main__':
    print("Start Time: " + str(datetime.datetime.now()))
    processInput()
    myMove = decideGameMove()

    print("allNodesGeneratedAllTime: " + str(allNodesGeneratedAllTime))
    print("End Time: " + str(datetime.datetime.now()))

    #inputNode1 = AlphaBetaNode()
    #inputNode1.setParent(None)
    #inputNode1.setState("0011000210002000201202000")
    #inputNode1.setValue(evaluateBoard(currentBoard))

    #inputNode2 = AlphaBetaNode()
    #inputNode2.setParent(inputNode1)
    #inputNode2.setState("0011000210002000201202000")
    #inputNode2.setValue(evaluateBoard(currentBoard))

    #print(inputNode1 == inputNode2)
    #print(hash(inputNode1) == hash(inputNode2))

    #createOutput(myMove)
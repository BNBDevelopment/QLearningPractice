import copy
import datetime
import multiprocessing
import queue
import textwrap

max_move_count = 24
current_move_count = 0
playerColor = 0
komi = 2.5
max_depth = 4

previousBoard = "" #how game looks after your last move
currentBoard = "" #home game looks after opponent's last move

class AlphaBetaNode:
    state = ""
    parent = None
    children = queue.PriorityQueue()
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
    def addChild(self,valuechildPair):
        self.children.put(valuechildPair)
    def getDepth(self):
        return self.depth
    def setDepth(self, val):
        self.depth = val
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

    def __lt__(self, other):
        if isinstance(other, AlphaBetaNode):
            selfCountPlayer = self.state.count(str(playerColor))
            selfCountEnemy = 25 - self.state.count("0") - selfCountPlayer

            otherCountPlayer = self.state.count(str(playerColor))
            otherCountEnemy = 25 - self.state.count("0") - otherCountPlayer
            return (selfCountPlayer-selfCountEnemy) < (otherCountPlayer-otherCountEnemy)
        else:
            return False

def processInput():
        with open("input.txt", 'r+') as inputFile:
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

        with open("moveCountFile.txt", 'r+') as moveCountFile:
            countLine = moveCountFile.readline()
            global current_move_count

            if countLine.strip() == "":
                current_move_count = 0
            else:
                current_move_count = int(countLine.strip())
        moveCountFile.close()

        with open("moveCountFile.txt", 'w+') as moveCountFile:
            if currentBoard.count("0") == 25:
                moveCountFile.write("1")
            else:
                moveCountFile.write(str(current_move_count+2))
        inputFile.close()
        print("currentboard: " + currentBoard)

def createOutput(childOfStartNode):
    outFile = open("output.txt","w")

    global currentBoard
    nextState = childOfStartNode.getState()

    changeIndex = -1
    for index, character in enumerate(currentBoard):
        #print("index: " + str(index))
        global playerColor
        if currentBoard[index] != nextState[index] and nextState[index] == str(playerColor):
            changeIndex = index

    if changeIndex == -1:
        outFile.write("PASS")
    else:
        myMoveX = int(changeIndex) % 5
        myMoveY = int(changeIndex) // 5
        outFile.write(str(myMoveY) + "," + str(myMoveX))

    outFile.close()

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

def absEvaluateBoard(givenBoard):
    nextMoveGameBoard = copy.deepcopy(givenBoard)

    totalOneFreeAdjacentSpots = 0
    totalTwoFreeAdjacentSpots = 0

    for index, char in enumerate(list(nextMoveGameBoard)):

        if nextMoveGameBoard[index] != "0" and (nextMoveGameBoard[index] == str("1") or nextMoveGameBoard[index] == str("2")):

            queueOfIndexesToCheck = queue.LifoQueue()
            queueOfIndexesToCheck.put(index)
            listOfFreeBorderNodes = set()
            listOfNodes = set()
            listOfNodes.add(index)
            indexColor = nextMoveGameBoard[index]
            isFreeGroup = False

            while queueOfIndexesToCheck.qsize() > 0:
                workingIndex = queueOfIndexesToCheck.get()

                nextMoveGameBoard = nextMoveGameBoard[:workingIndex] + "C" + nextMoveGameBoard[workingIndex + 1:]

                northIndex = int(workingIndex) - 5
                eastIndex = int(workingIndex) + 1
                westIndex = int(workingIndex) - 1
                southIndex = int(workingIndex) + 5

                if northIndex >= 0 and northIndex < 25:
                    if nextMoveGameBoard[northIndex] == "0":
                        listOfFreeBorderNodes.add(northIndex)
                    elif nextMoveGameBoard[northIndex] == indexColor:
                        if northIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(northIndex)
                            listOfNodes.add(northIndex)
                if eastIndex >= 0 and eastIndex < 25 and not (eastIndex % 5 == 0):
                    if nextMoveGameBoard[eastIndex] == "0":
                        listOfFreeBorderNodes.add(eastIndex)
                    elif nextMoveGameBoard[eastIndex] == indexColor:
                        if eastIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(eastIndex)
                            listOfNodes.add(eastIndex)
                if westIndex >= 0 and westIndex < 25 and not (westIndex % 5 == 4):
                    if nextMoveGameBoard[westIndex] == "0":
                        listOfFreeBorderNodes.add(westIndex)
                    elif nextMoveGameBoard[westIndex] == indexColor:
                        if westIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(westIndex)
                            listOfNodes.add(westIndex)
                if southIndex >= 0 and southIndex < 25:
                    if nextMoveGameBoard[southIndex] == "0":
                        listOfFreeBorderNodes.add(southIndex)
                    elif nextMoveGameBoard[southIndex] == indexColor:
                        if southIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(southIndex)
                            listOfNodes.add(southIndex)

            if indexColor == "1":
                totalOneFreeAdjacentSpots = totalOneFreeAdjacentSpots + len(listOfFreeBorderNodes)
            if indexColor == "2":
                totalTwoFreeAdjacentSpots = totalTwoFreeAdjacentSpots + len(listOfFreeBorderNodes)

    finalScore = 0
    global playerColor
    if playerColor == 1:
        blackScore = givenBoard.count("1") - 1 #If you start then you are here evaling a move that is one more than the enemy
        whiteScore = givenBoard.count("2")

        diffScore = ((blackScore - whiteScore) * 6.0) - (komi * 3.0)

        finalScore = diffScore + totalOneFreeAdjacentSpots - (4*totalTwoFreeAdjacentSpots)

    if playerColor == 2:
        blackScore = givenBoard.count("1")  # If they start then you are here evaling a move that is at the same count as enemy'smove (each have placed x tiles)
        whiteScore = givenBoard.count("2")

        diffScore = ((whiteScore - blackScore) * 6.0) + (komi * 3.0)

        finalScore = diffScore + totalTwoFreeAdjacentSpots - (4*totalOneFreeAdjacentSpots)

    isEndGame = False
    if previousBoard == currentBoard and currentBoard == nextMoveGameBoard:
        isEndGame = True
    elif current_move_count + 1 >= max_move_count:
        isEndGame = True

    return isEndGame, finalScore

def doAlphaBetaSearch():
    processInput()

    global currentBoard
    global previousBoard

    previousNode = AlphaBetaNode()
    previousNode.setParent(None)
    previousNode.setState(previousBoard)
    previousNode.setDepth(0)

    inputNode = AlphaBetaNode()
    inputNode.setParent(previousNode)
    inputNode.setState(currentBoard)
    inputNode.setDepth(1)

    global max_depth
    if current_move_count == 22:
        max_depth = 4
    elif current_move_count == 23:
        max_depth = 3
    elif current_move_count == 24 or current_move_count == 25:
        max_depth = 2
    elif currentBoard.count("0") <= 5:
        max_depth = 7
    elif currentBoard.count("0") <= 10:
        max_depth = 6


    vVal = maxPlayerMove(inputNode, -999999999999, 999999999999)

    print("Finished!")
    print("Start Value: " + str(absEvaluateBoard(currentBoard)[1]))
    print("Chosen child of start: " + str(inputNode.getChildThisNodeWouldChoose()))
    for part in textwrap.wrap(str(inputNode.getChildThisNodeWouldChoose()), 5): print(part)

    if inputNode.getChildThisNodeWouldChoose() is None:
        noNode = AlphaBetaNode()
        noNode.setParent()
        noNode.setState(currentBoard)
        noNode.setDepth(1)
        inputNode.setChildThisNodeWouldChoose(noNode)

    print("Chosen child of start value: " + str(absEvaluateBoard(inputNode.getChildThisNodeWouldChoose().getState())))
    print("End Value: " + str(vVal))
    createOutput(inputNode.getChildThisNodeWouldChoose())


def removeSurroundedTiles(givenState, placedTileColor):
    successorState = copy.deepcopy(givenState)

    #1 first
    for index, char in enumerate(list(successorState)):

        if successorState[index] != "0" and successorState[index] != str(placedTileColor):

            queueOfIndexesToCheck = queue.LifoQueue()
            queueOfIndexesToCheck.put(index)
            listOfBorderNodes = set()
            listOfNodes = set()
            listOfNodes.add(index)
            indexColor = successorState[index]
            isFreeGroup = False

            while queueOfIndexesToCheck.qsize() > 0:
                workingIndex = queueOfIndexesToCheck.get()

                northIndex = int(workingIndex) - 5
                eastIndex = int(workingIndex) + 1
                westIndex = int(workingIndex) - 1
                southIndex = int(workingIndex) + 5

                if northIndex >= 0 and northIndex < 25:
                    if successorState[northIndex] == "0":
                        isFreeGroup = True
                        #print("Not part of group to exclude: " + str(workingIndex))
                        break
                    elif successorState[northIndex] == indexColor:
                        if northIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(northIndex)
                            listOfNodes.add(northIndex)
                    #elif successorState[northIndex] != indexColor:
                    #    listOfBorderNodes.add()


                if eastIndex >= 0 and eastIndex < 25 and not(eastIndex%5 == 0):
                    if successorState[eastIndex] == "0":
                        isFreeGroup = True
                        #print("Not part of group to exclude: " + str(workingIndex))
                        break
                    elif successorState[eastIndex] == indexColor:
                        if eastIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(eastIndex)
                            listOfNodes.add(eastIndex)
                    #elif successorState[eastIndex] != indexColor:
                    #    listOfBorderNodes.add()
                if westIndex >= 0 and westIndex < 25 and not(westIndex%5 == 4):
                    if successorState[westIndex] == "0":
                        isFreeGroup = True
                        #print("Not part of group to exclude: " + str(workingIndex))
                        break
                    elif successorState[westIndex] == indexColor:
                        if westIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(westIndex)
                            listOfNodes.add(westIndex)
                    #elif successorState[westIndex] != indexColor:
                    #    listOfBorderNodes.add()

                if southIndex >= 0 and southIndex < 25:
                    if successorState[southIndex] == "0":
                        isFreeGroup = True
                        #print("Not part of group to exclude: " + str(workingIndex))
                        break
                    elif successorState[southIndex] == indexColor:
                        if southIndex not in listOfNodes:
                            queueOfIndexesToCheck.put(southIndex)
                            listOfNodes.add(southIndex)
                    #elif successorState[southIndex] != indexColor:
                    #    listOfBorderNodes.add()
            if not isFreeGroup:
                #print("HERE1: " + str(index))
                for indexVal in listOfNodes:
                    #print("Point is surrounded! Removing index: " + str(indexVal))
                    successorState = successorState[:indexVal] + "0" + successorState[indexVal + 1:]
    #print("successorState: " + successorState)
    return successorState


def generateChildren(workingNode):

    moveColor = 0
    opposingColor = 0
    global playerColor
    if workingNode.getDepth() % 2 == 1: #MIN PARENT #odd value, so its our move, so parent was their move
        if playerColor == 1:
            moveColor = 1
            opposingColor = 2
        else:
            moveColor = 2
            opposingColor = 1
    else:
        if playerColor == 1:
            moveColor = 2
            opposingColor = 1
        else:
            moveColor = 1
            opposingColor = 2

    enemyColor = 0
    if playerColor == 1:
        enemyColor = 2
    else:
        enemyColor = 1

    if workingNode.getParent().getState() != workingNode.getState(): #Dont want two passes in a row
        passState = copy.deepcopy(workingNode.getState())
        passNode = AlphaBetaNode()
        passNode.setChildren(queue.PriorityQueue())
        passNode.setState(passState)
        passNode.setParent(workingNode)
        passNode.setDepth(workingNode.getDepth() + 1)
        passVal = passState.count(str(playerColor)) - passState.count(str(enemyColor))
        workingNode.addChild((-passVal, passNode))

    for index, char in enumerate(list(workingNode.getState())):
        if char == "0":
            successorState = copy.deepcopy(workingNode.getState())
            successorState = successorState[:index] + str(moveColor) + successorState[index + 1:]

            firstcleanedState = removeSurroundedTiles(successorState, str(moveColor))
            secondcleanedState = removeSurroundedTiles(firstcleanedState, str(opposingColor))

            if firstcleanedState == secondcleanedState:
                if passesLibertyRuleCheck(firstcleanedState, index) and passesKoRuleCheck(firstcleanedState):

                    #removeSurroundedTiles(successorState, str(moveColor))
                    global alreadyGenerated
                    #if successorState not in alreadyGenerated:
                    nodeToAdd = AlphaBetaNode()
                    nodeToAdd.setChildren(queue.PriorityQueue())
                    nodeToAdd.setState(firstcleanedState)
                    nodeToAdd.setParent(workingNode)
                    nodeToAdd.setDepth(workingNode.getDepth() + 1)

                    #alreadyGenerated.add(successorState)
                    enemyColor = 0
                    if playerColor == 1:
                        enemyColor = 2
                    else:
                        enemyColor = 1
                    nodeVal = firstcleanedState.count(str(playerColor)) - firstcleanedState.count(str(enemyColor))
                    workingNode.addChild((-nodeVal, nodeToAdd))


def maxPlayerMove(workingNode, alpha, beta):
    #print("MAX Move on state: " + workingNode.getState())
    #print("Depth: " + str(workingNode.getDepth()))
    if workingNode.getDepth() == max_depth:
        returnValue = absEvaluateBoard(workingNode.getState())[1]
        #print("Reached Max Depth! \tState: " + str(workingNode.getState()) + "\tValue: " + str(returnValue))
        return returnValue
    vVal = -999999999999

    generateChildren(workingNode)
    for index,priorityChild in enumerate(workingNode.getChildren().queue):
        #print("Child: " + str(index))
        child = priorityChild[1]
        #vVal = max(vVal, minPlayerMove(child, alpha, beta))
        subQueryResults = minPlayerMove(child, alpha, beta)
        if subQueryResults > vVal:
            vVal = subQueryResults
            workingNode.setChildThisNodeWouldChoose(child)


        if vVal >= beta:
            #print("Pruning after checking first nodes: " + str(index) + "\tat depth: " + str(workingNode.getDepth()))
            return vVal
        alpha = max(alpha,vVal)
    return vVal


def minPlayerMove(workingNode, alpha, beta):
    #print("MIN Move on state: " + workingNode.getState())
    #print("Depth: " + str(workingNode.getDepth()))
    if workingNode.getDepth() == max_depth:
        returnValue = absEvaluateBoard(workingNode.getState())[1]
        #print("Reached Max Depth! \tState: " + str(workingNode.getState()) + "\tValue: " + str(returnValue))
        return returnValue
    vVal = 999999999999

    generateChildren(workingNode)
    for index,priorityChild in enumerate(workingNode.getChildren().queue):
        child = priorityChild[1]
        #vVal = min(vVal, maxPlayerMove(child, alpha, beta))
        subQueryResults = maxPlayerMove(child, alpha, beta)
        if subQueryResults < vVal:
            vVal = subQueryResults
            workingNode.setChildThisNodeWouldChoose(child)


        if vVal <= alpha:
            #print("Pruning after checking first nodes: " + str(index) + "\tat depth: " + str(workingNode.getDepth()))
            return vVal
        beta = min(beta, vVal)
    return vVal


def greedyNextMove(givenBoard):
    print("Ran out of time - doing greedy!")
    inputNode = AlphaBetaNode()
    inputNode.setParent(None)
    inputNode.setState(givenBoard)
    inputNode.setDepth(1)

    generateChildren(inputNode)

    maxChild = None
    maxVal = -99999999

    for child in inputNode.getChildren():
        childStateCleared = removeSurroundedTiles(child.getState())
        childVal = absEvaluateBoard(childStateCleared)[1]
        if childVal > maxVal:
            maxChild = child
            maxVal = childVal

    #print("Selecting greedy: " + maxChild.getState())
    createOutput(maxChild)

if __name__ == '__main__':
    print("Start Time: " + str(datetime.datetime.now()))

    #processInput()
    #test1 = absEvaluateBoard("0001100010001011101010101")
    #test2 = absEvaluateBoard("0201100010001011101010101")
    #test3 = absEvaluateBoard("0201110010001011101010101")
    #test4 = absEvaluateBoard("0201112010001011101010101")
    #test5 = absEvaluateBoard("1201112010001011101010101")

    #test6 = absEvaluateBoard("2221122211221010101010101")
    #test7 = absEvaluateBoard("2221122211221010101010101")
    #test8 = absEvaluateBoard("2221122211221010101010101")
    #test9 = absEvaluateBoard("2221122211221010101010101")
    #test10 = absEvaluateBoard("0001100011001011101010101")

    alphaBetaThread = multiprocessing.Process(target=doAlphaBetaSearch)
    alphaBetaThread.start()
    alphaBetaThread.join(9)
    #print("Here3: ")
    if alphaBetaThread.is_alive():
        #print("Here4")
        alphaBetaThread.terminate()
        #print("Here5")
        processInput()
        greedyNextMove(currentBoard)


    #doAlphaBetaSearch(currentBoard)

    print("End Time: " + str(datetime.datetime.now()))

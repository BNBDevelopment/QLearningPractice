import copy
import random
import textwrap
import math

playerColor = 0

previousBoard = [] #how game looks after your last move
currentBoard = [] #home game looks after opponent's last move

gamma = .75
alpha = .4
isTraining = True

def processInput():
    if not isTraining:
        #TODO
        print("PLAYING")
    else:
        inputFile = open("../input.txt", "r")
        statesOfGameFile = None

        myMostRecentMove = ""
        enemyMostRecentMove = ""

        with open("../input.txt", 'r') as inputFile:
            for lineNumber, lineText in enumerate(inputFile):
                lineText = lineText.rstrip()
                #print("LineText: " + lineText)
                if lineNumber == 0:
                    global playerColor
                    playerColor = int(lineText)
                    print("Setting player color to: " + str(playerColor))
                if lineNumber >= 1 and lineNumber < 6:
                    myMostRecentMove = myMostRecentMove + lineText
                    previousBoard.append(list(map(int, lineText)))
                if lineNumber >= 6 and lineNumber < 11:
                    enemyMostRecentMove = enemyMostRecentMove + lineText
                    currentBoard.append(list(map(int, lineText)))

        # Either I am making first move or enemy is so its the start of game
        if enemyMostRecentMove.count("1") + enemyMostRecentMove.count("2") < 2:
            statesOfGameFile = open("../moveCountFile.txt", "w+")
        else:
            statesOfGameFile = open("../moveCountFile.txt", "a+")

        statesOfGameFile.write(myMostRecentMove + "\n")
        statesOfGameFile.write(enemyMostRecentMove + "\n")

        inputFile.close()
        statesOfGameFile.close()


    #TEST
    visualizeGameBoard()

def createOutput(myMove):
    inputFile = open("../output.txt", "w")
    print("output: " + str(myMove))
    stateAndAction = list(myMove[1])
    inputFile.write(stateAndAction[0] + "," + stateAndAction[1])
    inputFile.close()


def decideGameMove():

    validNextStates, validNextActions = getAllPotentialNextStates(currentBoard)

    listOfSearchpairings = []
    for i in range(0,len(validNextStates)):
        textKey = str(validNextStates[i]).replace("[","").replace("]","").replace(" ","").replace(",","")
        searchPairing = textKey + "," + str(validNextActions[i])
        listOfSearchpairings.append(searchPairing)

    relevantActionQVals = []

    #TODO: Optimize file reading for q vals
    with open("storedQVals.txt", "r") as storedQValues:
        for line in storedQValues:
            for searchItem in listOfSearchpairings:
                print("Search item: " + str(searchItem))
                if searchItem in line:
                    relevantActionQVals.append(line.split(","))
                    break
    storedQValues.close()

    print("relevantActionQVals: " + str(relevantActionQVals))
    #choose the right action
    global isTraining

    if isTraining:
        #elements of randomwalk here

        myWeights = []
        for qValLine in relevantActionQVals:
            #print("qValLine: " + str(qValLine))
            weight = int(qValLine[2]) + 1 #TODO: a better way of normalizing values/getting better probability weights
            #print("currweight: " + str(weight))
            myWeights.append(weight)

       # print("Weights: " + str(myWeights))
        weightedProbChosenStateAction = (random.choices(relevantActionQVals, weights=myWeights, k=1))[0]
        print("weightedProbChosenStateAction: " + str(weightedProbChosenStateAction))
        return weightedProbChosenStateAction


    else:
        maxQVal = -100000
        bestNextStateAndAction = None
        for possibleNextState in relevantActionQVals:
            if possibleNextState[2] > maxQVal:
                maxQVal = possibleNextState[2]
                bestNextStateAndAction = (possibleNextState[0],possibleNextState[1])
            elif possibleNextState[2] == maxQVal: #TODO: is this necessary?
                bestNextStateAndAction = random.sample([(possibleNextState[0],possibleNextState[1]), bestNextStateAndAction], 1)

        return bestNextStateAndAction


def getAllPotentialNextStates(gameBoard):
    validNextActions = ["PASS"]
    validNextStates = [gameBoard.copy()] #Passing - no update to gameboard

    for rowNumber in range(0, len(gameBoard)):
        row =  gameBoard[rowNumber]
        for columnNumber in range(0, len(row)):
            print("X Move: " + str(columnNumber) + "\t\tY Move: " + str(rowNumber))
            if gameBoard[rowNumber][columnNumber] == 0:
                #global playerColor
                successorBoard = copy.deepcopy(gameBoard)
                print("Color: " + str(playerColor))
                print("Premove  board: " + str(successorBoard))
                successorBoard[rowNumber][columnNumber] = playerColor
                print("Postmove board: " + str(successorBoard))

                if passesLibertyRuleCheck(successorBoard,columnNumber,rowNumber) and passesKoRuleCheck(successorBoard):
                    validNextStates.append(gameBoard)
                    validNextActions.append(str(columnNumber) + str(rowNumber))
    return validNextStates, validNextActions


def passesLibertyRuleCheck(gameBoardToCheck,actionXCoord,actionYCoord):
    #if we were to place the tile and there is an adjacent (up,down,right,left) free space, then it's valid
    if (actionYCoord+1 > 0 and actionYCoord+1 < 5 and gameBoardToCheck[actionYCoord+1][actionXCoord] == 0) or \
            (actionYCoord-1 > 0 and actionYCoord-1 < 5 and gameBoardToCheck[actionYCoord-1][actionXCoord] == 0) or \
            (actionXCoord+1 > 0 and actionXCoord+1 < 5 and gameBoardToCheck[actionYCoord][actionXCoord+1] == 0) or \
            (actionXCoord-1 > 0 and actionXCoord-1 < 5 and gameBoardToCheck[actionYCoord][actionXCoord-1] == 0):
        return True
    else:
        #FIX
        #TODO: Now we need to check if placing the tile opens up space by capturing enemy pieces
        return True

def passesKoRuleCheck(gameBoardToCheck):
    for rowNumber in range(0, len(gameBoardToCheck)):
        row = gameBoardToCheck[rowNumber]
        for columnNumber in range(0, len(row)):
            if previousBoard[rowNumber][columnNumber] != gameBoardToCheck[rowNumber][columnNumber]:
                return True
    #Our chosen move is brings us to a loop - we would make the board look like it did after our last move! Illegal by Ko rule!
    return False


def postGameUpdateQVals():
    mapOfStatesAndQVals = {}

    with open("storedQVals.txt", "r") as storedQValues:
        with open("../moveCountFile.txt", 'r') as recentGameStates:
            for line in storedQValues:
                for recentGameState in recentGameStates:
                    print("Search item: " + str(recentGameState))
                    if recentGameState in line:
                        qValLine = line.split(",")
                        mapOfStatesAndQVals[qValLine[0]+","+qValLine[1]] = qValLine[2]
                        break
        recentGameStates.close()
    storedQValues.close()

    #update Q vals iterations
    updatesStillToBeMade = True
    global alpha
    while updatesStillToBeMade:
        for stateActionPair in mapOfStatesAndQVals.keys():
            reward = -0.04
            if(stateActionPar is "WIN"):
                reward = 5
            elif (stateActionPar is "WIN"):
                reward = -5
            mapOfStatesAndQVals[stateActionPair] = ((1 - alpha) * mapOfStatesAndQVals[stateActionPair]) + (alpha * (reward))

#for testing only
def visualizeGameBoard():
    print("You are playing as: " + ("Black" if playerColor == 1 else "White"))
    print("PREVIOUSLY: " + str(previousBoard))
    for row in previousBoard:
        line = ""
        for col in row:
            if col == 0: line = line + " _ "
            elif col == 1: line = line + " B "
            elif col == 2: line = line + " W "
        print(line)
    print("CURRENTLY: " + str(currentBoard))
    for row in currentBoard:
        line = ""
        for col in row:
            if col == 0: line = line + " _ "
            elif col == 1: line = line + " B "
            elif col == 2: line = line + " W "
        print(line)



if __name__ == '__main__':
    processInput()
    myMove = decideGameMove()
    createOutput(myMove)


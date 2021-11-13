import copy
import fileinput
import multiprocessing
import sys
from random import randrange

gamma = .75
alpha = .4

max_move_count = 24
current_move_count = 0
playerColor = 0
komi = 2.5


previousBoard = "0000000000000000000000000" #how game looks after your last move
currentBoard = "0000000000000000000000000" #home game looks after opponent's last move

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
        print(currentBoard)

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

def getMaxQValActionForState(givenBoard):
    allPossibleNextStates, allPossibleNextActions = getAllPotentialNextStatesAndActions(givenBoard)

    print("allPossibleNextStates: " + str(allPossibleNextStates))
    print("allPossibleNextActions: " + str(allPossibleNextActions))

    #find which next state has maxQVal
    dictionaryOfQValsEncountered = {}

    alternateUseKeys = []
    searchKeys = []
    for index in range(0, len(allPossibleNextStates)):
        #print("allPossibleNextStates[index] " + str(allPossibleNextStates[index]))
        #print("allPossibleNextActions[index] " + str(allPossibleNextActions[index]))
        searchKeys.append(str(allPossibleNextStates[index]) + "," + str(allPossibleNextActions[index]))
        alternateUseKeys.append(str(allPossibleNextStates[index]) + "," + str(allPossibleNextActions[index]))
    #TODO: improve search for q val efficiency
    with open("storedQVals.txt", "a+") as storedQValues:
        storedQValues.seek(0)
        firstRunPointer = 0
        maxValue = -100000
        maxValStateAction = None
        for line in storedQValues:
            if len(searchKeys) == 0:
                #CHECK if we need this - since we arent repoennign file may point to what we watn already
                break
            else:
                lineKey = line[0:28]
                lineQVal = line[28:]
                dictionaryOfQValsEncountered[lineKey] = lineQVal

                for key in searchKeys:
                    if key in lineKey:

                        #CHECK IF WORKING
                        searchKeys.remove(key)

                        if int(lineQVal) > maxValue:
                            maxValue = int(lineQVal)
                            maxValStateAction = lineKey
                        elif int(lineQVal) == maxValue:
                            print("We have to choose between equal value open spots!")
                            randomOpenSpotOfEqVal = randrange(len(alternateUseKeys))
                            if randomOpenSpotOfEqVal == 0:
                                maxValue = int(lineQVal)
                                maxValStateAction = lineKey

        #firstRunPointer = storedQValues.tell()
        storedQValues.close()
        #If we dont ahve a stored Q val for our state
        if maxValStateAction is None:
            print("NO SAVED Q VAL!")
            for key in alternateUseKeys:
                #print("key here: " + key)
                tempBoard = updateCurrentBoardWithAction(key)
                isEndGame, whiteScore, blackScore = evaluateBoard(tempBoard)
                score = 0
                if playerColor == 1:#black
                    score = blackScore - whiteScore
                else:
                    score = whiteScore - blackScore

                #print("key here: " + key)
                score = score/10
                if score > maxValue:
                    maxValue = score
                    maxValStateAction = key
                elif score == maxValue:
                    #print("We have to choose between equal value open spots!")
                    randomOpenSpotOfEqVal = randrange(len(alternateUseKeys))
                    #print("RandomVal: " + str(randomOpenSpotOfEqVal))
                    if randomOpenSpotOfEqVal == 0:
                        maxValue = score
                        maxValStateAction = key
            #storedQValues.seek(0, 2)
            #storedQValues.write(maxValStateAction + "," + str(maxValue))
        return maxValue, maxValStateAction

    #updateQVals


def updateCurrentBoardWithAction(stateActionPair):
    splitInputString = stateActionPair.split(",")
    chosenMoveIndex = splitInputString[1]
    state = splitInputString[0]

    if chosenMoveIndex == "PASS":
        return state

    global playerColor
    newState = state[:int(chosenMoveIndex)] + str(playerColor) + state[int(chosenMoveIndex)+1:]
    return newState


def doQlearningMove(givenBoard):
    #batch read the lines of the file for memory saving?

    print("doing Q learning game move")
    chosenMaxQVal, updatedStateByActionPair = getMaxQValActionForState(givenBoard)
    print("chosenMaxQVal: " + str(chosenMaxQVal))
    print("SELECTED MOVE! chosenStateActionPair: " + str(updatedStateByActionPair))
    createOutput(updatedStateByActionPair)



    #now to update Q Value with our sample
    updatedBoard = updateCurrentBoardWithAction(updatedStateByActionPair)
    print("second iter board: " + updatedBoard)
    bestNextQVal, bestNextStateActionPair = getMaxQValActionForState(updatedBoard)

    global alpha
    global gamma

    reward_sasprime = 0
    postSecondMoveupdatedBoard = updateCurrentBoardWithAction(bestNextStateActionPair)
    isEndGame, whiteScore, blackScore = evaluateBoard(postSecondMoveupdatedBoard)
    if isEndGame:

        #resetMoveCount
        with open("../moveCountFile.txt", 'w') as moveCountFile:
            moveCountFile.write("0")
        moveCountFile.close()

        if whiteScore > blackScore:
            if playerColor == 1: #black
                reward_sasprime = -10
            else:
                reward_sasprime = 10
        elif whiteScore < blackScore:
            if playerColor == 1: #black
                reward_sasprime = 10
            else:
                reward_sasprime = -10

    print("Old Q Val: " + str(chosenMaxQVal))
    updatedQVal = (1-alpha)*(chosenMaxQVal) + (alpha)*( (reward_sasprime) + (gamma)*(bestNextQVal) )
    print("New Q Val: " + str(updatedQVal))


    existingValueUpdated = False
    chosenAction = updatedStateByActionPair[26:]
    replacementKey = givenBoard + "," + chosenAction
    lineToWrite = replacementKey + "," + str(updatedQVal) + "\n"
    print("Updating Q Vals for state: " + givenBoard + "\t with action: " + chosenAction)

    #with open("storedQVals.txt", 'a+') as qValuesFile:
    #    qValuesFile.seek(0)
    #    for line in qValuesFile:
    #        print("test line: " + line)
    #        print("replacementKey: " + replacementKey)
    #        if replacementKey in line:
     #           print("Found matching!")
    #            qValuesFile.write(lineToWrite)
    #            existingValueUpdated = True

    for line in fileinput.input("storedQVals.txt", inplace=1):
        if replacementKey in line:
            #print("Found replacement!")
            line = line.replace(line, lineToWrite)
            existingValueUpdated = True
            #break
        sys.stdout.write(line)

    if existingValueUpdated is False:
        with open("storedQVals.txt", 'a') as qValuesFile:
            print("no match to update found")
            qValuesFile.write(lineToWrite)
        qValuesFile.close()

def doMINIMAXMove():
    #TODO
    global currentBoard
    myNextStates1, myNextActions1 = getAllPotentialNextStatesAndActions(currentBoard)
    enemyActions1 = []
    for state in myNextStates1:
        enemyNextStates1, enemyNextActions1 = getAllPotentialNextStatesAndActions(state)
        enemyActions1.append(enemyNextStates1)




def decideGameMove():
    #validNextStates, validNextActions = getAllPotentialNextStatesAndActions(currentBoard)
    #stateActionKeys = createKeysFromStateActions(validNextStates, validNextActions)

    #check for q val stuff - max 7 seconds
    global currentBoard
    qValCheckProcess = multiprocessing.Process(target=doQlearningMove(currentBoard))
    qValCheckProcess.start()

    qValCheckProcess.join(7)
    if qValCheckProcess.is_alive():
        #No q value is found in time! Must use alternate method
        qValCheckProcess.terminate()
        doMINIMAXMove()

def evaluateBoard(nextMoveGameBoard):
    global current_move_count
    global playerColor
    isEndGame = False

    if previousBoard == currentBoard and currentBoard == nextMoveGameBoard:
        print("After making our move, we have two passes in a row - GAME OVER!")
        isEndGame = True
    elif current_move_count + 1 >= max_move_count:
        print("After making our move, we have reached the max number of moves - GAME OVER!")
        isEndGame = True


    myTotalScore = 0
    blackScore = nextMoveGameBoard.count("1")
    whiteScore = nextMoveGameBoard.count("2") + komi
    if playerColor == 1:
        myTotalScore = blackScore - whiteScore
    else:
        myTotalScore = whiteScore - blackScore


    return isEndGame, myTotalScoreZ

def getAllPotentialNextStatesAndActions(givenBoard):
    validNextActions = ["PASS"]
    validNextStates = [copy.deepcopy(givenBoard)] #Passing - no update to gameboard

    print("givenBoard: " + str(givenBoard))
    for index, char in enumerate(list(givenBoard)):
        if char == "0":
            successorBoard = copy.deepcopy(givenBoard)
            #print("Color: " + str(playerColor))
            #print("Premove  board: " + str(successorBoard))
            #print("index: " + str(index))
            successorBoard = successorBoard[:index] + str(playerColor) + successorBoard[index+1:]
            #print("Postmove board: " + str(successorBoard))

            if passesLibertyRuleCheck(successorBoard, index) and passesKoRuleCheck(successorBoard):
                validNextStates.append(successorBoard)
                validNextActions.append(index)
    return validNextStates, validNextActions


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

if __name__ == '__main__':
    processInput()
    decideGameMove()
    #createOutput(myMove)

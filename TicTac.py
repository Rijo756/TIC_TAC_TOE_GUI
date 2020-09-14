import numpy as np
import pickle
import re, ast, os
import random
import threading

BOARD_ROWS = 3
BOARD_COLS = 3

#Class state which controls the game. Has two player classes as p1 and p2.

class State:
    def __init__(self, p1, p2):
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        self.p1 = p1
        self.p2 = p2
        self.isEnd = False
        self.boardHash = None
        # init p1 plays first
        self.playerSymbol = 1
        self.winning_player = 0

    # get unique hash of current board state
    def getHash(self):
        self.boardHash = str(self.board.reshape(BOARD_COLS * BOARD_ROWS))
        return self.boardHash

    def get_if_winner(self):
        # row
        for i in range(BOARD_ROWS):
            if sum(self.board[i, :]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[i, :]) == -3:
                self.isEnd = True
                return -1       
        # col
        for i in range(BOARD_COLS):
            if sum(self.board[:, i]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[:, i]) == -3:
                self.isEnd = True
                return -1
        # diagonal
        diag_sum1 = sum([self.board[i, i] for i in range(BOARD_COLS)])
        diag_sum2 = sum([self.board[i, BOARD_COLS - i - 1] for i in range(BOARD_COLS)])
        diag_sum = max(abs(diag_sum1), abs(diag_sum2))
        if diag_sum == 3:
            self.isEnd = True
            if diag_sum1 == 3 or diag_sum2 == 3:
                return 1
            else:
                return -1
        return 0

    def winner(self):
        winner = self.get_if_winner()

        if self.winning_player == winner and self.winning_player != 0:
          if winner == 1:
            #print ("good move by player1")
            self.p1.feedRewardruntime(0.9)
          else:
            #print ("good move by player2")
            self.p2.feedRewardruntime(0.9)
        elif self.winning_player == 1:
          self.p1.feedRewardruntime(0)
        elif self.winning_player == -1:
          self.p2.feedRewardruntime(0)

        self.winning_player = 0

        if winner != 0:
          return winner
        
        diag_sum1 = self.board[0, 0] + self.board[1, 1] + self.board[2, 2]
        diag_sum2 = self.board[0, 2] + self.board[1, 1] + self.board[2, 0]
        diag_sum = max(abs(diag_sum1), abs(diag_sum2))
        if diag_sum == 2:
            if ((diag_sum1 == 2 or diag_sum2 == 2) and self.playerSymbol == 1):
                self.winning_player = 1
            elif (self.playerSymbol == -1):
                self.winning_player = -1
        else:
          for i in range(BOARD_ROWS):
            if sum(self.board[i, :]) == 2 and self.playerSymbol == 1:
              self.winning_player = 1
            elif sum(self.board[i, :]) == -2 and self.playerSymbol == -1:
              self.winning_player = -1
            if sum(self.board[:, i]) == 2 and self.playerSymbol == 1:
              self.winning_player = 1
            elif sum(self.board[:, i]) == -2 and self.playerSymbol == -1:
              self.winning_player = -1

        # tie
        # no available positions
        if len(self.availablePositions()) == 0:
            self.isEnd = True
            return 0
        # not end
        self.isEnd = False
        return None

    def availablePositions(self):
        positions = []
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                if self.board[i, j] == 0:
                    positions.append((i, j))  # need to be tuple
        return positions

    def updateState(self, position):
        self.board[position] = self.playerSymbol
        # switch to another player
        self.playerSymbol = -1 if self.playerSymbol == 1 else 1

    # only when game ends
    def giveReward(self):
        result = self.winner()
        speed = len(self.availablePositions())/9
        #print (result,len(self.availablePositions()),speed)
        # backpropagate reward
        if result == 1:
            states = self.p1.feedReward(1)
            states1 = self.p1.feedReward(speed)
            states2 = self.p2.feedReward(0)
            self.p2.feedRewardHuman(0.95,states)
        elif result == -1:
            states1 = self.p1.feedReward(0)
            states = self.p2.feedReward(1)
            states2 = self.p2.feedReward(speed)
            self.p1.feedRewardHuman(0.95,states)
        else:
            states1 = self.p1.feedReward(0.2)
            states2 = self.p2.feedReward(0.5)

    # board reset
    def reset(self):
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        self.boardHash = None
        self.isEnd = False
        self.playerSymbol = 1

    def play(self, rounds=100):
        for i in range(rounds):
            if i % 1000 == 0:
                print("Rounds {}".format(i))
            while not self.isEnd:
                # Player 1
                positions = self.availablePositions()
                p1_action = self.p1.chooseAction(positions, self.board, self.playerSymbol)
                # take action and upate board state
                self.updateState(p1_action)
                #self.showBoard()
                board_hash = self.getHash()
                self.p1.addState(board_hash)
                # check board status if it is end

                win = self.winner()
                if win is not None:
                    #self.showBoard()
                    #print ("P1 Won")
                    # ended with p1 either win or draw
                    self.giveReward()
                    self.p1.reset()
                    self.p2.reset()
                    self.reset()
                    break

                else:
                    # Player 2
                    positions = self.availablePositions()
                    p2_action = self.p2.chooseAction(positions, self.board, self.playerSymbol)
                    self.updateState(p2_action)
                    #self.showBoard()
                    board_hash = self.getHash()
                    self.p2.addState(board_hash)

                    win = self.winner()
                    if win is not None:
                        #self.showBoard()
                        #print ("P2 Won")
                        # ended with p2 either win or draw
                        self.giveReward()
                        self.p1.reset()
                        self.p2.reset()
                        self.reset()
                        break

    # play with human
    def play2(self):
        while not self.isEnd:
            # Player 1
            positions = self.availablePositions()
            p1_action = self.p1.chooseAction(positions, self.board, self.playerSymbol)
            # take action and upate board state
            self.updateState(p1_action)
            #self.showBoard()
            # check board status if it is end
            win = self.winner()
            if win is not None:
                if win == 1:
                    #print(self.p1.name, "wins!")
                    w = resultGui(self.p1.name)
                    w.mainloop()
                else:
                    #print("tie!")
                    w = resultGui("     Its a Tie !!")
                    w.mainloop()
                self.p1.reset()
                self.p2.reset()
                self.reset()
                break

            else:
                # Player 2
                positions = self.availablePositions()
                p2_action = self.p2.chooseAction(positions, self.board, self.playerSymbol)

                self.updateState(p2_action)
                #self.showBoard()
                win = self.winner()
                if win is not None:
                    if win == -1:
                        #print(self.p2.name, "wins!")
                        w = resultGui(self.p2.name)
                        w.mainloop()
                    else:
                        #print("tie!")
                        w = resultGui("     Its a Tie !!")
                        w.mainloop()
                    self.p1.reset()
                    self.p2.reset()
                    self.reset()
                    break

    def showBoard(self):
        # p1: x  p2: o
        for i in range(0, BOARD_ROWS):
            print('-------------')
            out = '| '
            for j in range(0, BOARD_COLS):
                if self.board[i, j] == 1:
                    token = 'x'
                if self.board[i, j] == -1:
                    token = 'o'
                if self.board[i, j] == 0:
                    token = ' '
                out += token + ' | '
            print(out)
        print('-------------')

#Class Automatic Player which plays the game by itself. This player learn from the rewards.

class Player:
    def __init__(self, name, exp_rate=0.3):
        self.name = name
        self.states = []  # record all positions taken
        self.lr = 0.2
        self.exp_rate = exp_rate
        self.decay_gamma = 0.9
        self.states_value = {}  # state -> value

    def getHash(self, board):
        boardHash = str(board.reshape(BOARD_COLS * BOARD_ROWS))
        return boardHash

    def chooseAction(self, positions, current_board, symbol):
        if np.random.uniform(0, 1) <= self.exp_rate:
            # take random action
            idx = np.random.choice(len(positions))
            action = positions[idx]
            #print ("Random: ",action," with ", self.exp_rate)
        else:
            value_max = -999
            for p in positions:
                next_board = current_board.copy()
                next_board[p] = symbol
                next_boardHash = self.getHash(next_board)
                #print (next_board)
                value = 0 if self.states_value.get(next_boardHash) is None else self.states_value.get(next_boardHash)
                if value >= value_max:
                    value_max = value
                    action = p
            #print ("Selected: ",action," with ", self.exp_rate)
        # print("{} takes action {}".format(self.name, action))
        return action

    # append a hash state
    def addState(self, state):
        self.states.append(state)

    # at the end of game, backpropagate and update states value
    def feedReward(self, reward):
        for st in reversed(self.states):
            for i in range(4):
                #print (st)
                st = st.replace("[ ","[")
                ls = re.sub('\s+', ',', st)
                a = np.array(ast.literal_eval(ls))
                b = [a[6],a[3],a[0],a[7],a[4],a[1],a[8],a[5],a[2]]
                #print (str(np.array(b)))
                st = str(np.array(b))
                if self.states_value.get(st) is None:
                    self.states_value[st] = 0
                self.states_value[st] += self.lr * (self.decay_gamma * reward - self.states_value[st])
                reward = self.states_value[st]
        return self.states

    def feedRewardHuman(self, reward,states):
        for st in reversed(states):
            for i in range(4):
                #print (st)
                st = st.replace("[ ","[")
                ls = re.sub('\s+', ',', st)
                a = np.array(ast.literal_eval(ls))
                b = [a[6],a[3],a[0],a[7],a[4],a[1],a[8],a[5],a[2]]
                #print (str(np.array(b)))
                st = str(np.array(b))
                if self.states_value.get(st) is None:
                    self.states_value[st] = 0
                self.states_value[st] += self.lr * (self.decay_gamma * reward - self.states_value[st])
                reward = self.states_value[st]

    def feedRewardruntime(self,reward):
        if self.states == []:
            return
        st= self.states[-1]
        for i in range(4):
            #print (st)
            st = st.replace("[ ","[")
            ls = re.sub('\s+', ',', st)
            a = np.array(ast.literal_eval(ls))
            b = [a[6],a[3],a[0],a[7],a[4],a[1],a[8],a[5],a[2]]
            #print (str(np.array(b)))
            st = str(np.array(b))
            if self.states_value.get(st) is None:
                self.states_value[st] = 0
            self.states_value[st] += self.lr * (self.decay_gamma * reward - self.states_value[st])
            reward = self.states_value[st]
            #print (self.name," with reward: ", reward," , ",st)

    def reset(self):
        self.states = []

    def savePolicy(self):
        fw = open('policy_' + str(self.name), 'wb')
        pickle.dump(self.states_value, fw)
        fw.close()

    def loadPolicy(self, file):
        fr = open(file, 'rb')
        self.states_value = pickle.load(fr)
        fr.close()

#Class Human Player which plays the game from the GUI

class HumanPlayer:
    def __init__(self, name):
        self.name = name
        self.states = []

    def chooseAction(self, positions, current_board, symbol):
        w = HMI_ttt()
        w.buttontext(current_board)
        w.start()
        while True:
            #print (positions)
            #row = int(input("Input your action row:"))
            #col = int(input("Input your action col:"))
            row,col = w.getval()
            if row == -1 or col == -1:
                continue
                
            action = (row, col)
            if action in positions:
                #self.w.close_button()
                return action
            else:
                w = HMI_ttt()
                w.buttontext(current_board)
                w.start()
                

    # append a hash state
    def addState(self, state):
        self.states.append(state)

    # at the end of game, backpropagate and update states value
    def feedReward(self, reward):
        return self.states

    def feedRewardruntime(self,reward):
        pass
    
    def feedRewardHuman(self, reward,states):
        pass

    def reset(self):
        self.states = []

#Class GUI for the human player

import tkinter
from tkinter import *

class HMI_ttt(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.x = -1
        self.y = -1
        self.press = 0
        self.tk = tkinter.Tk()
        self.tk.title("TIC-TAC-TOE")
        self.button1 = Button( self.tk, text=" ", font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button1))
        self.button1.grid(row=3, column=0)

        self.button2 = Button(self.tk, text=' ', font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button2))
        self.button2.grid(row=3, column=1)

        self.button3 = Button( self.tk, text=' ',font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button3))
        self.button3.grid(row=3, column=2)

        self.button4 = Button( self.tk, text=' ', font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button4))
        self.button4.grid(row=4, column=0)

        self.button5 = Button( self.tk, text=' ', font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button5))
        self.button5.grid(row=4, column=1)

        self.button6 = Button( self.tk, text=' ', font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button6))
        self.button6.grid(row=4, column=2)

        self.button7 = Button( self.tk, text=' ', font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button7))
        self.button7.grid(row=5, column=0)

        self.button8 = Button( self.tk, text=' ', font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button8))
        self.button8.grid(row=5, column=1)

        self.button9 = Button( self.tk, text=' ', font='Times 20 bold', bg='gray', fg='white', height=4, width=8, command=lambda: self.btnClick(self.button9))
        self.button9.grid(row=5, column=2)
        
        
    def start(self):
        self.tk.mainloop()
        
    def buttontext(self,current_board):
        #print ("cc",current_board)
        symbol = [' ','X','O']
        val = current_board.reshape(3 * 3)
        self.button1["text"] = symbol[int(val[0])]
        self.button2["text"] = symbol[int(val[1])]
        self.button3['text'] = symbol[int(val[2])]
        self.button4['text'] = symbol[int(val[3])]
        self.button5['text'] = symbol[int(val[4])]
        self.button6['text'] = symbol[int(val[5])]
        self.button7['text'] = symbol[int(val[6])]
        self.button8['text'] = symbol[int(val[7])]
        self.button9['text'] = symbol[int(val[8])]
        
    def close_button(self):
        self.tk.destroy()
        
    def getval(self):
        if self.press == 1:
            x = self.x
            y = self.y
            self.press = 0
            return x,y
        return -1,-1 
        
    def btnClick(self,button):
        self.press = 1
        if button == self.button1:
            self.x = 0
            self.y = 0
        elif button == self.button2:
            self.x = 0
            self.y = 1
        elif button == self.button3:
            self.x = 0
            self.y = 2
        elif button == self.button4:
            self.x = 1
            self.y = 0
        elif button == self.button5:
            self.x = 1
            self.y = 1
        elif button == self.button6:
            self.x = 1
            self.y = 2
        elif button == self.button7:
            self.x = 2
            self.y = 0
        elif button == self.button8:
            self.x = 2
            self.y = 1
        elif button == self.button9:
            self.x = 2
            self.y = 2
        self.close_button()

#Class the result GUI

class resultGui(tkinter.Tk):

    def __init__(self,res):
        tkinter.Tk.__init__(self)
        self.title("RESULT")
        if "Tie" not in res:
            text = res + " WON !!"
        else:
            text = res
        self.L1 = tkinter.Label(self,font=("Helvetica", 14),text="      "+text)
        self.L1.pack( side = LEFT)
        self.L1.place(x=20, y=40)
        self.button1 = tkinter.Button(self,width=15,height=2,text="Close",command=self.close_button)
        self.button1.pack()
        self.button1.place (x=65 , y = 85)
        self.geometry('{}x{}'.format(250, 150))
        self.resizable(width=False, height=False)

    def close_button(self):
        self.destroy()

if os.path.isfile("policy_Computer"):
    p1 = Player("Computer", exp_rate=0)
    p1.loadPolicy("policy_Computer")
else:
    p1 = Player("Computer")


#-------Training-------
#p2 = Player("P2")
#st = State(p1, p2)
#st.play(50000)
#st = State(p2, p1)
#st.play(50000)
#p1.savePolicy()
#----------------------

NUMBER_OF_ROUNDS = 5

#Playing with Human with GUI

if __name__ == "__main__":
    
    p3 = HumanPlayer("human")
    
    for i in range(NUMBER_OF_ROUNDS):
        
        t = random.getrandbits(1)
        if t == 1:
            st = State(p1, p3)
        else:
            st = State(p3, p1)
        st.play2()

p1.savePolicy()

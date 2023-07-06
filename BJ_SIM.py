#!/usr/bin/env python3
import sys, os
import csv
import datetime, time
from random import shuffle
import numpy as np

from importer.StrategyImporter import StrategyImporter
from module.Custom_Tracker import Tracker
import module.PeaksTroughs as mPT
import module.BJFunctions as mBJF
#import module.Custom_Tracker as mTracker
import DB.BJSQL as sql

DEBUG_PRINT = 0 # Debug Print to Console 
CSV_SUMMARY = 0 # Export SUMMARY to CSV
CSV_DETAILS = 1 # Export DETAILS to CSV ** use exported file in PLAY_FROM_FILE option **
DETAIL_SUMMARY = 0 # Prints to console additional details about each simulation | For ShortSummary set to 0 | DetailSummary set to 1
DB_ENABLE = 0 # Insert results to BJ_DATA DB (path in BJSQL.py Module)

PLAY_FROM_FILE = 0 # Run results from a defined set of results / previous file created when CSV_DETAILS enabled
PLAY_FROM_MID = "00055" # File ID to play from / ignored when PLAY_FROM_FILE =0/false

#DESKTOP = os.path.join(os.path.expanduser("~"),"Desktop") #FOR MAC OS
#PLAY_FILE_NAME =  os.path.join(DESKTOP, "exports/" + PLAY_FROM_MID + "_BJ_DETAILS.csv")
PLAY_FILE_NAME = "exports/" + PLAY_FROM_MID + "_BJ_DETAILS.csv"
if PLAY_FROM_FILE == 1:
    LOG_TAG = "fromfile:"+PLAY_FROM_MID
    #OUTPUT_DETAILS_FILE = os.path.join(DESKTOP, "exports/#BJ_DETAILS_COMP.csv")
    OUTPUT_DETAILS_FILE = "exports/#BJ_DETAILS_COMP.csv"
else:
    LOG_TAG = "test walkaway" #saves TAG/txt to Summary and Detail CSV
    #OUTPUT_DETAILS_FILE = os.path.join(DESKTOP, "exports/00000_BJ_DETAILS.csv")
    OUTPUT_DETAILS_FILE = "exports/00000_BJ_DETAILS.csv"

SIMULATIONS = 2 #Simulation ends when # Shoes is reached OR Player_Bank <=BANK_RUIN OR def GetBL_WA() WALKAWAY returns True
SHOES = 1 #No. of shoes(games) to simulate in each simulation
SHOE_SIZE = 6 # No. of Decks per shoe
SHOE_PENETRATION = 0.25 # Remaining % of cards before shuffle 

#////////// Global Settings and Constants accross Each Simulaton \\\\\\\\\\\\\
NO_HANDS = 2 # No of hands(players) played each round | Set to any # of hands 1 or higher
BET_MINIMUM = 100  # Minimum Bet / hand -- MIN Bet over all hands should be 1-2 % of bank to avoid Ruin --
BET_INCREMENT = 50 # Progressive Bets - Increment wager after each win | set to 0 to disable Progressive betting
USE212 = False # Modified Progressive 
BET_MAX =  BET_MINIMUM * 15 #1500 #Max amount to bet on any one hand (pre split/double)
RESET_BETS = True # Reset Bets to BET_MIN and Streaks after each shoe
EXPECTED_LOSS_RATE = 1 # In percent / divided by 100 at execution | Casino Expected Loss  Theo Loss / For Comps

BANK_START = 10000 # Player Bank
BANK_RUIN =  0 #0 # bank amount below for RUIN
WA_ON_STREAK = 6 # 0 to disable | Times player reaches WIN_STREAK to trigger automatic WALK_AWAY (WA) | uses CT_Streak[WIN_STREAK[1]] to count
WALK_AWAY =  4000 #BET_MINIMUM * NO_HANDS * 10 # PL before Ending Game = WA walkaway
WALK_AWAY_TRIGGER =  12000 #used in conjunction with TRAILING_STOP
TRAILING_STOP = 0 # % of PL to use as trailing stop once WALK_AWAY_TRIGGER is reached when PL is positve | set to 0 to disable
LOSS_STOP = 0 #trailing amount from PlrBnk MIN to earn in event of WA Cut Losses | set to 0 to disable
LOSS_TRIGGER = 2500 # Loss trigger point overrides LOSS_STOP to WA if PL is back to >= 0 after falling below LossTrigger | LOSS_STOP must be > 0 to enable this feature
WALK_AWAY_BREAK = False # True # SET TO TRUE TO BREAK SIMULATION ON WALK AWAY - if False, simulation runs ALL shoes regardless of player PL or WalkAway logic(but tracks PL independently)

WIN_STREAK = [5,5,5]  # [neg count,neutral count, pos count]- dflt WIN_STREAK[1]| when progessive betting the number of consecutive hands to win before resetting to BET_MINIMUM |use inconjunction with COUNT_TIER[0] 
MAX_WIN_STREAK = 5 # MAXIMUM # of wins streak before lowering bet / #setting bet to minimum / overrides other streak settings
WIN_STREAK_RESET = False # Reset progressive after streak is reached - eg. if true hand is no. 7 bet as if 2nd win, etc | when false after win streak consecutive wins are BET_MIN until a loss

#TODO LOSS_STREAK
LOSS_STREAK = 10 # Consecutive losses to raise bet / by player-hand / using LOSS_MULTIPLIER as multiplier
LOSS_MULTIPLIER = 2
MAX_LOSS_STREAK = 20 #

MAXLOSS_DEV = -1 # 20 #Set as percent of starting bank - when bank < X% increase wager by BET_MULTIPLIER_FACTOR (ONLY useful in low # of shoes) | set to -1 to disable
MAXLOSS_DEV_OFF = 2000 # amount of Profit to disable MAXLOSS_DEV and return BM back to 1
BET_MULTIPLIER_FACTOR = 2 # 2= double / when MAXLOSS_DEV active - multiplies wager by factor

# //// WAVES EXPERIMENTAL - Not in use \\\\
##//// ERROR: no such column: nan - Set HH to a lower value - occurs when PL range is too small or # shoes too little \\\\##
HH = BET_MINIMUM * 10 # 1000 #min Height for measuring up/down waves - Lower value if errors occur
HAND_STREAK = 1 #180 # ~ 3 shoes(180) | hands played to determine loss velocity for STD_DEV Waves and Increasing Bet by BET_MULTIPLIER_FACTOR| set to 1 to disable 
SDEV_DWAVE = 5000 #BET_MINIMUM * NO_HANDS * 25 #10000 # STDDEV for Down Waves
SDEV_UWAVE =  4000 #BET_MINIMUM * NO_HANDS * 27 # #5400 # STDDEV for Up Waves

HOUSE_RULES = {
    'triple7': False,  # Count 3x7 as a blackjack
    'hitsoft17': False, # Does dealer hit soft 17
    'allowsurr': True, # Surrender Allowed (Surr any first 2 cards -- not after a split)
    '65BJ': False, # Pay 6-5 odds on Black Jack
    #TODO'maxsplithands': 4 # player max hands to split | aces only split once hard coded 
}

DECK_SIZE = 52.0
CARDS = {"Ace": 11, "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9, "Ten": 10, "Jack": 10, "Queen": 10, "King": 10}

#//////////  COUNTING CARDS OPTIONS  \\\\\\\\\\\\ > goto https://qfit.com/card-counting.htm for all variations
CC_OMEGA_II = {"Ace": 0, "Two": 1, "Three": 1, "Four": 2, "Five": 2, "Six": 2, "Seven": 1, "Eight": 0, "Nine": -1, "Ten": -2, "Jack": -2, "Queen": -2, "King": -2} # ADVANCED Hi-Opt 2
CC_OMEGA_I = {"Ace": 0, "Two": 0, "Three": 1, "Four": 1, "Five": 1, "Six": 1, "Seven": 0, "Eight": 0, "Nine": 0, "Ten": -1, "Jack": -1, "Queen": -1, "King": -1} # MID LEVEL Einstein - Hi-Opt 1
CC_HIGHLOW = {"Ace": -1, "Two": 1, "Three": 1, "Four": 1, "Five": 1, "Six": 1, "Seven": 0, "Eight": 0, "Nine": 0, "Ten": -1, "Jack": -1, "Queen": -1, "King": -1} # Basic Counting 
CC_ACEFIVE = {"Ace": -1, "Two": 0, "Three": 0, "Four": 0, "Five": 1, "Six": 0, "Seven": 0, "Eight": 0, "Nine": 0, "Ten": 0, "Jack": 0, "Queen": 0, "King": 0} # Count Aces and Fives Only

COUNT_STRATEGY = CC_ACEFIVE
USE_COUNT = False # For changing basic strategy | uses secondary file input
CC_RAISEBET = False #Raise bet if cnt is favorable | does not require USECOUNT to be true
CC_2HANDS = False # play 2 hands only when count>= count_tier[0] | must set NO_HANDS =2 
CC_1and1 = False # when true 2nd hand plays CC_RAISEBET, 1st hand plays progressive (CC_2HANDS must be True - does NOT require CC_RAISEBET to be true)
CC_STAND16 = False # Stand on 16 v 10 when count is high(COUNT_TIER[0]) AND surr not permitted - ignored when USE_COUNT is True
CC_HC_MULTIPLIER = 1 #2 # Bet Incremeent HichCount Multiplier to use if count favorable (above 3rd tier) - set in game.set_bets() | set to 1 to disable - does NOT require CC_RAISEBET to be true
BET_SPREAD = [2,3,5] #BET Multiplierr if count is favorable on CC_RAISEBET hands - rel to COUNT_TIER
COUNT_TIER = [3,4,8] # Count Values to modify strategy/bet - Count(cc/cnt) is High or Low (for selecting alternate strategy file) when >= COUNT_TIER[0] or <= COUNT_TIER[0] *-1


#//////////  STRATEGY & FILE IMPORT OPTIONS  \\\\\\\\\\\\
STRATEGY_FILE = "strategy/BOOK_STD17.csv"
HC_STRATEGY_FILE = "strategy/HCstand17-SAMPLE.csv"

#if len(sys.argv) >= 1:
#   STRATEGY_FILE = sys.argv[0] #user passed custom strategy file 
#else:
#   if HOUSE_RULES['hitsoft17'] == True: 
#       #hitsoft17 
#       #STRATEGY_FILE = "BS_H17.csv" 
#   else: #standall17's 
#       STRATEGY_FILE = "BOOKS17.csv"

    
HARD_STRATEGY = {}
SOFT_STRATEGY = {}
PAIR_STRATEGY = {}
HC_HARD_STRATEGY = {}
HC_SOFT_STRATEGY = {}
HC_PAIR_STRATEGY = {}
#TODO #CARD3_STRATEGY = {}
#TODO #LowCount LC STRATEGY File

Player_Bank_Max = [0,0]
Player_Bank_Min = [0,0]

#/////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\
#//// <<<END HEADER  | GLOBAL SETTINGS-OPTIONS>>> \\\\
#/////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\



def blockPrint():
    # Disable Printing to console
    sys.stdout = open(os.devnull, 'w')
    
def enablePrint():
    # Restore Printing to console
    sys.stdout = sys.__stdout__

def debug_print_console():
    if DEBUG_PRINT == 1: 
        enablePrint()
    else:
        blockPrint()

def csv_returnrows(rFile):
    with open(rFile,'r') as file:
        reader = csv.reader(file)
        rows =[]
        for r in reader:
            rows.append(r)
            
        return rows

def csv_detail_create():
    try:
        with open(OUTPUT_DETAILS_FILE,'r') as file:
            reader = csv.reader(file)
            csv_file = csv.DictReader(file)
#            rows = list(csv_file)
#            x = rows[len(rows)-1]
            
        with open(OUTPUT_DETAILS_FILE,'a', newline='') as file:
            writer =csv.writer(file)
            writer.writerow(["XXX","<",datetime.datetime.now(),">"])
            
    except FileNotFoundError:
        with open(OUTPUT_DETAILS_FILE, 'w', newline = '') as file:
            writer = csv.writer(file)
            writer.writerow(["SIM#","Shoe#","Player#","Rnd | Hnd | Mkhd", "Sub_Hand", "Status", "BM | Bet", "$AMT$","Count","P_Total","P_Hand","D_Total","D_Hand","Busted","BJ","Split","Surr","Double","Soft","Bank | PL","Exp Loss"])

#Normal Write Detail Row PLAY_FROM_FILE=FALSE
def csv_detail_write(c_objHand,c_nbhand,c_subhand,c_status,c_amt,c_DH,c_bank,c_bet,d_cards,p_cards,n_sim,s_num,p_num,cc,tc,e_loss): 
    ct = ("%s  |  %s" % (cc,tc)) # Counts
    hd = ("%s  |  %s  |  %s" % (c_nbhand,game.nb_hands[9],game.nb_hands[10])) # Round, No Hands | Marked Hand
    bt = ("%s  |  %s" % (game.get_Bet_Multiplier(),c_bet)) # BM | Bet
    bnk = ("%s  |  %s" % (c_bank, c_bank- BANK_START)) 
    with open(OUTPUT_DETAILS_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        fRow_list = [n_sim,s_num,p_num,hd,c_subhand,c_status,bt,c_amt,ct,c_objHand.value,p_cards,c_DH,d_cards,c_objHand.busted(),c_objHand.blackjack(),c_objHand.splithand,c_objHand.surrender,c_objHand.doubled,c_objHand.soft(),bnk,e_loss]
        if CSV_DETAILS == 1: writer.writerow(fRow_list)
        #writer.writerow([n_sim,s_num,p_num,hd,c_subhand,c_status,bt,c_amt,ct,c_objHand.value,p_cards,c_DH,d_cards,c_objHand.busted(),c_objHand.blackjack(),c_objHand.splithand,c_objHand.surrender,c_objHand.doubled,c_objHand.soft(),bnk,e_loss])
        return fRow_list

#When play from file is TRUE | PLAY_FROM_FILE=TRUE
def csv_write_row(rHand,sBet,sWin): 
    bt = ("%s  |  %s" % (game.get_Bet_Multiplier(),sBet)) # BM | Bet
    with open(OUTPUT_DETAILS_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([rHand[0],rHand[1],rHand[2],rHand[3],rHand[4],rHand[5],bt,sWin,rHand[8],rHand[9],rHand[10],rHand[11],rHand[12],rHand[13],rHand[14],rHand[15],rHand[16],rHand[17],rHand[18],game.Player_Bank])

def csv_sum_create():
    try:
        with open('_BJ_SUMMARY.csv','r') as file:            
            reader = csv.reader(file)
            csv_file = csv.DictReader(file)


        with open('_BJ_SUMMARY.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["XXX ", LOG_TAG, "<",datetime.datetime.now(),">"])
            #writer.writerow(["XXXX"])

            
    except FileNotFoundError:
        with open('_BJ_SUMMARY.csv', 'w', newline = '') as file:
            writer = csv.writer(file)
            writer.writerow(["SIM#","Edge","PL_Range","PnL","Max_Bnk","Min_Bnk","Max_Loss","BetMin","B_Inc","Streak","#Shoes","WalkAwy","REASON"])

def csv_sum_write(S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13):
    with open('_BJ_SUMMARY.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([S1,S2,S3,S6,S5,S4,S7,S8,S9,S10,S11,S12,S13]) #4 & 6. switched intentional
        

#>>> CARD <<<
class Card(object):
    """
    Represents a playing card with name and value.
    """
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "%s" % self.name

#>>> SHOE <<<
class Shoe(object):
    """
    Represents the shoe, which consists of a number of card decks.
    """
    reshuffle = False

    def __init__(self, decks):
        self.count = 0
        self.count_history = []
        self.ideal_count = {}
        self.decks = decks
        self.cards = self.init_cards()
        self.init_count()

    def __str__(self):
        s = ""
        for c in self.cards:
            s += "%s\n" % c
        return s

    def init_cards(self):
        """
        Initialize the shoe with shuffled playing cards and reset count.
        """
        self.count = 0
        self.count_history.append(self.count)

        cards = []
        for d in range(self.decks):
            for c in CARDS:
                for i in range(0, 4):
                    cards.append(Card(c, CARDS[c]))
        shuffle(cards)
        return cards

    def init_count(self):
        """
        Keep track of the number of occurrences for each card in the shoe in the course over the game. ideal_count
        is a dictionary containing (card name - number of occurrences in shoe) pairs
        """
        for card in CARDS:
            self.ideal_count[card] = 4 * SHOE_SIZE

    def deal(self):
        """
        Returns:    The next card off the shoe. If the shoe penetration is reached,
                    the shoe gets reshuffled.
        """
        if self.shoe_penetration() < SHOE_PENETRATION:
            self.reshuffle = True
        
        card = self.cards.pop()
        
        assert self.ideal_count[card.name] > 0, "cc"
        self.ideal_count[card.name] -= 1

        self.do_count(card)
        
        return card

    def do_count(self, card):
        """
        Add the dealt card to current count.
        """
        self.count += COUNT_STRATEGY[card.name]

        self.count_history.append(self.truecount()) #all  strat use true count / ACEFIVE will return hi/lo
        
        #print ("Card: %s - Current Count: %s" % (card,self.truecount()))
    
    def truecount(self):
        """
        Returns: The current true count UNLESS using ACEFIVE (returns hi/lo).
        """
        if COUNT_STRATEGY == CC_ACEFIVE:
            return self.count
        else:
            return round(self.count / (self.decks * self.shoe_penetration()),1)
    
    def get_count(self):
        """
        Returns: The current high/low count.
        """
        return self.count
    
    def shoe_penetration_inv(self):
        """
        Returns: Ratio of cards that have been played relative to all initial playable cards.
        """        
        FD = (DECK_SIZE * self.decks)
        return round(self.shoe_cardsplayed() / (FD - (FD * SHOE_PENETRATION)),1)

    def shoe_penetration(self):
        """
        Returns: Ratio of cards that are still in the shoe to all initial cards.
        """
        return len(self.cards) / (DECK_SIZE * self.decks)
    
    def shoe_cardsplayed(self):
        """
        Returns number of cards played in current shoe
        """
        return (DECK_SIZE * self.decks) - len(self.cards)

#>>> HAND <<<
class Hand(object):
    """
    Represents a hand, either from the dealer or from the player
    """
    _value = 0
    _aces = []
    _aces_soft = 0
    splithand = False
    surrender = False
    doubled = False

    def __init__(self, cards):
        self.cards = cards

    def __str__(self):
        h = ""
        for c in self.cards:
            h += "%s " % c
        return h

    @property
    def value(self):
        """
        Returns: The current value of the hand (aces are either counted as 1 or 11).
        """
        self._value = 0
        for c in self.cards:
            self._value += c.value

        if self._value > 21 and self.aces_soft > 0:
            for ace in self.aces:
                if ace.value == 11:
                    self._value -= 10
                    ace.value = 1
                    if self._value <= 21:
                        break

        return self._value

    @property
    def aces(self):
        """
        Returns all aces in the current hand.
        """
        self._aces = []
        for c in self.cards:
            if c.name == "Ace":
                self._aces.append(c)
        return self._aces

    @property
    def aces_soft(self):
        """
        Returns: The number of aces valued as 11
        """
        self._aces_soft = 0
        for ace in self.aces:
            if ace.value == 11:
                self._aces_soft += 1
        return self._aces_soft

    def soft(self):
        """
        Determines whether the current hand is soft (soft means that it consists of aces valued at 11).
        """
        if self.aces_soft > 0 and not self.blackjack():
            return True
        else:
            return False

    def splitable(self):
        """
        Determines if the current hand can be split.
        """
        if self.length() == 2 and self.cards[0].name == self.cards[1].name:
            return True
        else:
            return False

    def blackjack(self):
        """
        Check a hand for a blackjack
        """
        
        if not self.splithand and self.value == 21:
            if all(c.value == 7 for c in self.cards) and HOUSE_RULES['triple7']:
                return True
            elif self.length() == 2: # 2 card 21 = blackjack and splithand = false
                return True
            else:
                return False
        else:
            return False

    def busted(self):
        """
        Checks if the hand is busted.
        """
        if self.value > 21:
            return True
        else:
            return False

    def add_card(self, card):
        """
        Add a card to the current hand.
        """
        self.cards.append(card)

    def split(self):
        """
        Split the current hand.
        Returns: The new hand created from the split.
        """
        self.splithand = True
        c = self.cards.pop()
        new_hand = Hand([c])
        new_hand.splithand = True
        return new_hand,c

    def length(self):
        """
        Returns: The number of cards in the current hand.
        """
        return len(self.cards)


#>>> PLAYER <<<
class Player(object):
    """
    Represent a player
    """
    def __init__(self, hand=None, dealer_hand=None):
        self.hands = [hand]
        self.dealer_hand = dealer_hand

    def set_hands(self, new_hand, new_dealer_hand):
        self.hands = [new_hand]
        self.dealer_hand = new_dealer_hand

    def play(self, shoe,dealer_upcard):
        for hand in self.hands:
            # print "Playing Hand: %s" % hand
            self.play_hand(hand, shoe,dealer_upcard)

    def set_strategy(self,cnt):
        if cnt >= COUNT_TIER[0] and USE_COUNT == True:
            ss = HC_SOFT_STRATEGY
            sp = HC_PAIR_STRATEGY
            sh = HC_HARD_STRATEGY
        else:
            ss = SOFT_STRATEGY
            sp = PAIR_STRATEGY
            sh = HARD_STRATEGY
        return ss,sp,sh
    
    def play_hand(self, hand, shoe,dealer_upcard):
        split_aces = False
        if hand.length() < 2: #SPLIT HANDS
            if hand.cards[0].name == "Ace":
                hand.cards[0].value = 11
                split_aces = True # split aces once and only take 1 card
            self.hit(hand, shoe) #adding 2nd card to split hand
        
        cc = game.shoe.get_count()
        tc = game.shoe.truecount()

        s_STRATEGY,p_STRATEGY,h_STRATEGY = self.set_strategy(tc)
        
        while not hand.busted() and not hand.blackjack() and not split_aces:
            if hand.soft():
                flag = s_STRATEGY[hand.value][self.dealer_hand.cards[0].name]
            elif hand.splitable():
                flag = p_STRATEGY[hand.value][self.dealer_hand.cards[0].name]
            else:
                flag = h_STRATEGY[hand.value][self.dealer_hand.cards[0].name]

            if flag == 'D':

                if hand.length() == 2:
                    # print "Double Down"
                    hand.doubled = True
                    print ("DOUBLE DOWN: %s" % hand)
                    self.hit(hand, shoe) #take 1 card
                    break
                else:
                    #example: 3 card soft 13 vs 6, dealer 6 = hit, draw 5 now have 4 card soft 18 = Stand
                    if hand.soft() and hand._value > 17:
                        flag = "S"
                        print ("Standing on soft double hand: %s" % hand)
                    else:
                        flag = 'H'
                    
            if flag in ('Sr','RS'): #Can Not Surrender split hands
                if HOUSE_RULES['allowsurr'] and hand.splithand is not True:
                    if hand.length() == 2:
                        print ("Surrender hand: %s" % hand)
                        hand.surrender = True
                        break
                    elif flag == 'RS':
                        flag = 'S' 
                    else:
                        flag = 'H'
                else: #Surrender Not Permitted
                    if flag == 'RS':
                        flag = 'S'
                    else: #Sr
                        if CC_STAND16 and USE_COUNT == False and cc >= COUNT_TIER[0] and hand._value == 16 and dealer_upcard == 10: # standing on 16's vs 10 when count is positive and HC_Strategy not loaded.
                            flag = 'S'
                        else: #hitting when surr not permitted
                            flag = 'H'

            if flag == 'H':
                self.hit(hand, shoe)

            if flag == 'P':
                self.split(hand, shoe,dealer_upcard)

            if flag == 'S':
                break

    def hit(self, hand, shoe):
        c = shoe.deal()
        hand.add_card(c)
        print ("Player hit: %s" % (c))

    def split(self, hand, shoe,dealer_upcard):
        newhand, newcard = hand.split()
        self.hands.append(newhand)
        shoe.do_count(newcard)
        print ("SPLIT %s" % hand)
        self.play_hand(hand, shoe,dealer_upcard)

#>>> DEALER <<<
class Dealer(object):
    """
    Represent the dealer
    """
    def __init__(self, hand=None):
        self.hand = hand

    def set_hand(self, new_hand):
        self.hand = new_hand

    def play(self, shoe):

        if HOUSE_RULES['hitsoft17']:
            while self.hand.value < 17 or (self.hand.value == 17 and self.hand.soft()):
                if self.hand.value == 17 and self.hand.soft():
                    print("DEALER HAS SOFT 17 ")
                self.hit(shoe)
        else:
            while self.hand.value < 17:
                self.hit(shoe)
        if self.hand.value > 21:
            print ("Dealer BUST")
        
    def hit(self, shoe):
        c = shoe.deal()
        self.hand.add_card(c)
        print ("Dealer hit: %s" % (c))

#>>> Streaks Class <<<
class Streaks(object):
    """
    Tracks consecutive Winning/Losing Hands (Streaks) and Hand number
    """
    def __init__(self):
        #///// Track Consiecutive WINs and Losses(streaks) by Hand Number | Count streaks \\\\\
        self.CT_Streak = [0,0,0,0,0,0,0,0,0,0,0] # Count(CT) Streak for progressive - resets after WIN_STREAK is met
        self.L5hnd = [] # tracks losing 5th hand # when winning previous 4
        self.L5ct = 0 # count times when 5th hand lost after winning 4 in a row
        self.L7hnd = [] # tracks losing 7th consecutive hand #
        self.W5hnd = [] # tracks winning 5th consecutive hand #
        self.W_Streak = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # Counts Win Streaks - only resets on loss
        self.L_Streak = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] # Counts Loss Streaks - only resets on win


#>>> GAME Class <<<
class Game(object):
    """
    tracks all metrics for each game/simulation
    """
    def __init__(self):
        self.profitloss = 0 # Bankroll gain/loss
        self.High_Bank = BANK_START
        self.Player_Bank = BANK_START
        self.Player_Bank_byhand = [0] # tracks main player bank by each hand
        self.Player_Bank_Max = [BANK_START,1] #Max, Hand #
        self.Player_Bank_Min =  [BANK_START,1] #Min, Hand #
        self.Player_Stop =  -999999
        self.bet = 0 # Cumulative bets
        self.cards_played = 0 
        self.num_plhands = NO_HANDS
        self.nb_hands = [0,0,0,0,0,0,0,0,0,0,0] #Number Hands - 0rounds, 1win, 2loss, 3push, 4bust, 5bj, 6surr,7DBL_win,8DBL_loss,9hands_all,10 marked hand 
        self.Bet_Multiplier = 1
        self.HC_Multiple = 1
        self.MaxLoss_Dev_Active = False
        self.use212 = USE212
        self.Progressive_Streak = WIN_STREAK[1] #center value by default | progressive bet streak
        
        # objects
        self.streaks = Streaks()
        self.dealer = Dealer()
        
        #metrics tracked by player
        self.wager =[0] #actual wager per hand
        self.player =[0]
        self.Bet_Curr = [0] #current bet /baseline - before modifications for multiplier, double down, etc
        self.Bet_Streak = [0]
        self.L_Streak = [0]
        self.W_Streak = [0]
        self.wins = [0]
        self.loss = [0]
        self.hands_played_pl = [0] # by player
        self.PlayerPL = [0]
        for x in range(1,self.num_plhands+1): # Metrics tracked by player number - player 0 is null
            self.wager.append(0)
            self.player.append(Player())
            self.Bet_Curr.append(BET_MINIMUM)
            self.Bet_Streak.append(0)
            self.L_Streak.append(0)
            self.W_Streak.append(0)
            self.wins.append(0)
            self.loss.append(0)
            self.hands_played_pl.append(0)
            self.PlayerPL.append(0)
    
    def set_cc_wager(self,pl,tc,cc,cTR):
        if pl == 0:
            for x in range(1,self.num_plhands+1):
                self.set_wager(x, tc,cc,cTR)
        else: # when playing from file.
            self.set_wager(pl, tc,cc,cTR)
    
    def set_wager(self,x,tc,cc,cTR):
        #x = player
        self.wager[x] = self.Bet_Curr[x]
        if CC_RAISEBET == True:
            for y in range(len(cTR)-1,-1,-1):
                if tc >= cTR[y]:
                    self.wager[x] *= BET_SPREAD[y]
                    break
                
        elif x == 2 and CC_1and1 == True: #hard coded CC_RAISEBET logic to 2nd hand when 1n1=true and CC_Raisebet = false
            for y in range(len(cTR)-1,-1,-1):
                if tc >= cTR[y]:
                    self.wager[x] *= BET_SPREAD[y] 
                    break
        self.wager[x] *= self.Bet_Multiplier * self.HC_Multiple
        if self.wager[x] > BET_MAX:
            self.wager[x] = BET_MAX
    
#///////////////////////// PLAY ROUND \\\\\\\\\\\\\\\\\\\\\\\\\\
    def play_round(self,n_sim,n_shoe): # sets player,dealer hand
        tc = self.shoe.truecount() 
        cc = self.shoe.get_count()
        
        if CC_2HANDS == True and NO_HANDS > 1:
            if tc >= COUNT_TIER[0]:
                if self.num_plhands == 1:
                    self.Bet_Curr[2] = BET_MINIMUM
                    self.num_plhands = 2
            else: 
                self.num_plhands = 1
                    
        self.set_cc_wager(0,tc,cc,COUNT_TIER)
        player_hand = [0]
        for x in range(1,self.num_plhands+1): # deals player hands
            player_hand.append(Hand([self.shoe.deal(), self.shoe.deal()])) 
        
        dealer_hand = Hand([self.shoe.deal()])
        
        for x in range(1,self.num_plhands+1):
            self.player[x].set_hands(player_hand[x], dealer_hand)

        self.dealer.set_hand(dealer_hand) #upcard only
        dealer_upcard = self.dealer.hand.cards[0].value
        
        print ("--- Round %d ---" % (self.nb_hands[0]))
        for x in range(1,self.num_plhands+1):
            print ("Player Hand: %s %s" % ( x, self.player[x].hands[0]))
            
        print ("Dealer UPCARD: %s" % dealer_upcard)
        self.dealer.hit(self.shoe) #popping dealer hole card
        print ("Dealer Hand: %s" % self.dealer.hand)
        
        #player only plays if the dealer does not have blackjack with ace upcard
        if self.dealer.hand.blackjack() and dealer_upcard > 10:
            print ("Dealer BlackJack - players do not draw")
        else:
            for x in range(1,self.num_plhands+1):
                self.player[x].play(self.shoe,dealer_upcard) # play hand using imported strategy file

        All_Bust, All_BJ = True, True
        for x in range(1,self.num_plhands+1): # check player hands to see if all have Black Jack or All are Busted
            for b_hand in self.player[x].hands:
                if b_hand.busted() != True:
                    All_Bust = False
                    break
            if not self.player[x].hands[0].blackjack():
                All_BJ = False
        
        #dealer only plays if players have not busted all hands AND do not have black jack
        if not All_Bust and not All_BJ: 
            self.dealer.play(self.shoe)
        else:
            if All_BJ:
                print("Players have BLACKJACK - dealer does not draw")
            else:
                print("All Players BUSTED all hands - dealer does not draw")
                
        for PL in range(1,self.num_plhands+1):
            win_net = 0
            subhand = 0
            for hand in self.player[PL].hands: # includes split hands
                win, bet, status = self.get_hand_winnings(hand,PL) # Determine if Win or Lose then adjust bet/banks accordingly def set_bets()
                win_net += win # appends the cumulative wins/losses for hands that include splits/ sub-hands
                self.Player_Bank += win
                self.Player_Bank_byhand.append(self.Player_Bank)
                self.profitloss += win # PL 
                self.PlayerPL[PL] += win # PL by player/hand
                self.bet += bet # Cumulative bet - 
                self.hands_played_pl[PL] += 1 # No hands per game / per player
                self.nb_hands[9] += 1 # counting total hands all players, including splits
                subhand +=1
        
                print ("RESULT: %d.%d " % (self.nb_hands[9],subhand))
                print ("Player:%s $%d (%d) %s| Busted:%r, BlackJack:%r, Splithand:%r, Soft:%r, Surrender:%r, Doubled:%r" % (status,win, hand.value, self.player[PL].hands[subhand-1], hand.busted(), hand.blackjack(), hand.splithand, hand.soft(), hand.surrender, hand.doubled))
                print ("Dealer:    (%d) %s" % (self.dealer.hand.value,self.dealer.hand))
                print ("")
                
                self.set_MinMax_Banks() # Tracks Min and Max player banks / hand no
                
                lRow = csv_detail_write(hand,self.nb_hands[0],subhand,status,win,self.dealer.hand.value,self.Player_Bank,self.wager[PL],self.dealer.hand,self.player[PL].hands[subhand-1],n_sim,n_shoe+1,PL,cc,tc,self.get_expected_loss())
                master.raise_tracker_newhand(lRow,PL) # pass data to Tracker after every hand
                
                
            self.set_bets(win_net,status,PL,cc,tc) #prepares bets for next hand
            master.raise_tracker_handcompleted(subhand, PL,win_net)

    def set_MinMax_Banks(self): # track Min and Max player bank
        if self.Player_Bank > self.Player_Bank_Max[0]:
            self.Player_Bank_Max[0] = self.Player_Bank
            self.Player_Bank_Max[1] = self.nb_hands[9] #set to 0 to use round
        elif self.Player_Bank < self.Player_Bank_Min[0]:
            self.Player_Bank_Min[0] = self.Player_Bank
            self.Player_Bank_Min[1] = self.nb_hands[9] #set to 0 to use round
    
    
    def play_round_from_file(self,fRow): # called every row when reading from file
        win_net =0
        subH =1
        fLen = len(rList)
        fLen -= 1
        pl = int(rList[fRow,2])
        #// added to support count bets from file reading \\#
        ct = rList[fRow,8]
        sp_ct = ct.split('|')
        sp_ct[1] = sp_ct[1].strip()
        sp_ct[0] = sp_ct[0].strip()
        tc = float(sp_ct[1]) 
        cc = float(sp_ct[0])
        self.set_cc_wager(pl,tc,cc,COUNT_TIER)
        #//          END             \\
        
        #// Finding splits/sub-hands \\
        c =1
        if fRow < fLen: subH = int(rList[fRow+c,4])
        while subH > 1:
            if (fRow + c) < fLen:
                c += 1
                subH = int(rList[fRow+c,4]) 
            else:
                subH = 1
                
        #for sub hands (c)
        for x in range(c):
            xRow = fRow+x
            status = rList[xRow,5]
            
            win,bet = self.get_winbet(rList[xRow,17],pl, status)
            win_net += win
            self.Player_Bank += win
            self.Player_Bank_byhand.append(self.Player_Bank)
            self.profitloss += win # PL 
            self.PlayerPL[pl] += win # PL by player
            self.bet += bet # Cumulative bet - 
            self.hands_played_pl[pl] += 1 # No hands per game / per player
            
            if CSV_DETAILS == 1: 
                csv_write_row(rList[xRow],self.wager[pl],win)
                
            self.nb_hands[9] +=1 # No hands per shoe
            self.set_MinMax_Banks()

        self.set_bets(win_net,status,pl,cc,tc) #prepares bets for next hand
        return xRow

    def get_winbet(self,fDbl,pl_num,status): #play_from_file - determine if player win or lose - adjust banks
        win = 0.0 # win/loss multiplier of the bet
        bet = self.wager[pl_num]
        dbl = False
        if fDbl == "True": #DOUBLE
            dbl = True
            bet *= 2
        
        if status == "LOST":
            self.loss[pl_num] += 1
            self.nb_hands[2] += 1
            if dbl:
                win += -2
                self.nb_hands[8] += 1
            else:
                win += -1
                
        elif status == "WON":
            self.wins[pl_num] += 1
            self.nb_hands[1] += 1
            if dbl:
                win += 2
                self.nb_hands[7] += 1
            else:
                win += 1
                
        elif status == "WON BJ":
            self.wins[pl_num] += 1
            self.nb_hands[1] += 1
            self.nb_hands[5] +=1
            if HOUSE_RULES['65BJ']:
                win += 1.2
            else:
                win += 1.5
        elif status == "SURRENDER":
            self.loss[pl_num] += 1
            self.nb_hands[6] += 1
            win += -0.5
        elif status == "PUSH":
            self.nb_hands[3] += 1
            
        win *= self.wager[pl_num]
        return win, bet

        
    def get_hand_winnings(self, hand,pl_num): # set status, determine if player win or lose - adjust banks
        win = 0.0 # win/loss multiplier of the bet
        bet = self.wager[pl_num]
        if not hand.surrender:
            if hand.busted():
                status = "LOST"
                self.nb_hands[4] += 1
            else:
                if hand.blackjack():
                    
                    if self.dealer.hand.blackjack():
                        status = "PUSH"
                    else:
                        status = "WON BJ"
                elif self.dealer.hand.busted():
                    status = "WON"
                elif self.dealer.hand.value < hand.value:
                    status = "WON"
                elif self.dealer.hand.value > hand.value:
                    status = "LOST"
                elif self.dealer.hand.value == hand.value:
                    if self.dealer.hand.blackjack():
                        status = "LOST"  # player's 21 vs dealers blackjack
                    else:
                        status = "PUSH"
        else:
            status = "SURRENDER"
            self.nb_hands[6] += 1

        if status == "LOST":
            self.loss[pl_num] += 1
            self.nb_hands[2] += 1
            if hand.doubled:
                win += -2
                bet *= 2
                self.nb_hands[8] += 1
            else:
                win += -1
        
        elif status == "WON":
            self.wins[pl_num] += 1
            self.nb_hands[1] += 1
            if hand.doubled:
                win += 2
                bet *= 2
                self.nb_hands[7] += 1
            else:
                win += 1
        
        elif status == "WON BJ":
            self.wins[pl_num] += 1
            self.nb_hands[1] += 1
            self.nb_hands[5] +=1
            if HOUSE_RULES['65BJ']:
                win += 1.2
            else:
                win += 1.5
        elif status == "SURRENDER":
            self.loss[pl_num] += 1
            #self.nb_hands[2] += 1
            win += -0.5
        elif status == "PUSH":
            self.nb_hands[3] += 1
        
        win *= self.wager[pl_num]
        return win, bet, status
    
    
    def Reverse(self,data): # Custom reverse function
        current = len(data) 
        lc = current - HAND_STREAK
        #mk hand
        if lc < self.nb_hands[10]:
            lc = self.nb_hands[10]

        while current >= lc:
            current -= 1
            yield data[current]
    
    def temp_SDEV(self):
        #TODO this is experimental code | experimenting with up and down wave deviations...
        if self.Bet_Multiplier == 1:
            #compare bank to prev 150 hands OR Last NB10 | if over threshold raise BM 2 / mark hand nb10
            for pbr in self.Reverse(self.Player_Bank_byhand):
                if pbr - self.Player_Bank >= SDEV_DWAVE:
                    self.nb_hands[10] = self.nb_hands[9] #mark hand
                    self.High_Bank = pbr
                    self.Bet_Multiplier *= BET_MULTIPLIER_FACTOR
                    
                    #for debugging
                    print('##BM SET TO  2##')
                    print('HAND,CURRENT Player Bank, MARKED BANK(high)')
                    print(self.nb_hands[9], self.Player_Bank,pbr)
                    break
                
        elif self.Bet_Multiplier > 1 and self.MaxLoss_Dev_Active == False:
            #check bank V nb10 bank | if >= BM1
            #OR | if bank >= expected loss | bank10 - ep loss = (nbhands(10 - 9) * avgbet * [3% - set as constant]
            #OR | up wave + 1.6 SDdev
            #when resetting BM update NB10 to current hand
            #pr_highbank = self.Player_Bank_byhand[self.nb_hands[10]] + SDEV_DWAVE
            pr_highbank = self.High_Bank
            
            print('HAND,CURRENT Player Bank, HIGH_Bank, EXP Loss')
            print(self.nb_hands[9], self.Player_Bank,pr_highbank,self.get_expected_loss())
            bm1 = False
            if self.Player_Bank >= pr_highbank: # greater than prior highwater mark
                bm1 = True
                print('1 - bm1 is True')
            elif (self.Player_Bank - BANK_START) >= self.get_expected_loss(): # PL > then expected loss
                bm1 = True
                print('2 - bm1 is True')
            #elif self.Player_Bank_byhand[self.nb_hands[10]] - Player_Bank >= SDEV_UWAVE: # gain >= 1.6SD
            elif  self.Player_Bank >= self.Player_Bank_byhand[self.nb_hands[10]] + SDEV_UWAVE:
                bm1 = True
                print('3 - bm1 is True')
                
            if bm1 == True:
                self.Bet_Multiplier = 1
                self.nb_hands[10] = self.nb_hands[9]
                print('BM SET BACK TO  1 - Hand',self.nb_hands[9],'\n')
    
    def set_BM(self): #BET MULTIPLIER FACTOR
        #enablePrint()
        if self.Player_Bank <= (BANK_START * MAXLOSS_DEV / 100) and self.MaxLoss_Dev_Active == False and MAXLOSS_DEV > 0:
            self.Bet_Multiplier = BET_MULTIPLIER_FACTOR
            self.MaxLoss_Dev_Active = True
            self.nb_hands[10] = self.nb_hands[9] #mark hand

        elif self.MaxLoss_Dev_Active == True:
            if  self.Player_Bank >=  self.Player_Bank_byhand[self.nb_hands[10]] + MAXLOSS_DEV_OFF:
                self.Bet_Multiplier = 1
                self.MaxLoss_Dev_Active = False
                self.nb_hands[10] = self.nb_hands[9]
                print('HM BM SET BACK TO  1 - Hand',self.nb_hands[9],'\n')
                
        #blockPrint()
    
    def set_HCM(self,cc): # High Count (Tier3) Bet Multiplier Factor
        
        if cc >= COUNT_TIER[1]: # when count is very high
            self.Progressive_Streak = WIN_STREAK[2]
            if cc >= COUNT_TIER[2]: self.HC_Multiple = CC_HC_MULTIPLIER
        elif cc <= COUNT_TIER[1] *-1:
            self.Progressive_Streak = WIN_STREAK[0]
            self.HC_Multiple = 1
        else:
            self.Progressive_Streak = WIN_STREAK[1] # default value
            self.HC_Multiple = 1
    
    def bet_min(self,pl):
        self.Bet_Curr[pl] = BET_MINIMUM
        self.Bet_Streak[pl] = 0
        
    def set_bets(self,n_win,s_status,pl_num,arg_cc,arg_tc): #sets bets (bet_curr) for next hand | counts streaks
        #setBM and HCM must be in this function otherwise the hands9,10 are out of sync 
        self.set_BM() # SET Bet Multiple / Set BET_MULTIPLIER_FACTOR (used in set_cc_wager())
        self.set_HCM(arg_tc) # set High Count Bet Multiple (used in CC wager)
        cnt, l_cnt,w_cnt =0,0,0
        
        #////////////////////////// WIN HAND \\\\\\\\\\\\\\\\\\\\\\\
        if n_win > 0: # net winner - adjust bet
            self.Bet_Streak[pl_num] +=1
            self.W_Streak[pl_num] +=1
            if self.W_Streak[pl_num] == 5: self.streaks.W5hnd.append(self.nb_hands[9])
            l_cnt = self.L_Streak[pl_num]
            
            if l_cnt >= LOSS_STREAK: #TODO LOSS_STREAK
                self.Bet_Curr[pl_num] += BET_INCREMENT
            elif self.use212 and self.W_Streak[pl_num] == 1:
                self.Bet_Curr[pl_num] = BET_MINIMUM * 0.5 #(2nd hand bet 50%)
            
            elif self.W_Streak[pl_num] > MAX_WIN_STREAK:
                self.bet_min(pl_num)
            # ///////////\\\\\\\\\\\ #
            # ////  WIN STREAKS \\\\ #                
            elif self.Bet_Streak[pl_num] < self.Progressive_Streak: #TODO Possible BUG if WIN_STREAK_RESET = true
                if WIN_STREAK_RESET == False and self.W_Streak[pl_num] >= self.Progressive_Streak: # additional wins after a completed streak will BET MIN
                    self.bet_min(pl_num)
                else: # WSR = TRUE OR streak < .prog_streak | keep pressing
                    self.Bet_Curr[pl_num] += BET_INCREMENT

            elif self.Bet_Streak[pl_num] >= self.Progressive_Streak: 
                cnt = self.Bet_Streak[pl_num]
                self.streaks.CT_Streak[cnt] +=1 #count ct_winstreaks                 
                self.bet_min(pl_num)
                
            if l_cnt > 0: 
                if l_cnt > len(self.streaks.L_Streak) - 1:
                    self.streaks.L_Streak.append(1)
                else:
                    self.streaks.L_Streak[l_cnt] +=1
            self.L_Streak[pl_num] = 0
            
        #////////////////////////// LOSE HAND \\\\\\\\\\\\\\\\\\\\\\\
        elif n_win < 0: #loser - reset bets
            self.L_Streak[pl_num] +=1
            l_cnt = self.L_Streak[pl_num]
            w_cnt = self.W_Streak[pl_num]
            cnt = self.Bet_Streak[pl_num]
            if self.L_Streak[pl_num] == 7: self.streaks.L7hnd.append(self.nb_hands[9])

            if l_cnt >= LOSS_STREAK and l_cnt < MAX_LOSS_STREAK:
                self.Bet_Curr[pl_num] = BET_MINIMUM #TODO LOSS_STREAK
            elif l_cnt < LOSS_STREAK:
                self.Bet_Curr[pl_num] = BET_MINIMUM
            elif l_cnt >= MAX_LOSS_STREAK:
                self.Bet_Curr[pl_num] = BET_MINIMUM #TODO LOSS_STREAK
            
            if cnt > 0: self.streaks.CT_Streak[cnt] +=1
            if w_cnt > 0:
                self.streaks.W_Streak[w_cnt] +=1 
                if w_cnt == 4:
                    self.streaks.L5ct += 1 # of 5th hand losses after winning 4
                    self.streaks.L5hnd.append(self.nb_hands[9])
            self.W_Streak[pl_num] = 0
            self.Bet_Streak[pl_num] = 0
            
        #else: # << PUSH - do nothing >>
    
    def SetPlStp(self): #sets a trailing profit mark (stop) to Walk_away if <=
        
        if (self.Player_Bank - BANK_START) >= WALK_AWAY_TRIGGER:
            if TRAILING_STOP > 0:
                self.Player_Stop = (game.Player_Bank_Max[0] - BANK_START) * TRAILING_STOP
                self.Player_Stop += BANK_START
            
        return self.Player_Stop
    
    
    def get_lossPC(self,pl_num): #returns % of lost hands by Player
        Hloss = self.loss[pl_num]
        Hhands = self.get_hands_played(pl_num)
        return  mBJF.zero_div(Hloss,Hhands,2)
        
    def get_expected_loss(self):
        return (EXPECTED_LOSS_RATE / 100 * -1) * self.get_bet()
        
    def get_hands_played(self,pl_num):
        return self.hands_played_pl[pl_num]

    def get_wins(self,pl_num):
        return self.wins[pl_num]

    def get_loss(self,pl_num):
        return self.loss[pl_num]

    def get_money(self):
        return self.profitloss

    def get_plbyplayer(self,pl):
        return self.PlayerPL[pl]
    
    def get_bet(self):
        return self.bet
    
    def get_Bet_Multiplier(self):
        return self.Bet_Multiplier
        
    def Reset_Bets(self):
        cnt, l_cnt,w_cnt =0,0,0
        if RESET_BETS:
            # populate streak lists for last streak at end of shoe before reset
            for pl_num in range(1,self.num_plhands+1):
                l_cnt = self.L_Streak[pl_num]
                w_cnt = self.W_Streak[pl_num]
                cnt = self.Bet_Streak[pl_num]
                if cnt > 0: self.streaks.CT_Streak[cnt] +=1 #count ct_winstreaks
                if w_cnt > 0: self.streaks.W_Streak[w_cnt] +=1
                if l_cnt > 0: 
                    if l_cnt > len(self.streaks.L_Streak) - 1:
                        self.streaks.L_Streak.append(1)
                    else:
                        self.streaks.L_Streak[l_cnt] +=1
            #reset
            self.Bet_Curr = [0]
            self.Bet_Streak = [0]
            self.L_Streak = [0]
            self.W_Streak = [0]
            self.Bet_Multiplier = 1
            self.HC_Multiple = 1
            for x in range(1,self.num_plhands+1):
                self.Bet_Curr.append(BET_MINIMUM)
                self.Bet_Streak.append(0)
                self.L_Streak.append(0)
                self.W_Streak.append(0)
            

#////////////////////////////////////\\\\\\\\\\\\\\\\\\\\
#////////////////// END GAME CLASS \\\\\\\\\\\\\\\\\\\\\\
#////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

#>>> MASTER Class <<<
class Master(object):
    """
    master tracks all metrics over all simulations
    """
    def __init__(self):

        self.Range_WL =[] #PL Range
        self.Loss_Max= [] # Max Loss / game
        self.UpWaves=[] # Tracks Up and Down waves in Player_Bank when height is > HH
        self.DwnWaves=[]
        self.PL_byPlayer = [0]
        for x in range(1,NO_HANDS +1):
            self.PL_byPlayer.append(0)
        self.tot_hands = 0 # accross all simulations
        
        #Walk Away
        self.wa_stats = mBJF.list2_Dim(SIMULATIONS, 6) #row = sim# | COLS 0 True/Flase | 1 Reason | 2 Round | 3 Hand | 4 Bank | 5 Printed true/false
        self.wa_ct_reason = [0,0,0,0,0]
        
        #Custom tracker module
        self.tracker = Tracker(NO_HANDS)

    def raise_tracker_newhand(self,rw,pl):
        # raises event in tracker object to store metrics for custom tracking on every unique hand inc splits
        self.tracker.on_new_hand(rw,game,self.tot_hands + game.nb_hands[9],pl)

    def raise_tracker_handcompleted(self,subhands,pl,winnet):
        # fires when all player hands are completed
        self.tracker.on_hand_completed(game,subhands,pl,winnet)

def plotcharts(mny,cnting):
    mny = sorted(mny)
#TODO
#   fit = stats.norm.pdf(mny, np.mean(mny), np.std(mny))  
#   pl.plot(mny, fit, '-o')
#   #pl.hist(mny, normal=True)
#   pl.hist(mny, )
#   pl.show()
#   
#   plt.ylabel('count')
#   plt.plot(cnting, label='x')
#   plt.legend()
#   plt.show()


def print_stats():
    
    #//// PERCENTAGES Win/Loss/etc \\\\
    PC_win = game.nb_hands[1]/game.nb_hands[9]*100
    PC_lose = game.nb_hands[2]/game.nb_hands[9]*100
    PC_push = game.nb_hands[3]/game.nb_hands[9]*100
    PC_bust = game.nb_hands[4]/game.nb_hands[9]*100
    PC_bj = game.nb_hands[5]/game.nb_hands[9]*100
    PC_surr = game.nb_hands[6]/game.nb_hands[9]*100
    
    total_bet = game.get_bet()# sum of all bets placed
    total_pl = game.get_money() # sum of pl all shoes
    #///  EDGE FORMULAS \\\
    #////////////\\\\\\\\\\
    H_GPH = (game.nb_hands[2] + (game.nb_hands[6] * 0.5) + game.nb_hands[8]) - (game.nb_hands[1] + (game.nb_hands[5] *0.5) + game.nb_hands[7]) # EDGE/GPH assumes flat bet
    PC_H_GPH = round(H_GPH / game.nb_hands[9] * 100,3)
    A_GPH = round(total_pl / game.nb_hands[9],3)
    WinBet = round(total_pl/total_bet * 100,3)
    Avg_Bet = round(total_bet/game.nb_hands[9],2) #avg bet per player hand - switch to game.nb_hands[0] to get by round
    Theo_PL = round(H_GPH * Avg_Bet * -1 ,2) # 
    Cas_Theo_PL =  game.get_expected_loss()  #(EXPECTED_LOSS_RATE / 100 * -1) * Avg_Bet * game.nb_hands[9] 
    WinRate = round(A_GPH * Avg_Bet / 100,3)
    
    print("PnL: $ {} -- FINAL Bank: {}".format("{0:.2f}".format(total_pl),"{0:.2f}".format(game.Player_Bank)))
    print("Max Bank: $%d at %d | Min Bank: $%d at %d" % (game.Player_Bank_Max[0],game.Player_Bank_Max[1],game.Player_Bank_Min[0],game.Player_Bank_Min[1]))
    print("Range: $%d | Max Loss: $%d" % (master.Range_WL[s_num],master.Loss_Max[s_num]))
    print("Avg bet/hnd: %0.2f  Total bets: %0.2f" % (Avg_Bet,total_bet))
    
    print ("\nHouse Edge: %s" % ("{0:.3f}".format(PC_H_GPH))) # House EDGE = (W + BJ*.5 + DBLWIN) - (L + SUR*.5 + DBLLOSS) / NBHANDS(9) - EDGE/GPH assumes flat bet
    print ("Actual Edge: %s" % ("{0:.3f}".format(A_GPH))) # Players (actual) Edge or GainPerHand (GPH) = PL / NBHANDS(9)
    print ("Win Rate: %s" % ("{0:.3f}".format(WinRate))) # Win Rate[expected]  = Actual Played Cards EDGE * avg bet
    print ("win/bet = {} %)".format( "{0:.3f}".format(WinBet))) # Win bet = PL / total bet (sum of all bets)
    print ("Theo PnL: $ %s" % ("{0:.2f}".format(Theo_PL))) # House EDGE * AVGBet
    print ("Casino Exp Loss: $ %s" % ("{0:.2f}".format(Cas_Theo_PL))) # EXPECTED_LOSS_RATE % * avg beet * NBHANDS(9)
    
    if not DETAIL_SUMMARY: blockPrint()

    if PLAY_FROM_FILE == 0:
        inc = game.shoe.shoe_penetration_inv() # % played of final shoe
        tot_round_avg = round(game.nb_hands[0] / (shoe_num+inc),2)
        print ("\nSummary: %d Rounds, %0.2f Rounds /Shoe Avg" % (game.nb_hands[0], tot_round_avg)) 
        print (" Total Hands: %d, %d Cards /Round Avg" % (game.nb_hands[9], round(game.cards_played / tot_round_avg / (shoe_num+inc),1))) 
        print("\nWinn: %s %s \nLose: %s %s %s \nSurr: %s %s \nPush: %s %s" % ("{0}".format(game.nb_hands[1]),"{0:.2f}".format(PC_win), "{0}".format(game.nb_hands[2]),"{0:.2f}".format(PC_lose),"{0:.2f}".format(PC_lose+PC_surr),"{0}".format(game.nb_hands[6]),"{0:.2f}".format(PC_surr),"{0}".format(game.nb_hands[3]),"{0:.2f}".format(PC_push)))
        print("Bust: %s %s \nBJ: %s %s" % ("{0}".format(game.nb_hands[4]),"{0:.2f}".format(PC_bust), "{0}".format(game.nb_hands[5]),"{0:.2f}".format(PC_bj)))
    
    #////////////// STREAKS \\\\\\\\\\\\\\
    lsLen = len(game.streaks.L_Streak)-1
    wsLen = len(game.streaks.W_Streak)-1
    sevL_Streak =0
    elevL_Streak = 0
    for s in range(7,lsLen): #7Plus Losing Streaks
        sevL_Streak += game.streaks.L_Streak[s]
    for s in range(15,lsLen): #15Plus Losing Streaks
        elevL_Streak += game.streaks.L_Streak[s]
    S15L = str(game.streaks.L_Streak[11:15]) + "," + str(elevL_Streak) + "+" #string to log all loss streaks 11-15+
    S15L = mBJF.Rep_All(S15L, ',','-')
    print("\nCT-Streaks :", game.streaks.CT_Streak[1:7]) #CT = Count Streaks / Progressive Streaks

    if len(game.streaks.W5hnd) <= 20 and len(game.streaks.W5hnd) > 0: print("W5 Hand #'s", game.streaks.W5hnd)
    ldiff, diff, sdev = mBJF.GetListDiff(game.streaks.W5hnd)
    print("W5Hands--Mean/Game:",mBJF.zero_div(game.nb_hands[9],game.streaks.CT_Streak[5],0) , "Mean Difference:", diff , "STDev:", sdev, "(", sdev+diff,"/", (sdev*2)+diff,")")
    print("Lost 5th Hand:", game.streaks.L5ct) #lost 5th hand after winning 4
    if len(game.streaks.L5hnd) <= 10 and len(game.streaks.L5hnd) > 0: print("L5 Hand #'s", game.streaks.L5hnd)
    print("W-Streaks :", game.streaks.W_Streak[1:wsLen]) # W streaks are different than Progressive/CT streaks which are used to determine bet size
    print("L-Streaks :", game.streaks.L_Streak[1:lsLen])
    print("7+L-Streaks :", sevL_Streak, " | 11+L-Streaks :", S15L)
    if len(game.streaks.L7hnd) > 0: print("L7 Hand #'s", game.streaks.L7hnd)
    
    #////////////// PlayerBank UP/DOWN WAVES \\\\\\\\\\\\\\
    arPeaks, arTroughs,blChk = mPT.getPeaksTroughs(game.Player_Bank_byhand,HH)
    if blChk == True:
        arUPS, arDOWNS = mPT.getDistance(arPeaks,arTroughs)
        if len(arUPS) == 0: arUPS.append(1)
        if len(arDOWNS) == 0: arDOWNS.append(1)
        UPS_Mean = round(np.mean(arUPS),2)
        UPS_Sdev = round(np.std(arUPS),2)
        DOWNS_Mean = round(np.mean(arDOWNS),2)
        DOWNS_SDev = round(np.std(arDOWNS),2)
        master.UpWaves.extend(arUPS)
        master.DwnWaves.extend(arDOWNS)
    else:
        UPS_Mean =0
        UPS_Sdev=0
        DOWNS_Mean =0
        DOWNS_SDev =0
        
    if len(arPeaks) < 15 and blChk == True:
        print("Peaks :", arPeaks)
        print("Troughs :",arTroughs)
        print("Ups :", arUPS)
        print("Downs :", arDOWNS)

    #////////////// WALKAWAYs \\\\\\\\\\\\\\
    strWkawy = str(master.wa_stats[s_num][0]) + ":" +str(master.wa_stats[s_num][1]) +  " | " + str(master.wa_stats[s_num][4]) # True/Fase, reason, bank
    wa_PL = master.wa_stats[s_num][4] - BANK_START
    
    strID = str(mID) + "." + str(s_num)
    if PLAY_FROM_FILE == 1: strID = str(s_num)
    if CSV_SUMMARY == 1:
        csv_sum_write(strID,PC_H_GPH,master.Range_WL[s_num],game.Player_Bank_Min[0],game.Player_Bank_Max[0],total_pl,master.Loss_Max[s_num],BET_MINIMUM,BET_INCREMENT,WIN_STREAK,SHOES,strWkawy,master.wa_stats[s_num][1])
        
    if DB_ENABLE ==1:
        sLst = [str(mID),str(s_num), DBstr(strWkawy),str(total_pl),str(master.Range_WL[s_num]),str(game.Player_Bank_Min[0]),str(game.Player_Bank_Max[0]),str(master.Loss_Max[s_num]),str(Avg_Bet),str(PC_H_GPH)]
        sLst.extend([str(UPS_Mean),str(UPS_Sdev),str(DOWNS_Mean),str(DOWNS_SDev),str(game.nb_hands[9]),str(game.nb_hands[1]),str(game.nb_hands[2]),str(game.nb_hands[6]),str(game.nb_hands[3]),str(game.nb_hands[4]),str(game.nb_hands[5]),str(game.nb_hands[7]),str(game.nb_hands[8]),str(game.streaks.CT_Streak[4]),str(game.streaks.CT_Streak[5]),str(game.streaks.L5ct), str(sevL_Streak),DBstr(S15L)])
        
        sql.ins_DB(sLst,"SIM_RESULTS")
        time.sleep(0.05) # sleep for 50ms to avoid DB thread errors/ lag - ie missing data
        sLst = [str(mID),str(s_num), str(Theo_PL),str(wa_PL), str(total_pl),str(PC_H_GPH),str(A_GPH),str(WinBet),str(WinRate)]
        sql.ins_DB(sLst,"SIM_STATS")

    enablePrint()
#////////////////// END PRINT STATS \\\\\\\\\\\\\\\\\\


def DBstr(st):
    strV = "'" + str(st) + "'"
    return strV

def GetBL_WA(PS,s_num):

    blWK = False
    if master.wa_stats[s_num][0] == False:
        if game.streaks.CT_Streak[WIN_STREAK[1]] >= WA_ON_STREAK and WA_ON_STREAK > 0:
            blWK = True
            reason = "WINSTREAK"
            master.wa_ct_reason[0] += 1
        elif game.Player_Bank >= (WALK_AWAY + BANK_START):
            blWK = True
            reason = "PROFIT"
            master.wa_ct_reason[1] += 1
        elif game.Player_Bank <= PS:
            blWK = True
            reason = "PROFIT:TS"
            master.wa_ct_reason[2] += 1
        elif game.Player_Bank >= GetWA():
            blWK = True
            reason = "CUTLOSS"
            master.wa_ct_reason[3] += 1
            enablePrint()
            print("Bank: %s    WA_CutLossTgt: %s" % (game.Player_Bank, game.Player_Bank_Min[0] + LOSS_STOP))
            if DEBUG_PRINT == 0: blockPrint()
        elif game.Player_Bank <= BANK_RUIN:
            blWK = True
            reason = "RUIN"
            master.wa_ct_reason[4] += 1

    if blWK == True:
        master.wa_stats[s_num][0] = True
        master.wa_stats[s_num][1] = reason
        master.wa_stats[s_num][2] = game.nb_hands[0] # round
        master.wa_stats[s_num][3] = game.nb_hands[9] # hand no
        master.wa_stats[s_num][4] = game.Player_Bank
        master.tracker.on_walkaway(master.wa_stats)
    return blWK

def GetWA(): #Get WALK AWAY Loss
    
    wal = 999999
    if LOSS_STOP > 0: # When Stop Loss Setting is enabled
        if game.Player_Bank_Min[0] <= BANK_START - LOSS_TRIGGER:
            wal = game.Player_Bank_Min[0] + LOSS_STOP    
            if wal > BANK_START:
                wal = BANK_START #once trigger hit Loss stop at EVEN
        elif game.Player_Bank_Min[0] <= BANK_START:
            wal = game.Player_Bank_Min[0] + LOSS_STOP #Gain Less than WA Amount

    return wal

#/////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\
#////////////////////// MAIN \\\\\\\\\\\\\\\\\\\\\\\
if __name__ == "__main__":
    master = Master() # master object tracks metrics over all simulations
    mID =0
    
    hc_importer = StrategyImporter(HC_STRATEGY_FILE)
    HC_HARD_STRATEGY, HC_SOFT_STRATEGY, HC_PAIR_STRATEGY = hc_importer.import_player_strategy()
    importer = StrategyImporter(STRATEGY_FILE)
    HARD_STRATEGY, SOFT_STRATEGY, PAIR_STRATEGY = importer.import_player_strategy()

    if DB_ENABLE == 1:
        mID = sql.get_MSTRID()
        str_mID = str(mID)
        strCT = str(COUNT_TIER) + " | " + str(BET_SPREAD)
        strCT = mBJF.Rep_All(strCT,',','-')
        strLoss = str(LOSS_STREAK)
        strLoss = mBJF.Rep_All(strLoss, ',', '-')
        strSimShoe = "[" + str(SIMULATIONS) + " - " + str(SHOES) + "]"
        
        sLst = [str_mID,str(BET_MINIMUM),str(BET_INCREMENT),DBstr(WIN_STREAK),DBstr(strSimShoe),str(NO_HANDS),DBstr(LOG_TAG),str(WALK_AWAY),str(BANK_START),DBstr(USE212),DBstr(USE_COUNT),DBstr(CC_RAISEBET),DBstr(strCT), DBstr(strLoss)]
        sql.ins_DB(sLst,"SIM_SETTINGS")
        
        if PLAY_FROM_FILE == 0: #when results saved to DB - Filename will set same MSTRID as in DB 
            OUTPUT_DETAILS_FILE =  "exports/" + str_mID.zfill(5) + "_BJ_DETAILS.csv"
        
    if CSV_DETAILS == 1:
        csv_detail_create() # create default output detail CSV file 

    if CSV_SUMMARY == 1:
        csv_sum_create() # create default summary file
    
    if PLAY_FROM_FILE == 1: #PlayRound
        #get each row 
        rList = np.array(csv_returnrows(PLAY_FILE_NAME))
        rLen = len(rList)
        nxt_rw = -1
        rw = 1
        fr_MID = int(PLAY_FROM_MID)
        max_sim = sql.get_MAXSIM(fr_MID)
        s_num_r = 0
        
        for s_num in range(max_sim+1):
            print ('\n%s SIMULATION no. %d %s' % (8 * '#', s_num + 1, 8 * '#'))
            Prv_shoe_num = 1 #Shoe/Game Number
            game = Game() # game object contains hand objects and tracks all metrics by player and by simulation 
            while (s_num_r == s_num):
                # #Each Row / Represents 1 hand
                if master.wa_stats[s_num][0] == True and WALK_AWAY_BREAK == True:
                    break
                shoe_num = int(rList[rw,1])
                if shoe_num > Prv_shoe_num:
                    Prv_shoe_num = shoe_num
                    game.Reset_Bets()
                
                debug_print_console()
                game.nb_hands[0] += 1 #Number of rounds
                if rw > nxt_rw:
                    nxt_rw = game.play_round_from_file(rw)
                
                bl_wa = GetBL_WA(game.SetPlStp(),s_num)

                rw +=1
                if rw >= rLen:
                    break
                s_num_r = int(rList[rw,0])
                
            #////////////////////////\\\\\\\\\\\\\\\\\\
            #>>>> while rw in rList LOOP END  >>>>              

            master.PL_byPlayer[0] += game.get_money() # pl all players
            for x in range(1,NO_HANDS +1):
                master.PL_byPlayer[x] += game.get_plbyplayer(x)

            master.Range_WL.append(game.Player_Bank_Max[0] - game.Player_Bank_Min[0])
            master.Loss_Max.append(BANK_START-game.Player_Bank_Min[0])
            
            enablePrint()
            if master.wa_stats[s_num][0]:
                print("   >>>> PLAYER WALKS AWAY: Round %d Hand %d  w/ Bank: %d  Reason: %s<<<<" % (master.wa_stats[s_num][2],master.wa_stats[s_num][3],master.wa_stats[s_num][4],master.wa_stats[s_num][1]))
                master.wa_stats[s_num][5] = True #PrintedtoConsole
            
            if master.wa_stats[s_num][0] == False: master.wa_stats[s_num][4] = game.Player_Bank # tracking WA banks PL
            master.tot_hands += game.nb_hands[9] #totaling all hands / game 
            print_stats()
            
    #>>>>>>>>>>>> PLAY_FROM_FILE = 0/FALSE <<<<<<<<<<<<<<
    else: #>>>>>>>>>>>>>> PLAY ROUND <<<<<<<<<<<<<<
        for s_num in range(SIMULATIONS):
            print ('\n%s SIMULATION no. %d %s' % (8 * '#', s_num + 1, 8 * '#'))
            game = Game() #game object contains hand objects and tracks all metrics by player and by simulation
            master.tracker.on_newgame()
            for shoe_num in range(SHOES): #Shoe # in each simulation
                game.shoe = Shoe(SHOE_SIZE)
                if shoe_num > 0: game.Reset_Bets()
                
                while not game.shoe.reshuffle:
                    debug_print_console()
                    game.nb_hands[0] += 1 #Number of rounds
                    game.play_round(s_num,shoe_num)

                    if GetBL_WA(game.SetPlStp(),s_num) == True:
                        if WALK_AWAY_BREAK == True: break # break while loop
                
                
                game.cards_played += game.shoe.shoe_cardsplayed()
                master.tracker.on_shuffle(game.cards_played)
                
                enablePrint()
                if master.wa_stats[s_num][0] and not master.wa_stats[s_num][5]:
                    print("   >>>> PLAYER WALKS AWAY: Round %d Hand %d  w/ Bank: %d  Reason: %s<<<<" % (master.wa_stats[s_num][2],master.wa_stats[s_num][3],master.wa_stats[s_num][4],master.wa_stats[s_num][1]))
                    master.wa_stats[s_num][5] = True #PrintedtoConsole
                    if WALK_AWAY_BREAK: break # break for loop
            #//////////////////\\\\\\\\\\\\\\
            #<<<< FOR NUM_SHOES LOOP END >>>>
    
            master.PL_byPlayer[0] += game.get_money() # pl all players / all simulations
            for x in range(1,NO_HANDS +1):
                master.PL_byPlayer[x] += game.get_plbyplayer(x) # by player / all simultations
                
            master.Range_WL.append(game.Player_Bank_Max[0] - game.Player_Bank_Min[0])
            master.Loss_Max.append(BANK_START-game.Player_Bank_Min[0])
            
            if master.wa_stats[s_num][0] == False: master.wa_stats[s_num][4] = game.Player_Bank # tracking WA banks PL when WA is false
            master.tot_hands += game.nb_hands[9] #totaling all hands / game 
            print_stats()
            
        #///////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        #<<<< END PLAY_ROUND / MAIN CODE  IF-ELSE PLAY FROM FILE |  >>>>
    
    
    #///////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    #<<<< END Loop  for number of simulations / for loop >>>>
    
    print("\n<<<SUMMARY OF %s SIMULATIONS>>>" % str(s_num +1))
    print("Total Hands :", master.tot_hands)
    if not DETAIL_SUMMARY:blockPrint()
    Range_Sdev1 = round(np.std(master.Range_WL),0)
    Range_Mean = round(np.mean(master.Range_WL),0)
    Loss_Sdev1 = round(np.std(master.Loss_Max),0)
    Loss_Mean = round(np.mean(master.Loss_Max),0)
    MUps_Mean = round(np.mean(master.UpWaves),0)
    MUps_Sdev1 = round(np.std(master.UpWaves),0)
    MDwn_Mean =round(np.mean(master.DwnWaves),0)
    MDwn_Sdev1 = round(np.std(master.DwnWaves),0)
    print("Range :",master.Range_WL)
    print("Range Mean :",Range_Mean)
    print("Range Sdev :",Range_Sdev1)
    print("Max Loss :",master.Loss_Max)
    print("MaxLoss Mean :",Loss_Mean)
    print("MaxLoss Sdev :",Loss_Sdev1)

    if len(master.UpWaves) < 15:
        print("Ups :", master.UpWaves)
        print("UpWave Mean :",MUps_Mean)
        print("UpWave Sdev :",MUps_Sdev1)
        
        print("Downs :", master.DwnWaves)
        print("DownWave Mean :",MDwn_Mean)
        print("DownWave Sdev :",MDwn_Sdev1)
    
    ct_walkawy = mBJF.count2d(True,master.wa_stats) / 2 # 'True'totals are double counted - div /2 for actual count
    tot_wa_pl = 0 # python makes user define this??
    for x in range(SIMULATIONS):
        tot_wa_pl += master.wa_stats[x][4] - BANK_START
    enablePrint()
    print("WalkAways: %s Reason:WinStreak %s, Profit %s, TrailStop %s, Cutloss %s, RUIN %s " % (ct_walkawy,master.wa_ct_reason[0],master.wa_ct_reason[1],master.wa_ct_reason[2],master.wa_ct_reason[3],master.wa_ct_reason[4] ))
    print("TotPL: $ %s  WA_PnL: $ %s " % ("{0:.2f}".format(master.PL_byPlayer[0]),"{0:.2f}".format(tot_wa_pl))) #PL from sims where player gets up (WalkAway) before total shoes reached
    
    master.tracker.end_simulation()

    st_walkawy = str(ct_walkawy) + ' | ' + str(master.wa_ct_reason[0]) + ' | ' + str(master.wa_ct_reason[1]) + ' | ' + str(master.wa_ct_reason[2]) + ' | ' + str(master.wa_ct_reason[3]) + ' | ' + str(master.wa_ct_reason[4])
    if DB_ENABLE == 1:
        sLst = [str(mID),str(s_num+1),str(master.tot_hands),str(Range_Mean),str(Range_Sdev1),str(Loss_Mean),str(Loss_Sdev1),str(MUps_Mean),str(MUps_Sdev1),str(MDwn_Mean),str(MDwn_Sdev1),DBstr(st_walkawy)]
        sql.ins_DB(sLst,"SIM_SUMMARY")
        time.sleep(0.3)
        sql.ins_STATSUMMARY(mID)
        

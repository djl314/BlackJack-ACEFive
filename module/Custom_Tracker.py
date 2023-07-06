#!/usr/bin/env python3

# Create Custom tracking/export metrics

import numpy as np


class Tracker(object):
	"""
	imports all metrics on every hand over all simulations
	"""
	def __init__(self,players):
		self.raw_row =[] # raw list data of each row in details export file
		self.obj_game =[] # game object from simulation
		self.int_status = 0 # status as int
		self.shoes = 0 #shoes over all games
		self.games = 0 #total games/simulations / holds current sim_num
		self.players = players #no of player_hands
		self.wa_stats = []
		
		#custom trackers
		self.consec_losses = ConsecutiveLosses(players)
		self.max_loss = Max_Loss()
		
		
	def on_new_hand(self,rRow,game_obj,hand_no,pl_num): #unique player hand and split hands
		self.raw_row = rRow
		self.game_obj = game_obj
		self.hands_count_allgames = hand_no #master hand counter all games | use game_obj nb_hands[9] for game hand # 
		
		self.set_int_status(rRow) 
	
		
	
	def on_hand_completed(self,game_obj,sub_hands,pl_num,net_win):
		self.game_obj = game_obj
	
		self.consec_losses.do_logic(self)
	
	def on_shuffle(self, crdsplyd):
		self.shoes +=1
		self.game_obj.cards_played = crdsplyd
		
		self.consec_losses.set_activeFALSE(self.players)
	
	def on_walkaway(self,WA_Stats):
		self.wa_stats = WA_Stats
	
	def on_newgame(self):
		self.games +=1
		
	def end_simulation(self):
		print ('\n%s CUSTOM TRACKERS %s' % (8 * '#', 8 * '#'))
		
		self.consec_losses.printstats(self)
		
	def set_int_status(self,rRow): #set Status of hand to integer
		status = rRow[5]
		if status == "LOST":
			self.int_status = 2
		elif status == "WON":
			self.int_status = 1
		elif status == "WON BJ":
			self.int_status = 5
		elif status == "SURRENDER":
			self.int_status = 6
		elif status == "PUSH":
			self.int_status = 3
		
		
	
#/////////////////\\\\\\\\\\\\\\\\\\\\\
# /////// CONSECUTIVE LOSSES \\\\\\\\\\
class ConsecutiveLosses(object):
	"""
	tracks statistics and probabilities when losing 7 or more hands in a row
	"""
	def __init__(self,players):		
		self.active = False
		self.no_loss_trigger = 7 # change value to number of consecutive losses to trigger count
		self.count = 0 # no times 7 or more losses were tracked
		
		#data by player number
		self.active_player = [False] 
		self.trigger_hand = [0]  #pl_num,hand 
		self.firstwin_hand =  [0] 
		
		#metrics to track
		self.next10_hands = np.empty((0,2),int) #pl_num,status (0rounds, 1win, 2loss, 3push, 4bust, 5bj, 6surr,7DBL_win,8DBL_loss,9hands_no,10 marked hand)
		self.next5_hands = np.empty((0,2),int)#np.append(self.hand,np.array([[0,0]]), axis =0)
		self.next10_afterwin = np.empty((0,2),int) #pl_num,status (0rounds, 1win, 2loss, 3push, 4bust, 5bj, 6surr,7DBL_win,8DBL_loss,9hands_no,10 marked hand)
		self.next5_afterwin = np.empty((0,2),int)


		for x in range(1,players+1):
			self.active_player.append([False])
			self.trigger_hand.append(0)
			self.firstwin_hand.append(0)
			#np.append(self.trigger_hand,np.array([[x,0]]), axis =0)
			
			
	def do_logic(self,trckr):
		players = trckr.players
		
		#TODO 
			
		
	def set_activeFALSE(self,players):
		self.active = False
		for x in range(1,players+1):
			self.active_player[x] = False


	def printstats(self,trckr):
		print ('\n%s CONSEC_LOSSES OUTPUT SUMMARY %s' % (8 * '#', 8 * '#'))

#/////////////////\\\\\\\\\\\\\\\\\\\\\
# ////////// MAX $$ LOSS \\\\\\\\\\\\\\
class Max_Loss(object):
	"""
	tracks bank and probabilities when absolute loss$ falls below standard deviation over fixed number of hands
	"""
	def __init__(self):		
		self.active = False


		
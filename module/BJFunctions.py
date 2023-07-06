#!/usr/bin/env python3
import numpy as np

def GetListDiff(ini_list): #returns the difference between each element in the list as a list plus the mean and STDdeviation
	n = len(ini_list)
	
	diff_list = []
	if n > 1:
		for x, y in zip(ini_list[0::], ini_list[1::]):
			diff_list.append(y-x)
	else:
		diff_list.append(0)
	
	list_SDev = round(np.std(diff_list),0)
	list_Mean = round(np.mean(diff_list),0)
	
	return diff_list, list_Mean, list_SDev


def Rep_All(st,ch1,rch): # replace char
# iterating over the string
	modified_str = ''
	for char in range(0, len(st)):
		# checking if the character at char index is equivalent to 'a'
		if(st[char] == ch1):
				# append $ to modified string
				modified_str += rch
		else:
				# append original string character
				modified_str += st[char]
			
	return modified_str

def zero_div(x, y,rnd): #divide by zero / no error
	try:
		return round(x / y,rnd)
	except ZeroDivisionError:
		return 0


def list2_Dim(rws,cls): #create 2 dimensional list
	
	lst = [[0 for i in range(cls)] for j in range(rws)] ##row = sim# | COLS 0 True/Flase | 1 Reason | 2 Round | 3 Hand | 4 Bank
	for i in range(rws):
		lst[i][0] = False # set default walk away to false on all rows
		lst[i][5] = False # set default PrintedtoConsole = false
	
	return lst

def count2d(char,list): # count items in 2 dimensional list
	return sum([i.count(char) for i in list])

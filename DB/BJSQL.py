#!/usr/bin/env python3

import sqlite3 as SQL

DB_PATH = 'DB/BJ_DATA.db'

#def DB_Connect():
#	
#	c = SQL.connect('BJ_DATA.db')
#	
#	return c
	
def ins_DB(arrData,strTable):
	
	con = SQL.connect(DB_PATH)
	cur = con.cursor()

	strText = (','.join(arrData))
	
	strInsert = "INSERT INTO " + strTable + " VALUES (" + strText +")"
	#print(strText)
	#print(strInsert)
	cur.execute(strInsert)
	con.commit()
	
	con.close()
	
def get_MSTRID():
	
	con = SQL.connect(DB_PATH)
	cur = con.cursor()
	
	strSelect ="SELECT MAX(MSTR_ID) FROM SIM_SETTINGS"
	cur.execute(strSelect)
	res = cur.fetchone()
	con.close()
	try:
		ret = int(res[0])
		return ret + 1 
	#except sqlite3.Error as error:
	except:
		return 1
	
	

def get_MAXSIM(mID): #when play from file is true returns # of simulations run
	
	con = SQL.connect(DB_PATH)
	cur = con.cursor()
	
	strSelect ="SELECT MAX(SIM_ID) FROM SIM_RESULTS where MSTR_ID = " + str(mID)
	cur.execute(strSelect)
	res = cur.fetchone()
	
	#print(res[0])
	ret = int(res[0])
	
	
	con.close()
	return ret

def ins_STATSUMMARY(mID):
	
	con = SQL.connect(DB_PATH)
	cur = con.cursor()
	
	strInsert = "insert into SIM_STAT_SUM select MSTR_ID, 9999, round(avg(PL_THEO),2) as plt,round(sum(PL_WA),2) as plsumwa, round(sum(PL),2) as plsum, round(avg(PL),2) as pl2,round(avg(H_EDGE),3) as he, round(avg(A_EDGE),3) as ae, round(avg(WinBet),3) as wb, round(avg(WinRate),3) as wr from SIM_STATS where MSTR_ID = " + str(mID) + " group by MSTR_ID"
	
	#print(strText)
	#print(strInsert)
	cur.execute(strInsert)
	con.commit()
	
	con.close()
	

def DBstr(st):
	strV = "'" + str(st) + "'"
	return strV



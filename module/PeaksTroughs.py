#

# Function that returns true if num is
# greater than both arr[prv] and arr[nxt]
def isPeak(arr, n, cVal, prv, nxt,h,cTrough):
	
	rBool = True
	# If num is smaller than the element
	# on the left (if exists)
	if (prv >= 0 and arr[prv] > cVal):
		rBool= False

	# If num is smaller than the element
	# on the right (if exists)
	if (nxt < n and arr[nxt] > cVal):
		rBool = False
		
	if (rBool and cVal >= (cTrough + h)): 
		rBool = True
	else:	
		rBool = False
	
	return rBool

# Function that returns true if num is
# smaller than both arr[prv] and arr[nxt]
def isTrough(arr, n, cVal, prv, nxt,h,cPeak):
	
	rBool = True
	# If num is greater than the element
	# on the left (if exists)
	if (prv >= 0 and arr[prv] < cVal):
		rBool = False

	# If num is greater than the element
	# on the right (if exists)
	if (nxt < n and arr[nxt] < cVal):
		rBool = False
	
	if (rBool and cVal <= (cPeak - h)): 
		rBool = True
	else:	
		rBool = False
			
	return rBool

# List / Height
def getPeaksTroughs(arr,h):
	arPeaks =[]
	arTroughs =[]
	cPeak = 0
	cTrough = 0
	lstPT = 0
	n = len(arr)
	# For every element
	for i in range(n):

		# If the current element is a peak
		if (isPeak(arr, n, arr[i], i - 1, i + 1,h,cTrough)):
			if lstPT != 7:
				cPeak = arr[i]
				arPeaks.append(cPeak)
				lstPT =7
			else:
				if arr[i] > cPeak:
					cPeak = arr[i]
					x = len(arPeaks)
					arPeaks[x-1] = cPeak

		if (isTrough(arr, n, arr[i], i - 1, i + 1,h,cPeak)):
			if lstPT != 2:
				cTrough = arr[i]
				arTroughs.append(cTrough)
				lstPT = 2
			else:
				if arr[i] < cTrough:
					cTrough = arr[i]
					x = len(arTroughs)
					arTroughs[x-1] = cTrough
	
	if len(arPeaks) > 0 and len(arTroughs) > 0:
		return arPeaks,arTroughs, True
	else:
		return arPeaks,arTroughs, False

def getDistance (aPks,aTro):
	arPk2Tr =[]
	arTr2Pk =[]
	
	p = len(aPks) -1
	t = len(aTro) -1
	
	c = 0
	while c <= t:
		arPk2Tr.append((aPks[c]-aTro[c])*-1)
		c+=1
	
	c = 0
	while c < p:
		arTr2Pk.append(aPks[c+1] - aTro[c])
		c+=1
	
	return arTr2Pk,arPk2Tr
# Driver code
#arr = [1,2,9,4,8,5,10,11,15,5, 10, 5, 7, 4, 3, 5,2,1,10,20,15,9,8,5,10,13]
#print(arr)
#arPeaks, arTroughs = getPeaksTroughs(arr,8)
#arp,art = getDistance(arPeaks,arTroughs)
#
#print("Peaks : ", end = "")
#print(arPeaks)
#print("Troughs : ", end = "")
#print(arTroughs)
#
#print("Ups : ", end = "")
#print(art)
#print("Downs : ", end = "")
#print(arp)
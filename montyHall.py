#!/usr/bin/env python

#############################
# Monty Hall Test Program	#
# Author: Paul Salminen		#
# Date: 11/12/2015			#
#############################

import random

total = 1000000
fWins = 0
sWins = 0

for x in range(total):
	answer = random.randint(0,2)
	fGuess = random.randint(0,2)
	clue = [i for i in [0,1,2] if i!=fGuess and i!=answer][0]
	sGuess = [i for i in [0,1,2] if i!=fGuess and i!=clue][0]
	
	if fGuess == answer:
		fWins+=1
	elif sGuess == answer:
		sWins += 1
	else:
		print("Error!")

print 'First Guess: %.2f%% \nSecond Guess: %.2f%%' % ((float(fWins)*100 / float(total)), (float(sWins)*100 / float(total)))

#!/usr/bin/env python3
""" Monty Hall Test Program
Author: Paul Salminen
Date: 11/12/2015
"""

import random


def run():
    total = 1000000
    fWins = 0
    sWins = 0
    opts = [0, 1, 2]

    for _ in range(total):
        answer = random.randint(0, 2)
        fGuess = random.randint(0, 2)
        clue = [i for i in opts if i != fGuess and i != answer][0]
        sGuess = [i for i in opts if i != fGuess and i != clue][0]

        if fGuess == answer:
            fWins += 1
        elif sGuess == answer:
            sWins += 1
        else:
            print("Error!")

    first_guess = float(fWins) * 100 / float(total)
    second_guess = float(sWins) * 100 / float(total)

    print((f'First Guess: {first_guess:.2f}% '
           f'\nSecond Guess: {second_guess:.2f}%'))


if __name__ == '__main__':
    run()

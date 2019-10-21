#!/usr/bin/python
import enum
import json
import numpy as np
import os
import pandas as pd
import pickle

class Game(enum.Enum):
    WelcomeState = "welcome"
    TastingState = "tasting"
    AuditState = "audit"
    WinLoseState = "winLose"

if os.path.isfile('wine.pickle'):
    data = pickle.load( open( 'wine.pickle', 'rb') )
    
print("TieW {}\nTieL {}\nloser to winner {}\nwines low to high {}\n".format(data['tie']['winner'], data['tie']['loser'], data['winnernames'], data['winnerwines']))
print("LoveHate: {}\nConsistent: {}\n".format(data['scores'].std().idxmax(), data['scores'].std().idxmin()))
print('Good Buddies: {}\n'.format(data['good_buddies']))
print('Bad Buddies: {}\n'.format(data['bad_buddies']))
print('Wine Progress: {}\n'.format(data['wineprogress']))
print('Buddies (lower means closer to same scoring of wines: \n{}\n'.format(data['buddies']))
print('Personal Wine Score: \n{}\n'.format(data['mywinescore']))
print('All Scores: \n{}\n'.format(data['scores']))
print('Wine Names: \n{}\n'.format(data['winenames']))
print('bearernames: \n{}\n'.format(data['bearernames']))
print('Bottles and who brought: \n{}\n'.format(data['bottletoname']))
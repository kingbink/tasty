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
    
    s = json.loads(data['scores'].to_json(orient='index'))
    new_s = {}
    for name in s:
        new_s[name] = {}
        cnt = 0
        for wine in s[name]:
            if wine in data['bottletoname']:
                new_s[name][data['winenames'][wine]] = {'rating': str(s[name][wine])}
                if data['bottletoname'][data['winenames'][wine]] == name:
                    new_s[name][data['winenames'][wine]]['brought'] = 'I brought this'
                if data['myguess'][name] == cnt:
                    new_s[name][data['winenames'][wine]]['guessed'] = 'My guess'
                cnt += 1
    print('Bottles and who brought: \n{}\n'.format(json.dumps(data['bottletoname'], indent=4)))
    print(json.dumps(new_s, indent=4))

    print("TieW {}\nTieL {}\nloser to winner {}\nwines low to high {}\n".format(data['tie']['winner'], data['tie']['loser'], data['winnernames'], data['winnerwines']))
    print('Good Buddies: {}\n'.format(json.dumps(data['good_buddies'],indent=4)))
    print('Bad Buddies: {}\n'.format(json.dumps(data['bad_buddies'], indent=4)))
    if 'buddies' in data:
        print('Buddies (lower means closer to same scoring of wines: \n{}\n'.format(data['buddies']))
    # print('Personal Wine Score: \n{}\n'.format(data['mywinescore']))
    print('All Scores: \n{}\n'.format(data['scores']))
    print('Wine Names: \n{}\n'.format(data['winenames']))
    print('bearernames: \n{}\n'.format(data['bearernames']))
    if 'myguess' in data:
        print('My Guess: \n{}\n'.format(data['myguess']))

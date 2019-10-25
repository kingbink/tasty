#!/usr/bin/python
import enum
import json
import numpy as np
import os
import pandas as pd
import pickle
from collections import OrderedDict

class Game(enum.Enum):
    WelcomeState = "welcome"
    TastingState = "tasting"
    AuditState = "audit"
    WinLoseState = "winLose"

if os.path.isfile('wine.pickle'):
    data = pickle.load( open( 'wine.pickle', 'rb') )
    
    s = json.loads(data['scores'].to_json(orient='index'))
    #print(s)
    new_s = OrderedDict()
    for name in s:
        new_s[name] = OrderedDict()
        cnt = 0
        #print(s[name])
        for w in range(len(s[name])):
            if data['winenames'][w] == '???':
                new_s[name][data['winenames'].index[w]] = {'rating': str(s[name][data['winenames'].index[w]])}
                if data['myguess'][name] == cnt:
                    new_s[name][data['winenames'].index[w]]['guessed'] = 'My Guess'
                if cnt in data['notes'][name]:
                    new_s[name][data['winenames'].index[w]]['notes'] = data['notes'][name][cnt]
            else:
                new_s[name][data['winenames'][w]] = {'rating': str(s[name][data['winenames'].index[w]])}
                if data['bottletoname'][data['winenames'][w]] == name:
                    new_s[name][data['winenames'][w]]['brought'] = 'I brought this'
                if data['myguess'][name] == cnt:
                    new_s[name][data['winenames'][w]]['guessed'] = 'My Guess'
                if cnt in data['notes'][name]:
                    new_s[name][data['winenames'][w]]['notes'] = data['notes'][name][cnt]
            cnt += 1
            #print(json.dumps(new_s, indent=4))
        
            # if w in data['bottletoname']:
            #     new_s[name][data['winenames'][w]] = {'rating': str(s[name][w])}
                # if data['bottletoname'][data['winenames'][wine]] == name:
                #     new_s[name][data['winenames'][wine]]['brought'] = 'I brought this'
                # if data['myguess'][name] == cnt:
                    # new_s[name][data['winenames'][wine]]['guessed'] = 'My guess'
    print('Bottles and who brought: \n{}\n'.format(json.dumps(data['bottletoname'], indent=4)))
    # 
    # print("TieW {}\nTieL {}\nloser to winner {}\nwines low to high {}\n".format(data['tie']['winner'], data['tie']['loser'], data['winnernames'], data['winnerwines']))
    # print('Good Buddies: {}\n'.format(json.dumps(data['good_buddies'],indent=4)))
    # print('Bad Buddies: {}\n'.format(json.dumps(data['bad_buddies'], indent=4)))
    # if 'buddies' in data:
    #     print('Buddies (lower means closer to same scoring of wines: \n{}\n'.format(data['buddies']))
    # # print('Personal Wine Score: \n{}\n'.format(data['mywinescore']))
    print('All Scores: \n{}\n'.format(data['scores']))
    print('Wine Names: \n{}\n'.format(data['winenames']))
    print('bearernames: \n{}\n'.format(data['bearernames']))
    # if 'myguess' in data:
    #     print('My Guess: \n{}\n'.format(data['myguess']))
    print('all notes: \n{}\n'.format(data['notes']))
    print('Personalized output \n{}\n'.format(json.dumps(new_s, indent=4)))

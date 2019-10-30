#!/usr/bin/python
import argparse
import json
import numpy as np
import os
import pandas as pd
import pickle
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument('--name', '-n', help='Name of person to print summary about')
args = parser.parse_args()

sum_name = None
if args.name:
    sum_name = args.name.upper()

if os.path.isfile('wine.pickle'):
    data = pickle.load( open( 'wine.pickle', 'rb') )
    
    s = json.loads(data['scores'].to_json(orient='index'))
    #print(s)
    new_s = OrderedDict()
    for name in s:
        if name == sum_name or sum_name == None:
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
    
    w = data['scores'].sum().sort_values().index[::-1]
    new_w = OrderedDict()
    previous_score = 0
    previous_name = ''
    for wine in w:
        name = data['winenames'][wine]
        score = data['scores'].sum()[wine]
        new_w[name] = OrderedDict()
        new_w[name]['score'] = score
        new_w[name]['brought_by'] = data['bearernames'][wine]
        if score == previous_score:
            new_w[name]['tie'] = new_w[previous_name]['tie'] = True
        previous_name = name
        previous_score = score
    print('All Wines\n{}\n'.format(json.dumps(new_w, indent=4)))
    #print('Bottles and who brought: \n{}\n'.format(json.dumps(data['bottletoname'], indent=4)))
    # 
    # print("TieW {}\nTieL {}\nloser to winner {}\nwines low to high {}\n".format(data['tie']['winner'], data['tie']['loser'], data['winnernames'], data['winnerwines']))
    # print('Good Buddies: {}\n'.format(json.dumps(data['good_buddies'],indent=4)))
    # print('Bad Buddies: {}\n'.format(json.dumps(data['bad_buddies'], indent=4)))
    # if 'buddies' in data:
    #     print('Buddies (lower means closer to same scoring of wines: \n{}\n'.format(data['buddies']))
    # # print('Personal Wine Score: \n{}\n'.format(data['mywinescore']))
    
    if sum_name == None:
        print('All Scores: \n{}\n'.format(data['scores']))
        print('Wine Names: \n{}\n'.format(data['winenames']))
        print('bearernames: \n{}\n'.format(data['bearernames']))
        # if 'myguess' in data:
        #     print('My Guess: \n{}\n'.format(data['myguess']))
        print('all notes: \n{}\n'.format(data['notes']))
    print('Personal Output \n{}\n'.format(json.dumps(new_s, indent=4)))

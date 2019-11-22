#!/usr/bin/python
import argparse
import datetime
import json
import numpy as np
import os
import pandas as pd
import pickle
import re
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument('--name', '-n', help='Name of person to delete (BE CAREFUL')
args = parser.parse_args()

del_name = None
if args.name:
    del_name = args.name.upper()
    
# Make a backup first
now = datetime.datetime.now()
ts = now.strftime('%Y%m%d%H%M%S')
os.system('cp wine.pickle wine_backup_{}.pickle'.format(ts))

if os.path.isfile('wine.pickle'):
    data = pickle.load( open( 'wine.pickle', 'rb') )
    # Delete the del_name
    # scores
    data['scores'] = data['scores'].drop([del_name])
    # myguess
    del data['myguess'][del_name]
    # myreal
    del data['myreal'][del_name]
    # bearernames
    # winenames?
    c = 0
    for n in data['bearernames'].values:
        if n == del_name:
            data['bearernames'][c] = '???'
            data['winenames'][c] = '???'
        c += 1
    # notes[name]
    del data['notes'][del_name]
    # donelist
    data['donelist'] = data['donelist'].drop([del_name])
    # bottletoname
    for b,n in data['bottletoname'].items():
        if n == del_name:
            del data['bottletoname'][b]
    # save new pickle
    pickle.dump( data, open( 'wine.pickle', 'wb' ) )
    
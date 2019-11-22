# import copy
#import enum
import logging
logging.basicConfig(filename='tasty.log',
                    format='%(asctime)s - %(process)d-%(levelname)s - %(message)s',
                    level=logging.WARNING)

from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField, IntegerField, SubmitField
import json
from collections import OrderedDict
import numpy as np
import os
import pandas as pd
import pickle
import random
import re
# import tabulate
from wtforms.validators import InputRequired, Length, AnyOf



# import matplotlib as mpl
# mpl.use('Agg')

# import matplotlib.pyplot as plt
# plt.style.use('tableau-colorblind10')

# import socket
# import fcntl
# import struct
# 
# def get_ip_address(ifname):
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     return socket.inet_ntoa(fcntl.ioctl(
#         s.fileno(),
#         0x8915,  # SIOCGIFADDR
#         struct.pack('256s', ifname[:15])
#     )[20:24])
# 
# myip = get_ip_address('wifi0')

from settings import secret_key, bottles, email_address, email_password, rotatetime
# from game import Game
# game = Game()

from send_email import send_email

class ParticipantForm(FlaskForm):
    name = StringField('  Name  ',
                           validators=[InputRequired('A name is required!'),
                                       Length(min=2, max=40,
                                              message='Must be between 2 and 40 characters.')])
    bottle = StringField('  Bottle  ',
                           validators=[InputRequired('A bottle is required!'),
                                       Length(min=2, max=40,
                                              message='Must be between 2 and 40 characters.')])
    submit = SubmitField("  Enter  ")

    
# class MyBottleForm(FlaskForm):
#     name = StringField('name',
#                             validators=[InputRequired('A name is required!'),
#                                        Length(min=2, max=40,
#                                               message='Must be between 2 and 40 characters.')])
# 
# class Game(enum.Enum):
#     WelcomeState = "welcome"
#     TastingState = "tasting"
#     AuditState = "audit"
#     WinLoseState = "winLose"
    
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
socketio = SocketIO(app, async_mode=None)

data = {}
loaded_notes_list = ['This smells like cheese, but a seriously good cheese',
                     'What?!? Who brought this?',
                     'Yummy in my tummy!',
                     'Come on people!?!?, add some notes',
                     'Inconceivable',
                     "How about you, what's your favorite color?",
                     "Feeling Classy",
                     ]


@socketio.on('connect')
def connect():
    sendUpdate()

# Read in data if it's available
# Pickle is the best, wine.csv will need to build a few other keys based on csv input
# Last resort is fresh game, and build up everything by scratch
if os.path.isfile('wine.pickle'):
    logging.warning('Importing wine.pickle')
    data = pickle.load( open( 'wine.pickle', 'rb') )
# elif os.path.isfile('wine.csv'):
#     data['scores'] = pd.read_csv('wine.csv', index_col=0)
#     data['donelist'] = pd.Series(0, index=data['scores'].index)
#     data['bottles'] = len(data['scores'].columns)
#     if (len(data['scores'].index) >= 4):
#         # data['state'] = Game.TastingState
#         data['gamestate'] = "tasting"
#     else:
#         # data['state'] = Game.WelcomeState
#         data['gamestate'] = "welcome"
#     data['drinkwine'] = {'eatordrink': 'Drinking', 'boxorbottle': "Bottle", 'foodorbooze':'Wine'}
#     data['winenames'] = pd.Series('???', index=w)
#     data['bearernames'] = pd.Series('', index=data['scores'].columns)
else:
    # Create base scores, the rest gets built later
    logging.warning('Creating new data for new game')
    scores = pd.DataFrame(dtype=int)
    w = ['number #{}'.format(x+1) for x in range(bottles)]
    for col in w:
        scores[col] = pd.Series([], dtype=int)

    # Save in big dict
    data['scores'] = scores
    data['donelist'] = pd.Series([], dtype=int)
    newd = pd.DataFrame([[0 for x in range(len(data['scores'].columns))]],
    columns=data['scores'].columns, index=['mrmagoo'])
    data['scores'] = data['scores'].append(newd)
    data['donelist']['mrmagoo'] = 0
    data['donelistjson'] = data['donelist'].to_json()
    data['bottles'] = bottles
    data['rotatetime'] = rotatetime
    # data['state'] = Game.WelcomeState
    data['gamestate'] = 'welcome'
    data['drinkwine'] = {'eatordrink': 'Drinking', 'boxorbottle': "Bottle", 'foodorbooze':'Wine'}
    data['winenames'] = pd.Series('???', index=w)
    data['bottletoname'] = {}
    data['housebottles'] =''
    data['bearernames'] = pd.Series('', index=w)
    data['auditdone'] = False
    data['winnernames'] = ['brian', 'mona']
    data['winnerwines'] = ['cab', 'malbec']
    data['tie'] = {"winner": 1, "loser": 1}
    data['scoresjson'] = 'empty'
    data['mywinescore'] = {}
    data['myguess'] = {}
    data['myreal'] = {}
    data['notes'] = {}
    data['complete'] = {}
    data['complete']['good'] = 0
    data['complete']['bad'] = 0
    data['complete']['unknown'] = 0
    data['drinkertotals'] = pd.Series([0])
    data['drinkercnt'] = 0
    data['bad_buddies'] = {"catinthehat": ["thing1", "thing2"]}
    data['good_buddies'] = {"larry": ["curly", "moe"]}
    data['missraters'] = ["catinthehat"]
    data['winnernames'] = []
    data['winnerwines'] = []
    data['mywinescore'] = {}
    data['bubplot'] = [{'x':1, 'y':1, 'r':0}]
    data['bubguess'] = [{'x':1, 'y':1, 'r':0}]
    data['emailsent'] = {}
    data['randomnotes'] = loaded_notes_list
    logging.warning(data['rotatetime'])


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global data
    #print('starting settings listen')
    
    # process updated settings
    bobkey = request.form.get('bobkey')
    if bobkey:
        bobvalue = request.form.get('bobvalue')
        logging.warning('BoB key setting {} to {}'.format(bobkey, bobvalue))
        data['drinkwine'][bobkey] = bobvalue
    
    newb = request.form.get('bottleCount')
    if newb:
        logging.warning("New bottle count to {}".format(newb))
        newb = int(newb)
        if len(data['scores'].columns) < newb:
            # reset donelist as everyone has new bottles
            data['donelist'] = pd.Series(0, index=data['donelist'].index)
            w = ['number #{}'.format(x+1) for x in range(len(data['scores'].columns),newb)]
            for col in w:
                data['scores'][col] = 0
                data['winenames'][col] = '???'
                data['bearernames'][col] = ''
        elif len(data['scores'].columns) > newb:
            for col in data['scores'].columns[newb - len(data['scores'].columns):]:
                del data['scores'][col]
                del data['winenames'][col]
                del data['bearernames'][col]
        data['bottles'] = newb
    
    housebottles = request.form.get('housebottles')
    if housebottles:
        housebottles = re.sub(u"(\u2018|\u2019)", "'", housebottles)
        logging.warning("House Brought List: {}".format(housebottles))
        data['housebottles'] = housebottles
        # Remove all old house bottles
        re_name = re.compile(u'HouseBrought_')
        for b,n in data['bottletoname'].items():
            if re_name.match(n):
                del data['bottletoname'][b]
        
        # Add new list back
        houselist = housebottles.split(',')
        c = 1
        for b in houselist:
            data['bottletoname'][b.strip()] = 'HouseBrought_{}'.format(c)
            c += 1
        save_csv()
        
    winenum = request.form.get('wineNameNum')
    if winenum:
        winename = request.form.get('value')
        if winename:
            logging.warning("Mapping wine {} to {}".format(winenum, winename))
            #print('WineNum: WineName -> {}:{}'.format(winenum, winename))
            data['winenames'][int(winenum)] = str(winename)
            data['bearernames'][int(winenum)] = data['bottletoname'][winename]
            data['myreal'][data['bottletoname'][winename]] = int(winenum)
            save_csv()
        
        # winenamebearer = request.form.get('wineNameBearer')
        # if winenamebearer:
        #     data['bearernames'][int(winenum)] = str(winenamebearer)
    newrotatetime = request.form.get('rotatetime')
    if newrotatetime:
        logging.warning("Settings updating page rotate time to {}".format(newrotatetime))
        data['rotatetime'] = newrotatetime
        save_csv()
            
    donetoggle = request.form.get('doneToggle')
    donename = request.form.get('doneName')
    
    if donename:
        logging.warning("Settings page toggle {} Done status".format(donename))
        if donetoggle == "false":
            data['donelist'][donename] = 0
        else:
            data['donelist'][donename] = 1
        
    auditdone = request.form.get('auditDone')
    if auditdone != None:
        logging.warning('Settings page toggling audit')
        #print(auditdone)
        # seems to be reverse of expected?
        if auditdone == "false":
            data['auditdone'] = True
        else:
            data['auditdone'] = False

    if len(data['scores']) >= 1:
        logging.warning("Settings Page save_csv()")
        save_csv()
    return render_template('settings.html', data=data)


@app.route('/', methods=['GET', 'POST'])
def index():
    global data
    logging.warning('React Login Page Entered')
    
    name = None
    bottle = None
    
    name = request.form.get('user')
    bottle = request.form.get('bottle')
    
    if name:
        name = name.upper().strip()
        bottle = bottle.title().strip()
        if bottle == '':
            bottle = '{}_came_empty_handed'.format(name)
        logging.warning('{} is joining the game with bottle {}'.format(name, bottle))
        if len(data['scores']) == 1 and data['scores'].index == 'mrmagoo':
            data['scores'] = data['scores'].drop(index='mrmagoo')
            data['donelist'] = data['donelist'].drop(index='mrmagoo')
        if data['scores'].index.contains(name):
            logging.warning('Player already exists')
            override_name = request.form.get('override')
            if override_name == "true":
                logging.warning('Taking over {} with new {}'.format(name, bottle))
                for k,v in data['bottletoname'].items():
                    if v == name:
                        logging.warning('Removing {}'.format(k))
                        del data['bottletoname'][k]
                    if k == bottle:
                        logging.warning('Duplicate {} bottle, appending name {}'.format(bottle, name))
                        bottle += '_{}'.format(name)
                data['bottletoname'][bottle] = name
                save_csv()
                return redirect(url_for('rating', user=name), 301)
            return('already_exists')
        else:
            logging.warning("Adding new player")
            newd = pd.DataFrame([[0 for x in range(len(data['scores'].columns))]],
                columns=data['scores'].columns, index=[name])
            data['scores'] = data['scores'].append(newd)
            data['donelist'][name] = 0
            data['myguess'][name] = 100
            data['myreal'][name] = 100
            data['notes'][name] = {}
            for k,v in data['bottletoname'].items():
                if k == bottle:
                    bottle += '_{}'.format(name)
            data['bottletoname'][bottle] = name
            data['good_buddies'][name] = []
            data['bad_buddies'][name] = []
            data['emailsent'][name] = False
            save_csv()
            return redirect(url_for('rating', user=name), 301)
        
    
    return render_template('reactlogin.html', data=data, name=name)
    

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     global data
#     logging.debug('Login Page Entered')
#     
#     form = ParticipantForm()
#     if form.validate_on_submit():
#         name = str(form.name.data).upper()
#         bottle = str(form.bottle.data).strip()
#         logging.info('Name: {} entering with bottle {}'.format(name, bottle))
#         if len(data['scores']) == 1 and data['scores'].index == 'mrmagoo':
#             data['scores'] = data['scores'].drop(index='mrmagoo')
#             data['donelist'] = data['donelist'].drop(index='mrmagoo')
#         if data['scores'].index.contains(name):
#             return render_template('relogin.html', user=name)
#         else:
#             newd = pd.DataFrame([[0 for x in range(len(data['scores'].columns))]],
#                 columns=data['scores'].columns, index=[name])
#             data['scores'] = data['scores'].append(newd)
#             data['donelist'][name] = 0
#             data['myguess'][name] = 100
#             data['myreal'][name] = 100
#             data['notes'][name] = {}
#             data['bottletoname'][bottle] = name
#             data['good_buddies'][name] = []
#             data['bad_buddies'][name] = []
#             data['emailsent'][name] = False
#             save_csv()
#             return redirect(url_for('rating', user=name))
#             #return redirect(url_for('mybottle', user=name))
#     # if len(data['scores']) == 1 and data['scores'].index == 'mrmagoo':
#     #     return redirect(url_for('settings'))
#     return render_template('login.html', form=form)


@app.route('/rating/<user>', methods=['GET', 'POST'])
def rating(user=None):
    global data
    num = request.form.get('wine')
    if num:
        num = int(num)
    score = request.form.get('score')
    done = request.form.get('done')
    notes = request.form.get('notes')
    email = request.form.get('email')
    reset = request.form.get('reset')
    logging.debug('Rating Post, All Data for {}: {}'.format(user, request.form))
    

    if data['scores'].index.contains(user):
        if reset == 'reset':
            logging.warning("{} resetting number {}".format(user, num))
            #print("RESET wine {}".format(num))
            if num in data['notes'][user]:
                del data['notes'][user][num]
            if data['donelist'][user] == 0:
                data['scores'].ix[str(user), num] = 0
                data['myguess'][user] = 100
            save_csv()
            return render_template('tasting.html', data=data, user=user)
        else:
            if notes:
                notescleaned = re.sub(u"(\u2018|\u2019)", "'", notes)
                logging.warning("{} adding notes to {}".format(user, num))
                data['notes'][user][num] = notescleaned
                #data['randomnotes'].append(notes)
                save_csv()
                return render_template('tasting.html', data=data, user=user)
            
            if email != None:
                logging.warning('{} emailing'.format(user))
                # print('Emailing {} for user {}'.format(email, user))
                winner_data, summary_data = summary(user)
                sent_email = send_email(email, summary_data, winner_data)
                logging.warning("Was email sent? {}".format(sent_email))
                data['emailsent'][user] = sent_email
                save_csv()
                return render_template('tasting.html', data=data, user=user)
            
            if num == None or score == None:
                if done:
                    logging.warning('{} is all done'.format(user))
                    data['donelist'][user] = done
                    save_csv()
                return render_template('tasting.html', data=data, user=user)
            
            if score == "Mine":
                logging.warning('{} thinks {} is theirs'.format(user, num))
                data['myguess'][user] = num
                save_csv()
                return render_template('tasting.html', data=data, user=user)
            else:
                score = int(score)
                logging.warning("{} rates {} with a {}".format(user, num, score))
                # These checks are likely irrelevent 
                if num <= data['bottles']:
                    data['scores'].ix[str(user), num] = score
                    #data['scores'].loc[str(user)][num] = score
                    save_csv()
                    num = int(num) + 1
                    if int(num) > int(data['bottles']):
                        return "<h1>All Done</h1>\n{}".format(tabulate.tabulate(data['scores'].loc[[user]], headers='keys', tablefmt='html'))
                    return render_template('tasting.html', data=data, user=user)
        
        # From here on likely is not called 
        if num <= data['bottles']:
            logging.error("Why did I get here?")
            data['scores'].ix[str(user), num] = score
            #data['scores'].loc[str(user)][num] = score
            save_csv()
            num = int(num) + 1
            if int(num) > int(data['bottles']):
                return "<h1>All Done</h1>\n{}".format(tabulate.tabulate(data['scores'].loc[[user]], headers='keys', tablefmt='html'))
            return render_template('tasting.html', data=data, user=user)

        if num > int(bottles):
            logging.error("Number rated:{} should never be greater than total bottles available:{}".format(num, bottles))
            return "too many bottles {} out of {}\n{}".format(int(num), bottles, tabulate.tabulate(data['scores'], headers='keys', tablefmt='html'))
        
        #print(data)

        return render_template('tasting.html', data=data, user=user)
    return render_template('missinglogin.html', user=user)

def summary(user):
    s = json.loads(data['scores'].to_json(orient='index'))
    #print(s)
    new_s = OrderedDict()
    for name in s:
        if name == user:
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
    # print('All Wines\n{}\n'.format(json.dumps(new_w, indent=4)))
    # print('Personal Output \n{}\n'.format(json.dumps(new_s, indent=4)))
    logging.debug('Summary for {}: {}'.format(user, new_s))
    logging.debug('Wine Scores (Loser to Winner): {}'.format(new_w))
    return(new_w, new_s)
    

@app.route('/results', methods=['GET'])
def results():
    global data
    
    #if (data['state'] == Game.WelcomeState):
        #print("welcome")
        #return render_template('welcome.html', data=data)
    # add best wine, worst wine, most consisten wine, most contreversal,
    # biggest point person, lowest point person, person with rating closest to order of winners...
    # make sure to check for tie-breakers
    # return '<meta http-equiv="refresh" content="8" /><h1>Bottles: {}</h1>\n<h1>Winner</h1>\n{}\n\n<h1>Loser</h1>\n{}\n\n<h1>Gave most points:</h1>\n{}\n\n<h1>Gave least points:</h1>\n{}\n\n<h1>Ranking:</h1>\n{}\n\n<h1>Totals</h1>:\n{}\n\n<h1>TasterTotals:</h1>\n{}\n\n<h1>Wines Max Rating:</h1>\n{}\n\n<h1>Wines Min Rating:</h1>\n{}'.format(
    #     data['bottles'],
    #     data['scores'].sum().idxmax(),
    #     data['scores'].sum().idxmin(),
    #     data['scores'].sum(axis=1).idxmax(),
    #     data['scores'].sum(axis=1).idxmin(),
    #     tabulate.tabulate([data['scores'].sum().rank()], headers='keys', tablefmt='html'),
    #     tabulate.tabulate(data['scores'].append([data['scores'].sum()]), headers='keys', tablefmt='html'),
    #     tabulate.tabulate([[data['scores'].sum(axis=1)]], headers='keys', tablefmt='html'),
    #     tabulate.tabulate([data['scores'].max()], headers='keys', tablefmt='html'),
    #     tabulate.tabulate([data['scores'].min()], headers='keys', tablefmt='html'))
    return render_template('global.html', data=data, myip="blindwine.duckdns.org")


def save_csv():
    logging.warning('Saving Data...')
    global data
    global loaded_notes_list
    #print("save_csv start")
    #print(data['myguess'])
    #print(data['bottletoname'])
    
    # process stuff
    if (len(data['scores'].index) > 2):    
        data['winetotals'] = data['scores'].sum().sort_values()
        data['drinkertotals'] = data['scores'].sum(axis=1).sort_values()
        tie_loser = tie_winner = 0
        if len(data['scores'].sum().rank(method='max').sort_values()[-4:].mode()) < 4:
            tie_winner = 1
        if len(data['scores'].sum().rank(method='max').sort_values()[:2].mode()) < 2:
            tie_loser = 1
        data['tie'] = {"winner": tie_winner, "loser": tie_loser}
        names_winner = []
        wine_winner = []
        for wine in data['scores'].sum().rank(method='max').sort_values().index:
            names_winner.append(data['bearernames'][wine])
            wine_winner.append(data['winenames'][wine]  + " -> " + str(data['scores'].sum()[wine]))
        data['winnernames'] = names_winner
        data['winnerwines'] = wine_winner
                
        # make df for name to name, then interate over corr to populate correlation
        buddies = pd.DataFrame(columns=[data['scores'].index], index=[data['scores'].index])
        buddies = buddies.fillna(0)
        #buddies = pd.DataFrame(columns=[data['scores'].index], index=[x for x in range(len(data['scores'].index))])
        clipscores = pd.DataFrame()
        wineprogress = []
        unknown = good = bad = 0
        # figure our x:wine# % 4, y:wine#, r:sum of scores
        bubplot = []
        wc = 1
        for wine in data['scores'].columns:
            if data['scores'][wine].mean() > 1.0:
                clipscores[wine] = data['scores'][wine]
                wineprogress.append(wine)
            rdata = [0 for x in range(8)]
            for score in data['scores'][wine]:
                if score == 0:
                    unknown += 1
                elif score <= 4:
                    bad += 1
                else:
                    good += 1
                if score > 0:
                    #rdata[(score - 1) % 4] += 1
                    rdata[(score - 1)] += 1
            rc = 1
            scale = 144 / len(data['scores'].index)
            if sum(rdata) >= 1:
                for r in rdata:
                    bubdict = {}
                    bubdict['x'] = (rc * scale) + (random.randrange(-4,5) * 0.1 * scale)
                    bubdict['y'] = (wc * scale) + (random.randrange(-4,5) * 0.1 * scale)
                    bubdict['r'] = r * scale
                    bubplot.append(bubdict)
                    rc += 1
            wc += 1
        bubplot.append({'x': 0, 'y': 0, 'r':0})
        bubplot.append({'x': 9 * scale, 'y': (len(wineprogress) + 1) * scale, 'r':0})
        data['bubplot'] = bubplot
        data['wineprogress'] = wineprogress
        data['complete']['good'] = good
        data['complete']['bad'] = bad
        data['complete']['unknown'] = unknown
        
        # who's slow to rate
        missraters = {}
        trendsetter = pd.Series(0.0, index=data['scores'].index)
        winemean = data['scores'].mean()
        for wine in data['wineprogress']:
            offavg = 0
            for name in data['scores'].index:
                if int(data['scores'].loc[name][wine]) < 1:
                    if name in missraters:
                        missraters[name] += 1
                    else:
                        missraters[name] = 1
                    # missraters.append(name)
                offavg = abs(data['scores'].loc[name][wine] - winemean[wine])
                trendsetter[name] = trendsetter[name] + offavg
        data['missraters'] = missraters
        data['trendsetters'] = trendsetter.sort_values()

        #print('clipscores')
        #print(clipscores)
        for row in buddies.index:
            for col in buddies.columns:
                #print('row {} - col {}'.format(row[0],col[0]))
                if row[0] != col[0]:
                    for wine in clipscores:
                        score_diff = abs(clipscores[wine].loc[row] - clipscores[wine].loc[col])
                        buddies.ix[row, col] = buddies.ix[row, col] + score_diff
                    #print("processing => {}".format(data['scores'].iloc[row].corr(data['scores'].loc[col])))
                    #buddies.ix[row, col] = clipscores.iloc[row].corr(clipscores.loc[col], method='pearson')
                    #buddies.ix[row, col] = clipscores.iloc[row].cov(clipscores.loc[col])
        data['buddies'] = buddies
        
        buddy_dict_good = {}
        buddy_dict_bad = {}
        good_bar = len(wineprogress) * 1.1
        bad_bar = len(wineprogress) * 3
        for namecnt in range(len(data['buddies'].columns)):
            buddy_dict_good[data['buddies'].columns[namecnt][0]] = []
            buddy_dict_bad[data['buddies'].columns[namecnt][0]] = []
            for bud, diff in data['buddies'].iloc[namecnt].iteritems():
                if bud[0] != data['buddies'].columns[namecnt][0]:
                    if diff < good_bar:
                        buddy_dict_good[data['buddies'].columns[namecnt][0]].append(bud[0])
                    elif diff >= bad_bar:
                        buddy_dict_bad[data['buddies'].columns[namecnt][0]].append(bud[0])
        data['good_buddies'] = buddy_dict_good
        data['bad_buddies'] = buddy_dict_bad
        
        bubguess = []
        maxc = 2
        for wine in range(data['bottles']):
            guessdict = []
            bub = 6
            c = data['myguess'].values().count(wine)
            if c > maxc:
                maxc = c
            guessdict = {'x': wine+1, 'y': 0, 'r': 1}
            bubguess.append(guessdict)
            for up in range(c):
                guessdict = {'x': wine+1, 'y': up + 1, 'r': bub}
                bubguess.append(guessdict)
                bub *= 2
        bubguess.append({'x': 0, 'y': 0, 'r': 0})
        bubguess.append({'x': data['bottles'] + 1, 'y': maxc + 1, 'r': 0})
        data['bubguess'] = bubguess
        #print(bubguess)
        
        # Change state
        if (len(data['scores'].index) < data['bottles']/2):
            #print('welcome')
            # data['state'] = Game.WelcomeState
            data['gamestate'] = 'welcome'
        elif (len(data['scores'].index) >= 4) and len(data['wineprogress']) >= 2:
            #print('tasting')
            # data['state'] = Game.TastingState
            data['gamestate'] = 'tasting'
            if len(data['scores'].index) == data['donelist'].sum():
                #print("audit")
                # data['state'] = Game.AuditState
                data['gamestate'] = 'audit'
                if data['auditdone'] == True:
                    #print('winlose')
                    # data['state'] = Game.WinLoseState
                    data['gamestate'] = 'winLose'
                    
        # make plot barh
        # bh = data['scores'].T.plot.barh(stacked=True)
        # fig = bh.get_figure()
        # fig.savefig('static/allscores.png')

        mywinescore = {name: 0 for name in data['scores'].index}
        #if len(data['bearernames']) == len(data['scores']):
        for wine,name in data['bearernames'].iteritems():
            #print('{} - {}'.format(wine,name))
            if name in data['scores'].index:
                #print(name)
                mywinescore[name] = data['scores'].loc[name][wine]
                #print(mywinescore)
        data['mywinescore'] = mywinescore
        
        data['randomnotes'] = []
        for name in data['notes']:
            for wine in data['notes'][name]:
                data['randomnotes'].append(data['notes'][name][wine])
        realnotecnt = len(data['randomnotes'])
        if realnotecnt <= 6:
            for n in range(6 - realnotecnt):
                data['randomnotes'].append(random.choice(loaded_notes_list))
            
        #data['table'] = str(tabulate.tabulate(data['scores'], headers='keys', tablefmt='html'))
        # print("\nTieW {}\nTieL {}\nloser to winner {}\nwines low to high {}\n".format(tie_winner, tie_loser, names_winner, wine_winner))
        # print("LoveHate: {}\nConsistent: {}\n".format(data['scores'].std().idxmax(), data['scores'].std().idxmin()))
        # print("Audit Done {}".format(data['auditdone']))
        # print('Good Buddies: {}'.format(data['good_buddies']))
        # print('Bad Buddies: {}'.format(data['bad_buddies']))
        # print('Wine Names: {}'.format(data['winenames']))
        # print('Wine Progress: {}'.format(data['wineprogress']))
        # print('Shame: {}'.format(data['missraters']))
        # print('Buddies: \n{}'.format(data['buddies']))
        # print('Personal Wine Score: \n{}'.format(data['mywinescore']))
            
    data['scoresjson'] = data['scores'].to_json(orient='index')
    data['donelistjson'] = data['donelist'].to_json()


    # and finally, save to disk
    #print("writing data: {}".format(data))
    #data['scores'].to_csv('wine.csv')
    logging.warning('Numbers Crunched')
    pickle.dump( data, open( 'wine.pickle', 'wb' ) )
    logging.warning('Pickle Saved')
    
    
    sendUpdate()

def sendUpdate():
    logging.warning('Sending Update...')
    global data
    logging.debug('Total Data: {}'.format(data))
    #print("sendUpdate")
    dto = {
        "scores": data['scores'].sum().to_json(),
        "scoresjson": data['scoresjson'],
        "donelist": data['donelistjson'],
        "complete": data['complete'],
        #"state": data['state'].value,
        "gamestate": data['gamestate'],
        "drinkertotals": data['drinkertotals'].to_json(),
        "drinkercnt": len(data['drinkertotals']),
        "badbuddies": data['bad_buddies'],
        "goodbuddies": data['good_buddies'],
        "missraters": data['missraters'],
        "tie": data['tie'],
        "winnernames": data['winnernames'],
        "winnerwines": data['winnerwines'],
        "mywinescore": data['mywinescore'],
        "winenames": data['winenames'].to_json(),
        "notes": data['notes'],
        "randomnotes": data['randomnotes'],
        "bottlenames": data['bottletoname'].keys(),
        "bubplot": data['bubplot'],
        "myguess": data['myguess'],
        "bubguess": data['bubguess'],
        "bob": data['drinkwine'],
        "bottlecount": data['bottles'],
        "rotatetime": data['rotatetime'],
        "emailsent": data['emailsent']
    }
    #print(dto)
    socketio.emit('my_response', dto)
    logging.warning('Socket Emit Done')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
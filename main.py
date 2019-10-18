# import copy
import enum
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField, IntegerField, SubmitField
import numpy as np
import os
import pandas as pd
import pickle
import random
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

from settings import secret_key, bottles
# from game import Game
# game = Game()

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

    
class MyBottleForm(FlaskForm):
    name = StringField('name',
                            validators=[InputRequired('A name is required!'),
                                       Length(min=2, max=40,
                                              message='Must be between 2 and 40 characters.')])

class Game(enum.Enum):
    WelcomeState = "welcome"
    TastingState = "tasting"
    AuditState = "audit"
    WinLoseState = "winLose"
    
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
socketio = SocketIO(app, async_mode=None)

data = {}

@socketio.on('connect')
def connect():
    sendUpdate()

# Read in data if it's available
# Pickle is the best, wine.csv will need to build a few other keys based on csv input
# Last resort is fresh game, and build up everything by scratch
if os.path.isfile('wine.pickle'):
    data = pickle.load( open( 'wine.pickle', 'rb') )
elif os.path.isfile('wine.csv'):
    data['scores'] = pd.read_csv('wine.csv', index_col=0)
    data['donelist'] = pd.Series(0, index=data['scores'].index)
    data['bottles'] = len(data['scores'].columns)
    if (len(data['scores'].index) >= 4):
        data['state'] = Game.TastingState
    else:
        data['state'] = Game.WelcomeState
    data['winenames'] = pd.Series('unk', index=data['scores'].columns)
    data['bearernames'] = pd.Series('', index=data['scores'].columns)
else:
    # Create base scores, the rest gets built later
    scores = pd.DataFrame(dtype=int)
    w = ['wine #{}'.format(x+1) for x in range(bottles)]
    for col in w:
        scores[col] = pd.Series([], dtype=int)

    # Save in big dict
    data['scores'] = scores
    data['donelist'] = pd.Series([], dtype=int)
    newd = pd.DataFrame([[0 for x in range(len(data['scores'].columns))]],
    columns=data['scores'].columns, index=['mrmagoo'])
    data['scores'] = data['scores'].append(newd)
    data['donelist']['mrmagoo'] = 0 
    data['bottles'] = bottles
    data['state'] = Game.WelcomeState
    data['winenames'] = pd.Series('unk', index=w)
    data['bottletoname'] = {}
    data['bearernames'] = pd.Series('', index=w)
    data['auditdone'] = False
    data['winnernames'] = ['brian', 'mona']
    data['winnerwines'] = ['cab', 'malbec']
    data['tie'] = {"winner": 1, "loser": 1}
    data['scoresjson'] = 'empty'
    data['mywinescore'] = {}
    data['myguess'] = {}
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


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global data
    
    # process updated settings
    newb = request.form.get('bottleCount')
    if newb:
        newb = int(newb)
        if len(data['scores'].columns) < newb:
            # reset donelist as everyone has new bottles
            data['donelist'] = pd.Series(0, index=data['donelist'].index)
            w = ['wine #{}'.format(x+1) for x in range(len(data['scores'].columns),newb)]
            for col in w:
                data['scores'][col] = 0
                data['winenames'][col] = 'unk'
                data['bearernames'][col] = ''
        elif len(data['scores'].columns) > newb:
            for col in data['scores'].columns[newb - len(data['scores'].columns):]:
                del data['scores'][col]
                del data['winenames'][col]
                del data['bearernames'][col]
        data['bottles'] = newb
    
    winenum = request.form.get('wineNameNum')
    if winenum:
        winename = request.form.get('value')
        if winename:
            data['winenames'][int(winenum)] = str(winename)
            data['bearernames'][int(winenum)] = data['bottletoname'][winename]
            save_csv()
        
        # winenamebearer = request.form.get('wineNameBearer')
        # if winenamebearer:
        #     data['bearernames'][int(winenum)] = str(winenamebearer)
            
    donetoggle = request.form.get('doneToggle')
    donename = request.form.get('doneName')
    
    if donename:
        if donetoggle == "false":
            data['donelist'][donename] = 0
        else:
            data['donelist'][donename] = 1
        
    auditdone = request.form.get('auditDone')
    if auditdone != None:
        #print(auditdone)
        # seems to be reverse of expected?
        if auditdone == "false":
            data['auditdone'] = True
        else:
            data['auditdone'] = False

    if len(data['scores']) >= 1:
        save_csv()
    return render_template('settings.html', data=data)

@app.route('/', methods=['GET', 'POST'])
def index():
    global data
    
    form = ParticipantForm()
    if form.validate_on_submit():
        name = str(form.name.data).upper()
        bottle = str(form.bottle.data).strip()
        if len(data['scores']) == 1 and data['scores'].index == 'mrmagoo':
            data['scores'] = data['scores'].drop(index='mrmagoo')
            data['donelist'] = data['donelist'].drop(index='mrmagoo')
        if data['scores'].index.contains(name):
            return render_template('relogin.html', user=name)
        else:
            newd = pd.DataFrame([[0 for x in range(len(data['scores'].columns))]],
                columns=data['scores'].columns, index=[name])
            data['scores'] = data['scores'].append(newd)
            data['donelist'][name] = 0
            data['myguess'][name] = 100
            data['bottletoname'][bottle] = name
            save_csv()
            return redirect(url_for('rating', user=name))
            #return redirect(url_for('mybottle', user=name))
    return render_template('login.html', form=form)


@app.route('/mybottle/<user>', methods=['GET', 'POST'])
def mybottle(user=None):
    global data
    mybottle = MyBottleForm()
    if mybottle.validate_on_submit():
        pass
    return render_template('mybottle.html', mybottle=mybottle, user=user)

@app.route('/rating/<user>', methods=['GET', 'POST'])
def rating(user=None):
    global data
    num = request.form.get('wine')
    score = request.form.get('score')
    done = request.form.get('done')
    #print(data)

    
    if data['scores'].index.contains(user):
        if num == None or score == None:
            if done:
                data['donelist'][user] = done
                save_csv()
            return render_template('tasting.html', data=data, user=user)
        
        num = int(num)
        if score == "Mine":
            data['myguess'][user] = num
            save_csv()
            return render_template('tasting.html', data=data, user=user)
        else:
            score = int(score)
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
            data['scores'].ix[str(user), num] = score
            #data['scores'].loc[str(user)][num] = score
            save_csv()
            num = int(num) + 1
            if int(num) > int(data['bottles']):
                return "<h1>All Done</h1>\n{}".format(tabulate.tabulate(data['scores'].loc[[user]], headers='keys', tablefmt='html'))
            return render_template('tasting.html', data=data, user=user)

        if num > int(bottles):
            return "too many bottles {} out of {}\n{}".format(int(num), bottles, tabulate.tabulate(data['scores'], headers='keys', tablefmt='html'))
        
        print(data)

        return render_template('tasting.html', data=data, user=user)
    return render_template('missinglogin.html', user=user)


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
    return render_template('global.html', data=data, myip="blindTASTY")


def save_csv():
    global data
    print("save_csv start")
    #print(data['myguess'])
    print(data['bottletoname'])
    
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
        good_bar = len(wineprogress) * 2
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
        print(bubguess)
        
        # Change state
        if (len(data['scores'].index) < data['bottles']/2):
            print('welcome')
            data['state'] = Game.WelcomeState    
        elif (len(data['scores'].index) >= 4) and len(data['wineprogress']) >= 2:
            print('tasting')
            data['state'] = Game.TastingState
            if len(data['scores'].index) == data['donelist'].sum():
                print("audit")
                data['state'] = Game.AuditState
                if data['auditdone'] == True:
                    print('winlose')
                    data['state'] = Game.WinLoseState
                    
        # make plot barh
        # bh = data['scores'].T.plot.barh(stacked=True)
        # fig = bh.get_figure()
        # fig.savefig('static/allscores.png')

        mywinescore = {name: 0 for name in data['scores'].index}
        #if len(data['bearernames']) == len(data['scores']):
        for wine,name in data['bearernames'].iteritems():
            #print('{} - {}'.format(wine,name))
            if name:
                #print(name)
                mywinescore[name] = data['scores'].loc[name][wine]
                #print(mywinescore)
        data['mywinescore'] = mywinescore
            
        #data['table'] = str(tabulate.tabulate(data['scores'], headers='keys', tablefmt='html'))
        print("\nTieW {}\nTieL {}\nloser to winner {}\nwines low to high {}\n".format(tie_winner, tie_loser, names_winner, wine_winner))
        print("LoveHate: {}\nConsistent: {}\n".format(data['scores'].std().idxmax(), data['scores'].std().idxmin()))
        print("Audit Done {}".format(data['auditdone']))
        print('Good Buddies: {}'.format(data['good_buddies']))
        print('Bad Buddies: {}'.format(data['bad_buddies']))
        print('Wine Names: {}'.format(data['winenames']))
        print('Wine Progress: {}'.format(data['wineprogress']))
        print('Shame: {}'.format(data['missraters']))
        print('Buddies: \n{}'.format(data['buddies']))
        print('Personal Wine Score: \n{}'.format(data['mywinescore']))
    

            
            
    data['scoresjson'] = data['scores'].to_json(orient='index')
    data['donelistjson'] = data['donelist'].to_json()


    # and finally, save to disk
    #print("writing data: {}".format(data))
    data['scores'].to_csv('wine.csv')
    pickle.dump( data, open( 'wine.pickle', 'wb' ) )
    
    sendUpdate()

def sendUpdate():
    global data
    dto = {
        "scores": data['scores'].sum().to_json(),
        "complete": data['complete'],
        "state": data['state'].value,
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
        "bottletoname": data['bottletoname'],
        "bubplot": data['bubplot'],
        "myguess": data['myguess'],
        "bubguess": data['bubguess']
    }
    print(dto)
    socketio.emit('my_response', dto)





if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
# -*- coding: utf-8 -*-

from flask import Flask,jsonify,json,abort
from flask import request,make_response
from flask_cors import CORS, cross_origin
import cx_Oracle
import json
import datetime
import random
#import connect

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
database_url='piecia/piecia1@localhost:1521/xe'
range_values=[3,4,5,6,7]

@app.before_request
def option_autoreply():
    """ Always reply 200 on OPTIONS request """

    if request.method == 'OPTIONS':
        resp = app.make_default_options_response()

        headers = None
        if 'ACCESS_CONTROL_REQUEST_HEADERS' in request.headers:
            headers = request.headers['ACCESS_CONTROL_REQUEST_HEADERS']

        h = resp.headers

        # Allow the origin which made the XHR
        h['Access-Control-Allow-Origin'] = request.headers['Origin']
        # Allow the actual method
        h['Access-Control-Allow-Methods'] = request.headers['Access-Control-Request-Method']
        # Allow for 10 seconds
        h['Access-Control-Max-Age'] = "10"

        h['Access-Control-Allow-Credentials'] = "true"

        # We also keep current headers
        if headers is not None:
            h['Access-Control-Allow-Headers'] = headers

        return resp


@app.after_request
def set_allow_origin(resp):
    """ Set origin for GET, POST, PUT, DELETE requests """

    h = resp.headers

    # Allow crossdomain for other HTTP Verbs
    if request.method != 'OPTIONS' and 'Origin' in request.headers:
        h['Access-Control-Allow-Origin'] = request.headers['Origin']


    return resp

"""Dodanie nowych uzytkownikow
"""
@app.route('/Ps01.php', methods=['GET'])
@cross_origin(origin='*')
def add_users():
    auth=request.authorization
    if(not auth):
        abort(make_response('Nie przeslales danych do dodania uzytkownika'))
    login,password= auth.username, auth.password
    con = cx_Oracle.connect(database_url)
    cur = con.cursor()
    bind={'name':login,'password':password,'last_login':datetime.datetime.now(),'last_failed_login':datetime.datetime(1,1,1,1,1,1),
          'failed_attemps_login':0,'block_after':5}
    #bind={'data':None}
    sql='INSERT INTO users2 VALUES(user2_id.nextval,:name,:password,:last_login,:last_failed_login,:failed_attemps_login,:block_after)'
    cur.prepare(sql)
    cur.execute(sql,bind)
    con.commit() # zatwierdzenie operacji usuniecia wiadomosci
    sql='SELECT * FROM users2'
    cur.execute(sql)
    all_users=cur.fetchall()
    cur.close()
    con.close()
    return jsonify(all_users)
    
"""Formularz I
Logowanie - zwracany json dla zalogowanego użytkownika
"""
@app.route('/Ps04.php', methods=['GET'])
@cross_origin(origin='*')
def login():
    auth = request.authorization
    if(not auth):
        abort(make_response('Nie przeslales danych do logowania'))
    login,password=auth.username, auth.password
    con = cx_Oracle.connect(database_url)
    cur = con.cursor()
    check_user_by_login=checkUserByLogin(cur,login)
    if(not check_user_by_login):
        check_fake_user_by_login=checkFakeUserByLogin(cur,login)
        if(not check_fake_user_by_login):
            bind={'name':login,'last_failed_login':datetime.datetime.now(),'failed_attemps_login':1,'block_after':random.choice(range_values)}
            sql='INSERT INTO fake_users VALUES(fake_user_id.nextval,:name,:last_failed_login,:failed_attemps_login,:block_after)'
            cur.prepare(sql)
            cur.execute(sql,bind)
            con.commit() # zatwierdzenie operacji dodania fake_usera
            return jsonify({'info':'Niepoprawny login lub hasło','time':10})
        else:
            # 1 - patrzymy czy konto nie jest zablokowane
            # pobieramy liczbe prob logowan
            # oraz liczbe nieudanych logowan po ktorych nastepuje blokada konta
            bind={'name':login}
            sql='SELECT failed_attemps_login,block_after FROM fake_users WHERE name=:name'
            cur.prepare(sql)
            cur.execute(sql,bind)
            failed_login=cur.fetchone()
            failed_attemps_login, block_after=failed_login[0], failed_login[1]
            if(failed_attemps_login>=block_after):
                return jsonify({'info':'Twoje konto jest zablokowane'})
            # 2 sprawdzamy czy uzytkownik moze wykonac kolejna probe logowania
            sql='SELECT last_failed_login FROM fake_users WHERE name=:name'
            cur.prepare(sql)
            cur.execute(sql,bind)
            last_failed_login=cur.fetchone()[0]
            actual_time=datetime.datetime.now() 
            if (failed_attemps_login == 1):
                wait_time = last_failed_login + datetime.timedelta(seconds=10)
                wait_seconds=30
            elif(failed_attemps_login == 2):
                wait_time = last_failed_login + datetime.timedelta(seconds = 30)
                wait_seconds=60
            elif(failed_attemps_login==3):
                wait_time=last_failed_login+datetime.timedelta(minutes=1)
                wait_seconds=300
            elif(failed_attemps_login==4):
                wait_time=last_failed_login+datetime.timedelta(minutes=5)
                wait_seconds=1800
            elif(failed_attemps_login==5):
                wait_time=last_failed_login+datetime.timedelta(minutes=30)
                wait_seconds=3600
            elif(failed_attemps_login==6):
                wait_time=last_failed_login+datetime.timedelta(hours=1)
                wait_seconds=10000 #nie uzywane
            else:
                return jsonify({'info':'Twoje konto jest zablokowane'})
            if(wait_time > actual_time):
                diffrence_time = wait_time - actual_time
                return jsonify({'info' : 'Musisz poczekac','time' : diffrence_time.total_seconds()})
            else:
                # 3 - zwiekszamy liczbe prob logowan o 1 (failed_attemps_login)
                bind={'name' : login, 'last_failed_login' : actual_time}
                sql='UPDATE fake_users SET failed_attemps_login = failed_attemps_login + 1, last_failed_login=:last_failed_login WHERE name=:name'
                cur.prepare(sql)
                cur.execute(sql,bind)
                con.commit()
                failed_attemps_login=failed_attemps_login+1
                # 3 - sprawdzamy czy nie była to ostatnia próba logowania
                if(failed_attemps_login==block_after):
                    return jsonify({'info':'Twoje konto zostało zablokowane'})
                else:
                    return jsonify({'info':'Niepoprawny login lub hasło','time':wait_seconds})
    else:
        # 1 - patrzymy czy konto nie jest zablokowane
        # pobieramy liczbe prob logowan
        # oraz liczbe nieudanych logowan po ktorych nastepuje blokada konta
        bind={'name':login}
        sql='SELECT failed_attemps_login,block_after FROM users2 WHERE name=:name'
        cur.prepare(sql)
        cur.execute(sql,bind)
        failed_login=cur.fetchone()
        failed_attemps_login, block_after=failed_login[0], failed_login[1]
        if(failed_attemps_login>=block_after):
            return jsonify({'info':'Twoje konto jest zablokowane'})
        # 2 sprawdzamy czy uzytkownik moze wykonac kolejna probe logowania
        sql='SELECT last_failed_login FROM users2 WHERE name=:name'
        cur.prepare(sql)
        cur.execute(sql,bind)
        last_failed_login=cur.fetchone()[0]
        actual_time=datetime.datetime.now() 

        if(failed_attemps_login == 0):
            wait_time = datetime.datetime(1,1,1,1,1,1)
            wait_seconds=10
        elif (failed_attemps_login == 1):
            wait_time = last_failed_login + datetime.timedelta(seconds=10)
            wait_seconds=30
        elif(failed_attemps_login == 2):
            wait_time = last_failed_login + datetime.timedelta(seconds = 30)
            wait_seconds=60
        elif(failed_attemps_login==3):
            wait_time=last_failed_login+datetime.timedelta(minutes=1)
            wait_seconds=300
        elif(failed_attemps_login==4):
            wait_time=last_failed_login+datetime.timedelta(minutes=5)
            wait_seconds=1800
        elif(failed_attemps_login==5):
            wait_time=last_failed_login+datetime.timedelta(minutes=30)
            wait_seconds=3600
        elif(failed_attemps_login==6):
            wait_time=last_failed_login+datetime.timedelta(hours=1)
            wait_seconds=10000 #nie uzywane
        else:
            return jsonify({'info':'Twoje konto jest zablokowane'})
        if(wait_time > actual_time):
            diffrence_time = wait_time - actual_time
            return jsonify({'info' : 'Musisz poczekac','time' : diffrence_time.total_seconds()})
        else:
            check_user=checkUser(cur,login,password)
            if(not check_user):
                # 3 - zwiekszamy liczbe prob logowan o 1 (failed_attemps_login)
                bind={'name' : login, 'last_failed_login' : actual_time}
                sql='UPDATE users2 SET failed_attemps_login = failed_attemps_login + 1, last_failed_login=:last_failed_login WHERE name=:name'
                cur.prepare(sql)
                cur.execute(sql,bind)
                con.commit()
                failed_attemps_login=failed_attemps_login+1
                # 3 - sprawdzamy czy nie była to ostatnia próba logowania
                if(failed_attemps_login==block_after):
                    return jsonify({'info':'Twoje konto zostało zablokowane'})
                else:
                    return jsonify({'info':'Niepoprawny login lub hasło','time':wait_seconds})
            else:
                #poprawne logowanie
                bind={'name':login}
                sql='SELECT * FROM users2 WHERE name=:name'
                cur.prepare(sql)
                cur.execute(sql,bind)
                correct_user=cur.fetchone()
                bind={'name':login,'last_login':actual_time}
                sql='UPDATE users2 SET failed_attemps_login = 0,last_login=:last_login WHERE name=:name'
                cur.prepare(sql)
                cur.execute(sql,bind)
                con.commit()
                return jsonify({'name':correct_user[1],'last_login':correct_user[3],'last_failed_login':correct_user[4],
                                'failed_attemps_login':correct_user[5],'block_after':correct_user[6]})


"""Formularz II
Zmiana parametru block_after
"""
@app.route('/Ps042.php', methods=['GET'])
@cross_origin(origin='*')
def changeOption():
    auth = request.authorization
    if(not auth):
        abort(make_response('Nie przeslales danych do logowania'))
    login, password = auth.username, auth.password
    con = cx_Oracle.connect(database_url)
    cur = con.cursor()
    check_user = checkUser(cur,login,password)
    if( not check_user):
        return jsonify({'info':'Nieporawny login lub hasło'})
    else:
        block_after=int(request.args.get('par'))
        if(block_after < 3 or block_after > 7):
            return jsonify({'info' : 'Nieprawidłowy zakres'})
        else:
            bind ={'name' : login, 'block_after' : block_after}
            sql = 'UPDATE users2 SET block_after =: block_after WHERE name =: name'
            cur.prepare(sql)
            cur.execute(sql,bind)
            con.commit()
            bind={'name':login}
            sql='SELECT * FROM users2 WHERE name =: name'
            cur.prepare(sql)
            cur.execute(sql,bind)
            correct_user=cur.fetchone()
            return jsonify({'name':correct_user[1],'last_login':correct_user[3],'last_failed_login':correct_user[4],
                            'failed_attemps_login':correct_user[5],'block_after':correct_user[6]})


def checkUserByLogin(cur,login):
    bind = {'login': login}
    sql = 'select * from users2 where name = :login'
    cur.prepare(sql)
    cur.execute(sql, bind)
    logged_user = cur.fetchone() 
    if(logged_user):
        return True
    else:
        return False
def checkFakeUserByLogin(cur,login):
    bind = {'login': login}
    sql = 'select * from fake_users where name = :login'
    cur.prepare(sql)
    cur.execute(sql, bind)
    logged_user = cur.fetchone() 
    if(logged_user):
        return True
    else:
        return False

def checkUser(cur,login,password):
    bind = {'login': login,'password_check':password}
    sql = 'select * from users2 where name = :login AND password=:password_check'
    cur.prepare(sql)
    cur.execute(sql, bind)
    logged_user = cur.fetchone() 
    if(logged_user):
        return True
    else:
        return False 

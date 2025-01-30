#!/usr/bin/python3
#coding: utf-8
'''
Base file of MemberBase
'''

import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory, make_response, jsonify
from flask import url_for, redirect
import flask_login
import json
import csv
from jinja2 import Template
from modules import dbio, settingsIo

# global settings:

settingsfile = 'MemberBase.conf'

settings = settingsIo.settingsIo(settingsfile)
dbfile = settings.get('dbfile')
host = settings.get('host')
port = settings.get('port')
port = '5000' #TODO: remove when main-dev done
debug = settings.get('debug')

# WebServer stuff:

MemberBase = Flask(__name__)

# login-stuff

MemberBase.secret_key = settings.get('secret_key')
login_manager = flask_login.LoginManager()
login_manager.init_app(MemberBase)

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username != settings.get('admin'):
        return
    user = User()
    user.id = username
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    #if username not in users:
    if username != settings.get('admin'):
        return
    user = User()
    user.id = username
    if username == settings.get('admin'):
        user.is_authenticated = settings.checkPw(request.form['password'])
    return user

# routes

@MemberBase.route('/', methods=['GET'])
def index():
    '''show index-page'''
    if settings.get('admin') == '':
        return redirect('_init')
    elif flask_login.current_user.is_anonymous:
        return render_template('index.html', relroot='./', organame=settings.get('organame'))
    elif flask_login.current_user.id == settings.get('admin'):
        return redirect('admin')
    else:
        return redirect('_user/'+flask_login.current_user.id)

@MemberBase.route('/_init', methods=['GET', 'POST'])
def init():
    if settings.get('admin') == '':
        if request.method == 'GET':
            return render_template('init.html', relroot='./', path='_init')
        password = request.form['password']
        if password != '':
            settings.set('admin', 'admin')
            settings.set('password', password)
            return redirect('_login')
        return 'ERROR: password was not set!'
    else:
        return redirect('./')

@MemberBase.route('/_login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return redirect('./')
    username = request.form['username']
    password = request.form['password']
    if username == settings.get('admin'):
        if settings.checkPw(password):
            user = User()
            user.id = username
            flask_login.login_user(user)
            return redirect('admin')
    return 'Bad login'

@MemberBase.route('/_logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect('./')

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

@MemberBase.route('/_static/<filename>', methods=['GET'])
def sendStatic(filename):
    '''send static files like css or js'''
    return send_from_directory('static', filename)


@MemberBase.route('/admin', methods=['GET'])
@flask_login.login_required
def admin():
    '''show admin-page'''
    user = flask_login.current_user.id
    if flask_login.current_user.id != settings.get('admin'):
        return '405 not allowed'
    db = dbio.MbDb(dbfile)
    sJson = json.dumps({'dbfile':settings.get('dbfile'), 'host':settings.get('host'), 'port':settings.get('port'), 
            'debug':settings.get('debug'), 'organame':settings.get('organame'), 'magazine_name':settings.get('magazine_name')});
    members = db.getMembers()
    msJson = json.dumps(members, indent=2)
    return render_template('admin.html', relroot='./', authuser=flask_login.current_user.id, sJson=sJson, msJson=msJson)

@MemberBase.route('/_adminSaveSettings', methods=['PUT'])
@flask_login.login_required
def adminSaveSettings():
    '''save admin-settings'''
    user = flask_login.current_user.id
    if flask_login.current_user.id != settings.get('admin'):
        return '405 not allowed'
    s = request.json
    for key in s:
        settings.set(key, s[key])
    return 'Success!'

@MemberBase.route('/manage', methods=['GET'])
@flask_login.login_required
def manage():
    '''show manager-page'''
    user = flask_login.current_user.id
    if flask_login.current_user.id != settings.get('admin'):
        return '405 not allowed'
    db = dbio.MbDb(dbfile)
    members = db.getMembers()
    msJson = json.dumps(members, indent=2)
    return render_template('manage.html', relroot='./', authuser=flask_login.current_user.id, msJson=msJson)

@MemberBase.route('/manage/<mid>', methods=['GET'])
@flask_login.login_required
def manageMember(mid):
    '''show member-management-page'''
    user = flask_login.current_user.id
    if flask_login.current_user.id != settings.get('admin'):# TODO: allow for management-users
        return '405 not allowed'
    db = dbio.MbDb(dbfile)
    member = db.getMember(mid)
    mJson = json.dumps(member, indent=2)
    return render_template('manageMember.html', relroot='../', authuser=flask_login.current_user.id, mJson=mJson)

@MemberBase.route('/member/<mid>', methods=['GET'])
def member(mid):
    '''show member-page'''
    if len(mid)!=19 and len(mid)!=29 and len(mid)!=39:
        return '404'
    db = dbio.MbDb(dbfile)
    member = db.getMember(mid)
    if flask_login.current_user.is_anonymous:
        user = '[private URL]'
    else:
        user = flask_login.current_user.id
    mJson = json.dumps(member)
    return render_template('member.html', relroot='../', authuser=user, mJson=mJson, magazine_name=settings.get('magazine_name'))

@MemberBase.route('/member', methods=['POST'])
def memberNew():
    # TODO
    '''create a new member'''
    pass

@MemberBase.route('/member/<mid>', methods=['PUT'])
def memberUpdate(mid):
    '''update a member'''
    m = request.json
    db = dbio.MbDb(dbfile)
    result = db.updateMember(flask_login.current_user.id, m)
    return result

@MemberBase.route('/_csvImport', methods=['GET'])
@flask_login.login_required
def csvImport():
    if flask_login.current_user.is_anonymous or flask_login.current_user.id != settings.get("admin"):
        return render_template("error.html", relroot="./", title='403: not allowed', text=""), 403
    return render_template("csvImport.html", relroot="./", loginuser='admin')

@MemberBase.route('/_csvImport', methods=['POST'])
@flask_login.login_required
def csvImportPost():
    if flask_login.current_user.is_anonymous or flask_login.current_user.id != settings.get("admin"):
        return render_template("error.html", relroot="./", title='403: not allowed', text=""), 403
    try:
        csvfile = request.files["file"].read().decode()
    except:
        return 'ERROR reading CSV-file!'
    db = dbio.MbDb(dbfile)
    data = csv.reader(csvfile.splitlines(), delimiter=',', quotechar='"')
    linecount = 0
    importcount = 0
    for row in data:
        if linecount == 0:
            if ','.join(row) != 'family_name,given_name,date_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,email,phone,mobile,iban,bic,join_date,note_public,note_manager':
                return 'ERROR: Wrong title line, please read CAREFULLY what to do here and what can go wrong!'
            linecount += 1
            continue
        db_res = db.addMember(family_name=row[0],given_name=row[1],date_of_birth=row[2],birth_name=row[3],title=row[4],call_name=row[5],sex=row[6],street=row[7],street_number=row[8],appartment=row[9],postal_code=row[10],city=row[11],state=row[12],country=row[13],email=row[14],phone=row[15],mobile=row[16],iban=row[17],bic=row[18],join_date=row[19],note_public=row[20],note_manager=row[21])
        if db_res != False:
            importcount += 1
        linecount += 1
    #db.addData(flask_login.current_user.id, d['text'])
    return 'TODO ('+str(linecount)+' Zeilen gelesen, '+str(importcount)+' importiert)'

@MemberBase.route('/_delete/<did>', methods=['DELETE'])
@flask_login.login_required
def delete(wid):
    # TODO
    '''delete data'''
    db = dbio.PwDb(dbfile)
    db.deleteWord(did)
    return 'ok'

# run it:

if __name__ == "__main__":
    MemberBase.run(host=host, debug=debug)

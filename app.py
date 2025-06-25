#!/usr/bin/python3
#coding: utf-8
'''
Base file of MemberBase
'''

import os
import sqlite3
from flask import Flask, render_template, request, send_from_directory, make_response, jsonify, send_file
from flask import url_for, redirect
import flask_login
import json
import csv, io
from jinja2 import Template
from modules import dbio, settingsIo
from datetime import datetime, timedelta
from markdown import markdown as md2html

# global settings:

settingsfile = 'MemberBase.conf'

settings = settingsIo.settingsIo(settingsfile)
dbfile = settings.get('dbfile')
host = settings.get('host')
port = settings.get('port')
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
    if username == settings.get('admin'):
        user = User()
        user.id = username
        return user
    db = dbio.MbDb(dbfile)
    mid = db.getMidFromMail(username)
    if mid != None:
        user = User()
        user.id = username
        return user
    return

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    password = request.form.get('password')
    user = User()
    user.id = username
    db = dbio.MbDb(dbfile)
    if username == settings.get('admin'):
        user.is_authenticated = settings.checkPw(password)
    elif db.getMidFromMail('username') != None:
        user.is_authenticated = db.checkPasswd(username, password)
    if user.is_authenticated:
        return user
    return

# routes

@MemberBase.route('/', methods=['GET'])
def index():
    '''show index-page'''
    if settings.get('admin') == '':
        return redirect('_init')
    elif flask_login.current_user.is_anonymous or flask_login.current_user.id==None:
        return render_template('index.html', relroot='./', organame=settings.get('organame'))
    elif flask_login.current_user.id == settings.get('admin'):
        return redirect('admin')
    else:
        db = dbio.MbDb(dbfile)
        mid = db.getMidFromMail(flask_login.current_user.id)
        return redirect('member/'+mid)

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
    db = dbio.MbDb(dbfile)
    mid = db.getMidFromMail(username)
    if mid != None:
        db = dbio.MbDb(dbfile)
        user = User()
        user.id = username
        flask_login.login_user(user)
        return redirect('member/'+db.getMidFromMail(username))
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
    members = db.getMembers('')
    msJson = json.dumps(members, indent=2)
    groups = db.getGroups()
    gJson = json.dumps(groups, indent=2)
    return render_template('admin.html', relroot='./', 
            authuser=flask_login.current_user.id, sJson=sJson, 
            msJson=msJson, gJson=gJson, 
            privacy_declaration = settings.get('privacy_declaration'))

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
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return '405 not allowed'
    states = settings.get('states')
    statesJson = json.dumps(states)
    return render_template('manage.html', relroot='./', authuser=flask_login.current_user.id, statesJson=statesJson)

@MemberBase.route('/manageList/<state>', methods=['GET'])
@flask_login.login_required
def manageList(state):
    '''show member-lists for management according to state'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return '405 not allowed'
    members = db.getMembers(state)
    msJson = json.dumps(members, indent=2)
    return render_template('manageList.html', relroot='../', authuser=flask_login.current_user.id, msJson=msJson, magazine_name=settings.get('magazine_name'), state=state)

@MemberBase.route('/manage/<mid>', methods=['GET'])
@flask_login.login_required
def manageMember(mid):
    '''show member-management-page'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return '405 not allowed'
    member = db.getMemberFull(mid)
    mJson = json.dumps(member, indent=2)
    return render_template('manageMember.html', relroot='../', authuser=flask_login.current_user.id, mJson=mJson, states=json.dumps(settings.get('states')))

@MemberBase.route('/member/<mid>', methods=['GET'])
def member(mid):
    '''show member-page'''
    if len(mid)!=19 and len(mid)!=29 and len(mid)!=39:
        return '404'
    db = dbio.MbDb(dbfile)
    member = db.getMember(mid)
    if member == None:
        return 404
    elif len(mid)==19 or len(mid)==29:
        return redirect('./'+member['mid'])
    if flask_login.current_user.is_anonymous or flask_login.current_user.id == None:
        if db.checkPasswdSet(mid):
            return redirect('../')
        else:
            user = '[private URL]'
    else:
        user = flask_login.current_user.id
    mJson = json.dumps(member)
    if flask_login.current_user.id == settings.get('admin'):
        groups = ['management']
    else:
        groups = db.getGroups(mid)
    gJson = json.dumps(groups)
    geos = db.getGeos()
    geoJson = json.dumps(geos)
    manager = db.checkManager(user)
    privDec = md2html(settings.get('privacy_declaration'))
    return render_template('member.html', relroot='../', authuser=user, manager=manager, 
            mJson=mJson, gJson=gJson, magazine_name=settings.get('magazine_name'),
            privacy_declaration=privDec, geoJson=geoJson)

@MemberBase.route('/addMember', methods=['GET'])
@flask_login.login_required
def addMember():
    '''page to create a new member'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return render_template("error.html", relroot="./", title='403: not allowed', text=""), 403
    return render_template("addMember.html", relroot="./", authuser=flask_login.current_user.id, states=json.dumps(settings.get('states')))

@MemberBase.route('/addMember', methods=['PUT'])
@flask_login.login_required
def addMemberPut():
    '''create a new member'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return render_template("error.html", relroot="./", title='403: not allowed', text=""), 403
    m = request.json
    mid = db.addMember(family_name=m['family_name'],given_name=m['given_name'],date_of_birth=m['date_of_birth'])
    return(mid)    

@MemberBase.route('/member/<mid>', methods=['PUT'])
@flask_login.login_required
def memberUpdate(mid):
    '''update a member'''
    if flask_login.current_user.is_anonymous:
        return render_template("error.html", relroot="./", title='403: not allowed', text=""), 403
    m = request.json
    db = dbio.MbDb(dbfile)
    result = db.updateMember(flask_login.current_user.id, request.remote_addr, m)
    return result

@MemberBase.route('/memberAdmin/<mid>', methods=['PUT'])
@flask_login.login_required
def memberUpdateAdmin(mid):
    '''update a member as admin or manager'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return render_template("error.html", relroot="./", title='403: not allowed', text=""), 403
    m = request.json
    result = db.updateMemberFull(flask_login.current_user.id, request.remote_addr, m)
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
    data = csv.reader(csvfile.splitlines(), delimiter=';', quotechar='"')
    linecount = 0
    importcount = 0
    for row in data:
        if linecount == 0:
            if ','.join(row) != 'family_name,given_name,date_of_birth,place_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,email,phone,mobile,iban,bic,join_date,status,note_public,note_manager':
                return 'ERROR: Wrong title line, please read CAREFULLY what to do here and what can go wrong!'
            linecount += 1
            continue
        db_res = db.addMember(family_name=row[0],given_name=row[1],date_of_birth=row[2],place_of_birth[3],birth_name=row[4],title=row[5],call_name=row[6],sex=row[7],street=row[8],street_number=row[9],appartment=row[10],postal_code=row[11],city=row[12],state=row[13],country=row[14],email=row[15],phone=row[16],mobile=row[17],iban=row[18],bic=row[19],join_date=row[20],status=row[21],note_public=row[22],note_manager=row[23])
        if db_res != False:
            importcount += 1
        linecount += 1
    #db.addData(flask_login.current_user.id, d['text'])
    return 'TODO ('+str(linecount)+' Zeilen gelesen, '+str(importcount)+' importiert)'

@MemberBase.route('/group/<gid>', methods=['GET'])
@flask_login.login_required
def group(gid):
    '''show group'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return '405 not allowed'
    gname = db.getGroupName(gid)
    gmembers = db.getMembers(status='', gid=gid)
    gNmembers = db.getNotMembers(gid)
    gmJson = json.dumps(gmembers, indent=2)
    gnmJson = json.dumps(gNmembers, indent=2)
    return render_template('group.html', relroot='../', authuser=flask_login.current_user.id, gmJson=gmJson, gnmJson=gnmJson, gname=gname, gid=gid)

@MemberBase.route('/group/addMember', methods=['PUT'])
@flask_login.login_required
def groupAddMember():
    '''show group'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return '405 not allowed'
    job = request.json
    db.addGroupMember(job['gid'], job['addMember'])
    return 'ok'

@MemberBase.route('/log/<dataset>', methods=['GET'])
@flask_login.login_required
def log(dataset = ''):
    '''show log'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return '405 not allowed'
    log = db.getLog(dataset)
    logJson = json.dumps(log, indent=2)
    return render_template('log.html', relroot='../', authuser=flask_login.current_user.id, logJson=logJson, dataset=dataset)

@MemberBase.route('/csvExport/<selection>', methods=['GET'])
@flask_login.login_required
def csvExport(selection):
    '''exports members as csvfile according to the selection'''
    user = flask_login.current_user.id
    db = dbio.MbDb(dbfile)
    if flask_login.current_user.id != settings.get('admin') and not db.checkManager(user):
        return '405 not allowed'
    sel = selection.split('_')
    if sel[0] == 'mail':
        csvfile = db.csvExportMail(sel[1])
    elif sel[0] == 'addr':
        csvfile = db.csvExportAddr(sel[1])
    elif sel[0] == 'addr':
        csvfile = db.csvExportAddr(sel[1])
    else:
        return '404 not found'
    mem = io.BytesIO()
    mem.write(csvfile.getvalue().encode())
    mem.seek(0)
    return send_file(
            mem,
            download_name=f"" + datetime.now().strftime('%Y/%m/%d')+'_MemberList_'+selection+'.csv',
            as_attachment=True,
            mimetype='text/csv',
            )

@MemberBase.route('/_deleteMember/<mid>', methods=['DELETE'])
@flask_login.login_required
def deleteMember(mid):
    # TODO
    '''delete member'''
    db = dbio.MbDb(dbfile)
    res = db.deleteMember(flask_login.current_user.id, request.remote_addr, mid)
    return res

# run it:

if __name__ == "__main__":
    MemberBase.run(host=host, debug=debug)

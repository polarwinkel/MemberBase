#!/usr/bin/python3
'''
Database-IO-file
'''

import sqlite3, json
import os
from modules import dbInit
from datetime import datetime
import hashlib, uuid
import io
import huuid

class MbDb:
    ''' Database-Connection '''
    def __init__(self, dbfile):
        if not os.path.exists(dbfile):
            connection = sqlite3.connect(dbfile)
            cursor = connection.cursor()
            # activate support for foreign keys in SQLite:
            sql_command = 'PRAGMA foreign_keys = ON;'
            cursor.execute(sql_command)
            connection.commit()
            connection.close()
        self._connection = sqlite3.connect(dbfile) # _x = potected, __ would be private
        dbInit.checkTables(self)
    
    def reloadDb(self, dbfile):
        '''reloads the database file, i.e. after external changes/sync'''
        self._connection.commit() # not necessary, just to be sure
        self._connection.close()
        self._connection = sqlite3.connect(dbfile)
    
    def checkMember(self, family_name, given_name, date_of_birth):
        '''checks if a member exists, returning mid or False'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT mid FROM members 
                WHERE family_name=? AND given_name=? AND date_of_birth=?'''
        cursor.execute(sqlTemplate, (family_name, given_name, date_of_birth))
        mid = cursor.fetchone()
        return mid
    
    def addMember(self, family_name,given_name,date_of_birth,birth_name='',title='',call_name='',sex='',street='',street_number='',appartment='',postal_code='',city='',state='',country='',email='',phone='',mobile='',iban='',bic='',join_date='',status='',note_public='',note_manager=''):
        '''adds a new member, returning its mid (or False if exists)'''
        if self.checkMember(family_name, given_name, date_of_birth) is not None:
            return False
        mid = huuid.new()
        # TODO: check if one with first 32bit exists already
        cursor = self._connection.cursor()
        sqlTemplate = '''INSERT INTO members (mid,family_name,given_name,date_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,email,phone,mobile,iban,bic,join_date,status,note_public,note_manager)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''
        cursor.execute(sqlTemplate, (mid,family_name,given_name,date_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,email,phone,mobile,iban,bic,join_date,status,note_public,note_manager))
        self._connection.commit()
        sqlTemplate = '''SELECT mid FROM members 
                WHERE family_name=? AND given_name=? AND date_of_birth=?'''
        cursor.execute(sqlTemplate, (family_name, given_name, date_of_birth))
        mid = cursor.fetchone()[0]
        sqlTemplate = '''UPDATE members SET last_update = CURRENT_TIMESTAMP 
                WHERE mid=?;'''
        cursor.execute(sqlTemplate, (mid, ))
        self._connection.commit()
        return mid
    
    def getMember(self, mid):
        '''returns most information of a member'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT mid, family_name,given_name,date_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,geo_lat,geo_lon,email,phone,mobile,iban,bic,join_date,status,privacy_accepted,allow_debit,email_newsletter,email_protocols,email_magazine,allow_images_public,privacy_accepted,allow_address_internal,note_public,note_manager,last_update
                FROM members WHERE mid LIKE ?'''
        cursor.execute(sqlTemplate, (mid+'%', ))
        m = cursor.fetchone()
        self._connection.commit()
        if m is None:
            return None
        result = {
                'mid'                   : m[0],
                'family_name'           : m[1],
                'given_name'            : m[2],
                'date_of_birth'         : m[3],
                'birth_name'            : m[4],
                'title'                 : m[5],
                'call_name'             : m[6],
                'sex'                   : m[7],
                'street'                : m[8],
                'street_number'         : m[9],
                'appartment'            : m[10],
                'postal_code'           : m[11],
                'city'                  : m[12],
                'state'                 : m[13],
                'country'               : m[14],
                'geo_lat'               : m[15],
                'geo_lon'               : m[16],
                'email'                 : m[17],
                'phone'                 : m[18],
                'mobile'                : m[19],
                'iban'                  : m[20],
                'bic'                   : m[21],
                'join_date'             : m[22],
                'status'                : m[23],
                'privacy_accepted'      : m[24],
                'allow_debit'           : m[25],
                'email_newsletter'      : m[26],
                'email_protocols'       : m[27],
                'email_magazine'        : m[28],
                'allow_images_public'   : m[29],
                'privacy_accepted'      : m[30],
                'allow_address_internal': m[31],
                'note_public'           : m[32],
                'note_manager'          : m[33],
                'last_update'           : m[34]
                }
        return result
    
    def getMemberFull(self, mid):
        '''returns all information of a member'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT * FROM members WHERE mid LIKE ?'''
        cursor.execute(sqlTemplate, (mid+'%', ))
        m = cursor.fetchone()
        self._connection.commit()
        if m is None:
            return None
        result = {}
        keys = list(map(lambda x: x[0], cursor.description))
        for k in keys:
            result[k] = m[keys.index(k)]
        return result
    
    def updateMember(self, user, ip, m):
        # TODO: update all options
        '''update a member'''
        if m['email_newsletter']=='on':
            m['email_newsletter']=1
        else:
            m['email_newsletter']=0
        if m['email_protocols']=='on':
            m['email_protocols']=1
        else:
            m['email_protocols']=0
        if m['email_magazine']=='on':
            m['email_magazine']=1
        else:
            m['email_magazine']=0
        if m['privacy_accepted']=='on':
            m['privacy_accepted']=1
        else:
            m['privacy_accepted']=0
        if m['allow_address_internal']=='on':
            m['allow_address_internal']=1
        else:
            m['allow_address_internal']=0
        cursor = self._connection.cursor()
        # log:
        mOld = self.getMember(m['mid'])
        old = {}
        new = {}
        for key in m:
            if key in mOld.keys() and mOld[key] != m[key]:
                old[key] = mOld[key]
                new[key] = m[key]
        address = 0
        email = 0
        payment = 0
        for key in new:
            if key in ['family_name','given_name','title','street','street_number','appartment','postal_code','city','state','country']:
                address = 1
            if key == 'email':
                email = 1
            if key in ['iban','bic','allow_debit']:
                payment = 1
        sqlTemplate = '''INSERT INTO log 
                (timestamp,changed_mid,user_mid,remote_ip,address,email,payment,old_data,new_data)
                VALUES (CURRENT_TIMESTAMP,?,?,?,?,?,?,?,?)'''
        mOld = cursor.fetchone()
        cursor.execute(sqlTemplate, (m['mid'],self.getMidFromMail(user),ip,address,email,payment,str(old),str(new)))
        # update:
        sqlTemplate = '''UPDATE members SET title = ?, call_name = ?, 
                street=?, street_number=?, appartment=?, postal_code=?, city=?, 
                email_newsletter=?, email_protocols=?, email_magazine=?, 
                privacy_accepted=?, allow_address_internal=?, geo_lat=?, geo_lon=?
                WHERE mid=?'''
        cursor.execute(sqlTemplate, (m['title'], m['call_name'], m['street'], m['street_number'], 
                m['appartment'], m['postal_code'], m['city'], 
                m['email_newsletter'], m['email_protocols'], m['email_magazine'], 
                m['privacy_accepted'], m['allow_address_internal'], m['geo_lat'], m['geo_lon'], 
                m['mid']))
        if len(m['password'])>=10:
            salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512(m['password'].encode('utf-8') + salt.encode('utf-8')).hexdigest()
            sqlTemplate = '''UPDATE members SET pwsalt=?, pwhash=? WHERE mid=?'''
            cursor.execute(sqlTemplate, (salt, hashed_password, m['mid']))
        # TODO: add log entry
        self._connection.commit()
        return('ok')
    
    def getMidFromMail(self, email):
        '''returns a member-id to an eMail-address'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT mid FROM members WHERE email=?'''
        cursor.execute(sqlTemplate, (email, ))
        result = cursor.fetchone()
        self._connection.commit()
        if result != None:
            return result[0]
        return None
    
    def getGroupName(self, gid):
        '''returns the name of a group'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT group_name FROM groups WHERE gid=?'''
        cursor.execute(sqlTemplate, (gid, ))
        res = cursor.fetchone()
        self._connection.commit()
        if res is None:
            return None
        return res[0]
    
    def getGroups(self, mid=''):
        '''returns a list of all groups [of a member]'''
        cursor = self._connection.cursor()
        if mid=='':
            sqlTemplate = '''SELECT gid, group_name FROM groups'''
            cursor.execute(sqlTemplate, )
        else:
            sqlTemplate = '''SELECT groups.gid, groups.group_name FROM groups JOIN group_members
                    ON groups.gid = group_members.gid WHERE group_members.mid=?'''
            cursor.execute(sqlTemplate, (mid, ))
        tup = cursor.fetchall()
        self._connection.commit()
        if tup is None:
            return None
        result = []
        for t in tup:
            result.append({
                    'gid'           : t[0],
                    'group_name'    : t[1]
                })
        return result
    
    def getMembers(self, gid=''):
        '''returns a list of all members [with a certain group]'''
        cursor = self._connection.cursor()
        if gid=='':
            sqlTemplate = '''SELECT mid, family_name, given_name, date_of_birth FROM members'''
            cursor.execute(sqlTemplate, )
        else:
            sqlTemplate = '''SELECT members.mid, members.family_name, members.given_name, members.date_of_birth 
                    FROM members JOIN group_members ON members.mid=group_members.mid
                    WHERE gid=?'''
            cursor.execute(sqlTemplate, (gid, ))
        tup = cursor.fetchall()
        self._connection.commit()
        if tup is None:
            return None
        result = []
        for t in tup:
            result.append({
                    'mid'           : t[0],
                    'family_name'   : t[1],
                    'given_name'    : t[2],
                    'date_of_birth' : t[3]
                })
        return result
    
    def getGeos(self):
        '''returns a list of all allowed member-locations'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT given_name, call_name, geo_lat, geo_lon FROM members
                WHERE geo_lat NOT NULL AND allow_address_internal=1'''
        cursor.execute(sqlTemplate, )
        tup = cursor.fetchall()
        self._connection.commit()
        if tup is None:
            return None
        result = []
        for t in tup:
            m = {
                    'name'      : t[0],
                    'geo_lat'   : t[2],
                    'geo_lon'   : t[3]
                }
            if t[1] != '':
                m['name'] = t[1]
            result.append(m)
        return result
    
    def getNotMembers(self, gid):
        '''returns a list of all non-members of a group'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT mid, family_name, given_name, date_of_birth
                FROM members WHERE mid NOT IN
                (SELECT mid FROM group_members WHERE gid=?)
                ORDER BY family_name, given_name'''
        cursor.execute(sqlTemplate, (gid, ))
        tup = cursor.fetchall()
        self._connection.commit()
        if tup is None:
            return None
        result = []
        for t in tup:
            result.append({
                    'mid'           : t[0],
                    'family_name'   : t[1],
                    'given_name'    : t[2],
                    'date_of_birth' : t[3]
                })
        return result
    
    def addGroupMember(self, gid, mid):
        '''adds a member to a group'''
        cursor = self._connection.cursor()
        sqlTemplate = '''INSERT INTO group_members (gid, mid)
                VALUES (?, ?)'''
        cursor.execute(sqlTemplate, (gid, mid))
        self._connection.commit()
        return 'ok'
    
    def checkManager(self, user):
        '''check if a user-id (eMail) is member of group manager'''
        mid = self.getMidFromMail(user)
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT group_members.mid FROM group_members JOIN groups 
                ON group_members.gid=groups.gid 
                WHERE groups.group_name='management' and group_members.mid=?'''
        cursor.execute(sqlTemplate, (mid, ))
        res = cursor.fetchone()
        if res == None:
            return False
        return True
    
    def checkPasswdSet(self, mid):
        '''checks if a password is set for a user (short-mid allowed)'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT pwhash FROM members WHERE mid LIKE ?'''
        cursor.execute(sqlTemplate, (mid+'%', ))
        u = cursor.fetchone()
        self._connection.commit()
        if u[0] == None:
            return False
        return True
        
    def csvExportMail(self, sel):
        '''export member-list according to the selection'''
        cursor = self._connection.cursor()
        if sel == 'n':
            where = 'WHERE email_newsletter=1'
        if sel == 'p':
            where = 'WHERE email_protocols=1'
        elif sel == 'm':
            where = 'WHERE email_magazine=1'
        sqlTemplate = '''SELECT family_name, given_name, title, sex, email
                FROM members {where} ORDER BY
                REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                family_name,'ä','ae'),'ö','oe'),'ü','ue'),'Ä','Ae'),'Ö','Oe'),'Ü','Ue'),'ß','ss'), 
                REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                given_name,'ä','ae'),'ö','oe'),'ü','ue'),'Ä','Ae'),'Ö','Oe'),'Ü','Ue'),'ß','ss') '''.format(where=where)
        cursor.execute(sqlTemplate)
        mlist = cursor.fetchall()
        f = io.StringIO() # init-value would leave the cursor at beginning
        f.write('family_name,given_name,title,sex,email,\n')
        for m in mlist:
            cstr = m[0]+','+m[1]+','+m[2]+','+m[3]+','+m[4]+',\n'
            f.write(cstr)
        f.seek(0) # get cursor to beginning
        return f
    
    def csvExportAddr(self, sel):
        '''export member-list according to the selection'''
        cursor = self._connection.cursor()
        if sel == 'p':
            where = 'WHERE email_protocols=0 OR email_protocols IS NULL'
        elif sel == 'm':
            where = 'WHERE email_magazine=0 OR email_magazine IS NULL'
        elif sel == 'pm':
            where = 'WHERE email_protocols=0 OR email_protocols IS NULL OR email_magazine=0 OR email_magazine IS NULL'
        sqlTemplate = '''SELECT family_name, given_name, title, sex, street, street_number, appartment, postal_code, city, country
                FROM members {where} ORDER BY
                REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                family_name,'ä','ae'),'ö','oe'),'ü','ue'),'Ä','Ae'),'Ö','Oe'),'Ü','Ue'),'ß','ss'), 
                REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                given_name,'ä','ae'),'ö','oe'),'ü','ue'),'Ä','Ae'),'Ö','Oe'),'Ü','Ue'),'ß','ss') '''.format(where=where)
        cursor.execute(sqlTemplate)
        mlist = cursor.fetchall()
        f = io.StringIO()
        f.write('family_name,given_name,title,sex,street,street_number,appartment,postal_code,city,country,\n')
        for m in mlist:
            cstr = m[0]+','+m[1]+','+m[2]+','+m[3]+','+m[4]+','+m[5]+','+m[6]+','+m[7]+','+m[8]+','+m[9]+',\n'
            f.write(cstr)
        f.seek(0) # get cursor to beginning
        return f
    
    def checkPasswd(self, email, passwd):
        '''checks a password for an email'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT pwhash, pwsalt FROM members WHERE email=?'''
        cursor.execute(sqlTemplate, (email, ))
        u = cursor.fetchone()
        self._connection.commit()
        if u == None:
            return False
        hashed = hashlib.sha512(passwd.encode('utf-8') + u[1].encode('utf-8')).hexdigest()
        return u[0] == hashed
    
    def getLog(self, dataset=''):
        '''get the last 1000 log-entries'''
        cursor = self._connection.cursor()
        if dataset=='all':
            sqlTemplate = '''SELECT 
                    timestamp, changed_mid, user_mid, family_name, given_name, 
                    remote_ip, old_data, new_data 
                    FROM log JOIN members ON log.changed_mid=members.mid
                    ORDER BY timestamp DESC LIMIT 1000'''
        elif dataset=='address':
            sqlTemplate = '''SELECT 
                    timestamp, changed_mid, user_mid, family_name, given_name,
                    remote_ip, old_data, new_data 
                    FROM log JOIN members ON log.changed_mid=members.mid
                    WHERE log.address == 1
                    ORDER BY timestamp DESC LIMIT 1000'''
        cursor.execute(sqlTemplate, )
        tup = cursor.fetchall()
        self._connection.commit()
        log = []
        for l in tup:
            log.append({
                    'timestamp'     : l[0],
                    'changed_mid'   : l[1],
                    'user_mid'      : l[2],
                    'family_name'   : l[3],
                    'given_name'    : l[4],
                    'remote_ip'     : l[5],
                    'old_data'      : l[6],
                    'new_data'      : l[7]
                })
        return log
    
    def deleteMember(self, mid):
        '''delete a member'''
        cursor = self._connection.cursor()
        sqlTemplate = '''DELETE FROM group_members WHERE mid=?;'''
        cursor.execute(sqlTemplate, (mid))
        sqlTemplate = '''DELETE FROM members WHERE mid=?;'''
        cursor.execute(sqlTemplate, (mid))
        self._connection.commit()
    

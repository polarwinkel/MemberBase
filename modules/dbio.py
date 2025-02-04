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
    
    def addMember(self, family_name,given_name,date_of_birth,birth_name='',title='',call_name='',sex='',street='',street_number='',appartment='',postal_code='',city='',state='',country='',email='',phone='',mobile='',iban='',bic='',join_date='',note_public='',note_manager=''):
        '''adds a new member, returning its mid (or False if exists)'''
        if self.checkMember(family_name, given_name, date_of_birth) is not None:
            return False
        mid = huuid.new()
        # TODO: check if one with first 32bit exists already
        cursor = self._connection.cursor()
        sqlTemplate = '''INSERT INTO members (mid,family_name,given_name,date_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,email,phone,mobile,iban,bic,join_date,note_public,note_manager)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''
        cursor.execute(sqlTemplate, (mid,family_name,given_name,date_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,email,phone,mobile,iban,bic,join_date,note_public,note_manager))
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
        sqlTemplate = '''SELECT family_name,given_name,date_of_birth,birth_name,title,call_name,sex,street,street_number,appartment,postal_code,city,state,country,geo_lat,geo_lon,email,phone,mobile,iban,bic,join_date,allow_debit,email_newsletter,email_protocols,email_magazine,allow_images_public,allow_address_internal,note_public,note_manager,last_update
                FROM members WHERE mid LIKE ?'''
        cursor.execute(sqlTemplate, (mid+'%', ))
        tup = cursor.fetchall()
        self._connection.commit()
        if tup is None:
            return None
        result = []
        for t in tup:
            result.append({
                    'mid'                   : mid,
                    'family_name'           : t[0],
                    'given_name'            : t[1],
                    'date_of_birth'         : t[2],
                    'birth_name'            : t[3],
                    'title'                 : t[4],
                    'call_name'             : t[5],
                    'sex'                   : t[6],
                    'street'                : t[7],
                    'street_number'         : t[8],
                    'appartment'            : t[9],
                    'postal_code'           : t[10],
                    'city'                  : t[11],
                    'state'                 : t[12],
                    'country'               : t[13],
                    'geo_lat'               : t[14],
                    'geo_lon'               : t[15],
                    'email'                 : t[16],
                    'phone'                 : t[17],
                    'mobile'                : t[18],
                    'iban'                  : t[19],
                    'bic'                   : t[20],
                    'join_date'             : t[21],
                    'allow_debit'           : t[22],
                    'email_newsletter'      : t[23],
                    'email_protocols'       : t[24],
                    'email_magazine'        : t[25],
                    'allow_images_public'   : t[26],
                    'allow_address_internal': t[27],
                    'note_public'           : t[28],
                    'note_manager'          : t[29],
                    'last_update'           : t[30]
                })
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
        if m['allow_address_internal']=='on':
            m['allow_address_internal']=1
        else:
            m['allow_address_internal']=0
        cursor = self._connection.cursor()
        # log:
        sqlTemplate = '''SELECT * FROM members WHERE mid=?'''
        cursor.execute(sqlTemplate, (m['mid'], ))
        # TODO: log only changes; set 'address' to True if address changed
        sqlTemplate = '''INSERT INTO log 
                (timestamp,changed_mid,user_mid,remote_ip,old_data,new_data)
                VALUES (CURRENT_TIMESTAMP,?,?,?,?,?)'''
        mOld = cursor.fetchone()
        cursor.execute(sqlTemplate, (m['mid'],self.getMidFromMail(user),ip,str(mOld),str(m)))
        # update:
        sqlTemplate = '''UPDATE members SET street=?, street_number=?, 
                appartment=?, postal_code=?, city=?, 
                email_newsletter=?, email_protocols=?, email_magazine=?, 
                allow_address_internal=?, geo_lat=?, geo_lon=?
                WHERE mid=?'''
        cursor.execute(sqlTemplate, (m['street'], m['street_number'], 
                m['appartment'], m['postal_code'], m['city'], 
                m['email_newsletter'], m['email_protocols'], m['email_magazine'], 
                m['allow_address_internal'], m['geo_lat'], m['geo_lon'], 
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
        sqlTemplate = '''SELECT given_name, geo_lat, geo_lon FROM members
                WHERE geo_lat NOT NULL AND allow_address_internal=1'''
        cursor.execute(sqlTemplate, )
        tup = cursor.fetchall()
        self._connection.commit()
        if tup is None:
            return None
        result = []
        for t in tup:
            result.append({
                    'given_name'    : t[0],
                    'geo_lat'       : t[1],
                    'geo_lon'       : t[2]
                })
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
    
    def getLog(self):
        '''get the last 1000 log-entries'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT * FROM log'''
        cursor.execute(sqlTemplate, )
        res = cursor.fetchall()
        self._connection.commit()
        return res
    
    def deleteMember(self, mid):
        '''delete a member'''
        cursor = self._connection.cursor()
        sqlTemplate = '''DELETE FROM group_members WHERE mid=?;'''
        cursor.execute(sqlTemplate, (mid))
        sqlTemplate = '''DELETE FROM members WHERE mid=?;'''
        cursor.execute(sqlTemplate, (mid))
        self._connection.commit()
    

#!/usr/bin/python3
'''
Database-IO-file
'''

import sqlite3, json
import os
from modules import dbInit
from datetime import datetime
import hashlib, uuid
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
    
    def updateMember(self, user, m):
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
        cursor = self._connection.cursor()
        sqlTemplate = '''UPDATE members SET street=?, street_number=?, 
                appartment=?, postal_code=?, city=?, 
                email_newsletter=?, email_protocols=?, email_magazine=?
                WHERE mid=?'''
        cursor.execute(sqlTemplate, (m['street'], m['street_number'], 
                m['appartment'], m['postal_code'], m['city'], 
                m['email_newsletter'], m['email_protocols'], m['email_magazine'], m['mid']))
        if len(m['password'])>=10:
            salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512(m['password'].encode('utf-8') + salt.encode('utf-8')).hexdigest()
            sqlTemplate = '''UPDATE members SET pwsalt=?, pwhash=? WHERE mid=?'''
            cursor.execute(sqlTemplate, (salt, hashed_password, m['mid']))
        # TODO: add log entry
        self._connection.commit()
        return('ok')
    
    def getMidFromMail(self, email):
        '''returns a mid to an eMail-address'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT mid FROM members WHERE email=?'''
        cursor.execute(sqlTemplate, (email, ))
        result = cursor.fetchone()
        self._connection.commit()
        if result != None:
            return result[0]
        return None
    
    def getGroups(self, mid=''):
        '''returns a list of all groups a member has'''
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
        
    def checkPasswd(self, email, passwd):
        '''checks a password for a email'''
        cursor = self._connection.cursor()
        sqlTemplate = '''SELECT pwhash, pwsalt FROM members WHERE email=?'''
        cursor.execute(sqlTemplate, (email, ))
        u = cursor.fetchone()
        self._connection.commit()
        if u == None:
            return False
        hashed = hashlib.sha512(passwd.encode('utf-8') + u[1].encode('utf-8')).hexdigest()
        return u[0] == hashed
        
    def deleteMember(self, mid):
        cursor = self._connection.cursor()
        sqlTemplate = '''DELETE FROM data WHERE did=?;'''
        cursor.execute(sqlTemplate, (did))
        self._connection.commit()
    

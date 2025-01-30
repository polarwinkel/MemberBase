#!/usr/bin/python3
'''
Settings-IO-file
'''

import yaml, os, json
import hashlib, uuid

class settingsIo:
    def __init__(self, sfile):
        if not os.path.exists(sfile):
            s = {}
            s['dbfile'] = 'MemberBase.sqlite3'
            s['host'] = '0.0.0.0'
            s['port'] = '4208'
            s['debug'] = True
            s['organame'] = 'society'
            s['magazine_name'] = 'magazine'
            s['admin']=''
            s['secret_key']=uuid.uuid4().hex
            # extensions to be used by python-markdown:
            with open(sfile, 'w') as file:
                yaml.dump(s, file)
        with open(sfile) as file:
            self.sfile = sfile
            self.s = yaml.full_load(file)
            #self.s = yaml.safe_load(file) #deprecated
    
    def get(self, key):
        '''returns the value to a settings key'''
        if key=='dbfile':
            return self.s['dbfile']
        elif key=='host':
            return self.s['host']
        elif key=='port':
            return self.s['port']
        elif key=='debug':
            return self.s['debug']
        elif key=='organame':
            return self.s['organame']
        elif key=='magazine_name':
            return self.s['magazine_name']
        elif key=='admin':
            return self.s['admin']
        elif key=='secret_key':
            return self.s['secret_key']
        else:
            raise NameError('settings not found for '+str(key))
    
    def checkPw(self, password):
        '''check password'''
        hashed = hashlib.sha512(password.encode('utf-8') + self.s['salt'].encode('utf-8')).hexdigest()
        return self.s['password'] == hashed
    
    def set(self, key, value):
        '''writes new settings to the settings-file'''
        # TODO: integrity-check
        if key == 'password':
            import hashlib, uuid
            salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512(value.encode('utf-8') + salt.encode('utf-8')).hexdigest()
            self.s['salt'] = salt
            self.s['password'] = hashed_password
        else:
            self.s[key] = value
        with open(self.sfile, 'w') as f:
            yaml.dump(self.s, f)
        with open(self.sfile) as f:
            self.s = yaml.full_load(f)
            #self.s = yaml.safe_load(f) #deprecated
    
    def getJson(self):
        '''returns settings as json-string'''
        return json.dumps(self.s)

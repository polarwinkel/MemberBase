#!/usr/bin/python3
'''
Database-IO-file
'''

import sqlite3
import os

def checkTables(db):
    ''' makes sure default tables exist in the Database '''
    cursor = db._connection.cursor()
    sql_command = '''
        CREATE TABLE IF NOT EXISTS members (
            mid VARCHAR(64) NOT NULL PRIMARY KEY,
            family_name VARCHAR(64) NOT NULL,
            given_name VARCHAR(64) NOT NULL,
            date_of_birth DATE NOT NULL,
            place_of_birth VARCHAR(64),
            birth_name VARCHAR(64),
            confession VARCHAR(64),
            title VARCHAR(64),
            title_show BOOLEAN,
            qualification VARCHAR(128),
            profession VARCHAR(128),
            call_name VARCHAR(64),
            sex CHAR,
            street VARCHAR(64),
            street_number VARCHAR(8),
            appartment VARCHAR(64),
            postal_code VARCHAR(8),
            city VARCHAR(64),
            state VARCHAR(64),
            country VARCHAR(2),
            email VARCHAR(64),
            secret VARCHAR(64),
            pwsalt VARCHAR(64),
            pwhash VARCHAR(256),
            phone VARCHAR(16),
            mobile VARCHAR(16),
            privacy_accepted BOOLEAN,
            allow_images_public BOOLEAN,
            allow_email_internal BOOLEAN,
            allow_address_internal BOOLEAN,
            allow_city_internal BOOLEAN,
            geo_lat VARCHAR(16),
            geo_lon VARCHAR(16),
            email_newsletter BOOLEAN,
            email_protocols BOOLEAN,
            email_magazine BOOLEAN,
            iban VARCHAR(32),
            bic VARCHAR(32),
            allow_debit BOOLEAN,
            join_date DATE,
            status VARCHAR(256),
            memberships TEXT,
            parents_family_name VARCHAR(64),
            parents_given_name VARCHAR(64),
            parents_street VARCHAR(64),
            parents_street_number VARCHAR(8),
            parents_appartment VARCHAR(64),
            parents_postal_code VARCHAR(8),
            parents_city VARCHAR(64),
            parents_state VARCHAR(64),
            parents_country VARCHAR(2),
            note_public TEXT,
            note_manager TEXT,
            last_update DATE
        );'''
    try:
        cursor.execute(sql_command)
    except sqlite3.OperationalError as err:
        args = list(err.args)
        args.append('Failed to create members table')
        err.args = tuple(args)
        raise
    # add colums added later; uncomment this some day!
    newColumns = [
            'allow_email_internal BOOLEAN',
            'allow_city_internal BOOLEAN'
        ]
    for col in newColumns:
        sql_command = 'ALTER TABLE members ADD COLUMN '+col+';'
        try:
            cursor.execute(sql_command)
        except sqlite3.OperationalError as err:
            pass #print(str(err)) # obviously the column is existing already
    
    sql_command = '''
        CREATE TABLE IF NOT EXISTS groups (
            gid VARCHAR(64) NOT NULL PRIMARY KEY,
            group_name VARCHAR(64) UNIQUE
        );'''
    try:
        cursor.execute(sql_command)
    except sqlite3.OperationalError as err:
        args = list(err.args)
        args.append('Failed to create groups table')
        err.args = tuple(args)
        raise
    sql_command = '''SELECT gid FROM groups WHERE group_name='management' '''
    cursor.execute(sql_command)
    gid = cursor.fetchone()
    if gid==None:
        import huuid
        sql_command = '''INSERT INTO groups (gid, group_name) VALUES (?,?) '''
        cursor.execute(sql_command, (huuid.new(), 'management'))
    
    sql_command = '''
        CREATE TABLE IF NOT EXISTS group_members (
            mid INTEGER NOT NULL,
            gid INTEGER NOT NULL
        );'''
    try:
        cursor.execute(sql_command)
    except sqlite3.OperationalError as err:
        args = list(err.args)
        args.append('Failed to create group_members table')
        err.args = tuple(args)
        raise
    
    sql_command = '''
        CREATE TABLE IF NOT EXISTS log (
            timestamp DATE NOT NULL,
            changed_mid INTEGER NOT NULL,
            user_mid VARCHAR(64),
            remote_ip VARCHAR(64),
            address BOOLEAN,
            email BOOLEAN,
            payment BOOLEAN,
            old_data TEXT,
            new_data TEXT
        );'''
    try:
        cursor.execute(sql_command)
    except sqlite3.OperationalError as err:
        args = list(err.args)
        args.append('Failed to create group_members table')
        err.args = tuple(args)
        raise
    
    db._connection.commit()

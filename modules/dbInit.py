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
            birth_name VARCHAR(64),
            title VARCHAR(64),
            call_name VARCHAR(64),
            sex CHAR,
            street VARCHAR(64),
            street_number VARCHAR(8),
            appartment VARCHAR(64),
            postal_code VARCHAR(8),
            city VARCHAR(64),
            state VARCHAR(64),
            country VARCHAR(2),
            geo_lat VARCHAR(16),
            geo_lon VARCHAR(16),
            email VARCHAR(64),
            secret VARCHAR(64),
            pwsalt VARCHAR(64),
            pwhash VARCHAR(256),
            phone VARCHAR(16),
            mobile VARCHAR(16),
            iban VARCHAR(32),
            bic VARCHAR(32),
            join_date DATE,
            allow_debit BOOLEAN,
            email_newsletter BOOLEAN,
            email_protocols BOOLEAN,
            email_magazine BOOLEAN,
            allow_images_public BOOLEAN,
            allow_address_internal BOOLEAN,
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

#!/usr/bin/python3
#Special thanks to KR0SIV for his DAPNET2APRS program https://github.com/KR0SIV/DAPNET2APRS
#and N8ACL for his DAPNETNotifier program https://github.com/n8acl/DAPNETNotifier  
#on both of which this program is based
#Copyright 2023 John Tetreault WA1OKB, released under the Gnu General Public License v3.0
#
import json
import re
import requests
import time
import http.client, urllib
import sys
import aprslib
from requests.auth import HTTPBasicAuth
from os import system, name
from time import sleep


##### Define Configs
first_run = True
linefeed = "\r\n"
wait_time = 60
dapnet_username = 'YOUR_DAPNET_LOGIN'
dapnet_password = 'YOUR_DAPNET_API_PASSWORD'
dapnet_url = 'http://www.hampager.de:8080/calls?ownerName=' +dapnet_username
callsign = 'YOUR_CALLSIGN'
aprs_passcode = 'YOUR_APRS_PASSCODE'
pager_id = 'YOUR_DAPNET_RIC'
send_to = 'APRS_CALLSIGN_TO_SEND_TO'
db_engine = 'mysql'     #you can use either 'mysql' or 'sqlite', I didnt want sqlite hammering away at my Pi SD card, so I used my MariaDB server on my nas instead

if db_engine == 'mysql':
  import mysql.connector
  mysqlhost = "YOUR_MYSQL_SERVER"             #If you want to use MySQL/MariaDB, put your server info here
  mysqluser = "MYSQL_SERVER_LOGIN"
  mysqlpassword = "MYSQL_SERVER_PASSWORD"
  db = "dapnet"
else:
  import sqlite3 as sql
  from sqlite3 import Error
  import os
  db = os.path.dirname(os.path.abspath(__file__)) + "/dapnet.db"


##### Define SQL Functions
def create_connection(db_file):
    conn = None
    if db_engine == 'mysql':
    #Create connection to MySQL/MariaDB Database    
        try:
             conn = mysql.connector.connect(
               host = mysqlhost,
               user = mysqluser,
               password = mysqlpassword,
               database = db_file
             )
        except Error as e:
             print (e)
    else:
    # Creates connection to dapnet.db SQLlite3 Database
       try:
           conn = sql.connect(db_file)
       except Error as e:
           print (e)
    return conn

def exec_sql(conn,sql):
    # Executes SQL for Updates, inserts and deletes
    cur = conn.cursor(buffered=True)
    cur.execute(sql)
    conn.commit()

def select_sql(conn,sql):
    # Executes SQL for Selects
    cur = conn.cursor(buffered=True)
    cur.execute(sql)
    return cur.fetchall()

def new(conn):
# Create new database if not exists
    if db_engine == 'mysql':
      conn = mysql.connector.connect(
          host = mysqlhost,
          user = mysqluser,
          password = mysqlpassword
      )
      cur = conn.cursor(buffered=True)
      sql = "CREATE DATABASE " + db
      cur.execute(sql)
      sql = "USE " + db
      cur.execute(sql)

    create_message_table = """ create table if not exists messages (
text text, 
timestamp text
); """

    exec_sql(conn, create_message_table)

    data = get_api_data()

    for i in range(0,len(data)):
        text = data[i]['text']
        timestamp = data[i]['timestamp']

        sql = "insert into messages (text, timestamp) "
        sql = sql + "values('" + text + "','" + timestamp + "');"

        exec_sql(conn, sql)



##### Get API Data
def get_api_data():
    return requests.get(dapnet_url, auth=HTTPBasicAuth(dapnet_username,dapnet_password)).json()

##### Send APRS function
def send_aprs(msg):
        try:
              print("Forwarding for " + pager_id + " to APRS: " + msg)
              AIS = aprslib.IS(callsign, aprs_passcode, port=14580)
              AIS.connect()
              AIS.sendall("DAPNET>APRS,TCPIP*::" + send_to.ljust(9) + ":" + msg)
        except:
            pass


##### Main Program

# check to see if the database exists. If not create it. Otherwise create a connection to it for the rest of the script
if db_engine == 'mysql':
     conn = mysql.connector.connect(
          host = mysqlhost,
          user = mysqluser,
          password = mysqlpassword
     )
     cur = conn.cursor(buffered=True)
     cur.execute("SHOW DATABASES")
     db_exists = 0
     for x in cur:
        if str(x) == "('"+db+"',)":
           sql = "USE " + db
           cur.execute(sql)
           db_exists = 1
     if db_exists == 0:
        new(conn)
else:
  conn = sql_connection(db)
  if not os.path.exists(db):
    conn = sql_connection(db)
    new(conn)
  else:
    conn = sql_connection(db) 

# Check API and if the last message was not already sent, send it... else ignore it.
try:
    while True:
        if first_run: # If this is the first run, don't send anything
            first_run = False
        else:
            # Wait the check time to not pound the API and get rate Limited
            if wait_time < 60:
                sleep(60)
            else:
                sleep(wait_time) 

            # get the data from the API
            data = get_api_data()

            for i in range(0,len(data)):
                text = data[i]['text']
                timestamp = data[i]['timestamp']

                sql = "select count(text) as text_cnt from messages where text = '" + text + "' and timestamp = '" + timestamp + "';"
                result = select_sql(conn, sql)

                for row in result:
                    text_cnt = row[0]

                if text_cnt == 0:

                    sql = "insert into messages (text, timestamp) "
                    sql = sql + "values('" + text + "','" + timestamp + "');"

                    exec_sql(conn,sql)
                    
                    # Send the message 
                    send_aprs(text)
                    

                    break

except Exception as e:
    print(str(e))


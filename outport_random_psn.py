#!/usr/bin/env python
# -*- coding:utf-8 -*-

import datetime
import time

import mysql
from mysql import connector

import random
from random import *


gStartID = 1
gEndID   = 5500000

psnCounts = gEndID - gStartID + 1;
psnFile   = "c:\\psn%s-%s.txt" % (gStartID, gEndID)
#psnFile = "c:\\psn460001-510000.txt";
#psnFile = "c:\\psn510001-610000.txt";
#psnCounts = 100000;

user = 'root';
passwd = 'mysql111';
host = '127.0.0.1';
db = 'sport_camera_sn';

table_unused = "psn";

# connect db
try:
    conn = mysql.connector.connect(user = user, password = passwd, host = host, database = db);
except Exception as e:
    print(e);
    #return None;
    
cursor = conn.cursor();

try:
    file = open(psnFile, "w");
except Exception as e:
    print(e);

sql_select_cmd = "select id, psn from %s where is_used = 0 limit %s, %s;" % (table_unused, 0, psnCounts);

try:
    cursor.execute(sql_select_cmd); # return row was executed
    
    rows = cursor.fetchall();
    
    #print(rows);
    
    for row in rows:
        print(row);
        file.write("%s,%s\n" % (row[0], row[1]));
        
        #now = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S");
        
        #sql_insert_cmd = "insert into %s(psn, date) values ('%s', '%s');" % (table_used, row[1], now);
        #print(sql_insert_cmd)
        #cursor.execute(sql_insert_cmd);
        
        #sql_delete_cmd = "delete from %s where psn='%s';" % (table_unused, row[1]);
        #conn.commit();

except Exception as e:
    print(e);


file.close();
cursor.close();
conn.close();

#!/usr/bin/env python3
# -*- coding:utf-8 -*-
""" SQL connections for provision"""

import pyodbc
import sqlalchemy
import urllib

PLMADMINDB = pyodbc.connect(('Driver={SQL Server};Server=DBSVR01;'
                             'Database=PLMADMINDB;Trusted_Connection=yes;'))

SYNCSVR01 = pyodbc.connect(
    ('Driver={SQL Server};Server=SYNCSVR01\\SYNCSVR;'
     'Database=NETSyncServer2014;Trusted_Connection=yes;'))

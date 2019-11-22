#!/usr/bin/env python3
# -*- coding:utf-8 -*-

""" Import dash job notes from individual csv files

origPath leads to CompanyExport
"""

import pyodbc
import glob
import os
import argparse
import pandas as pd
from datetime import datetime
import time
import sys

def notes_migration(svr: str, db: str, origPath: str) -> None:
	sys.stdout = open("results_Notes.txt","w")

	starttime = time.time()
	print(datetime.utcfromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S'))

	query = """SELECT 
			job_JobID, 
			FORMAT(JOB_ID, '0000000'), 
			FORMAT(PROJECT_ID, '000000') 
		FROM JOB"""
	cnxn = pyodbc.connect(r'Driver={SQL Server};Server=' + svr +
							';Database=' + db + ';Trusted_Connection=yes;')
	cnxn.autocommit = True
	cursor = cnxn.cursor()
	cursor.execute(query)

	jn_proj = {
		str(k): (v1, v2) 
		for (k,v1, v2) in cursor.fetchall()
	}

	paths = {}
	for loc in glob.iglob(origPath + '/*'):
		if not os.path.isdir(loc) or not loc.split('\\')[-1].startswith('Jobs'):
			continue

		for f in glob.iglob(loc + '/*'):
			f = f.replace('\\','/')
			jn = f.split('/')[-1].split(',')[0].replace('JN=','')
			if jn in jn_proj:
				paths[jn] = f + '/NotesForJob/NotesFor_JN=' + jn + '.csv'

	for jn, path in paths.items():
		if not os.path.isfile(path):
				continue
		notes = pd.read_csv(path)

		notes['DateEntered'] = pd.to_datetime(notes['DateEntered'])
		notes['DateEntered'] = notes.DateEntered.fillna('1900-01-01')
		notes['AddedBy'] = notes.AddedBy.str.replace("'", "''").str.strip(u'\u200b')
		notes['Note'] = notes.Note.str.replace("'", "''").str.strip(u'\u200b')
		notes['DateEnetered'] = notes.DateEntered
		notes = notes.dropna(subset=['Note']).fillna('')
		
		for row in notes.iterrows():
			params = [
				str(jn).strip(u'\u200b'),
				8,
				'Job Notes from DASH',
				row[1]['Note'],
				row[1]['DateEntered'],
				row[1]['AddedBy'],
				datetime.now(),
				0,
				'Active',
			]


			queryAdd = """INSERT INTO CORRESPONDENCE (
					RecordSource_FKey,
					CORRESPONDENCE_Type_ID,
					CORRESPONDENCE_Title,
					CORRESPONDENCE_Body,
					CORRESPONDENCE_DateTime,
					RecordSource_FKey2,
					CORRESPONDENCE_CreatedDate, 
					CORRESPONDENCE_Status_ID, 
					CORRESPONDENCE_STATUS
			) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ? )"""

			try:
				cursor.execute(queryAdd, params)
			except: 
				print(params)

	ctjQuery = """INSERT INTO CORRESPONDENCE_ToJob (
			CORRESPONDENCE_ID, 
			JOB_ID
		) SELECT 
			c.CORRESPONDENCE_ID, 
			j.JOB_ID 
		FROM CORRESPONDENCE c 
		INNER JOIN JOB j ON j.job_JobID = c.RecordSource_FKey 
		WHERE c.CORRESPONDENCE_Title = 'Job Notes from DASH' """

	cursor.execute(ctjQuery)
	cnxn.close()

	endtime = time.time()
	print('Run time: '+str(endtime - starttime)+' seconds')
	print('Run time: '+str((endtime - starttime)/60)+' minutes')

	sys.stdout.close()


def run() -> None:
	parser = argparse.ArgumentParser('Imports migration data into SQL')
	parser.add_argument('-c', '--config', default='../', 
					help='Path to config file directory')
	parser.add_argument('-r', '--run', default='Test', 
					help='Type of run (test or prod).')

	args = parser.parse_args()
	args.run = args.run.capitalize()

	import SettingsReader
	config = SettingsReader.runtime_settings(args.run, args.config)

	notes_migration(config['svr'], config['db'], config['path'])


if __name__=='__main__':
	run()
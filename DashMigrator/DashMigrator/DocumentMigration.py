#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""DataImport holds data_import function. 
Inserts DASH data into our SQL db. 
"""

import os
import sys
import glob
import time
import argparse
from typing import Dict, Tuple, List
from collections import defaultdict
from datetime import datetime
import shutil
import pyodbc


def document_migration(svr: str, db: str, bfpath: str, origPath: str) -> None:
    """ Moves documents from original dash directory structure 
    to our builder files

	Args:
		svr - server of db
	"""
    starttime = time.time()
    print(datetime.utcfromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S'))

    idStore = ID_query(svr, db)

    paths = []
    for folder in os.listdir(origPath):
        if not folder.startswith('Jobs'):
            continue
        folderPath = os.path.join(origPath, folder)

        paths.extend(
            glob.glob(os.path.join(folderPath, 'JN=**/Photos&Docs/**/*')))

    errs = []
    for path in paths:
        docParts = path.split('\\')
        jobNumber = docParts[2].split(',')[0].replace('JN=', '')
        album = docParts[-2].replace('Album=', '')
        fileName = docParts[-1]

        if jobNumber in idStore:
            pathParts = idStore[jobNumber]
        else:
            continue

        if album == 'ROOT':
            dst = (f"{bfpath}/Sites/Site_{pathParts[2]}/Projects/Project_"
                   f"{pathParts[1]}/Jobs/Job_{pathParts[0]}/Documents/")
        else:
            dst = (f"{bfpath}/Sites/Site_{pathParts[2]}/Projects/Project_"
                   f"{pathParts[1]}/Jobs/Job_{pathParts[0]}/Documents/{album}")

        os.makedirs(dst, exist_ok=True)
        if os.path.isfile(os.path.join(dst, fileName)):
            continue

        if "." in path:
            print('. worked')
            try:
                print(f'{path}')
                shutil.copy2(path, dst)
            except:
                errs.append(f"error - dst: {dst} src: {path}")
        elif os.path.isfile(path):
            print('no file')
            try:
                print(f'{path}')
                shutil.copy2(path, dst + fileName + '.jpg')
            except:
                errs.append(f"error - dst: {dst}")

    print('\n'.join(errs))
    endtime = time.time()
    print('Run time: ' + str(endtime - starttime) + ' seconds')
    print('Run time: ' + str((endtime - starttime) / 60) + ' minutes')
    return


def ID_query(svr: str, db: str) -> Dict[str, Tuple[str, str, str]]:
    """ID_query creates dict of job_jobID 
	to formatted job/project/site IDs in DB

	Args:
		svr: Server name
		db: Database name
	Returns:
		Dict of job_jobID : (JOB_ID, PROJECT_ID, SITE_ID)
	"""
    query = """SELECT 
			job_jobID, 
			FORMAT(JOB_ID, '0000000'), 
			FORMAT(PROJECT_ID, '000000'), 
			FORMAT(SITE_ID, '0000') 
		FROM JOB"""

    cnxn = pyodbc.connect((f'Driver={{SQL Server}};Server={svr};'
                           f'Database={db};Trusted_Connection=yes;'))
    cursor = cnxn.cursor()

    cursor.execute(query)
    res = cursor.fetchall()
    cnxn.close()

    return {str(k): (v1, v2, v3) for (k, v1, v2, v3) in res}


def run() -> None:
    """run operates when program is started from main
	"""
    parser = argparse.ArgumentParser('Imports migration data into SQL')
    parser.add_argument('-c',
                        '--config',
                        default='../',
                        help='Path to config file directory')
    parser.add_argument('-r',
                        '--run',
                        default='Test',
                        help='Type of run (test or prod).')

    args = parser.parse_args()
    args.run = args.run.capitalize()

    import SettingsReader
    config = SettingsReader.runtime_settings(args.run, args.config)
    bfpath = os.path.join(config['bfbase'], config['db'])

    document_migration(config['svr'], config['db'], bfpath, config['path'])


if __name__ == '__main__':
    run()

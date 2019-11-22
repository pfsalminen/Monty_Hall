#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""DashMigrator is a CLI program to run for DASH migrations
Uses google's fire to make function names command line options

ImportData - Add data to database
MoveDocuments - Copy dash documents to bfsvr and add them to customer db
ImportNotes - Add all job notes to customer db

configPath must be added when run for all
Optional run on ImportData must be 'Test' or 'Prod'

Example:
	python DashMigrator.py ImportData --configPath=./configs/TESTRUN.ini
"""

import os
import glob
from typing import Dict
import fire

from DashMigrator import (DataImport, DocumentMigration, DocumentSQL,
                          NotesImport, SettingsReader, CompanyCleanup,
                          CreateMapping)


def ImportData(run: str = 'Test', configPath: str = './config.ini') -> None:
    """CLI funcation to import Dash data to RM
	Removes duplicates from company table (via notes)
	Adds company, customer, and job tables to database
	If test, creates cleanup/mapping sheets

	Args:
		run: String that determines which db data is sent to (Test or Prod)
		configPath: String that leads to the config file
	"""
    info = SettingsReader.runtime_settings(run.capitalize(), configPath)

    files = glob.glob(info['path'] + '/*tbl*.csv')
    if not files:
        print('CSVs not found')
        return

    tmp = files[0].replace('\\', '/')
    fPath = tmp[:tmp.index('tbl')]

    good = CompanyCleanup.clean_company(fPath + 'tblCompany.csv')
    if not good:
        print('Error cleaning company file')
        return

    DataImport.data_import(info['svr'], info['db'], fPath)

    if run == 'Test':
        CreateMapping.run(info['db'])


def MoveDocuments(configPath: str = './config.ini') -> None:
    """CLI function to move DASH documents
	Moves documents from DASH folder in config to bfsvr in config
	Adds moved documents to customers database
	Only runs to production

	Args:
		configPath: String that leads to the config file
	"""
    info = SettingsReader.runtime_settings('Prod', configPath)
    bfpath = os.path.join(info['bfbase'], info['db'])

    DocumentMigration.document_migration(info['svr'], info['db'], bfpath,
                                         info['path'])

    DocumentSQL.document_sql(info['svr'], info['db'], bfpath)


def ImportNotes(configPath: str = './config.ini') -> None:
    """CLI function to import notes to customer db
	Looks through all job folders in DASH folder from config
	Adds the notes to customers database
	Only runs to production

	Args:
		configPath: String that leads to the config file
	"""
    info = SettingsReader.runtime_settings('Prod', configPath)

    NotesImport.notes_migration(info['svr'], info['db'], info['path'])


if __name__ == '__main__':
    fire.Fire()

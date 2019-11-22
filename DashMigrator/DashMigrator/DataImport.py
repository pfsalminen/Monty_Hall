#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""DataImport holds data_import function. 
Inserts DASH data into our SQL db. 
"""

import argparse
import time
from typing import Dict
import pandas as pd
import numpy as np
import sqlalchemy
import urllib
import pyodbc


def data_import(svr: str, db: str, path: str) -> None:
    """data_import inserts data tbl data into our SQL db

	Args:
		svr: Server name
		db: Database name
		path: Path to dash's csv data
	Returns:
		None
	"""
    starttime = time.time()

    engine = make_engine(svr, db)

    row_counts = {}
    tables = [
        'tblCompany',
        'tblCustomer',
        'tblJob',
    ]
    for tbl in tables:
        df = pd.read_csv(path + tbl + '.csv')
        df = stringify_columns(df)

        row_counts[tbl] = df.shape[0]

        dtypes = {col: sqlalchemy.types.String() for col in df.columns}
        try:
            df.to_sql(f'DASH_{tbl}$',
                      engine,
                      if_exists='replace',
                      dtype=dtypes,
                      index=False)
        except Exception as e:
            print(f'Table {tbl} not imported. {e}')

    endtime = time.time()
    print_results(row_counts, starttime, endtime)


def make_engine(svr: str, db: str) -> sqlalchemy.engine.base.Engine:
    """make_engine creates and returns a sqlalchemy engine
	which is connected to the customers db
	
	Args:
		svr: Server name
		db: Database name
	Returns:
		engine: sqlalchemy engine to customer db
	"""
    cStr = urllib.parse.quote_plus((f"Driver={{SQL Server}};Server={svr};"
                                    f"Database={db};Trusted_Connection=yes;"))
    engine = sqlalchemy.create_engine(f'mssql+pyodbc:///?odbc_connect={cStr}')

    return engine


def stringify_columns(df: pd.DataFrame) -> pd.DataFrame:
    """stringify_columns changes all dataframe columns to object
	While doing so, it cleans them-
		Fills all NANs with -1, 
		Converts cols to int then string (to get rid of unwanted .0)
		Replaces -1 with NAN to keep null values
	
	Args: 
		df: DataFrame to convert to strings
	Returns:
		DataFrame with all columns as object (str)
	"""
    toCleanCols = [col for col in df.columns if df.dtypes[col] != 'object']
    for col in toCleanCols:
        df[col] = (df[col].fillna(-1).astype(np.int64).astype(str).replace(
            '-1', np.nan))

    return df


def print_results(row_counts: Dict[str, int], start: float, end: float) -> None:
    """print_results prints CSV row counts 
	(so I can confirm in SQL)

	Args: 
		row_counts: Dictionary of row counts for each table inserted
		start: float of start time
		end: float, end time
	Returns:
		None
	"""
    print(f"Company count: {row_counts['tblCompany']}")
    print(f"Customer count: {row_counts['tblCustomer']}")
    print(f"Job count: {row_counts['tblJob']}")
    print(f'Run time: {str(end - start)} seconds')
    print(f'Run time: {str((end - start)/60)} minutes')


def parse_args() -> argparse.Namespace:
    """parse_args parses command line arguments

	Args:
		None
	Returns:
		Parsed args
	"""
    parser = argparse.ArgumentParser('Imports migration data into SQL')
    parser.add_argument('-c',
                        '--config',
                        default='./config.ini',
                        help='Path to config file directory')
    parser.add_argument('-r',
                        '--run',
                        default='Test',
                        help='Type of run (test or prod).')

    args = parser.parse_args()
    args.run = args.run.capitalize()

    return args


def run() -> None:
    """run operates when program is started from main
	"""
    import SettingsReader

    args = parse_args()
    config = SettingsReader.runtime_settings(args.run, args.config)

    data_import(config['svr'], config['db'], config['filepath'])


if __name__ == '__main__':
    run()

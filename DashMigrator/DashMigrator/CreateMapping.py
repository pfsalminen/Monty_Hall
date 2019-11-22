#!/usr/bin/env python3
# -*- coding=utf-8 -*-

import argparse
import os
from typing import List
import pyodbc
import sqlalchemy
import urllib
import pandas as pd
import xlsxwriter


def get_items(que: str, db: str) -> List[str]:
    """Runs query on test DB for cleanup sheets 
	
	Args:
		que: SQL query
		db: Database to use
	Returns:
		List: Query results
	"""
    conn = pyodbc.connect(("Driver={SQL Server};Server=IntegrationsSvr;"
                           f"Database={db};Trusted_Connection=yes;"))
    cur = conn.cursor()
    cur.execute(que)
    return [item[0] for item in cur.fetchall()]


def mapper(fName: str, dashName: str, rmName: str, dashItems: List[str],
           rmItems: List[str]) -> None:
    """Creates mapping sheet for dash migration cleanup
	
	Args:
		fName: File name of excel to create
		dashName: Name of dash field
		rmName: Name of RM field
		dashItems: List of items in dash name
		rmItems: List of items in rm name
	Returns:
		None
	"""
    colors = {
        'staff': '#f8cbad',
        'determination': '#c6e0b4',
        'progress': '#bdd7ee',
    }

    book = xlsxwriter.Workbook(fName)
    sheet = book.add_worksheet()

    opt = rmName.split(' ')[-1].lower()
    bold = book.add_format({'bold': True})
    rmFormat = book.add_format({'bg_color': colors[opt]})
    rmHeader = book.add_format({
        'bold': True,
        'bg_color': colors[opt],
    })

    row, col = 0, 0
    maxLen = -1

    # Write headers
    sheet.write(row, col, dashName, bold)
    sheet.write(row, col + 1, rmName, rmHeader)
    row += 1

    # Write dash items
    # (with blank field to fill out)
    for item in dashItems:
        if len(item) > maxLen:
            maxLen = len(item)

        sheet.write(row, col, item)
        sheet.write(row, col + 1, ' ', rmFormat)
        row += 1

    # Write rm header below
    row += 3
    sheet.write(row, col, rmName, rmHeader)
    row += 1

    # Write rm items
    for item in rmItems:
        if len(item) > maxLen:
            maxLen = len(item)

        sheet.write(row, col, item, rmFormat)
        row += 1

    sheet.set_column(0, 1, maxLen + 2)
    book.close()


def duplicateSheet(db: str) -> None:
    """Creates spreadsheet with duplicate companies from DASH company table
	
	Args:
		db: Name of database
	Returns:
		None
	"""
    cStr = urllib.parse.quote_plus(
        ("Driver={SQL Server};Server=IntegrationsSvr;"
         f"Database={db};Trusted_Connection=yes;"))
    engine = sqlalchemy.create_engine(f'mssql+pyodbc:///?odbc_connect={cStr}')

    que = """SELECT
		CompanyId,
		CompanyType,
		CompanyName,
		'' AS 'IMPORT / SKIP / RENAME',
		[Address],
		City,
		[State],
		Zip,
		MainPhone,
		CorrespondenceEmail,
		[Status]
	FROM DASH_TBLcompany$
	WHERE CompanyName IN
	(
		SELECT CompanyName
		FROM DASH_TBLcompany$
		GROUP BY CompanyName
		HAVING COUNT(CompanyName)>1
	)
	ORDER BY CompanyName, CompanyId"""
    df = pd.read_sql_query(que, engine, coerce_float=False)

    writer = pd.ExcelWriter(f'{db}_DASH_RM_duplicate_companies.xlsx',
                            engine='xlsxwriter')

    df.to_excel(writer, sheet_name='Sheet1', index=False)

    # Get the xlsxwriter workbook and worksheet objects.
    book = writer.book
    sheet = writer.sheets['Sheet1']
    highlighter = book.add_format({'bg_color': '#ccc0da'})

    # Stylize the column widths
    for i, col in enumerate(df.columns):
        maxLen = max(len(col), df[col].str.len().max())

        if 'import' in col.lower():
            sheet.set_column(i, i, maxLen + 2, highlighter)
        else:
            sheet.set_column(i, i, maxLen + 2)

    writer.save()


def run(db: str = None) -> None:
    """ Runs through all cleanup sheets"""
    if not db:
        print('Please provide test database name')
        return

    fBase = os.path.dirname(os.path.abspath(__file__))

    # RM Progress/DASH Status
    fName = os.path.join(fBase, f'{db}_DASH_RM_progress_mapping.xlsx')
    status = get_items(("SELECT DISTINCT status FROM DASH_tblJob$ "
                        "WHERE [Status] IS NOT NULL ORDER BY [Status]"), db)

    progress = get_items("SELECT DISTINCT cmb_Desc FROM JOB_Progress", db)

    mapper(fName, 'DASH Status', 'RM Progress', status, progress)

    # RM Determination/DASH Reason
    fName = os.path.join(fBase, 'DASH_RM_determination_mapping.xlsx')
    reason = get_items(("SELECT DISTINCT reason FROM DASH_tblJob$ "
                        "WHERE reason IS NOT NULL ORDER BY reason"), db)

    determination = get_items(
        "SELECT DISTINCT cmb_Desc FROM ITEM_Determination", db)

    mapper(fName, 'DASH Reason', 'RM Determination', reason, determination)

    # Staff mapping
    fName = os.path.join(fBase, 'DASH_RM_staff_mapping.xlsx')
    dash_staff = [
        'Estimator',
        'Coordinator',
        'Superviser',
        'AccountingPerson',
        'MarketingPerson',
        'Foreman',
        'ReceivedBy',
    ]
    rm_staff = [
        'Project Mgr',
        'Estimator',
        'Lead Tech',
        'Marketing Rep',
        'Call Taker',
        'Accounting',
    ]
    mapper(fName, 'DASH Staff Fields', 'RM Staff', dash_staff, rm_staff)

    # Duplicate Companies
    duplicateSheet(db)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', help='Test database name')
    args = parser.parse_args()

    run(args.db)

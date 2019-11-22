#!/usr/bin/env python3
# -*- coding:utf-8 -*-

""" Sets up each puroclean company
* Creates builder files folder from stub
* Updates logo paths in System_Settings
* Creates Intuitive Mobile folder from stub
    * Updates html to have dbname
* Creates ThirdPartAuth XML
* Adds row to customer table using PCMASTERDB
* Adds row to tblAuth table using PCMASTERDB
* Creates NetSyncServer folder from XM Stub
    * Changes DBName to Customer name
* Adds rows to NETSyncServer2014.Integrations
* Creates new excel for site only builder_emps
* Adds info to BUILDER and SITE tables
* Inserts builder emps into each database
* Updates PLMSyncServer.cfg
    ** Needs to be tested!
    ** update_xm8_config()
    ** update_sync_config()

TODO:
    update update_plm_admin() for any customer
    update update_logo_paths() for any customer
    update update_sites() for any customer
    Check out builder files stuffs

QBO:
--- UPDATE tblAuth SET QBONLINE_ENABLED = 1
"""

import os
import shutil
import xml.etree.ElementTree as ET
import datetime
import argparse
from typing import Set, List, Tuple

import pandas as pd
import pyodbc
import sqlalchemy
import urllib


def get_args() -> argparse.Namespace:
    """ Parse cmdline arguments with argparse """
    parser = argparse.ArgumentParser(description='Setup '
                                    'new puroclean customers')
    parser.add_argument('--num', '-n', help='Priority '
                        'number to run')
    parser.add_argument('--region', '-r', default='US', help='Region of sites'
                        'to look at. US or CA, default is US.')
    parser.add_argument('--db', help='Specific Database to run')
    return parser.parse_args()


def open_sites(region: str) -> pd.DataFrame:
    if region == 'US':
        df = (pd.read_excel('puroclean_sites.xlsx', sheet_name='Site Import')
                    .dropna(subset=['DB Name']))
        df['RecordSource_FKey'] = df['site_SiteDesc']
        df['REGION_ID'] = 1
    
    elif region=='CA':
        df = (pd.read_excel('puroclean_ca_sites.xlsx', sheet_name='Site Import')
                    .dropna(subset=['DB Name']))
        df['RecordSource_FKey'] = df['site_SiteDesc']
        df['REGION_ID'] = 1
    else:
        print('ERROR reading data, invalid region')
        return

    return df


def open_data(num: int, region: str) -> pd.DataFrame:
    """ Read in PuroCleanXASetup.xlsx and clean column names"""
    if region == 'US':
        df = (pd.read_excel('PC_franchise_locations.xlsx',
                        sheet_name='Active & Pending')
                    .fillna({'Setup Priority':-1})
                    .loc[lambda df: df['Signed Up?'] == 'Yes']
                    .loc[lambda df: df['Setup Priority'].astype(int) == num if num
                                    else df['Setup Priority'].notna()]
                    .dropna(subset=['DB Name'])
                    .join((pd.read_excel('PuroCleanXASetup.xlsx',
                                names=['site_id', 'xactnet_address', 'account_id'])
                            .set_index('site_id')), on='Site ID', how='left'))
    elif region=='CA':
        df = (pd.read_excel('PC_franchise_locations.xlsx',
                        sheet_name='Canada Active & Pending')
                    .fillna({'Setup Priority':-1})
                    .loc[lambda df: df['Signed Up?'] == 'Yes']
                    .loc[lambda df: df['Setup Priority'].astype(int) == num if num
                                    else df['Setup Priority'].notna()]
                    .dropna(subset=['DB Name']))
    else:
        print('ERROR reading data, invalid region')
        return

    return df


def open_one_record(db: str, region: str) -> pd.Series:
    if region == 'US':
        df = (pd.read_excel('PC_franchise_locations.xlsx',
                        sheet_name='Active & Pending')
                    .fillna({'Setup Priority':-1})
                    .loc[lambda df: df['Signed Up?'] == 'Yes']
                    .join((pd.read_excel('PuroCleanXASetup.xlsx',
                                names=['site_id', 'xactnet_address', 'account_id'])
                            .set_index('site_id')), on='Site ID', how='left')
                    .loc[lambda df: df['DB Name'] == db])
    elif region=='CA':
        df = (pd.read_excel('PC_franchise_locations.xlsx',
                        sheet_name='Canada Active & Pending')
                    .fillna({'Setup Priority':-1})
                    .loc[lambda df: df['Signed Up?'] == 'Yes']
                    .loc[lambda df: df['DB Name'] == db])
    
    if not df.empty:
        return df.iloc[0]


def list_databases(svr: str='DBSVR03') -> Set[str]:
    conn = pyodbc.connect((f"Driver={{SQL Server}};Server={svr};"
                            "Database=master;Trusted_Connection=yes;"))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sys.databases")
    return set([row[0] for row in cur.fetchall()])


def copy_folder(old: str, new: str):
    """ copies folder old and contents to folder new"""
    if os.path.isdir(new):
        return

    try:
        shutil.copytree(old, new)
    except shutil.Error as e:
        print(f'Files not copied. Error: {e}')
    except OSError as e:
        print(f'Files not copied. Error: {e}')


def document_maker(db: str, base: str='//bfsvr03/BUILDERFILES/RMBFSVR/',
                    master_copy: str='PCMASTERDB') -> None:
    """ Copies all files from the masterDB builder files folder
    to a new company folder"""
    master = os.path.join(base, master_copy)
    company = os.path.join(base, db)

    copy_folder(master, company)


def intuitive_setup(db: str, master_copy: str='PCMASTERDB_STUB') -> None:
    """ Create the intuitive mobile folder from stub copy
    and then edits the HTML for company name"""
    base = '//appsvr08/inetpub/Sites/www.intuitivemobile.com/'
    master = os.path.join(base, master_copy)
    company = os.path.join(base, db)

    copy_folder(master, company)

    master_login = os.path.join(company, 'masterlogin.html')
    with open(master_login, 'r+') as f:
        content = f.read()
        content = content.replace("STUB_COPY", db)
        content = content.replace('MOBILEMANAGER_WEB', 'MOBILEMANAGER_WEB05')
        f.seek(0)
        f.write(content)
        f.truncate()


def make_ThirdPartAuth_xml(db: str, acnt_id: int) -> None:
    """ Writes the ThirdPartAuth XML"""
    base = '//syncsvr01/Netsyncserver/XactwareIntegration/ThirdPartAuth'
    out_name = os.path.join(base, f'xm8auth_{db}.xml')

    if os.path.exists(out_name):
        return

    root = ET.Element('XACTDOC')
    doc = ET.SubElement(root, 'XACTNET_INFO', thirdPartyId="3364615")
    companies = ET.SubElement(root, 'COMPANIES')
    company = ET.SubElement(companies, 'COMPANY', action="enable", 
                            id=f"{acnt_id}", name=f"{db}")
    tree = ET.ElementTree(root)

    tree.write(out_name, encoding='UTF-8', xml_declaration=True)


def update_plm_admin(db: str, svr: str='DBSVR01') -> None:
    """ Makes updated to customers and tblAuth """
    conn = pyodbc.connect((f'Driver={{SQL Server}};Server={svr};'
                        'Database=PLMADMINDB;Trusted_Connection=yes;'))
    cur = conn.cursor()

    test_customers = f"""SELECT * FROM Customers WHERE CustomerCode = '{db}' """
    cur.execute(test_customers)
    if not cur.fetchone():
        update_customers(db, cur)

    test_auth = f"""SELECT * FROM tblAuth WHERE Company = '{db}' """
    cur.execute(test_auth)
    if not cur.fetchone():
        update_tblAuth(db, cur)


def update_customers(db: str, cur: pyodbc.Cursor) -> None:
    """ Inserts row for customer into customers"""
    cust_que = "SELECT * FROM Customers WHERE CustomerCode = 'PCMASTERDB' "
    exe_desc = cur.execute(cust_que).description
    customer = {
        k[0].lower(): v
        for k, v in zip(exe_desc, cur.fetchone())
    }

    # Delete fields that are autopopulated
    del customer['customer_id']
    del customer['customer_guid']
    del customer['recorddatetime']

    customer['customercode'] = db
    customer['notes'] = f'Site Provisioned on {datetime.datetime.now()}'
    customer['baseurl'] = f'{db}.restorationmanager.net'
    customer['dbserver_id'] = '4'

    keys = list(customer.keys())
    vals = ', '.join('?' for _ in keys)
    insert_vals = [customer[key] for key in keys]

    insert_que = f"""INSERT INTO Customers(
            {', '.join(keys)}
        ) VALUES (
            {vals}
        )"""

    try:
        cur.execute(insert_que, insert_vals)
        cur.commit()
    except Exception as e:
        print(f'No customer row: {db}\tException: {e}')


def update_tblAuth(db: str, cur: pyodbc.Cursor) -> None:
    """Inserts row for customer into tblAuth"""
    auth_que = "SELECT * FROM tblAuth WHERE COMPANY = 'PCMASTERDB' "
    exe_desc = cur.execute(auth_que).description
    auth = {
        k[0].lower(): v
        for k, v in zip(exe_desc, cur.fetchone())
    }

    cur.execute(("SELECT Customer_ID FROM Customers "
                f"WHERE CustomerCode='{db}' "))
    customer_id = cur.fetchone()[0]

    # Delete autopopulated fields
    del auth['id'], auth['recorddatetime']

    auth['company'] = db
    auth['password'] = db[::-1]
    auth['db_name'] = db
    auth['image_directory'] = auth['image_directory'].replace('PCMASTERDB', db)
    auth['customer_id'] = customer_id
    auth['db_dsn'] = 'INT_DBSVR03'
    auth['emailsync_email'] = f"{db}@servicesoftwareinc.com"
    auth['emailsync_pw'] = '!SSllc3mail!'

    keys = list(auth.keys())
    vals = ', '.join('?' for _ in keys)
    insert_vals = [auth[key] for key in keys]

    insert_que = f"""
        INSERT INTO tblAuth(
            {', '.join(keys)}
        ) VALUES (
            {vals}
        )"""

    try:
        cur.execute(insert_que, insert_vals)
        cur.commit()
    except Exception as e:
        print(f'No tblAuth row: {db}\tException: {e}')

def setup_xact(db: str, xact_addr: str, svr: str='DBSVR03') -> None:
    """ Runs provision stored procedure
    and adds xn address to company database"""
    run_jobtoxa(svr, db)
    update_xn_address(svr, db, xact_addr)


def update_xn_address(svr: str, db: str, xact_addr: str) -> None:
    """ Inserts XN addresses into customer DB"""
    conn = pyodbc.connect((f'Driver={{SQL Server}};Server={svr};'
                            f'Database={db};Trusted_Connection=yes;'))
    cur = conn.cursor()

    cur.execute('SELECT XactNetAddress FROM XNADDRESS')
    results = [i[0] for i in cur.fetchall()]
    if xact_addr in results:
        return

    que = f"""INSERT INTO XNAddress(XactNetAddress) VALUES ('{xact_addr}')"""
    cur.execute(que)
    cur.commit()


def run_jobtoxa(svr: str, db: str) -> None:
    """ Runs Provision_XM8_JOBRMTOXA stores procedure"""
    conn = pyodbc.connect(('Driver={SQL Server};Server=SYNCSVR01\\SYNCSVR;'
                        'Database=NETSyncServer2014;Trusted_Connection=yes;'))
    cur = conn.cursor()

    que = f"""EXEC Provision_XM8_JOBRMTOXA '{db}','{svr}' """

    cur.execute(que)
    cur.commit()


def update_logo_paths(db: str) -> None:
    """ Changes the system settings table logo paths
    from the master db to company db"""
    conn = pyodbc.connect(('Driver={SQL Server};Server=DBSVR03;'
                        f'Database={db};Trusted_Connection=yes;'))
    cur = conn.cursor()

    que = 'SELECT Logo, LogoReports FROM System_Settings'
    cur.execute(que)
    logo, logo_reports = cur.fetchone()

    if 'PCMASTERDB' not in logo and 'PCMASTERDB' not in logo_reports:
        return

    logo = logo.replace('PCMASTERDB', db)
    logo_reports = logo_reports.replace('PCMASTERDB', db)

    update_que = f""" UPDATE SYSTEM_Settings
        SET Logo='{logo}',
            LogoReports='{logo_reports}' """

    try:
        cur.execute(update_que)
        cur.commit()
    except Exception as e:
        print(f'Settings not updated: {db}\tException: {e}')


def cleanThirdPartAuth(acnt_ids: List[int]) -> None:
    """ LEGACY: one time use. Deletes xm8_PUROCLEAN-* if ID in acnt_ids"""
    base_loc = '//syncsvr01/Netsyncserver/XactwareIntegration/ThirdPartAuth'
    for f in os.listdir(base_loc):
        if not f.startswith('xm8auth_PUROCLEAN'):
            continue

        with open(os.path.join(base_loc, f), 'r') as x:
            tree = ET.parse(x)
        root = tree.getroot()

        if int(root[1][0].attrib['id']) in acnt_ids:
            print(root[1][0].attrib['id'])
            os.remove(os.path.join(base_loc, f))


def create_netsync(db: str, master_copy: str='PCMASTER',
                    base: str='//syncsvr01/c$/Program Files/Netsyncserver/') -> None:
    """ Creates netsyncserver folder for comapny"""
    master = os.path.join(base, master_copy)
    company = os.path.join(base, db)

    copy_folder(master, company)

    update_netsync(db)


def update_netsync(db: str, dsn: str='SYNC_DBSVR03',
                    base: str='//syncsvr01/c$/Program Files/Netsyncserver/') -> None:
    """ Updates SyncServerProject for company"""
    with open(os.path.join(base, db, 'SyncServerProject.cfg'), 'r+') as f:
        content = f.read()
        content = content.replace('DBNAME\t//DBName', f'{db}\t//DBName')
        content = content.replace('SYNC_DBSVR01\t//DSN', f'{dsn}\t//DSN')
        f.seek(0)
        f.write(content)
        f.truncate()


def update_xm8_config(db: str, xact_addr: str, path: str='./PLMSyncServer.cfg') -> bool:
    """ Updates PLMSyncServer.cfg to include xact addresses"""
    opening, middle, ending = _get_file_parts(path, '[SYNC_XM8TODBMAPPING]')
    
    new_line = f'{xact_addr}\t{db}\t1'
    middle = _add_sorted_line(middle, new_line)
    
    to_save = _combine_lines((opening, middle, ending))

    return save_config(path, to_save)

    
def update_sync_config(db: str, path: str='./PLMSyncServer.cfg') -> bool:
    """ Updates the sync objects part of PLMSyncServer.cfg"""
    
    opening, middle, ending = _get_file_parts(path, '[SYNC_PROJECTS]')

    new_line_parts = middle[0].split('\t')
    new_line_parts[0] = db
    new_line = '\t'.join(new_line_parts)
    middle = _add_sorted_line(middle, new_line)

    to_save = _combine_lines((opening, middle, ending))

    return save_config(path, to_save)


def _get_file_parts(path: str, start: str, end: str='[END]') -> Tuple[List[str]]:
    """ Reads file and separates into (opening, useful part, ending) """
    with open(path, 'r') as f:
        lines = f.read().splitlines()

    start_loc = lines.index(start) + 1

    opening = lines[:start_loc]
    middle = lines[:start_loc]

    end_loc = middle.index(end)
    middle = middle[:end_loc]

    ending = lines[end:]

    return opening, middle, ending


def _add_sorted_line(lines: List[str], new_line: str) -> List[str]:
    """ Appends new line to list and returns the sorted list """
    lines.append(new_line)
    lines.sort()

    return lines


def _combine_lines(parts: Tuple[List[str]]) -> List[str]:
    """ Flattens tuple of lists into list of strings ending with '\n' """
    return [
        row + '\n'
        for part in parts
        for row in part
    ]

def save_config(path: str, to_save: List[str]) -> bool:
    """ Saves the list of strings as config file """
    try:
        with open(path, 'r+') as f:
            f.seek(0)
            f.writelines(to_save)
            f.truncate()
        return True
    except Exception as e:
        print(e)
        return False


def insert_netsyncserver(db: str, svr: str='DBSVR03') -> None:
    """ Inserts rows into NetSyncServer2014 for company"""
    conn = pyodbc.connect(('Driver={SQL Server};Server=SYNCSVR01\\SYNCSVR;'
                        'Database=NETSyncServer2014;Trusted_Connection=yes;'))
    cur = conn.cursor()

    cur.execute(f"""SELECT * FROM INTEGRATIONS WHERE DBNAME = '{db}' """)
    if cur.fetchone():
        return

    sync_types = [
        'XM8_CORRUPDATE',
        'XM8_DOCUPDATE',
        'XM8_ASSIGNUPDATE',
    ]

    inserts = [[
        db,
        1,
        '2019-07-27 06:40:13.000',
        sync_type,
        'IDLE',
        svr,
        'PLMSyncUser',
        '!Miss0ur1',
    ] for sync_type in sync_types]

    que = """INSERT INTO INTEGRATIONS (
            DBNAME,
            RUN_EVERY_MINUTES,
            LAST_RUN,
            SYNC_TYPE,
            STATUS,
            DBSERVER,
            DBUSER,
            DBPASSWORD
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

    cur.executemany(que, inserts)
    cur.commit()


def filter_builder_emps(db: str, region: str, overwrite: bool=False) -> str:
    """ Creates new excel only with builder emps for that site"""
    if region == 'US':
        f_name = 'PuroClean_Builder_Emps.xlsx'
    elif region == 'CA':
        f_name = 'PuroClean_CA_Builder_Emps.xlsx'

    out_name = f'./builder_emps/{db}_builder_emp.xlsx'
    if os.path.isfile(out_name) and not overwrite:
        return out_name

    xls = pd.ExcelFile(f_name)
    with pd.ExcelWriter(out_name, engine='xlsxwriter') as writer:
        for sheetName in xls.sheet_names:
            sheet = pd.read_excel(f_name, sheet_name=sheetName)
            sheet = sheet[sheet['DBName'] == db].drop_duplicates()
            if sheet.empty:
                return ''
            sheet.to_excel(writer, sheet_name=sheetName)

    return out_name


def update_sites(row: pd.Series) -> None:
    """ Updates customers site table"""
    db = row['DB Name']

    row = row.drop('DB Name')
    conn = pyodbc.connect((f'Driver={{SQL Server}};Server=DBSVR03;'
                            f'Database={db};Trusted_Connection=yes;'))
    cur = conn.cursor()

    site_que = f"""UPDATE SITE
        SET {' = ?, '.join(row.index.tolist())} = ?
        FROM SITE
        WHERE SITE_ID = 1"""

    vals = [
        str(i) if str(i) != 'nan'
        else None
        for i in row.tolist()
    ]

    cur.execute(site_que, vals)
    cur.commit()

    builder_que = f"""UPDATE BUILDER SET
        build_BuilderName = '{row['site_SiteDesc']}',
        build_BuilderNameShort = '{db}',
        build_Address1 = '{row['site_Address1']}',
        build_Address2 = '{row['site_Address2']}',
        build_City = '{row['site_City']}',
        build_StateCD = '{row['site_StateCD']}',
        build_StateName = '{row['site_StateName']}',
        build_Zip = '{row['site_Zip']}',
        build_CityStateZip = '{row['site_CityStateZip']}',
        build_FullAddress = '{row['site_FullAddress']}',
        build_Email = '{row['site_ContEmail']}',
        BUILDER_Phone1 = '{row['site_ContPhone']}',
        build_PLMWebSite = 'http://{db}.restorationmanager.net',
        build_OwnerWebSite = 'http://{db}.restorationmanager.net',
        build_VendorWebSite = 'http://{db}.restorationmanager.net' """

    cur.execute(builder_que)
    cur.commit()


def insert_builder_emps(db: str, f_name: str) -> None:
    """ Inserts builder emps from the filtered excel file"""
    if not create_tables(db, f_name):
        print(f'{db} - No Builder Emps')
        return

    conn = pyodbc.connect((f'Driver={{SQL Server}};Server=DBSVR03;'
                        f'Database={db};Trusted_Connection=yes;'))
    cur = conn.cursor()

    with open('builder_emp_import.sql', 'r') as f:
        reader = f.read()
        scripts = reader.split(';')

    for script in scripts:
        try:
            cur.execute(script)
            cur.commit()
        except Exception as e:
            print(f'ERROR: {db}\t{script}\t{e}')
            return


def create_tables(db: str, f_name: str) -> bool:
    """ Creates tables in customer DB from excel file using pandas"""
    if not os.path.exists(f_name):
        return False

    cStr = urllib.parse.quote_plus((f"Driver={{SQL Server}};Server=DBSVR03;"
                                    f"Database={db};Trusted_Connection=yes;"))

    engine = sqlalchemy.create_engine(f'mssql+pyodbc:///?odbc_connect={cStr}')

    sheet_names = ['BuilderEmpPermission', 'BUILDER_Emp', 'BUILDER_EmpLogon']
    for sheet in sheet_names:
        df = pd.read_excel(f_name, sheet_name=sheet)

        if 'index' in df.columns:
            df = df.drop(['index'], axis=1)

        if sheet == 'BUILDER_EmpLogon':
            df = df.drop(['Builder_Emp_ID'], axis=1)

        try:
            df.to_sql(sheet+'$', engine, if_exists='replace')
        except Exception as e:
            print(f'ERROR: {db} Table {sheet} not created \t {e}')
            return False

    return True


def run_one(row: pd.Series, sites: pd.DataFrame, region: str) -> None:
    """ Runs all functions for one database"""
    all_databases = list_databases()

    if type(row['DB Name']) is not str:
        return

    if row['DB Name'] not in all_databases:
        print(f"No Database for {row['DB Name']}")
        return

    document_maker(row['DB Name'])
    intuitive_setup(row['DB Name'])
    update_plm_admin(row['DB Name'])
    update_logo_paths(row['DB Name'])
    create_netsync(row['DB Name'])
    insert_netsyncserver(row['DB Name'])

    
    # Make XM8 ThirdPartAuth XML
    if region == 'US':
        if pd.notna(row.account_id):
            make_ThirdPartAuth_xml(row['DB Name'], int(row.account_id))

        if pd.notna(row.xactnet_address):
            setup_xact(row['DB Name'], row.xactnet_address)
    elif region == 'CA':
        if pd.notna(row['Account ID']):
            make_ThirdPartAuth_xml(row['DB Name'], int(row['Account ID']))
        
        if pd.notna(row['XactNet Address']):
            setup_xact(row['DB Name'], row['XactNet Address'])

    # Update Site tables
    cur_site = sites[sites['DB Name'] == row['DB Name']]
    if cur_site.shape[0] >= 1:
        update_sites(cur_site.iloc[0])
    else:
        print(f"No Site: {row['DB Name']}")

    # Builder Emps
    be_file = filter_builder_emps(row['DB Name'], region)
    if be_file:
        print(f'file is {be_file}')
        insert_builder_emps(row['DB Name'], be_file)
    else:
        try:
            os.remove(f'./builder_emps/{db}_builder_emp.xlsx')
        except:
            print(f"{row['DB Name']} updated")
            return

    print(f"{row['DB Name']} updated")

    return


def run() -> None:
    args = get_args()
    if args.num:
        num = int(args.num)
    
    sites = open_sites(args.region)
    if args.db:
        comp = open_one_record(args.db, args.region)
        run_one(comp, sites, args.region)
    else:
        comps = open_data(num, args.region)
        for _, row in comps.iterrows():
            run_one(row, sites, args.region)

    # clean puroclean ThirdPartAuth
    # acnts = comps.account_id.dropna().astype('int').tolist()
    # cleanThirdPartAuth(acnts)


if __name__ == '__main__':
    run()

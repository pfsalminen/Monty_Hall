#!/usr/bin/env python3
# -*- coding:utf-8 -*-
""" Sets up each puroclean company
* Creates builder files folder from stub
* Updates logo paths in System_Settings
* Creates Intuitive Mobile folder from stub
    * Updates html to have dbname
* Creates ThirdPartAuth XML
* Adds row to customer table using SERVPROMASTERDB
* Adds row to tblAuth table using SERVPROMASTERDB
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
    intiutiveMobile- change the managerline

    update update_plm_admin() for any customer
    update update_logo_paths() for any customer
    update update_sites() for any customer
    Check out builder files stuffs

"""
import os
import sys
import xml.etree.ElementTree as ET
import dataclasses
import datetime
import subprocess
import urllib
import sqlalchemy
import pandas as pd
import pyodbc
import utils
import storage
import connections
sys.path.insert(0,
                os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class Provision(storage.Company):
    """ Class with functions to provision new database
    Inherits variables form Company (and Master)
    Init vars: db, svr, bakLoc, bfLoc, master, nssLoc, nssConfig"""
    def init(self):
        self.all_databases = utils.list_databases(self.svr)

        self.conn = pyodbc.connect((f"Driver={{SQL Server}};Server={self.svr};"
                                    "Database=master;Trusted_Connection=yes;"))
        self.conn.autocommit = True

    def create_database(self) -> None:
        """ Creates a new DB from a backup file"""
        cur = self.conn.cursor()

        # See if db already exists
        if self.db in self.all_databases:
            print(f'Database {self.db} exists in {self.svr}')
            return

        que = f"""
        RESTORE DATABASE [{self.db}] FROM  DISK = N'{self.sql_bakloc()}' 
        WITH FILE = 1, NOUNLOAD, STATS = 10, RECOVERY, 
        MOVE 'SERVPROTRAINING_Data' TO 'D:\\SQL DATA\\{self.db}.mdf', 
        MOVE 'SERVPROTRAINING_Log' TO 'D:\\SQL DATA\\{self.db}.ldf' """

        cur.execute(que)

    def build_site(self) -> None:
        """ Runs the buildSite cmd for the database name"""
        subprocess.check_output(["cmd", "/c", "./buildSite.cmd", self.db])

    def document_maker(self) -> None:
        """ Copies all files from the masterDB builder files folder
        to a new company folder"""

        master = os.path.join(self.bfLoc, self.master_copy)
        company = os.path.join(self.bfLoc, self.db)

        utils.copy_folder(master, company)

    def intuitive_setup(self) -> None:
        """ Create the intuitive mobile folder from stub copy
        and then edits the HTML for company name"""

        master = os.path.join(self.intLoc, self.master_copy)
        company = os.path.join(self.intLoc, self.db)

        utils.copy_folder(master, company)

        html = os.path.join(company, 'masterlogin.html')
        with open(html, 'r+') as f:
            content = f.read()
            content = content.replace(self.master_copy, self.db)
            content = content.replace('MOBILEMANAGER', self.manager)
            f.seek(0)
            f.write(content)
            f.truncate()

    def make_ThirdPartAuth_xml(self) -> None:
        """ Writes the ThirdPartAuth XML"""

        if not self.tpaID:
            print('No ThirdPartyID')
            return
        if not self.accnt_id:
            print('No Account Id')
            return

        tpaLoc = '//syncsvr01/Netsyncserver/XactwareIntegration/ThirdPartAuth'
        out_name = os.path.join(tpaLoc, f'xm8auth_{self.db}.xml')

        if os.path.exists(out_name):
            return

        root = ET.Element('XACTDOC')
        doc = ET.SubElement(root, 'XACTNET_INFO', f'thirdPartyId=3364615')
        companies = ET.SubElement(root, 'COMPANIES')
        company = ET.SubElement(companies,
                                'COMPANY',
                                action="enable",
                                id=f"{self.accnt_id}",
                                name=f"{self.db}")
        tree = ET.ElementTree(root)

        tree.write(out_name, encoding='UTF-8', xml_declaration=True)

    def update_plm_admin(self) -> None:
        """ Makes updated to customers and tblAuth """

        cur = connections.DBSVR01.cursor()

        cur.execute(("SELECT * FROM Customers "
                     f"WHERE CustomerCode = '{self.db}' "))
        if not cur.fetchone():
            self.update_customers(cur)

        cur.execute(("SELECT * FROM tblAuth " f"WHERE Company = '{self.db}' "))
        if not cur.fetchone():
            self.update_tblAuth(cur)

    def update_customers(self, cur: pyodbc.Cursor) -> None:
        """ Inserts row for customer into customers"""

        cust_que = ("SELECT * FROM Customers "
                    f"WHERE CustomerCode = '{self.master_copy}' ")
        exe_desc = cur.execute(cust_que).description
        customer = {k[0].lower(): v for k, v in zip(exe_desc, cur.fetchone())}

        # Delete fields that are autopopulated
        del customer['customer_id']
        del customer['customer_guid']
        del customer['recorddatetime']

        customer['customercode'] = self.db
        customer['notes'] = f'Site Provisioned on {datetime.datetime.now()}'
        customer['baseurl'] = f'{self.db}.restorationmanager.net'
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
            print(f'No customer row: {self.db}\tException: {e}')

    def update_tblAuth(self, cur: pyodbc.Cursor) -> None:
        """Inserts row for customer into tblAuth"""

        auth_que = ("SELECT * FROM tblAuth "
                    f"WHERE COMPANY = '{self.master_copy}' ")
        exe_desc = cur.execute(auth_que).description
        auth = {k[0].lower(): v for k, v in zip(exe_desc, cur.fetchone())}

        cur.execute(("SELECT Customer_ID FROM Customers "
                     f"WHERE CustomerCode='{self.db}' "))
        customer_id = cur.fetchone()[0]

        # Delete autopopulated fields
        del auth['id'], auth['recorddatetime']

        auth['company'] = self.db
        auth['password'] = (self.db)[::-1]
        auth['db_name'] = self.db
        auth['image_directory'] = auth['image_directory'].replace(
            self.master_copy, self.db)
        auth['customer_id'] = customer_id
        auth['db_dsn'] = 'INT_DBSVR03'
        auth['emailsync_email'] = f"{self.db}@servicesoftwareinc.com"
        auth['emailsync_pw'] = '!SSllc3mail!'
        auth['qbonline_enabled'] = int(self.QBO)

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
            print(f'No tblAuth row: {self.db}\tException: {e}')

    def setup_xact(self) -> None:
        """ Runs provision stored procedure
        and adds xn address to company database"""

        if not self.xactnet_addr:
            print('Please provide XactNet Addrress')
            return

        self.run_jobtoxa()
        self.update_xn_address()

    def run_jobtoxa(self) -> None:
        """ Runs Provision_XM8_JOBRMTOXA stores procedure"""

        conn = pyodbc.connect(
            ('Driver={SQL Server};Server=SYNCSVR01\\SYNCSVR;'
             'Database=NETSyncServer2014;Trusted_Connection=yes;'))
        cur = conn.cursor()

        que = f"""EXEC Provision_XM8_JOBRMTOXA '{self.db}','{self.svr}' """
        cur.execute(que)
        cur.commit()

    def update_xn_address(self) -> None:
        """ Inserts XN addresses into customer DB"""

        conn = pyodbc.connect((f'Driver={{SQL Server}};Server={self.svr};'
                               f'Database={self.db};Trusted_Connection=yes;'))
        cur = conn.cursor()

        cur.execute('SELECT XactNetAddress FROM XNADDRESS')
        results = [i[0] for i in cur.fetchall()]
        if self.xactnet_addr in results:
            return

        que = ("INSERT INTO XNAddress(XactNetAddress) "
               f"VALUES ('{self.xactnet_addr}')")
        cur.execute(que)
        cur.commit()

    def update_logo_paths(self) -> None:
        """ Changes the system settings table logo paths
        from the master db to company db"""

        conn = pyodbc.connect((f'Driver={{SQL Server}};Server={self.svr};'
                               f'Database={self.db};Trusted_Connection=yes;'))
        cur = conn.cursor()

        que = 'SELECT Logo, LogoReports FROM System_Settings'
        cur.execute(que)
        logo, logo_reports = cur.fetchone()

        if self.master_copy not in logo and self.master_copy not in logo_reports:
            return

        logo = logo.replace(self.master_copy, self.db)
        logo_reports = logo_reports.replace(self.master_copy, self.db)

        update_que = f""" UPDATE SYSTEM_Settings
            SET Logo='{logo}',
            LogoReports='{logo_reports}' """

        try:
            cur.execute(update_que)
            cur.commit()
        except Exception as e:
            print(f'Settings not updated: {self.db}\tException: {e}')

    def create_netsync(self) -> None:
        """ Creates netsyncserver folder for comapny"""

        master = os.path.join(self.nssLoc, self.master_copy)
        company = os.path.join(self.nssLoc, self.db)

        utils.copy_folder(master, company)

        self.update_netsync()

    def update_netsync(self) -> None:
        """ Updates SyncServerProject for company"""

        with open(os.path.join(self.nssLoc, self.db, 'SyncServerProject.cfg'),
                  'r+') as f:
            content = f.read()
            content = content.replace(f'{self.master_copy}\t//DBName',
                                      f'{self.db}\t//DBName')
            content = content.replace(f'DEFAULTDSN\t//DSN',
                                      f'{self.dsn()}\t//DSN')
            f.seek(0)
            f.write(content)
            f.truncate()

    def update_xm8_config(self) -> bool:
        """ Updates PLMSyncServer.cfg to include xact addresses"""

        path = os.path.join(self.nssLoc, 'PLMSyncServer.cfg')

        opening, middle, ending = utils.get_file_parts(
            path, '[SYNC_XM8TODBMAPPING]')

        new_line = f'{self.xactnet_addr.upper()}\t{self.db.upper()}\t1'
        middle = utils.add_sorted_line(middle, new_line)

        to_save = utils.combine_lines((opening, middle, ending))

        return utils.save_config(path, to_save)

    def update_sync_config(self) -> bool:
        """ Updates the sync objects part of PLMSyncServer.cfg"""

        path = os.path.join(self.nssLoc, 'PLMSyncServer.cfg')

        opening, middle, ending = utils.get_file_parts(
            path, '[SYNC_PROJECTS]')

        new_line_parts = middle[0].split('\t')
        new_line_parts[0] = self.db.upper()
        new_line = '\t'.join(new_line_parts)

        middle = utils.add_sorted_line(middle, new_line)

        to_save = utils.combine_lines((opening, middle, ending))

        return utils.save_config(path, to_save)

    def insert_netsyncserver(self) -> None:
        """ Inserts rows into NetSyncServer2014 for company"""

        conn = pyodbc.connect(
            ('Driver={SQL Server};Server=SYNCSVR01\\SYNCSVR;'
             'Database=NETSyncServer2014;Trusted_Connection=yes;'))
        cur = conn.cursor()

        cur.execute(f"SELECT * FROM INTEGRATIONS WHERE DBNAME = '{self.db}' ")
        if cur.fetchone():
            return

        sync_types = [
            'XM8_CORRUPDATE',
            'XM8_DOCUPDATE',
            'XM8_ASSIGNUPDATE',
        ]

        inserts = [[
            self.db,
            1,
            '2019-07-27 06:40:13.000',
            sync_type,
            'IDLE',
            self.svr,
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

    def update_site(self, row: pd.Series) -> None:
        """ Updates customers site table"""

        row['Site_Code'] = str(row.Site_Code)[-4:]
        row = row.drop('DB Name')

        conn = pyodbc.connect((f'Driver={{SQL Server}};Server={self.svr};'
                               f'Database={self.db};Trusted_Connection=yes;'))
        cur = conn.cursor()

        site_que = f"""UPDATE SITE
            SET {' = ?, '.join(row.index.tolist())} = ?
            FROM SITE
            WHERE SITE_ID = 1"""

        vals = [str(i) if str(i) != 'nan' else None for i in row.tolist()]

        cur.execute(site_que, vals)
        cur.commit()

    def update_builder(self, row: pd.Series) -> None:
        """ Update customer builder table"""

        row = row.drop('DB Name')

        conn = pyodbc.connect((f'Driver={{SQL Server}};Server={self.svr};'
                               f'Database={self.db};Trusted_Connection=yes;'))
        cur = conn.cursor()

        builder_que = f"""UPDATE BUILDER SET
            build_BuilderName = '{row['site_SiteDesc']}',
            build_BuilderNameShort = '{self.db}',
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
            build_PLMWebSite = 'http://{self.db}.restorationmanager.net',
            build_OwnerWebSite = 'http://{self.db}.restorationmanager.net',
            build_VendorWebSite = 'http://{self.db}.restorationmanager.net' """

        cur.execute(builder_que)
        cur.commit()


class BuilderEmps(storage.Company):
    """ Class for files to import builder Emps from spreadsheet"""
    def filter_builder_emps(self, f_name: str, overwrite: bool = False) -> str:
        """ Creates new excel only with builder emps for that site"""

        out_name = f'./builder_emps/{self.db}_builder_emp.xlsx'
        if os.path.isfile(out_name) and not overwrite:
            return out_name

        xls = pd.ExcelFile(f_name)
        with pd.ExcelWriter(out_name, engine='xlsxwriter') as writer:
            for sheet_names in xls.sheet_names:
                sheet = pd.read_excel(f_name, sheet_name=sheet_names)
                sheet = sheet[sheet['DBName'] == self.db].drop_duplicates()
                if sheet.empty:
                    return ''
                sheet.to_excel(writer, sheet_name=sheet_names, index=False)

        return out_name

    def create_tables(self, f_name: str) -> bool:
        """ Creates tables in customer DB from excel file using pandas"""

        if not os.path.exists(f_name):
            return False

        conn_str = urllib.parse.quote_plus(
            (f"Driver={{SQL Server}};Server={self.svr};"
             f"Database={self.db};Trusted_Connection=yes;"))
        engine = sqlalchemy.create_engine(
            f'mssql+pyodbc:///?odbc_connect={conn_str}')

        sheet_names = [
            'BuilderEmpPermission',
            'BUILDER_Emp',
            'BUILDER_EmpLogon',
            'Builder_EmpReportsPermissions',
        ]
        for sheet in sheet_names:
            df = pd.read_excel(f_name, sheet_name=sheet)

            if 'index' in df.columns:
                df = df.drop(['index'], axis=1)

            if sheet == 'BUILDER_EmpLogon':
                df = df.drop(['Builder_Emp_ID'], axis=1)

            try:
                df.to_sql(sheet + '$', engine, if_exists='replace')
            except Exception as e:
                print(f'ERROR: {self.db} Table {sheet} not created \t {e}')
                return False

        return True

    def insert_builder_emps(self, f_name: str) -> None:
        """ Inserts builder emps from the filtered excel file"""

        if not self.create_tables(f_name):
            print(f'{self.db} - No Builder Emps')
            return

        conn = pyodbc.connect((f'Driver={{SQL Server}};Server=DBSVR03;'
                               f'Database={self.db};Trusted_Connection=yes;'))
        cur = conn.cursor()

        with open('builder_emp_import.sql', 'r') as f:
            reader = f.read()
            scripts = reader.split(';')

        for script in scripts:
            try:
                cur.execute(script)
                cur.commit()
            except Exception as e:
                print(f'ERROR: {self.db}\t{script}\t{e}')
                return


def open_sites() -> pd.DataFrame:
    """ Reads in sites file"""
    df = (pd.read_excel('servpro_sites.xlsx',
                        sheet_name='Site Import').dropna(subset=['DB Name']))
    df['RecordSource_FKey'] = df['site_SiteDesc']
    df['REGION_ID'] = 1

    return df


def open_data() -> pd.DataFrame:
    """ Read in master excel and clean column names"""
    df = (pd.read_excel('servpro_master.xlsx',
                        sheet_name='Franchise Master Setup').fillna({
                            'Setup Priority':
                            -1
                        }).loc[lambda df: df['Signed Up?'] == 'Yes'].dropna(
                            subset=['DB Name']))

    return df


def open_one_record(db: str) -> pd.Series:
    """ Reads in one row from master excel"""

    df = (pd.read_excel('servpro_master.xlsx',
                        sheet_name='Franchise Master Setup').fillna({
                            'Setup Priority':
                            -1
                        }).loc[lambda df: df['Signed Up?'] == 'Yes'].
          loc[lambda df: df['DB Name'] == db])

    if not df.empty:
        return df.iloc[0]
    return pd.Series()


def run_one(company: storage.Company, site: pd.Series) -> None:
    """ Runs all functions for one database"""

    provision = Provision(**dataclasses.asdict(company))

    if not provision.db:
        return

    provision.document_maker()
    provision.intuitive_setup()
    provision.update_plm_admin()
    provision.update_logo_paths()
    provision.create_netsync()
    provision.update_sync_config()
    provision.update_xm8_config()
    provision.insert_netsyncserver()
    provision.make_ThirdPartAuth_xml()
    provision.setup_xact()

    # Update Site tables
    if site:
        provision.update_site(site)
        provision.update_builder(site)
    else:
        print(f"No Site: {provision.db}")

    # Builder Emps
    f_name = 'Servpro_Builder_Emps.xlsx'
    if f_name:
        be = BuilderEmps(**dataclasses.asdict(company))
        be_file = be.filter_builder_emps(f_name)

    if be_file:
        be.insert_builder_emps(be_file)
    else:
        print('Builder Emps not updated.')
        print(f"{storage.db} updated")

        return

    print(f"{storage.db} updated")

    return


def run() -> None:
    """ Main function that runs if called directly"""
    sites = open_sites()
    comps = open_data()
    master = storage.Master(master_copy='SERVPROMASTERDB',
                            bakLoc=('//DBSVR02/SQLBackups/'
                                    'SERVPROMASTERDB_FINAL_20190829.bak'))

    for _, row in comps.iterrows():
        company = storage.Company(db=row['DB Name'],
                                  svr='DBSVR03',
                                  accnt_id=row['Account ID'],
                                  QBO=True,
                                  xactnet_addr=row['XactNet Address'],
                                  **dataclasses.asdict(master))

        # create_database(row['DB Name'], BAKLOC, 'DBSVR03')
        # print(f"{row['DB Name']} - Database created. ")

        site = sites[sites['DB Name'] == row['DB Name']]
        if site.shape[0] >= 1:
            site = site.iloc[0]
        else:
            site = None

        run_one(company, site)


if __name__ == '__main__':
    run()

import os
import pyodbc
import time
import argparse
from datetime import datetime
import sys


def document_sql(svr: str, db: str, bfpath: str) -> None:
    sys.stdout = open("results_SQL.txt", "w")

    starttime = time.time()
    print(datetime.utcfromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S'))

    paths = []

    for root, _, files in os.walk(bfpath + "/Sites"):
        for f in files:
            if "Job_" in root:
                paths.append([root, f])

    shortDir, fName = list(zip(*paths))

    job_id = [x.split('\\')[5].split('_')[1] for x in shortDir]
    doc_desc = [f.replace("'", "''") for f in fName]
    doc_title = [f.replace("'", "''") for f in fName]
    doc_path = [
        d.replace(bfpath, '') + '\\' + f.replace("'", "''") for d, f in paths
    ]

    params = [[
        path2, id, desc, title, path
    ] for (path2, id, desc, title,
           path) in zip(doc_path, job_id, doc_desc, doc_title, doc_path)]

    query = "BEGIN IF NOT EXISTS (SELECT * FROM JOB_Document WHERE Document_Path = ?) BEGIN INSERT INTO JOB_Document (JOB_ID,Document_Deleted,Document_Viewable,Document_Desc,Document_Title,Document_Path,ViewableInProjectPortal,RecordSource_FKey3) \
			VALUES (?,0,1,?,?,?,1,'DASH Migration') END END"

    cnxn = pyodbc.connect(r'Driver={SQL Server};Server=' + svr + ';Database=' +
                          db + ';Trusted_Connection=yes;autocommit=True')
    cnxn.autocommit = True
    cursor = cnxn.cursor()
    print(query)
    cursor.executemany(query, params)

    query2 = "INSERT INTO JOB_Folder (JOB_ID, FolderName, IsLocked) SELECT DISTINCT jd.JOB_ID, SUBSTRING(Document_Path,68,CHARINDEX('\\',Document_Path,68)-68), 0 FROM JOB_Document jd WHERE jd.RecordSource_FKey3 = 'DASH Migration' AND CHARINDEX('\\',Document_Path,68) <> 0 AND Document_Path NOT LIKE '%\\MergeDocuments\\%'"
    query3 = "UPDATE JOB_Document SET JOB_Folder_ID = jf.JOB_Folder_ID FROM JOB_Folder jf INNER JOIN JOB_Document jd on SUBSTRING(jd.Document_Path,68,CHARINDEX('\\',jd.Document_Path,68)-68) = jf.FolderName AND jf.JOB_ID = jd.JOB_ID WHERE jd.RecordSource_FKey3 = 'DASH Migration' AND CHARINDEX('\\',Document_Path,68) <> 0 AND Document_Path NOT LIKE '%\\MergeDocuments\\%'"
    print(query2)
    cursor.execute(query2)
    print(query3)
    cursor.execute(query3)

    cnxn.close()
    endtime = time.time()

    print('Run time: ' + str(endtime - starttime) + ' seconds')
    print('Run time: ' + str((endtime - starttime) / 60) + ' minutes')

    sys.stdout.close()


def run() -> None:
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

    document_sql(config['svr'], config['db'],
                 os.path.join(config['bfbase'], config['db']))


if __name__ == '__main__':
    run()

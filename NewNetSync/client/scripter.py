#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import json
import requests
from typing import Dict, List
from ftplib import FTP 
import pyodbc

class InfoExchange:
    """Holds functions for interacting with the AWS API"""

    def __init__(self, companyName: str=None, outDir: str=''):
        if outDir:
            self.outDir = outDir
        else:
            print('Using default output dir')
            self.outDir = 'C:\\Program Files\\Service Software\\outBox'

        self.companyName = companyName
        assert self.companyName, 'companyName cannot be blank'

        now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.resultsKey = f'{companyName}/results_{now}.json'

        self.outFile = os.path.join(self.outDir, self.resultsKey)

    def get_runtime_scripts(self) -> None:
        """Sends GET request to lambda function
        Saves presigned GET URL for the script s3 bucket
        and presigned POST URL to results s3 bucket
        """
        LAMBDAURL = 'https://i98a7tv185.execute-api.us-west-1.amazonaws.com/test'

        payload = {"companyName": self.companyName,
                    "resultsKey": self.resultsKey}

        req = requests.get(LAMBDAURL, params=payload)
        assert req.status_code == 200, "Error in get request"
        data = req.json()

        self.scripts = requests.get(data['scriptUrl']).json()
        self.postInfo = data['postUrl']

    def save_file(self, contents: str) -> None:
        """Saves file to designated outFile

        Args:
            contents: JSON-like string
        """
        with open(self.outFile, 'w') as f:
            json.dump(contents, f)

    def s3Upload(self, contents: str='') -> bool:
        """ Uploads results to s3 bucket
        
        Args: 
            contents: JSON-like string
        Returns:
            bool: whether upload was a success
        """
        if contents:
            file_toSend = {self.resultsKey: contents}
        else:
            with open(self.outFile, 'rb') as file_:
                file_toSend = {self.resultsKey: json.load(file_)}
        
        response = requests.post(self.postInfo['url'], 
                                data=self.postInfo['fields'], 
                                files=file_toSend)

        if response.status_code == 200:
            return True
        else:
            return False

    def ftpUpload(self) -> None:
        """Uploads file to our server via FTP (last resort)
        """
        with open(self.outFile, 'rb') as file_:
            with FTP(host='servicesoftwareinc.com') as ftp:
                ftp.login(user='owner', passwd='punchlist')
                ftp.cwd(f'./SYNC/{self.companyName}/InBox/')
                ftp.storbinary(f'STOR {self.outFile}', json.load(file_))
                ftp.quit()


class Scripter:
    """Functions for running integration scripts"""

    def __init__(self, integrationName: str, queryName: str, 
                script: str, opts: Dict[str]):

        self.integrationName = integrationName
        self.queryName = queryName
        self.script = script

        odbc = opts.get('odbc_name')
        username = opts.get('user')
        passwd = opts.get('password')
        assert (odbc and username and passwd), "ODBC information missing"

        self.queryCur = self._connect_query(odbc, username, passwd)

    def _connect_query(self, odbc: str, user: str, passwd: str) -> pyodbc.Cursor:
        queryConn = pyodbc.connect(f'DSN={odbc};UID={user};PWD={passwd}',
                                    autocommit=True)
        return queryConn.cursor()

    def run_query(self) -> Dict:
        self.queryCur.execute(self.script)
        headers = [column[0] for column in self.queryCur.description]
        data = self.queryCur.fetchall()

        return self._prepare_json(headers, data)

    def _prepare_json(self, headers: List[str], data: List) -> Dict:
        dataList = []
        for row in data():
            rowDict = {col : dat for col, dat in zip(headers, row)}
            dataList.append(rowDict)

        toJSON = {
            'integrationName': self.integrationName,
            'queryName': self.queryName,
            'data': dataList,
        }

        return toJSON


def run() -> None:
    """Gets and runs integration scripts"""
    CONFIGFILE = './data/CONFIG.json'
    with open(CONFIGFILE, 'r') as jsonFile:
        CONFIG = json.load(jsonFile)

    exchanger = InfoExchange(CONFIG['company_name'], CONFIG['output_dir'])
    exchanger.get_runtime_scripts()
    results = {}

    for integration, intScripts in exchanger.scripts.items():
        opts = CONFIG['odbc_sources'].get(integration)

        for query, script in intScripts.items():
            runner = Scripter(integration, query, script, opts)
            results[query] = runner.run_query()

    jsonResults = json.dumps(results)

    uploaded = exchanger.s3Upload(jsonResults)
    if not uploaded:
        exchanger.save_file(jsonResults)
        exchanger.ftpUpload()


if __name__=='__main__':
    run()

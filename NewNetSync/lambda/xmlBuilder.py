#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sqlite3
import datetime
import os

db = sqlite3.connect('./configDB.sqlite')
cur = db.cursor()


class xmlBuilder:

    def __init__(self, outDir, intName, queryName, headers, data):
        self.outDir = outDir
        self.intName = intName
        self.queryName = queryName
        self.data = data
        self.headers = headers

        self._load_xml_settings()

    def _load_xml_settings(self):
        query = '''SELECT syncObjName, beginning, end FROM xmlSchemas WHERE queryName = ?'''
        cur.execute(query, (self.queryName,))
        self.objName, self.xmlBeginning, self.xmlEnd = cur.fetchone()

    def build_xml(self):
        # Build XML Schema
        self.xmlString = self.xmlBeginning
        for column in self.headers:
            self.xmlString += f'\n                <xs:element name="{column}" type="xs:string" minOccurs="0" />'
        self.xmlString += f'\n {self.xmlEnd}'

        # Add Data to XML
        for row in self.data:
            self.xmlString += f'\n <{self.objName}>'
            for i, item in enumerate(row):
                self.xmlString += f'\n    <{self.headers[i]}>{item}</{self.headers[i]}>'
            self.xmlString += f'\n </{self.objName}>'
        self.xmlString += '\n</dsOutput>'

        return(self.xmlString)

    def save_xml(self):
        with open(os.path.join(self.outDir, self.xmlName()), 'w') as f:
            f.write(self.xmlString)

    def xml_name(self):
        now = datetime.datetime.now().strftime('%Y_%j_%H_%M_%S')
        return f'{self.queryName}_{self.intName}_{now}.xml'


def test():
    headers, data = tester.getData()
    builder = xmlBuilder('./', 'BMT', 'JOB', headers, data)
    builder.build_xml()
    builder.save_xml()

if __name__=='__main__':
    test()

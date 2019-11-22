#!/usr/bin/env python3
# -*- coding:utf-8 -*-
""" New Net Sync Client GUI adds/modifies/deletes customer scripts from S3

TODO:
    Changing Company/Script source breaks it
    Get add/delete +/- buttons to work

Notes:

    For searching "folders"
        result = client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter='/')
    
    To get unique "folders"
        sorted(set([
            os.path.dirname(x.key)
            for x in self.bucket.list()
        ]))
"""

import os
import sys
import json
import types
import datetime
from collections import defaultdict
import boto
from PySide2 import QtCore, QtGui, QtWidgets
import qtawesome as qta
from qtmodern.styles import dark
from gui import config, popups, syntaxer


class App(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.item = None
        self.comp = None

        self._create_s3_connection()
        self.get_scripts()

        flags = QtCore.Qt.WindowFlags(QtCore.Qt.WindowShadeButtonHint)
        self.setWindowFlags(flags)
        self.title = 'Net_Sync Client'

        left = 20
        top = 100
        self.width = 1200
        self.height = 800
        self.setGeometry(QtCore.QRect(left, top, self.width, self.height))

        self.font = QtGui.QFont("Arial", 12)
        self.setFont(self.font)

        self.initUI()

    def _create_s3_connection(self):
        try:
            self.conn = boto.s3.connect_to_region(
                'us-west-2',
                aws_access_key_id=config.AWS_KEY,
                aws_secret_access_key=config.AWS_SECRET)
        except:
            # Test to see if this shows on its own
            # Maybe I need to create a popups.ErrorPopup.show() ?
            error = popups.ErrorPopup('No Internet Connection')
            error.show()
            raise RuntimeError('Cannot connect to internet')
        else:
            self.bucket = self.conn.get_bucket('integrationconfigs')

    def initUI(self):
        self.setWindowTitle(self.title)
        self.scriptsInfoBox = QtWidgets.QGroupBox('Integration')
        self.buttonGB = QtWidgets.QGroupBox('')
        self.infoLayout = QtWidgets.QVBoxLayout()

        self.script_title = QtWidgets.QLineEdit()
        self.script_title.resize(self.width * 4 / 5, self.height / 5)
        self.script_title.setFont(self.font)
        self.infoLayout.addWidget(self.script_title)

        self.script_box = QtWidgets.QPlainTextEdit()
        self.script_box.setFont(self.font)
        self.script_box.setTabStopWidth(
            4 * QtGui.QFontMetrics(self.font).width('  '))
        self.script_box.resize(self.width * 4 / 5, self.height * 3 / 5)
        self.syntax = syntaxer.SQLHighlighter(self.script_box.document())
        self.infoLayout.addWidget(self.script_box)

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.saveButton = QtWidgets.QPushButton('Save Script')
        self.saveButton.resize(self.width * 1 / 3, self.height * 1 / 6)
        self.saveButton.clicked.connect(self.save_script)
        self.saveButton.setFont(self.font)
        self.buttonLayout.addWidget(self.saveButton)

        self.newButton = QtWidgets.QPushButton('New Script')
        self.newButton.resize(self.width * 1 / 3, self.height * 1 / 6)
        self.newButton.clicked.connect(self.create_new_script)
        self.newButton.setFont(self.font)
        self.buttonLayout.addWidget(self.newButton)
        self.buttonGB.setLayout(self.buttonLayout)

        self.infoLayout.addWidget(self.buttonGB)
        self.scriptsInfoBox.setLayout(self.infoLayout)

        self.windowLayout = QtWidgets.QHBoxLayout()

        self.choiceBox = QtWidgets.QGroupBox('Select')
        self.choiceLayout = QtWidgets.QVBoxLayout()

        self.companyBox = QtWidgets.QComboBox()
        self.populate_companies()
        self.companyBox.activated[str].connect(self.populate_versions)
        self.choiceLayout.addWidget(self.companyBox)

        self.company_files = QtWidgets.QListWidget()
        self.company_files.itemClicked.connect(self.load_tree)
        self.company_files.resize(self.width / 5, self.height / 3)
        self.choiceLayout.addWidget(self.company_files)

        self.script_tree = QtWidgets.QTreeView(self)
        self.script_tree.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.script_tree.setFont(self.font)

        self.script_tree.clicked[QtCore.QModelIndex].connect(
            self.show_selected_script)
        self.script_tree.resize(self.width / 5, self.height / 3)
        self.choiceLayout.addWidget(self.script_tree)

        self.intBtnLayout = QtWidgets.QHBoxLayout()
        self.intBtnAdd = QtWidgets.QPushButton()
        self.addIcon = qta.icon('mdi.plus', color='grey')
        self.intBtnAdd.setIcon(self.addIcon)
        self.intBtnAdd.clicked.connect(self.add_integration)
        self.intBtnLayout.addWidget(self.intBtnAdd)

        self.intBtnDelete = QtWidgets.QPushButton()
        self.minusIcon = qta.icon('mdi.minus', color='grey')
        self.intBtnDelete.setIcon(self.minusIcon)
        self.intBtnDelete.clicked.connect(self.delete_integration)
        self.intBtnLayout.addWidget(self.intBtnDelete)
        self.choiceLayout.addLayout(self.intBtnLayout)

        self.compBtnLayout = QtWidgets.QHBoxLayout()
        self.compBtnAdd = QtWidgets.QPushButton("Add Company")
        self.compBtnAdd.clicked.connect(self.add_company)
        self.compBtnLayout.addWidget(self.compBtnAdd)

        self.compBtnDelete = QtWidgets.QPushButton("Delete")
        self.compBtnAdd.clicked.connect(self.delete_company)
        self.compBtnLayout.addWidget(self.compBtnDelete)
        self.choiceLayout.addLayout(self.compBtnLayout)

        self.choiceBox.setLayout(self.choiceLayout)
        self.windowLayout.addWidget(self.choiceBox, 1)

        self.windowLayout.addWidget(self.scriptsInfoBox, 3)
        self.setLayout(self.windowLayout)

    def load_tree(self, choice):
        self.script_tree.setModel(None)
        self.scripts = self.get_script(choice)

        self.root_model = QtGui.QStandardItemModel()
        self.script_tree.setModel(self.root_model)
        self.populate_tree(self.scripts, self.root_model.invisibleRootItem())

    def get_script(self, choice):
        self.scriptName = f'{self.comp}/{choice.text()}'
        k = boto.s3.key.Key(self.bucket, self.scriptName)
        return json.loads(k.get_contents_as_string())

    def get_scripts(self, company: str = None):
        self.companyScripts = defaultdict(list)

        for file_ in self.bucket.list(prefix=company):
            fName = file_.key
            if fName.split('.')[-1] == 'json':
                company, version = fName.split('/')
                self.companyScripts[company].append(version)

    def populate_companies(self):
        self.companyBox.clear()
        self.companyBox.addItem('--------')
        for company in self.companyScripts.keys():
            self.companyBox.addItem(company)

    def populate_versions(self, comp: str):
        self.comp = comp
        for file_ in self.companyScripts[comp]:
            self.company_files.addItem(file_)

    def populate_tree(self, children, parent):
        if type(children) is dict:
            for key, val in sorted(children.items()):
                child = QtGui.QStandardItem()
                child.setText(key)
                parent.appendRow(child)
                if type(val) is dict:
                    self.populate_tree(val, child)
        else:
            child = QtGui.QStandardItem()
            child.setText(children)
            parent.appendRow(child)

    def show_selected_script(self, index: int):
        if self.item:
            self.scripts[self.item.parent().text()][
                self.item.text()] = self.script_box.toPlainText()

        self.item = self.root_model.itemFromIndex(index)
        scriptBody = self.scripts[self.item.parent().text()][self.item.text()]

        self.script_title.setText(self.item.text())
        self.script_box.clear()
        self.script_box.setPlainText(scriptBody)

    def save_script(self):
        """ Save current script to S3, acts on save button press
        """
        self._animate_save_button()

        # Update current script to textbox contents
        self.scripts[self.item.parent().text()][
            self.item.text()] = self.script_box.toPlainText()

        self._save_script()

        # TODO
        # Figure this part out - reloading all trees/scripts after save
        if self.item.text() != self.script_title.text():
            self.script_tree.setModel(None)
            del self.root_model
            self.loadCompanyTree(self.comp)

        self._reset_save_button()

    def _save_script(self):
        """ Create key from date and write to s3
        """
        newScriptName = f"{self.comp}/{datetime.datetime.now().strftime('%Y%m%d')}.json"
        k = boto.s3.key.Key(self.bucket, newScriptName)
        k.set_contents_from_string(json.dumps(self.scripts))

    def _animate_save_button(self):
        """ Starts animation on save button
        """
        spin_icon = qta.icon('fa5s.spinner',
                             color='grey',
                             animation=qta.Spin(self.saveButton))
        self.saveButton.setText('')
        self.saveButton.setIcon(spin_icon)
        QtWidgets.QApplication.processEvents()

    def _reset_save_button(self):
        """ Resets save button to text after animation
        """
        self.saveButton.setIcon(QtGui.QIcon())
        self.saveButton.setText('Save Script')
        QtWidgets.QApplication.processEvents()

    def create_new_script(self):
        """ Create a new script for a company/integration
        Saves current script, and clears all text boxes. 
        """
        self.save_script()
        self.script_title.clear()
        self.script_box.clear()

    def add_integration(self):
        """ Add new integration type for a company (ie. BMT)
        self.newIntPopup = popups.NewIntegrationPopup()
        self.newIntPopup.show()
        self.newIntPopup.saveBtn.clicked.connect(self._add_integration)
        """
        return

    def _add_integration(self):
        newIntegrationName = self.newIntPopup.intNameBox.text()
        self.scripts[newIntegrationName][newIntegrationName] = ''
        self._save_script()
        self.populate_companies()
        self.loadCom

    def delete_integration(self):
        """ Deletes a specific integration type for a company (ie. BMT)
        """
        
        return

    def add_company(self):
        """ Create new company integration by opening popup
        """
        self.newCompPopup = popups.NewCompanyPopup()
        self.newCompPopup.show()
        self.newCompPopup.saveBtn.clicked.connect(self._add_company)

    def _add_company(self):
        """ Handles creating a new company 
            - creates popup for info
            TODO: creates company from default
            - Repopulates tree
        """
        newCompanyName = self.newCompPopup.compNameBox.text()
        self.companyBox.clear()
        self.get_scripts()

        scriptName = f'{newCompanyName}/'
        self.load_tree(newCompanyName)
        self.populate_companies()
        self.loadCompanyTree(newCompanyName)

    def delete_company(self):
        """ Deletes a company's integration (all keys in 'folder')

        TODO:
            Check to make sure selected item is a company

        Commenting out for now until safety popup created-

        warn = popups.DeletionWarning(self.comp)
        for key in self.bucket.list(prefix=self.comp+'/'):
            key.delete()
        self.companyBox.clear()
        self.populate_companies()
        """
        return


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dark(app)
    ex = App()
    ex.show()

    sys.exit(app.exec_())

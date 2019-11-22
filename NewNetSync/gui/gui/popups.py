#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import time
import boto

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

import qtawesome as qta
from qtmodern.styles import dark

if __name__ == '__main__':
    import config
else:
    from gui import config


class NewCompanyPopup(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.otherBox = None
        self.bmt = False
        self.tmb = False
        self.other = None

        flags = Qt.WindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(flags)
        self.win_layout = QVBoxLayout()

        self.comp_layout = QVBoxLayout()
        self.comp_label = QLabel('Company Name')
        self.comp_name_box = QLineEdit()
        self.comp_layout.addWidget(self.comp_label)
        self.comp_layout.addWidget(self.comp_name_box)
        self.win_layout.addLayout(self.comp_layout)

        self.opt_layout = QVBoxLayout()
        self.opt_box = QGroupBox('Integration Type')

        self.opt_bmt = QCheckBox('BMT')
        self.opt_bmt.setChecked(False)
        self.opt_bmt.stateChanged.connect(lambda: self.box_state(self.opt_bmt))
        self.opt_layout.addWidget(self.opt_bmt)

        self.opt_tmb = QCheckBox('Timberline')
        self.opt_tmb.setChecked(False)
        self.opt_tmb.stateChanged.connect(lambda: self.box_state(self.opt_tmb))
        self.opt_layout.addWidget(self.opt_tmb)

        self.opt_other = QCheckBox('Other')
        self.opt_other.setChecked(False)
        self.opt_other.stateChanged.connect(
            lambda: self.box_state(self.opt_other))
        self.opt_layout.addWidget(self.opt_other)

        self.opt_box.setLayout(self.opt_layout)
        self.win_layout.addWidget(self.opt_box)

        self.btn_layout = QHBoxLayout()

        self.add_btn = QPushButton('Add Company')
        self.add_btn.clicked.connect(self.add_comp)
        self.btn_layout.addWidget(self.add_btn)

        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)
        self.btn_layout.addWidget(self.cancel_btn)
        self.win_layout.addLayout(self.btn_layout)

        self.setLayout(self.win_layout)

    def box_state(self, opt):
        if opt.text() == 'BMT':
            if opt.isChecked() == True:
                self.bmt = True
            else:
                self.bmt = False

        if opt.text() == 'Timberline':
            if opt.isChecked() == True:
                self.tmb = True
            else:
                self.tmb = False

        if opt.text() == 'Other':
            if opt.isChecked() == True:
                self.other_box = QLineEdit()
                self.opt_layout.addWidget(self.other_box)
            else:
                self.opt_layout.removeWidget(self.other_box)
                self.other_box.deleteLater()
                self.other_box = None

    def get_file(self, keys, dir_name):
        """REWRITE FOR JSON
        """
        found = False
        for k in keys:
            if dirName in k.name:
                scriptName = k.name.replace('_DEFAULT',
                                            self.compNameBox.text())
                self.bucket.copy_key(k.name, self.bucket.name, scriptName)
                found = True

        if not found:
            newScript = f'{self.compNameBox.text()}/{dirName}/newScript.sql'
            newKey = boto.s3.key.Key(self.bucket, newScript)
            newKey.set_contents_from_string('SELECT...')

    def add_comp(self):
        spin_icon = qta.icon('fa5s.spinner',
                             color='grey',
                             animation=qta.Spin(self.add_btn))
        self.add_btn.setText('')
        self.add_btn.setIcon(spin_icon)
        QApplication.processEvents()

        self.conn = boto.s3.connect_to_region(
            'us-west-2',
            aws_access_key_id=config.AWS_KEY,
            aws_secret_access_key=config.AWS_SECRET)
        self.bucket = self.conn.get_bucket('integrationconfigs')

        keys = [k for k in self.bucket.list(prefix='_DEFAULT/')]

        if self.bmt:
            self.get_files(keys, 'BMT')
        if self.tmb:
            self.get_files(keys, 'Timberline')
        if self.otherBox:
            if len(self.otherBox.text()) < 2:
                nameError = errorBox('Enter valid company name')
                nameError.show()
            else:
                self.get_files(keys, self.otherBox.text())

        self.add_btn.setIcon(QIcon())
        self.add_btn.setText('Save Script')
        QApplication.processEvents()
        time.sleep(.3)
        self.close()


class NewIntegrationPopup(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        flags = Qt.WindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(flags)
        self.win_layout = QVBoxLayout()

        self.int_layout = QVBoxLayout()
        self.int_label = QLabel('Integration Name')
        self.int_name_box = QLineEdit()
        self.comp_layout.addWidget(self.int_label)
        self.comp_layout.addWidget(self.int_name_box)
        self.win_layout.addLayout(self.int_layout)

        self.btn_layout = QHBoxLayout()

        self.add_btn = QPushButton('Add Integration')
        self.add_btn.clicked.connect(self.add_integration)
        self.btn_layout.addWidget(self.add_btn)

        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.close)
        self.btn_layout.addWidget(self.cancel_btn)
        self.win_layout.addLayout(self.btn_layout)

        self.setLayout(self.win_layout)

    def get_files(self, keys, dirName):
        found = False
        for k in keys:
            if dirName in k.name:
                scriptName = k.name.replace('_DEFAULT',
                                            self.compNameBox.text())
                self.bucket.copy_key(k.name, self.bucket.name, scriptName)
                found = True

        if not found:
            newScript = f'{self.compNameBox.text()}/{dirName}/newScript.sql'
            newKey = boto.s3.key.Key(self.bucket, newScript)
            newKey.set_contents_from_string('SELECT...')

    def add_integration(self):
        spin_icon = qta.icon('fa5s.spinner',
                             color='grey',
                             animation=qta.Spin(self.add_btn))
        self.add_btn.setText('')
        self.add_btn.setIcon(spin_icon)
        QApplication.processEvents()

        AWS_KEY = 'AKIAIVFU5YZHIVROUFMA'
        AWS_SECRET = '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'
        self.conn = boto.s3.connect_to_region('us-west-2',
                                              aws_access_key_id=AWS_KEY,
                                              aws_secret_access_key=AWS_SECRET)
        self.bucket = self.conn.get_bucket('integrationconfigs')

        keys = [k for k in self.bucket.list(prefix='_DEFAULT/')]

        if self.bmt:
            self.get_files(keys, 'BMT')
        if self.tmb:
            self.get_files(keys, 'Timberline')
        if self.otherBox:
            if len(self.otherBox.text()) < 2:
                nameError = errorBox('Enter valid company name')
                nameError.show()
            else:
                self.get_files(keys, self.otherBox.text())

        self.add_btn.setIcon(QIcon())
        self.add_btn.setText('Save Script')
        QApplication.processEvents()
        time.sleep(.3)
        self.close()


class ErrorPopup(QWidget):
    def __init__(self, error_name):
        QWidget.__init__(self)

        self.error_label = QLabel(error_name)
        self.error_layout = QHBoxLayout()
        self.error_layout.addWidget(self.error_label)
        self.setLayout(error_layout)

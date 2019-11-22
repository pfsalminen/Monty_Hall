#!/usr/bin/env python3
# -*- coding:utf-8 -*-
""" GUI to set up a new customer in RM/PLM/IM

TODO:
    update_logo_paths:
        change provisioner to copy file to bfsvr
        the write to db
    update_site:
        find some way to feed in data?
"""
from typing import List, Dict
import sys
import time
from collections import OrderedDict
import PySide2.QtCore as qtCore
import PySide2.QtGui as qtGui
import PySide2.QtWidgets as qtWidget
import qtawesome as qta
from qtmodern.styles import dark
import provision

class Window(qtWidget.QMainWindow):
    """ Gui class for DB provisioner"""

    def __init__(self) -> None:
        qtWidget.QMainWindow.__init__(self)

        self.provision = provision.Provision()

        flags = qtCore.Qt.WindowFlags(qtCore.Qt.WindowShadeButtonHint)
        self.setWindowFlags(flags)
        self.setWindowTitle('Database Builder')
        shape = (20, 200, 500, 800)
        self.setGeometry(qtCore.QRect(*(shape)))
        self.init_ui()

    def init_ui(self) -> None:
        """ Init for the UI. Is called by init"""

        self.layout = qtWidget.QVBoxLayout()

        #############################################
        # Row One
        row_one_layout = qtWidget.QHBoxLayout()
        row_one_layout.setSpacing(10)
        row_one_layout.setMargin(0)
        row_one_layout.setContentsMargins(-10, -10, -10, -10)

        self.radio_group = qtWidget.QButtonGroup()
        for i, choice in enumerate(['RM', 'PLM', 'IM']):
            btn = qtWidget.QRadioButton(choice)
            btn.connect(btn, qtCore.SIGNAL("clicked()"), self._radio_clicked)
            if i == 0:
                btn.setChecked(True)
            row_one_layout.addWidget(btn, 0, qtCore.Qt.AlignTop)
            self.radio_group.addButton(btn, i)

        self.selected_options = []
        self.radio_choice = 'RM'

        db_name = qtWidget.QLineEdit()
        db_name.setPlaceholderText('DB Name')
        db_name.setFixedWidth(300)
        db_name.textEdited.connect(self._set_db)
        row_one_layout.addWidget(db_name)

        self.layout.addLayout(row_one_layout)

        #############################################
        # Row Two
        row_two_layout = qtWidget.QHBoxLayout()

        master_name = qtWidget.QLineEdit()
        master_name.setPlaceholderText('Master Name')
        master_name.setText(self.provision.master_copy)
        master_name.setFixedWidth(300)
        master_name.textEdited.connect(self._set_master)
        row_two_layout.addWidget(master_name)

        svr_box = qtWidget.QComboBox()
        servers = [
            'DBSVR01',
            'DBSVR02',
            'DBSVR03',
            'DBSVR04',
        ]
        svr_box.addItem('------')
        for server in servers:
            svr_box.addItem(server)

        svr_box.activated[str].connect(self._set_server)
        row_two_layout.addWidget(svr_box)

        self.layout.addLayout(row_two_layout)
        self.layout.addWidget(QHLine(), 1, 0)

        #############################################
        # Options
        self.option_layout = qtWidget.QVBoxLayout()
        self._add_options()
        self.layout.addLayout(self.option_layout)

        #############################################
        # Go Button
        go_button = qtWidget.QPushButton("Go!")
        go_button.clicked.connect(self.go)
        self.layout.addWidget(go_button)

        #############################################
        # Progress bar
        self.progress = qtWidget.QProgressBar()
        completed = 0
        self.progress.setValue(completed)
        self.layout.addWidget(self.progress)

        #############################################
        # Status window
        self.info = qtWidget.QPlainTextEdit()
        # self.info.setEnabled(False)
        metrics = qtGui.QFontMetrics(FONT)
        self.info.setTabStopWidth(4 * metrics.width('  '))
        self.layout.addWidget(self.info)

        widget = qtWidget.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

    def _set_db(self, db: str) -> None:
        self.provision.db = db.upper()

    def _set_master(self, master: str) -> None:
        self.provision.master_copy = master

    def _make_options(self) -> None:
        """ Declares the option_dict variable"""
        self.option_dict = OrderedDict({
            'CreateDatabase': {
                'checkbox': self._checkbox('CreateDatabase'),
                'bakLoc': self._line_edit('Master Backup Location', 'bakLoc')
            },
            'BuildSite': {
                'checkbox': self._checkbox('BuildSite'),
            },
            'NetSyncServer': {
                'checkbox': self._checkbox('NetSyncServer'),
                'nssLoc': self._line_edit('Folder Location', 'nssLoc')
            },
            'BuilderFiles': {
                'checkbox': self._checkbox('BuilderFiles'),
                'bfLoc': self._line_edit('Folder Location', 'bfLoc'),
            },
            'NSS2014Integration': {
                'checkbox': self._checkbox('NSS2014Integration'),
            },
            'IntuitiveFolder': {
                'checkbox': self._checkbox('IntuitiveFolder'),
                'intLoc': self._line_edit('Folder Location', 'intLoc'),
            },
            'CompanyLogo': {
                'checkbox': self._checkbox('CompanyLogo'),
                'path': self._line_edit('Logo Path', 'logo'),
            },
            'PLMAdmin': {
                'checkbox': self._checkbox('PLMAdmin'),
            },
            'UpdateSite': {
                'checkbox': self._checkbox('UpdateSite'),
            },
            'EnableQBO': {
                'checkbox': self._checkbox('EnableQBO')
            },
            'XactSetup': {
                'checkbox':
                    self._checkbox('XactSetup'),
                'accnt_ID':
                    self._line_edit('Account ID', 'accnt_id'),
                'xactnet_addr':
                    self._line_edit('Xactnet Address', 'xactnet_addr'),
            },
        })

    def _file_button(self,
                     line_item: qtWidget.QLineEdit) -> qtWidget.QPushButton:
        """ Create a button to open a file explorer"""
        btn = qtWidget.QPushButton('Browse')
        btn.clicked.connect(lambda x: self._get_path(line_item))
        btn.hide()

        return btn

    @staticmethod
    def _get_path(line_item: qtWidget.QLineEdit) -> None:
        """ Sets the path selected in file explorer to the path line"""
        browser = qtWidget.QFileDialog()
        browser.setFileMode(qtWidget.QFileDialog.ExistingFile)

        if browser.exec_():
            path = browser.selectedFiles()[0]
            line_item.setText(path)

    @staticmethod
    def _clear_options(layout: qtWidget.QVBoxLayout) -> None:
        """ Empties all the items in a layout"""
        for i in reversed(range(layout.count())):
            inner_layout = layout.itemAt(i).layout()
            for j in reversed(range(inner_layout.count())):
                part = inner_layout.itemAt(j).widget()
                layout.removeWidget(part)
                part.setParent(None)

    def _line_edit(self, text: str, opt: str) -> qtWidget.QLineEdit:
        """ Returns a lineEdit widget, properly formatted"""
        widget = qtWidget.QLineEdit()
        widget.setPlaceholderText(text)
        widget.textChanged.connect(
            lambda x: self.text_change(widget.text(), opt))

        if opt == 'bakLoc' and self.provision.bakLoc:
            widget.setText(self.provision.bakLoc)
        elif opt == 'nssLoc' and self.provision.nssLoc:
            widget.setText(self.provision.nssLoc)
        elif opt == 'bfLoc' and self.provision.bfLoc:
            widget.setText(self.provision.bfLoc)
        elif opt == 'intLoc' and self.provision.intLoc:
            widget.setText(self.provision.intLoc)
        elif opt == 'xactnet_addr' and self.provision.xactnet_addr:
            widget.setText(self.provision.xactnet_addr)
        elif opt == 'accnt_id' and self.provision.accnt_id:
            widget.setText(self.provision.accnt_id)

        widget.hide()

        return widget

    def text_change(self, text: str, opt: str) -> None:
        """ Updates variable based on that text box was changed
        """
        if not text:
            return

        if opt == 'bakLoc':
            self.provision.bakLoc = text
        elif opt == 'nssLoc':
            self.provision.nssLoc = text
        elif opt == 'bfLoc':
            self.provision.bfLoc = text
        elif opt == 'intLoc':
            self.provision.intLoc = text
        elif opt == 'xactnet_addr':
            self.provision.xactnet_addr = text
        elif opt == 'accnt_id':
            self.provision.accnt_id = text

    def _checkbox(self, option: str) -> qtWidget.QCheckBox:
        """ Returns a checkbox widget, properly formatted"""
        btn = qtWidget.QCheckBox(option)
        btn.stateChanged.connect(self._option_selected)

        return btn

    @staticmethod
    def _format_options(options: Dict) -> qtWidget.QVBoxLayout:
        """ formats the options and suboptions nicely"""
        tmp = qtWidget.QVBoxLayout()
        tmp.addWidget(options['checkbox'])

        for k in options:
            if k == 'checkbox':
                continue
            tmp.addWidget(options[k])

        return tmp

    def browse_buttons(self, options: List) -> None:
        """ Creates the file browser button for options"""
        if not options:
            return

        for part in options:
            master = [x for x in self.option_dict[part] if x != 'checkbox'][0]
            self.option_dict[part]['button'] = self._file_button(
                self.option_dict[part][master])

    def delete_uneeded_options(self) -> None:
        """ Deleted the RM-centric options if type choice is not RM"""
        if self.radio_choice != 'RM':
            del self.option_dict['XactSetup']

    def _add_options(self) -> None:
        """ Contructs the option widgets/layout"""
        self._make_options()
        browser_options = [
            'CreateDatabase',
            'NetSyncServer',
            'BuilderFiles',
            'IntuitiveFolder',
            'CompanyLogo',
        ]
        self.browse_buttons(browser_options)
        self.delete_uneeded_options()

        for v in self.option_dict.values():
            self.option_layout.addLayout(self._format_options(v))

    def _radio_clicked(self) -> None:
        """ Called when rm/plm/im is chosen. Changes options based on it"""
        self.radio_choice = self.radio_group.checkedButton().text()
        self._clear_options(self.option_layout)
        self._add_options()

    def _option_selected(self) -> None:
        """ Called when option is (un)checked. Shows/hides items. Updated selection list"""
        self.selected_options = []
        for k, v in self.option_dict.items():
            if k == 'EnableQBO' and v['checkbox'].isChecked():
                self.provision.QBO = True
                continue

            if v['checkbox'].isChecked():
                self.selected_options.append(v['checkbox'].text())
            for name in v:
                if name == 'checkbox':
                    continue

                if v['checkbox'].isChecked():
                    self.option_dict[k][name].show()
                else:
                    self.option_dict[k][name].hide()
                    if isinstance(self.option_dict[k][name],
                                  qtWidget.QLineEdit):
                        self.option_dict[k][name].clear()

    def _set_server(self, text: str) -> None:
        """ Stores server choice in self.svrName"""
        self.provision.svr = text

    def _run_function(self, fn_name: str) -> bool:
        """ Runs provision function
        
        Change to bool, with tries and error handling
        """

        try:
            if fn_name == 'CreateDatabase':
                self.provision.create_database()
            elif fn_name == 'BuildSite':
                self.provision.build_site()
            elif fn_name == 'NetSyncServer':
                self.provision.create_netsync()
            elif fn_name == 'BuilderFiles':
                self.provision.document_maker()
            elif fn_name == 'NSS2014Integration':
                self.provision.insert_netsyncserver()
            elif fn_name == 'IntuitiveFolder':
                self.provision.intuitive_setup()
            elif fn_name == 'CompanyLogo':
                self.provision.update_logo_paths()
            elif fn_name == 'PLMAdmin':
                self.provision.update_plm_admin()
            elif fn_name == 'UpdateSite':
                return True
                # self.provision.update_site()
            elif fn_name == 'XactSetup':
                self.provision.make_ThirdPartAuth_xml()
                self.provision.setup_xact()
                self.provision.update_xn_address()
        except Exception as e:
            self._update_text(e)
            return False
        else:
            return True

    def _update_text(self, new_text: str) -> None:
        current_text = self.info.toPlainText()
        self.info.setPlainText(current_text + '\n' + new_text)
        self.info.moveCursor(qtGui.QTextCursor.End)

    def validate_runtime(self) -> bool:
        """ Ensures all needed options valid to run"""
        valid = True
        if not self.provision.db:
            self._update_text('Please enter a DB Name.')
            valid = False

        if not self.provision.svr or self.provision.svr == '------':
            self._update_text('Please select a server.')
            valid = False

        if not self.selected_options:
            self._update_text('Please select at least one option.')
            valid = False

        if 'CreateDatabase' in self.selected_options:
            if not self.option_dict['CreateDatabase']['bakLoc'].text().endswith(
                    '.bak'):
                self._update_text('Please choose a valid backup')
                valid = False

        return valid

    def go(self) -> None:
        """ Runs the program. Responds to Go button"""

        print('\n'.join(
            k
            for k, v in self.__dict__.items()
            if not callable(v)
        ))

        self.info.clear()

        if not self.validate_runtime():
            return

        self.provision.init()

        self._update_text(f'Starting {self.provision.db} on {self.comapny.svr}')
        completed = 0
        opt_percent = 100 / len(self.selected_options)
        while self.selected_options:
            runner = self.selected_options.pop(0)
            self._update_text(f'Running {runner}...')

            # Actually runs function
            success = self._run_function(runner)
            if not success:
                self.selected_options = [runner] + self.selected_options
                return

            self._update_text('\tCompleted')

            completed += opt_percent
            self.progress.setValue(completed)
            time.sleep(1)

        self._radio_clicked()

    def log_error(self, error_msg: str) -> None:
        """ Updates error textbox if there is one"""
        self._update_text(error_msg)
        # sys.exit()


class QHLine(qtWidget.QFrame):
    """ Create Hr line"""

    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(qtWidget.QFrame.HLine)
        self.setFrameShadow(qtWidget.QFrame.Sunken)


class QVLine(qtWidget.QFrame):
    """ Create Vertical line"""

    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(qtWidget.QFrame.VLine)
        self.setFrameShadow(qtWidget.QFrame.Sunken)


if __name__ == '__main__':
    FONT = qtGui.QFont("Arial", 12)
    FONT.setStyleHint(qtGui.QFont.Monospace)

    APP = qtWidget.QApplication(sys.argv)
    dark(APP)
    APP.setFont(FONT)
    ex = Window()
    ex.show()

    sys.exit(APP.exec_())

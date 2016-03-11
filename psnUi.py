#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
==============================================================
Changelog:

    1. 2015/01/27
    create this program

==============================================================
'''

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import mysql
from mysql import connector

import os

import threading

import time


#getRC = lambda cur: cur.rowcount if hasattr(cur,'rowcount')  else -1

gHost     = "";
gPassword = "";
#gHost     = "127.0.0.1";
#gPassword = "mysql111";
gPort     = 3306;

gUser     = "root";
gDB       = "sport_camera_sn";
gTable    = "psn_copy";
#gTable    = "psn";

gSelectSql = 'select id, psn from %s where is_used = 0 limit %s;';
gUpdateSql = 'update %s set is_used=1, use_date=now()  where is_used = 0 limit %s;';


def SqlConnect():
    print("In SqlConnect: host: %s, password: %s" % (gHost, gPassword));

    try:
        conn = mysql.connector.connect(user = gUser, password = gPassword, host = gHost, database = gDB);
        return conn;
    except Exception as e:
        sigs.sigSqlErr.emit("Mysql connect failed\nPlease set sql host and password\nin File -> Mysql");
        print(e);


class PsnMngrHandler(threading.Thread):
    def __init__(self, count, file):
        threading.Thread.__init__(self);
        self.psnCount = count;
        self.psnFile = file;
        self.row = [];

    def run(self):
        self.conn = SqlConnect();
        if (self.conn == None):
            return;
            
        self.cur = self.conn.cursor();
        
        self.cur.execute(gSelectSql % (gTable, self.psnCount));
        self.rows = self.cur.fetchall();

        try:
            self.psnFp = open(self.psnFile, "w");
        except Exception as e:
            print(e);

        i = 0;
        for row in self.rows:
            i += 1;
            print("in handler thread");
            print(row);
            self.row = row;

            self.psnFp.write("%s,%s\n" % (row[0], row[1]));
            sigs.sigPassSn.emit(row, i);

        self.psnFp.close();
        
        # set sn "is_used = 1"
        self.cur.execute(gUpdateSql % (gTable, self.psnCount));
        self.conn.commit();
        
        self.cur.close();
        self.conn.close();

    def stop():
        self.psnFp.close();
        self.cur.close();
        self.conn.close();
        
        self.thread_stop = True;


class PsnMngrUI(QMainWindow):
    def __init__(self):
        super(PsnMngrUI, self).__init__();
        
        self.psnCount = 0;

        self.createOptionsGroupBox();
        self.createPsnTable();
        self.createProgressbar();
        self.createButtonsLayout();
        
        self.mainLayout = QVBoxLayout();
        self.mainLayout.addWidget(self.optionsGroupBox);
        self.mainLayout.addWidget(self.psnTable);
        self.mainLayout.addWidget(self.psnProgressbar);
        self.mainLayout.addWidget(self.groupBox);
        
        self.mainWidget = QWidget();
        self.mainWidget.setLayout(self.mainLayout);
        self.setCentralWidget(self.mainWidget);
        
        self.createActions()
        self.createMenus()
        
        self.setWindowTitle("PsnMngr");
        self.resize(800, 600);


    def createActions(self):
        self.sqlAct = QAction("&Mysql", self, shortcut="Ctrl+D",
            statusTip="Input SQL host and password", triggered=self.getSqlParam)
            
        self.quitAct = QAction("&Quit", self, shortcut="Ctrl+Q",
            statusTip="Quit the application", triggered=self.close)


    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&Menu")
        self.fileMenu.addAction(self.sqlAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAct)

        
    def createComboBox(self, text=""):
        comboBox = QComboBox();
        comboBox.setEditable(True);
        comboBox.addItem(text);
        comboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred);
        return comboBox;

        
    def createButton(self, text, member):
        button = QPushButton(text);
        button.clicked.connect(member);
        return button;

        
    def createOptionsGroupBox(self):
        self.optionsGroupBox = QGroupBox("");
        
        self.countLabel = QLabel("Psn count");
        self.countComboBox = self.createComboBox("");
        
        self.outportFileLabel = QLabel("outport file");
        self.fileComboBox = self.createComboBox("Please choose a file for save SN...");
        self.browseButton = self.createButton("&Browse...", self.browse);
        
        self.optionsGroupBoxLayout = QGridLayout();
        self.optionsGroupBoxLayout.addWidget(self.countLabel, 0, 0);
        self.optionsGroupBoxLayout.addWidget(self.countComboBox, 0, 1);
        self.optionsGroupBoxLayout.addWidget(self.outportFileLabel, 1, 0);
        self.optionsGroupBoxLayout.addWidget(self.fileComboBox, 1, 1);
        self.optionsGroupBoxLayout.addWidget(self.browseButton, 1, 2);
        
        self.optionsGroupBox.setLayout(self.optionsGroupBoxLayout);

        
    def createPsnTable(self):
        self.psnTable = QTableWidget(0, 2);
        self.psnTable.setSelectionBehavior(QAbstractItemView.SelectRows);

        self.psnTable.setHorizontalHeaderLabels(("No.", "SN"));
        self.psnTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch);
        self.psnTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch);
        self.psnTable.verticalHeader().hide();
        #self.psnTable.setShowGrid(False);

        
    def createProgressbar(self):
        self.psnProgressbar = QProgressBar();
        self.psnProgressbar.setRange(0, 100);
        self.psnProgressbar.setValue(0);
        self.psnProgressbar.hide();
        
        
    def createButtonsLayout(self):
        self.psnOutportButton = self.createButton("Outport", self.outportHandler);
        self.psnCancelButton = self.createButton("Cancel", self.close);

        self.groupBox = QGroupBox("");
        self.groupBoxLayout = QHBoxLayout();
        self.groupBoxLayout.addStretch(1);
        self.groupBoxLayout.addWidget(self.psnOutportButton);
        self.groupBoxLayout.addWidget(self.psnCancelButton);
        
        self.groupBox.setLayout(self.groupBoxLayout);

        
    def browse(self):
        self.file = QFileDialog.getOpenFileName(self, "Open Psn Record", "", "TXT Files(*.txt)");
        if self.file:
            print(self.file)
            if self.fileComboBox.findText(self.file[0]) == -1:
                self.fileComboBox.addItem(self.file[0]);

            self.fileComboBox.setCurrentIndex(self.fileComboBox.findText(self.file[0]));


    def showPsnToTable(self, list):
        SnNo = QTableWidgetItem(str(list[0]))
        SnNo.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        SnNo.setFlags(SnNo.flags() ^ Qt.ItemIsEditable)
        
        SnSN = QTableWidgetItem(list[1])
        SnSN.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        SnSN.setFlags(SnSN.flags() ^ Qt.ItemIsEditable)

        row = self.psnTable.rowCount()
        self.psnTable.insertRow(row)
        self.psnTable.setItem(row, 0, SnNo)
        self.psnTable.setItem(row, 1, SnSN)

        
    def updateProgressBar(self, val):
        self.psnProgressbar.setValue(val);
        print("updateProgressBar val: %d\n" % val)


    def showSNData(self, row, count):
        print("In main thread");
        print(row);
        self.showPsnToTable(row);
        self.updateProgressBar((count/self.psnCount) * 100);
        print("showSNData count: %d, self.psnCount: %d.\n" % (count, self.psnCount))


    def popupMsg(self, prompt):
        msgBox = QMessageBox();
        
        msgBox.setWindowTitle("INFO");
        msgBox.setIcon(msgBox.Information);
        msgBox.setStandardButtons(msgBox.Ok | msgBox.Cancel);
        msgBox.setText(prompt);
        
        msgBox.exec_();


    def getSqlParam(self):
        sqlParamDialog = QDialog();
        sqlParamDialog.resize(240, 160);
        
        sqlParamDialog.sqlHost = QLineEdit();
        sqlParamDialog.sqlPassword = QLineEdit();
        
        grid = QGridLayout();
        grid.addWidget(QLabel("Please input mysql Host and password:"), 0, 0, 1, 2);
        
        grid.addWidget(QLabel("sql host"), 1, 0, 1, 1);
        grid.addWidget(sqlParamDialog.sqlHost, 1, 1, 1, 1);

        grid.addWidget(QLabel("password"), 2, 0, 1, 1);
        grid.addWidget(sqlParamDialog.sqlPassword, 2, 1, 1, 1);

        buttonBox = QDialogButtonBox();
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel);

        buttonBox.accepted.connect(sqlParamDialog.accept);
        buttonBox.rejected.connect(sqlParamDialog.reject);

        layout = QVBoxLayout();
        layout.addLayout(grid);

        layout.addWidget(buttonBox);
        sqlParamDialog.setLayout(layout);

        r = sqlParamDialog.exec_();
        
        # only click Ok button, can go in here
        if (r == QDialog.Accepted):
            global gHost;
            global gPassword;
            gHost = sqlParamDialog.sqlHost.text();
            gPassword = sqlParamDialog.sqlPassword.text();

            print("getsqlparam: gHost: %s , gPassword: %s" % (gHost, gPassword));


    def outportHandler(self):
        strPsnCount = self.countComboBox.currentText();
        strFilename = self.fileComboBox.currentText();

        if (strPsnCount == "" or strFilename == ""):
            self.popupMsg("\"Psn Count\" or \"Outport File\"\n\nCan not be empty!");
            return;

        if (not os.path.exists(strFilename)):
            self.popupMsg("\"Outport File\": %s is not exists!" % strFilename);
            return;

        print("Psn Count: " + strPsnCount);
        print("Outport File: " + strFilename);

        self.psnCount = int(strPsnCount);
        if (self.psnCount == 0):
            self.popupMsg("\"Psn Count\" Can not be zero!");
            return;

        if (gHost == '' or gPassword == ''):
            print("in outportHandler: H: %s; P: %s" % (gHost, gPassword));
            self.popupMsg("Please set database host and password\nIn \"File\" -> \"Mysql\"");
            return;

        # TODO: here create a thread
        self.psnProgressbar.show();
        self.psnThread = PsnMngrHandler(self.psnCount, strFilename); 
        self.psnThread.setDaemon(True);
        self.psnThread.start();


class Sigs(QObject):
    sigPassSn = pyqtSignal(tuple, int);
    sigSqlErr = pyqtSignal(str);


if __name__ == '__main__':
    import sys;

    sigs = Sigs();
    
    app = QApplication(sys.argv);
    psnMUI = PsnMngrUI();
    
    sigs.sigPassSn.connect(psnMUI.showSNData);
    sigs.sigSqlErr.connect(psnMUI.popupMsg);
    
    psnMUI.show();
    
    sys.exit(app.exec_());

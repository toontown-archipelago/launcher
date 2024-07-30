# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGraphicsView,
    QLabel, QLineEdit, QMainWindow, QMenuBar,
    QProgressBar, QPushButton, QSizePolicy, QStatusBar,
    QTextBrowser, QWidget)

class Ui_launcher(object):
    def setupUi(self, launcher):
        if not launcher.objectName():
            launcher.setObjectName(u"launcher")
        launcher.resize(800, 600)
        launcher.setStyleSheet(u"background: transparent;\n"
"")
        self.centralwidget = QWidget(launcher)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setAutoFillBackground(False)
        self.centralwidget.setStyleSheet(u"")
        self.releaseNotesText = QTextBrowser(self.centralwidget)
        self.releaseNotesText.setObjectName(u"releaseNotesText")
        self.releaseNotesText.setEnabled(True)
        self.releaseNotesText.setGeometry(QRect(70, 140, 531, 211))
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setBold(False)
        self.releaseNotesText.setFont(font)
        self.releaseNotesText.setAutoFillBackground(False)
        self.releaseNotesText.setStyleSheet(u"background:transparent; border: 1px solid black;\n"
"color: rgb(0, 0, 0);")
        self.releaseNotesText.setAcceptRichText(True)
        self.releaseNotesText.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.graphicsView = QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName(u"graphicsView")
        self.graphicsView.setGeometry(QRect(-11, 2, 800, 600))
        self.graphicsView.setStyleSheet(u"border-image: url(:/resources/750x500_bg1.png);\n"
" background-repeat: no-repeat;")
        self.installprogressBar = QProgressBar(self.centralwidget)
        self.installprogressBar.setObjectName(u"installprogressBar")
        self.installprogressBar.setEnabled(False)
        self.installprogressBar.setGeometry(QRect(57, 362, 591, 51))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        self.installprogressBar.setFont(font1)
        self.installprogressBar.setValue(0)
        self.installprogressBar.setTextVisible(True)
        self.releasesComboBox = QComboBox(self.centralwidget)
        self.releasesComboBox.setObjectName(u"releasesComboBox")
        self.releasesComboBox.setGeometry(QRect(20, 440, 103, 32))
        self.releasesComboBox.setFont(font1)
        self.releasesComboBox.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"border: 2px solid black;\n"
"border-radius: 5px;")
        self.pushButton_hostServer = QPushButton(self.centralwidget)
        self.pushButton_hostServer.setObjectName(u"pushButton_hostServer")
        self.pushButton_hostServer.setGeometry(QRect(20, 470, 100, 32))
        self.pushButton_hostServer.setFont(font1)
        self.pushButton_hostServer.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"border: 2px solid black;\n"
"border-radius: 5px;")
        self.pushButton_runSettings = QPushButton(self.centralwidget)
        self.pushButton_runSettings.setObjectName(u"pushButton_runSettings")
        self.pushButton_runSettings.setGeometry(QRect(130, 450, 101, 51))
        font2 = QFont()
        font2.setFamilies([u"Arial"])
        font2.setPointSize(10)
        self.pushButton_runSettings.setFont(font2)
        self.pushButton_runSettings.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"border: 2px solid black;\n"
"border-radius: 5px;")
        self.pushButton_generateSeed = QPushButton(self.centralwidget)
        self.pushButton_generateSeed.setObjectName(u"pushButton_generateSeed")
        self.pushButton_generateSeed.setGeometry(QRect(240, 450, 121, 51))
        self.pushButton_generateSeed.setFont(font1)
        self.pushButton_generateSeed.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"border: 2px solid black;\n"
"border-radius: 5px;")
        self.lineEdit_ipAddress = QLineEdit(self.centralwidget)
        self.lineEdit_ipAddress.setObjectName(u"lineEdit_ipAddress")
        self.lineEdit_ipAddress.setGeometry(QRect(320, 410, 113, 21))
        self.lineEdit_ipAddress.setFont(font2)
        self.lineEdit_ipAddress.setStyleSheet(u"border: 2px solid black;\n"
"border-radius: 5px;\n"
"color: rgb(0, 0, 0);")
        self.lineEdit_username = QLineEdit(self.centralwidget)
        self.lineEdit_username.setObjectName(u"lineEdit_username")
        self.lineEdit_username.setGeometry(QRect(450, 410, 113, 21))
        self.lineEdit_username.setFont(font2)
        self.lineEdit_username.setStyleSheet(u"border: 2px solid black;\n"
"border-radius: 5px;\n"
"\n"
"color: rgb(0, 0, 0);")
        self.pushButton_Settings = QPushButton(self.centralwidget)
        self.pushButton_Settings.setObjectName(u"pushButton_Settings")
        self.pushButton_Settings.setGeometry(QRect(20, 410, 21, 32))
        self.pushButton_Settings.setFont(font1)
        self.pushButton_Settings.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"border: 2px solid black;\n"
"border-radius: 5px;\n"
"qproperty-icon: url(:/resources/cog-svgrepo-com.svg)")
        self.pushButton_connect = QPushButton(self.centralwidget)
        self.pushButton_connect.setObjectName(u"pushButton_connect")
        self.pushButton_connect.setGeometry(QRect(370, 450, 121, 51))
        font3 = QFont()
        font3.setFamilies([u"Arial"])
        font3.setPointSize(11)
        self.pushButton_connect.setFont(font3)
        self.pushButton_connect.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"border: 2px solid black;\n"
"border-radius: 5px;")
        self.pushButton_startAll = QPushButton(self.centralwidget)
        self.pushButton_startAll.setObjectName(u"pushButton_startAll")
        self.pushButton_startAll.setGeometry(QRect(520, 450, 121, 51))
        self.pushButton_startAll.setFont(font3)
        self.pushButton_startAll.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"border: 2px solid black;\n"
"border-radius: 5px;")
        self.rememberMecheckBox = QCheckBox(self.centralwidget)
        self.rememberMecheckBox.setObjectName(u"rememberMecheckBox")
        self.rememberMecheckBox.setGeometry(QRect(320, 430, 121, 20))
        self.rememberMecheckBox.setFont(font1)
        self.rememberMecheckBox.setStyleSheet(u"color: rgb(0, 0, 0);\n"
"")
        self.minusButton = QPushButton(self.centralwidget)
        self.minusButton.setObjectName(u"minusButton")
        self.minusButton.setGeometry(QRect(670, 0, 31, 32))
        self.minusButton.setStyleSheet(u"image: url(:/resources/minus.png);\n"
"background: transparent;")
        self.closeButton = QPushButton(self.centralwidget)
        self.closeButton.setObjectName(u"closeButton")
        self.closeButton.setGeometry(QRect(730, 0, 31, 32))
        self.closeButton.setStyleSheet(u"image: url(:/resources/close.png);\n"
"background: transparent;")
        self.downloadLabel = QLabel(self.centralwidget)
        self.downloadLabel.setObjectName(u"downloadLabel")
        self.downloadLabel.setEnabled(True)
        self.downloadLabel.setGeometry(QRect(70, 350, 531, 16))
        self.downloadLabel.setFont(font3)
        self.downloadLabel.setStyleSheet(u"color: rgb(0, 0, 0);")
        launcher.setCentralWidget(self.centralwidget)
        self.graphicsView.raise_()
        self.releaseNotesText.raise_()
        self.installprogressBar.raise_()
        self.releasesComboBox.raise_()
        self.pushButton_hostServer.raise_()
        self.pushButton_runSettings.raise_()
        self.pushButton_generateSeed.raise_()
        self.lineEdit_ipAddress.raise_()
        self.lineEdit_username.raise_()
        self.pushButton_Settings.raise_()
        self.pushButton_connect.raise_()
        self.pushButton_startAll.raise_()
        self.rememberMecheckBox.raise_()
        self.minusButton.raise_()
        self.closeButton.raise_()
        self.downloadLabel.raise_()
        self.menubar = QMenuBar(launcher)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 37))
        launcher.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(launcher)
        self.statusbar.setObjectName(u"statusbar")
        launcher.setStatusBar(self.statusbar)

        self.retranslateUi(launcher)

        QMetaObject.connectSlotsByName(launcher)
    # setupUi

    def retranslateUi(self, launcher):
        launcher.setWindowTitle(QCoreApplication.translate("launcher", u"launcher", None))
        self.releaseNotesText.setHtml(QCoreApplication.translate("launcher", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Arial'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'.TimesNewRoman'; font-size:18pt;\">Release Notes</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:'.TimesNewRoman'; font-size:12pt;\">Coming Soon</span></p></body></html>", None))
        self.releasesComboBox.setPlaceholderText(QCoreApplication.translate("launcher", u"V0.0", None))
        self.pushButton_hostServer.setText(QCoreApplication.translate("launcher", u"Host a Server", None))
        self.pushButton_runSettings.setText(QCoreApplication.translate("launcher", u"Open Run Settings", None))
        self.pushButton_generateSeed.setText(QCoreApplication.translate("launcher", u"Generate a Seed", None))
        self.lineEdit_ipAddress.setPlaceholderText(QCoreApplication.translate("launcher", u"Server IP: 127.0.0.1", None))
        self.lineEdit_username.setPlaceholderText(QCoreApplication.translate("launcher", u"Username: player1", None))
        self.pushButton_Settings.setText("")
        self.pushButton_connect.setText(QCoreApplication.translate("launcher", u"Connect with User/IP", None))
        self.pushButton_startAll.setText(QCoreApplication.translate("launcher", u"Start All (Solo/Offline)", None))
        self.rememberMecheckBox.setText(QCoreApplication.translate("launcher", u"Remember Me", None))
        self.minusButton.setText("")
        self.closeButton.setText("")
        self.downloadLabel.setText(QCoreApplication.translate("launcher", u"Downloading: ", None))
    # retranslateUi


# This Python file uses the following encoding: utf-8
from sys import platform, argv, exit as sys_exit
from pathlib import Path
from os import environ, chdir
import zipfile
import io
# import time
# import multiprocessing
import stat
import subprocess
import threading
import json
import requests
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
# from PySide6.QtCore import QPoint
from PySide6.QtCore import QThread, Signal
from PySide6.QtCore import QStandardPaths
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_launcher
import resources_rc

GAME_DIRECTORY = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation), 'Toontown Archipelago')
if platform == 'darwin':
    ZIP_NAME = 'TTAP-macos.zip'
else:
    ZIP_NAME = 'TTAP.zip'


class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal()
    def __init__(self, asset_game, asset_yaml, asset_apworld, gameDirectory):
        super().__init__()
        self.asset_game = asset_game
        self.asset_yaml = asset_yaml
        self.asset_apworld = asset_apworld
        self.gameDirectory = gameDirectory

    def run(self):
        self.download_files(self.asset_game, self.asset_yaml, self.asset_apworld)
        self.finished.emit()

    def download_files(self, asset_game, asset_yaml, asset_apworld):
        # Download the first file
        self.downloadFile(asset_game)
        self.progress.emit(33)

        # Download the second file
        self.downloadFile(asset_yaml)
        self.progress.emit(66)

        # Download the third file
        self.downloadFile(asset_apworld)
        self.progress.emit(100)

    def downloadFile(self, asset):
        # download the file
        response = requests.get(asset.get('browser_download_url'), stream=True, timeout=10)
        response.raise_for_status()
        # if file is a zip extract it
        if asset['name'].endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                archive.extractall(self.gameDirectory)
        else:
            # save the file
            with Path(self.gameDirectory, asset['name']).open('wb') as file:
                file.write(response.content)

class launcher(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_launcher()
        self.ui.setupUi(self)
        self.ui.installprogressBar.setVisible(False)
        # make the main window transparent
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.prefs = self.loadPrefs()
        self.ui.minusButton.clicked.connect(self.showMinimized)
        self.ui.closeButton.clicked.connect(self.close)
        self.ui.downloadLabel.setVisible(False)
        self.setMouseTracking(True)
        # fill the releases combo box with the list of  releases
        self.releases = self.getReleases()
        self.updateComboBox()
        self.writeReleaseNotes()
        self.releaseSelected = self.ui.releasesComboBox.currentText()
        self.ui.releasesComboBox.currentIndexChanged.connect(self.releaseChanged)
        self.setGameDirectory()
        self.ui.pushButton_hostServer.clicked.connect(self.hostServer)
        self.ui.pushButton_connect.clicked.connect(self.connectToServer)
        self.ui.prereleasesCheckBox.stateChanged.connect(self.updateComboBox)
        self.download_thread = None
        self.offset = None


    # events to allow dragging of window

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)

    def loadPrefs(self):
        try:
            with Path(GAME_DIRECTORY, "prefs.json").open('r', encoding='utf-8') as file:
                prefs = json.load(file)
        except OSError:
            print("preferences could not be loaded.\nIf this is the first time running, this can be ignored.")
            prefs = {}
        #adds default values if missing, otherwise does nothing.
        prefs['remember'] = prefs.get('remember', False)
        prefs["username"] = prefs.get('username', 'player1')
        prefs["serverIP"] = prefs.get('serverIP', '127.0.0.1')
        prefs["prereleases"] = prefs.get('prereleases', False) 
        self.ui.rememberMeCheckBox.setChecked(prefs.get('remember'))
        self.ui.prereleasesCheckBox.setChecked(prefs.get('prereleases'))
        if prefs.get('remember'):
            self.ui.lineEdit_username.setText(prefs.get('username'))
            self.ui.lineEdit_ipAddress.setText(prefs.get('serverIP'))
        return prefs

    def savePrefs(self):
        self.prefs['remember'] = self.ui.rememberMeCheckBox.isChecked()
        self.prefs['prereleases'] = self.ui.prereleasesCheckBox.isChecked()
        if self.prefs.get('remember'):
            self.prefs["username"] = self.ui.lineEdit_username.text()
            self.prefs["serverIP"] = self.ui.lineEdit_ipAddress.text()
        with Path(GAME_DIRECTORY, "prefs.json").open('w', encoding='utf-8') as file:
            json.dump(self.prefs, file)

    def updateComboBox(self):
        self.ui.releasesComboBox.clear()
        if self.ui.prereleasesCheckBox.isChecked():
            self.ui.releasesComboBox.addItems(self.releases.keys())
        else:
            releases = {k:v for k,v in self.releases.items() if not v["prerelease"]}
            self.ui.releasesComboBox.addItems(releases)
        # choose the latest release by default
        self.ui.releasesComboBox.setCurrentIndex(0)
        self.releaseSelected = self.ui.releasesComboBox.currentText()

    def hostServer(self):
        # check if we downloaded the release we selected
        self.downloadRelease()
        # TODO: multithreaded running of all server components including astron, uberdog and ai

    def runClient(self):
        self.savePrefs()
        chdir(self.gameDirectory)
        if platform == 'darwin':
            modes = Path('launch').stat().st_mode
            if not modes & stat.S_IXUSR:
                Path('launch').chmod(modes | stat.S_IXUSR)
            subprocess.Popen(['./launch'])
        elif platform == 'win32':
            subprocess.Popen('launch', creationflags=134217728)
        elif platform.startswith('linux'):
            # use wine
            subprocess.Popen(['wine', 'launch'])


    def connectToServer(self):
        # read from lineEdit_ipAddress, and lineEdit_username,
        # default ip : 127.0.0.1
        # default username : player1
        ip = self.ui.lineEdit_ipAddress.text()
        username = self.ui.lineEdit_username.text()
        if not ip:
            ip = "127.0.0.1"
        if not username:
            username = "player1"
        # check if we downloaded the release we selected
        self.downloadRelease()
        if self.download_thread:
            self.download_thread.finished.connect(lambda: self.startClientThread(username, ip))
        else:
            self.startClientThread(username, ip)



    def startClientThread(self, username, ip):
        environ['SERVICE_TO_RUN'] = 'CLIENT'
        environ['TTOFF_LOGIN_TOKEN'] = username
        environ['TTOFF_GAME_SERVER'] = ip
        clientThread = threading.Thread(target=self.runClient)
        clientThread.start()

    # make the list of releases based on the https://github.com/toontown-archipelago/toontown-archipelago/releases API
    def getReleases(self):
        url = "https://api.github.com/repos/toontown-archipelago/toontown-archipelago/releases"
        query = {"per_page": 100} #TODO: setup pagination, before we hit 100 releases.
        response = requests.get(url, query, timeout=10)
        data = response.json()
        releases = {}
        for release in data:
            releases[release["tag_name"]] = release
            assets = release.get('assets', [])
            if next((item for item in assets if item['name'] == ZIP_NAME)) is not None:
                releases.update({release["tag_name"]: release})
        return releases

    def releaseChanged(self):
        self.releaseSelected = self.ui.releasesComboBox.currentText()
        # download the release if it doesn't exist already
        self.downloadRelease()

    def writeReleaseNotes(self):
        for _,v in self.releases.items():
            self.ui.releaseNotesText.append(v["name"] + '\n')
            self.ui.releaseNotesText.append(v["body"])

    def setGameDirectory(self):
        self.gameDirectory = Path(GAME_DIRECTORY / self.releaseSelected)

    def downloadRelease(self):
        self.setGameDirectory()
        if Path(self.gameDirectory,'game').exists() or Path(self.gameDirectory,'release').exists() or self.releaseSelected == "":
            return
        asset = next((item for item in self.releases.get(self.releaseSelected, {}).get('assets', []) if item['name'] == ZIP_NAME), None)

        asset_yaml = next((item for item in self.releases.get(self.releaseSelected, {}).get("assets", []) if item['name'].endswith(".yaml")), None)
        asset_apworld = next((item for item in self.releases.get(self.releaseSelected, {}).get("assets", []) if item['name'].endswith('.apworld')), None)
        if None in [asset, asset_yaml, asset_apworld]:
            print(f"Error trying to download {self.releaseSelected}: an asset is missing from the release.")
            return
        self.updateProgress(0)
        self.download_thread = DownloadThread(asset, asset_yaml, asset_apworld, self.gameDirectory)
        self.download_thread.progress.connect(self.updateProgress)
        self.download_thread.finished.connect(self.onDownloadFinished)
        self.download_thread.start()



    def updateProgress(self, value):
        self.ui.downloadLabel.setVisible(True)
        self.ui.installprogressBar.setVisible(True)
        self.ui.installprogressBar.setValue(value)

    def onDownloadFinished(self):
        self.ui.downloadLabel.setVisible(False)
        self.ui.installprogressBar.setVisible(False)
        self.setGameDirectory()




if __name__ == "__main__":
    app = QApplication(argv)
    widget = launcher()
    widget.show()
    sys_exit(app.exec())

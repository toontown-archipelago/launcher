# This Python file uses the following encoding: utf-8
from sys import platform, argv, exit as sys_exit
from pathlib import Path
from os import environ, chdir
from itertools import count
import zipfile
import io
# import time
# import multiprocessing
import stat
import subprocess
# import threading
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
    progress = Signal(int,str)
    finished = Signal()
    def __init__(self, assets, gameDirectory):
        super().__init__()
        self.assets = assets
        self.gameDirectory = gameDirectory

    def run(self):
        self.download_files(self.assets)
        self.finished.emit()

    def download_files(self, assets):
        self.gameDirectory.mkdir(exist_ok=True) #ensure directory exists, game isn't necessarily the first.
        for k,v in enumerate(assets):
            self.progress.emit(int(k/len(assets)*100), v.get('name'))
            self.downloadFile(v)

    def downloadFile(self, asset):
        # download the file
        response = requests.get(asset.get('browser_download_url'), stream=True, timeout=10)
        response.raise_for_status()
        # if file is a zip extract it
        if asset['name'].endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                archive.extractall(self.gameDirectory)
        else:
            # save the file
            with Path(self.gameDirectory, asset.get('name')).open('wb') as file:
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
            with Path(GAME_DIRECTORY, 'prefs.json').open('r', encoding='utf-8') as file:
                prefs = json.load(file)
        except OSError:
            print("preferences could not be loaded.\nIf this is the first time running, this can be ignored.")
            prefs = {}
        #adds default values if missing, otherwise does nothing.
        prefs['remember'] = prefs.get('remember', False)
        prefs['username'] = prefs.get('username', 'player1')
        prefs['serverIP'] = prefs.get('serverIP', '127.0.0.1')
        prefs['prereleases'] = prefs.get('prereleases', False)
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
            self.prefs['username'] = self.ui.lineEdit_username.text()
            self.prefs['serverIP'] = self.ui.lineEdit_ipAddress.text()
        with Path(GAME_DIRECTORY, 'prefs.json').open('w', encoding='utf-8') as file:
            json.dump(self.prefs, file)

    def updateComboBox(self):
        self.ui.releasesComboBox.clear()
        if self.ui.prereleasesCheckBox.isChecked():
            self.ui.releasesComboBox.addItems(self.releases.keys())
        else:
            releases = {k:v for k,v in self.releases.items() if not v['prerelease']}
            self.ui.releasesComboBox.addItems(releases)
        # choose the latest release by default
        self.ui.releasesComboBox.setCurrentIndex(0)
        self.releaseSelected = self.ui.releasesComboBox.currentText()

    def hostServer(self):
        # check if we downloaded the release we selected
        self.downloadRelease()
        self.startServerThreads()

    def runClient(self):
        self.savePrefs()
        chdir(self.gameDirectory/'game')
        if platform == 'darwin':
            modes = Path('launch').stat().st_mode
            if not modes & stat.S_IXUSR:
                Path('launch').chmod(modes | stat.S_IXUSR)
            subprocess.Popen(['./launch'])
        elif platform == 'win32':
            subprocess.Popen('launch', creationflags=subprocess.CREATE_NO_WINDOW)
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
        self.runClient()

    def startServerThreads(self):
        # astron
        chdir(self.gameDirectory / 'game' / 'astron')
        # print current dir of game directory
        print(f"Current directory: {Path.cwd()}")
        # first if we are on a unix system chmod the astrond files
        if platform != 'win32':
            # for each file in astron folder
            for file in Path('.').glob('*'):
                modes = Path(file).stat().st_mode
                if not modes & stat.S_IXUSR:
                    Path(file).chmod(modes | stat.S_IXUSR)

        # macos has a different astrond for arm64
        # check for the arm64 architecture using uname 
        if platform == 'darwin' and subprocess.check_output(['uname', '-m']).strip() == b'arm64':
            subprocess.Popen(['./astrond-arm', '--loglevel', 'info', 'config/astrond.yml'], shell=True)
        elif platform == 'darwin':
            subprocess.Popen(['./astrond', '--loglevel', 'info', 'config/astrond.yml'], shell=True)
        else:
            subprocess.Popen(['astrond', '--loglevel', 'info', 'config/astrond.yml'], creationflags=subprocess.CREATE_NEW_CONSOLE)

        # uberdog
        # if we are on unix systems then chmod launch
        if platform != 'win32':
            modes = Path(self.gameDirectory / 'game' / 'launch').stat().st_mode
            if not modes & stat.S_IXUSR:
                Path(self.gameDirectory / 'game' / 'launch').chmod(modes | stat.S_IXUSR)
        chdir(self.gameDirectory / 'game')
        environ['SERVICE_TO_RUN'] = 'UD'
        if platform == 'win32':
            subprocess.Popen(['launch',
                            '--base-channel', '1000000',
                            '--max-channels', '999999',
                            '--stateserver', '4002',
                            '--astron-ip', '127.0.0.1:7199',
                            '--eventlogger-ip', '127.0.0.1:7197',
                            'config/common.prc',
                            'config/production.prc'],
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif platform == 'darwin':
                subprocess.Popen(['./launch',
                            '--base-channel', '1000000',
                            '--max-channels', '999999',
                            '--stateserver', '4002',
                            '--astron-ip', '127.0.0.1:7199',
                            '--eventlogger-ip', '127.0.0.1:7197',
                            'config/common.prc',
                            'config/production.prc'],
                            shell=True)

        #AI
        chdir(self.gameDirectory / 'game')
        environ['SERVICE_TO_RUN'] = 'AI'
        if platform == 'win32':
            subprocess.Popen(['launch',
                            '--base-channel', '401000000',
                            '--max-channels', '999999',
                            '--stateserver', '4002',
                            '--astron-ip', '127.0.0.1:7199',
                            '--eventlogger-ip', '127.0.0.1:7197',
                            '--district-name', 'Archipelago Avenue',
                            'config/common.prc',
                            'config/production.prc'],
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif platform == 'darwin':
            subprocess.Popen(['./launch',
                            '--base-channel', '401000000',
                            '--max-channels', '999999',
                            '--stateserver', '4002',
                            '--astron-ip', '127.0.0.1:7199',
                            '--eventlogger-ip', '127.0.0.1:7197',
                            '--district-name', 'Archipelago Avenue',
                            'config/common.prc',
                            'config/production.prc'],
                            shell=True)


    # make the list of releases based on the https://github.com/toontown-archipelago/toontown-archipelago/releases API
    def getReleases(self):
        url = "https://api.github.com/repos/toontown-archipelago/toontown-archipelago/releases"
        releases = {}
        query = {'per_page': 100}
        for i in count(1):
            query['page'] = i
            response = requests.get(url, query, timeout=10)
            data = response.json()
            if not data: #github returns an empty list when you request a page further than the oldest release
                break
            for release in data:
                releases[release.get('tag_name')] = release
                assets = release.get('assets', [])
                if any(item.get('name') == ZIP_NAME for item in assets):
                    releases.update({release.get('tag_name'): release})
        return releases

    def releaseChanged(self):
        self.releaseSelected = self.ui.releasesComboBox.currentText()
        # download the release if it doesn't exist already
        self.downloadRelease()

    def writeReleaseNotes(self):
        for v in self.releases.values():
            self.ui.releaseNotesText.append(v['name'] + '\n')
            self.ui.releaseNotesText.append(v['body'])

    def setGameDirectory(self):
        self.gameDirectory = Path(GAME_DIRECTORY / self.releaseSelected)

    def downloadRelease(self):
        self.setGameDirectory()
        if Path(self.gameDirectory,'game').exists() or self.releaseSelected == "":
            return
        assets = list(
                      item for item in self.releases.get(self.releaseSelected, {}).get('assets', [])
                      if any([item['name'] == ZIP_NAME,
                          item['name'].endswith('.yaml'),
                          item['name'].endswith('.apworld')
                      ])
                     )
        if len(assets) < 3:
            print(f"Error trying to download {self.releaseSelected}: an asset is missing from the release")
            return
        elif len(assets) > 3:
            print(f"Error trying to download {self.releaseSelected}: There are too many assets. (This probably shouldn't happen.)")
            return
        self.updateProgress(0)
        self.download_thread = DownloadThread(assets, self.gameDirectory)
        self.download_thread.progress.connect(self.updateProgress)
        self.download_thread.finished.connect(self.onDownloadFinished)
        self.download_thread.start()



    def updateProgress(self, value, asset_name='game'):
        self.ui.downloadLabel.setVisible(True)
        self.ui.downloadLabel.setText(f"Downloading {asset_name}...")
        self.ui.installprogressBar.setVisible(True)
        self.ui.installprogressBar.setValue(value)

    def onDownloadFinished(self):
        self.ui.downloadLabel.setVisible(False)
        self.ui.installprogressBar.setVisible(False)
        if Path(self.gameDirectory, 'release').exists():
            for file in self.gameDirectory.glob('release/*'):
                file.rename(self.gameDirectory/file.name)
            Path(self.gameDirectory,'release').rmdir()
        self.setGameDirectory()




if __name__ == "__main__":
    app = QApplication(argv)
    widget = launcher()
    widget.show()
    sys_exit(app.exec())

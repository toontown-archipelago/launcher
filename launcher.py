# This Python file uses the following encoding: utf-8
import logging
from sys import platform, argv, exit as sys_exit, executable
import sys 
import platform as platform_module
from pathlib import Path
from os import environ, chdir, path, pardir, curdir
from itertools import count
import zipfile
import io
import datetime
import time
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
            with (self.gameDirectory/asset.get('name')).open('wb') as file:
                file.write(response.content)

class launcher(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = None
        self.setup_logging()
        if self.logger:
            self.logger.info("Launcher initialization started.")
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
        self.gameDirectory = GAME_DIRECTORY/self.releaseSelected
        self.ui.releasesComboBox.currentTextChanged.connect(self.releaseChanged)
        self.ui.pushButton_hostServer.clicked.connect(self.hostServer)
        self.ui.pushButton_connect.clicked.connect(self.connectToServer)
        self.ui.pushButton_startAll.clicked.connect(self.startAll)
        self.ui.prereleasesCheckBox.stateChanged.connect(self.updateComboBox)
        self.download_thread = None
        self.offset = None
        self.subprocesses = []
        self.server_processes = {'uberdog': None, 'astron': None, 'AI': None}
        self.done_pre_run = False
        # disable any buttons not implemented yet
        # TODO: re enable these when their feature is implemented
        self.ui.pushButton_runSettings.setEnabled(False)
        self.ui.pushButton_runSettings.setVisible(False)
        self.ui.pushButton_generateSeed.setEnabled(False)
        self.ui.pushButton_generateSeed.setVisible(False)
        self.ui.pushButton_Settings.setEnabled(False)
        self.ui.pushButton_Settings.setVisible(False)
        # allow the dragging of graphicsView to change the window position
        self.ui.graphicsView.setMouseTracking(True)
        self.ui.graphicsView.mousePressEvent = self.mousePressEvent
        self.ui.graphicsView.mouseMoveEvent = self.mouseMoveEvent
        self.ui.graphicsView.mouseReleaseEvent = self.mouseReleaseEvent

    def setup_logging(self):
        log_directory = self.getLauncherLogDirectory()
        log_path = Path(log_directory / 'launcher.log')
        logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Launcher started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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

    # on exit we should close any existing subprocesses
    def closeEvent(self, event):
        for i in self.subprocesses:
            if i.poll() is None:
                i.kill()
        for i in self.server_processes.values():
            if i is not None and i.poll() is None:
                i.kill()
        super().closeEvent(event)


    def getLauncherLogDirectory(self):
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            return Path(sys.executable).parent
        else:
            # Running in a normal Python environment
            return Path(__file__).parent
        
    def loadPrefs(self):
        try:
            with (GAME_DIRECTORY/'prefs.json').open('r', encoding='utf-8') as file:
                prefs = json.load(file)
        except OSError:
                if self.logger:
                    self.logger.exception("Preferences could not be loaded.")
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
        with (GAME_DIRECTORY/'prefs.json').open('w', encoding='utf-8') as file:
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


    def preRun(self):
        #if we've already done this since the last time the version was changed, there's no need.
        if self.done_pre_run:
            return
        # ensure we've downloaded the selected release.
        self.downloadRelease()
        # use callback to notify us when the download is complete to execute the rest of the code
        if self.download_thread:
            self.download_thread.finished.connect(self.preSetup)
            return
      
    def preSetup(self):
        # macos folder structure didn't match windows, at least up to v0.10.4, ensure compatibility with those versions.
        if (self.gameDirectory/'release').exists():
            for file in self.gameDirectory.glob('release/*'):
                file.rename(self.gameDirectory/file.name)
            (self.gameDirectory/'release').rmdir()
        # ensure launch has execute permissions for platforms other than windows.
        if platform != 'win32':
            modes = (self.gameDirectory/'game'/'launch').stat().st_mode
            if not modes & stat.S_IXUSR:
                (self.gameDirectory/'game'/'launch').chmod(modes | stat.S_IXUSR)
            # do the same for astrond
            for file in (self.gameDirectory/'game'/'astron').glob('*'):
                modes = file.stat().st_mode
                if not modes & stat.S_IXUSR:
                    file.chmod(modes | stat.S_IXUSR)
        # ensure the log directory exists.
        (self.gameDirectory/'log').mkdir(exist_ok=True)
        # TODO: setup cleaning log files out, delete older than 24 hours, probably.
        self.done_pre_run = True

    def startAll(self):
        self.hostServer()
        self.connectToServer()

    def hostServer(self):
        # run pre run if necessary
        self.preRun()
        self.startServerThreads()

    def runClient(self):
        self.savePrefs()
        chdir(self.gameDirectory/'game')
        launchFile = self.gameDirectory/'game'/'launch'
        with (self.gameDirectory/'log'/f'client-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.log').open('w', encoding='utf-8') as logfile:
            if platform == 'darwin':
                p = subprocess.Popen([ launchFile ], stdout=logfile, stderr=subprocess.STDOUT)
            elif platform == 'win32':
                p = subprocess.Popen([ launchFile ], creationflags=subprocess.CREATE_NO_WINDOW, stdout=logfile, stderr=subprocess.STDOUT)
            elif platform.startswith('linux'):
                # use wine
                p = subprocess.Popen([ 'wine', launchFile ], stdout=logfile, stderr=subprocess.STDOUT)
        return p


    def connectToServer(self):
        #execute pre run steps, if necessary.
        self.preRun()
        # read from lineEdit_ipAddress, and lineEdit_username,
        # default ip : 127.0.0.1
        # default username : player1
        ip = self.ui.lineEdit_ipAddress.text()
        username = self.ui.lineEdit_username.text()
        if not ip:
            ip = "127.0.0.1"
        if not username:
            username = "player1"
        if self.download_thread:
            self.download_thread.finished.connect(lambda: self.startClientThread(username, ip))
        else:
            self.startClientThread(username, ip)



    def startClientThread(self, username, ip):
        environ['SERVICE_TO_RUN'] = 'CLIENT'
        environ['TTOFF_LOGIN_TOKEN'] = username
        environ['TTOFF_GAME_SERVER'] = ip
        self.subprocesses.append(self.runClient())

    def startServerThreads(self):
        for service in ['astron', 'uberdog', 'AI']:
            if (self.server_processes.get(service, None) is None # service never started,
               or not self.server_processes[service].poll() is None): # or service has stopped.
                self.server_processes[service] = self.startService(service)

    def startAstronServer(self):
        astron_dir = self.gameDirectory / 'game' / 'astron'
        config_path = astron_dir / 'config' / 'astrond.yml'
        chdir(astron_dir)
        # Run the astrond subprocess
        # macos has a different astrond for arm64
        # check for the arm64 architecture using uname
        if platform_module.machine() == 'arm64':
            astrond_executable = self.gameDirectory/'game'/'astron'/'astrond-arm'
        else:
            astrond_executable = self.gameDirectory/'game'/'astron'/'astrond'
        with (self.gameDirectory/'log'/f'astrond-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.log').open('w', encoding='utf-8') as logfile:
            if platform == 'win32':
                p = subprocess.Popen([astrond_executable, '--loglevel', 'info', str(config_path)], creationflags=subprocess.CREATE_NO_WINDOW, stdout=logfile, stderr=subprocess.STDOUT)
            else:
                p = subprocess.Popen([astrond_executable, '--loglevel', 'info', str(config_path)], stdout=logfile, stderr=subprocess.STDOUT)
        return p

    def startService(self, service):
        chdir(self.gameDirectory / 'game')
        if service == 'astron':
            return self.startAstronServer()
        if service == 'uberdog':
            environ['SERVICE_TO_RUN'] = 'UD'
            base_channel = '1000000'
            extra_args = []
        elif service == 'AI':
            environ['SERVICE_TO_RUN'] = 'AI'
            base_channel = '401000000'
            extra_args = ['--district-name', 'Archipelago Avenue']
        else:
            raise ValueError(f"Unknown TTAP Service: {service}")
        with (self.gameDirectory/'log'/f'{service}-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.log').open('w', encoding='utf-8') as logfile:
            if platform == 'win32':
                p = subprocess.Popen(['launch',
                                    '--base-channel', base_channel,
                                    '--max-channels', '999999',
                                    '--stateserver', '4002',
                                    '--astron-ip', '127.0.0.1:7199',
                                    '--eventlogger-ip', '127.0.0.1:7197',
                                    *extra_args,
                                    'config/common.prc',
                                    'config/production.prc'],
                                    creationflags=subprocess.CREATE_NO_WINDOW,
                                    stdout=logfile, stderr=subprocess.STDOUT)
            else:
                p = subprocess.Popen(['./launch',
                                    '--base-channel', base_channel,
                                    '--max-channels', '999999',
                                    '--stateserver', '4002',
                                    '--astron-ip', '127.0.0.1:7199',
                                    '--eventlogger-ip', '127.0.0.1:7197',
                                    *extra_args,
                                    'config/common.prc',
                                    'config/production.prc'],
                                    stdout=logfile, stderr=subprocess.STDOUT)
        return p

    # make the list of releases based on the https://github.com/toontown-archipelago/toontown-archipelago/releases API
    def getReleases(self):
        url = "https://api.github.com/repos/toontown-archipelago/toontown-archipelago/releases"
        releases = {}
        query = {'per_page': 100}
        for i in count(1):
            query['page'] = i
            response = requests.get(url, query, timeout=10)
            data = response.json()
            if not data: # github returns an empty list when you request a page further than the oldest release
                break
            for release in data:
                assets = release.get('assets', [])
                if any(item.get('name') == ZIP_NAME for item in assets):
                    releases.update({release.get('tag_name'): release})
        return releases

    def releaseChanged(self, releaseSelected):
        self.releaseSelected = releaseSelected
        self.gameDirectory = GAME_DIRECTORY/releaseSelected
        self.done_pre_run = False

    def writeReleaseNotes(self):
        for v in self.releases.values():
            self.ui.releaseNotesText.append(v['name'] + '\n')
            self.ui.releaseNotesText.append(v['body'])

    def downloadRelease(self):
        if (self.gameDirectory/'game').exists() or self.releaseSelected == "":
            return
        assets = list(
                      item for item in self.releases.get(self.releaseSelected, {}).get('assets', [])
                      if any([item['name'] == ZIP_NAME,
                          item['name'].endswith('.yaml'),
                          item['name'].endswith('.apworld')
                      ])
                     )
        
        if len(assets) < 3:
            if self.logger:
                self.logger.exception(f"Error trying to download {self.releaseSelected}: an asset is missing from the release")
            print(f"Error trying to download {self.releaseSelected}: an asset is missing from the release")
            return
        elif len(assets) > 3:
            if self.logger:
                self.logger.exception(f"Error trying to download {self.releaseSelected}: There are too many assets. (This probably shouldn't happen.)")    
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
        self.ui.downloadLabel.setText(f"Download complete.")
        self.ui.installprogressBar.setVisible(False)




if __name__ == "__main__":
    app = QApplication(argv)
    widget = launcher()
    widget.show()
    # write to log file on crash
    try:
        app.exec()
    except Exception as e:
        widget.logger.exception(f"Exception occured while running the launcher: {e}")
        sys_exit(1)

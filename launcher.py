# This Python file uses the following encoding: utf-8
import sys
import requests
import os
import zipfile
import io
import time
import multiprocessing
import stat
import subprocess
import threading
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtCore import QPoint
from PySide6.QtCore import QThread, Signal
# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_launcher
import resources_rc
if sys.platform == 'win32':
    GAME_DIRECTORY_WINDOWS = os.path.join(os.getenv("APPDATA"), "Toontown Archipelago")
elif sys.platform == 'darwin':
    GAME_DIRECTORY_MACOS = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Toontown Archipelago")
elif sys.platform == 'linux':
    GAME_DIRECTORY_LINUX = os.path.join(os.getenv("HOME"), "Toontown Archipelago")
LAUNCHER_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal()
    def __init__(self, url, url_yaml, apworld_url, releaseSelected):
        super().__init__()
        self.url = url
        self.url_yaml = url_yaml
        self.apworld_url = apworld_url
        self.releaseSelected = releaseSelected

    def run(self):
        self.download_files(self.url, self.url_yaml, self.apworld_url)
        self.finished.emit()

    def download_files(self, url, url_yaml, apworld_url):
        # Download the first file
        self.downloadFile(url)
        self.progress.emit(33)
        
        # Download the second file
        self.downloadFile(url_yaml)
        self.progress.emit(66)
        
        # Download the third file
        self.downloadFile(apworld_url)
        self.progress.emit(100)

    def downloadFile(self, url):
        # download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        # if file is a zip extract it
        if url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                if sys.platform == 'darwin':
                    archive.extractall(GAME_DIRECTORY_MACOS + f'/{self.releaseSelected}')
                elif sys.platform == 'win32':
                    archive.extractall(GAME_DIRECTORY_WINDOWS + f'/{self.releaseSelected}')
                elif sys.platform.startswith('linux'):
                    archive.extractall(GAME_DIRECTORY_LINUX) + f'/{self.releaseSelected}'
                else:
                    print("Unsupported platform")
                    return
        else:
            # save the file
            with open(url.split("/")[-1], "wb") as file:
                # write to the game directory
                if sys.platform == 'darwin':
                    with open(GAME_DIRECTORY_MACOS + f'/{self.releaseSelected}' + '/' + url.split("/")[-1], "wb") as file:
                        file.write(response.content)
                elif sys.platform == 'win32':
                    with open(GAME_DIRECTORY_WINDOWS + f'/{self.releaseSelected}' + '/' + url.split("/")[-1], "wb") as file:
                        file.write(response.content)
                elif sys.platform.startswith('linux'):
                    with open(GAME_DIRECTORY_LINUX + f'/{self.releaseSelected}' + '/' + url.split("/")[-1], "wb") as file:
                        file.write(response.content)
                else:
                    print("Unsupported platform")
                    return

class launcher(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_launcher()
        self.ui.setupUi(self)
        self.ui.installprogressBar.setVisible(False)
        # make the main window transparent
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
    
        self.ui.minusButton.clicked.connect(self.showMinimized)
        self.ui.closeButton.clicked.connect(self.close)
        self.ui.downloadLabel.setVisible(False)
        self.setMouseTracking(True)
        # fill the releases combo box with the list of  releases
        releases = self.getReleases()
        self.ui.releasesComboBox.addItems(releases)
        # choose the latest release by default
        self.ui.releasesComboBox.setCurrentIndex(0)
        self.releaseSelected = releases[0]
        self.ui.releasesComboBox.currentIndexChanged.connect(self.releaseChanged)
        self.setGameDirectory()
        self.ui.pushButton_hostServer.clicked.connect(self.hostServer)
        self.ui.pushButton_connect.clicked.connect(self.connectToServer)
        self.ui.rememberMecheckBox.stateChanged.connect(self.rememberMe)
        self.download_thread = None


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



    def rememberMe(self):
        if self.ui.rememberMeCheckBox.isChecked():
            # TODO save the username and ip address to a file so we can remember it
            return 
        


    def hostServer(self):
        # check if we downloaded the release we selected
        self.downloadRelease()
        # TODO , multithreaded running of all server components including astron, uberdog and ai

    def runClient(self):
        if sys.platform == 'darwin':
            modes = os.stat('launch').st_mode
            if not modes & stat.S_IXUSR:
               os.chmod('launch', modes | stat.S_IXUSR)
            subprocess.Popen(['./launch'])
        elif sys.platform == 'win32':
            subprocess.Popen('launch', creationflags=134217728)
        elif sys.platform.startswith('linux'):
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
        os.environ['SERVICE_TO_RUN'] = 'CLIENT'
        os.environ['TTOFF_LOGIN_TOKEN'] = username 
        os.environ['TTOFF_GAME_SERVER'] = ip
        os.chdir(self.gameDirectory)
        clientThread = threading.Thread(target=self.runClient)
        clientThread.start()

    # make the list of releases based on the https://github.com/toontown-archipelago/toontown-archipelago/releases API
    def getReleases(self):
        url = "https://api.github.com/repos/toontown-archipelago/toontown-archipelago/releases"
        response = requests.get(url)
        data = response.json()
        releases = []
        for release in data:
            assets = release.get('assets', [])
            if sys.platform == 'darwin':
                for asset in assets:
                    if asset["name"] == "TTAP-macos.zip":
                        releases.append(release["name"])
            elif sys.platform == 'win32':
                for asset in assets:
                    if asset["name"] == "TTAP.zip":
                        releases.append(release["name"])
            elif sys.platform.startswith('linux'):
                # download the windows version so they can use wine
                for asset in assets:
                    if asset["name"] == "TTAP.zip":
                    # if asset["name"] == "TTAP-linux.zip":
                        releases.append(release["name"])
            else:
                print("Unsupported platform")
                return []
        return releases
    
    def releaseChanged(self, release):
        self.releaseSelected = release
        # download the release if it doesn't exist already
        self.downloadRelease()

    def setGameDirectory(self):
        if sys.platform == 'darwin':
            self.gameDirectory = GAME_DIRECTORY_MACOS + f'/{self.releaseSelected}/release/game'
        elif sys.platform == 'win32':
            self.gameDirectory = GAME_DIRECTORY_WINDOWS + f'/{self.releaseSelected}/release/game'
        elif sys.platform.startswith('linux'):
            self.gameDirectory = GAME_DIRECTORY_LINUX + f'/{self.releaseSelected}/release/game'
        else:
            print("Unsupported platform")
            self.gameDirectory = None
            return
        
    def checkIfGameDirectoryExists(self):
         if sys.platform == 'darwin':
            if os.path.exists(GAME_DIRECTORY_MACOS + f'/{self.releaseSelected}'):
                return True
         elif sys.platform == 'win32':
            if os.path.exists(GAME_DIRECTORY_WINDOWS + f'/{self.releaseSelected}'):
                return True
         elif sys.platform.startswith('linux'):
            if os.path.exists(GAME_DIRECTORY_LINUX + f'/{self.releaseSelected}'):
                return True
            
    def downloadRelease(self):
        if self.checkIfGameDirectoryExists():
            self.setGameDirectory()
            return
        if sys.platform == 'darwin':
            url = f"https://github.com/toontown-archipelago/toontown-archipelago/releases/download/{self.releaseSelected}/TTAP-macos.zip"
        elif sys.platform == 'win32':
            url = f"https://github.com/toontown-archipelago/toontown-archipelago/releases/download/{self.releaseSelected}/TTAP.zip"
        elif sys.platform.startswith('linux'):
            url = f"https://github.com/toontown-archipelago/toontown-archipelago/releases/download/{self.releaseSelected}/TTAP.zip"
        else:
            print("Unsupported platform")
            return
           
        url_yaml = f"https://github.com/toontown-archipelago/toontown-archipelago/releases/download/{self.releaseSelected}/EXAMPLE_TOONTOWN.yaml"
        apworld_url = f"https://github.com/toontown-archipelago/toontown-archipelago/releases/download/{self.releaseSelected}/toontown.apworld"

        self.download_thread = DownloadThread(url, url_yaml, apworld_url, self.releaseSelected)
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
    app = QApplication(sys.argv)
    widget = launcher()
    widget.show()
    sys.exit(app.exec())

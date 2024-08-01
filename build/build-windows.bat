# use nuitka to build the launcher

nuitka.exe "launcher.py" --standalone --assume-yes-for-downloads --windows-console-mode='disable' --enable-plugins=pyside6 --windows-icon-from-ico=resources/icon.ico --output-dir=dist

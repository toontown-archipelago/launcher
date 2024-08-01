# Within GitHub Actions and similar platforms, it's advisable to use the Python.org
# version of Python 3.11. This enables a universal2 framework for py2app.
# (Otherwise, the default runners on GitHub include a version with only one architecture.)
if [[ "$CI" == "true" ]]; then
  shopt -s expand_aliases
  alias python3=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11
fi
python3 -m venv --upgrade-deps venv
source venv/bin/activate
python3 -m pip install wheel



# use nuitka to build the launcher
nuitka --standalone   --assume-yes-for-downloads --output-dir=dist  --enable-plugins=pyside6  --macos-create-app-bundle --macos-target-arch=arm64 --macos-app-icon=resources/icon.icns  launcher.py
nuitka --standalone   --assume-yes-for-downloads  --output-dir=dist_x86_64 --enable-plugins=pyside6 --macos-target-arch=x86_64 --macos-create-app-bundle --macos-app-icon=resources/icon.icns  launcher.py

codesign --deep --force --sign - dist/launcher.app
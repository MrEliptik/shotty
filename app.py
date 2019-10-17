import sys
import mss
import platform
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal
from shotty_gui import ShottyFullscreen, ShottyAboutWindow
import _globals

_platform = platform.system()
# Global app
app = QApplication(sys.argv)

def main(): 
    app.setQuitOnLastWindowClosed(False)
    qIcon = QIcon('icons/shotty.png')
    app.setWindowIcon(qIcon)
    
    shotty = ShottyFullscreen()

    tray = QSystemTrayIcon()
    if tray.isSystemTrayAvailable():
        tray.setIcon(QIcon('icons/shotty.png'))
        tray.setVisible(True)
        tray.show()

        # Add a menu
        trayMenu = QMenu()
        region_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take region screenshot')
        full_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take screenshot')
        settings_action = QAction(QIcon("icons/settings.png"), 'Settings')
        about_action = QAction(QIcon("icons/info.png"), 'About')
        exit_action = QAction(QIcon("icons/exit.png"), 'Exit Shoty')

        exit_action.triggered.connect(app.exit)
        about_action.triggered.connect(shotty.showShottyAboutWindow)

        trayMenu.addAction(region_screenshot_action)
        trayMenu.addAction(full_screenshot_action)
        trayMenu.addAction(settings_action)
        trayMenu.addAction(about_action)
        trayMenu.addAction(exit_action)    

        tray.setContextMenu(trayMenu)
    else:
        print("[ERROR] Can't instantiate tray icon")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

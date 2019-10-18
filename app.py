import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal, QDateTime
from shotty_gui import ShottyFullscreen, ShottyAboutWindow
import _globals
from utils import showNotification, screenshot, getDateTime

def main(): 

    d = getDateTime()

    # Global app
    app = QApplication(sys.argv)

    QApplication.setQuitOnLastWindowClosed(False)
    qIcon = QIcon('icons/shotty.png')
    app.setWindowIcon(qIcon)
    
    shotty = ShottyFullscreen()

    tray = QSystemTrayIcon()
    if tray.isSystemTrayAvailable():
        showNotification('Shotty', 'Running in the background')

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
        region_screenshot_action.triggered.connect(shotty.initUI)
        # We need to pass checked because connect passes
        # a bool arg as first param
        full_screenshot_action.triggered.connect(
            lambda checked, date=getDateTime(), x1=-1, y1=-1, x2=-1, y2=-1, 
                im=screenshot(): shotty.saveScreenShot(date, x1, y1, x2, y2, im=im[:,:,:3])
        )
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

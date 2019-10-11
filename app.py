import sys
import mss
import platform
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal
from shotty_gui import ShottyFullscreen, ShottyInfoWindow
import _globals

_platform = platform.system()
# Global app
app = QApplication(sys.argv)

shotty = None

if _platform == 'Linux':
    from Xlib.display import Display
    from Xlib import X
elif _platform == 'Windows':
    import pythoncom as pc
    from pyHook import HookManager, GetKeyState, HookConstants
elif _platform == 'Darwin':
    print('[ERROR] macOS not supported!')
else:
    print('[ERROR] {} not supported!'.format(_platform))

def OnKeyboardEvent(event):
    #global running
    if _platform == 'Linux':
        if event._data['detail'] == 107:
            _globals.keyLogging = False
            return False
    elif _platform == 'Windows':
        if event.KeyID == 44:
            print("snapshot pressed")
            _globals.keyLogging = False
            # Ensures event will not propagate
            return False
    # Event will propagate normally
    return True

class Tray():
    def __init__(self, qIcon):
        self.tray = self.createShottyTray(qIcon)
        
    def createShottyTray(self, qIcon):
        tray = QSystemTrayIcon(qIcon)
        if tray.isSystemTrayAvailable():
            tray.setIcon(qIcon)
            tray.setVisible(True)
            tray.setContextMenu(self.createTrayMenu())
            tray.show()

            return tray

        print("[ERROR] Can't instantiate tray icon")
        return None

    def createTrayMenu(self):
        # Add a menu
        trayMenu = QMenu()
        region_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take region screenshot')
        full_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take screenshot')
        settings_action = QAction(QIcon("icons/settings.png"), 'Settings')
        about_action = QAction(QIcon("icons/info.png"), 'About')
        exit_action = QAction(QIcon("icons/exit.png"), 'Exit Shoty')

        exit_action.triggered.connect(exitApp)
        about_action.triggered.connect(launchShottyInfoWindow)

        trayMenu.addAction(region_screenshot_action)
        trayMenu.addAction(full_screenshot_action)
        trayMenu.addAction(settings_action)
        trayMenu.addAction(about_action)
        trayMenu.addAction(exit_action) 

        return trayMenu   

def main():
    #global keyLogging
    # Try putting the app in tray  
    app.setQuitOnLastWindowClosed(False)
    qIcon = QIcon('icons/shotty.png')
    app.setWindowIcon(qIcon)
    
    tray = Tray(qIcon)
    '''
    tray = QSystemTrayIcon()
    if tray.isSystemTrayAvailable():
        tray.setIcon(qIcon)
        tray.setVisible(True)
        tray.show()

        # Add a menu
        trayMenu = QMenu()
        region_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take region screenshot')
        full_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take screenshot')
        settings_action = QAction(QIcon("icons/settings.png"), 'Settings')
        about_action = QAction(QIcon("icons/info.png"), 'About')
        exit_action = QAction(QIcon("icons/exit.png"), 'Exit Shoty')

        exit_action.triggered.connect(exitApp)
        about_action.triggered.connect(launchShottyInfoWindow)

        trayMenu.addAction(region_screenshot_action)
        trayMenu.addAction(full_screenshot_action)
        trayMenu.addAction(settings_action)
        trayMenu.addAction(about_action)
        trayMenu.addAction(exit_action)    

        tray.setContextMenu(trayMenu)
    else:
        print("[ERROR] Can't instantiate tray icon")
    '''

    # Run until user clicks on exit iconTray
    while _globals.running:
        if _platform == 'Linux':
            
            # Get root screen
            root = Display().screen().root
            # Add key grabber for 'print'
            root.grab_key(107, X.Mod2Mask, 0, X.GrabModeAsync, X.GrabModeAsync)

            # Create a loop to keep the application running
            _globals.keyLogging = True
            while _globals.keyLogging:
                event = root.display.next_event()
                OnKeyboardEvent(event)
                time.sleep(0.1)
            
            # Close the grabber for the time 
            # of the application
            #TODO

            startApp(screenshot(), tray)

        elif _platform == 'Windows':
            # create a hook manager
            hm = HookManager()
            # watch for all mouse events
            hm.KeyDown = OnKeyboardEvent
            # set the hook
            hm.HookKeyboard()
            # wait forever
            _globals.keyLogging = True
            while _globals.keyLogging:
                pc.PumpWaitingMessages()
                time.sleep(0.1)

            startApp(screenshot(), tray)

def screenshot():
    with mss.mss() as sct:
        # Get raw pixels from the screen, save it to a Numpy array
        im = np.array(sct.grab(sct.monitors[1]))
    return im

def startApp(im, tray): 
    global shotty  
    shotty = ShottyFullscreen(im, tray)
    sys.exit(app.exec_())

def launchShottyInfoWindow():
    shotty = ShottyInfoWindow()
    #sys.exit(app.exec_())

def exitApp():
    _globals.running = False
    sys.exit()

if __name__ == "__main__":
    main()

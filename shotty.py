import sys
import mss
import platform
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from gui import Shotty

_platform = platform.system()

# Global app
app = QApplication(sys.argv)
keyLogging = False

if _platform == 'Linux':
    import pyxhook     
elif _platform == 'Windows':
    import pythoncom as pc
    from pyHook import HookManager, GetKeyState, HookConstants
elif _platform == 'Darwin':
    print('[ERROR] macOS not supported!')
else:
    print('[ERROR] {} not supported!'.format(_platform))

def OnKeyboardEvent(event):
    global keyLogging
    if _platform == 'Linux':
        if event.Ascii == 44:
            keyLogging = False
            return False
    elif _platform == 'Windows':
        if event.KeyID == 44:
            print("snapshot pressed")
            keyLogging = False
            # Ensures event will not propagate
            return False
    # Event will propagate normally
    return True

def main():
    global keyLogging
    # Try putting the app in tray  
    app.setQuitOnLastWindowClosed(False)
    qIcon = QIcon('icons/shotty.png')
    app.setWindowIcon(qIcon)
    tray = QSystemTrayIcon()
    if tray.isSystemTrayAvailable():
        tray.setIcon(qIcon)
        tray.setVisible(True)
        tray.show()

        # Add a menu
        trayMenu = QMenu()
        region_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take region screenshot')
        full_screenshot_action = QAction(QIcon("icons/screenshot.png"), 'Take screenshot')
        settings_screenshot_action = QAction(QIcon("icons/settings.png"), 'Settings')
        exit_action = QAction(QIcon("icons/exit.png"), 'Exit Shoty')
        trayMenu.addAction(region_screenshot_action)
        trayMenu.addAction(full_screenshot_action)
        trayMenu.addAction(settings_screenshot_action)
        trayMenu.addAction(exit_action)

        tray.setContextMenu(trayMenu)
    else:
        print("[ERROR] Can't instantiate tray icon")

    if _platform == 'Linux':
        # Create hookmanager
        hookman = pyxhook.HookManager()
        # Define our callback to fire when a key is pressed down
        hookman.KeyDown = OnKeyboardEvent
        # Hook the keyboard
        hookman.HookKeyboard()
        # Start our listener
        hookman.start()

        # Create a loop to keep the application running
        keyLogging = True
        while keyLogging:
            time.sleep(0.1)

        startApp(screenshot(), tray)
    
    elif _platform == 'Windows':
        # create a hook manager
        hm = HookManager()
        # watch for all mouse events
        hm.KeyDown = OnKeyboardEvent
        # set the hook
        hm.HookKeyboard()
        # wait forever
        keyLogging = True
        while keyLogging:
            pc.PumpWaitingMessages()
            time.sleep(0.1)

        startApp(screenshot(), tray)

    '''
    # Close the listener when we are done
    hookman.cancel()
    '''
def screenshot():
    with mss.mss() as sct:
        # Get raw pixels from the screen, save it to a Numpy array
        im = np.array(sct.grab(sct.monitors[1]))
    return im

def startApp(im, tray):   
    shotty = Shotty(im, tray)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

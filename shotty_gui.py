from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QDesktopWidget, QMenu, QFileDialog, QAction, QSystemTrayIcon, QMessageBox
from PyQt5.QtCore import Qt, QObject, QTimer, QRect, QPoint, QDateTime, QDir, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QBrush, QColor, QPen, QIcon, QFont
from PyQt5.QtMultimedia import QSound
import numpy as np
import sys
import time
import platform
from threading import Thread
from utils import mask_image, setMouseTracking, screenshot, showNotification, getExtension, getDateTime
import _globals
from about import ShottyAboutWindow

_platform = platform.system()

if _platform == 'Linux':
    from Xlib.display import Display
    from Xlib import X
elif _platform == 'Windows':
    import pythoncom as pc
    from pyHook import HookManager
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

class overlay(QWidget):
    def __init__(self, parent=None):
        super(overlay, self).__init__(parent)

        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)

        self.im = None

        self.setPalette(palette)

        self.active = True

        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0

        self.line_x = 0
        self.line_y = 0

    def setCoords(self, x1, y1, x2, y2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

    def setLineCoords(self, line_x, line_y):
        self.line_x = line_x
        self.line_y = line_y

    def paintEvent(self, event):
        if not self.active:
            return
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.green, Qt.DiagCrossPattern))
        painter.drawRect(self.x1, self.y1, self.x2-self.x1, self.y2-self.y1)
        painter.setPen(QPen(Qt.green, 1, Qt.DotLine))
        painter.drawLine(0, self.line_y, self.width(), self.line_y)
        painter.drawLine(self.line_x, 0, self.line_x, self.height())

class HotkeyThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)

    # run method gets called when we start the thread
    def run(self):
        # Run until user clicks on exit iconTray
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
                #print('Hotkey thread waiting..')

            print('Closing HookManager')
            del hm

        print("Finish hotkey")
        # git clone done, now inform the main thread with the output
        self.signal.emit('done')

class SaveImageThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, im, filename):
        QThread.__init__(self)
        self.im = im
        self.filename = filename

    # run method gets called when we start the thread
    def run(self):
        self.im.save(self.filename)
        self.signal.emit('done')

class ShottyFullscreen(QWidget):
    def __init__(self):
        super().__init__()

        # This is the thread object
        self.hotkeyThread = HotkeyThread()  
        self.hotkeyThread.start()
        # Connect the signal from the thread to the finished method
        self.hotkeyThread.signal.connect(self.initUI)

    def initUI(self):
        QSound.play("sounds/shutter.wav")

        self.pressed = False
        QApplication.setOverrideCursor(Qt.CrossCursor)
        # Create widget
        self.l_imFullscreen = QLabel(self)
        self.l_mousePos = QLabel(self)
        self.l_dimensions = QLabel(self)

        font = QFont("Calibri", 15)
        self.l_dimensions.setFont(font)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showFullscreenshotMenu)

        self.setTextLabelPosition(0, 0)
        setMouseTracking(self, True)
        self.rect_x1 = 0
        self.rect_y1 = 0
        self.rect_x2 = 0
        self.rect_y2 = 0
        self.line_x = 0
        self.line_y = 0
     
        im = screenshot()
        # Remove alpha
        self.im = im[:, :, :3].copy()

        h, w, c = self.im.shape
        print('New shape: {},{},{}'.format(h, w, c))

        qImg = QImage(self.im, w, h, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        self.l_imFullscreen.setPixmap(pixmap)
        self.l_imFullscreen.resize(pixmap.width(), pixmap.height())

        self.overlay = overlay(self.l_imFullscreen)
        self.overlay.resize(pixmap.width(), pixmap.height())

        print("Overlay size: {}, {}".format(
            self.overlay.frameGeometry().width(), self.overlay.frameGeometry().height()))

        setMouseTracking(self, True)

        self.setWindowFlags(
            Qt.WindowCloseButtonHint | Qt.WindowType_Mask)
        monitor = QDesktopWidget().screenGeometry(0)
        self.move(monitor.left(), monitor.top())
        self.showFullScreen()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
            # User hit escape, we want to run hotkey hook again
            self.hotkeyThread.start()
            self.hotkeyThread.signal.connect(self.initUI)

    def mouseMoveEvent(self, e):
        self.line_x = e.x()
        self.line_y = e.y()

        zoom = self.im[e.y()-10:e.y()+10, e.x()-10:e.x()+10, :].copy()
        h, w, _ = zoom.shape
        qPixZoom = mask_image(zoom)
        qPixZoom = qPixZoom.scaled(160, 160, Qt.KeepAspectRatio)

        painter = QPainter()
        painter.begin(qPixZoom)
        painter.setPen(QPen(Qt.green, 4, Qt.DotLine))
        # Horizontal line
        painter.drawLine(0, 80, 65, 80)
        painter.drawLine(95, 80, 160, 80)
        # Vertical line
        painter.drawLine(80, 0, 80, 65)
        painter.drawLine(80, 95, 80, 160)
        painter.end()
        self.l_mousePos.setPixmap(qPixZoom)
        self.l_mousePos.resize(160, 160)

        # print(e.x(), e.y())
        self.setTextLabelPosition(e.x(), e.y())
        QWidget.mouseMoveEvent(self, e)
        self.overlay.setLineCoords(e.x(), e.y())
        if self.pressed:
            self.overlay.setCoords(self.rect_x1, self.rect_y1, e.x(), e.y())
            self.l_dimensions.move(self.rect_x1, self.rect_y1 - 35)
            self.l_dimensions.resize(e.x(), 50)
            self.l_dimensions.setText('W: %dpx H: %dpx' % (abs(e.x() - self.rect_x1), abs(e.y() - self.rect_y1)))
        self.overlay.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.pressed = True
            self.rect_x1 = e.x()
            self.rect_y1 = e.y()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.showCroppedMenu(e)
            self.pressed = False
            self.rect_x1 = 0
            self.rect_y1 = 0
            self.rect_x2 = 0
            self.rect_y2 = 0
            self.overlay.setCoords(
                self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
            self.overlay.update()
            self.l_dimensions.setText('')
        if e.button() == Qt.RightButton:
            self.overlay.active = False
            self.showFullscreenshotMenu(e)

    def setTextLabelPosition(self, x, y):
        # make sur zoom bubble stay inside the screen
        if (x + 160) > self.width():
            self.l_mousePos.move(x - 160 - 20, y)
        elif (y + 160) > self.height():
            self.l_mousePos.move(x + 20, y - 160)
        else:
            self.l_mousePos.move(x + 20, y)

    def saveScreenShot(self, filename, x1, y1, x2, y2, im="self"):

        if getExtension(filename) == '':
            filename += '.png'
        
        if im == "self":
            im = self.im
        if x1 == -1:
            h, w, _ = im.shape
            qScreen = QImage(im.copy(), w, h,
                             QImage.Format_RGB888).rgbSwapped()
        else:
            crop_im = im[y1:y2, x1:x2, :].copy()
            h, w, _ = crop_im.shape
            qScreen = QImage(crop_im, w, h, QImage.Format_RGB888).rgbSwapped()

        self.saveImageThread = SaveImageThread(qScreen, filename)  
        self.saveImageThread.start()
        # Connect the signal from the thread to the finished method
        self.saveImageThread.signal.connect(
            lambda checked, title='Shotty', msg='Image saved: {}'.format(filename): showNotification(title, msg)
        )

        #return qScreen.save(filename)

    def copyToClipboard(self, x1, y1, x2, y2):
        if x1 == -1:
            h, w, _ = self.im.shape
            qScreen = QImage(self.im.copy(), w, h,
                             QImage.Format_RGB888).rgbSwapped()
        else:
            crop_im = self.im[y1:y2, x1:x2, :].copy()
            h, w, _ = crop_im.shape
            qScreen = QImage(crop_im, w, h, QImage.Format_RGB888).rgbSwapped()
        QApplication.clipboard().setImage(qScreen)

    def showCroppedMenu(self, e):
        menu = QMenu()
        save_crop_action = QAction(QIcon("icons/save.png"), "Save region", self)
        saveAs_crop_action = QAction(QIcon("icons/save-as.png"), "Save region as..", self)
        clipboard_crop_action = QAction(QIcon("icons/copy-clipboard.png"), "Copy region to clipboard", self)
        cancel_action = QAction(QIcon("icons/close-window.png"), "Cancel", self)
        exit_action = QAction(QIcon("icons/exit.png"), "Exit", self)

        menu.addAction(save_crop_action)
        menu.addAction(saveAs_crop_action)
        menu.addAction(clipboard_crop_action)
        menu.addAction(cancel_action)
        menu.addAction(exit_action)

        action = menu.exec_(self.mapToGlobal(QPoint(e.x(), e.y())))

        if action == save_crop_action:
            datetime = getDateTime()
            self.saveScreenShot(datetime,self.rect_x1, self.rect_y1, e.x(), e.y())
            self.close()
        elif action == saveAs_crop_action:
            datetime = getDateTime()
            filename = self.saveFileDialog(datetime)
            if filename:
                self.saveScreenShot(filename, self.rect_x1, self.rect_y1, e.x(), e.y())
                self.close()
        elif action == clipboard_crop_action:
            self.copyToClipboard(self.rect_x1, self.rect_y1, e.x(), e.y())
            self.close()
        elif action == cancel_action:
            return
        elif action == exit_action:
            self.close()
            _globals.running = False

    def showFullscreenshotMenu(self, e):
        menu = QMenu()

        save_full_action = QAction(QIcon("icons/save.png"), "Save", self)
        saveAs_full_action = QAction(QIcon("icons/save.png"), "Save as..", self)
        clipboard_full_action = QAction(QIcon("icons/copy-clipboard.png"), "Copy to clipboard", self)
        cancel_action = QAction(QIcon("icons/close-window.png"), "Cancel", self)
        exit_action = QAction(QIcon("icons/exit.png"), "Exit", self) 

        menu.addAction(save_full_action)
        menu.addAction(saveAs_full_action)
        menu.addAction(clipboard_full_action)
        menu.addAction(cancel_action)
        menu.addAction(exit_action)
        
        action = menu.exec_(self.mapToGlobal(QPoint(e.x(), e.y())))

        self.overlay.active = True

        if action == save_full_action:
            datetime = getDateTime()
            self.saveScreenShot(datetime, -1, -1, -1, -1)
            self.close()
        elif action == saveAs_full_action:
            datetime = getDateTime()
            filename = self.saveFileDialog(datetime)
            if filename:
                self.saveScreenShot(filename, -1, -1, -1, -1)
                self.close()
        elif action == clipboard_full_action:
            self.copyToClipboard(-1, -1, -1, -1)
        elif action == cancel_action:
            return
        elif action == exit_action:
            self.close()
            _globals.running = False
        
    def saveFileDialog(self, default):
        filename, ext = QFileDialog.getSaveFileName(
            self, "Save screenshot as..", default, filter=('.png'))
        if filename:
            return filename + ext

    def showShottyAboutWindow(self):
        self.shottyAboutWindow = ShottyAboutWindow()

    # Unused
    def closeEvent(self, e):

        # Unused
        '''
        close = QMessageBox.question(self,
                                        "Exit",
                                        "Are you sure you want to exit?",
                                        QMessageBox.Yes | QMessageBox.No)
        if close == QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()
        '''
    
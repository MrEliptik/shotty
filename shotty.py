from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QDesktopWidget, QMenu, QFileDialog, QAction
from PyQt5.QtCore import Qt, QObject, QTimer, QRect, QPoint, QDateTime, QDir
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QBrush, QColor, QPen, QIcon
import sys
import mss
import numpy as np
import signal
import cv2 as cv

import pyxhook
import time


def MouseMoveFilter(QObject):
    def eventFilter(self, obj, e):
        if e.type() == QtCore.QEvent.MouseMove:
                        # Hide the old tooltip, so that it can move
            QtGui.QToolTip.hideText()
            QtGui.QToolTip.showText(e.globalPos(), '%04f, %04f' %
                                    (e.globalX(), e.globalY()), obj)
            print(e.globalX(), e.globalY())

            return False
        # Call Base Class Method to Continue Normal Event Processing
        return super(MouseMoveFilter, self).eventFilter(obj, e)


class overlay(QWidget):
    def __init__(self, parent=None):
        super(overlay, self).__init__(parent)

        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)

        self.setPalette(palette)

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
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.green, Qt.DiagCrossPattern))
        painter.drawRect(self.x1, self.y1, self.x2-self.x1, self.y2-self.y1)
        painter.setPen(QPen(Qt.green, 1, Qt.DotLine))
        painter.drawLine(0, self.line_y, self.width(), self.line_y)
        painter.drawLine(self.line_x, 0, self.line_x, self.height())


class Shotty(QWidget):
    def __init__(self, im):
        super().__init__()
        print('Removing alpha..')
        self.im = im[:, :, :3].copy()
        self.initUI()
        self.setTextLabelPosition(0, 0)
        self.setMouseTracking(True)
        self.rect_x1 = 0
        self.rect_y1 = 0
        self.rect_x2 = 0
        self.rect_y2 = 0
        self.line_x = 0
        self.line_y = 0
        self.pressed = False

    def setMouseTracking(self, flag):
        def recursive_set(parent):
            for child in parent.findChildren(QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)
        QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def initUI(self):
        QApplication.setOverrideCursor(Qt.CrossCursor)
        # Create widget
        self.label = QLabel(self)
        self.l_mousePos = QLabel(self)
        self.l_mousePos.resize(200, 100)

        self.label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label.customContextMenuRequested.connect(self.showMenu)

        pixmap = QPixmap('white-round-md.png')
        # self.l_mousePos.setPixmap(pixmap)
        h, w, c = self.im.shape
        print('New shape: {},{},{}'.format(h, w, c))

        qImg = QImage(self.im, w, h, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.width(), pixmap.height())

        self.overlay = overlay(self.label)
        self.overlay.resize(pixmap.width(), pixmap.height())

        print("Overlay size: {}, {}".format(
            self.overlay.frameGeometry().width(), self.overlay.frameGeometry().height()))

        self.setWindowFlags(
            Qt.WindowCloseButtonHint | Qt.WindowType_Mask)
        monitor = QDesktopWidget().screenGeometry(0)
        self.move(monitor.left(), monitor.top())
        self.showFullScreen()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
            sys.exit()

    def mouseMoveEvent(self, e):
        self.line_x = e.x()
        self.line_y = e.y()

        zoom = self.im[e.y()-10:e.y()+10, e.x()-10:e.x()+10, :].copy()
        h, w, _ = zoom.shape
        # qZoom = QImage(zoom, w, h, QImage.Format_RGB888).rgbSwapped()
        # qPixZoom = QPixmap.fromImage(qZoom)
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
        self.overlay.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.pressed = True
            self.rect_x1 = e.x()
            self.rect_y1 = e.y()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.showMenu(e, 'cropped')
            self.pressed = False
            self.rect_x1 = 0
            self.rect_y1 = 0
            self.rect_x2 = 0
            self.rect_y2 = 0
            self.overlay.setCoords(
                self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
            self.overlay.update()
        '''
        if e.button() == Qt.RightButton:
            self.showMenu(e, 'fullscreen')
        '''

    def setTextLabelPosition(self, x, y):
        self.l_mousePos.move(x + 20, y)

    def saveScreenShot(self, filename, x1, y1, x2, y2):
        if x1 == -1:
            h, w, _ = self.im.shape
            qScreen = QImage(self.im.copy(), w, h,
                             QImage.Format_RGB888).rgbSwapped()
        else:
            crop_im = self.im[y1:y2, x1:x2, :].copy()
            h, w, _ = crop_im.shape
            qScreen = QImage(crop_im, w, h, QImage.Format_RGB888).rgbSwapped()
        qScreen.save(filename)

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

    def showMenu(self, e, type='fullscreen'):
        menu = QMenu()
        if type == 'cropped':

            save_crop_action = menu.addAction(
                QAction(QIcon("icons/save.png"), "Save region", self))
            saveAs_crop_action = menu.addAction(
                QAction(QIcon("icons/save-as.png"), "Save region as..", self))
            clipboard_crop_action = menu.addAction(
                QAction(QIcon("icons/copy-clipboard.png"), "Copy region to clipboard", self))
            cancel_action = menu.addAction(
                QAction(QIcon("icons/close-window.png"), "Cancel", self))
            exit_action = menu.addAction(
                QAction(QIcon("icons/exit.png"), "Exit", self))
            action = menu.exec_(self.mapToGlobal(QPoint(e.x(), e.y())))

            if action == save_crop_action:
                datetime = QDateTime.currentDateTime()
                self.saveScreenShot(datetime.toString(),
                                    self.rect_x1, self.rect_y1, e.x(), e.y())
                self.close()
                sys.exit()
            if action == saveAs_crop_action:
                datetime = QDateTime.currentDateTime()
                filename = self.saveFileDialog(datetime.toString())
                if filename:
                    self.saveScreenShot(
                        filename, self.rect_x1, self.rect_y1, e.x(), e.y())
                    self.close()
                    sys.exit()
            elif action == clipboard_crop_action:
                self.copyToClipboard(self.rect_x1, self.rect_y1, e.x(), e.y())
                self.close()
                sys.exit()

        elif type == 'fullscreen':
            save_full_action = menu.addAction(
                QAction(QIcon("icons/save.png"), "Save", self))
            saveAs_full_action = menu.addAction(
                QAction(QIcon("icons/save.png"), "Save as..", self))
            clipboard_full_action = menu.addAction(
                QAction(QIcon("icons/copy-clipboard.png"), "Copy to clipboard", self))
            cancel_action = menu.addAction(
                QAction(QIcon("icons/close-window.png"), "Cancel", self))
            exit_action = menu.addAction(
                QAction(QIcon("icons/exit.png"), "Exit", self))
            action = menu.exec_(self.mapToGlobal(QPoint(e.x(), e.y())))

            if action == save_full_action:
                datetime = QDateTime.currentDateTime()
                self.saveScreenShot(datetime.toString(), -1, -1, -1, -1)
                self.close()
                sys.exit()
            elif action == saveAs_full_action:
                datetime = QDateTime.currentDateTime()
                filename = self.saveFileDialog(datetime.toString())
                if filename:
                    self.saveScreenShot(filename, -1, -1, -1, -1)
                    self.close()
                    sys.exit()
            elif action == clipboard_full_action:
                self.copyToClipboard(-1, -1, -1, -1)
                self.close()
                sys.exit()
        if action == cancel_action:
            return
        elif action == exit_action:
            self.close()
            sys.exit()

    def saveFileDialog(self, default):
        '''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        dialog = QFileDialog()
        dialog.setFilter(dialog.filter() | QDir.Hidden)
        dialog.setDefaultSuffix('png')
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(['Image PNG (*.png)'])
        dialog.setDefaultSuffix('png')
        dialog.setOptions(options)
        # dialog.open()

        QFileDialog.getSaveFileName(
            dialog, "Save screenshot as..", default, "Image file (*.png)")
        '''

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save screenshot as..", default, "Image file (*.png)")
        if filename:
            return filename


def mask_image(imgdata, imgtype='jpg', size=64):
    """Return a ``QPixmap`` from *imgdata* masked with a smooth circle.

    *imgdata* are the raw image bytes, *imgtype* denotes the image type.

    The returned image will have a size of *size* × *size* pixels.

    """
    # Load image and convert to 32-bit ARGB (adds an alpha channel):
    # image = QImage.fromData(imgdata, imgtype)
    h, w, _ = imgdata.shape
    image = QImage(imgdata, w, h, QImage.Format_RGB888).rgbSwapped()
    image.convertToFormat(QImage.Format_ARGB32)

    # Crop image to a square:
    imgsize = min(image.width(), image.height())
    rect = QRect(
        (image.width() - imgsize) / 2,
        (image.height() - imgsize) / 2,
        imgsize,
        imgsize,
    )
    image = image.copy(rect)

    # Create the output image with the same dimensions and an alpha channel
    # and make it completely transparent:
    out_img = QImage(imgsize, imgsize, QImage.Format_ARGB32)
    out_img.fill(Qt.transparent)

    # Create a texture brush and paint a circle with the original image onto
    # the output image:
    brush = QBrush(image)        # Create texture brush
    painter = QPainter(out_img)  # Paint the output image
    painter.setBrush(brush)      # Use the image texture brush
    painter.setPen(Qt.NoPen)     # Don't draw an outline
    painter.setRenderHint(QPainter.Antialiasing, True)  # Use AA
    painter.drawEllipse(0, 0, imgsize, imgsize)  # Actually draw the circle
    painter.end()                # We are done (segfault if you forget this)

    # Convert the image to a pixmap and rescale it.  Take pixel ratio into
    # account to get a sharp image on retina displays:
    # pr = QWindow().devicePixelRatio()
    pm = QPixmap.fromImage(out_img)
    # pm.setDevicePixelRatio(pr)
    # size *= pr
    # pm = pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return pm

# This function is called every time a key is presssed
def kbevent(event):
    global running
    # print key info
    print(event)

    # If the ascii value matches spacebar, terminate the while loop
    if event.Ascii == 32:
        running = False

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create hookmanager
    hookman = pyxhook.HookManager()
    # Define our callback to fire when a key is pressed down
    hookman.KeyDown = kbevent
    # Hook the keyboard
    hookman.HookKeyboard()
    # Start our listener
    hookman.start()

    # Create a loop to keep the application running
    running = True
    while running:
        time.sleep(0.1)

    with mss.mss() as sct:
        # Get raw pixels from the screen, save it to a Numpy array
        im = np.array(sct.grab(sct.monitors[1]))

    app = QApplication(sys.argv)
    shotty = Shotty(im)

    sys.exit(app.exec_())

    # Close the listener when we are done
    hookman.cancel()

if __name__ == "__main__":
    main()

from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QDesktopWidget, QMenu, QFileDialog, QAction
from PyQt5.QtCore import Qt, QObject, QTimer, QRect, QPoint, QDateTime, QDir
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QBrush, QColor, QPen, QIcon, QFont
import numpy as np
import sys
from utils import mask_image, setMouseTracking

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
    def __init__(self, im, tray=None):
        super().__init__()
        print('Removing alpha..')
        self.im = im[:, :, :3].copy()
        self.initUI()
        self.setTextLabelPosition(0, 0)
        #setMouseTracking(self, True)
        self.rect_x1 = 0
        self.rect_y1 = 0
        self.rect_x2 = 0
        self.rect_y2 = 0
        self.line_x = 0
        self.line_y = 0
        self.pressed = False
        if tray.isSystemTrayAvailable():
            self.tray = tray
            self.showNotification('Shotty', 'Shotty is running in the background.')

    def initUI(self):
        QApplication.setOverrideCursor(Qt.CrossCursor)
        # Create widget
        self.l_imFullscreen = QLabel(self)
        self.l_mousePos = QLabel(self)
        self.l_dimensions = QLabel(self)

        font = QFont("Calibri", 15)
        self.l_dimensions.setFont(font)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showFullscreenshotMenu)

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
            sys.exit()

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
            self.showFullscreenshotMenu(e)

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

    def showCroppedMenu(self, e):
        menu = QMenu()
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
        elif action == saveAs_crop_action:
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
        elif action == cancel_action:
            return
        elif action == exit_action:
            self.close()
            sys.exit()

    def showFullscreenshotMenu(self, e):
        menu = QMenu()
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
        elif action == cancel_action:
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

    def showNotification(self, title, mess):
        self.tray.showMessage(title, mess)


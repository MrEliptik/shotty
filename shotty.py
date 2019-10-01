from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QDesktopWidget
from PyQt5.QtCore import Qt, QObject, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QBrush, QColor, QPen
import sys
import mss
import numpy as np
import signal
import cv2 as cv


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

    def setCoords(self, x1, y1, x2, y2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

    def paintEvent(self, event):     
        print('paint: ({},{}) ({},{})'.format(self.x1, self.y1, self.x2, self.y2))    
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.green, Qt.DiagCrossPattern))
        painter.drawRect(self.x1, self.y1, self.x2-self.x1, self.y2-self.y1)
        #painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
        #painter.setPen(QPen(Qt.NoPen))  

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
        self.pressed = False

    def initUI(self):
        QApplication.setOverrideCursor(Qt.CrossCursor)
        # Create widget
        self.label = QLabel(self)
        self.l_mousePos = QLabel(self)
        self.l_mousePos.resize(200, 100)


        pixmap = QPixmap('white-round-md.png')
        self.l_mousePos.setPixmap(pixmap)
        h, w, c = self.im.shape

        self.im = self.im[:, :, :3].copy()
        h, w, c = self.im.shape
        print('New shape: {},{},{}'.format(h, w, c))

        qImg = QImage(self.im, w, h, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.width(), pixmap.height())

        self.overlay = overlay(self.label)
        self.overlay.resize(pixmap.width(), pixmap.height())

        print("Overlay size: {}, {}".format(self.overlay.frameGeometry().width(), self.overlay.frameGeometry().height()))

        self.setWindowFlags(
            Qt.WindowCloseButtonHint | Qt.WindowType_Mask)
        monitor = QDesktopWidget().screenGeometry(1)
        self.move(monitor.left(), monitor.top())
        self.showFullScreen()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
            sys.exit()

    def mouseMoveEvent(self, e):
        #print(e.x(), e.y())
        self.setTextLabelPosition(e.x(), e.y())
        QWidget.mouseMoveEvent(self, e)
        print(self.pressed)
        if self.pressed:
            print('Event press coords: ({},{}) ({},{})'.format(self.rect_x1, self.rect_y1, e.x(), e.y()))
            self.overlay.setCoords(self.rect_x1, self.rect_y1, e.x(), e.y())
            self.overlay.update()

    def mousePressEvent(self, e):
        print('Press: {}'.format(e.pos()))
        self.pressed = True
        print('Press: {}'.format(self.pressed))
        self.rect_x1 = e.x()
        self.rect_y1 = e.y()

    def mouseReleaseEvent(self, e):
        print('Release: {}'.format(e.pos()))  
        self.pressed = False
        self.rect_x1 = 0
        self.rect_y1 = 0
        self.rect_x2 = 0
        self.rect_y2 = 0
        self.overlay.setCoords(self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
        self.overlay.update()

    def setTextLabelPosition (self, x, y):
        self.l_mousePos.move(x + 20, y)
        print(self.l_mousePos.x(), self.l_mousePos.y())
        #self.l_mousePos.setText('Mouse ( %d : %d )' % (self.l_mousePos.x(), self.l_mousePos.y()))


def mask_image(imgdata, imgtype='jpg', size=64):
    """Return a ``QPixmap`` from *imgdata* masked with a smooth circle.

    *imgdata* are the raw image bytes, *imgtype* denotes the image type.

    The returned image will have a size of *size* × *size* pixels.

    """
    # Load image and convert to 32-bit ARGB (adds an alpha channel):
    image = QImage.fromData(imgdata, imgtype)
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
    pr = QWindow().devicePixelRatio()
    pm = QPixmap.fromImage(out_img)
    pm.setDevicePixelRatio(pr)
    size *= pr
    pm = pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    return pm

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    with mss.mss() as sct:
        # Get raw pixels from the screen, save it to a Numpy array
        im = np.array(sct.grab(sct.monitors[1]))
    '''
    cv.imshow("screenshot", im)
    cv.waitKey(0)
    cv.destroyAllWindows()
    '''
    app = QApplication(sys.argv)
    shotty = Shotty(im)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QDesktopWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import sys
import mss
import numpy as np
import signal
import cv2 as cv

class Shotty(QWidget):
    def __init__(self, im):
        super().__init__()
        print('Removing alpha..')
        self.im = im[:,:,:3].copy()
        self.initUI()
        self.setMouseTracking(True)

    def initUI(self):
        QApplication.setOverrideCursor(Qt.CrossCursor)
        # Create widget
        self.label = QLabel(self)
        self.l_mousePos = QLabel(self)
        h, w, c = self.im.shape
        print(h, w ,c)

        
        self.im = self.im[:,:,:3].copy()
        h, w, c = self.im.shape
        print('New shape: {},{},{}'.format(h, w, c))

        
        print(self.im.strides[0])
        qImg = QImage(self.im, w, h, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImg)
        self.label.setPixmap(pixmap)
        self.label.resize(pixmap.width(), pixmap.height())

        self.label.keyPressEvent = app.quit()      

        self.label.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowType_Mask)
        monitor = QDesktopWidget().screenGeometry(1)
        self.label.move(monitor.left(), monitor.top())
        self.label.showFullScreen()
    
    def mouseMoveEvent(self, event):
        print(event.x(), event.y())
        self.l_mousePos.setText('(%dpx, %dpx)' % (event.x(), event.y()))


if __name__ == "__main__":
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
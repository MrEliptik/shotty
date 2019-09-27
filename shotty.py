from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QDesktopWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
import sys
import mss
import numpy as np
import signal
import cv2 as cv

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    with mss.mss() as sct:
        # Get raw pixels from the screen, save it to a Numpy array
        im = np.array(sct.grab(sct.monitors[1]))
    
    cv.imshow("screenshot", im)
    cv.waitKey(0)
    cv.destroyAllWindows()
    
    

    app = QApplication(sys.argv)

    # Create widget
    label = QLabel()
    label2 = QLabel()
    h, w, c = im.shape
    print(h, w ,c)

    print('Removing alpha..')
    im = im[:,:,:3].copy()
    h, w, c = im.shape
    print('New shape: {},{},{}'.format(h, w, c))

    
    print(im.strides[0])
    qImg = QImage(im, w, h, QImage.Format_RGB888).rgbSwapped()

    #qImg = QImage(np.require(im, np.uint8, 'C'), w, h, im.strides[0], QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(qImg)
    label.setPixmap(pixmap)
    label.resize(pixmap.width(), pixmap.height())

    label.keyPressEvent = app.quit()
     

    label.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowType_Mask)
    monitor = QDesktopWidget().screenGeometry(0)
    label.move(monitor.left(), monitor.top())
    label.showFullScreen()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLabel, QDesktopWidget, QMenu, QFileDialog, QAction
from PyQt5.QtCore import Qt, QObject, QTimer, QRect, QPoint, QDateTime, QDir, QDateTime
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter, QBrush, QColor, QPen, QIcon
import numpy as np
import os
import mss
from pynotifier import Notification
import platform

_platform = platform.system()

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

def screenshot():
    with mss.mss() as sct:
        # Get raw pixels from the screen, save it to a Numpy array
        im = np.array(sct.grab(sct.monitors[1]))
    return im

def getDateTime():
    d = QDateTime.currentDateTime()
    return d.toString("yyyy-MM-dd_hh-mm-ss")

def getExtension(filename):
    basename = os.path.basename(filename)
    filename, file_ext = os.path.splitext(basename)
    return file_ext

def showNotification(title, msg):
    if _platform == 'Windows':
        icon = 'icons/shotty.ico'
    else: 
        icon = 'icons/shotty.png'

    try:
        Notification(
            title=title,
            description=msg,
            icon_path=icon, # On Windows .ico is required, on Linux - .png
            duration=5,                              # Duration in seconds
            urgency=Notification.URGENCY_CRITICAL
        ).send()
    except Exception as e:
        print(e)
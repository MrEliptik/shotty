from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGridLayout
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtCore import Qt
import sys
import os; os.chdir(os.path.dirname(sys.argv[0]))

class ShottyAboutWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Shotty - Cross platform screenshot app'
        self.height = 300
        self.width = 250
        size = QApplication.primaryScreen().size()
        self.top = size.height() / 2
        self.left = size.width() / 2
        self.initUI()

    def initUI(self):
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setFixedSize(self.size())
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

        self.l_shottyIcon = QLabel()
        self.l_shottyIcon.setPixmap(QPixmap('icons/shotty.png').scaled(64, 64, Qt.KeepAspectRatio, Qt.FastTransformation))

        self.l_version = QLabel('v0.1')

        self.l_author = QLabel('Victor Meunier')
        self.l_email = QLabel('victormeunier.dev@gmail.com')

        self.l_github = QLabel()
        self.l_github.setText("<a href=\"https://github.com/MrEliptik/shotty\" />GitHub</a>")
        self.l_github.setOpenExternalLinks(True)

        self.l_credits =QLabel()

        #self.vbx = QVBoxLayout(self)
        #self.vbx.addWidget(self.l_github)
        self.grid = QGridLayout(self)
        self.grid.addWidget(self.l_shottyIcon, 0, 0)
        self.grid.addWidget(self.l_version, 0, 1)
        self.grid.addWidget(self.l_author, 1, 0)
        self.grid.addWidget(self.l_email, 1, 1)
        self.grid.addWidget(self.l_github, 2, 0)
        self.grid.addWidget(self.l_credits, 2, 1)

        self.show()

    def close(self):
        self.close

    def closeEvent(self, event):
        self.close

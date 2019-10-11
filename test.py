from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
from PyQt5 import Qt
import sys
app = Qt.QApplication(sys.argv)

systemtray_icon = Qt.QSystemTrayIcon(Qt.QIcon('icons/screenshot.png'), app)

if systemtray_icon.isSystemTrayAvailable():
    # Context Menu
    ctmenu = QMenu()
    actionshow = ctmenu.addAction("Show/Hide")
    actionshow.triggered.connect(
        lambda: self.hide() if self.isVisible() else self.show())
    actionquit = ctmenu.addAction("Quit")
    #actionquit.triggered.connect(app.close)

    systemtray_icon.setContextMenu(ctmenu)
    systemtray_icon.show()
    systemtray_icon.showMessage('Title', 'Content')
else:
    print("NOT SUPPORTED")

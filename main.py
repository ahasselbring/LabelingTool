#!/usr/bin/env python3

import sys

from PyQt5.QtWidgets import QApplication

from mainwindow import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('HULKs Image Labeling Tool')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

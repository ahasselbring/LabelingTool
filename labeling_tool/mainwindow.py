from PyQt5.QtCore import QFileInfo, QSettings, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QApplication, QFileDialog, QMainWindow, QMessageBox
from labeling_tool.imagedatabase import ImageDatabase, LabeledImage, LabelBase
from labeling_tool.imagedatabasewidget import ImageDatabaseWidget
from labeling_tool.labels import *
from labeling_tool.labelwidget import LabelWidget

from labeling_tool.imagewidget import ImageWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.__imageDatabase = ImageDatabase(self)
        self.__filePath = ''

        self.__settings = QSettings('HULKs', 'ImageLab', self)
        self.__recentFiles = self.__settings.value('RecentFiles', [])
        if not self.__recentFiles:
            self.__recentFiles = []
        self.__maxNumberOfRecentFiles = 8

        self.__fileNewAction = QAction('&New', self)
        self.__fileNewAction.setShortcuts(QKeySequence.New)

        self.__fileOpenAction = QAction('&Open....', self)
        self.__fileOpenAction.setShortcuts(QKeySequence.Open)

        self.__fileSaveAction = QAction('&Save', self)
        self.__fileSaveAction.setEnabled(False)
        self.__fileSaveAction.setShortcuts(QKeySequence.Save)

        self.__fileSaveAsAction = QAction('Save &As...', self)
        self.__fileSaveAsAction.setEnabled(False)
        self.__fileSaveAsAction.setShortcuts(QKeySequence.SaveAs)

        self.__fileCloseAction = QAction('&Close', self)
        self.__fileCloseAction.setEnabled(False)
        self.__fileCloseAction.setShortcuts(QKeySequence.Close)

        self.__fileExitAction = QAction('E&xit', self)
        self.__fileExitAction.setShortcuts(QKeySequence.Quit)

        self.__imageDatabaseWidget = ImageDatabaseWidget(self.__imageDatabase, self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.__imageDatabaseWidget)

        self.__labelWidget = LabelWidget(self.__imageDatabase, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.__labelWidget)

        self.__imageWidget = ImageWidget(self)
        self.setCentralWidget(self.__imageWidget)

        self.__fileMenu = self.menuBar().addMenu('&File')

        self.__labelMenu = self.menuBar().addMenu('&Labels')
        for cls in sorted(LabelBase.__subclasses__(), key=lambda _: _.name().lower()):
            act = self.__labelMenu.addAction(cls.icon(), cls.name())
            act.triggered.connect(lambda checked, cls=cls: self.__imageWidget.showLabelType(cls) if checked else self.__imageWidget.hideLabelType(cls))
            act.setCheckable(True)
            act.setChecked(True)

        self.__viewMenu = self.menuBar().addMenu('&View')
        self.__viewMenu.addAction(self.__imageDatabaseWidget.toggleViewAction())
        self.__viewMenu.addAction(self.__labelWidget.toggleViewAction())

        self.__helpMenu = self.menuBar().addMenu('&Help')
        aboutAction = self.__helpMenu.addAction('&About')
        aboutQtAction = self.__helpMenu.addAction('About &Qt')

        self.__fileNewAction.triggered.connect(self.newFile)
        self.__fileOpenAction.triggered.connect(self.open)
        self.__fileSaveAction.triggered.connect(self.save)
        self.__fileSaveAsAction.triggered.connect(lambda: self.save(saveAs=True))
        self.__fileExitAction.triggered.connect(self.close)

        self.__imageDatabase.preImageDatabaseChanged.connect(self.__imageDatabaseWidget.preChangeImageDatabase)
        self.__imageDatabase.imageDatabaseChanged.connect(self.__imageDatabaseWidget.changeImageDatabase)
        self.__imageDatabase.imageDatabaseChanged.connect(self.__imageWidget.changeImageDatabase)
        self.__imageDatabase.imageDatabaseChanged.connect(self.__labelWidget.changeImageDatabase)
        self.__imageDatabase.preImageAdded.connect(self.__imageDatabaseWidget.preAddImage)
        self.__imageDatabase.imageAdded.connect(self.__imageDatabaseWidget.addImage)
        self.__imageDatabase.preImageRemoved.connect(self.__imageDatabaseWidget.preRemoveImage)
        self.__imageDatabase.imageRemoved.connect(self.__imageDatabaseWidget.removeImage)
        self.__imageDatabase.imageRemoved.connect(self.__imageWidget.removeImage)
        self.__imageDatabase.imageRemoved.connect(self.__labelWidget.removeImage)
        self.__imageDatabase.labelAdded.connect(self.__imageWidget.addLabel)
        # self.__imageDatabase.labelAdded.connect(self.__labelWidget.addLabel)
        self.__imageDatabase.labelChanged.connect(self.__imageWidget.changeLabel)
        # self.__imageDatabase.labelChanged.connect(self.__labelWidget.changeLabel)
        self.__imageDatabase.labelRemoved.connect(self.__imageWidget.removeLabel)
        # self.__imageDatabase.labelRemoved.connect(self.__labelWidget.removeLabel)
        self.__imageDatabaseWidget.addImageClicked.connect(self.addImage)
        self.__imageDatabaseWidget.selectImageClicked.connect(self.__imageWidget.selectImage)
        self.__imageDatabaseWidget.selectImageClicked.connect(self.__labelWidget.selectImage)
        self.__imageDatabaseWidget.removeImageClicked.connect(self.__imageDatabase.removeImage)
        self.__imageWidget.mousePressed.connect(self.__labelWidget.addPoint)
        self.__labelWidget.labelCreated.connect(self.__imageDatabase.addLabel)
        self.__labelWidget.labelEdited.connect(self.__imageDatabase.changeLabel)
        self.__labelWidget.labelDeleted.connect(self.__imageDatabase.removeLabel)

        """
        self.statusBar().clearMessage()
        self.__imageWidget.mouseMoved.connect(lambda point: self.statusBar().showMessage('(' + str(point.x()) + ',' + str(point.y()) + ')')) # TODO
        """

        self.__fileMenu.aboutToShow.connect(self.updateFileMenu)

        aboutAction.triggered.connect(self.about)
        aboutQtAction.triggered.connect(QApplication.instance().aboutQt)

        self.setWindowTitle('HULKs Image Labeling Tool')
        self.setUnifiedTitleAndToolBarOnMac(True)

    def about(self):
        QMessageBox.about(self, 'About', 'ImageLab 11 Beta<br />A tool for labeling images.')

    def newFile(self):
        if not self.closeFile():
            return

        self.__imageDatabase.createNew()
        self.__filePath = ''

        self.__fileSaveAction.setEnabled(True)
        self.__fileSaveAsAction.setEnabled(True)
        self.__fileCloseAction.setEnabled(True)

    def open(self):
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', self.__settings.value('OpenDirectory', ''))
        if fileName == '':
            return
        self.__settings.setValue('OpenDirectory', QFileInfo(fileName).dir().path())

        self.openFile(fileName)

    def save(self, saveAs = False):
        if not self.__imageDatabase.modified():
            return True

        if self.__filePath == '' or saveAs:
            fileName, _ = QFileDialog.getSaveFileName(self, 'Save File', self.__settings.value('OpenDirectory', ''))
            if fileName == '':
                return False

            fileInfo = QFileInfo(fileName)
            self.__settings.setValue('OpenDirectory', fileInfo.dir().path())

            self.__filePath = fileInfo.absoluteDir().canonicalPath() + '/' + fileInfo.fileName()

        self.saveFile(self.__filePath)

    def openFile(self, fileName):
        if not self.closeFile():
            return

        fileInfo = QFileInfo(fileName)
        filePath = fileInfo.absoluteDir().canonicalPath() + '/' + fileInfo.fileName()

        while self.__recentFiles.count(filePath) > 0:
            self.__recentFiles.remove(filePath)

        if not fileInfo.exists():
            self.__settings.setValue('RecentFiles', self.__recentFiles)
            return

        self.__recentFiles.insert(0, filePath)
        del self.__recentFiles[self.__maxNumberOfRecentFiles:]
        self.__settings.setValue('RecentFiles', self.__recentFiles)

        self.__imageDatabase.readFromFile(filePath)
        self.__filePath = filePath

        self.__fileSaveAction.setEnabled(True)
        self.__fileSaveAsAction.setEnabled(True)
        self.__fileCloseAction.setEnabled(True)

    def saveFile(self, fileName):
        fileInfo = QFileInfo(fileName)
        filePath = fileInfo.absoluteDir().canonicalPath() + '/' + fileInfo.fileName()

        while self.__recentFiles.count(filePath) > 0:
            self.__recentFiles.remove(filePath)

        self.__recentFiles.insert(0, filePath)
        del self.__recentFiles[self.__maxNumberOfRecentFiles:]
        self.__settings.setValue('RecentFiles', self.__recentFiles)

        self.__imageDatabase.writeToFile(filePath)
        self.__filePath = filePath


    def closeFile(self):
        if self.__imageDatabase.modified():
            reply = QMessageBox.question(self, 'Unsaved changes', 'Your database has unsaved changes. Do you want to save it?', QMessageBox.Yes | QMessageBox.No | QMessageBox.Abort, QMessageBox.Abort)
            if reply == QMessageBox.Yes:
                self.save()
            elif reply == QMessageBox.No:
                pass
            else:
                return False

        self.__fileSaveAction.setEnabled(False)
        self.__fileSaveAsAction.setEnabled(False)
        self.__fileCloseAction.setEnabled(False)

        self.__imageDatabase.clear()

        return True

    def updateFileMenu(self):
        self.__fileMenu.clear()
        self.__fileMenu.addAction(self.__fileNewAction)
        self.__fileMenu.addAction(self.__fileOpenAction)
        self.__fileMenu.addSeparator()
        self.__fileMenu.addAction(self.__fileSaveAction)
        self.__fileMenu.addAction(self.__fileSaveAsAction)

        if self.__recentFiles:
            self.__fileMenu.addSeparator()
            shortcut = ord('1')
            for f in self.__recentFiles:
                action = self.__fileMenu.addAction('&' + chr(shortcut) + ' ' + QFileInfo(f).fileName())
                action.triggered.connect(lambda unused, f=f: self.openFile(f))
                shortcut = shortcut + 1

        self.__fileMenu.addSeparator()
        self.__fileMenu.addAction(self.__fileCloseAction)
        self.__fileMenu.addAction(self.__fileExitAction)

    def closeEvent(self, event):
        if not self.closeFile():
            event.ignore()
            return
        super().closeEvent(event)

    def addImage(self):
        if not self.__imageDatabase.exists():
            return

        fileName, _ = QFileDialog.getOpenFileName(self, 'Add Image', self.__settings.value('ImageDirectory', ''))
        if fileName == '':
            return
        fileInfo = QFileInfo(fileName)
        filePath = fileInfo.absoluteDir().canonicalPath() + '/' + fileInfo.fileName()
        self.__settings.setValue('ImageDirectory', fileInfo.dir().path())

        self.__imageDatabase.addImage(LabeledImage(filePath))

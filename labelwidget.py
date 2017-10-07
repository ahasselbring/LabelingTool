from PyQt5.QtCore import pyqtSignal, QAbstractItemModel, QModelIndex, Qt, QVariant
from PyQt5.QtWidgets import QAction, QDockWidget, QMenu, QTreeView

from imagedatabase import ImageDatabase, LabelBase, LabeledImage

from labels import * # TODO

class ImageDatabaseModel(QAbstractItemModel):
    def __init__(self, imageDatabase, parent=None):
        super().__init__(parent)

        self.__imageDatabase = imageDatabase

    def columnCount(self, parent = QModelIndex()):
        return 0

    def data(self, index, role = Qt.DisplayRole):
        return QVariant()

    def index(self, row, column, parent = QModelIndex()):
        return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def rowCount(self, parent = QModelIndex()):
        return 0

class LabelWidget(QDockWidget):
    labelCreated = pyqtSignal(LabeledImage, LabelBase)

    def __init__(self, imageDatabase, parent=None):
        super().__init__(parent)

        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWindowTitle('Labeling')

        self.__treeView = QTreeView()
        self.__treeView.customContextMenuRequested.connect(self.__prepareMenu)
        self.__treeView.setAlternatingRowColors(True)
        self.__treeView.setContextMenuPolicy(Qt.NoContextMenu)

        self.__imageDatabase = imageDatabase
        self.__treeModel = ImageDatabaseModel(imageDatabase)
        self.__treeView.setModel(self.__treeModel)
        self.__selectedImage = None

        self.__currentCls = LineLabel # TODO
        self.__currentPoints = []

        self.setWidget(self.__treeView)

    def preChangeImageDatabase(self):
        self.__selectedImage = None
        self.__treeModel.beginResetModel()

    def changeImageDatabase(self):
        self.__treeModel.endResetModel()
        self.__treeView.setContextMenuPolicy(Qt.CustomContextMenu if self.__imageDatabase.exists() else Qt.NoContextMenu)

    def selectImage(self, image):
        if image == self.__selectedImage:
            return
        self.__treeModel.beginResetModel()
        self.__selectedImage = image
        self.__treeModel.endResetModel()

    def addPoint(self, point):
        if not self.__selectedImage:
            return
        self.__currentPoints.append(point)
        if len(self.__currentPoints) == self.__currentCls.requiredNumberOfClicks():
            self.labelCreated.emit(self.__selectedImage, self.__currentCls.fromClicks(self.__currentPoints))
            self.__currentPoints.clear()

    def __prepareMenu(self, pos):
        menu = QMenu()

        # TODO
        index = self.__treeView.indexAt(pos)
        if index.isValid():
            menu.addSeparator()
            pass

        menu.exec_(self.__treeView.mapToGlobal(pos))
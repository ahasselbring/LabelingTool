from PyQt5.QtCore import pyqtSignal, QAbstractListModel, QModelIndex, Qt, QVariant
from PyQt5.QtWidgets import QAction, QDockWidget, QMenu, QListView

from labeling_tool.imagedatabase import LabeledImage


class ImageDatabaseModel(QAbstractListModel):
    def __init__(self, imageDatabase, parent=None):
        super().__init__(parent)

        self.__imageDatabase = imageDatabase

    def data(self, index, role = Qt.DisplayRole):
        if self.__imageDatabase.exists() and index.isValid() and role == Qt.DisplayRole:
            return QVariant(self.__imageDatabase.labeledImages[index.row()].imageFile)
        else:
            return QVariant()

    def rowCount(self, parent = QModelIndex()):
        return len(self.__imageDatabase.labeledImages) if self.__imageDatabase.exists() else 0

class ImageDatabaseWidget(QDockWidget):
    addImageClicked = pyqtSignal()
    selectImageClicked = pyqtSignal(LabeledImage)
    removeImageClicked = pyqtSignal(LabeledImage)

    def __init__(self, imageDatabase, parent=None):
        super().__init__(parent)

        self.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.setWindowTitle('Image Database')

        self.__listView = QListView()
        self.__listView.customContextMenuRequested.connect(self.__prepareMenu)
        self.__listView.activated.connect(lambda index: self.selectImageClicked.emit(self.__imageDatabase.labeledImages[index.row()]))
        self.__listView.setAlternatingRowColors(True)
        self.__listView.setContextMenuPolicy(Qt.NoContextMenu)

        self.__imageDatabase = imageDatabase
        self.__listModel = ImageDatabaseModel(imageDatabase)
        self.__listView.setModel(self.__listModel)

        self.setWidget(self.__listView)

    def preChangeImageDatabase(self):
        self.__listModel.beginResetModel()

    def changeImageDatabase(self):
        self.__listModel.endResetModel()
        self.__listView.setContextMenuPolicy(Qt.CustomContextMenu if self.__imageDatabase.exists() else Qt.NoContextMenu)

    def preAddImage(self, image):
        index = len(self.__imageDatabase.labeledImages)
        self.__listModel.beginInsertRows(QModelIndex(), index, index)

    def addImage(self, image):
        self.__listModel.endInsertRows()

    def preRemoveImage(self, image):
        index = self.__imageDatabase.labeledImages.index(image)
        self.__listModel.beginRemoveRows(QModelIndex(), index, index)

    def removeImage(self, image):
        self.__listModel.endRemoveRows()

    def __prepareMenu(self, pos):
        menu = QMenu()

        addFileAction = QAction('Add Image', self)
        addFileAction.triggered.connect(lambda: self.addImageClicked.emit())
        menu.addAction(addFileAction)

        index = self.__listView.indexAt(pos)
        if index.isValid():
            menu.addSeparator()

            removeFileAction = QAction('Remove Image', self)
            removeFileAction.triggered.connect(lambda: self.removeImageClicked.emit(self.__imageDatabase.labeledImages[index.row()]))
            menu.addAction(removeFileAction)

        menu.exec_(self.__listView.mapToGlobal(pos))

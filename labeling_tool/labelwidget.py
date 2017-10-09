from ast import literal_eval
from enum import Enum
from PyQt5.QtCore import pyqtSignal, QAbstractItemModel, QModelIndex, Qt, QVariant
from PyQt5.QtWidgets import QAction, QComboBox, QDockWidget, QLineEdit, QMenu, QStyledItemDelegate, QTabBar, QTreeView, QVBoxLayout, QWidget
import weakref
from labeling_tool.labels import *

from labeling_tool.imagedatabase import LabelBase, LabeledImage

class LabelProperty:
    def __init__(self, name, obj=None, parent=None):
        self.__name = name
        if obj is not None:
            self.__ref = weakref.ref(obj)
        self.__parent = parent

    def name(self):
        return self.__name

    def property(self):
        return getattr(self.__ref(), self.__name)

    def setProperty(self, val):
        setattr(self.__ref(), self.__name, val)

    def parent(self):
        return self.__parent

class LabelDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        item = index.internalPointer()
        var = type(item.property())
        if issubclass(var, Enum):
            return QComboBox(parent)
        else:
            return QLineEdit(parent)

    def setEditorData(self, editor, index):
        self.blockSignals(True)
        item = index.internalPointer()
        var = type(item.property())
        if issubclass(var, Enum):
            editor.addItems(var.__members__.keys())
            editor.setCurrentIndex(item.property().value)
        else:
            editor.setText(str(index.internalPointer().property()))
        self.blockSignals(False)

    def setModelData(self, editor, model, index):
        item = index.internalPointer()
        var = type(item.property())
        if issubclass(var, Enum):
            model.setData(index, var[editor.currentText()], Qt.EditRole)
        else:
            model.setData(index, literal_eval(editor.text()), Qt.EditRole)

class LabelModel(QAbstractItemModel):
    labelEdited = pyqtSignal(LabeledImage, LabelBase)

    def __init__(self, labelType, parent=None):
        super().__init__(parent)

        self.__labelType = labelType
        self.__items = set()
        self.selectedImage = None

    def columnCount(self, parent = QModelIndex()):
        return 2

    def rowCount(self, parent = QModelIndex()):
        if parent.column() > 0 or not self.selectedImage or not self.__labelType in self.selectedImage.labels:
            return 0

        if not parent.isValid():
            return len(self.selectedImage.labels[self.__labelType])
        elif isinstance(parent.internalPointer(), LabelBase):
            return len(vars(parent.internalPointer()))
        else:
            return 0

    def index(self, row, column, parent = QModelIndex()):
        if not self.hasIndex(row, column, parent) or not self.selectedImage:
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.selectedImage.labels[self.__labelType]
            return self.createIndex(row, column, parentItem[row])
        else:
            parentItem = parent.internalPointer()
            p = LabelProperty(list(vars(parentItem).keys())[row], parentItem, parentItem)
            # TODO TODO TODO This is necessary because p becomes garbage-collected otherwise
            self.__items.add(p)
            return self.createIndex(row, column, p)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        if isinstance(childItem, LabelBase):
            return QModelIndex()
        else:
            parentItem = childItem.parent()
            return self.createIndex(self.selectedImage.labels[self.__labelType].index(parentItem), 0, parentItem)

    def data(self, index, role = Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        item = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if isinstance(item, LabelBase):
                return str(index.row()) if index.column() == 0 else QVariant()
            elif index.column() == 1:
                return item.name()
            else:
                if isinstance(item.property(), Enum):
                    return item.property().name
                else:
                    return str(item.property())

        return QVariant()

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return 'Name' if section == 0 else 'Value'
        return QVariant()

    def flags(self, index):
        item = index.internalPointer()
        if isinstance(item, LabelBase):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif index.column() == 0:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role = Qt.EditRole):
        if role != Qt.EditRole:
            return False
        index.internalPointer().setProperty(value)
        self.labelEdited.emit(self.selectedImage, index.internalPointer().parent())
        return True

class LabelWidget(QDockWidget):
    remainingClicksChanged = pyqtSignal(int)
    labelCreated = pyqtSignal(LabeledImage, LabelBase)
    labelEdited = pyqtSignal(LabeledImage, LabelBase)
    labelDeleted = pyqtSignal(LabeledImage, LabelBase)

    def __init__(self, imageDatabase, parent=None):
        super().__init__(parent)

        self.setAllowedAreas(Qt.RightDockWidgetArea)
        self.setWindowTitle('Labeling')

        self.__imageDatabase = imageDatabase
        self.__selectedImage = None

        self.__currentCls = None
        self.__currentPoints = []

        self.__treeModels = []

        proxy = QWidget(self)

        self.__mainLayout = QVBoxLayout(proxy)
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)

        self.__typeToIndex = {}
        self.__tabBar = QTabBar(self)
        for cls in sorted(LabelBase.__subclasses__(), key=lambda _: _.name().lower()):
            self.__typeToIndex[cls] = self.__tabBar.count()
            self.__tabBar.addTab(cls.icon(), cls.name())
            self.__tabBar.setTabData(self.__tabBar.count() - 1, cls)
            model = LabelModel(cls, self)
            model.labelEdited.connect(self.labelEdited)
            self.__treeModels.append(model)
        self.__tabBar.currentChanged.connect(self.__changeTab)

        self.__treeView = QTreeView(self)
        self.__treeView.setModel(self.__treeModels[0])
        self.__treeView.setItemDelegate(LabelDelegate(self))
        self.__treeView.setAlternatingRowColors(True)
        self.__treeView.setContextMenuPolicy(Qt.NoContextMenu)
        self.__treeView.customContextMenuRequested.connect(self.__prepareMenu)

        self.__mainLayout.addWidget(self.__tabBar)
        self.__mainLayout.addWidget(self.__treeView)

        proxy.setLayout(self.__mainLayout)
        self.setWidget(proxy)

    def changeImageDatabase(self):
        for model in self.__treeModels:
            model.beginResetModel()
        self.__selectedImage = None
        for model in self.__treeModels:
            model.selectedImage = None
            model.endResetModel()
        self.__treeView.setContextMenuPolicy(Qt.CustomContextMenu if self.__imageDatabase.exists() else Qt.NoContextMenu)

    def removeImage(self, image):
        if image != self.__selectedImage:
            return
        for model in self.__treeModels:
            model.beginResetModel()
        self.__selectedImage = None
        for model in self.__treeModels:
            model.selectedImage = None
            model.endResetModel()

    def selectImage(self, image):
        if image == self.__selectedImage:
            return
        for model in self.__treeModels:
            model.beginResetModel()
        self.__selectedImage = image
        for model in self.__treeModels:
            model.selectedImage = image
            model.endResetModel()

    def preAddLabel(self, image, label):
        if image != self.__selectedImage:
            return
        index = len(self.__selectedImage.labels[type(label)]) if type(label) in self.__selectedImage.labels else 0
        self.__treeModels[self.__typeToIndex[type(label)]].beginInsertRows(QModelIndex(), index, index)

    def addLabel(self, image, label):
        if image != self.__selectedImage:
            return
        self.__treeModels[self.__typeToIndex[type(label)]].endInsertRows()

    def changeLabel(self, image, label):
        if image != self.__selectedImage:
            return
        index = self.__treeModels[self.__typeToIndex[type(label)]].index(self.__selectedImage.labels[type(label)].index(label), 0, QModelIndex())
        self.__treeModels[self.__typeToIndex[type(label)]].dataChanged.emit(index, index)

    def preRemoveLabel(self, image, label):
        if image != self.__selectedImage:
            return
        index = self.__selectedImage.labels[type(label)].index(label)
        self.__treeModels[self.__typeToIndex[type(label)]].beginRemoveRows(QModelIndex(), index, index)

    def removeLabel(self, image, label):
        if image != self.__selectedImage:
            return
        self.__treeModels[self.__typeToIndex[type(label)]].endRemoveRows()

    def addPoint(self, point):
        if not self.__selectedImage or not self.__currentCls:
            return
        self.__currentPoints.append(point)
        if len(self.__currentPoints) == self.__currentCls.requiredNumberOfClicks():
            self.labelCreated.emit(self.__selectedImage, self.__currentCls.fromClicks(self.__currentPoints))
            self.__currentPoints.clear()
            self.__currentCls = None
            self.remainingClicksChanged.emit(0)
        else:
            self.remainingClicksChanged.emit(self.__currentCls.requiredNumberOfClicks() - len(self.__currentPoints))

    def __prepareMenu(self, pos):
        menu = QMenu(self)

        addLabelAction = QAction('Add Label', self)
        addLabelAction.triggered.connect(self.__startLabel)
        menu.addAction(addLabelAction)

        index = self.__treeView.indexAt(pos)
        if index.isValid():
            menu.addSeparator()

            removeLabelAction = QAction('Remove Label', self)
            removeLabelAction.triggered.connect(lambda: self.labelDeleted.emit(self.__selectedImage, index.internalPointer() if isinstance(index.internalPointer(), LabelBase) else index.internalPointer().parent()))
            menu.addAction(removeLabelAction)

        menu.exec_(self.__treeView.mapToGlobal(pos))

    def __startLabel(self):
        if self.__tabBar.currentIndex() < 0:
            return

        self.__currentPoints.clear()
        self.__currentCls = self.__tabBar.tabData(self.__tabBar.currentIndex())
        self.remainingClicksChanged.emit(self.__currentCls.requiredNumberOfClicks())

    def __changeTab(self, index):
        index = self.__tabBar.currentIndex()

        self.__treeView.setModel(self.__treeModels[index] if index >= 0 else None)

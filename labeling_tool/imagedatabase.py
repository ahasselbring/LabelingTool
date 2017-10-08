from PyQt5.QtCore import pyqtSignal, QObject
import pickle
import json

class LabeledImage:
    def __init__(self, imageFile = ''):
        self.imageFile = imageFile
        self.labels = {}

class LabelBase:
    def draw(self, painter):
        raise NotImplementedError

    @staticmethod
    def requiredNumberOfClicks():
        raise NotImplementedError

def encodeImageDatabase(obj):
    def translateName(name):
        components = name.split()
        return components[0].title() + ''.join(_.title() for _ in components[1:])
    if isinstance(obj, LabeledImage):
        return dict({ 'fileName':  obj.imageFile }, **{ translateName(cls.name()): labels for cls, labels in obj.labels.items() })
    elif isinstance(obj, LabelBase):
        return obj.__dict__
    raise TypeError('Cannot serialize ', repr(obj))

class ImageDatabase(QObject):
    preImageDatabaseChanged = pyqtSignal()
    imageDatabaseChanged = pyqtSignal()
    preImageAdded = pyqtSignal(LabeledImage)
    imageAdded = pyqtSignal(LabeledImage)
    preImageRemoved = pyqtSignal(LabeledImage)
    imageRemoved = pyqtSignal(LabeledImage)
    preLabelAdded = pyqtSignal(LabeledImage, LabelBase)
    labelAdded = pyqtSignal(LabeledImage, LabelBase)
    labelChanged = pyqtSignal(LabeledImage, LabelBase)
    preLabelRemoved = pyqtSignal(LabeledImage, LabelBase)
    labelRemoved = pyqtSignal(LabeledImage, LabelBase)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__modified = False
        self.__exists = False
        self.labeledImages = []

    def modified(self):
        return self.__modified

    def exists(self):
        return self.__exists

    def clear(self):
        self.preImageDatabaseChanged.emit()
        self.__modified = False
        self.__exists = False
        self.labeledImages = []
        self.imageDatabaseChanged.emit()

    def createNew(self):
        self.preImageDatabaseChanged.emit()
        self.__modified = False
        self.__exists = True
        self.labeledImages = []
        self.imageDatabaseChanged.emit()

    def readFromFile(self, fileName):
        self.preImageDatabaseChanged.emit()
        with open(fileName, 'rb') as f:
            self.labeledImages = pickle.load(f)
        self.__modified = False
        self.__exists = True
        self.imageDatabaseChanged.emit()

    def writeToFile(self, fileName):
        if not self.__exists:
            return
        with open(fileName, 'wb') as f:
            pickle.dump(self.labeledImages, f)
        self.__modified = False

    def exportToJson(self, fileName):
        if not self.__exists:
            return
        with open(fileName, 'w') as f:
            json.dump({'imageDatabase': self.labeledImages}, f, default=encodeImageDatabase)

    def addImage(self, labeledImage):
        if not self.__exists:
            return

        # TODO: make sure that the same image is not already in the database
        for f in self.labeledImages:
            # TODO: make sure that absolute paths are compared
            if f.imageFile == labeledImage.imageFile:
                return

        self.preImageAdded.emit(labeledImage)
        self.labeledImages.append(labeledImage)
        self.__modified = True
        self.imageAdded.emit(labeledImage)

    def removeImage(self, labeledImage):
        if not self.__exists:
            return

        # TODO: make sure that the image is indeed in the database

        self.preImageRemoved.emit(labeledImage)
        self.labeledImages.remove(labeledImage)
        self.__modified = True
        self.imageRemoved.emit(labeledImage)

    def addLabel(self, labeledImage, label):
        if not self.__exists:
            return

        if not type(label) in labeledImage.labels:
            labeledImage.labels[type(label)] = []

        self.preLabelAdded.emit(labeledImage, label)
        labeledImage.labels[type(label)].append(label)
        self.__modified = True
        self.labelAdded.emit(labeledImage, label)

    def changeLabel(self, labeledImage, label):
        if not self.__exists:
            return

        # Well, I think it has already been changed.

        self.__modified = True
        self.labelChanged.emit(labeledImage, label)

    def removeLabel(self, labeledImage, label):
        if not self.__exists:
            return

        if not type(label) in labeledImage.labels:
            return

        self.preLabelRemoved.emit(labeledImage, label)
        labeledImage.labels[type(label)].remove(label)
        self.__modified = True
        self.labelRemoved.emit(labeledImage, label)

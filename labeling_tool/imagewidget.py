from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QRect
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtWidgets import QWidget

class ImageWidget(QWidget):
    mousePressed = pyqtSignal(QPoint)
    mouseMoved = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__hiddenLabelTypes = set()
        self.__image = QImage()
        self.__selectedImage = None

        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if event.button() != 1 or self.__image.isNull() or not self.__selectedImage:
            return

        origin = QPoint(self.width() / 2 - self.__image.width() / 2, self.height() / 2 - self.__image.height() / 2)
        relPos = event.pos() - origin
        if relPos.x() < 0 or relPos.y() < 0 or relPos.x() >= self.__image.width() or relPos.y() >= self.__image.height():
            return

        self.mousePressed.emit(relPos)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        if self.__image.isNull() or not self.__selectedImage:
            return

        origin = QPoint(self.width() / 2 - self.__image.width() / 2, self.height() / 2 - self.__image.height() / 2)
        relPos = event.pos() - origin

        self.mouseMoved.emit(relPos)

    def paintEvent(self, event):
        if self.__image.isNull() or not self.__selectedImage:
            return

        origin = QPoint(self.width() / 2 - self.__image.width() / 2, self.height() / 2 - self.__image.height() / 2)

        painter = QPainter(self)
        painter.translate(origin)
        painter.drawImage(QPoint(), self.__image)

        for labelType in self.__selectedImage.labels:
            if labelType in self.__hiddenLabelTypes:
                continue
            for label in self.__selectedImage.labels[labelType]:
                    label.draw(painter)

    def changeImageDatabase(self):
        self.__image = QImage()
        self.__selectedImage = None
        self.update()

    def hideLabelType(self, labelType):
        self.__hiddenLabelTypes.add(labelType)
        self.update()

    def showLabelType(self, labelType):
        self.__hiddenLabelTypes.remove(labelType)
        self.update()

    def removeImage(self, image):
        if image != self.__selectedImage:
            return
        self.__image = QImage()
        self.__selectedImage = None
        self.update()

    def addLabel(self, image, label):
        if image != self.__selectedImage:
            return
        self.update()

    def changeLabel(self, image, label):
        if image != self.__selectedImage:
            return
        self.update()

    def removeLabel(self, image, label):
        if image != self.__selectedImage:
            return
        self.update()

    def selectImage(self, image):
        if image == self.__selectedImage:
            return
        self.__image.load(image.imageFile)
        self.__selectedImage = image
        self.update()

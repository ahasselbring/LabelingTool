import math
from enum import Enum

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPen

import labeling_tool.resources_rc

from labeling_tool.imagedatabase import LabelBase


class BallLabel(LabelBase):
    def __init__(self, center, radius, blurred=False):
        super().__init__()
        self.center = center
        self.radius = radius
        self.blurred = blurred

    def draw(self, painter):
        painter.setPen(QPen(Qt.red, 3 if self.blurred else 1))
        painter.drawEllipse(self.center[0] - self.radius, self.center[1] - self.radius, 2 * self.radius, 2 * self.radius)

    @staticmethod
    def name():
        return 'Balls'

    @staticmethod
    def icon():
        return QIcon(':/Icons/ball.png')

    @staticmethod
    def requiredNumberOfClicks():
        return 2

    @classmethod
    def fromClicks(cls, points):
        assert(len(points) == 2)
        center = (points[0].x(), points[0].y())
        dxdy = (points[0] - points[1])
        radius = int(math.sqrt(dxdy.x() * dxdy.x() + dxdy.y() * dxdy.y()))
        return cls(center, radius)

class LineLabel(LabelBase):
    def __init__(self, start, end):
        super().__init__()
        self.start = start
        self.end = end

    def draw(self, painter):
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(self.start[0], self.start[1], self.end[0], self.end[1])

    @staticmethod
    def name():
        return 'Lines'

    @staticmethod
    def icon():
        return QIcon(':/Icons/line.png')

    @staticmethod
    def requiredNumberOfClicks():
        return 2

    @classmethod
    def fromClicks(cls, points):
        assert(len(points) == 2)
        return cls((points[0].x(), points[0].y()), (points[1].x(), points[1].y()))

class GoalPostLabel(LabelBase):
    def __init__(self, base):
        super().__init__()
        self.base = base

    def draw(self, painter):
        painter.setPen(QPen(Qt.green, 1))
        painter.drawEllipse(self.base[0] - 10, self.base[1] - 10, 20, 20)

    @staticmethod
    def name():
        return 'Goal Posts'

    @staticmethod
    def icon():
        return QIcon(':/Icons/goalPost.png')

    @staticmethod
    def requiredNumberOfClicks():
        return 1

    @classmethod
    def fromClicks(cls, points):
        assert(len(points) == 1)
        return cls((points[0].x(), points[0].y()))

class TeamColor(Enum):
    NONE = 0
    BLUE = 1
    RED = 2
    YELLOW = 3
    BLACK = 4
    WHITE = 5
    GREEN = 6
    ORANGE = 7
    PURPLE = 8
    BROWN = 9
    GRAY = 10

class RobotLabel(LabelBase):
    def __init__(self, topLeft, bottomRight, teamColor=TeamColor.NONE):
        super().__init__()
        self.topLeft = topLeft
        self.bottomRight = bottomRight
        self.teamColor = teamColor

    def draw(self, painter):
        teamColorToQtColor = {
            TeamColor.NONE: Qt.darkGray,
            TeamColor.BLUE: Qt.blue,
            TeamColor.RED: Qt.red,
            TeamColor.YELLOW: Qt.yellow,
            TeamColor.BLACK: Qt.black,
            TeamColor.WHITE: Qt.white,
            TeamColor.GREEN: Qt.green,
            TeamColor.ORANGE: Qt.darkYellow,
            TeamColor.PURPLE: Qt.darkMagenta,
            TeamColor.BROWN: Qt.darkRed,
            TeamColor.GRAY: Qt.gray
        }
        painter.setPen(QPen(teamColorToQtColor[self.teamColor], 2))
        painter.drawRect(self.topLeft[0], self.topLeft[1], self.bottomRight[0] - self.topLeft[0], self.bottomRight[1] - self.topLeft[1])

    @staticmethod
    def name():
        return 'Robots'

    @staticmethod
    def icon():
        return QIcon(':/Icons/robot.png')

    @staticmethod
    def requiredNumberOfClicks():
        return 2

    @classmethod
    def fromClicks(cls, points):
        assert(len(points) == 2)
        # TODO: This should also work when the user clicked in the wrong order
        return cls((points[0].x(), points[0].y()), (points[1].x(), points[1].y()))

class PenaltySpotLabel(LabelBase):
    def __init__(self, spot):
        super().__init__()

        self.spot = spot

    def draw(self, painter):
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(self.spot[0] - 10, self.spot[1], self.spot[0] + 10, self.spot[1])
        painter.drawLine(self.spot[0], self.spot[1] - 10, self.spot[0], self.spot[1] + 10)

    @staticmethod
    def name():
        return 'Penalty Spots'

    @staticmethod
    def icon():
        return QIcon(':/Icons/penaltySpot.png')

    @staticmethod
    def requiredNumberOfClicks():
        return 1

    @classmethod
    def fromClicks(cls, points):
        assert(len(points) == 1)
        return cls((points[0].x(), points[0].y()))

# TODO: center circle, intersections, field border etc.

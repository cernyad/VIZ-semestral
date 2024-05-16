# Copyright (c) 2021 Ladislav Čmolík
#
# Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is 
# hereby granted.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE 
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE 
# FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS 
# OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING 
# OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import sys, random, math
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QSizePolicy, QGraphicsTextItem, \
    QGraphicsLineItem
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QBrush, QPen, QTransform, QPainter, QSurfaceFormat, QColor


class VisGraphicsScene(QGraphicsScene):
    def __init__(self):
        super(VisGraphicsScene, self).__init__()
        self.selection = None
        self.wasDragg = False
        self.pen = QPen(Qt.black)
        self.selected = QPen(Qt.red)

    def mouseReleaseEvent(self, event): 
        if(self.wasDragg):
            return
        if(self.selection):
            self.selection.setPen(self.pen)
        item = self.itemAt(event.scenePos(), QTransform())
        if(item):
            item.setPen(self.selected)
            self.selection = item


class VisGraphicsView(QGraphicsView):
    def __init__(self, scene, parent):
        super(VisGraphicsView, self).__init__(scene, parent)
        self.startX = 0.0
        self.startY = 0.0
        self.distance = 0.0
        self.myScene = scene
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)

    def wheelEvent(self, event):
        zoom = 1 + event.angleDelta().y()*0.001;
        self.scale(zoom, zoom)
        
    def mousePressEvent(self, event):
        self.startX = event.pos().x()
        self.startY = event.pos().y()
        self.myScene.wasDragg = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        endX = event.pos().x()
        endY = event.pos().y()
        deltaX = endX - self.startX
        deltaY = endY - self.startY
        distance = math.sqrt(deltaX*deltaX + deltaY*deltaY)
        if(distance > 5):
            self.myScene.wasDragg = True
        super().mouseReleaseEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('VIZ Qt for Python Example')
        self.createGraphicView()
        self.generateAndMapData()
        self.setMinimumSize(700, 350)
        self.show()

    def createGraphicView(self):
        self.scene = VisGraphicsScene()
        self.brush = [QBrush(Qt.yellow), QBrush(Qt.green), QBrush(Qt.blue)]
        
        format = QSurfaceFormat();
        format.setSamples(4);
        
        gl = QOpenGLWidget();
        gl.setFormat(format);
        gl.setAutoFillBackground(True)
        
        self.view = VisGraphicsView(self.scene, self)
        self.view.setViewport(gl);
        self.view.setBackgroundBrush(QColor(255, 255, 255))
        
        self.setCentralWidget(self.view)
        self.view.setGeometry(0, 0, 800, 600)


    # x axis range is ca. (60, 130)
    # y axis range is ca. (25, 50)
    # -> ration width:height is ca. 70 : 25

    def mercator_projection(self, longitude, latitude):
        x = (longitude + 180) * (self.view.width() / 360)
        y = (180 / math.pi) * math.log(math.tan(math.pi / 4 + latitude * math.pi / 360))
        y = (self.view.height() / 2) - (self.view.height() * y / (2 * 180))
        return x, y
    def generateAndMapData(self):
        cities = [
            {'name': 'New York', 'latitude': 40.7128, 'longitude': -74.0060},
            {'name': 'Los Angeles', 'latitude': 34.0522, 'longitude': -118.2437},
            {'name': 'Chicago', 'latitude': 41.8781, 'longitude': -87.6298},
            {'name': 'Houston', 'latitude': 29.7604, 'longitude': -95.3698},
            {'name': 'Phoenix', 'latitude': 33.4484, 'longitude': -112.0740},
            {'name': 'Philadelphia', 'latitude': 39.9526, 'longitude': -75.1652},
            {'name': 'San Antonio', 'latitude': 29.4241, 'longitude': -98.4936},
            {'name': 'San Diego', 'latitude': 32.7157, 'longitude': -117.1611},
            {'name': 'Dallas', 'latitude': 32.7767, 'longitude': -96.7970},
            {'name': 'San Jose', 'latitude': 37.3382, 'longitude': -121.8863},
            # Add more cities as needed
        ]

        # Define scaling factor
        scale_factor = 20  # Adjust this value as needed


        # Map data to graphical elements
        for city in cities:
            # Convert latitude and longitude to scene coordinates
            x, y = self.mercator_projection(city['longitude'], city['latitude'])

            # Apply scaling factor
            x *= scale_factor
            y *= scale_factor

            # Add city circle
            d = 10
            ellipse = self.scene.addEllipse(x - d / 2, y - d / 2, d, d, self.scene.pen, self.brush[0])

            # Add city label
            text = QGraphicsTextItem(city['name'])
            text.setPos(x + 10, y - 10)  # Adjust position for label
            self.scene.addItem(text)

            # Add edges between cities
            edges = [
                ('New York', 'Los Angeles'),
                ('New York', 'Chicago'),
                # Add more edges as needed
            ]
            for edge in edges:
                city1 = next((city for city in cities if city['name'] == edge[0]), None)
                city2 = next((city for city in cities if city['name'] == edge[1]), None)
                if city1 and city2:
                    x1, y1 = self.mercator_projection(city1['longitude'], city1['latitude'])
                    x2, y2 = self.mercator_projection(city2['longitude'], city2['latitude'])
                    x1 *= scale_factor
                    y1 *= scale_factor
                    x2 *= scale_factor
                    y2 *= scale_factor
                    line = QGraphicsLineItem(x1, y1, x2, y2)
                    self.scene.addItem(line)


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

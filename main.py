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
from airline_dataset import AirlineDataset
import sys, random, math
from PySide6.QtCore import Qt, QSize
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QSizePolicy, QGraphicsTextItem, \
    QGraphicsLineItem, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, QGraphicsEllipseItem
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QBrush, QPen, QTransform, QPainter, QSurfaceFormat, QColor


dataset = AirlineDataset("./data/airlines.graphml")
class VisGraphicsScene(QGraphicsScene):
    def __init__(self):
        super(VisGraphicsScene, self).__init__()
        self.city_items = {}
        self.selection = None
        self.wasDragg = False
        self.pen = QPen(Qt.black)
        color = QColor(0, 255, 0, 127)  # Red color with 50% opacity
        self.brush = QBrush(color)

        self.selected_pen = QPen(Qt.red)
        self.selected_brush = QBrush(Qt.red)

    def mouseReleaseEvent(self, event):
        if (self.wasDragg):
            return
        if (self.selection):
            self.selection.setPen(self.pen)
            self.selection.setBrush(self.brush)
        item = self.itemAt(event.scenePos(), QTransform())
        if (item):
            item.setPen(self.selected_pen)
            item.setBrush(self.selected_brush)
            self.selection = item

            if isinstance(item, QGraphicsEllipseItem): # city
                print(f"selected: {item.data(0)}")


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
        zoom = 1 + event.angleDelta().y() * 0.001;
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
        distance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
        if (distance > 5):
            self.myScene.wasDragg = True
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('VIZ Qt for Python Example')
        self.createWidgets()
        self.generateAndMapData()
        self.setMinimumSize(1000, 600)
        self.show()

    def createWidgets(self):
        # Create main widget to hold layout
        mainWidget = QWidget()
        self.setCentralWidget(mainWidget)
        layout = QHBoxLayout(mainWidget)

        # Create visualization view
        self.scene = VisGraphicsScene()
        self.brush = [QBrush(Qt.yellow), QBrush(Qt.green), QBrush(Qt.blue)]

        format = QSurfaceFormat();
        format.setSamples(4);

        gl = QOpenGLWidget()
        gl.setFormat(format)
        gl.setAutoFillBackground(True)

        self.view = VisGraphicsView(self.scene, self)
        self.view.setViewport(gl)
        self.view.setBackgroundBrush(QColor(255, 255, 255))
        self.view.setGeometry(0, 0, 1000, 1000)
        layout.addWidget(self.view)


        # Create list widget for cities
        self.cityListWidget = QListWidget()
        self.cityListWidget.itemClicked.connect(self.onCityListItemClicked)  # Connect signal to slot
        layout.addWidget(self.cityListWidget)

        layout.setStretch(0, 5)  # Set stretch factor for visualization view
        layout.setStretch(1, 1)  # Set stretch factor for list widget

    def onCityListItemClicked(self, item):
        city_name = item.text()
        if self.scene.selection:
            self.scene.selection.setPen(self.scene.pen)  # Reset previous selection
            self.scene.selection.setBrush(self.scene.brush)  # Reset previous selection
        city_item = self.scene.city_items.get(city_name)
        if city_item:
            city_item.setPen(self.scene.selected_pen)  # Highlight selected city
            city_item.setBrush(self.scene.selected_brush)  # Highlight selected city
            self.scene.selection = city_item
    def get_airport_size(self, airport):
        MAX_SIZE = 100
        size = 10
        for e in dataset.edges:
            idx = airport["index"]
            if idx == e[0] or idx == e[1]:
                size *= 1.01

        return min(size, MAX_SIZE)

    # x axis range is ca. (60, 130)
    # y axis range is ca. (25, 50)
    # -> ration width:height is ca. 70 : 25

    def mercator_projection(self, longitude, latitude):
        x = (longitude + 180) * (self.view.width() / 360)
        y = (180 / math.pi) * math.log(math.tan(math.pi / 4 + latitude * math.pi / 360))
        y = (self.view.height() / 2) - (self.view.height() * y / (2 * 180))
        return x, y

    def generateAndMapData(self):
        cities = dataset.nodes

        cities.sort(key=lambda x: x['name'])

        # Populate list widget with city names
        for city in cities:
            item = QListWidgetItem(city['name'])
            self.cityListWidget.addItem(item)



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
            d = self.get_airport_size(city)
            ellipse = self.scene.addEllipse(x - d / 2, y - d / 2, d, d, self.scene.pen, self.scene.brush)
            ellipse.setData(0, city['name'])  # Store the city name as custom data
            self.scene.city_items[city['name']] = ellipse  # Store the ellipse item

            # Add city label
            text = QGraphicsTextItem(city['name'])
            text.setPos(x + 10, y - 10)  # Adjust position for label
            self.scene.addItem(text)




def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
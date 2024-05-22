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
import numpy as np

from airline_dataset import AirlineDataset
import sys, random, math
from PySide6.QtCore import Qt, QSize
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QSizePolicy, QGraphicsTextItem, \
    QGraphicsLineItem, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, QGraphicsEllipseItem
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QBrush, QPen, QTransform, QPainter, QSurfaceFormat, QColor
from my_fdeb import MyFdeb


dataset = AirlineDataset("./data/airlines.graphml")
class VisGraphicsScene(QGraphicsScene):
    def __init__(self):
        super(VisGraphicsScene, self).__init__()
        self.city_items = {}
        self.selection = None
        self.wasDragg = False

        color = QColor(255, 255, 0, 200)  # Red color with 50% opacity
        self.pen = QPen(color)
        self.brush = QBrush(color)

        selected_color = QColor(0, 255, 0, 255)
        self.selected_pen = QPen(selected_color)
        self.selected_brush = QBrush(selected_color)

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
        self.setMinimumSize(1600, 900)
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
        self.view.scale(0.4, 0.4)
        self.view.setBackgroundBrush(QBrush(QColor(0, 0, 128, 255)))
        layout.addWidget(self.view)


        # Create list widget for cities
        self.cityListWidget = QListWidget()
        self.cityListWidget.itemClicked.connect(self.onCityListItemClicked)  # Connect signal to slot
        self.cityListWidget.itemSelectionChanged.connect(self.changeItemColor)
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

    def changeItemColor(self):

        for i in range(self.cityListWidget.count()):
            item = self.cityListWidget.item(i)
            item.setData(Qt.BackgroundRole, QBrush(QColor("white")))
            item.setData(Qt.ForegroundRole, QBrush(QColor("black")))

            # Change the color of selected items
        selected_items = self.cityListWidget.selectedItems()
        for item in selected_items:
            item.setData(Qt.BackgroundRole, QBrush(QColor("blue")))  # Change background color to blue
            item.setData(Qt.ForegroundRole, QBrush(QColor("white")))  # Change text color to white


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

    def get_edge_coords(self, airports):
        edges = dataset.edges

        coords = np.zeros((len(edges), 2, 2))
        for i, e in enumerate(edges):
            x1, y1 = airports[e[0]]["x"], airports[e[0]]["y"]
            x2, y2 = airports[e[1]]["x"], airports[e[1]]["y"]

            print(f"edge from {airports[e[0]]['name']} to {airports[e[1]]['name']}")
            print(f"x1: {x1} y1: {y1} x2: {x2} y2: {y2}")

            coords[i, 0, 0] = x1
            coords[i, 0, 1] = y1
            coords[i, 1, 0] = x2
            coords[i, 1, 1] = y2


        return coords
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

            city["x"] = x
            city["y"] = y

            # Add city circle
            d = self.get_airport_size(city)
            ellipse = self.scene.addEllipse(x - d / 2, y - d / 2, d, d, self.scene.pen, self.scene.brush)
            ellipse.setData(0, city['name'])  # Store the city name as custom data
            self.scene.city_items[city['name']] = ellipse  # Store the ellipse item

            # Add city label
            text = QGraphicsTextItem(city['name'])
            text.setDefaultTextColor(Qt.black)
            text.setPos(x + 10, y - 10)  # Adjust position for label
            self.scene.addItem(text)

        # sort back to original order
        cities.sort(key=lambda x: x['index'])
        edge_coords = self.get_edge_coords(cities)

        overflow_const = 100 # 10 worked for 60 its, not for 100
        # PERFORM EDGE BUNDLING
        edge_coords /= overflow_const  # prevent overflow

        # mf = MyFdeb()
        # edges_fdeb = mf.my_fdeb(edge_coords)
        # print(edges_fdeb.shape)
        # with open('edges_fdeb.npy', 'wb') as f:
        #     np.save(f, edges_fdeb)

        with open('edges_fdeb_best.npy', 'rb') as f:
            edges_fdeb = np.load(f)

        edges_fdeb *= overflow_const
        edge_coords *= overflow_const
        print(edge_coords)

        # edges_fdeb = edge_coords # switch bundled/not bundled

        for i in range(edges_fdeb.shape[0]):
            for j in range(edges_fdeb.shape[1]-1):
                x1, y1 = edges_fdeb[i, j, :]
                x2, y2 = edges_fdeb[i, j+1, :]

                line = QGraphicsLineItem(x1, y1, x2, y2)
                line.setZValue(-50)  # Set a low Z-value for edges
                line.setPen(QPen(QColor(255, 0, 0, 60)))
                self.scene.addItem(line)







def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
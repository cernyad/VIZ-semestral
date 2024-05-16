import sys
import cartopy.crs as ccrs
import cartopy
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSizePolicy, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("U.S. Contour")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.fig, self.ax = plt.subplots(figsize=(6, 4), subplot_kw={'projection': ccrs.LambertConformal()})
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

        self.draw_map()

    def draw_map(self):
        ax = self.ax
        ax.set_extent([-125, -66.5, 20, 50], ccrs.Geodetic())
        ax.coastlines()
        ax.add_feature(cartopy.feature.STATES, linestyle='-', edgecolor='black')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

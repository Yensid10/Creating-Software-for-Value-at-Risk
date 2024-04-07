from kivy.uix.screenmanager import Screen
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import random

import logging
logging.getLogger('matplotlib').setLevel(logging.INFO)

# Contains code inspired by: https://stackoverflow.com/a/55184676
class Graphs(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infoPopup = None
        self.currentLine = None
        self.Graph1()
        

    def Graph1(self):
        x = list(range(1, 101))
        y = [random.randint(i, 1000) for i in x]
        self.createGraph(x, y, 'some random linear numbers', 'more random linear numbers', 'Random Graph 1')

    def Graph2(self):
        x = list(range(1, 101))
        y = [i ** 2 for i in x]  # Example quadratic data
        self.createGraph(x, y, 'numbers', 'more numbers', 'Quadratic?')


    def createGraph(self, x, y, xlabel, ylabel, title):
        self.ids.graphSection.clear_widgets()
        self.fig, self.ax = plt.subplots()
        self.currentLine, = self.ax.plot(x, y, 'o-')
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        
        self.infoPopup = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        self.infoPopup.set_visible(False)

        canvas = FigureCanvasKivyAgg(self.fig)
        canvas.mpl_connect("motion_notify_event", self.mouse_hover)
        
        canvas = FigureCanvasKivyAgg(self.fig)
        self.ids.graphSection.add_widget(canvas)

    def showPopup(self, x, y):
        text = f"({x}, {y})"
        self.infoPopup.set_text(text)
        self.infoPopup.xy = (x, y)
        self.infoPopup.set_visible(True)
        self.fig.canvas.draw_idle()

    def hidePopup(self):
        self.infoPopup.set_visible(False)
        self.fig.canvas.draw_idle()

    def mouse_hover(self, event):
        if event.inaxes == self.ax:
            cont, ind = self.currentLine.contains(event)
            if cont:
                pos = ind['ind'][0]
                x, y = self.currentLine.get_data()
                self.showPopup(x[pos], y[pos])
            else:
                self.hidePopup()

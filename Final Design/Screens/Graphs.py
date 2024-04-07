from kivy.uix.screenmanager import Screen
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import random

import logging
logging.getLogger('matplotlib').setLevel(logging.INFO)

class Graphs(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.line1 = None
        self.createGraph1()

    # Inspired by: https://stackoverflow.com/a/55184676
    def createGraph1(self):
        self.ids.graphSection.clear_widgets()

        # Create matplotlib figure and axes
        self.fig, self.ax = plt.subplots()

        x = list(range(1, 101))
        y = [random.randint(i, 1000) for i in x]
        self.line1, = self.ax.plot(x, y, 'o-')

        self.ax.set_xlabel('some random linear numbers')
        self.ax.set_title('Random Graph 1')
        self.ax.set_ylabel('more random linear numbers')

        canvas = FigureCanvasKivyAgg(self.fig)
        canvas.mpl_connect("motion_notify_event", self.mouse_hover)

        self.infoPopup = self.ax.annotate("", xy=(0, 0), xytext=(-20, -30), textcoords="offset points",
                                            bbox=dict(boxstyle="round", fc="w"),
                                            arrowprops=dict(arrowstyle="->"))
        self.infoPopup.set_visible(False)

        self.ids.graphSection.add_widget(canvas)

    def createGraph2(self):
        self.ids.graphSection.clear_widgets()
        plt.figure(figsize=(6, 4))
        plt.plot([124, 34345, 123, 1333])
        plt.ylabel('some random numbers')
        plt.title('Random Graph 2')
        plt.xlabel('more random numbers')

        plt.tight_layout()
        
        self.ids.graphSection.add_widget(FigureCanvasKivyAgg(plt.gcf()))

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
            cont, ind = self.line1.contains(event)
            if cont:
                pos = ind['ind'][0]
                x, y = self.line1.get_data()
                self.showPopup(x[pos], y[pos])
            else:
                self.hidePopup()

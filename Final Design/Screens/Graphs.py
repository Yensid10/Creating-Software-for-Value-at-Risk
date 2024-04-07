from kivy.uix.screenmanager import Screen

import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import logging
logging.getLogger('matplotlib').setLevel(logging.INFO)

class Graphs(Screen):
    def __init__(self, **kwargs):
        super(Graphs, self).__init__(**kwargs)
        self.createGraph()

    def createGraph(self):
        plt.figure(figsize=(6, 4))
        plt.plot([1, 29, 12, 4])
        plt.ylabel('some random numbers')
        plt.title('Random Graph')
        plt.xlabel('more random numbers')

        plt.tight_layout()

        self.ids.graphSection.add_widget(FigureCanvasKivyAgg(plt.gcf()))

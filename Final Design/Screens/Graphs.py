from kivy.uix.screenmanager import Screen

import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

import logging
logging.getLogger('matplotlib').setLevel(logging.INFO)

class Graphs(Screen):
    def __init__(self, **kwargs):
        super(Graphs, self).__init__(**kwargs)
        self.createGraph1()

    def createGraph1(self):
        self.ids.graphSection.clear_widgets()
    
        plt.figure(figsize=(6, 4))
        plt.plot([1, 29, 12, 4])
        plt.ylabel('some random numbers')
        plt.title('Random Graph 1')
        plt.xlabel('more random numbers')
    
        plt.tight_layout()
    
        self.ids.graphSection.add_widget(FigureCanvasKivyAgg(plt.gcf()))
    
    def createGraph2(self):
        self.ids.graphSection.clear_widgets()
    
        plt.figure(figsize=(6, 4))
        plt.plot([124, 34345, 123, 1333])
        plt.ylabel('some random numbers')
        plt.title('Random Graph 2')
        plt.xlabel('more random numbers')
    
        plt.tight_layout()
    
        self.ids.graphSection.add_widget(FigureCanvasKivyAgg(plt.gcf()))

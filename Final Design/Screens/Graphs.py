import time
from kivy.uix.screenmanager import Screen
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import random
import numpy as np
from kivy.storage.jsonstore import JsonStore

import threading
from kivy.clock import mainthread

import logging
logging.getLogger('matplotlib').setLevel(logging.INFO)

# Contains code inspired by: https://stackoverflow.com/a/55184676
class Graphs(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infoPopup = None
        self.currentLine = None
        self.Graph1()

    @property
    def portfolio(self): # Used for self.portfolio possibly being used in other functions
        return self.manager.get_screen('Portfolio') if self.manager else None

    def Graph1(self):
        x = list(range(1, 101))
        y = [random.randint(i, 1000) for i in x]
        self.createGraph(x, y, 'some random linear numbers', 'more random linear numbers', 'Random Graph 1')
        # CHANGE THIS TO BE PAST PORTFOLIO DATA :))


    def Graph2(self):
        x = list(range(1, 101))
        y = [i ** 2 for i in x]  # Example quadratic data
        self.createGraph(x, y, 'numbers', 'more numbers', 'Quadratic?')


    def graph3(self):
        threading.Thread(target=self.monteCarloConvSim).start()

    def monteCarloConvSim(self):
        stocks = self.portfolio.tempDownload
        store = JsonStore('holdings.json')
        totalValue = float(self.portfolio.totalValue.text.split('£')[1].replace(',', '')[:-4])

        weightings = np.zeros(len(stocks['Close'].columns))
        for x, stockKey in enumerate(store):
            stockData = store.get(stockKey)
            currentPrice = stocks['Close'][stockData['ticker']].loc[stocks['Close'][stockData['ticker']].last_valid_index()]
            currentValue = currentPrice * float(stockData['sharesOwned'])
            weightings[x] = currentValue / totalValue

        closeDiffs = stocks['Close'].pct_change(fill_method=None).dropna()
        
        checkpoints = list(range(500, 25500, 500)) # Iteration checkpoints to check for convergence 
        varResults = []

        for sim in checkpoints:
            # Generate all simulations at once
            optimisedSim = np.random.multivariate_normal(closeDiffs.mean(), closeDiffs.cov(), (self.portfolio.varCalc.timeHori, sim))
            portfoReturns = np.zeros(sim)

            for x in range(sim):
                portfoReturns[x] = np.sum(np.sum(optimisedSim[:, x, :] * weightings, axis=1))

            # Calculate VaR at this checkpoint
            VaR = np.percentile(sorted(portfoReturns), 100 * self.portfolio.varCalc.rlPercent) * totalValue
            varResults.append(round(-VaR))
            time.sleep(1) # Make it so i show that the graph is loading somehow.
        
        # Plotting the convergence of VaR
        self.createGraph(checkpoints, varResults, 'Number of Simulations', 'Value at Risk (VaR)', 'Convergence Analysis of Monte Carlo Simulation Based on Current Portfolio')

    @mainthread
    def createGraph(self, x, y, xlabel, ylabel, title):
        self.ids.graphSection.clear_widgets()
        self.fig, self.ax = plt.subplots()
        self.currentLine, = self.ax.plot(x, y, 'o-')
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        # self.ax.grid(True)
        
        self.infoPopup = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        self.infoPopup.set_visible(False)

        canvas = FigureCanvasKivyAgg(self.fig)
        canvas.mpl_connect("motion_notify_event", self.mouse_hover)

        self.fig.tight_layout()
        
        canvas = FigureCanvasKivyAgg(self.fig)
        self.ids.graphSection.add_widget(canvas)

    def showPopup(self, x, y):
        text = f"({y})"
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

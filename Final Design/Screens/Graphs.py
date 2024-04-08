from kivy.uix.screenmanager import Screen
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import numpy as np
from kivy.storage.jsonstore import JsonStore
import yfinance as yf

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
        self.graph1Flag = False # May change
        self.threadRunning = False
        self.stopThread = threading.Event()

    def on_enter(self): # To run graph1 the first time you enter the screen, temporary solution
        if not self.graph1Flag:
            self.graph1()
            self.graph1Flag = True


            

    @property
    def portfolio(self): # Used for self.portfolio possibly being used in other functions
        return self.manager.get_screen('Portfolio') if self.manager else None
    



    def graph1(self):
        stocks = self.portfolio.tempDownload
        store = JsonStore('holdings.json')

        closePrices = stocks['Close'].tail(500)
    
        totalValues = []
        for i in range(len(closePrices)):
            dailyTotal = 0
            row = closePrices.iloc[i]
            for stockKey in store:
                stockData = store.get(stockKey)
                dailyTotal += row[stockData['ticker']] * float(stockData['sharesOwned'])
            totalValues.append(dailyTotal)

        # y values for total portfolio value every 15 days
        x = list(range(500, 0, -15))  # adjust the range to match the length of y
        y = totalValues[::15]
        y = self.replaceNan(y)
        y = [round(num) for num in y]
        y[-1] = round(self.portfolio.tempTotalValue)

        self.createGraph(x, y, 'Last 500 Days', 'Total Theoretical Portfolio Value (£)', 'Portfolio Value Over Time With Theoretical Current Shares', '£')


    def graph2(self):
        tempStockInfo = self.portfolio.tempStockInfo
        if tempStockInfo is not None:
            stocks = self.portfolio.tempDownload
            store = JsonStore('holdings.json')

            closePrices = stocks['Close'][tempStockInfo['ticker']].tail(500)

            totalValues = []
            for i in range(len(closePrices)):
                dailyTotal = 0
                row = closePrices.iloc[i]
                for stockKey in store:
                    stockData = store.get(stockKey)
                    if stockData['ticker'] == tempStockInfo['ticker']:
                        dailyTotal += row
                totalValues.append(dailyTotal)

            # y values for total portfolio value every 15 days
            x = list(range(500, 0, -15))  # adjust the range to match the length of y
            y = totalValues[::15]
            y = self.replaceNan(y)
            y = [round(num, 2) for num in y]
            y[-1] = round(self.portfolio.tempCurrentPrice, 2)

            
            self.createGraph(x, y, 'Last 500 Days', self.portfolio.tempStockInfo['ticker'] + ' Share Value (£)', self.portfolio.tempStockInfo['name'].split("(", 1)[0] + 'Individual Share Pricing Over Time', '£')

    def graph3(self):
        ftse100 = [ticker + ".L" for ticker in self.manager.get_screen('VaRChecker').ftse100['Ticker'].tolist()]
        # print(ftse100)
        # stockData = yf.download(ftse100, period="500d")['Adj Close']
        # print(stockData)

        # stockData = yf.download(ftse100, period="500d")
        # VaRs = {}
        # for stock in stockData.columns.levels[1]:  # iterate over stock tickers
        #     VaRs[stock] = self.portfolio.varCalc.modelSim(1000, stockData['Adj Close'][stock])
        # print(VaRs)
        
    # def modelSim(self, totalValue, stocks):
    #     closeDiffs = stocks.pct_change(fill_method=None).dropna()
    #     return "{:,.2f}".format((-totalValue*norm.ppf(self.rlPercent/100, np.mean(closeDiffs), np.std(closeDiffs)))*np.sqrt(self.timeHori))







    def graph5(self):
        x = list(range(0, 101))
        y = [i ** 2 for i in x]  # Example quadratic data
        self.createGraph(x, y, 'numbers', 'more numbers', 'Quadratic?', "")







    def graph6(self):
        if not self.threadRunning:
            self.threadRunning = True
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
        varResults = [np.nan]

        for sim in checkpoints:
            if self.stopThread.is_set():
                return
            # Generate all simulations at once
            optimisedSim = np.random.multivariate_normal(closeDiffs.mean(), closeDiffs.cov(), (self.portfolio.varCalc.timeHori, sim))
            portfoReturns = np.zeros(sim)

            weightings = weightings.reshape(1, -1)
            portfoReturns = np.sum(optimisedSim * weightings, axis=2)

            VaR = np.percentile(sorted(portfoReturns), 100 * self.portfolio.varCalc.rlPercent) * totalValue
            varResults.append(round(-VaR))
        
        self.threadRunning = False
        checkpoints.insert(0, 0)
        # Plotting the convergence of VaR
        self.createGraph(checkpoints, varResults, 'Number of Simulations', 'Value at Risk (£)', 'Convergence Analysis of Monte Carlo Simulation Based on Current Portfolio', "£")

    @mainthread
    def createGraph(self, x, y, xlabel, ylabel, title, currentSymbol):
        print(y)
        self.ids.graphSection.clear_widgets()
        self.fig, self.ax = plt.subplots()
        self.currentLine, = self.ax.plot(x, y, 'o-')

        if x[0] > x[-1]:
            xTicks = np.arange(x[0], -1, -max(x[0] // 5, 20)) 
            xTicks = np.append(xTicks, 0) 
        else:
            xTicks = np.linspace(start=min(x), stop=max(x), num=min(len(x), 5))

        self.ax.set_xticks(xTicks)
        self.ax.set_xticklabels([str(int(tick)) for tick in xTicks])

        # Only invert the x-axis if the first values are in descending order
        if x[0] > x[-1]:
            self.ax.invert_xaxis()

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        
        self.infoPopup = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        self.infoPopup.set_visible(False)

        canvas = FigureCanvasKivyAgg(self.fig)
        canvas.mpl_connect("motion_notify_event", self.mouse_hover)

        self.fig.tight_layout()
        self.currentSymbol = currentSymbol
        
        self.ids.graphSection.add_widget(canvas)





    def showPopup(self, x, y):
        # Temporary solution for weird floating points being displayed
        if y.is_integer():
            text = f"{self.currentSymbol}{int(y):,}"
        else:
            text = f"{self.currentSymbol}{y:,.2f}"
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

    def replaceNan(self, y):
        for i in range(len(y)):
            if np.isnan(y[i]):
                if i == 0:
                    nextValue = next((y[j] for j in range(i + 1, len(y)) if not np.isnan(y[j])), None)
                    nextNextValue = next((y[j] for j in range(i + 2, len(y)) if not np.isnan(y[j])), None)
                    if nextValue is not None and nextNextValue is not None:
                        y[i] = nextValue - (nextNextValue - nextValue)
                else:
                    prevValue = next((y[j] for j in range(i - 1, -1, -1) if not np.isnan(y[j])), None)
                    nextValue = next((y[j] for j in range(i + 1, len(y)) if not np.isnan(y[j])), None)
                    if prevValue is not None and nextValue is not None:
                        y[i] = (prevValue + nextValue) / 2
                    if np.isnan(y[-1]):
                        lastNoneNan = next((y[i] for i in range(len(y) - 2, -1, -1) if not np.isnan(y[i])), None)
                        if lastNoneNan is not None:
                            y[-1] = (lastNoneNan + y[-1]) / 2
        return y
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

    @property
    def portfolio(self): # Used for self.portfolio possibly being used in other functions
        return self.manager.get_screen('Portfolio') if self.manager else None
    
    @property
    def varChecker(self):  # Used for self.varChecker possibly being used in other functions
        return self.manager.get_screen('VaRChecker') if self.manager else None

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

            x = list(range(500, 0, -15))
            y = totalValues[::15]
            y = self.replaceNan(y)
            y = [round(num, 2) for num in y]
            y[-1] = round(self.portfolio.tempCurrentPrice, 2)

            self.createGraph(x, y, 'Last 500 Days', self.portfolio.tempStockInfo['ticker'] + ' Share Value (£)', self.portfolio.tempStockInfo['name'].split("(", 1)[0] + 'Individual Share Pricing Over Time', '£')



    def graph3(self): # I added all the methods for this here, since it was harder to get to work then everything else, so I want to keep it as it's own section
        if not self.threadRunning:
            self.threadRunning = True
            threading.Thread(target=self.ftse100Ranking).start()
    
    def ftse100Ranking(self):
        ftse100 = [ticker + ".L" for ticker in self.varChecker.ftse100['Ticker'].tolist()]
        ftse100Names = self.varChecker.ftse100['Company'].tolist()
        tickerToName = dict(zip(ftse100, ftse100Names))  # mapping between tickers and names
    
        stockData = yf.download(ftse100, period="500d")
        VaRs = {}
        for stock in stockData.columns.levels[1]:  # iterate over stock tickers
            VaRs[tickerToName[stock]] = float(self.portfolio.varCalc.modelSim(1000, stockData['Adj Close'][stock])) #  company name is the key
    
        sortedVar = dict(sorted(VaRs.items(), key=lambda item: item[1]))
        self.threadRunning = False
        self.createRankingGraph(list(sortedVar.keys()), list(sortedVar.values()), 'FTSE100 Stocks Ranked by VaR', 'Value at Risk for £1000 holding of Stock', 'Ranking FTSE100 Stocks based on their Value at Risk for £1000 holding of Stock')
        

    @mainthread
    def createRankingGraph(self, tickers, vars, xlabel, ylabel, title):
        self.ids.graphSection.clear_widgets()
        self.fig, self.ax = plt.subplots()
        self.currentLine, = self.ax.plot(range(len(vars)), vars, 'o-')
    
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
    
        self.infoPopup = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        self.infoPopup.set_visible(False)
    
        self.tickerHover = tickers # Save the tickers for the hover function
    
        canvas = FigureCanvasKivyAgg(self.fig)
        canvas.mpl_connect("motion_notify_event", self.FTSEonHover)
        self.fig.tight_layout()
        self.ids.graphSection.add_widget(canvas)

    def FTSEonHover(self, event):
        if event.inaxes == self.ax:
            cont, ind = self.currentLine.contains(event)
            if cont:
                pos = ind['ind'][0]
                tickerName = self.tickerHover[pos]  # Access the corresponding ticker value
                self.showFTSE(tickerName, event.xdata, event.ydata)
            else:
                self.hidePopup() # Can still use the previous hidePopup function

    def showFTSE(self, tickerName, x, y): 
        # Get the limits of the axes
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        print(xlim, ylim)
        print(x, y)
    
        # Calculate the relative position of the point within the axes
        x_rel = (x - xlim[0]) / (xlim[1] - xlim[0])
        y_rel = (y - ylim[0]) / (ylim[1] - ylim[0])
    
        # Have self tested these, they appear to be perfect
        if x_rel < 0.5: # Left half
            xOffset = -10
        else: # Right half
            xOffset = -95

        if y_rel < 0.5: # Bottom half
            yOffset = 60
        else: # Top half
            yOffset = 0
    
        # # Update the position of the annotation text
        self.infoPopup.xy = (x, y)
        self.infoPopup.set_position((-x + xOffset, -y + yOffset)) # I think this overly complicates it, but it works
        self.infoPopup.set_text(f"Stock: {tickerName}")
        self.infoPopup.set_visible(True)
        self.fig.canvas.draw_idle()



    def graph4(self):
        test = self.varChecker.currentStock.text



    def graph5(self):
        stocks = self.portfolio.tempDownload
        store = JsonStore('holdings.json')

        # Create a mapping between stock tickers and names
        tickerToName = {stock: store.get(stock)['name'].split("(")[0].strip() for stock in stocks.columns.levels[1]}
        # print(tickerToName)

        VaRs = {}
        for stock in stocks.columns.levels[1]:  # iterate over stock tickers
            VaRs[tickerToName[stock]] = float(self.portfolio.varCalc.modelSim(1000, stocks['Adj Close'][stock]))  # name is the key

        sortedVar = dict(sorted(VaRs.items(), key=lambda item: item[1]))
        print(sortedVar)
        self.createRankingGraph(list(sortedVar.keys()), list(sortedVar.values()), 'Portfolio Stocks Ranked by VaR', 'Value at Risk for £1000 holding of Stock', 'Ranking Portfolio Stocks based on their Value at Risk for £1000 holding of Stock')




    def graph6(self):
        if not self.threadRunning:
            self.threadRunning = True
            threading.Thread(target=self.monteCarloConvSim).start()

    def monteCarloConvSim(self):
        stocks = self.portfolio.tempDownload
        store = JsonStore('holdings.json')
        totalValue = float(self.portfolio.tempTotalValue)

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





    def graph7(self):
        stocks = self.portfolio.tempDownload
        totalValue = float(self.portfolio.tempTotalValue)
        count = 0
        adjust = int(len(stocks)/10)
        VaRs = []
        nextDays = []
        store = JsonStore('holdings.json')
        weightings = np.zeros(len(stocks['Adj Close'].columns))
        for x, stockKey in enumerate(store):
            stockData = store.get(stockKey)
            currentPrice = stocks['Adj Close'][stockData['ticker']].loc[stocks['Adj Close'][stockData['ticker']].last_valid_index()]
            currentValue = currentPrice * float(stockData['sharesOwned'])
            weightings[x] = currentValue / totalValue
        

        for i in range(1, len(stocks) - adjust - 1):            
            # Monte Carlo Simulation VaR calculation
            closeDiffs = stocks['Adj Close'].pct_change(fill_method=None).dropna()
            simNum = 10000
            convThreshold = 0.001
            previousVar = float('inf')
            converged = False
    
            while not converged and simNum <= 100000:            
                portfoReturns = np.zeros(simNum)
                optimisedSim = np.random.multivariate_normal(closeDiffs.mean().values, closeDiffs.cov().values, (self.portfolio.varCalc.timeHori, simNum))
    
                weightings = weightings.reshape(1, -1)
                portfoReturns = np.sum(optimisedSim * weightings, axis=2)
    
                currentVar = -np.percentile(sorted(portfoReturns), 100 * self.portfolio.varCalc.rlPercent)
    
                if previousVar != float('inf') and abs((currentVar - previousVar) / previousVar) < convThreshold:
                    converged = True
                else:
                    previousVar = currentVar
                    simNum += 5000
    
            VaR = -currentVar*100 # Not currently multiplied by totalValue
            VaRs.append(VaR)
            # print(VaR)

            # Calculate total value for the day specified (i+adjust)
            totalValue = 0
            for stockKeys in store:
                stockData = store.get(stockKeys)
                currentPrice = stocks['Adj Close'][stockData['ticker']].iloc[i+adjust]
                totalValue += (currentPrice * float(stockData['sharesOwned']))
            
            # Calculate total value for the next day (i+adjust+1)
            totalValueNextDay = 0
            for stockKeys in store:
                stockData = store.get(stockKeys)
                nextDayPrice = stocks['Adj Close'][stockData['ticker']].iloc[i+adjust+1]
                totalValueNextDay += (nextDayPrice * float(stockData['sharesOwned']))
            
            # Calculate the percentage difference between the two days
            percentageDifference = (((totalValueNextDay - totalValue) / totalValue) * 100)*np.sqrt(self.portfolio.varCalc.timeHori)
            nextDays.append(percentageDifference)
            # print(percentageDifference)
    
            if not np.isnan(percentageDifference) and VaR > percentageDifference:
                count += 1
        print(count)
        print(VaRs)
        print(nextDays)
    
    #     # ... existing code ...




        # def backTest(self, stock):
        #     #Taken from Single Stock VaR.py
        #     count = 0
        #     adjust = int(len(stock)/10)
        #     for i in range(1, len(stock) - adjust - 1):
        #         backTest = stock['Adj Close'].pct_change()[i:i+adjust]
        #         if self.simMethod == "Historical":
        #             VaR = np.percentile(backTest, self.rlPercent)*np.sqrt(self.timeHori)*self.portfolio
        #         else:
        #             VaR = (-self.portfolio*norm.ppf(self.rlPercent/100, np.mean(backTest), np.std(backTest)))*np.sqrt(self.timeHori)*-1 #Always returns a positive value with model simulation, so needs to be multiplied by -1
        #         nextDay = stock['Adj Close'].pct_change()[i+adjust:i+adjust+1].values[0]*np.sqrt(self.timeHori)*self.portfolio
        #         if VaR > nextDay:
        #             count += 1
        #     pValue = binom.cdf((len(stock)-adjust)-count,len(stock)-adjust,1-self.rlPercent/100)
        #     #I know this doesn't provide enough statistical analysis, I will improve on it more in the future
        #     if pValue > self.rlPercent/100:
        #         setattr(self.backTestCheck, 'color', (0, 1, 0, 1)) #Green
        #         setattr(self.backTestCheck, 'text', "PASSED: " + str(round(pValue*100, 0)) + "% (p-value)")
        #     else:
        #         setattr(self.backTestCheck, 'color', (1, 0, 0, 1)) #Red
        #         setattr(self.backTestCheck, 'text', "FAILED: " + str(round(pValue*100, 0)) + "% (p-value)")

#       def convMonteCarloSim(self, totalValue, stocks):
            # start = time.time()

            # store = JsonStore('holdings.json')
            # weightings = np.zeros(len(stocks['Adj Close'].columns))
            # for x, stockKey in enumerate(store):
            #     stockData = store.get(stockKey)
            #     currentPrice = stocks['Adj Close'][stockData['ticker']].loc[stocks['Adj Close'][stockData['ticker']].last_valid_index()]
            #     currentValue = currentPrice * float(stockData['sharesOwned'])
            #     weightings[x] = currentValue / totalValue

            # closeDiffs = stocks['Adj Close'].pct_change(fill_method=None).dropna()
            # simNum = 10000
            # convThreshold = 0.0075
            # previousVar = float('inf')
            # converged = False

            # while not converged and simNum <= 100000:            
            #     portfoReturns = np.zeros(simNum)
            #     optimisedSim = np.random.multivariate_normal(closeDiffs.mean().values, closeDiffs.cov().values, (self.timeHori, simNum))

            #     weightings = weightings.reshape(1, -1)
            #     portfoReturns = np.sum(optimisedSim * weightings, axis=2)

            #     currentVar = -np.percentile(sorted(portfoReturns), 100 * self.rlPercent)

            #     if previousVar != float('inf') and abs((currentVar - previousVar) / previousVar) < convThreshold:
            #         converged = True
            #     else:
            #         previousVar = currentVar
            #         simNum += 5000

            # end = time.time()
            # print(f"Monte Carlo Sim Speed: {end - start} seconds")
            # return "{:,.2f}".format(currentVar * totalValue)

        





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
        canvas.mpl_connect("motion_notify_event", self.mouseHover)

        self.fig.tight_layout()
        self.currentSymbol = currentSymbol
        
        self.ids.graphSection.add_widget(canvas)


    def showPopup(self, x, y):
        if y.is_integer():
            text = f"{self.currentSymbol}{int(y):,}"
        else:
            text = f"{self.currentSymbol}{y:,.2f}"

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        x_rel = (x - xlim[0]) / (xlim[1] - xlim[0])
        y_rel = (y - ylim[0]) / (ylim[1] - ylim[0])
    
        # Have self tested these, they are different to the last way but work perfect for this section
        if x_rel < 0.5: # Left half
            xOffset = 10
        else: # Right half
            xOffset = -40

        if y_rel < 0.5: # Bottom half
            yOffset = 20
        else: # Top half
            yOffset = -40
    
        self.infoPopup.xy = (x, y)
        self.infoPopup.set_position((xOffset, yOffset))
        self.infoPopup.set_text(text)
        self.infoPopup.set_visible(True)
        self.fig.canvas.draw_idle()

    def hidePopup(self):
        self.infoPopup.set_visible(False)
        self.fig.canvas.draw_idle()

    def mouseHover(self, event):
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
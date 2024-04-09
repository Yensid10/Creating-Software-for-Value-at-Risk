from kivy.uix.screenmanager import Screen
import matplotlib.pyplot as plt
from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import numpy as np
from kivy.storage.jsonstore import JsonStore
import yfinance as yf
import threading
from kivy.clock import mainthread, Clock
import logging
from scipy.stats import binom
logging.getLogger('matplotlib').setLevel(logging.INFO)

# Contains code inspired by: https://stackoverflow.com/a/55184676
class Graphs(Screen):

    @property
    def portfolio(self): # Used for self.portfolio possibly being used in other functions
        return self.manager.get_screen('Portfolio') if self.manager else None
    
    @property
    def varChecker(self):  # Used for self.varChecker possibly being used in other functions
        return self.manager.get_screen('VaRChecker') if self.manager else None
    
    def checkForStocks(func): # Used to make sure that certain graphs cannot be run if there are no stocks in the portfolio
        def wrapper(*args, **kwargs):
            holdings = JsonStore('holdings.json')
            if len(holdings) == 0:
                print("Cannot create graph due to lack of stocks in portfolio.")
                return
            return func(*args, **kwargs)
        return wrapper

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.infoPopup = None 
        self.currentLine = None
        self.graph4Running = False # Used to check if the respective threads for each graph is already being ran
        self.graph5Running = False 
        self.graph6Running = False 
        Clock.schedule_once(lambda dt: self.graph1(), 0) # This is used to run the first graph as soon as the portfolio screen is loaded



    @checkForStocks
    def graph1(self): # Theoretical Portfolio Value Over Time
        stocks = self.portfolio.tempDownload
        store = JsonStore('holdings.json')

        closePrices = stocks['Close'].tail(500)
    
        totalValues = []
        for i in range(len(closePrices)):
            dailyTotal = 0
            row = closePrices.iloc[i]
            for stockKey in store:
                stockData = store.get(stockKey)
                if len(store) != 1:
                    currentPrice = row[stockData['ticker']]
                else:
                    currentPrice = row
                dailyTotal += currentPrice * float(stockData['sharesOwned'])
            totalValues.append(dailyTotal)

        # Done with 10 day intervals because it looks sufficient for what this is trying to show
        x = list(range(500, 0, -10))
        y = totalValues[::10]
        y = self.replaceNan(y) # Intuitively replace nan figures so the graph looks complete
        y = [round(num) for num in y]
        y[-1] = round(self.portfolio.tempTotalValue) # Sets the final value to be what is displayed on the portfolio screen for consistency

        self.createGraph(x, y, 'Last 500 Days', 'Total Theoretical Portfolio Value (£)', 'Theoretical Portfolio Value Over Time With Current Shares', '£', 'red')



    @checkForStocks
    def graph2(self): # Portfolio Stocks Ranked by VaR
        stocks = self.portfolio.tempDownload # Doesn't need threading because it doesn't need to re-download anything
        store = JsonStore('holdings.json')
        if len(store) == 1: # Pointless to show a ranking of 1 stock
            print("Cannot create rankings graph due to lack of stocks in portfolio.")
            return

        # Create a map between stock tickers and names
        tickerToName = {stock: store.get(stock)['name'].split("(")[0].strip() for stock in stocks.columns.levels[1]}

        VaRs = {}
        for stock in stocks.columns.levels[1]:  # iterate over tickers
            VaRs[tickerToName[stock]] = float(self.portfolio.varCalc.modelSim(100, stocks['Adj Close'][stock]))  # name is the key

        sortedVar = dict(sorted(VaRs.items(), key=lambda item: item[1])) # sort the dictionary by value
        self.createRankingGraph(list(sortedVar.keys()), list(sortedVar.values()), 'Portfolio Stocks Ranked by VaR (Best-Worst)', 'Value at Risk Percentage (%)', 'Ranking Portfolio Stocks based on their Value at Risk', 'blue')



    @checkForStocks
    def graph3(self): # Individual Share Pricing Over Time
        tempStockInfo = self.portfolio.tempStockInfo
        if tempStockInfo is None: # Makes sure a stock is selected on the portfolio screen
            self.graph3Ref.text = "[color=ff0000]Please [u]Select a Stock[/u] on the [b]Portfolio Screen[/b] First![/color]"
            Clock.schedule_once(lambda dt: setattr(self.graph3Ref, 'text', "[b][u]Current Stock History[/u][/b]\n [color=ff0000]Select Stock in Portfolio Tab[/color]"), 3)
        else:
            stocks = self.portfolio.tempDownload
            store = JsonStore('holdings.json')

            if len(store) != 1: # Needs to be called differently if there's only 1 stock being stored
                closePrices = stocks['Close'][tempStockInfo['ticker']].tail(500)
            else:
                closePrices = stocks['Close'].tail(500)

            totalValues = []
            for i in range(len(closePrices)): 
                dailyTotal = 0
                row = closePrices.iloc[i] 
                for stockKey in store:
                    stockData = store.get(stockKey)
                    if stockData['ticker'] == tempStockInfo['ticker']:
                        dailyTotal += row
                totalValues.append(dailyTotal)

            # Same as graph 1
            x = list(range(500, 0, -10))
            y = totalValues[::10]
            y = self.replaceNan(y)
            y = [round(num, 2) for num in y]
            y[-1] = round(self.portfolio.tempCurrentPrice, 2) 

            self.createGraph(x, y, 'Last 500 Days', self.portfolio.tempStockInfo['ticker'] + ' Share Value (£)', self.portfolio.tempStockInfo['name'].split("(", 1)[0] + 'Individual Share Pricing Over Time', '£', '#F4743B')



    @checkForStocks
    def graph4(self): # Monte Carlo Simulation Convergence Analysis
        if not self.graph4Running:
            self.graph4Running = True
            thread = threading.Thread(target=self.monteCarloSimConvAnalysis)
            thread.daemon = True
            thread.start()

    def monteCarloSimConvAnalysis(self): 
        stocks = self.portfolio.tempDownload
        store = JsonStore('holdings.json')
        if len(store) == 1: # Monte Carlo Simulation doesn't work with 1 stock
            print("Cannot create rankings graph due to lack of stocks in portfolio.")
            return
        totalValue = float(self.portfolio.tempTotalValue)

        weightings = np.zeros(len(stocks['Close'].columns))
        for x, stockKey in enumerate(store):
            stockData = store.get(stockKey)
            currentPrice = stocks['Close'][stockData['ticker']].loc[stocks['Close'][stockData['ticker']].last_valid_index()]
            currentValue = currentPrice * float(stockData['sharesOwned'])
            weightings[x] = currentValue / totalValue

        closeDiffs = stocks['Close'].pct_change(fill_method=None).dropna()
        
        checkpoints = list(range(500, 25500, 500)) # Iteration checkpoints to check for convergence, 25000 seems to always produce a good visual result
        varResults = [np.nan] # Helps me set the first value to not be plotted, but to show the right x coordinate on the graph

        for sim in checkpoints:
            # Generate all simulations at once
            optimisedSim = np.random.multivariate_normal(closeDiffs.mean(), closeDiffs.cov(), (self.portfolio.varCalc.timeHori, sim))
            portfoReturns = np.zeros(sim)

            # Vectorisation + adapted to fit time horizon
            weightings = weightings.reshape(1, -1)
            portfoReturns = np.sum(optimisedSim * weightings, axis=-1)

            VaR = np.percentile(portfoReturns, 100 * self.portfolio.varCalc.rlPercent) * totalValue
            varResults.append(round(-VaR))
        
        checkpoints.insert(0, 0) # x-axis starts at 0
        self.graph4Running = False
        self.createGraph(checkpoints, varResults, 'Number of Simulations', 'Value at Risk (£)', 'Convergence Analysis of Monte Carlo Simulation Based on Current Portfolio', "£", 'purple')



    def graph5(self): # FTSE100 Stocks Ranked by VaR
        if not self.graph5Running:
            self.graph5Running = True
            thread = threading.Thread(target=self.ftse100Ranking) # Needs threading since it takes time to download the stock information for 100 stocks
            thread.daemon = True
            thread.start()
    
    def ftse100Ranking(self):
        ftse100 = [ticker + ".L" for ticker in self.varChecker.ftse100['Ticker'].tolist()]
        ftse100Names = self.varChecker.ftse100['Company'].tolist()
        tickerToName = dict(zip(ftse100, ftse100Names))  # mapping between tickers and names
    
        stockData = yf.download(ftse100, period="500d")
        VaRs = {}
        for stock in stockData.columns.levels[1]:  # iterate over stock tickers
            VaRs[tickerToName[stock]] = float(self.portfolio.varCalc.modelSim(100, stockData['Adj Close'][stock])) # If you use 100, it will just generate a standard percentage
    
        sortedVar = dict(sorted(VaRs.items(), key=lambda item: item[1])) # sort the dictionary by value
        self.graph5Running = False
        self.createRankingGraph(list(sortedVar.keys()), list(sortedVar.values()), 'FTSE100 Stocks Ranked by VaR (Best-Worst)', 'Value at Risk Percentage (%)', 'Ranking FTSE100 Stocks based on their Value at Risk', 'black')



    @checkForStocks
    def graph6(self): # Monte Carlo Simulation Backtesting
        if not self.graph6Running:
            self.graph6Running = True # Done to check that it doesn't run this same code again when pressed and create multiple instances, it also stops other threads from running at the same time as well
            thread = threading.Thread(target=self.monteCarloSimBackTest)
            thread.daemon = True
            thread.start()

    def monteCarloSimBackTest(self):
        store = JsonStore('holdings.json')
        if len(store) == 1: # Monte Carlo Simulation doesn't work with 1 stock
            print("Cannot create rankings graph due to lack of stocks in portfolio.")
            return
        print("Back-Test Started!")
        stocks = self.portfolio.tempDownload
        totalValue = float(self.portfolio.tempTotalValue)
        count = 0
        adjust = int(len(stocks)/10) # Works the same way as it did for my VaR checker
        VaRs = []
        pDifferences = []
        weightings = np.zeros(len(stocks['Adj Close'].columns))
        for x, stockKey in enumerate(store):
            stockData = store.get(stockKey)
            currentPrice = stocks['Adj Close'][stockData['ticker']].loc[stocks['Adj Close'][stockData['ticker']].last_valid_index()]
            currentValue = currentPrice * float(stockData['sharesOwned'])
            weightings[x] = currentValue / totalValue
        

        for i in range(1, len(stocks) - adjust - 1): # Changed this to increment differently to generate faster, but it didn't look as good
            closeDiffs = stocks['Adj Close'].pct_change(fill_method=None).dropna()
            simNum = 10000
            convThreshold = 0.001
            previousVar = float('inf')
            converged = False
    
            while not converged and simNum <= 100000:            
                portfoReturns = np.zeros(simNum)
                optimisedSim = np.random.multivariate_normal(closeDiffs.mean().values, closeDiffs.cov().values, (self.portfolio.varCalc.timeHori, simNum))
    
                weightings = weightings.reshape(1, -1)
                portfoReturns = np.sum(optimisedSim * weightings, axis=-1)
    
                currentVar = -np.percentile(portfoReturns, 100 * self.portfolio.varCalc.rlPercent)
    
                if previousVar != float('inf') and abs((currentVar - previousVar) / previousVar) < convThreshold:
                    converged = True
                else:
                    previousVar = currentVar
                    simNum += 5000
    
            VaR = -currentVar*100 # Not multiplied by portfolio to give a percentage (negative because its the possible loss you could have, so comparing that to the actual losses, it would be negative)
            VaRs.append(VaR)

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
            pDifferences.append(percentageDifference)
    
            if not np.isnan(percentageDifference) and VaR > percentageDifference:
                count += 1
            
        # Calculate p-value
        pValue = binom.cdf(count, len(VaRs), 1-self.portfolio.varCalc.rlPercent)
        
        # Print statistical analysis
        if pValue > self.portfolio.varCalc.rlPercent/100:
            print("PASSED: " + str(round(pValue*100, 0)) + "% (p-value)")
        else:
            print("FAILED: " + str(round(pValue*100, 0)) + "% (p-value)")
        # I know this is not displayed in a graph, but I wanted to still check, and due to the nature of Monte Carlo sim, it does not pass backtesting when the portfolio is too diverse, so even though smaller portfolio's and backtesting for single stock, I don't think its worth showing that it fails backtesting, as it is expected for well diversified ones
        self.graph6Running = False
        self.backTestGraph(range(462, 0, -1), VaRs, pDifferences, 'Last 450 Days', 'Value at Risk vs Percentage Difference (%)', 'Monte Carlo Simulation Back-Test Comparing 50 Day Rolling Window of VaR to Daily Percentage Difference')




    @mainthread
    def createGraph(self, x, y, xlabel, ylabel, title, currentSymbol, colour):
        self.ids.graphSection.clear_widgets() # Clears the graph section to make way for the new graph
        self.fig, self.ax = plt.subplots()
        self.currentLine, = self.ax.plot(x, y, 'o-', color=colour)

        if x[0] > x[-1]: # If the x-axis is in descending order, set the ticks to be in descending order
            xTicks = np.arange(x[0], -1, -max(x[0] // 5, 20)) 
            xTicks = np.append(xTicks, 0) 
        else: # If the x-axis is in ascending order, set the ticks to be in ascending order
            xTicks = np.linspace(start=min(x), stop=max(x), num=min(len(x), 5))

        self.ax.set_xticks(xTicks)
        self.ax.set_xticklabels([str(int(tick)) for tick in xTicks])

        # Only invert the x-axis if the first values are in descending order
        if x[0] > x[-1]:
            self.ax.invert_xaxis()

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        
        self.infoPopup = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->")) # Initialise infoPopup
        self.infoPopup.set_visible(False)

        canvas = FigureCanvasKivyAgg(self.fig) 
        canvas.mpl_connect("motion_notify_event", self.mouseHover) # Connects the mouseHover function to the canvas

        self.fig.tight_layout() # Makes sure the graph fits the canvas
        self.currentSymbol = currentSymbol # Used to display the current symbol in the popup
        
        self.ids.graphSection.add_widget(canvas)

    def showPopup(self, x, y):
        if y.is_integer(): # If the y value is an integer, display it as an integer, otherwise display it as a float
            text = f"{self.currentSymbol}{int(y):,}"
        else:
            text = f"{self.currentSymbol}{y:,.2f}"

        # Checks the relative position of the point within the axes
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        relativeX = (x - xlim[0]) / (xlim[1] - xlim[0])
        relativeY = (y - ylim[0]) / (ylim[1] - ylim[0])
    
        # Have self tested these, they are different to the last way but work perfect for this section
        if relativeX < 0.5: # Left half
            xOffset = 10
        else: # Right half
            xOffset = -40

        if relativeY < 0.5: # Bottom half
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
        if event.inaxes == self.ax: # If the mouse is in the axes
            cont, ind = self.currentLine.contains(event) # Check if the mouse is on the line
            if cont: # If so...
                pos = ind['ind'][0] # Get the position of the mouse on the line
                x, y = self.currentLine.get_data() # and the x and y values
                self.showPopup(x[pos], y[pos]) # and show the popup
            else:
                self.hidePopup() # If the mouse is not on the line, hide the popup



    @mainthread
    def createRankingGraph(self, tickers, vars, xlabel, ylabel, title, colour): # Needed to use different logic for this
        self.ids.graphSection.clear_widgets()
        self.fig, self.ax = plt.subplots()
        self.currentLine, = self.ax.plot(range(len(vars)), vars, 'o-', color=colour)
    
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        self.ax.set_xticks([])  # Hide x-axis ticks and labels as they are not needed for a ranking
    
        self.infoPopup = self.ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points", bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        self.infoPopup.set_visible(False)
    
        self.tickerHover = tickers  # Save the tickers for the hover function
    
        canvas = FigureCanvasKivyAgg(self.fig)
        canvas.mpl_connect("motion_notify_event", self.rankingOnHover)
        self.fig.tight_layout()
        self.ids.graphSection.add_widget(canvas)

    def rankingOnHover(self, event):
        if event.inaxes == self.ax:
            cont, ind = self.currentLine.contains(event)
            if cont:
                pos = ind['ind'][0]
                tickerName = self.tickerHover[pos]  # Access the corresponding ticker value
                self.showRanking(tickerName, event.xdata, event.ydata) # Show the popup with this different data
            else:
                self.hidePopup() # Can still use the previous hidePopup function

    def showRanking(self, tickerName, x, y): 
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        relativeX = (x - xlim[0]) / (xlim[1] - xlim[0])
        relativeY = (y - ylim[0]) / (ylim[1] - ylim[0])
    
        # Have self tested these, they appear to be perfect
        if relativeX < 0.5: # Left half
            xOffset = -10
        else: # Right half
            xOffset = -95

        if relativeY < 0.5: # Bottom half
            yOffset = 60
        else: # Top half
            yOffset = -30
    
        # # Update the position of the annotation text
        self.infoPopup.xy = (x, y)
        self.infoPopup.set_position((-x + xOffset, -y + yOffset)) # I think this overly complicates it, but it works
        self.infoPopup.set_text(f"Stock: {tickerName}")
        self.infoPopup.set_visible(True)
        self.fig.canvas.draw_idle()



    @mainthread 
    def backTestGraph(self, x, y1, y2, xlabel, ylabel, title): # Needs again different logic, due to no hover and drawing 2 lines
        self.ids.graphSection.clear_widgets()
        self.fig, self.ax = plt.subplots()
        self.ax.plot(x, y1, 'o-', color='blue', label='Value at Risk (%)') # Plot the first line
        self.ax.plot(x, y2, 'o-', color='red', label='Daily Percentage Difference (%)') # Plot the second line

        xTicks = np.arange(450, -1, -50)
        self.ax.set_xticks(xTicks)
        self.ax.set_xticklabels([str(int(tick)) for tick in xTicks])

        if x[0] > x[-1]:
            self.ax.invert_xaxis()

        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        self.ax.legend() # Add a legend to the graph

        canvas = FigureCanvasKivyAgg(self.fig)
        self.fig.tight_layout()        
        self.ids.graphSection.add_widget(canvas)



    def replaceNan(self, y): # Used to replace nan values in the y list intuitively
        for i in range(len(y)):
            if np.isnan(y[i]):
                if i == 0: # If the first value is nan
                    nextValue = next((y[j] for j in range(i + 1, len(y)) if not np.isnan(y[j])), None)
                    nextNextValue = next((y[j] for j in range(i + 2, len(y)) if not np.isnan(y[j])), None)
                    if nextValue is not None and nextNextValue is not None: # If the next value and the value after that are not nan, set the first value to be the average between the two, taken away from the last non-nan value
                        y[i] = nextValue - (nextNextValue - nextValue)
                else: # If the nan is not the first value
                    prevValue = next((y[j] for j in range(i - 1, -1, -1) if not np.isnan(y[j])), None)
                    nextValue = next((y[j] for j in range(i + 1, len(y)) if not np.isnan(y[j])), None)
                    if prevValue is not None and nextValue is not None: # And the previous and next values are not nan, set the value to be the average of the two
                        y[i] = (prevValue + nextValue) / 2 
                    if np.isnan(y[-1]): # If the last value is nan
                        lastNoneNan = next((y[i] for i in range(len(y) - 2, -1, -1) if not np.isnan(y[i])), None) 
                        if lastNoneNan is not None: # If the value before the last nan value is not nan, set the last value to be the average of this value and the last y value, since I have set it to be what is displayed on the portfolio screen
                            y[-1] = (lastNoneNan + y[-1]) / 2
        return y
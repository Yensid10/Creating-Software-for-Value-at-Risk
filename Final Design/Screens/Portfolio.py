from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
import yfinance as yf
from kivy.clock import Clock, ClockEvent
import numpy as np
from scipy.stats import norm
import time
import matplotlib.pyplot as plt
import logging

class Portfolio(Screen):
    stockCards = ObjectProperty(None)
    stockName = ObjectProperty(None)
    totalValue = ObjectProperty(None)
    totalReturn = ObjectProperty(None)
    totalShares = ObjectProperty(None)
    dailyVaR = ObjectProperty(None)
    tempStockInfo = None
    iSTCheck = None
    sSTCheck = None
    returnButton = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.varCalc = VaRCalculators()
        self.loadStocks()
        self.initialStockTotals()

    def openPopup(self):
        popup = InputStock()
        popup.bind(on_dismiss=self.loadStocks)
        popup.bind(on_dismiss=self.initialStockTotals)
        popup.open()

    def addStock(self, stockData):
        stockCard = Stocks(portfolio=self, **stockData)
        self.ids.stockCards.add_widget(stockCard)

    def loadStocks(self, *args):
        store = JsonStore('holdings.json')
        # Clear existing stock widgets
        self.ids.stockCards.clear_widgets()

        # Load existing stocks and display them
        for stockKeys in store:
            stockData = store.get(stockKeys)
            self.addStock(stockData)

    def initialStockTotals(self, *args):
        if isinstance(self.sSTCheck, ClockEvent):
            Clock.unschedule(self.sSTCheck)
            self.sSTCheck = None

        if not isinstance(self.iSTCheck, ClockEvent):
            self.iSTCheck = Clock.schedule_interval(self.initialStockTotals, 60)
        store = JsonStore('holdings.json')

        if hasattr(self, 'returnButton'):  # Check if the returnButton exists
            self.returnButton.opacity = 0
            self.returnButton.disabled = True

        if len(store) != 0:
            totalValue = 0
            totalCurrentPrices = 0
            totalInitialPrices = 0
            totalShares = 0

            start = time.time()
            stocks = yf.download([store.get(stockKey)['ticker'] for stockKey in store], period='500d')
            end = time.time()
            print(f"Initial Stock Totals Speed: {end - start} seconds")

            for stockKeys in store:
                stockData = store.get(stockKeys)
                currentPrice = stocks['Close'][stockData['ticker']].loc[stocks['Close'][stockData['ticker']].last_valid_index()]
                totalValue = totalValue + (currentPrice * float(stockData['sharesOwned']))
                totalCurrentPrices = totalCurrentPrices + currentPrice
                totalInitialPrices = totalInitialPrices + float(stockData['initialPrice'])
                totalShares = totalShares + int(stockData['sharesOwned'])
            
            totalReturn = ((totalCurrentPrices / totalInitialPrices) - 1) * 100
            self.stockName.text = "[u]Total Portfolio Value[/u]"
            self.totalValue.text = "Total Value: £{:,.2f}".format(totalValue)
            self.totalReturn.text = "Total Return: {:.2f}%".format(totalReturn)
            self.totalShares.text = f"Total No. of Shares: {totalShares}"
            self.dailyVaR.text = f"Value at Risk: £{self.varCalc.convMonteCarloSim(totalValue, stocks)}"

            # Option to perform Monte Carlo Simulation visual convergence analysis below
            # Clock.unschedule(self.iSTCheck)
            # self.iSTCheck = None
            # self.varCalc.monteCarloSimAnalysis(totalValue, stocks)

    def specificStockTotals(self, *args):
        if isinstance(self.iSTCheck, ClockEvent):
            Clock.unschedule(self.iSTCheck)
            self.iSTCheck = None

        if not isinstance(self.sSTCheck, ClockEvent):
            self.sSTCheck = Clock.schedule_interval(self.specificStockTotals, 60)

        self.returnButton.opacity = 1
        self.returnButton.disabled = False
        
        stocks = yf.download([self.tempStockInfo['ticker']], period='500d')

        currentPrice = stocks['Close'].loc[stocks['Close'].last_valid_index()]
        totalValue = currentPrice * float(self.tempStockInfo['sharesOwned'])
        totalReturn = ((currentPrice / self.tempStockInfo['initialPrice']) - 1) * 100

        self.stockName.text = "[u]" + self.tempStockInfo['ticker'] + " Stock Value[/u]"
        self.totalValue.text = "Current Value: £{:,.2f}".format(totalValue)
        self.totalReturn.text = "Current Return: {:.2f}%".format(totalReturn)
        self.totalShares.text = f"No. of Shares: {self.tempStockInfo['sharesOwned']}"
        self.dailyVaR.text = f"Value at Risk: £{self.varCalc.modelSim(totalValue, stocks)}"



class VaRCalculators:
    rlPercent = 0.05
    timeHori = 1

    def __init__(self, *args):
        pass

    # def monteCarloSim(self, totalValue, stocks):
    #     start = time.time()
    #     store = JsonStore('holdings.json')
    #     weightings = np.zeros(len(stocks['Close'].columns))

    #     for x, stockKey in enumerate(store):
    #         stockData = store.get(stockKey)
    #         currentPrice = stocks['Close'][stockData['ticker']].loc[stocks['Close'][stockData['ticker']].last_valid_index()]
    #         currentValue = currentPrice * float(stockData['sharesOwned'])
    #         weightings[x] = currentValue / totalValue

    #     closeDiffs = stocks['Close'].pct_change(fill_method=None).dropna()
    #     simNum = 10000
    #     portfoReturns = np.zeros(simNum)

    #     # Massive optimisation here, I generate all the simulations at once, rather than one at a time, using (timeHori, simNum)!
    #     optimisedSim = np.random.multivariate_normal(closeDiffs.mean(), closeDiffs.cov(), (self.timeHori, simNum)) 
    #     for x in range(simNum): 
    #         portfoReturns[x] = np.sum(np.sum(optimisedSim[:, x, :] * weightings, axis=1))
        
    #     end = time.time()
    #     print(f"Monte Carlo Sim Speed: {end - start} seconds")
    #     return "{:,.2f}".format(-np.percentile(sorted(portfoReturns), 100 * self.rlPercent)*totalValue)
    
    def convMonteCarloSim(self, totalValue, stocks):
        start = time.time()

        store = JsonStore('holdings.json')
        weightings = np.zeros(len(stocks['Close'].columns))
        for x, stockKey in enumerate(store):
            stockData = store.get(stockKey)
            currentPrice = stocks['Close'][stockData['ticker']].loc[stocks['Close'][stockData['ticker']].last_valid_index()]
            currentValue = currentPrice * float(stockData['sharesOwned'])
            weightings[x] = currentValue / totalValue

        closeDiffs = stocks['Close'].pct_change(fill_method=None).dropna()
        simNum = 5000
        convThreshold = 0.005
        previousVar = float('inf')
        converged = False

        while not converged and simNum <= 100000:            
            portfoReturns = np.zeros(simNum)
            optimisedSim = np.random.multivariate_normal(closeDiffs.mean().values, closeDiffs.cov().values, (self.timeHori, simNum))

            for x in range(simNum):
                portfoReturns[x] = np.sum(np.sum(optimisedSim[:, x, :] * weightings, axis=1))

            currentVar = -np.percentile(sorted(portfoReturns), 100 * self.rlPercent)

            if previousVar != float('inf') and abs((currentVar - previousVar) / previousVar) < convThreshold:
                converged = True
            else:
                previousVar = currentVar
                simNum += 5000

        end = time.time()
        print(f"Monte Carlo Sim Speed: {end - start} seconds")
        return "{:,.2f}".format(currentVar * totalValue)

    def monteCarloSimAnalysis(self, totalValue, stocks):
        store = JsonStore('holdings.json')
        weightings = np.zeros(len(stocks['Close'].columns))

        for x, stockKey in enumerate(store):
            stockData = store.get(stockKey)
            currentPrice = stocks['Close'][stockData['ticker']].loc[stocks['Close'][stockData['ticker']].last_valid_index()]
            currentValue = currentPrice * float(stockData['sharesOwned'])
            weightings[x] = currentValue / totalValue

        closeDiffs = stocks['Close'].pct_change(fill_method=None).dropna()
        
        checkpoints = list(range(500, 10500, 500)) # Iteration checkpoints to check for convergence 
        varResults = []

        for sim in checkpoints:
            # Generate all simulations at once
            optimisedSim = np.random.multivariate_normal(closeDiffs.mean(), closeDiffs.cov(), (self.timeHori, sim))
            portfoReturns = np.zeros(sim)

            for x in range(sim):
                portfoReturns[x] = np.sum(np.sum(optimisedSim[:, x, :] * weightings, axis=1))

            # Calculate VaR at this checkpoint
            VaR = np.percentile(sorted(portfoReturns), 100 * self.rlPercent) * totalValue
            varResults.append(-VaR)
        

        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        # Plotting the convergence of VaR
        plt.plot(checkpoints, varResults, marker='o')
        plt.xlabel('Number of Simulations')
        plt.ylabel('Value at Risk (VaR)')
        plt.title('Convergence Analysis of Monte Carlo Simulation')
        plt.grid(True)
        plt.show()

    
    def modelSim(self, totalValue, stocks): # Needs some back-testing implemented
        closeDiffs = stocks['Close'].pct_change(fill_method=None).dropna()
        return "{:,.2f}".format((-totalValue*norm.ppf(self.rlPercent/100, np.mean(closeDiffs), np.std(closeDiffs)))*np.sqrt(self.timeHori))

class Stocks(Button):
    def __init__(self, portfolio, ticker, sharesOwned, initialPrice, **kwargs):
        super().__init__(**kwargs)
        self.currentPortfolio = portfolio
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = "113sp"

        self.text = f"ticker: {ticker}"

        self.stockInfo = {
            'ticker': ticker,
            'sharesOwned': sharesOwned,
            'initialPrice': initialPrice
        }

    def on_release(self):
        print(self.stockInfo)
        self.currentPortfolio.tempStockInfo = self.stockInfo  # Update tempStockInfo in Portfolio
        self.currentPortfolio.specificStockTotals()

class InputStock(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.5, 0.5)
        self.title = 'Create/Update Holding'

    def saveStock(self):
        # Generate Initial Stock Info
        stocks = yf.download([self.inputTicker.text], period='1d')
        initialPrice = stocks['Close'].loc[stocks['Close'].last_valid_index()]

        stockData = {
            'ticker': self.inputTicker.text,
            'sharesOwned': self.inputShares.text,
            'initialPrice': initialPrice,
        }
        JsonStore('holdings.json').put(stockData['ticker'], **stockData) # Save to JSONStore, basically caching the data 
        print(f"Added new holding: {stockData}") 
        self.dismiss()

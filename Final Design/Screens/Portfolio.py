from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
import yfinance as yf
from kivy.clock import Clock, ClockEvent
import numpy as np
from scipy.stats import norm
import time
import matplotlib.pyplot as plt
import logging
from bs4 import BeautifulSoup
import requests

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
    deleteButton = ObjectProperty(None)

    logging.getLogger('yfinance').setLevel(logging.WARNING)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.varCalc = VaRCalculators()
        self.initialStockTotals()

    def handle_popup_dismiss(self, value):
        self.initialStockTotals()

    def openPopup(self):
        popup = InputStock()
        popup.dismiss_handler = self.handle_popup_dismiss
        popup.open() 

    def addStock(self, stockData, currentPrice):
        stockCard = Stocks(portfolio=self, **stockData, currentPrice=currentPrice)
        self.ids.stockCards.add_widget(stockCard)

    def loadStocks(self, stocks):
        store = JsonStore('holdings.json')
        # Clear existing stock widgets
        self.ids.stockCards.clear_widgets()

        # Load existing stocks and display them
        for stockKeys in store:
            stockData = store.get(stockKeys)
            currentPrice = stocks['Close'][stockData['ticker']].loc[stocks['Close'][stockData['ticker']].last_valid_index()]
            self.addStock(stockData, currentPrice)

    def deleteStock(self):
        store = JsonStore('holdings.json')
        store.delete(self.tempStockInfo['ticker'])
        self.initialStockTotals()

    def initialStockTotals(self, *args):
        if isinstance(self.sSTCheck, ClockEvent):
            Clock.unschedule(self.sSTCheck)
            self.sSTCheck = None

        if not isinstance(self.iSTCheck, ClockEvent):
            self.iSTCheck = Clock.schedule_interval(self.initialStockTotals, 60)
        store = JsonStore('holdings.json')

        self.returnButton.opacity = 0
        self.deleteButton.opacity = 0
        self.returnButton.disabled = True
        self.deleteButton.disabled = True


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
                totalValue += (currentPrice * float(stockData['sharesOwned']))
                totalCurrentPrices += currentPrice * float(stockData['sharesOwned'])
                totalInitialPrices += float(stockData['initialPrice']) * float(stockData['sharesOwned'])
                totalShares += int(stockData['sharesOwned'])

            totalReturn = ((totalCurrentPrices / totalInitialPrices) - 1) * 100

            self.stockName.text = "[u]Total Portfolio Value[/u]"
            self.totalValue.text = "Total Value: £{:,.2f}".format(totalValue)
            self.totalReturn.text = f"Total Return: {totalReturn:.2f}% / £{totalCurrentPrices - totalInitialPrices:,.2f}"
            self.totalShares.text = f"Total No. of Shares: {totalShares}"

            VaR = self.varCalc.convMonteCarloSim(totalValue, stocks)
            self.dailyVaR.text = f"Value at Risk: {(float(VaR) / totalValue) * 100:.2f}% / £{VaR}"

            self.loadStocks(stocks)

            # Option to perform Monte Carlo Simulation visual convergence analysis below
            # Clock.unschedule(self.iSTCheck)
            # self.iSTCheck = None
            # self.varCalc.monteCarloSimVisualisation(totalValue, stocks)

    def specificStockTotals(self, *args):
        if isinstance(self.iSTCheck, ClockEvent):
            Clock.unschedule(self.iSTCheck)
            self.iSTCheck = None

        if not isinstance(self.sSTCheck, ClockEvent):
            self.sSTCheck = Clock.schedule_interval(self.specificStockTotals, 60)

        self.returnButton.opacity = 1
        self.deleteButton.opacity = 1
        self.returnButton.disabled = False
        self.deleteButton.disabled = False
        
        store = JsonStore('holdings.json')
        stocks = yf.download([store.get(stockKey)['ticker'] for stockKey in store], period='500d')

        currentPrice = stocks['Close'][self.tempStockInfo['ticker']].loc[stocks['Close'][self.tempStockInfo['ticker']].last_valid_index()]
        totalValue = currentPrice * float(self.tempStockInfo['sharesOwned'])
        totalReturn = ((currentPrice / self.tempStockInfo['initialPrice']) - 1) * 100
        totalReturnMoney = totalValue - (self.tempStockInfo['initialPrice'] * float(self.tempStockInfo['sharesOwned']))

        self.stockName.text = "[u]" + self.tempStockInfo['ticker'] + " Stock Value[/u]"
        self.totalValue.text = "Current Value: £{:,.2f}".format(totalValue)
        self.totalReturn.text = f"Total Return: {totalReturn:.2f}% / £{totalReturnMoney:,.2f}"
        self.totalShares.text = f"No. of Shares: {self.tempStockInfo['sharesOwned']}"

        VaR = self.varCalc.modelSim(totalValue, stocks['Close'][self.tempStockInfo['ticker']])
        self.dailyVaR.text = f"Value at Risk: {(float(VaR) / totalValue) * 100:.2f}% / £{VaR}"

        self.loadStocks(stocks)

class VaRCalculators:
    rlPercent = 0.05
    timeHori = 1

    def __init__(self, *args):
        pass
    
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
        simNum = 10000
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

    def monteCarloSimVisualisation(self, totalValue, stocks):
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
        closeDiffs = stocks.pct_change(fill_method=None).dropna()
        return "{:,.2f}".format((-totalValue*norm.ppf(self.rlPercent/100, np.mean(closeDiffs), np.std(closeDiffs)))*np.sqrt(self.timeHori))

class Stocks(Button):
    def __init__(self, portfolio, name, ticker, sharesOwned, initialPrice, currentPrice, **kwargs):
        super().__init__(**kwargs)
        self.currentPortfolio = portfolio
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = "110sp"
        self.background_normal = ''  # remove default background image
        self.background_color = (1, 1, 1, 1)  # white
        self.color = (0, 0, 0, 1)
        self.font_size = "20sp"

        self.text = f"{name}: £{currentPrice:,.2f}"

        self.stockInfo = {
            'name': name,
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
        self.size_hint = (0.5, 0.4)
        self.title = '                                   Create/Update Holding' # Centers title
        self.dismiss_handler = None

    def findCompanyName(self, ticker):
        yFinancePage = f"https://finance.yahoo.com/quote/{ticker}"
        headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    } # I don't know why this makes it work for certain stocks but it does, so great!!
        response = requests.get(yFinancePage, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        companyName = soup.find('h1', class_='D(ib) Fz(18px)')
        if companyName:
            return companyName.text
        return None

    def saveStock(self):
        # Generate Initial Stock Info
        stocks = yf.download([self.inputTicker.text], period='1d')
        initialPrice = stocks['Close'].loc[stocks['Close'].last_valid_index()]

        stockData = {
            'name': self.findCompanyName(self.inputTicker.text),
            'ticker': self.inputTicker.text,
            'sharesOwned': self.inputShares.text,
            'initialPrice': initialPrice,
        }
        JsonStore('holdings.json').put(stockData['ticker'], **stockData) # Save to JSONStore, basically caching the data 
        print(f"Added new holding: {stockData}") 
        self.dismiss_handler(1)
        self.dismiss()

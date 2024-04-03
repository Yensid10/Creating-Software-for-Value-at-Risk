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

class Portfolio(Screen):
    stockCards = ObjectProperty(None)
    stockName = ObjectProperty(None)
    totalValue = ObjectProperty(None)
    totalReturn = ObjectProperty(None)
    totalShares = ObjectProperty(None)
    dailyVaR = ObjectProperty(None)
    stockInfo = None
    iSTCheck = None
    sSTCheck = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loadStocks()
        self.initialStockTotals()

        # test1 = yf.download(['AAPL'], period='1d').tail(1)['Close'].iloc[0]
        # print(test1)

    def openPopup(self):
        popup = InputStock()
        popup.bind(on_dismiss=self.loadStocks)
        popup.bind(on_dismiss=self.initialStockTotals)
        popup.open()

    def addStock(self, stockData):
        stockCard = Stocks(portfolio=self, **stockData)
        self.ids.stockCards.add_widget(stockCard)

    def loadStocks(self, *args):
        print("Loading stocks")
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
            self.iSTCheck = Clock.schedule_interval(self.initialStockTotals, 10)
        store = JsonStore('holdings.json')

        if len(store) != 0:
            totalValue = 0
            totalCurrentPrices = 0
            totalInitialPrices = 0
            totalShares = 0

            for stockKeys in store:
                stockData = store.get(stockKeys)
                currentPrice = yf.download([stockData['ticker']], period='1d').tail(1)['Close'].iloc[0]
                totalValue = totalValue + (currentPrice * float(stockData['sharesOwned']))
                totalCurrentPrices = totalCurrentPrices + currentPrice
                totalInitialPrices = totalInitialPrices + float(stockData['initialPrice'])
                totalShares = totalShares + int(stockData['sharesOwned'])
            
            print(totalCurrentPrices, totalInitialPrices)
            totalReturn = ((totalCurrentPrices / totalInitialPrices) - 1) * 10
            self.stockName.text = "[u]Total Portfolio Value[/u]"
            self.totalValue.text = "Total Value: £{:,.2f}".format(totalValue)
            self.totalReturn.text = "Total Return: {:.2f}%".format(totalReturn)
            self.totalShares.text = f"Total No. of Shares: {totalShares}"
        

    def specificStockTotals(self, *args):
        if self.stockInfo is None:
                    return

        if isinstance(self.iSTCheck, ClockEvent):
            Clock.unschedule(self.iSTCheck)
            self.iSTCheck = None

        if not isinstance(self.sSTCheck, ClockEvent):
            self.sSTCheck = Clock.schedule_interval(self.specificStockTotals, 10)
        
        currentPrice = yf.download([self.stockInfo['ticker']], period='1d').tail(1)['Close'].iloc[0]
        totalValue = currentPrice * float(self.stockInfo['sharesOwned'])
        totalReturn = ((currentPrice / self.stockInfo['initialPrice']) - 1) * 10

        self.stockName.text = "[u]" + self.stockInfo['ticker'] + " Stock Value[/u]"
        self.totalValue.text = "Current Value: £{:,.2f}".format(totalValue)
        self.totalReturn.text = "Current Return: {:.2f}%".format(totalReturn)
        self.totalShares.text = f"Current No. of Shares: {self.stockInfo['sharesOwned']}"
        # self.dailyVaR.text = f"5% Daily VaR (£): {stockInfo['currentVaR']}"

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
        self.currentPortfolio.stockInfo = self.stockInfo  # Update stockInfo in Portfolio
        self.currentPortfolio.specificStockTotals()

class InputStock(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.5, 0.5)
        self.title = 'New Holding'

    def saveStock(self):
        # Generate Initial Stock Info
        initialPrice = yf.download([self.inputTicker.text], period='1d').tail(1)['Close'].iloc[0]

        stockData = {
            'ticker': self.inputTicker.text,
            'sharesOwned': self.inputShares.text,
            'initialPrice': initialPrice,
        }
        JsonStore('holdings.json').put(stockData['ticker'], **stockData) # Save to JSONStore, basically caching the data 
        print(f"Added new holding: {stockData}") 
        self.dismiss()



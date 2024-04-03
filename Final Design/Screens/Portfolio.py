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
from kivy.clock import Clock

class Portfolio(Screen):
    stockCards = ObjectProperty(None)
    stockName = ObjectProperty(None)
    totalValue = ObjectProperty(None)
    dailyReturn = ObjectProperty(None)
    totalShares = ObjectProperty(None)
    dailyVaR = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loadStocks()
        Clock.schedule_interval(self.loadStocks, 10)

    def openPopup(self):
        popup = InputStock()
        popup.bind(on_dismiss=self.loadStocks)
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

    def updateTotals(self, totalStockInfo):
        self.stockName.text = totalStockInfo['ticker']
        # self.totalValue.text = f"Total Value (£): {totalStockInfo['totalPrice']}"
        # self.dailyReturn.text = f"Daily Return (%): {totalStockInfo['dailyReturns']}"
        self.totalShares.text = f"Total No. of Shares: {totalStockInfo['overallShares']}"
        # self.dailyVaR.text = f"5% Daily VaR (£): {totalStockInfo['currentVaR']}"

class Stocks(Button):
    def __init__(self, portfolio, ticker, overallShares, **kwargs):
        super().__init__(**kwargs)
        self.currentPortfolio = portfolio
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = "113sp"

        self.text = f"ticker: {ticker}"

        self.stockInfo = {
            'ticker': ticker,
            'overallShares': overallShares,
        }

    def on_release(self):
        print(self.stockInfo)
        self.currentPortfolio.updateTotals(self.stockInfo)

class InputStock(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.5, 0.5)
        self.title = 'New Holding'

    def saveStock(self):
        # Generate Initial Stock Info


        stockData = {
            'ticker': self.inputTicker.text,
            'overallShares': self.inputShares.text,
        }
        JsonStore('holdings.json').put(stockData['ticker'], **stockData) # Save to JSONStore, basically caching the data 
        print(f"Added new holding: {stockData['ticker']}") # Current form of verification that it has added properly, add some stuff to make sure they can only input certain bits of information
        self.dismiss()



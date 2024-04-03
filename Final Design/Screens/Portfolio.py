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

    def openPopup(self):
        popup = InputStock()
        popup.bind(on_dismiss=self.loadStocks)
        popup.open()

    def addStock(self, stockData):
        stockCard = Stocks(**stockData)
        self.ids.stockCards.add_widget(stockCard)

    def loadStocks(self, *args):
        store = JsonStore('holdings.json')
        # Clear existing stock widgets
        self.ids.stockCards.clear_widgets()

        # Load existing stocks and display them
        for stockKeys in store:
            stockData = store.get(stockKeys)
            self.addStock(stockData)

    # def updateTotals(self, totalStockInfo): # Currently updates the right hand stuff on the screen, but I need it to not use these exact values the way they are currently being used, I need to link it all to yahoo finance and get it to calculate all the data properly!
    #     self.stockName.text = totalStockInfo['name']
    #     self.totalValue.text = f"Total Value (£): {totalStockInfo['totalPrice']}"
    #     self.dailyReturn.text = f"Daily Return (%): {totalStockInfo['dailyReturns']}"
    #     self.totalShares.text = f"Total No. of Shares: {totalStockInfo['overallShares']}"
    #     self.dailyVaR.text = f"5% Daily VaR (£): {totalStockInfo['currentVaR']}"

class Stocks(Button):
    def __init__(self, ticker, overallShares, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = "113sp"

        self.text = f"ticker: {ticker}"

        self.stockInfo = {
            'ticker': ticker,
            'overallShares': overallShares,
        }

    def on_release(self):
        pass

class InputStock(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.5, 0.5)
        self.title = 'New Holding'

    def saveStock(self):
        stockData = {
            'ticker': self.inputTicker.text,
            'overallShares': self.inputShares.text,
        }
        JsonStore('holdings.json').put(stockData['ticker'], **stockData) # Save to JSONStore, basically caching the data 
        print(f"Added new holding: {stockData['ticker']}") # Current form of verification that it has added properly, add some stuff to make sure they can only input certain bits of information
        self.dismiss()



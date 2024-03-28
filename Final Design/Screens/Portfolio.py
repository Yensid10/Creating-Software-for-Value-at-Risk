from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore

class Portfolio(Screen):
    store = JsonStore('holdings.json')
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
        self.popup = InputStock(self.addStock)
        self.popup.open()

    def addStock(self, stockData):
        stockCard = Stocks(updateCallback=self.updateTotals, **stockData)
        self.ids.stockCards.add_widget(stockCard)
        self.store.put(stockData['name'], **stockData) # Save to JSONStore, basically caching the data 
        print(f"Added new holding: {stockData['name']}") # Current form of verification that it has added properly, add some stuff to make sure they can only input certain bits of information


    def loadStocks(self):
        # Load existing stocks and display them
        for stockKeys in self.store:
            stockData = self.store.get(stockKeys)
            self.addStock(stockData)

    def updateTotals(self, totalStockInfo): # Currently updates the right hand stuff on the screen, but I need it to not use these exact values the way they are currently being used, I need to link it all to yahoo finance and get it to calculate all the data properly!
        self.stockName.text = totalStockInfo['name']
        self.totalValue.text = f"Total Value (£): {totalStockInfo['totalPrice']}"
        self.dailyReturn.text = f"Daily Return (%): {totalStockInfo['dailyReturns']}"
        self.totalShares.text = f"Total No. of Shares: {totalStockInfo['overallShares']}"
        self.dailyVaR.text = f"5% Daily VaR (£): {totalStockInfo['currentVaR']}"

class Stocks(Button):
    def __init__(self, name, totalPrice, overallShares, dailyReturns, currentVaR, updateCallback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = "113sp"
        self.add_widget(Label(text=f"Name: {name}", size_hint_y=None))
        self.updateCallback = updateCallback

        self.totalStockInfo = {
            'name': name,
            'totalPrice': totalPrice,
            'overallShares': overallShares,
            'dailyReturns': dailyReturns,
            'currentVaR': currentVaR
        }

    def on_release(self):
        self.updateCallback(self.totalStockInfo)

class InputStock(Popup):
    def __init__(self, addStockCallback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (.5, .5)
        self.title = 'New Holding'
        
        data = BoxLayout(orientation='vertical', spacing=5, padding=5)
        self.inputName = TextInput(hint_text='Name', size_hint_y=None, height=30)
        self.inputPrice = TextInput(hint_text='Total Price', size_hint_y=None, height=30)
        self.inputShares = TextInput(hint_text='Total No. of Shares', size_hint_y=None, height=30)
        self.inputReturns = TextInput(hint_text='Daily Return (%)', size_hint_y=None, height=30)
        self.inputVaR = TextInput(hint_text='VaR as percent Portfolio', size_hint_y=None, height=30)
        # I need to remove most of these from the input popup, but at the moment I just need to check that I can store, update and everything else for this stuff.
        
        saveButton = Button(text='Save', size_hint_y=None, height=30)
        saveButton.bind(on_release=lambda instance: self.saveStock(addStockCallback))
        
        data.add_widget(self.inputName)
        data.add_widget(self.inputPrice)
        data.add_widget(self.inputShares)
        data.add_widget(self.inputReturns)
        data.add_widget(self.inputVaR)
        data.add_widget(saveButton)
        
        self.data = data

    def saveStock(self, addStockCallback):
        stockData = {
            'name': self.inputName.text,
            'totalPrice': self.inputPrice.text,
            'overallShares': self.inputShares.text,
            'dailyReturns': self.inputReturns.text,
            'currentVaR': self.inputVaR.text
        }
        addStockCallback(stockData)
        self.dismiss()



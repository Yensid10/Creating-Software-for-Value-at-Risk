from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
import yfinance as yf
from kivy.clock import Clock, ClockEvent
import numpy as np
from scipy.stats import norm
import logging
from bs4 import BeautifulSoup
import requests
from kivy.animation import Animation

class Portfolio(Screen):
    tempStockInfo = None
    iSTCheck = None
    sSTCheck = None
    tempDownload = None
    tempTotalValue = None
    tempCurrentPrice = None
    
    logging.getLogger('yfinance').setLevel(logging.WARNING)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.varCalc = VaRCalculators()
        self.initialStockTotals()

    def handlePopupDismiss(self, value):
        self.initialStockTotals()

    def openPopup(self):
        popup = InputStock()
        popup.dismissHandler = self.handlePopupDismiss
        popup.open() 

    def adjDeleteHandler(self):
        if self.adjDeleteButton.text == "Adjust VaR":
            popup = AdjustVaRPopup(portfolio=self, varCalc=self.varCalc, var=self.dailyVaR.text)            
        else:
            popup = ConfirmDelete(portfolio=self, ticker=self.tempStockInfo['ticker'])
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
            if len(store) != 1:
                currentPrice = stocks['Adj Close'][stockData['ticker']].loc[stocks['Adj Close'][stockData['ticker']].last_valid_index()]
            else:
                currentPrice = stocks['Adj Close'].loc[stocks['Adj Close'].last_valid_index()]
            self.addStock(stockData, currentPrice)        

    def initialStockTotals(self, *args):
        if isinstance(self.sSTCheck, ClockEvent):
            Clock.unschedule(self.sSTCheck)
            self.sSTCheck = None

        if not isinstance(self.iSTCheck, ClockEvent):
            self.iSTCheck = Clock.schedule_interval(self.initialStockTotals, 60)
        store = JsonStore('holdings.json')
        if len(store) == 0:
            self.stockName.text = "[u][b]PORTFOLIO[/u][/b]"
            self.totalValue.text = "Total Value: [b]£0.00[/b]"
            self.totalReturn.text = "Total Return: [color=ffffff]0.00% / £0.00[/color]"
            self.totalShares.text = "Total No. of Shares: 0"
            self.dailyVaR.text = "[b]Value at Risk: 0.00% / £0.00[/b]"
            self.tempTotalValue = None
            self.loadStocks(None)

        self.returnButton.opacity = 0
        self.returnButton.disabled = True
        self.adjDeleteButton.text = "Adjust VaR"
        self.tempStockInfo = None


        anime = Animation(rgba=[0.25, 0.25, 0.25, 1], duration=0.5)
        anime.start(self.rightSide.canvas.before.children[0])


        if len(store) != 0:
            totalValue = 0
            totalCurrentPrices = 0
            totalInitialPrices = 0
            totalShares = 0

            stocks = yf.download([store.get(stockKey)['ticker'] for stockKey in store], period='500d')
            self.tempDownload = stocks

            for stockKeys in store:
                stockData = store.get(stockKeys)
                if len(store) != 1:
                    currentPrice = stocks['Adj Close'][stockData['ticker']].loc[stocks['Adj Close'][stockData['ticker']].last_valid_index()]
                else:
                    currentPrice = stocks['Adj Close'].loc[stocks['Adj Close'].last_valid_index()]
                totalValue += (currentPrice * float(stockData['sharesOwned']))
                totalCurrentPrices += currentPrice * float(stockData['sharesOwned'])
                totalInitialPrices += float(stockData['initialPrice']) * float(stockData['sharesOwned'])
                totalShares += int(stockData['sharesOwned'])

            self.tempTotalValue = totalValue
            totalReturn = ((totalCurrentPrices / totalInitialPrices) - 1) * 100
            totalReturnColor = 'ff3333ff' if totalReturn < 0 else ('ffffff' if totalReturn == 0 else '00e000')
            if totalReturn < 0.01 and totalReturn > 0: totalReturn = "<0.01"
            elif totalReturn > -0.01 and totalReturn < 0: totalReturn = "<-0.01"
            else: totalReturn = "{:.2f}".format(totalReturn)

            self.stockName.text = "[u][b]PORTFOLIO[/u][/b]"
            self.totalValue.text = "Total Value: [b]£{:,.2f}".format(totalValue)+"[/b]"
            self.totalReturn.text = f"Total Return: [color={totalReturnColor}]{totalReturn}% / £{totalCurrentPrices - totalInitialPrices:,.2f}[/color]"
            self.totalShares.text = f"Total No. of Shares: {float(totalShares):,.0f}"


            if len(store) != 1:
                VaR = self.varCalc.convMonteCarloSim(totalValue, stocks)
            else:
                VaR = self.varCalc.modelSim(totalValue, stocks['Close'])
            self.dailyVaR.text = f"[b]Value at Risk: {(float(VaR.replace(',', '')) / totalValue) * 100:.2f}% / £{VaR[:-3]}[/b]"

            self.loadStocks(stocks)


    def specificStockTotals(self, *args):
        if isinstance(self.iSTCheck, ClockEvent):
            Clock.unschedule(self.iSTCheck)
            self.iSTCheck = None

        if not isinstance(self.sSTCheck, ClockEvent):
            self.sSTCheck = Clock.schedule_interval(self.specificStockTotals, 60)

        self.returnButton.opacity = 1
        self.returnButton.disabled = False
        self.adjDeleteButton.text = "Delete Stock"

        anime = Animation(rgba=[0.35, 0.35, 0.35, 1], duration=0.5)
        anime.start(self.rightSide.canvas.before.children[0])
        
        store = JsonStore('holdings.json')
        stocks = yf.download([store.get(stockKey)['ticker'] for stockKey in store], period='500d')
        self.tempDownload = stocks

        if len(store) != 1:
            currentPrice = stocks['Close'][self.tempStockInfo['ticker']].loc[stocks['Close'][self.tempStockInfo['ticker']].last_valid_index()]
        else:
            currentPrice = stocks['Close'].loc[stocks['Close'].last_valid_index()]
        self.tempCurrentPrice = currentPrice
        totalValue = currentPrice * float(self.tempStockInfo['sharesOwned'])
        totalReturn = ((currentPrice / self.tempStockInfo['initialPrice']) - 1) * 100
        totalReturnMoney = totalValue - (self.tempStockInfo['initialPrice'] * float(self.tempStockInfo['sharesOwned']))

        totalReturnColor = 'ff3333ff' if totalReturn < 0 else ('ffffff' if totalReturn == 0 else '00e000')
        if totalReturn < 0.01 and totalReturn > 0: totalReturn = "<0.01"
        elif totalReturn > -0.01 and totalReturn < 0: totalReturn = "<-0.01"
        else: totalReturn = "{:.2f}".format(totalReturn)

        self.stockName.text = "[u][b]" + self.tempStockInfo['ticker'] + "[/u][/b]"
        self.totalValue.text = "Current Share Price: £{:,.2f}".format(currentPrice)
        self.totalReturn.text = f"Total Return: [color={totalReturnColor}]{totalReturn}% / £{totalReturnMoney:,.2f}[/color]"
        self.totalShares.text = f"No. of Shares: {float(self.tempStockInfo['sharesOwned']):,.0f}"

        if len(store) != 1:            
            VaR = self.varCalc.modelSim(totalValue, stocks['Close'][self.tempStockInfo['ticker']])
        else:
            VaR = self.varCalc.modelSim(totalValue, stocks['Close'])
        self.dailyVaR.text = f"[b]Value at Risk: {(float(VaR.replace(',', '')) / totalValue) * 100:.2f}% / £{VaR[:-3]}[/b]"

        self.loadStocks(stocks)







class VaRCalculators:
    rlPercent = None
    timeHori = None

    def __init__(self, *args):
        self.rlPercent = 0.05
        self.timeHori = 1
    
    def convMonteCarloSim(self, totalValue, stocks):
        store = JsonStore('holdings.json')
        weightings = np.zeros(len(stocks['Adj Close'].columns))
        for x, stockKey in enumerate(store):
            stockData = store.get(stockKey)
            currentPrice = stocks['Adj Close'][stockData['ticker']].loc[stocks['Adj Close'][stockData['ticker']].last_valid_index()]
            currentValue = currentPrice * float(stockData['sharesOwned'])
            weightings[x] = currentValue / totalValue

        closeDiffs = stocks['Adj Close'].pct_change(fill_method=None).dropna()
        simNum = 10000
        convThreshold = 0.001
        previousVar = float('inf')
        converged = False

        while not converged and simNum <= 100000:            
            portfoReturns = np.zeros(simNum)
            optimisedSim = np.random.multivariate_normal(closeDiffs.mean().values, closeDiffs.cov().values, (self.timeHori, simNum))

            weightings = weightings.reshape(1, -1)
            portfoReturns = np.sum(optimisedSim * weightings, axis=-1)

            currentVar = -np.percentile(portfoReturns, 100 * self.rlPercent)

            if previousVar != float('inf') and abs((currentVar - previousVar) / previousVar) < convThreshold:
                converged = True
            else:
                previousVar = currentVar
                simNum += 5000

        return "{:,.2f}".format(currentVar * totalValue)


    def modelSim(self, totalValue, stocks): # Needs some back-testing implemented
        closeDiffs = stocks.pct_change(fill_method=None).dropna()
        return "{:,.2f}".format((-totalValue*norm.ppf(self.rlPercent, np.mean(closeDiffs), np.std(closeDiffs)))*np.sqrt(self.timeHori)) # The /100 was ruining this whole thing :(((
    





class Stocks(GridLayout):
    def __init__(self, portfolio, name, ticker, sharesOwned, initialPrice, currentPrice, **kwargs):
        super().__init__(**kwargs)
        self.currentPortfolio = portfolio
        self.cols = 2
        self.size_hint_y = None
        self.height = "110sp"
        
        nameLabel = Label(
            text=name,
            markup=True,
            halign='right',
            valign='middle',
            text_size=("300sp", None), 
            size_hint_x=None,
            width="303sp",
            color=(0, 0, 0, 1),
            font_size="21.5sp"
        )
        nameLabel.bind(size=nameLabel.setter('text_size'))
        
        priceLabel = Label(
            text=f"[b]: £{currentPrice*float(sharesOwned):,.2f}[/b]",
            halign='left',
            valign='middle',
            text_size=("200sp", None),
            size_hint_x=None,
            width="200sp",
            markup=True,
            color=(0, 0, 0, 1),
            font_size="20sp"
        )
        priceLabel.bind(size=priceLabel.setter('text_size'))

        self.add_widget(nameLabel)
        self.add_widget(priceLabel)

        self.stockInfo = {
            'name': name,
            'ticker': ticker,
            'sharesOwned': sharesOwned,
            'initialPrice': initialPrice
        }

    def on_touch_down(self, touch): # Has to be called this, its a kivy thing
        if self.collide_point(*touch.pos):
            self.currentPortfolio.tempStockInfo = self.stockInfo
            self.currentPortfolio.specificStockTotals()
        return super().on_touch_down(touch)






class InputStock(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dismissHandler = None

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
        sharesCheck = True
        self.inputTicker.text = self.inputTicker.text.strip()
        if self.inputTicker.text == "":
            stocks = None        
        else:
            stocks = yf.download(self.inputTicker.text.capitalize(), period='1d')
        if self.inputShares.text == "":
            self.inputShares.text = "0"

        if int(self.inputShares.text) <= 0:
            self.inputShares.text = ""
            self.inputShares.hint_text = "Invalid Shares"
            self.inputShares.background_color = [1, 0.6, 0.6, 1]
            anime = Animation(background_color=[1, 1, 1, 1], duration=1)
            anime.start(self.inputShares)
            self.inputShares.focus = True
            sharesCheck = False

        try:
            initialPrice = stocks['Adj Close'].loc[stocks['Adj Close'].last_valid_index()]
        except:
            self.inputTicker.text = ""
            self.inputTicker.hint_text = "Invalid Ticker"
            self.inputTicker.background_color = [1, 0.6, 0.6, 1]
            anime = Animation(background_color=[1, 1, 1, 1], duration=1)
            anime.start(self.inputTicker)
            self.inputTicker.focus = True
            sharesCheck = False
        
        if sharesCheck:
            stockData = {
                'name': self.findCompanyName(self.inputTicker.text),
                'ticker': self.inputTicker.text.upper(),
                'sharesOwned': self.inputShares.text,
                'initialPrice': initialPrice,
            }
            JsonStore('holdings.json').put(stockData['ticker'], **stockData)
            print(f"Added new holding: {stockData}") 
            self.dismissHandler(1)
            self.dismiss()





class ConfirmDelete(Popup):
    def __init__(self, portfolio, ticker=None,  **kwargs):
        super().__init__(**kwargs)
        self.ticker = ticker
        self.currentPortfolio = portfolio

    def on_confirm(self):
        JsonStore('holdings.json').delete(self.ticker)
        self.currentPortfolio.initialStockTotals()
        self.dismiss()




class AdjustVaRPopup(Popup):
    def __init__(self, portfolio, varCalc, var, **kwargs):
        super().__init__(**kwargs)
        self.varCalc = varCalc
        self.currentPortfolio = portfolio
        self.varLabel.text = f"There is a [color=ff8000]{int(self.varCalc.rlPercent * 100)}%[/color] chance that my portfolio could \nlose more than [b]{var.rsplit(' ', 1)[-1]}[/b] in the next [color=00AAff]{self.varCalc.timeHori}[/color] day(s)."

    def submit(self):
        inputCheck = True
        if not self.timeHoriInput.text.isdigit() or not (1 <= int(self.timeHoriInput.text) <= 30):
            self.timeHoriInput.text = ""
            self.timeHoriInput.hint_text = "Invalid Horizon [1-30]"
            self.timeHoriInput.background_color = [1, 0.6, 0.6, 1]
            anime = Animation(background_color=[1, 1, 1, 1], duration=1)
            anime.start(self.timeHoriInput)
            self.timeHoriInput.focus = True
            inputCheck = False
        else:
            self.varCalc.timeHori = int(self.timeHoriInput.text)

        try:
            rlPercent = float(self.riskLevelInput.text)
            if not (0 < rlPercent <= 50):
                raise Exception
        except:
            self.riskLevelInput.text = ""
            self.riskLevelInput.hint_text = "Invalid Percentage [1-50]"
            self.riskLevelInput.background_color = [1, 0.6, 0.6, 1]
            anime = Animation(background_color=[1, 1, 1, 1], duration=1)
            anime.start(self.riskLevelInput)
            self.riskLevelInput.focus = True
            inputCheck = False
        else:
            self.varCalc.rlPercent = rlPercent / 100.0
        if inputCheck:
            self.currentPortfolio.initialStockTotals()
            self.dismiss()


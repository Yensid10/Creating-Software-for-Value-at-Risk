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
logging.getLogger('yfinance').setLevel(logging.WARNING)

class Portfolio(Screen):
    tempStockInfo = None # Used to store the info of whatever stock is clicked on
    iSTCheck = None # Used to stop blocking of the initialStockTotals function
    sSTCheck = None # Used to stop blocking of the specificStockTotals function
    tempDownload = None # Used to store the download of the stocks to be referenced in another screen
    tempTotalValue = None # Used to store the total value of the portfolio to be referenced in another screen
    tempCurrentPrice = None # Used to store the current price of a stock to be referenced in another screen

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.varCalc = VaRCalculators() 
        self.initialStockTotals() # Initialises the portfolio and repeats every 60 seconds, also runs loadStocks

    def handlePopupDismiss(self, value):
        self.initialStockTotals() # I callback to make this happen when a add stock pop-up is saved successfully

    def openPopup(self):
        popup = InputStock()
        popup.dismissHandler = self.handlePopupDismiss
        popup.open() 

    def adjDeleteHandler(self): # Used to handle the adjust VaR and delete stock buttons
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
            if len(store) != 1: # I use variations of this code a lot since you need to call the code differently when there is one stock in the portfolio
                currentPrice = stocks['Adj Close'][stockData['ticker']].loc[stocks['Adj Close'][stockData['ticker']].last_valid_index()]
            else:
                currentPrice = stocks['Adj Close'].loc[stocks['Adj Close'].last_valid_index()]
            self.addStock(stockData, currentPrice)        

    def initialStockTotals(self, *args):
        if isinstance(self.sSTCheck, ClockEvent): # Stops the blocking of the specificStockTotals function
            Clock.unschedule(self.sSTCheck)
            self.sSTCheck = None

        if not isinstance(self.iSTCheck, ClockEvent): 
            self.iSTCheck = Clock.schedule_interval(self.initialStockTotals, 60) # Repeats every 60 seconds

        store = JsonStore('holdings.json')
        if len(store) == 0: # If there are no stocks in the portfolio
            self.stockName.text = "[u][b]PORTFOLIO[/u][/b]"
            self.totalValue.text = "Total Value: [b]£0.00[/b]"
            self.totalReturn.text = "Total Return: [color=ffffff]0.00% / £0.00[/color]"
            self.totalShares.text = "Total No. of Shares: 0"
            self.dailyVaR.text = "[b]Value at Risk: 0.00% / £0.00[/b]"
            self.tempTotalValue = None
            self.loadStocks(None) # Clears the stock widgets since it isn't called after a delete if there are no stocks

        # Reset the portfolio to its original state
        self.returnButton.opacity = 0
        self.returnButton.disabled = True
        self.adjDeleteButton.text = "Adjust VaR"
        self.tempStockInfo = None

        # Animate the background colour of the right side of the screen to a slightly darker shade
        anime = Animation(rgba=[0.25, 0.25, 0.25, 1], duration=0.5)
        anime.start(self.rightSide.canvas.before.children[0])


        if len(store) != 0: # If there are stocks in the portfolio
            totalValue = 0
            totalCurrentPrices = 0
            totalInitialPrices = 0
            totalShares = 0

            stocks = yf.download([store.get(stockKey)['ticker'] for stockKey in store], period='500d') # Downloads the stocks for the portfolio all at once
            self.tempDownload = stocks

            for stockKeys in store: # Generates the necessary values to be displayed
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
            totalReturnColor = 'ff3333ff' if totalReturn < 0 else ('ffffff' if totalReturn == 0 else '00e000') # Determines the colour of the total return text, using red for negative, green for positive and white for no change
            if totalReturn < 0.01 and totalReturn > 0: totalReturn = "<0.01" # This is to prevent 0.00% from being green and vice-versa for -0.00%
            elif totalReturn > -0.01 and totalReturn < 0: totalReturn = "<-0.01"
            else: totalReturn = "{:.2f}".format(totalReturn)

            self.stockName.text = "[u][b]PORTFOLIO[/u][/b]"
            self.totalValue.text = "Total Value: [b]£{:,.2f}".format(totalValue)+"[/b]"
            self.totalReturn.text = f"Total Return: [color={totalReturnColor}]{totalReturn}% / £{totalCurrentPrices - totalInitialPrices:,.2f}[/color]"
            self.totalShares.text = f"Total No. of Shares: {float(totalShares):,.0f}"


            if len(store) != 1: # You can't run Monte Carlo simulations on a single stock, so this helps to determine which method to use
                VaR = self.varCalc.convMonteCarloSim(totalValue, stocks)
            else:
                VaR = self.varCalc.modelSim(totalValue, stocks['Adj Close'])
            self.dailyVaR.text = f"[b]Value at Risk: {(float(VaR.replace(',', '')) / totalValue) * 100:.2f}% / £{VaR[:-3]}[/b]"

            self.loadStocks(stocks)


    def specificStockTotals(self, *args): # Temporary Stock Info was passed in from the stocks class
        if isinstance(self.iSTCheck, ClockEvent):
            Clock.unschedule(self.iSTCheck)
            self.iSTCheck = None

        if not isinstance(self.sSTCheck, ClockEvent):
            self.sSTCheck = Clock.schedule_interval(self.specificStockTotals, 60)

        self.returnButton.opacity = 1
        self.returnButton.disabled = False
        self.adjDeleteButton.text = "Delete Stock"

        anime = Animation(rgba=[0.35, 0.35, 0.35, 1], duration=0.5) # Slightly brighter shade of grey
        anime.start(self.rightSide.canvas.before.children[0])
        
        store = JsonStore('holdings.json')
        stocks = yf.download([store.get(stockKey)['ticker'] for stockKey in store], period='500d') # Still downloads all the stocks, since I may need them in my graphs screen
        self.tempDownload = stocks

        if len(store) != 1:
            currentPrice = stocks['Adj Close'][self.tempStockInfo['ticker']].loc[stocks['Adj Close'][self.tempStockInfo['ticker']].last_valid_index()]
        else:
            currentPrice = stocks['Adj Close'].loc[stocks['Adj Close'].last_valid_index()]
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
            VaR = self.varCalc.modelSim(totalValue, stocks['Close'][self.tempStockInfo['ticker']]) # Has to be called differently for single stock as well
        else:
            VaR = self.varCalc.modelSim(totalValue, stocks['Close'])
        self.dailyVaR.text = f"[b]Value at Risk: {(float(VaR.replace(',', '')) / totalValue) * 100:.2f}% / £{VaR[:-3]}[/b]"

        self.loadStocks(stocks)







class VaRCalculators:
    def __init__(self, *args):
        self.rlPercent = 0.05 # Default values
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
        simNum = 10000 # Good initial starting simulation amount
        convThreshold = 0.001 # The threshold for convergence (percentage, 0.1%)
        previousVar = float('inf')
        converged = False

        while not converged and simNum <= 100000: # Whilst the simulation hasn't converged and the simulation amount is less than 100,000
            portfoReturns = np.zeros(simNum)
            optimisedSim = np.random.multivariate_normal(closeDiffs.mean().values, closeDiffs.cov().values, (self.timeHori, simNum))

            # These are commented on within graphs screen
            weightings = weightings.reshape(1, -1)
            portfoReturns = np.sum(optimisedSim * weightings, axis=-1)

            currentVar = -np.percentile(portfoReturns, 100 * self.rlPercent)

            if previousVar != float('inf') and abs((currentVar - previousVar) / previousVar) < convThreshold:
                converged = True
            else:
                previousVar = currentVar
                simNum += 5000

        return "{:,.2f}".format(currentVar * totalValue)


    def modelSim(self, totalValue, stocks):
        closeDiffs = stocks.pct_change(fill_method=None).dropna()
        return "{:,.2f}".format((-totalValue*norm.ppf(self.rlPercent, np.mean(closeDiffs), np.std(closeDiffs)))*np.sqrt(self.timeHori)) # I had an 100 in this from my VaRChecker producing bad results, but it is working now, also needs to be multiplied by square root of time horizon to get the correct value if time horizon has been adjusted
    





class Stocks(GridLayout):
    def __init__(self, portfolio, name, ticker, sharesOwned, initialPrice, currentPrice, **kwargs):
        super().__init__(**kwargs)
        self.currentPortfolio = portfolio # Passes in the screen to start functions when needed
        self.cols = 2 # So I can align them where I want within the scroll wheel, which is wrapped around the ":"
        self.size_hint_y = None
        self.height = "110sp" # Need to use sp so it adapts to whatever screen size is needed
        
        nameLabel = Label(
            text=name,
            markup=True,
            halign='right',
            valign='middle',
            text_size=("300sp", None), 
            size_hint_x=None,
            width="303sp",
            color=(0, 0, 0, 1),
            font_size="21.5sp" # Slightly bigger to contrast the prices bolding
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

    def on_touch_down(self, touch): # Used to emulate a button, since it is not one now
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
        } # Needed to emulate a User-Agent, as if you are an actual browser accessing the page, since this helps retrieve results from yahoo for non-american stocks, denoted with a "." in the ticker
        response = requests.get(yFinancePage, headers=headers) # I use requests to get the page, since the yfinance function to get the name is currently broken
        soup = BeautifulSoup(response.content, 'html.parser') # I use BeautifulSoup to parse the HTML of the page
        companyName = soup.find('h1', class_='D(ib) Fz(18px)') # When using inspect element on yahoo pages, the name is always within this specific element, so I retrieve it
        if companyName:
            return companyName.text
        return None

    def saveStock(self):
        sharesCheck = True # Very messy use of verification but it makes sure that each input is valid, can be mutually exclusive between the two inputs
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
            anime = Animation(background_color=[1, 1, 1, 1], duration=1) # Animates the background colour back to white, as if flashing to say you have entered the wrong thing
            anime.start(self.inputShares)
            self.inputShares.focus = True # Focuses the user back to this input box, which only works if the above box is correct
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
                'name': self.findCompanyName(self.inputTicker.text), # If the company name was not correct, it wouldn't have been able to download the stock information, so this function should always work
                'ticker': self.inputTicker.text.upper(),
                'sharesOwned': self.inputShares.text,
                'initialPrice': initialPrice,
            }
            JsonStore('holdings.json').put(stockData['ticker'], **stockData)
            print(f"Added new holding: {stockData}")  # Only time I print, since I think its nice to see
            self.dismissHandler(1) # Basically is used to make portfolio run a function in a very specific instance
            self.dismiss()





class ConfirmDelete(Popup):
    def __init__(self, portfolio, ticker=None,  **kwargs):
        super().__init__(**kwargs)
        self.ticker = ticker
        self.currentPortfolio = portfolio

    def on_confirm(self):
        JsonStore('holdings.json').delete(self.ticker)
        self.currentPortfolio.initialStockTotals() # I call this to refresh the portfolio after the stock is deleted
        self.dismiss()




class AdjustVaRPopup(Popup):
    def __init__(self, portfolio, varCalc, var, **kwargs):
        super().__init__(**kwargs)
        self.varCalc = varCalc
        self.currentPortfolio = portfolio
        self.varLabel.text = f"There is a [color=ff8000]{int(self.varCalc.rlPercent * 100)}%[/color] chance that my portfolio could \nlose more than [b]{var.rsplit(' ', 1)[-1]}[/b] in the next [color=00AAff]{self.varCalc.timeHori}[/color] day(s)." # Colours used to make it easier for the user to understand, helps to explain VaR as well

    def submit(self):
        inputCheck = True # Similar sort of verification as before
        if not self.timeHoriInput.text.isdigit() or not (1 <= int(self.timeHoriInput.text) <= 30):
            self.timeHoriInput.text = ""
            self.timeHoriInput.hint_text = "Invalid Horizon [1-30]" # Helps to specify the restrictions after they get something wrong
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
            self.varCalc.rlPercent = rlPercent / 100.0 # Divided by 100 to get the percentage in decimal form
        if inputCheck:
            self.currentPortfolio.initialStockTotals()
            self.dismiss()


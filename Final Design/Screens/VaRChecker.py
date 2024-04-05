from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.screenmanager import Screen
import datetime as dt
import numpy as np
from scipy.stats import norm, binom
import yfinance as yf
import pandas as pd

#Importing the FTSE100 list from Wikipedia
ftse100 = pd.read_html('https://en.wikipedia.org/wiki/FTSE_100_Index')[4]

class VaRChecker(Screen):
    # Declare ObjectProperty variables for the stock list and user inputs, as well as all other variables
    stockList = ObjectProperty(None)
    userInputs = ObjectProperty(None)
    portfolio = 100000000
    rlPercent = 5 #Maybe change to be a slider and change to be certainty level in the future
    timeHori = 1
    simMethod = "Historical"
    currentTicker = ""

    def __init__(self, **kwargs):
        # Call the parent class's constructor
        super(VaRChecker, self).__init__(**kwargs)
        self.populateList()
        self.populateInputs()

    def populateList(self):
        for i in range(len(ftse100)):
            button = Button(text=ftse100['Company'][i], size_hint_y=None, height="30sp", font_size="20sp")
            #Set the currentStock to the stock ticker that is clicked, and save it to the variable
            button.bind(on_release=lambda btn, i=i: (setattr(self.currentStock, 'text', "Stock: " + ftse100['Ticker'][i]), setattr(self, 'currentTicker', str(ftse100['Ticker'][i])))) 
            self.stockList.add_widget(button)

    def simMethodPressed(self, current):
        self.simMethod = current.text
        if current.state == 'normal':
            current.state = 'down'            
            self.populateInputs()
            
    def backTest(self, stock):
        #Taken from Single Stock VaR.py
        count = 0
        adjust = int(len(stock)/10)
        for i in range(1, len(stock) - adjust - 1):
            backTest = stock['Adj Close'].pct_change()[i:i+adjust]
            if self.simMethod == "Historical":
                VaR = np.percentile(backTest, self.rlPercent)*np.sqrt(self.timeHori)*self.portfolio
            else:
                VaR = (-self.portfolio*norm.ppf(self.rlPercent/100, np.mean(backTest), np.std(backTest)))*np.sqrt(self.timeHori)*-1 #Always returns a positive value with model simulation, so needs to be multiplied by -1
            nextDay = stock['Adj Close'].pct_change()[i+adjust:i+adjust+1].values[0]*np.sqrt(self.timeHori)*self.portfolio
            if VaR > nextDay:
                count += 1
        pValue = binom.cdf((len(stock)-adjust)-count,len(stock)-adjust,1-self.rlPercent/100)
        #I know this doesn't provide enough statistical analysis, I will improve on it more in the future
        if pValue > self.rlPercent/100:
            setattr(self.backTestCheck, 'color', (0, 1, 0, 1)) #Green
            setattr(self.backTestCheck, 'text', "PASSED: " + str(round(pValue*100, 0)) + "% (p-value)")
        else:
            setattr(self.backTestCheck, 'color', (1, 0, 0, 1)) #Red
            setattr(self.backTestCheck, 'text', "FAILED: " + str(round(pValue*100, 0)) + "% (p-value)")

    def generateVaR(self):
        #Taken from Single Stock VaR.py
        if self.currentTicker == "":
            setattr(self.valAtRisk, 'text', " VaR: Select a stock")
            return
        endDate = dt.datetime.now()
        startDate = endDate - dt.timedelta(days=1000)
        stock = yf.download(self.currentTicker, startDate, endDate).tail(500) #I chose to default it to 500 days, I may include a slider for days in the future.
        try:
            closeDiffs = stock['Adj Close'].pct_change().dropna()
        except:
            try:
                stock = yf.download(self.currentTicker + ".L", startDate, endDate).tail(500) #Fixed an issue where it would not work for stocks with .L at the end
                closeDiffs = stock['Adj Close'].pct_change().dropna()
            except:
                setattr(self.valAtRisk, 'text', " Stock not found")
                return
        #There were two errors, one where there was only 1 value given from stock, so closeDiffs would be empty, and another one where all the values were the same for all bits of stock data, so all of closeDiffs would be 0, this fixes both.
        if closeDiffs.empty or (closeDiffs == 0).all(): 
            setattr(self.valAtRisk, 'text', " STOCK ERROR")
            return
        if self.simMethod == "Historical":
            # Assuming that N-days VaR = 1-day VaR * sqrt(N)
            VaR = str('{:,}'.format(int(round(np.percentile(closeDiffs, self.rlPercent)*self.portfolio*-1*np.sqrt(self.timeHori), 0)))) #Returns a negative value, so needs to be multiplied by -1
        else:
            VaR = str('{:,}'.format(int(round((-self.portfolio*norm.ppf(self.rlPercent/100, np.mean(closeDiffs), np.std(closeDiffs)))*np.sqrt(self.timeHori), 0))))
        
        setattr(self.valAtRisk, 'text', " VaR: £" + VaR)        
        self.backTest(stock)

    def createButtons(self):
        self.userInputs.add_widget(Label(text="Select Method:", size_hint_y=None, height="30sp", font_size="20sp"))
        radioButtons = BoxLayout(size_hint_y=None, height="35sp", padding=["120sp", 0])
        
        #Historical Simulation Button
        hButton = ToggleButton(text='Historical', group='simMethod', size_hint_x=None, width="100sp")
        hButton.bind(on_press=self.simMethodPressed)
        if self.simMethod == 'Historical':
            hButton.state = 'down'
        else:
            hButton.state = 'normal'
        radioButtons.add_widget(hButton)
        
        #Model Simulation Button
        mButton = ToggleButton(text='Model', group='simMethod', size_hint_x=None, width="100sp")
        mButton.bind(on_press=self.simMethodPressed)
        if self.simMethod == 'Model':
            mButton.state = 'down'
        else:
            mButton.state = 'normal'
        radioButtons.add_widget(mButton)

        self.userInputs.add_widget(radioButtons)
        
    def validateInput(self, current, varName, maxVal):
        try:
            if current.text == "" or int(current.text) < 0:
                raise Exception #This will be caught by the except statement below, defaulting any incorrect values
            if int(current.text) > maxVal:
                setattr(self, varName, maxVal)
            else:            
                setattr(self, varName, int(current.text))
        except:
            if varName == 'portfolio':
                setattr(self, varName, 100000000)
            elif varName == 'rlPercent':
                setattr(self, varName, 5)
            else:
                setattr(self, varName, 1)
        self.populateInputs()

    def populateInputs(self):
        self.userInputs.clear_widgets() #Clears all the widgets in the layout, or they will duplicate
        self.userInputs.add_widget(Label(text="\n", size_hint_y=None, height="5sp", font_size="20sp"))
        # Create a dictionary of variable names and their corresponding displayed texts and max values
        variables = {
            'portfolio': ('Enter Portfolio Value (£): ', '1000000000'),
            'rlPercent': ('Enter Risk Level Percentage (%): ', '50'),
            'timeHori': ('Enter Time Horizon (No. of Days): ', '31')
        }
        for varName, (label, maxVal) in variables.items():
            self.userInputs.add_widget(Label(text=label, size_hint_y=None, height="30sp", font_size="20sp"))
            centeredLayout = BoxLayout(size_hint_y=None, height="30sp", padding=["85sp", 0]) #Padding used to center the text input
            #Needs to set multiline to false or it won't let you use enter to validate         
            text = TextInput(size_hint_x=None, width="275sp", font_size="15sp", multiline=False)
            # text.bind(on_focus=self.onFocus) #Was not working, so will maybe try again in the future
            text.bind(on_text_validate=lambda current, varName=varName, maxVal=int(maxVal): self.validateInput(current, varName, maxVal))
            centeredLayout.add_widget(text)
            self.userInputs.add_widget(centeredLayout)
        
        self.createButtons()
        
        if self.portfolio == 100000000 and self.rlPercent == 5 and self.timeHori == 1:
            self.userInputs.add_widget(Label(text="\n\n\n\n\n[u]Current Info Given (Default)[/u]\n" + f"Portfolio Value: £{'{:,}'.format(self.portfolio)}\n" + f"Risk Level Percentage: {self.rlPercent}%\n" + f"Time Horizon: {self.timeHori} day(s)", size_hint_y=None, height="10sp", markup=True, font_size="20sp", pos_hint={'center_x': 0.3}))
        else:
            self.userInputs.add_widget(Label(text="\n\n\n\n\n[u]Current Info Given[/u]\n" + f"Portfolio Value: £{'{:,}'.format(self.portfolio)}\n" + f"Risk Level Percentage: {self.rlPercent}%\n" + f"Time Horizon: {self.timeHori} day(s)", size_hint_y=None, height="10sp", markup=True, font_size="20sp", pos_hint={'center_x': 0.3}))

        #Adding back-testing title
        floatLayout = FloatLayout()
        label = Label(text='[u]Back-Testing[/u]', pos_hint={'center_x': 0.9, 'center_y': 0.1}, font_size="14sp", markup=True, color=(0, 0, 0, 1))#Using the pos_hint to make sure its in the right place, which it now always is
        floatLayout.add_widget(label)

        # Add the FloatLayout to the userInputs GridLayout so it can be drawn in the right place every time
        self.userInputs.add_widget(floatLayout)
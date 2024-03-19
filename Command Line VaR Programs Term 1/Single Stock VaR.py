import datetime as dt
import time
import numpy as np
from scipy.stats import norm, binom
import yfinance as yf
import pandas as pd



ftse100 = pd.read_html('https://en.wikipedia.org/wiki/FTSE_100_Index')[4]

def VaRCalc(p, rL, mean, sD):
    return -p*(norm.ppf(rL, mean, sD))

print("WELCOME TO THE VAR CALCULATOR\n-----------------------------\nWhich companies stock would you like to calculate the VaR for?")
for i in range(len(ftse100)):
    print(str(i+1) + " - " + ftse100['Company'][i])
    time.sleep(0.005)
    
while True:
    try:
        compIndex = int(input("Enter the number of the company: "))-1
        if compIndex > -1 and compIndex < 100:
            company = ftse100['Ticker'][compIndex]
            break
        print("Please re-enter a valid input")
    except:
        print("Please re-enter a valid input")
        
while True:
    try:
        portfolio = int(input("Enter the portfolio value (£): "))
        if portfolio > 0:
            break
    except:
        print("Please re-enter a valid input")
        
while True:
    try:
        rlPercent = int(input("Enter the risk level percentage (1%, 5%, etc.): "))
        if rlPercent > 0 and rlPercent < 100:
            break
        print("Please re-enter a valid input")
    except:
        print("Please re-enter a valid input")
        
while True:
    try:
        timeHori = int(input("Enter the time horizon (Max: 100 days): "))
        if timeHori > 0 and timeHori < 100:
            break
        print("Please re-enter a valid input")
    except:
        print("Please re-enter a valid input")
        
while True:
    try:
        print("How many days of historical data would you like to use, or would you like to choose your own date boundaries?\n1. 100 days\n2. 500 days\n3. Choose your own")
        data = int(input("Enter the number of your choice: "))
        if data > 0 and data < 4:
            break
        print("Please re-enter a valid input")
    except:
        print("Please re-enter a valid input")
        
if data == 1:
    endDate = dt.datetime.now()
    startDate = endDate - dt.timedelta(days=200)
    adjust = 100
elif data == 2:
    endDate = dt.datetime.now()
    startDate = endDate - dt.timedelta(days=1000)
    adjust = 500
else:
    while True:
        try:
            startDate = input("Enter the start date (YYYY-MM-DD), earliest available is 2010-01-01: ")
            endDate = input("Enter the end date (YYYY-MM-DD): ")
            startDate = dt.datetime(int(startDate[0:4]), int(startDate[5:7]), int(startDate[8:10]))
            endDate = dt.datetime(int(endDate[0:4]), int(endDate[5:7]), int(endDate[8:10]))
            if startDate < endDate & (endDate - startDate).days > timeHori & startDate > dt.datetime(2010, 1, 1):
                adjust = (endDate - startDate).days
                break
            print("Please re-enter a valid input")
        except:
            print("Please re-enter a valid input")
#The adjust is used to make sure that there are 100/500 days of stock data, since it excludes weekends and holidays
stock = yf.download(company, startDate, endDate).tail(adjust)

while True:
    try:
        VaRType = str(input("Would you like to calculate VaR using Historical Simulation, or using Model Building/Variance-Covariance (H/M): "))
        if VaRType == "H" or VaRType == "M" or VaRType == "h" or VaRType == "m":
            break
        print("Please re-enter a valid input")
    except:
        print("Please re-enter a valid input")
        
print()        
closeDiffs = stock['Adj Close'].pct_change().dropna()
if VaRType == "H" or VaRType == "h":
    # Assuming that N-days VaR = 1-day VaR * sqrt(N)
    print("VaR is: £" + str(round(np.percentile(closeDiffs, rlPercent)*portfolio*-1*np.sqrt(timeHori), 2)))
else:
    print("VaR is: £" + str(round(VaRCalc(portfolio, rlPercent/100, np.mean(closeDiffs), np.std(closeDiffs))*np.sqrt(timeHori), 2)))
    
count = 0
adjust = int(len(stock)/10)
for i in range(1, len(stock) - adjust - 1):
    backTest = stock['Adj Close'].pct_change()[i:i+adjust]
    if VaRType == "H" or VaRType == "h":
        VaR = np.percentile(backTest, rlPercent)*np.sqrt(timeHori)*portfolio
    else:
        VaR = VaRCalc(portfolio, rlPercent/100, np.mean(backTest), np.std(backTest))*np.sqrt(timeHori)*-1        
    nextDay = stock['Adj Close'].pct_change()[i+adjust:i+adjust+1].values[0]*np.sqrt(timeHori)*portfolio
    if VaR > nextDay:
        count += 1
        
# failureRate = round(count/(len(stock)-adjust)*100, 1)
pValue = binom.cdf((len(stock)-adjust)-count,len(stock)-adjust,1-rlPercent/100)

if pValue > rlPercent/100:
    print("Back Test: PASSED with " + str(round(pValue*100, 0)) + "% statistical significance level (p-value)")
else:
    print("Back Test: FAILED with " + str(round(pValue*100, 0)) + "% statistical significance level (p-value)")
    
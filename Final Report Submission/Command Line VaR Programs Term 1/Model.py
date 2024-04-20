import datetime as dt
import numpy as np
from scipy.stats import norm
import yfinance as yf

print("Model Building VaR\n")
def dailyVar(P, rl, mean, sD):
    # print(-P*norm.ppf(rl, mean, sD))
    return P - P*(norm.ppf(rl, mean, sD) + 1)

if __name__ == "__main__":
    startDate = dt.datetime(2021, 10, 26)
    endDate = dt.datetime(2023, 10, 24)
    #format              year, month, day
    
    stock = yf.download('NKE', startDate, endDate)
    closeDiffs = stock['Adj Close'].pct_change()
    
    portfolio = 100000000
    rlPercent = 0.05
    mean = np.mean(closeDiffs)
    sD = np.std(closeDiffs)
    
    VaR = dailyVar(portfolio, rlPercent, mean, sD)
    print("500 Day stock history, for 1 day time horizon, 95% certainty, Portfolio of 100,000,000, VaR for the 23/10/2023: £" + str(round(VaR, 3)))
    
    count = 0
    for i in range(1, len(stock) - 100):
        backTest = np.array([])
        backTest = stock['Adj Close'].pct_change()[i:i+100]
        VaR = dailyVar(portfolio, rlPercent, np.mean(backTest), np.std(backTest))
        nextDay = stock['Adj Close'].pct_change()[i+100:i+101].values[0]
        if VaR*-1 > (nextDay*portfolio): #Needs to be multiplied by -1 as VaR is a predicted loss
            count += 1
    print("Back Test for 100-day rolling window of 500 Day stock history, at 95% certainty: " + str(round(count/(len(stock)-100)*100, 1)) + "%")
    
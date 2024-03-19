import datetime as dt
import time
import numpy as np
from scipy.stats import norm
import yfinance as yf
import pandas as pd


endDate = dt.datetime(2023, 1, 1)
startDate = endDate - dt.timedelta(days=1000)
stock1 = yf.download('NKE', startDate, endDate).tail(500)
stock2 = yf.download('AAPL', startDate, endDate).tail(500) 
stock3 = yf.download('MSFT', startDate, endDate).tail(500)
 
stocks = pd.DataFrame({
    'NKE': stock1['Adj Close'].pct_change().dropna(),
    'AAPL': stock2['Adj Close'].pct_change().dropna(),
    'MSFT': stock3['Adj Close'].pct_change().dropna()
})
weights = np.array([0.4, 0.3, 0.3])

portReturn = np.dot(weights, stocks.mean()) #Weighted average of the returns
portCovariance = np.cov(stocks, rowvar=False) #rowvar means that each row is an observation, and each column is a variable
portSD = np.sqrt(np.dot(weights.T, np.dot(portCovariance, weights)))

confidence = 0.95
zScore = norm.ppf(confidence)
portfolio = 100000000
# portSD = np.std(stocks['NKE'])

VaR = portfolio * (portReturn + zScore * portSD) 
print("Portfolio VaR: £" + str(round(VaR, 0)))


# closeDiffs = stocks['NKE']
# mean = np.mean(closeDiffs)
# sD = np.std(closeDiffs)
# VaR = portfolio - portfolio*(norm.ppf(1- confidence, mean, sD) + 1)
# print("Using previous method, VaR for just NKE is: £" + str(round(VaR, 0)))
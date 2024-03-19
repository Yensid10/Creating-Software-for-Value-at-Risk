import numpy as np
import yfinance as yf

# Download historical data for Nike, Adidas, and Under Armour
stock = yf.download(['NKE', 'ADS.DE', 'UAA'], period='100d')

# Calculate daily returns
closeDiffs = stock['Close'].pct_change().dropna()

# Portfolio weights
weighting = np.array([0.333, 0.333, 0.334])

# Calculate mean and covariance of returns
mean = closeDiffs.mean()
cov = closeDiffs.cov()
timeHori = 1

portfoReturns = []
# Monte Carlo simulations
for x in range(10000):
    simReturns = np.random.multivariate_normal(mean, cov, timeHori)
    singleReturn = np.sum(simReturns * weighting)
    portfoReturns.append(singleReturn)

# Calculate VaR
portfoReturns = sorted(portfoReturns)
rlPercent = 0.05

print("VaR: £" + str("{:,}".format(round(-np.percentile(portfoReturns, 100 * rlPercent)*100000000, 2))))
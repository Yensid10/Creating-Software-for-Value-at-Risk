import csv
import numpy as np

print("Historical Simulation VaR/n")
closes = np.array([])
with open('C:/Users/bensh/OneDrive/Essentials/Documents/Git/PROJECT/Command Line VaR Programs/NKE.csv', 'r') as file:
    reader = csv.reader(file)
    flag = True
    for row in reader:
        if flag:
            flag = False
            continue
        closes = np.append(closes, float(row[5]))
        
diffs = np.array([])
for i in range(1, len(closes)): 
    diffs = np.append(diffs, (closes[i]/closes[i-1] - 1))
    
print("500 Day stock history, for 1 day time horizon, 95% certainty, Portfolio of 100,000,000, VaR for the 23/10/2023: £" + str(round(np.percentile(diffs, 5)*100000000*-1, 3)))

count = 0
for i in range(1, len(closes) - 100):
    backTest = np.array([])
    for x in range(i, i + 100):
        backTest = np.append(backTest, (closes[x]/closes[x-1] - 1))
    VaR = np.percentile(backTest, 5)
    if VaR > ((closes[x+1]/closes[x] - 1)):
        count += 1
print("Back Test for 100-day rolling window of 500 Day stock history, at 95% certainty: " + str(round(count/(len(closes)-100)*100, 1)) + "%")
from bs4 import BeautifulSoup
import requests

def findCompanyName(ticker):
    yFinancePage = f"https://finance.yahoo.com/quote/{ticker}"
    response = requests.get(yFinancePage)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    companyName = soup.find('h1', class_='D(ib) Fz(18px)')
    if companyName:
        return companyName.text
    return None

tickers = ["AAPL", "GOOG", "MSFT"]

for ticker in tickers:
    print(f"The company name for ticker {ticker} is {findCompanyName(ticker)}.")
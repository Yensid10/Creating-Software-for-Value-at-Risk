from bs4 import BeautifulSoup
import requests

def findCompanyName(ticker):
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



tickers = ["AAPL", "NKE", "UAA", "ADS.DE", "TSLA", "AAL.L"]

for ticker in tickers:
    print(f"The company name for ticker {ticker} is {findCompanyName(ticker)}.")
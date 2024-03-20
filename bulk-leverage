from pybit.unified_trading import HTTP
import time
from pybit.exceptions import InvalidRequestError


# API Infos
bybit_api_key = "Bybit API"
bybit_api_secret = "Bybit API Secret"

# Desired leverage   
lev=10 

# Create API session
session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_api_secret
)

# Read symbol list from txt file
with open('pairs.txt') as f:
    symbollist = f.read().splitlines()

for symbol in symbollist:
    try:
        response = session.set_leverage(
            category="linear", #inverse
            symbol=symbol,
            buyLeverage=lev,
            sellLeverage=lev,
        )
        print(f"{symbol} leverage set: {response}")
    except InvalidRequestError as e:
        print(f"Error encountered: {symbol}")
        continue  # Move to next symbol

    time.sleep(1)  # Add a short delay to not send requests too quickly to the API

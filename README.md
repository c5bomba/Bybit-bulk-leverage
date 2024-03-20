# Bybit-bulk-leverage
 This Python script uses the PyBit library to set leverage for multiple trading pairs on the Bybit exchange. 

  It reads a list of trading pairs from a file (pairs.txt), then sets the buy and sell leverage to a specified value (lev) for each trading pair. It creates an API session with Bybit using the HTTP class from pybit.unified_trading, and catches and ignores any InvalidRequestError that may occur during the process. Finally, it adds a short 1-second delay between requests to prevent sending requests too quickly.

The InvalidRequestError can occur if the pair doesn't exist or if the leverage is already set as desired.

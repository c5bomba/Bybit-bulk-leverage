from pybit.unified_trading import HTTP
import time
from pybit.exceptions import InvalidRequestError
import sys
import logging

bybit_logger = logging.getLogger("pybit._http_manager")
bybit_logger.setLevel(logging.CRITICAL) 
# --- Constants ---
API_KEY = "API KEY"
API_SECRET = "API SECRET"
CATEGORY = "linear" # ( linear, inverse, spot)
SYMBOLS_FILENAME = 'pairs.txt'
REQUEST_LIMIT = 1000
API_SLEEP_TIME = 0.2 
LEVERAGE_SLEEP_TIME = 0.1
RATE_LIMIT_SLEEP_TIME = 1
BYBIT_RATE_LIMIT_CODE = 10006 
BYBIT_LEVERAGE_NOT_MODIFIED_CODE = 110044
BYBIT_LEVERAGE_NOT_MODIFIED_ALT_CODE = 110043 # Leverage not modified 
BYBIT_TIMESTAMP_ERROR_CODE = 10002       # Timestamp/recv_window error
RETRY_DELAY_TIMESTAMP_ERROR = 0.25  # Retry delay for 10002 errors (in seconds)

# --- API Session Setup ---
print("Initializing Bybit API session...")
try:
    session = HTTP(
        testnet=False,
        api_key=API_KEY,
        api_secret=API_SECRET,
        timeout=(10, 30) # (connect, read) timeouts in seconds
    )
    server_time = session.get_server_time()
    print(f"API Session successful. Server time: {server_time.get('time')}")
except InvalidRequestError as e:
     print(f"!!! CRITICAL: API key/secret invalid or insufficient permissions: {e}")
     sys.exit(1)
except Exception as e:
    print(f"!!! CRITICAL: Failed to create Bybit API session: {e}")
    sys.exit(1)

def get_all_linear_symbols(session):
    """Fetches all trading symbols for CATEGORY via Bybit API with pagination."""
    symbols = []
    cursor = ""
    print(f"\nFetching '{CATEGORY}' symbols from Bybit API...")
    page_count = 0
    while True:
        page_count += 1
        print(f"  Fetching page {page_count}...", end=' ')
        try:
            response = session.get_instruments_info(
                category=CATEGORY,
                limit=REQUEST_LIMIT,
                cursor=cursor,
                status="Trading"
            )
            if response and response.get("retCode") == 0:
                result = response.get("result", {})
                current_symbols = [item["symbol"] for item in result.get("list", [])]
                symbols.extend(current_symbols)
                fetched_count = len(current_symbols)
                print(f"Fetched {fetched_count}. Total: {len(symbols)}")
                cursor = result.get("nextPageCursor", "")
                if not cursor:
                    print("-> Finished fetching all symbols.")
                    break
                if fetched_count < REQUEST_LIMIT and not cursor:
                    print("-> Fetched fewer symbols than limit and no next cursor, assuming end.")
                    break
            elif response and response.get("retCode") == BYBIT_RATE_LIMIT_CODE:
                 print(f"-> Rate limit hit (Code {BYBIT_RATE_LIMIT_CODE}). Sleeping for {RATE_LIMIT_SLEEP_TIME} seconds...")
                 time.sleep(RATE_LIMIT_SLEEP_TIME)
            else:
                ret_code = response.get("retCode", "N/A")
                ret_msg = response.get("retMsg", "Unknown Error")
                print(f"-> Error fetching symbols! Code: {ret_code}, Msg: {ret_msg}")
                print(f"   Full error response: {response}")
                return None
        except InvalidRequestError as e:
            print(f"-> Invalid request during symbol fetch: {e}")
            return None
        except Exception as e:
            print(f"-> Unexpected exception while fetching symbols: {e}")
            return None
        time.sleep(API_SLEEP_TIME)
    print(f"Total unique symbols fetched: {len(set(symbols))}")
    return list(set(symbols))

def write_symbols_to_file(symbollist, filename):
    """Writes a list of symbols to a file, overwriting it."""
    if symbollist is None:
         print("! Error: Cannot write None symbol list to file.")
         return False
    if not isinstance(symbollist, list):
         print("! Error: Input symbollist is not a list.")
         return False
    print(f"\nWriting {len(symbollist)} symbols to '{filename}'...")
    try:
        with open(filename, 'w') as f:
            for symbol in symbollist:
                f.write(f"{symbol}\n")
        print(f"-> Successfully wrote symbols to '{filename}'")
        return True
    except IOError as e:
        print(f"! Error: Could not write to file '{filename}': {e}")
        return False

def read_symbols_from_file(filename):
    """Reads symbols from a file, one per line."""
    print(f"\nReading symbols from '{filename}'...")
    try:
        with open(filename, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        if not symbols:
            print(f"-> Warning: '{filename}' is empty.")
            return []
        print(f"-> Read {len(symbols)} symbols from '{filename}'")
        return symbols
    except FileNotFoundError:
        print(f"! Error: File '{filename}' not found.")
        return None
    except IOError as e:
        print(f"! Error: Could not read from file '{filename}': {e}")
        return None

def _log_symbol_processing_issue(issue_type, symbol, message="", code=None, is_api_error=False):
    padding = 20
    if is_api_error:
        print(f"\n! {issue_type}: {symbol.ljust(padding)} Code={code}, Msg='{message}'")
    else:
        print(f"\n! {issue_type}: {symbol.ljust(padding)} {message}")

def set_leverages_for_symbols(session, symbollist, leverage_str):
    if not symbollist:
        print("! Warning: No symbols provided to set leverage for.")
        return
    if not leverage_str.isdigit() or int(leverage_str) <= 0:
        print(f"! Error: Invalid leverage value '{leverage_str}'. Must be a positive integer.")
        return
    
    target_leverage = int(leverage_str)
    total_symbols = len(symbollist)
    print(f"\nAttempting to set leverage to {target_leverage}x for {total_symbols} symbols...")
    s_count, e_count, sk_count = 0, 0, 0
    MAX_RETRIES = 2
    # Define error code
    SKIP_RET_CODES = [BYBIT_LEVERAGE_NOT_MODIFIED_CODE, BYBIT_LEVERAGE_NOT_MODIFIED_ALT_CODE]
    SKIP_ERROR_CODE_SUBSTRINGS = [f"ErrCode: {BYBIT_LEVERAGE_NOT_MODIFIED_CODE}", f"ErrCode: {BYBIT_LEVERAGE_NOT_MODIFIED_ALT_CODE}"]
    RETRY_ERROR_CODE_SUBSTRING = f"ErrCode: {BYBIT_TIMESTAMP_ERROR_CODE}"

    for i, symbol in enumerate(symbollist):
        print(f"  Processing {i+1}/{total_symbols}: {symbol.ljust(20)}", end='\r')
        
        processed_symbol_status = None

        for attempt in range(MAX_RETRIES + 1): 
            try:
                if attempt > 0: 
                    print(f"  Retrying {symbol} (attempt {attempt}/{MAX_RETRIES})...{' '*20}", end='\r')
                response = session.set_leverage(
                    category=CATEGORY,
                    symbol=symbol,
                    buyLeverage=leverage_str,
                    sellLeverage=leverage_str,
                )

                current_ret_code = response.get('retCode') if response else None

                if current_ret_code == 0:
                    s_count += 1
                    processed_symbol_status = 'success'
                    break 
                
                if current_ret_code in SKIP_RET_CODES:
                    sk_count += 1
                    processed_symbol_status = 'skipped'
                    break 

                if current_ret_code == BYBIT_TIMESTAMP_ERROR_CODE:
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY_TIMESTAMP_ERROR)
                        continue
                    else:
                        _log_symbol_processing_issue("Error", symbol, message=f"Failed (API Code {BYBIT_TIMESTAMP_ERROR_CODE}) after {MAX_RETRIES} retries.")
                        e_count += 1
                        processed_symbol_status = 'error'
                        break 
                
                if response and current_ret_code != 0: # Other API errors
                    rc = response.get("retCode","N/A")
                    rm = response.get('retMsg','Unknown API Error')
                    _log_symbol_processing_issue("API Error", symbol, message=rm, code=rc, is_api_error=True)
                    e_count += 1
                    processed_symbol_status = 'error'
                    break
                
                if not response: # Shouldn't happen if API doesn't fail
                    _log_symbol_processing_issue("Error", symbol, message="No response from API call.")
                    e_count += 1
                    processed_symbol_status = 'error'
                    break

            except InvalidRequestError as e:
                err_str = str(e)
                if any(substring in err_str for substring in SKIP_ERROR_CODE_SUBSTRINGS):
                    sk_count += 1
                    processed_symbol_status = 'skipped'
                    break
                
                if RETRY_ERROR_CODE_SUBSTRING in err_str: # Error 10002"
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY_TIMESTAMP_ERROR)
                        continue
                    else:
                        _log_symbol_processing_issue("Error", symbol, message=f"Failed ({RETRY_ERROR_CODE_SUBSTRING}) after {MAX_RETRIES} retries.")
                        e_count += 1
                        processed_symbol_status = 'error'
                        break
                
                _log_symbol_processing_issue("Request Error", symbol, message=str(e))
                e_count += 1
                processed_symbol_status = 'error'
                break
            
            except Exception as e:
                _log_symbol_processing_issue("Unexpected Error", symbol, message=str(e))
                e_count += 1
                processed_symbol_status = 'error'
                break
        
        if processed_symbol_status is None:
            _log_symbol_processing_issue("Internal Logic Error", symbol, message="Processing incomplete.")
            e_count += 1

        if i == total_symbols - 1:
             print(f"  {' ' * 70}\r", end='')

        time.sleep(LEVERAGE_SLEEP_TIME)

    # Summary
    print(f"\nLeverage setting process finished.")
    print("=" * 25)
    print("    Leverage Summary")
    print("=" * 25)
    print(f"  Successfully Set: {s_count}")
    print(f"  Already Set/Skipped: {sk_count}")
    print(f"  Errors:         {e_count}")
    print("-" * 25)

def main():
    """Main function to handle user interaction and script logic."""
    while True:
        print("\n" + "=" * 40)
        print("      BYBIT LEVERAGE TOOL")
        print("=" * 40)
        print("  Available Actions:")
        print(f"    [1] Update & Save Symbol List ('{SYMBOLS_FILENAME}')")
        print(f"    [2] Set Leverage from Symbol List ('{SYMBOLS_FILENAME}')")
        print("    [3] Exit")
        print("-" * 40)

        choice = input("  Enter your choice [1, 2, or 3]: ")
        print("-" * 40)

        if choice == '1':
            print("Action [1]: Update Symbol List selected.")
            symbols = get_all_linear_symbols(session)
            if symbols is not None: 
                if symbols:
                     write_symbols_to_file(symbols, SYMBOLS_FILENAME)
                else:
                     print("-> Warning: Fetched 0 trading symbols. File will not be updated.")
            else:
                print("! Action [1] failed: Could not fetch symbols from API.")    

        elif choice == '2':
            print("Action [2]: Set Leverage selected.")
            symbols_file = read_symbols_from_file(SYMBOLS_FILENAME)

            if symbols_file is None:
                 print(f"! Action [2] failed: '{SYMBOLS_FILENAME}' not found or couldn't be read.")
                 print("  Please run option [1] first or ensure the file exists.")
                 continue

            if not symbols_file:
                print(f"! Action [2] failed: '{SYMBOLS_FILENAME}' is empty.")
                print("  Please run option [1] first to populate the file.")
                continue

            while True:
                leverage_val = input(f"  Enter desired leverage (e.g., 10, must be > 0): ")
                if leverage_val.isdigit() and int(leverage_val) > 0:
                    break
                else:
                    print("! Invalid input. Leverage must be a whole positive number.")
            
            set_leverages_for_symbols(session, symbols_file, leverage_val)
          
        elif choice == '3':
             print("Action [3]: Exit selected.")
             print("Exiting script. Goodbye!")
             break 

        else:
            print(f"! Invalid choice '{choice}'. Please enter 1, 2, or 3.")
                 
        input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    print("Script starting...")
    main()
    print("Script finished.")

# Bybit Bulk Leverage Tool

This Python script utilizes the PyBit library to efficiently manage and set leverage for multiple trading pairs on the Bybit exchange (specifically for the "linear" category).

It offers an interactive command-line interface to fetch the latest trading symbols, save them to a local file, and then apply a user-specified leverage to all symbols read from that file. The script incorporates robust error handling, retry mechanisms for common transient API issues, and provides clear feedback on its progress and results.

## Key Features

*   **Symbol List Management:**
    *   Fetch all currently trading "linear" symbols directly from the Bybit API.
    *   Save the fetched symbol list to a local file (default: `pairs.txt`).
    *   Read symbols from the local file for leverage setting.
*   **Bulk Leverage Setting:**
    *   Set buy and sell leverage to a user-specified value for all symbols in the list.
*   **Interactive CLI Menu:**
    *   Option [1]: Update & Save Symbol List (fetches from Bybit and overwrites `pairs.txt`).
    *   Option [2]: Set Leverage from Symbol List (reads `pairs.txt` and applies leverage).
    *   Option [3]: Exit.
*   **Robust Error Handling & Retries:**
    *   Gracefully handles and logs various Bybit API return codes:
        *   Leverage already set/not modified (codes 110043, 110044): Symbol is skipped.
        *   Timestamp/recv_window errors (code 10002): Retries automatically with a short delay.
        *   API rate limits (code 10006): Pauses and retries.
        *   Other specific API errors and general request errors are logged.
    *   Configurable maximum retries for timestamp-related errors.
*   **User Feedback & Logging:**
    *   Real-time progress display during symbol fetching and leverage setting.
    *   Detailed summary report after leverage setting (successes, skips, errors).
    *   Suppresses verbose `pybit` library logs for known, handled errors (e.g., timestamp errors) to keep the output clean.
*   **Configurable Parameters:**
    *   API Key and Secret (must be configured in the script).
    *   Sleep timers for API calls, between leverage settings, for rate limit cooldowns, and retry delays.

## Prerequisites

*   Python 3.x
*   `pybit` library: Install using `pip install pybit`

## Configuration

1.  **API Credentials:**
    *   Open `bulk-leverage.py`.
    *   Locate the `API_KEY` and `API_SECRET` constants near the top of the file.
    *   Replace the placeholder values with your actual Bybit API key and secret.
        ```python
        API_KEY = "YOUR_API_KEY"
        API_SECRET = "YOUR_API_SECRET"
        ```
    *   Ensure your API key has the necessary permissions for trading (or specifically for setting leverage if your operations are limited).

2.  **Symbols File (Optional Initial Setup):**
    *   The script uses `pairs.txt` (by default) to store trading symbols.
    *   You can either let the script create/update this file using Option [1] from the menu, or you can manually create `pairs.txt` in the same directory as the script and populate it with one trading symbol per line (e.g., BTCUSDT, ETHUSDT).

## Usage

1.  Navigate to the directory containing `bulk-leverage.py` in your terminal.
2.  Run the script:
    ```bash
    python bulk-leverage.py
    ```
3.  The script will initialize the API session and then present you with the main menu:
    ```
    ========================================
          BYBIT LEVERAGE TOOL
    ========================================
      Available Actions:
        [1] Update & Save Symbol List ('pairs.txt')
        [2] Set Leverage from Symbol List ('pairs.txt')
        [3] Exit
    ----------------------------------------
      Enter your choice [1, 2, or 3]:
    ```
4.  **Option [1]:** Fetches all "linear" trading symbols from Bybit and saves them to `pairs.txt`. Useful for getting an up-to-date list.
5.  **Option [2]:** Prompts you to enter the desired leverage (e.g., 10). It then reads symbols from `pairs.txt` and attempts to set the leverage for each.
6.  Follow the on-screen prompts and information.

## Important Notes

*   **API Rate Limits:** The script includes `LEVERAGE_SLEEP_TIME` (default 0.1 seconds) between individual leverage set requests to stay within common Bybit API rate limits (typically 10 requests/second for this endpoint). If you encounter frequent rate limit errors (10006), consider slightly increasing this sleep time.
*   **Error Codes:** The script is designed to handle several common Bybit error codes. If you encounter persistent or unhandled errors, check the Bybit API documentation for the specific error code meanings.
*   **Testnet:** The script is configured for the mainnet (`testnet=False`). If you wish to use it with the Bybit testnet, you'll need to change this setting in the `HTTP` session initialization and use testnet API keys.
*   **Permissions:** Ensure your API keys have the correct permissions to read instrument info and set leverage.


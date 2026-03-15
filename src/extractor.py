import logging
import pandas as pd
import yfinance as yf
from src.settings import START_DATE, END_DATE

class DataExtractor:

    def _process_ticker_dataframe(self, df):
        # Keep only relevant column which is the close price
        df = df[["Close"]].rename(columns={"Close": "Price"})

        # Compute daily returns and drop the first date
        df["Returns"] = df["Price"].pct_change()
        df = df.dropna()

        # Convert index to date type
        df.index = df.index.date
        df.index.name = "Date"
        return df

    def _extract_single_ticker_data(self, ticker: str, start_date: str, end_date: str):
        """
        Extract and process data for a single ticker.
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            df_processed = self._process_ticker_dataframe(df)

            if df.empty:
                logging.warning(f"No data available for ticker: {ticker}")
                return None

            return df_processed
        except Exception as e:
            logging.error(f"Error downloading {ticker}: {e}")
            return None


    def extract_data(
        self,
        tickers: list[str],
        start_data: str = START_DATE,
        end_date: str = END_DATE,
    ):
        """
        Extract historical stock data for multiple tickers.

        Args:
            tickers: List of stock ticker symbols
            start_date: Start date for data download (YYYY-MM-DD format)
            end_date: End date for data download (YYYY-MM-DD format)

        Returns:
            Dictionary mapping ticker to DataFrame with columns ['Price', 'Returns']
        """
        all_stock_data = {}

        for ticker in tickers:
            df_processed = self._extract_single_ticker_data(ticker, start_data, end_date)
            if df_processed is not None:
                all_stock_data[ticker] = df_processed

        return all_stock_data
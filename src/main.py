from src.settings import START_DATE, END_DATE, PORTFOLIO_TICKERS
import sys
import pandas as pd
from src.extractor import DataExtractor
from src.database import save_results_to_supabase
from src.optimiser import optimize_portfolio_mean_variance
from src.model import ProphetModel
from src.processor import preprocess_data, collect_recent_prices, append_predictions
import logging

def run_optimisation(
        tickers: list[str],
        start_date: str = START_DATE,
        end_date: str = END_DATE
):
    """
    Run portfolio optimisation: pull data, predict, calculate allocation, and log result.

    Args:
        tickers: List of stock ticker symbols
        start_date: Start date for historical data (YYYY-MM-DD format). Defaults to START_DATE.
        end_date: End date for historical data (YYYY-MM-DD format). Defaults to END_DATE.

    Returns:
        Dictionary containing optimisation results with keys:
        - date: date object representing date optimisation was run
        - prediction_date: date object for the prediction (next day after last historical date)
        - predictions: dict[str, float] of predicted prices for each ticker
        - current_prices: dict[str, float] of current prices for each ticker
        - predicted_returns: dict[str, float] of predicted returns for each ticker
        - weights: dict[str, float] of optimal portfolio weights for each ticker

    Returns empty dict if data extraction fails.
    """
    current_date = pd.to_datetime(end_date).date()
    logging.info(f"Starting portfolio optimisation for tickers: {tickers} as of {current_date}")

    #1. Extract hitorical data
    logging.info("Extracting Historical data...")
    all_stock_data = DataExtractor().extract_data(tickers, start_date, end_date)
    if not all_stock_data:
        logging.warning("No data extracted. Existing optimisation.")
        return {}
    
    # 2. Preprocess historical data
    logging.info("Preprocessing data...")
    portfolio_data = preprocess_data(all_stock_data)

    # 3. Predict next step using Prophet
    model = ProphetModel()
    predictions, predicted_returns = model.predict_for_tickers(portfolio_data)

    # 4. Collect actual price history for the past month
    actual_prices_last_month = collect_recent_prices(portfolio_data)

    # 5. Append predictions to historical data
    predicted_data = append_predictions(portfolio_data, predictions, predicted_returns)

    # 6. Optimise portfolio using predicted returns as expected returns
    logging.info("Calculating optimal portfolio allocation...")
    weights_dict = optimize_portfolio_mean_variance(predicted_data)


    # 7. Log results
    logging.info("Portfolio Optimisation Results")
    logging.info(f"Date: {current_date}")

    logging.info("\nPredicted Prices (Next Day):")
    for ticker, price in predictions.items():
        logging.info(f"  {ticker}: ${price:.2f}")

    logging.info("\nPredicted Returns:")
    for ticker, ret in predicted_returns.items():
        logging.info(f"  {ticker}: {ret * 100:.2f}%")

    logging.info("\nOptimal Portfolio Weights:")
    for ticker, weight in weights_dict.items():
        logging.info(f"  {ticker}: {weight * 100:.2f}%")

    return {
        "date": current_date,
        "predictions": predictions,
        "predicted_returns": predicted_returns,
        "actual_prices_last_month": actual_prices_last_month,
        "weights": weights_dict,
    }

def main() -> None:
    """Main CLI entry point - saves results to Supabase."""
    try:
        result = run_optimisation(tickers=PORTFOLIO_TICKERS)

        if not result:
            logging.error("Optimisation returned empty result")
            sys.exit(1)

        try:
            save_results_to_supabase(result)
            print("\nResults successfully saved to Supabase database")
        except Exception as db_error:
            logging.error(f"Failed to save to Supabase: {db_error}")
            print(f"\nWarning: Failed to save to Supabase: {db_error}")
            sys.exit(1)

    except Exception as e:
        logging.error(f"Error during optimisation: {e}")
        print(f"Error during optimisation: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
import json
from datetime import datetime, timedelta
from typing import Annotated

import yfinance as yf
from loguru import logger
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from yfinance.const import SECTOR_INDUSTY_MAPPING

from yfmcp.types import Interval
from yfmcp.types import Period
from yfmcp.types import SearchType
from yfmcp.types import Sector
from yfmcp.types import TopType

# https://github.com/jlowin/fastmcp/issues/81#issuecomment-2714245145
mcp = FastMCP("Yahoo Finance MCP Server", log_level="ERROR")


@mcp.tool()
def get_ticker_info(symbol: Annotated[str, Field(description="The stock symbol")]) -> str:
    """Retrieve stock data including company info, financials, trading metrics and governance data."""
    ticker = yf.Ticker(symbol)

    # Convert timestamps to human-readable format
    info = ticker.info
    for key, value in info.items():
        if not isinstance(key, str):
            continue

        if key.lower().endswith(("date", "start", "end", "timestamp", "time", "quarter")):
            try:
                info[key] = datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                logger.error("Unable to convert {}: {} to datetime, got error: {}", key, value, e)
                continue

    return json.dumps(info, ensure_ascii=False)


@mcp.tool()
def get_ticker_news(symbol: Annotated[str, Field(description="The stock symbol")]) -> str:
    """Fetches recent news articles related to a specific stock symbol with title, content, and source details."""
    ticker = yf.Ticker(symbol)
    news = ticker.get_news()
    return str(news)


@mcp.tool()
def search(
    query: Annotated[str, Field(description="The search query (ticker symbol or company name)")],
    search_type: Annotated[SearchType, Field(description="Type of search results to retrieve")],
) -> str:
    """Fetches and organizes search results from Yahoo Finance, including stock quotes and news articles."""
    s = yf.Search(query)
    match search_type.lower():
        case "all":
            return json.dumps(s.all, ensure_ascii=False)
        case "quotes":
            return json.dumps(s.quotes, ensure_ascii=False)
        case "news":
            return json.dumps(s.news, ensure_ascii=False)
        case _:
            return "Invalid output_type. Use 'all', 'quotes', or 'news'."


def get_top_etfs(
    sector: Annotated[Sector, Field(description="The sector to get")],
    top_n: Annotated[int, Field(description="Number of top ETFs to retrieve")],
) -> str:
    """Retrieve popular ETFs for a sector, returned as a list in 'SYMBOL: ETF Name' format."""
    if top_n < 1:
        return "top_n must be greater than 0"

    s = yf.Sector(sector)

    result = [f"{symbol}: {name}" for symbol, name in s.top_etfs.items()]

    return "\n".join(result[:top_n])


def get_top_mutual_funds(
    sector: Annotated[Sector, Field(description="The sector to get")],
    top_n: Annotated[int, Field(description="Number of top mutual funds to retrieve")],
) -> str:
    """Retrieve popular mutual funds for a sector, returned as a list in 'SYMBOL: Fund Name' format."""
    if top_n < 1:
        return "top_n must be greater than 0"

    s = yf.Sector(sector)
    return "\n".join(f"{symbol}: {name}" for symbol, name in s.top_mutual_funds.items())


def get_top_companies(
    sector: Annotated[Sector, Field(description="The sector to get")],
    top_n: Annotated[int, Field(description="Number of top companies to retrieve")],
) -> str:
    """Get top companies in a sector with name, analyst rating, and market weight as JSON array."""
    if top_n < 1:
        return "top_n must be greater than 0"

    try:
        s = yf.Sector(sector)
        df = s.top_companies
    except Exception as e:
        return json.dumps({"error": f"Failed to get top companies for sector '{sector}': {e}"})
    if df is None:
        return json.dumps({"error": f"No top companies available for {sector} sector."})
    return df.iloc[:top_n].to_json(orient="records")


def get_top_growth_companies(
    sector: Annotated[Sector, Field(description="The sector to get")],
    top_n: Annotated[int, Field(description="Number of top growth companies to retrieve")],
) -> str:
    """Get top growth companies grouped by industry within a sector as JSON array with growth metrics."""
    if top_n < 1:
        return "top_n must be greater than 0"

    results = []

    for industry_name in SECTOR_INDUSTY_MAPPING[sector]:
        industry = yf.Industry(industry_name)

        df = industry.top_growth_companies
        if df is None:
            continue

        results.append(
            {
                "industry": industry_name,
                "top_growth_companies": df.iloc[:top_n].to_json(orient="records"),
            }
        )
    return json.dumps(results, ensure_ascii=False)


def get_top_performing_companies(
    sector: Annotated[Sector, Field(description="The sector to get")],
    top_n: Annotated[int, Field(description="Number of top performing companies to retrieve")],
) -> str:
    """Get top performing companies grouped by industry within a sector as JSON array with performance metrics."""
    if top_n < 1:
        return "top_n must be greater than 0"

    results = []

    for industry_name in SECTOR_INDUSTY_MAPPING[sector]:
        industry = yf.Industry(industry_name)

        df = industry.top_performing_companies
        if df is None:
            continue

        results.append(
            {
                "industry": industry_name,
                "top_performing_companies": df.iloc[:top_n].to_json(orient="records"),
            }
        )
    return json.dumps(results, ensure_ascii=False)


@mcp.tool()
def get_top(
    sector: Annotated[Sector, Field(description="The sector to get")],
    top_type: Annotated[TopType, Field(description="Type of top companies to retrieve")],
    top_n: Annotated[int, Field(description="Number of top entities to retrieve (limit the results)")] = 10,
) -> str:
    """Get top entities (ETFs, mutual funds, companies, growth companies, or performing companies) in a sector."""
    match top_type:
        case "top_etfs":
            return get_top_etfs(sector, top_n)
        case "top_mutual_funds":
            return get_top_mutual_funds(sector, top_n)
        case "top_companies":
            return get_top_companies(sector, top_n)
        case "top_growth_companies":
            return get_top_growth_companies(sector, top_n)
        case "top_performing_companies":
            return get_top_performing_companies(sector, top_n)
        case _:
            return "Invalid top_type"


@mcp.tool()
def get_price_history(
    symbol: Annotated[str, Field(description="The stock symbol")],
    period: Annotated[Period, Field(description="Time period to retrieve data for (e.g. '1d', '1mo', '1y')")] = "1mo",
    interval: Annotated[Interval, Field(description="Data interval frequency (e.g. '1d', '1h', '1m')")] = "1d",
) -> str:
    """Fetch historical price data for a given stock symbol over a specified period and interval."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(
        period=period,
        interval=interval,
        rounding=True,
    )
    return df.to_markdown()


@mcp.tool()
def calculate_profit_loss(
    symbol: Annotated[str, Field(description="The stock symbol")],
    start_date: Annotated[
        str,
        Field(description="Start date in ISO format (YYYY-MM-DD) to calculate the price from"),
    ],
    end_date: Annotated[
        str,
        Field(description="End date in ISO format (YYYY-MM-DD) to calculate the price to"),
    ],
) -> str:
    """Calculate the profit or loss and percentage change between two dates for a given stock symbol."""

    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError as exc:
        return json.dumps({"error": f"Invalid date format: {exc}"})

    if start_dt >= end_dt:
        return json.dumps({"error": "start_date must be earlier than end_date"})

    ticker = yf.Ticker(symbol)
    history = ticker.history(
        start=start_dt,
        end=end_dt + timedelta(days=1),
        interval="1d",
        rounding=True,
    )

    if history.empty:
        return json.dumps(
            {
                "error": (
                    "No historical data available for the given symbol and date range. "
                    "Please verify the symbol and that the dates fall on trading days."
                )
            }
        )

    start_price = history.iloc[0]["Close"]
    end_price = history.iloc[-1]["Close"]

    profit_loss = end_price - start_price
    percent_change = None
    if start_price != 0:
        percent_change = float((profit_loss / start_price) * 100)

    return json.dumps(
        {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "start_price": float(start_price),
            "end_price": float(end_price),
            "profit_loss": float(profit_loss),
            "percent_change": percent_change,
        }
    )


def main() -> None:
    mcp.run()

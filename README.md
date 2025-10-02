# Yahoo Finance MCP Server

A simple MCP server for Yahoo Finance using [yfinance](https://github.com/ranaroussi/yfinance). This server provides a set of tools to fetch stock data, news, and other financial information.

<a href="https://glama.ai/mcp/servers/@narumiruna/yfinance-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@narumiruna/yfinance-mcp/badge" />
</a>

## Tools

- **get_ticker_info**

  - Retrieve stock data including company info, financials, trading metrics and governance data.
  - Inputs:
    - `symbol` (string): The stock symbol.

- **get_ticker_news**

  - Fetches recent news articles related to a specific stock symbol with title, content, and source details.
  - Inputs:
    - `symbol` (string): The stock symbol.

- **search**

  - Fetches and organizes search results from Yahoo Finance, including stock quotes and news articles.
  - Inputs:
    - `query` (string): The search query (ticker symbol or company name).
    - `search_type` (string): Type of search results to retrieve (options: "all", "quotes", "news").

- **get_top** *(consolidated tool from [PR #1](https://github.com/Talismanic/yfinance-mcp/pull/1))*

  - A single entry point for discovering the "top" insights from Yahoo Finance without juggling multiple tools. Depending on the `top_type` you pick, the server will route your request to the relevant Yahoo Finance endpoint and return:
    - **Top ETFs** and **Top Mutual Funds** as newline-delimited `SYMBOL: Name` pairs, ideal when you just want a quick ranked list.
    - **Top Companies**, **Top Growth Companies**, and **Top Performing Companies** as JSON payloads (or a list of industry-grouped JSON strings) that include analyst ratings, weights, growth, or performance metrics—perfect for downstream parsing or summarisation workflows.
  - Inputs:
    - `sector` (string): The sector to explore.
    - `top_type` (string): Which insight you need. Valid values are `"top_etfs"`, `"top_mutual_funds"`, `"top_companies"`, `"top_growth_companies"`, and `"top_performing_companies"`.
    - `top_n` (number, optional): Limit the number of entities returned (default 10). Applies to all output types so you can keep responses concise.
  - Returns an error message if an unsupported `top_type` is supplied or no data is available for the requested sector, making it easy to detect and handle edge cases in your client code.

- **get_price_history**

  - Fetch historical price data for a given stock symbol over a specified period and interval.
  - Inputs:
    - `symbol` (string): The stock symbol.
    - `period` (string, optional): Time period to retrieve data for (e.g. '1d', '1mo', '1y'). Default is '1mo'.
    - `interval` (string, optional): Data interval frequency (e.g. '1d', '1h', '1m'). Default is '1d'.

## Usage

You can use this MCP server either via uv (Python package installer) or Docker.

### Via uv

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Add the following configuration to your MCP server configuration file:

```json
{
  "mcpServers": {
    "yfmcp": {
      "command": "uvx",
      "args": ["yfmcp@latest"]
    }
  }
}
```

### Via Docker

Add the following configuration to your MCP server configuration file:

```json
{
  "mcpServers": {
    "yfmcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "narumi/yfinance-mcp"]
    }
  }
}

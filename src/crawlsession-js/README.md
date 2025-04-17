# Crawl API Session Example

This example demonstrates how to use the Crawl API's session capabilities to crawl a website and follow links within the same session.

## Features

- Creates a crawl session
- Performs an initial crawl of a webpage (Bulma.io)
- Parses the HTML to extract stylesheet links
- Processes and crawls each stylesheet link in the same session
- Demonstrates managing session state

## Running the Example

1. Install dependencies:
   ```
   npm install
   ```

2. Run the example:
   ```
   npm start
   ```

## How It Works

The example demonstrates session-based crawling by:
1. Initiating a session
2. Performing the first crawl to get a webpage
3. Extracting stylesheet links from the HTML response
4. Submitting each stylesheet as a new job in the same session
5. Handling the chained responses efficiently using the session mechanism

This approach is more efficient than creating separate connections for each request, as it leverages the server's ability to chain related requests.
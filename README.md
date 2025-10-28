# Salesforce MCP Server

This project provides a Model-Context-Protocol (MCP) server that acts as a bridge between a Large Language Model (LLM) and the Salesforce API. It exposes a set of tools that allow the LLM to interact with Salesforce data, covering both Sales Cloud and Service Cloud functionalities.

## Features

- **Salesforce Integration**: Connects securely to a Salesforce instance using user credentials.
- **Tool Exposure**: Exposes a rich set of tools for interacting with Salesforce objects like Contacts, Accounts, Opportunities, and Cases.
- **Sales Cloud Tools**: Search contacts, get account details, list open opportunities, and log activities.
- **Service Cloud Tools**: Get case details, list open cases, create new cases, and add comments.
- **Global Search**: Perform a global search across multiple Salesforce objects.
- **MCP Compliant**: Built on the `mcp.server` framework for seamless integration with MCP-compatible clients.

## Prerequisites

To run this server, you need valid Salesforce credentials. The server can be configured via environment variables or command-line arguments.

**Environment Variables:**

- `SF_USERNAME`: Your Salesforce username.
- `SF_PASSWORD`: Your Salesforce password.
- `SF_TOKEN`: Your Salesforce security token.
- `SF_DOMAIN`: The Salesforce domain to use. Defaults to `login` for production. Use `test` for sandboxes.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd salesforce_mcp_server
    ```

2.  **Install dependencies:**
    This project uses `uv` for package management.
    ```bash
    uv pip install -r requirements.txt 
    # Or if you have the pyproject.toml and uv.lock
    uv sync
    ```
    *(Note: A `requirements.txt` may need to be generated from `pyproject.toml` if not present)*

## Running the Server

You can start the server using the `run.py` script. You must provide your Salesforce credentials either as environment variables (see Prerequisites) or as command-line arguments.

```bash
python run.py --sf-username "your_user@example.com" --sf-password "your_password" --sf-token "your_token"
```

**Command-line options:**

- `--port`: Port to run the server on (default: `3000`).
- `--host`: Host to bind to (default: `127.0.0.1`).
- `--sf-username`: Salesforce username.
- `--sf-password`: Salesforce password.
- `--sf-token`: Salesforce security token.
- `--sf-domain`: Salesforce domain (default: `login`).
- `--log-level`: Logging level (e.g., `INFO`, `DEBUG`).

## Available Tools

The server exposes the following tools to the LLM:

### Sales Cloud Tools

-   **`search_contact`**: Searches for a contact in Salesforce by name and optionally by email.
-   **`get_account_details`**: Retrieves the full details of a customer account by its exact name or ID.
-   **`list_open_opportunities`**: Lists all sales opportunities (deals) that are not yet closed. Can be filtered by account or owner.
-   **`log_activity`**: Records an activity (like a call or email) and associates it with a record (Contact, Account, Opportunity).

### Service Cloud Tools

-   **`get_case_details`**: Retrieves the details of a support ticket (Case) using its ticket number.
-   **`list_open_cases`**: Lists all open support tickets, with optional filtering by contact email or account name.
-   **`create_case`**: Creates a new support ticket for a customer.
-   **`add_comment_to_case`**: Adds a comment (internal note or public reply) to an existing support ticket.

### Global Search Tool

-   **`search_salesforce`**: Performs a global search across Salesforce (Accounts, Contacts, Opportunities, Cases) using a search term.

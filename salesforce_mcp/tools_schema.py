import mcp.types as types

def get_tools_schema() -> list[types.Tool]:
    """Defines and returns the schema for all Salesforce tools to be exposed to the LLM."""
    return [
        # --- Sales Cloud Tools ---
        types.Tool(
            name="search_contact",
            description="Searches for a contact in Salesforce by name and optionally by email.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The name (or part of the name) of the contact to search for."},
                    "email": {"type": "string", "description": "(Optional) The exact email of the contact to refine the search."}
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="get_account_details",
            description="Retrieves the full details of a customer account (company) by its exact name or ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {"type": "string", "description": "The exact name of the account (e.g., 'Acme Corp')."},
                    "account_id": {"type": "string", "description": "The Salesforce ID of the account (e.g., '0015Y00002oR...')."}
                },
                "description": "Provide either account_name or account_id."
            },
        ),
        types.Tool(
            name="list_open_opportunities",
            description="Lists all sales opportunities (deals) that are not yet closed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "(Optional) Filters opportunities for a specific account by its ID."},
                    "owner_email": {"type": "string", "description": "(Optional) Filters opportunities belonging to a specific sales representative by their email."}
                },
            },
        ),
        types.Tool(
            name="log_activity",
            description="Logs an activity (like a call or email) and associates it with a record (Contact, Account, Opportunity).",
            inputSchema={
                "type": "object",
                "properties": {
                    "related_to_id": {"type": "string", "description": "The Salesforce ID of the record to link this activity to (e.g., a Contact or Account ID)."},
                    "subject": {"type": "string", "description": "The title or subject of the activity (e.g., 'Follow-up call')."},
                    "description": {"type": "string", "description": "A detailed description of what happened during the activity."}
                },
                "required": ["related_to_id", "subject", "description"],
            },
        ),
        
        # --- Service Cloud Tools ---
        types.Tool(
            name="get_case_details",
            description="Retrieves the details of a support ticket (Case) using its ticket number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_number": {"type": "string", "description": "The visible ticket number (e.g., '00001234')."}
                },
                "required": ["case_number"],
            },
        ),
        types.Tool(
            name="list_open_cases",
            description="Lists all open support tickets, filtered by contact email or account name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_email": {"type": "string", "description": "(Optional) The customer's email to find their tickets."},
                    "account_name": {"type": "string", "description": "(Optional) The exact name of the account to find its tickets."}
                },
            },
        ),
        types.Tool(
            name="create_case",
            description="Creates a new support ticket for a customer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "The title of the issue."},
                    "description": {"type": "string", "description": "The full description of the issue encountered by the customer."},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High"], "description": "The priority of the ticket (defaults to 'Medium')."},
                    "contact_id": {"type": "string", "description": "(Optional) The ID of the contact creating the ticket."},
                    "account_id": {"type": "string", "description": "(Optional) The ID of the account associated with the ticket."}
                },
                "required": ["subject", "description"],
                "description": "At least one of contact_id or account_id must be provided."
            },
        ),
        types.Tool(
            name="add_comment_to_case",
            description="Adds a comment (a note) to an existing support ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "The Salesforce ID of the ticket (e.g., '5005Y0000...')."},
                    "comment": {"type": "string", "description": "The content of the comment to add."},
                    "is_internal": {"type": "boolean", "description": "Set to 'true' for an internal note (not visible to the customer), 'false' for a public comment."}
                },
                "required": ["case_id", "comment"],
            },
        ),
        
        # --- Global Search Tool ---
        types.Tool(
            name="search_salesforce",
            description="Global search in Salesforce (Accounts, Contacts, Opportunities, Cases) with a search term.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The term to search for (e.g., 'Acme', 'Smith', 'Printer issue')."}
                },
                "required": ["query"],
            },
        ),
    ]

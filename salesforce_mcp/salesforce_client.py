import logging
from typing import Any, Literal
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)

class SalesforceClient:
    """A client for interacting with the Salesforce API."""
    def __init__(self, username: str, password: str, security_token: str, domain: str = 'login'):
        try:
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
            logger.info(f"Successfully connected to Salesforce for user {username} on domain {domain}.")
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")
            raise

    def _soql_query(self, query: str) -> list[dict[str, Any]]:
        """Executes a SOQL query and returns the results."""
        logger.debug(f"Executing SOQL: {query}")
        try:
            result = self.sf.query_all(query)
            return [dict(row) for row in result['records']]
        except Exception as e:
            logger.error(f"SOQL Error: {e}")
            raise

    def _sosl_search(self, query: str) -> list[dict[str, Any]]:
        """Executes a SOSL search."""
        logger.debug(f"Executing SOSL: {query}")
        try:
            result = self.sf.search(query)
            return [dict(row) for row in result.get('searchRecords', [])]
        except Exception as e:
            logger.error(f"SOSL Error: {e}")
            raise

    # --- Sales Cloud ---

    def search_contact(self, name: str, email: str | None = None) -> list[dict[str, Any]]:
        """Searches for a contact by name and optionally by email."""
        where_clauses = [f"Name LIKE '%{name}%'"]
        if email:
            where_clauses.append(f"Email = '{email}'")
        query = f"SELECT Id, Name, Email, Phone, Account.Name FROM Contact WHERE {' AND '.join(where_clauses)}"
        return self._soql_query(query)

    def get_account_details(self, account_name: str | None = None, account_id: str | None = None) -> list[dict[str, Any]]:
        """Retrieves details for an account by name or ID."""
        if not account_name and not account_id:
            raise ValueError("Either account_name or account_id must be provided.")
        
        where_clause = f"Id = '{account_id}'" if account_id else f"Name = '{account_name}'"
        query = f"SELECT Id, Name, Industry, Phone, Website, BillingStreet, BillingCity, BillingCountry FROM Account WHERE {where_clause} LIMIT 1"
        return self._soql_query(query)

    def list_open_opportunities(self, account_id: str | None = None, owner_email: str | None = None) -> list[dict[str, Any]]:
        """Lists open opportunities, filtered by account or owner."""
        where_clauses = ["IsClosed = false"]
        if account_id:
            where_clauses.append(f"AccountId = '{account_id}'")
        if owner_email:
            where_clauses.append(f"Owner.Email = '{owner_email}'")
        
        query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity WHERE {' AND '.join(where_clauses)}"
        return self._soql_query(query)

    def log_activity(self, related_to_id: str, subject: str, description: str) -> dict[str, Any]:
        """Logs a new task (activity) related to a record (Account, Contact, Opp, etc.)."""
        logger.info(f"Creating a task for {related_to_id}: {subject}")
        try:
            result = self.sf.Task.create({
                'WhoId': related_to_id,
                'WhatId': related_to_id,
                'Subject': subject,
                'Description': description,
                'Status': 'Completed'
            })
            return result
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            try:
                logger.debug("Attempting with WhatId only...")
                result = self.sf.Task.create({
                    'WhatId': related_to_id,
                    'Subject': subject,
                    'Description': description,
                    'Status': 'Completed'
                })
                return result
            except Exception as e2:
                logger.error(f"Second attempt to create task failed: {e2}")
                raise e2


    # --- Service Cloud ---

    def get_case_details(self, case_number: str) -> list[dict[str, Any]]:
        """Retrieves details for a case by its case number."""
        query = f"SELECT Id, CaseNumber, Subject, Status, Priority, Description, Contact.Name, Account.Name FROM Case WHERE CaseNumber = '{case_number}'"
        return self._soql_query(query)

    def list_open_cases(self, contact_email: str | None = None, account_name: str | None = None) -> list[dict[str, Any]]:
        """Lists open cases for a contact or account."""
        where_clauses = ["IsClosed = false"]
        if contact_email:
            where_clauses.append(f"Contact.Email = '{contact_email}'")
        if account_name:
            where_clauses.append(f"Account.Name = '{account_name}'")
            
        query = f"SELECT Id, CaseNumber, Subject, Status, Priority, Contact.Name FROM Case WHERE {' AND '.join(where_clauses)}"
        return self._soql_query(query)

    def create_case(self, subject: str, description: str, priority: Literal['Low', 'Medium', 'High'] = 'Medium', contact_id: str | None = None, account_id: str | None = None) -> dict[str, Any]:
        """Creates a new case."""
        if not contact_id and not account_id:
            raise ValueError("Either contact_id or account_id must be provided to create a case.")
            
        payload = {
            'Subject': subject,
            'Description': description,
            'Priority': priority,
            'Status': 'New',
            'ContactId': contact_id,
            'AccountId': account_id
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        logger.info(f"Creating a new case: {subject}")
        return self.sf.Case.create(payload)

    def add_comment_to_case(self, case_id: str, comment: str, is_internal: bool = True) -> dict[str, Any]:
        """Adds a comment (public or internal) to a case."""
        logger.info(f"Adding a comment to case {case_id}")
        return self.sf.CaseComment.create({
            'ParentId': case_id,
            'CommentBody': comment,
            'IsPublished': not is_internal
        })

    # --- Global Search ---

    def search_salesforce(self, query: str) -> list[dict[str, Any]]:
        """Executes a global search (SOSL) across multiple objects."""
        sosl_query = f"FIND '{{{query}}}' IN ALL FIELDS RETURNING Account(Id, Name), Contact(Id, Name, Email), Opportunity(Id, Name), Case(Id, CaseNumber, Subject)"
        return self._sosl_search(sosl_query)

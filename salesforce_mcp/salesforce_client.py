import logging
from typing import Any, Literal
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)

class SalesforceClient:
    """
    Classe encapsulant la logique métier pour interagir avec l'API Salesforce.
    C'est l'équivalent de votre classe BigQueryDatabase.
    """
    def __init__(self, username: str, password: str, security_token: str, domain: str = 'login'):
        try:
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain
            )
            logger.info(f"Connexion à Salesforce réussie pour l'utilisateur {username} sur le domaine {domain}.")
        except Exception as e:
            logger.error(f"Échec de la connexion à Salesforce: {e}")
            raise

    def _soql_query(self, query: str) -> list[dict[str, Any]]:
        """Exécute une requête SOQL et retourne les résultats."""
        logger.debug(f"Exécution SOQL: {query}")
        try:
            result = self.sf.query_all(query)
            # Convertit OrderedDict en dict pour une sérialisation JSON plus simple
            return [dict(row) for row in result['records']]
        except Exception as e:
            logger.error(f"Erreur SOQL: {e}")
            raise

    def _sosl_search(self, query: str) -> list[dict[str, Any]]:
        """Exécute une recherche SOSL."""
        logger.debug(f"Exécution SOSL: {query}")
        try:
            result = self.sf.search(query)
            # 'searchRecords' est la clé contenant les résultats
            return [dict(row) for row in result.get('searchRecords', [])]
        except Exception as e:
            logger.error(f"Erreur SOSL: {e}")
            raise

    # --- Fonctions Sales Cloud ---

    def search_contact(self, name: str, email: str | None = None) -> list[dict[str, Any]]:
        """Recherche un contact par nom et optionnellement par email."""
        where_clauses = [f"Name LIKE '%{name}%'"]
        if email:
            where_clauses.append(f"Email = '{email}'")
        query = f"SELECT Id, Name, Email, Phone, Account.Name FROM Contact WHERE {' AND '.join(where_clauses)}"
        return self._soql_query(query)

    def get_account_details(self, account_name: str | None = None, account_id: str | None = None) -> list[dict[str, Any]]:
        """Récupère les détails d'un compte par nom ou ID."""
        if not account_name and not account_id:
            raise ValueError("account_name ou account_id doit être fourni.")
        
        where_clause = f"Id = '{account_id}'" if account_id else f"Name = '{account_name}'"
        query = f"SELECT Id, Name, Industry, Phone, Website, BillingStreet, BillingCity, BillingCountry FROM Account WHERE {where_clause} LIMIT 1"
        return self._soql_query(query)

    def list_open_opportunities(self, account_id: str | None = None, owner_email: str | None = None) -> list[dict[str, Any]]:
        """Liste les opportunités ouvertes, filtrées par compte ou propriétaire."""
        where_clauses = ["IsClosed = false"]
        if account_id:
            where_clauses.append(f"AccountId = '{account_id}'")
        if owner_email:
            where_clauses.append(f"Owner.Email = '{owner_email}'")
        
        query = f"SELECT Id, Name, StageName, Amount, CloseDate, Account.Name FROM Opportunity WHERE {' AND '.join(where_clauses)}"
        return self._soql_query(query)

    def log_activity(self, related_to_id: str, subject: str, description: str) -> dict[str, Any]:
        """Consigne une nouvelle tâche (activité) liée à un enregistrement (Compte, Contact, Opp...)."""
        logger.info(f"Création d'une tâche pour {related_to_id}: {subject}")
        try:
            result = self.sf.Task.create({
                'WhoId': related_to_id, # Peut être Contact/Lead
                'WhatId': related_to_id, # Peut être Compte/Opp/Case...
                'Subject': subject,
                'Description': description,
                'Status': 'Completed' # Suppose que l'activité est déjà terminée
            })
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la création de la tâche: {e}")
            # Tenter de deviner s'il s'agit d'un WhoId ou WhatId
            try:
                logger.debug("Tentative avec WhatId uniquement...")
                result = self.sf.Task.create({
                    'WhatId': related_to_id,
                    'Subject': subject,
                    'Description': description,
                    'Status': 'Completed'
                })
                return result
            except Exception as e2:
                logger.error(f"Échec de la deuxième tentative de création de tâche: {e2}")
                raise e2


    # --- Fonctions Service Cloud ---

    def get_case_details(self, case_number: str) -> list[dict[str, Any]]:
        """Récupère les détails d'un ticket (Case) par son numéro."""
        query = f"SELECT Id, CaseNumber, Subject, Status, Priority, Description, Contact.Name, Account.Name FROM Case WHERE CaseNumber = '{case_number}'"
        return self._soql_query(query)

    def list_open_cases(self, contact_email: str | None = None, account_name: str | None = None) -> list[dict[str, Any]]:
        """Liste les tickets ouverts pour un contact ou un compte."""
        where_clauses = ["IsClosed = false"]
        if contact_email:
            where_clauses.append(f"Contact.Email = '{contact_email}'")
        if account_name:
            where_clauses.append(f"Account.Name = '{account_name}'")
            
        query = f"SELECT Id, CaseNumber, Subject, Status, Priority, Contact.Name FROM Case WHERE {' AND '.join(where_clauses)}"
        return self._soql_query(query)

    def create_case(self, subject: str, description: str, priority: Literal['Low', 'Medium', 'High'] = 'Medium', contact_id: str | None = None, account_id: str | None = None) -> dict[str, Any]:
        """Crée un nouveau ticket (Case)."""
        if not contact_id and not account_id:
            raise ValueError("contact_id ou account_id doit être fourni pour créer un ticket.")
            
        payload = {
            'Subject': subject,
            'Description': description,
            'Priority': priority,
            'Status': 'New',
            'ContactId': contact_id,
            'AccountId': account_id
        }
        # Filtre les valeurs None
        payload = {k: v for k, v in payload.items() if v is not None}
        logger.info(f"Création d'un nouveau ticket: {subject}")
        return self.sf.Case.create(payload)

    def add_comment_to_case(self, case_id: str, comment: str, is_internal: bool = True) -> dict[str, Any]:
        """Ajoute un commentaire (public ou interne) à un ticket."""
        logger.info(f"Ajout d'un commentaire au ticket {case_id}")
        return self.sf.CaseComment.create({
            'ParentId': case_id,
            'CommentBody': comment,
            'IsPublished': not is_internal
        })

    # --- Fonction de Recherche Globale ---

    def search_salesforce(self, query: str) -> list[dict[str, Any]]:
        """Exécute une recherche globale (SOSL) sur plusieurs objets."""
        sosl_query = f"FIND '{{{query}}}' IN ALL FIELDS RETURNING Account(Id, Name), Contact(Id, Name, Email), Opportunity(Id, Name), Case(Id, CaseNumber, Subject)"
        return self._sosl_search(sosl_query)

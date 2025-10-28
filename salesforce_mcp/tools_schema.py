import mcp.types as types

def get_tools_schema() -> list[types.Tool]:
    """
    Définit et retourne le schéma pour tous les tools Salesforce
    qui seront exposés au LLM.
    """
    return [
        # --- Outils Sales Cloud ---
        types.Tool(
            name="search_contact",
            description="Recherche un contact dans Salesforce par nom et optionnellement par email.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Le nom (ou partie du nom) du contact à rechercher."},
                    "email": {"type": "string", "description": "(Optionnel) L'email exact du contact pour affiner la recherche."}
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="get_account_details",
            description="Récupère les détails complets d'un compte client (entreprise) par son nom exact ou son ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {"type": "string", "description": "Le nom exact du compte (ex: 'Acme Corp')."},
                    "account_id": {"type": "string", "description": "L'ID Salesforce du compte (ex: '0015Y00002oR...')."}
                },
                "description": "Fournir soit account_name, soit account_id."
            },
        ),
        types.Tool(
            name="list_open_opportunities",
            description="Liste toutes les opportunités de vente (affaires) qui ne sont pas encore clôturées.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "(Optionnel) Filtre les opportunités pour un compte spécifique par son ID."},
                    "owner_email": {"type": "string", "description": "(Optionnel) Filtre les opportunités appartenant à un commercial spécifique par son email."}
                },
            },
        ),
        types.Tool(
            name="log_activity",
            description="Enregistre une activité (comme un appel ou un email) et l'associe à un enregistrement (Contact, Compte, Opportunité).",
            inputSchema={
                "type": "object",
                "properties": {
                    "related_to_id": {"type": "string", "description": "L'ID Salesforce de l'enregistrement auquel lier cette activité (ex: un ID de Contact ou de Compte)."},
                    "subject": {"type": "string", "description": "Le titre ou l'objet de l'activité (ex: 'Appel de suivi')."},
                    "description": {"type": "string", "description": "Une description détaillée de ce qui s'est passé durant l'activité."}
                },
                "required": ["related_to_id", "subject", "description"],
            },
        ),
        
        # --- Outils Service Cloud ---
        types.Tool(
            name="get_case_details",
            description="Récupère les détails d'un ticket de support (Case) en utilisant son numéro de ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_number": {"type": "string", "description": "Le numéro visible du ticket (ex: '00001234')."}
                },
                "required": ["case_number"],
            },
        ),
        types.Tool(
            name="list_open_cases",
            description="Liste tous les tickets de support ouverts, filtrés par email du contact ou nom du compte.",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_email": {"type": "string", "description": "(Optionnel) L'email du client pour trouver ses tickets."},
                    "account_name": {"type": "string", "description": "(Optionnel) Le nom exact du compte pour trouver ses tickets."}
                },
            },
        ),
        types.Tool(
            name="create_case",
            description="Crée un nouveau ticket de support pour un client.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Le titre du problème."},
                    "description": {"type": "string", "description": "La description complète du problème rencontré par le client."},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High"], "description": "La priorité du ticket (par défaut 'Medium')."},
                    "contact_id": {"type": "string", "description": "(Optionnel) L'ID du contact créant le ticket."},
                    "account_id": {"type": "string", "description": "(Optionnel) L'ID du compte associé au ticket."}
                },
                "required": ["subject", "description"],
                "description": "Il faut fournir au moins un contact_id ou un account_id."
            },
        ),
        types.Tool(
            name="add_comment_to_case",
            description="Ajoute un commentaire (une note) à un ticket de support existant.",
            inputSchema={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string", "description": "L'ID Salesforce du ticket (ex: '5005Y0000...')."},
                    "comment": {"type": "string", "description": "Le contenu du commentaire à ajouter."},
                    "is_internal": {"type": "boolean", "description": "Mettre à 'true' pour une note interne (non visible par le client), 'false' pour un commentaire public."}
                },
                "required": ["case_id", "comment"],
            },
        ),
        
        # --- Outil de Recherche Globale ---
        types.Tool(
            name="search_salesforce",
            description="Recherche globale dans Salesforce (Comptes, Contacts, Opportunités, Tickets) avec un terme de recherche.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Le terme à rechercher (ex: 'Acme', 'Dupont', 'Problème imprimante')."}
                },
                "required": ["query"],
            },
        ),
    ]

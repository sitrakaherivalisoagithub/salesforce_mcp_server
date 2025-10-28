import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

import click
import uvicorn
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
import mcp.types as types
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# Importations depuis nos modules locaux
from salesforce_mcp.event_store import InMemoryEventStore
from salesforce_mcp.salesforce_client import SalesforceClient
from salesforce_mcp.tools_schema import get_tools_schema

logger = logging.getLogger(__name__)

# --- Point d'entrée principal (main) avec Click et Uvicorn ---

@click.command()
@click.option("--port", default=3000, help="Port d'écoute pour HTTP", show_default=True)
@click.option("--host", default="127.0.0.1", help="Hôte sur lequel écouter", show_default=True)
@click.option("--sf-username", envvar="SF_USERNAME", required=True, help="Nom d'utilisateur Salesforce (ou via env var SF_USERNAME)")
@click.option("--sf-password", envvar="SF_PASSWORD", required=True, help="Mot de passe Salesforce (ou via env var SF_PASSWORD)")
@click.option("--sf-token", envvar="SF_TOKEN", required=True, help="Token de sécurité Salesforce (ou via env var SF_TOKEN)")
@click.option("--sf-domain", envvar="SF_DOMAIN", default="login", help="Domaine Salesforce ('login' pour prod, 'test' pour sandbox)", show_default=True)
@click.option("--log-level", default="INFO", help="Niveau de logging (DEBUG, INFO, WARNING, ERROR)", show_default=True)
def main(
    port: int,
    host: str,
    sf_username: str,
    sf_password: str,
    sf_token: str,
    sf_domain: str,
    log_level: str,
) -> int:
    """
    Démarre le MCP Server pour Salesforce.
    """
    # Configuration du logging
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Niveau de log invalide: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Réduire le bruit de certaines bibliothèques
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger.info(f"Démarrage du serveur MCP Salesforce sur http://{host}:{port}")

    # Initialisation du client logique Salesforce
    try:
        sf_client = SalesforceClient(
            username=sf_username,
            password=sf_password,
            security_token=sf_token,
            domain=sf_domain
        )
    except Exception as e:
        logger.error(f"Impossible d'initialiser le client Salesforce: {e}")
        return 1
    
    # Création du serveur MCP
    app = Server("salesforce-manager")

    # Enregistrement du handler list_tools
    @app.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        logger.debug("Appel de list_tools")
        return get_tools_schema()

    # Enregistrement du handler call_tool
    @app.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.ContentBlock]:
        logger.debug(f"Appel du tool: {name} avec les arguments: {arguments}")
        arguments = arguments or {}
        
        try:
            # Mapping des noms de tools aux fonctions du client
            tool_function_map = {
                "search_contact": sf_client.search_contact,
                "get_account_details": sf_client.get_account_details,
                "list_open_opportunities": sf_client.list_open_opportunities,
                "log_activity": sf_client.log_activity,
                "get_case_details": sf_client.get_case_details,
                "list_open_cases": sf_client.list_open_cases,
                "create_case": sf_client.create_case,
                "add_comment_to_case": sf_client.add_comment_to_case,
                "search_salesforce": sf_client.search_salesforce,
            }
            
            if name not in tool_function_map:
                raise ValueError(f"Tool inconnu : {name}")
                
            # Appel de la fonction correspondante avec les arguments dépackés
            results = tool_function_map[name](**arguments)
            
            # Conversion du résultat en ContentBlock
            # Nous utilisons str(results) pour une sérialisation simple.
            # Pour une meilleure lisibilité par le LLM, on pourrait utiliser json.dumps
            import json
            results_text = json.dumps(results, indent=2, default=str)
            
            return [types.TextContent(type="text", text=results_text)]
        
        except Exception as e:
            logger.error(f"Erreur lors de l'appel du tool '{name}': {e}", exc_info=True)
            return [types.TextContent(type="text", text=f"Erreur : {e}")]

    # --- Configuration Starlette/Uvicorn (identique à votre template) ---
    
    event_store = InMemoryEventStore()
    session_manager = StreamableHTTPSessionManager(app=app, event_store=event_store)

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        """Handler pour les requêtes HTTP streamables."""
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app_lifespan: Starlette) -> AsyncIterator[None]:
        """Gère le cycle de vie de l'application (démarrage/arrêt)."""
        async with session_manager.run():
            logger.info("Session manager démarré.")
            yield
            logger.info("Application en cours d'arrêt...")

    starlette_app = Starlette(
        debug=(log_level.upper() == "DEBUG"),
        routes=[Mount("/mcp", app=handle_streamable_http)],
        lifespan=lifespan,
    )

    # Démarrage du serveur Uvicorn
    uvicorn.run(
        starlette_app, 
        host=host, 
        port=port, 
        log_level=log_level.lower()
    )

    return 0

if __name__ == "__main__":
    main()

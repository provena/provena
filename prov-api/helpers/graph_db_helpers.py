from prov.model import ProvDocument  # type: ignore
from SharedInterfaces.RegistryModels import *
from fastapi import HTTPException, Depends
from random import randint
from config import Config, get_settings
from provdbconnector import ProvDb  # type: ignore
from provdbconnector.db_adapters.neo4j.neo4jadapter import Neo4jAdapter  # type: ignore
from helpers.neo4j_helpers import get_credentials


def mocked_graph_db_store() -> str:
    print("WARNING: Mocking database integration")
    return ''.join([str(i) for i in [randint(0, 9) for _ in range(10)]])


def upload_prov_document(
        id: str,
        prov_document: ProvDocument,
        config: Config
) -> str:
    """    upload_prov_document
        Wrapper method for uploading provenance document to backend store.
        Currently this is either a mocked graph store (just returns a random 
        id), or uses prov-db-connector to store the provenance document into 
        neo4j.

        Arguments
        ----------
        model_run_item : ItemModelRun
            The item model run - currently unused but may be helpful.
        prov_document : ProvDocument
            The provenance document (python-prov)

        Returns
        -------
         : str
            The id for the saving process - currently not used

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    if config.mock_graph_db:
        return mocked_graph_db_store()
    else:
        return neo4j_graph_db_store(
            id=id,
            prov_document=prov_document,
            config=config
        )


def neo4j_graph_db_store(
        id: str,
        prov_document: ProvDocument,
        config: Config
) -> str:
    """    neo4j_graph_db_store
        Uses prov-db-connector to save the python prov document 
        to a neo4j backend. the auth info, endpoint etc are defined
        in the config file. 

        The model run item is not used currently but might contain 
        information we need later. 

        The prov document is a python-prov document - prov-db-connector
        interfaces directly with this document type.


        Arguments
        ----------
        id: str
        prov_document : ProvDocument
            The prov document (python-prov)

        Returns
        -------
         : str
            The document ID that prov-db-connector generates, 
            currently not used.

        Raises
        ------
        HTTPException
            If an error occurs while connecting to the neo4j instance
        HTTPException
            If an error occurs while writing the python-prov prov
            document to the neo4j store

        See Also (optional)
        --------

        Examples (optional)
        --------
    """
    print("Writing prov document to neo4j backend.")

    user, password = get_credentials(config=config)

    # Connect to neo4j instance
    try:
        prov_connector = ProvDb(
            adapter=Neo4jAdapter,
            auth_info={
                "user_name": user,
                "user_password": password,
                "host": f"{config.neo4j_host}:{config.neo4j_port}",
                "encrypted": config.neo4j_encrypted,
            },
        )
    except Exception as e:
        print(
            f"Failed to connect to neo4j instance through prov-db-connector. Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to neo4j instance through prov-db-connector. Error: {e}"
        )

    # Write document to neo4j store through prov-db-connector API
    try:
        document_id = prov_connector.save_document(
            content=prov_document
        )
    except Exception as e:
        print(
            f"For record with ID: {id}, failed to save document to neo4j instance through prov-db-connector. Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"For record with ID: {id}, failed to save document to neo4j instance through prov-db-connector. Error: {e}"
        )

    return document_id

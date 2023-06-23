from typing import Any, Dict, List
from config import Config
from opensearchpy import OpenSearch

# Type alias query response for now
QueryResponse = Any


def text_multi_match_query_with_field_filter(match_text: str, match_filter: str, search_fields: List[str], must_match_field: str, size: int) -> Dict[str, Any]:
    return {
        "size": size,
        "query":
            {
                "bool": {
                    "must": [
                        {
                            "match": {
                                must_match_field: match_filter
                            }
                        },
                        {
                            "multi_match": {
                                # query and fields
                                "query": match_text,
                                "fields": search_fields,

                                # query setup
                                "type": "cross_fields",
                                "operator": "and",

                                # fine tuning params

                                # Fuzziness not allowed with cross fields match type

                                # "fuzziness": "AUTO",
                                # "fuzzy_transpositions": True,

                                # Allow type coercion
                                "lenient": True,
                                # Allow phrase re-arranging
                                "slop": 2
                            }
                        }
                    ]
                }
            }
    }


def text_multi_match_query(match_text: str, fields: List[str], size: int) -> Dict[str, Any]:
    return {
        "size": size,
        "query": {
            "multi_match": {
                # query and fields
                "query": match_text,
                "fields": fields,

                # query setup
                "type": "cross_fields",
                "operator": "and",

                # fine tuning params

                # Fuzziness not allowed with cross fields match type

                # "fuzziness": "AUTO",
                # "fuzzy_transpositions": True,

                # Allow type coercion
                "lenient": True,
                # Allow phrase re-arranging
                "slop": 2
            }
        }
    }


def linearised_query(match_text: str, size: int, config: Config) -> Dict[str, Any]:
    return {
        "size": size,
        "query": {
            "match": {
                config.linearised_field: {
                    # query and fields
                    "query": match_text,

                    # operator - AND or OR
                    "operator": "or",

                    # fine tuning params
                    "fuzziness": "AUTO",
                    "fuzzy_transpositions": True,

                    # Allow type coercion
                    "lenient": True,

                    # use the standard analyser
                    "analyzer": "standard"
                }
            }
        }
    }


def linearised_query_with_filter(match_text: str, must_match_field: str, match_filter: str, size: int, config: Config) -> Dict[str, Any]:
    return {
        "size": size,
        "query":
            {
                "bool": {
                    "must": [
                        {
                            "match": {
                                must_match_field: match_filter
                            }
                        },
                        {
                            "match": {
                                config.linearised_field: {
                                    # query and fields
                                    "query": match_text,
                                    # operator - AND or OR
                                    "operator": "or",

                                    # fine tuning params
                                    "fuzziness": "AUTO",
                                    "fuzzy_transpositions": True,

                                    # Allow type coercion
                                    "lenient": True,

                                    # use the standard analyser
                                    "analyzer": "standard"
                                }
                            }
                        }
                    ]
                }
            }
    }


def multi_match_query_index(index: str, query: str, fields: List[str], size: int, config: Config, client: OpenSearch) -> Any:
    print(
        f"Searching for query {query} on index {index} with fields {fields}.")
    return client.search(
        body=text_multi_match_query(
            size=size,
            match_text=query,
            fields=fields,
        ),
        index=index,
    )


def query_linearised_index(index: str, query: str, size: int, config: Config, client: OpenSearch) -> Any:
    print(
        f"Searching for query {query} using linearised/ngram index {index}.")
    return client.search(
        body=linearised_query(match_text=query, size=size, config=config),
        index=index,
    )


def query_linearised_index_with_filter(index: str, query: str, must_match_text: str, must_match_field: str, size: int, config: Config, client: OpenSearch) -> Any:
    print(
        f"Searching for query {query} using linearised/ngram index {index}.")
    return client.search(
        body=linearised_query_with_filter(
            match_text=query,
            size=size,
            config=config,
            must_match_field=must_match_field,
            match_filter=must_match_text
        ),
        index=index,
    )


def multi_match_query_index_with_filter(index: str, query: str, must_match_text: str, must_match_field: str, fields: List[str], size: int, config: Config, client: OpenSearch) -> Any:
    print(
        f"Searching for query {query} on index {index} with fields {fields}.")
    return client.search(
        body=text_multi_match_query_with_field_filter(
            size=size,
            match_text=query,
            search_fields=fields,
            match_filter=must_match_text,
            must_match_field=must_match_field
        ),
        index=index,
    )


def fetch_document(index: str, id: str, config: Config, client: OpenSearch) -> Any:
    return client.get(
        index=index,
        id=id
    )


def delete_document(index: str, id: str, config: Config, client: OpenSearch) -> Any:
    return client.delete(
        index=index,
        id=id
    )


def delete_index(index: str, config: Config, client: OpenSearch) -> Any:
    return client.indices.delete(index=index)

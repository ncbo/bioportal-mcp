################################################################################
# bioportal_mcp/main.py
# This module provides a FastMCP wrapper for the BioPortal API
################################################################################
import os
from typing import Any, Dict, List, Optional, Tuple
import requests
from fastmcp import FastMCP


# CONSTANTS
BIOPORTAL_API_BASE_URL = "https://data.bioontology.org"
BIOPORTAL_UI_BASE_URL = "https://bioportal.bioontology.org/ontologies"


# HELPER FUNCTIONS
def get_api_key(api_key: Optional[str] = None) -> str:
    """
    Get BioPortal API key from parameter or environment variable.

    Args:
        api_key: Optional API key provided directly.

    Returns:
        The API key string.

    Raises:
        ValueError: If no API key is provided or found in environment.
    """
    if api_key is None:
        api_key = os.getenv('BIOPORTAL_API_KEY')

    if api_key is None:
        raise ValueError(
            "BioPortal API key is required. Provide it as a parameter or set BIOPORTAL_API_KEY environment variable.")

    return api_key


def extract_ontology_info(result: Dict[str, Any]) -> Tuple[str, str]:
    """
    Extract ontology acronym and page URL from a BioPortal API result.

    Args:
        result: A dictionary containing BioPortal API result data.

    Returns:
        A tuple of (ontology_acronym, ontology_page_url).
    """
    ontology_acronym = ''
    ontology_page_url = ''

    if 'links' in result and 'ontology' in result['links']:
        ontology_url = result['links']['ontology']
        if ontology_url:
            # Extract acronym from URL like "https://data.bioontology.org/ontologies/NCIT"
            ontology_acronym = ontology_url.split('/')[-1]
            # Create BioPortal ontology page URL
            ontology_page_url = f"{BIOPORTAL_UI_BASE_URL}/{ontology_acronym}"

    return ontology_acronym, ontology_page_url


# API WRAPPER SECTION for BioPortal API
def search_bioportal(
    query: str,
    api_key: Optional[str] = None,
    ontologies: Optional[List[str]] = None,
    require_exact_match: bool = False,
    also_search_properties: bool = False,
    also_search_obsolete: bool = False,
    max_page_size: int = 50,
    max_records: Optional[int] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Search for ontology terms in BioPortal using the search endpoint.

    Args:
        query: The search term to look for.
        api_key: BioPortal API key. If not provided, will try to get from BIOPORTAL_API_KEY environment variable.
        ontologies: List of ontology acronyms to restrict search to (e.g., ['NCIT', 'GO']).
        require_exact_match: Whether to require exact matches only.
        also_search_properties: Whether to also search in ontology properties.
        also_search_obsolete: Whether to include obsolete terms in search.
        max_page_size: Maximum number of records to retrieve per API call.
        max_records: Maximum total number of records to retrieve.
        verbose: If True, print progress information during retrieval.

    Returns:
        A list of dictionaries, where each dictionary represents a search result.
        Each result contains class information including '@id', 'prefLabel', 'definition', etc.
    """
    api_key = get_api_key(api_key)
    endpoint_url = f"{BIOPORTAL_API_BASE_URL}/search"

    all_records = []
    page = 1

    while True:
        params = {
            "q": query,
            "apikey": api_key,
            "page": page,
            "pagesize": max_page_size,
            "require_exact_match": "true" if require_exact_match else "false",
            "also_search_properties": "true" if also_search_properties else "false",
            "also_search_obsolete": "true" if also_search_obsolete else "false",
        }

        if ontologies:
            params["ontologies"] = ",".join(ontologies)

        try:
            response = requests.get(endpoint_url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"Error fetching from BioPortal: {e}")
            break
        except ValueError as e:
            if verbose:
                print(f"Error parsing JSON response: {e}")
            break

        # BioPortal search returns results in 'collection' field
        if isinstance(data, dict) and 'collection' in data:
            records = data['collection']
        elif isinstance(data, list):
            records = data
        else:
            if verbose:
                print(f"Unexpected response format: {type(data)}")
            break

        if not records:
            break

        all_records.extend(records)

        if verbose:
            print(
                f"Fetched {len(records)} records from page {page}; total so far: {len(all_records)}")

        # Check if we've hit the max_records limit
        if max_records is not None and len(all_records) >= max_records:
            all_records = all_records[:max_records]
            if verbose:
                print(
                    f"Reached max_records limit: {max_records}. Stopping fetch.")
            break

        # BioPortal pagination: if we got fewer records than page size, we're done
        if len(records) < max_page_size:
            break

        page += 1

    return all_records


def search_properties_bioportal(
    query: str,
    api_key: Optional[str] = None,
    ontologies: Optional[List[str]] = None,
    require_exact_match: bool = False,
    also_search_views: bool = False,
    require_definitions: bool = False,
    ontology_types: Optional[List[str]] = None,
    property_types: Optional[List[str]] = None,
    max_page_size: int = 50,
    max_records: Optional[int] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Search for ontology properties in BioPortal using the property search endpoint.

    Args:
        query: The search term to look for in property labels and IDs.
        api_key: BioPortal API key. If not provided, will try to get from BIOPORTAL_API_KEY environment variable.
        ontologies: List of ontology acronyms to restrict search to (e.g., ['NCIT', 'GO']).
        require_exact_match: Whether to require exact matches only (by property id, label, or generated label).
        also_search_views: Whether to include ontology views in the search.
        require_definitions: Whether to filter results only to those that include definitions.
        ontology_types: List of ontology types to filter by (e.g., ['ONTOLOGY', 'VALUE_SET_COLLECTION']).
        property_types: List of property types to filter by (e.g., ['object', 'annotation', 'datatype']).
        max_page_size: Maximum number of records to retrieve per API call.
        max_records: Maximum total number of records to retrieve.
        verbose: If True, print progress information during retrieval.

    Returns:
        A list of dictionaries, where each dictionary represents a property search result.
        Each result contains property information including '@id', 'label', 'definition', etc.
    """
    api_key = get_api_key(api_key)
    endpoint_url = f"{BIOPORTAL_API_BASE_URL}/property_search"

    all_records = []
    page = 1

    while True:
        params = {
            "q": query,
            "apikey": api_key,
            "page": page,
            "pagesize": max_page_size,
            "require_exact_match": "true" if require_exact_match else "false",
            "also_search_views": "true" if also_search_views else "false",
            "require_definitions": "true" if require_definitions else "false",
        }

        if ontologies:
            params["ontologies"] = ",".join(ontologies)

        if ontology_types:
            params["ontology_types"] = ",".join(ontology_types)

        if property_types:
            params["property_types"] = ",".join(property_types)

        try:
            response = requests.get(endpoint_url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"Error fetching from BioPortal Property Search: {e}")
            break
        except ValueError as e:
            if verbose:
                print(f"Error parsing JSON response: {e}")
            break

        # BioPortal property search returns results in 'collection' field
        if isinstance(data, dict) and 'collection' in data:
            records = data['collection']
        elif isinstance(data, list):
            records = data
        else:
            if verbose:
                print(f"Unexpected response format: {type(data)}")
            break

        if not records:
            break

        all_records.extend(records)

        if verbose:
            print(
                f"Fetched {len(records)} property records from page {page}; total so far: {len(all_records)}")

        # Check if we've hit the max_records limit
        if max_records is not None and len(all_records) >= max_records:
            all_records = all_records[:max_records]
            if verbose:
                print(
                    f"Reached max_records limit: {max_records}. Stopping fetch.")
            break

        # BioPortal pagination: if we got fewer records than page size, we're done
        if len(records) < max_page_size:
            break

        page += 1

    return all_records


def get_analytics_bioportal(
    api_key: Optional[str] = None,
    ontology_acronym: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Get ontology analytics data from BioPortal using the analytics endpoint.

    Args:
        api_key: BioPortal API key. If not provided, will try to get from BIOPORTAL_API_KEY environment variable.
        ontology_acronym: Ontology acronym to get analytics for (e.g., 'NCIT'). If None, gets all analytics.
        month: Month number (1-12) for filtering analytics by month/year.
        year: Year for filtering analytics by month/year (e.g., 2024).
        verbose: If True, print progress information during retrieval.

    Returns:
        A dictionary containing analytics data. For all ontologies, returns a dictionary with ontology
        acronyms as keys. For a single ontology, returns detailed analytics including visitor stats by month/year.
    """
    api_key = get_api_key(api_key)

    # Determine endpoint based on ontology_acronym
    if ontology_acronym:
        endpoint_url = f"{BIOPORTAL_API_BASE_URL}/ontologies/{ontology_acronym}/analytics"
    else:
        endpoint_url = f"{BIOPORTAL_API_BASE_URL}/analytics"

    params = {
        "apikey": api_key,
    }

    # Add month/year parameters if provided (only valid for global analytics)
    if not ontology_acronym:
        if month is not None:
            params["month"] = str(month)
        if year is not None:
            params["year"] = str(year)

    try:
        response = requests.get(endpoint_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"Error fetching from BioPortal Analytics: {e}")
        return {}
    except ValueError as e:
        if verbose:
            print(f"Error parsing JSON response: {e}")
        return {}

    return data if isinstance(data, dict) else {}


# DISABLED for now to avoid overloading BioPortal API
# def annotate_text_bioportal(
#     text: str,
#     api_key: Optional[str] = None,
#     ontologies: Optional[List[str]] = None,
#     semantic_types: Optional[List[str]] = None,
#     expand_semantic_types_hierarchy: bool = False,
#     expand_class_hierarchy: bool = False,
#     class_hierarchy_max_level: int = 0,
#     expand_mappings: bool = False,
#     stop_words: Optional[List[str]] = None,
#     minimum_match_length: Optional[int] = None,
#     exclude_numbers: bool = False,
#     whole_word_only: bool = True,
#     exclude_synonyms: bool = False,
#     longest_only: bool = False,
#     verbose: bool = False,
# ) -> List[Dict[str, Any]]:
#     """
#     Annotate text using the BioPortal Annotator endpoint.

#     Args:
#         text: The text to annotate.
#         api_key: BioPortal API key. If not provided, will try to get from BIOPORTAL_API_KEY environment variable.
#         ontologies: List of ontology acronyms to use for annotation (e.g., ['NCIT', 'GO']).
#         semantic_types: List of UMLS semantic type identifiers to filter by.
#         expand_semantic_types_hierarchy: Use semantic types and their immediate children.
#         expand_class_hierarchy: Include ancestors of classes when annotating.
#         class_hierarchy_max_level: Depth of hierarchy to use (0 = no hierarchy).
#         expand_mappings: Use manual mappings (UMLS, REST, CUI, OBOXREF) in annotation.
#         stop_words: Custom list of stop words (case insensitive).
#         minimum_match_length: Minimum length of matched text.
#         exclude_numbers: Exclude annotations that are numbers.
#         whole_word_only: Match whole words only.
#         exclude_synonyms: Exclude synonym matches.
#         longest_only: Return only the longest match for a given phrase.
#         verbose: If True, print progress information during retrieval.

#     Returns:
#         A list of dictionaries, where each dictionary represents an annotation.
#         Each annotation contains information about the matched text, location, and associated ontology class.
#     """
#     # Get API key from parameter or environment
#     if api_key is None:
#         api_key = os.getenv('BIOPORTAL_API_KEY')

#     if api_key is None:
#         raise ValueError(
#             "BioPortal API key is required. Provide it as a parameter or set BIOPORTAL_API_KEY environment variable.")

#     base_url = "https://data.bioontology.org"
#     endpoint_url = f"{base_url}/annotator"

#     params = {
#         "text": text,
#         "apikey": api_key,
#         "expand_semantic_types_hierarchy": "true" if expand_semantic_types_hierarchy else "false",
#         "expand_class_hierarchy": "true" if expand_class_hierarchy else "false",
#         "class_hierarchy_max_level": class_hierarchy_max_level,
#         "expand_mappings": "true" if expand_mappings else "false",
#         "exclude_numbers": "true" if exclude_numbers else "false",
#         "whole_word_only": "true" if whole_word_only else "false",
#         "exclude_synonyms": "true" if exclude_synonyms else "false",
#         "longest_only": "true" if longest_only else "false",
#     }

#     if ontologies:
#         params["ontologies"] = ",".join(ontologies)

#     if semantic_types:
#         params["semantic_types"] = ",".join(semantic_types)

#     if stop_words:
#         params["stop_words"] = ",".join(stop_words)

#     if minimum_match_length is not None:
#         params["minimum_match_length"] = minimum_match_length

#     try:
#         response = requests.get(endpoint_url, params=params)
#         response.raise_for_status()
#         data = response.json()
#     except requests.exceptions.RequestException as e:
#         if verbose:
#             print(f"Error fetching from BioPortal Annotator: {e}")
#         return []
#     except ValueError as e:
#         if verbose:
#             print(f"Error parsing JSON response: {e}")
#         return []

#     # BioPortal annotator returns a list of annotations
#     if isinstance(data, list):
#         return data
#     else:
#         if verbose:
#             print(f"Unexpected response format: {type(data)}")
#         return []


# MCP TOOL SECTION
def search_ontology_terms(
    query: str,
    ontologies: Optional[str] = None,
    max_results: int = 10,
    require_exact_match: bool = False,
    api_key: Optional[str] = None
) -> List[Tuple[str, str, str, str]]:
    """
    Search for ontology terms in BioPortal.

    This function searches across BioPortal ontologies for terms matching the given query.
    It returns a list of tuples containing the term ID, preferred label, ontology, and ontology URL.

    Args:
        query: The search term (e.g., "melanoma", "breast cancer", "neuron").
        ontologies: Comma-separated list of ontology acronyms to search in (e.g., "NCIT,GO,HP").
                   If None, searches across all ontologies.
        max_results: Maximum number of results to return (default: 10).
        require_exact_match: If True, only return exact matches (default: False).
        api_key: BioPortal API key. If not provided, uses BIOPORTAL_API_KEY environment variable.

    Returns:
        List[Tuple[str, str, str, str]]: List of tuples where each tuple contains:
            - Term ID (e.g., "http://purl.obolibrary.org/obo/NCIT_C4872")
            - Preferred label (e.g., "Breast Cancer")
            - Ontology acronym (e.g., "NCIT")
            - Ontology URL (e.g., "https://bioportal.bioontology.org/ontologies/NCIT")

    Examples:
        # Search for cancer terms
        results = search_ontology_terms("cancer")

        # Search for cell types in Cell Ontology
        results = search_ontology_terms("neuron", ontologies="CL")

        # Search for exact matches only
        results = search_ontology_terms("melanoma", require_exact_match=True)
    """
    try:
        ontology_list = None
        if ontologies:
            ontology_list = [ont.strip() for ont in ontologies.split(",")]

        # Search using BioPortal API
        results = search_bioportal(
            query=query,
            api_key=api_key,
            ontologies=ontology_list,
            require_exact_match=require_exact_match,
            max_records=max_results,
            verbose=False
        )

        # Process results into simplified format
        processed_results = []
        for result in results[:max_results]:  # Ensure we don't exceed max_results
            term_id = result.get('@id', '')
            pref_label = result.get('prefLabel', '')

            # Extract ontology from links if available
            ontology_acronym, ontology_page_url = extract_ontology_info(result)

            if term_id and pref_label:
                processed_results.append(
                    (term_id, pref_label, ontology_acronym, ontology_page_url))

        return processed_results

    except Exception as e:
        print(f"Error searching BioPortal: {e}")
        return []


def search_ontology_properties(
    query: str,
    ontologies: Optional[str] = None,
    max_results: int = 10,
    require_exact_match: bool = False,
    require_definitions: bool = False,
    property_types: Optional[str] = None,
    api_key: Optional[str] = None
) -> List[Tuple[str, str, str, str]]:
    """
    Search for ontology properties in BioPortal.

    This function searches for ontology properties (object properties, annotation properties, 
    datatype properties) by their labels and IDs across BioPortal ontologies.

    Args:
        query: The search term (e.g., "has part", "related to", "has dimension").
        ontologies: Comma-separated list of ontology acronyms to search in (e.g., "NCIT,GO,HP").
                   If None, searches across all ontologies.
        max_results: Maximum number of results to return (default: 10).
        require_exact_match: If True, only return exact matches by property id, label, or generated label (default: False).
        require_definitions: If True, only return properties that have definitions (default: False).
        property_types: Comma-separated list of property types to filter by: "object", "annotation", "datatype".
                       If None, returns all property types.
        api_key: BioPortal API key. If not provided, uses BIOPORTAL_API_KEY environment variable.

    Returns:
        List[Tuple[str, str, str, str]]: List of tuples where each tuple contains:
            - Property ID (e.g., "http://www.w3.org/2000/01/rdf-schema#label")
            - Property label (e.g., "label")
            - Ontology acronym (e.g., "NCIT")
            - Ontology URL (e.g., "https://bioportal.bioontology.org/ontologies/NCIT")

    Examples:
        # Search for properties containing "part"
        results = search_ontology_properties("part")

        # Search for object properties only
        results = search_ontology_properties("related", property_types="object")

        # Search for properties with definitions in specific ontologies
        results = search_ontology_properties("has", ontologies="GO,CHEBI", require_definitions=True)
    """
    try:
        ontology_list = None
        if ontologies:
            ontology_list = [ont.strip() for ont in ontologies.split(",")]

        property_type_list = None
        if property_types:
            property_type_list = [pt.strip()
                                  for pt in property_types.split(",")]

        # Search using BioPortal Property Search API
        results = search_properties_bioportal(
            query=query,
            api_key=api_key,
            ontologies=ontology_list,
            require_exact_match=require_exact_match,
            require_definitions=require_definitions,
            property_types=property_type_list,
            max_records=max_results,
            verbose=False
        )

        # Process results into simplified format
        processed_results = []
        for result in results[:max_results]:  # Ensure we don't exceed max_results
            property_id = result.get('@id', '')

            # Try to get label, fall back to labelGenerated
            label = result.get('label', '')
            if not label:
                label = result.get('labelGenerated', '')

            # Extract ontology from links if available
            ontology_acronym, ontology_page_url = extract_ontology_info(result)

            if property_id and label:
                processed_results.append(
                    (property_id, label, ontology_acronym, ontology_page_url))

        return processed_results

    except Exception as e:
        print(f"Error searching BioPortal properties: {e}")
        return []


# DISABLED for now to avoid overloading BioPortal API
# def annotate_text(
#     text: str,
#     ontologies: Optional[str] = None,
#     longest_only: bool = False,
#     exclude_numbers: bool = False,
#     whole_word_only: bool = True,
#     api_key: Optional[str] = None
# ) -> List[Tuple[str, str, str, str, int, int]]:
#     """
#     Annotate text to find ontology terms mentioned in it.

#     This function analyzes text and identifies mentions of ontology terms, returning
#     information about each match including the matched text, class information, and location.

#     Args:
#         text: The text to annotate (e.g., "Melanoma is a malignant tumor of melanocytes").
#         ontologies: Comma-separated list of ontology acronyms to use (e.g., "NCIT,GO,HP").
#                    If None, uses all ontologies.
#         longest_only: If True, return only the longest match for overlapping annotations (default: False).
#         exclude_numbers: If True, exclude annotations that are purely numeric (default: False).
#         whole_word_only: If True, match whole words only (default: True).
#         api_key: BioPortal API key. If not provided, uses BIOPORTAL_API_KEY environment variable.

#     Returns:
#         List[Tuple[str, str, str, str, int, int]]: List of tuples where each tuple contains:
#             - Matched text (e.g., "Melanoma")
#             - Class ID (e.g., "http://purl.obolibrary.org/obo/NCIT_C3224")
#             - Preferred label (e.g., "Melanoma")
#             - Ontology acronym (e.g., "NCIT")
#             - Start position in text (e.g., 0)
#             - End position in text (e.g., 8)

#     Examples:
#         # Annotate medical text
#         results = annotate_text("Melanoma is a malignant tumor of melanocytes")

#         # Annotate with specific ontologies
#         results = annotate_text("breast cancer", ontologies="NCIT,DOID")

#         # Get only longest matches
#         results = annotate_text("breast cancer", longest_only=True)
#     """
#     try:
#         ontology_list = None
#         if ontologies:
#             ontology_list = [ont.strip() for ont in ontologies.split(",")]

#         # Annotate using BioPortal API
#         annotations = annotate_text_bioportal(
#             text=text,
#             api_key=api_key,
#             ontologies=ontology_list,
#             longest_only=longest_only,
#             exclude_numbers=exclude_numbers,
#             whole_word_only=whole_word_only,
#             verbose=False
#         )

#         # Process annotations into simplified format
#         processed_annotations = []
#         for annotation in annotations:
#             # Extract annotation information
#             annotations_data = annotation.get('annotations', [])
#             annotated_class = annotation.get('annotatedClass', {})

#             # Get class information
#             class_id = annotated_class.get('@id', '')
#             pref_label = annotated_class.get('prefLabel', '')

#             # Extract ontology from links
#             ontology_acronym = ''
#             if 'links' in annotated_class and 'ontology' in annotated_class['links']:
#                 ontology_url = annotated_class['links']['ontology']
#                 if ontology_url:
#                     ontology_acronym = ontology_url.split('/')[-1]

#             # Get all text positions for this annotation
#             for annot_detail in annotations_data:
#                 matched_text = annot_detail.get('text', '')
#                 start_pos = annot_detail.get('from', 0)
#                 end_pos = annot_detail.get('to', 0)

#                 if class_id and pref_label and matched_text:
#                     processed_annotations.append((
#                         matched_text,
#                         class_id,
#                         pref_label,
#                         ontology_acronym,
#                         start_pos,
#                         end_pos
#                     ))

#         return processed_annotations

#     except Exception as e:
#         print(f"Error annotating text with BioPortal: {e}")
#         return []


def get_ontology_analytics(
    ontology_acronym: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get visitor analytics for BioPortal ontologies.

    This function retrieves Google Analytics data for ontology visits. You can get analytics
    for all ontologies, filter by month/year, or get detailed analytics for a specific ontology.

    Args:
        ontology_acronym: Ontology acronym to get analytics for (e.g., "NCIT", "GO").
                         If None, returns analytics for all ontologies.
        month: Month number (1-12) to filter analytics. Only valid when ontology_acronym is None.
        year: Year to filter analytics (e.g., 2024). Only valid when ontology_acronym is None.
        api_key: BioPortal API key. If not provided, uses BIOPORTAL_API_KEY environment variable.

    Returns:
        Dict[str, Any]: Analytics data dictionary containing visitor statistics.
            - For all ontologies: returns dict with ontology acronyms as keys and visit counts
            - For single ontology: returns detailed analytics with monthly/yearly breakdowns

    Examples:
        # Get analytics for all ontologies
        analytics = get_ontology_analytics()

        # Get analytics for a specific ontology
        analytics = get_ontology_analytics(ontology_acronym="NCIT")

        # Get analytics for all ontologies in April 2024
        analytics = get_ontology_analytics(month=4, year=2024)

        # Get analytics for all ontologies in 2024
        analytics = get_ontology_analytics(year=2024)
    """
    try:
        # Get analytics using BioPortal API
        analytics_data = get_analytics_bioportal(
            api_key=api_key,
            ontology_acronym=ontology_acronym,
            month=month,
            year=year,
            verbose=False
        )

        return analytics_data

    except Exception as e:
        print(f"Error getting analytics from BioPortal: {e}")
        return {}


# MAIN SECTION
# Create the FastMCP instance
mcp = FastMCP("bioportal_mcp")

# Register all tools
mcp.tool(search_ontology_terms)
mcp.tool(search_ontology_properties)
mcp.tool(get_ontology_analytics)
# mcp.tool(annotate_text)


def main():
    """Main entry point for the application."""
    mcp.run()


if __name__ == "__main__":
    main()

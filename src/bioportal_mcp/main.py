################################################################################
# bioportal_mcp/main.py
# This module provides a FastMCP wrapper for the BioPortal API
################################################################################
import os
from typing import Any, Dict, List, Optional, Tuple
import requests
from fastmcp import FastMCP


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
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv('BIOPORTAL_API_KEY')

    if api_key is None:
        raise ValueError(
            "BioPortal API key is required. Provide it as a parameter or set BIOPORTAL_API_KEY environment variable.")

    base_url = "https://data.bioontology.org"
    endpoint_url = f"{base_url}/search"

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


def annotate_text_bioportal(
    text: str,
    api_key: Optional[str] = None,
    ontologies: Optional[List[str]] = None,
    semantic_types: Optional[List[str]] = None,
    expand_semantic_types_hierarchy: bool = False,
    expand_class_hierarchy: bool = False,
    class_hierarchy_max_level: int = 0,
    expand_mappings: bool = False,
    stop_words: Optional[List[str]] = None,
    minimum_match_length: Optional[int] = None,
    exclude_numbers: bool = False,
    whole_word_only: bool = True,
    exclude_synonyms: bool = False,
    longest_only: bool = False,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Annotate text using the BioPortal Annotator endpoint.

    Args:
        text: The text to annotate.
        api_key: BioPortal API key. If not provided, will try to get from BIOPORTAL_API_KEY environment variable.
        ontologies: List of ontology acronyms to use for annotation (e.g., ['NCIT', 'GO']).
        semantic_types: List of UMLS semantic type identifiers to filter by.
        expand_semantic_types_hierarchy: Use semantic types and their immediate children.
        expand_class_hierarchy: Include ancestors of classes when annotating.
        class_hierarchy_max_level: Depth of hierarchy to use (0 = no hierarchy).
        expand_mappings: Use manual mappings (UMLS, REST, CUI, OBOXREF) in annotation.
        stop_words: Custom list of stop words (case insensitive).
        minimum_match_length: Minimum length of matched text.
        exclude_numbers: Exclude annotations that are numbers.
        whole_word_only: Match whole words only.
        exclude_synonyms: Exclude synonym matches.
        longest_only: Return only the longest match for a given phrase.
        verbose: If True, print progress information during retrieval.

    Returns:
        A list of dictionaries, where each dictionary represents an annotation.
        Each annotation contains information about the matched text, location, and associated ontology class.
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv('BIOPORTAL_API_KEY')

    if api_key is None:
        raise ValueError(
            "BioPortal API key is required. Provide it as a parameter or set BIOPORTAL_API_KEY environment variable.")

    base_url = "https://data.bioontology.org"
    endpoint_url = f"{base_url}/annotator"

    params = {
        "text": text,
        "apikey": api_key,
        "expand_semantic_types_hierarchy": "true" if expand_semantic_types_hierarchy else "false",
        "expand_class_hierarchy": "true" if expand_class_hierarchy else "false",
        "class_hierarchy_max_level": class_hierarchy_max_level,
        "expand_mappings": "true" if expand_mappings else "false",
        "exclude_numbers": "true" if exclude_numbers else "false",
        "whole_word_only": "true" if whole_word_only else "false",
        "exclude_synonyms": "true" if exclude_synonyms else "false",
        "longest_only": "true" if longest_only else "false",
    }

    if ontologies:
        params["ontologies"] = ",".join(ontologies)

    if semantic_types:
        params["semantic_types"] = ",".join(semantic_types)

    if stop_words:
        params["stop_words"] = ",".join(stop_words)

    if minimum_match_length is not None:
        params["minimum_match_length"] = minimum_match_length

    try:
        response = requests.get(endpoint_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"Error fetching from BioPortal Annotator: {e}")
        return []
    except ValueError as e:
        if verbose:
            print(f"Error parsing JSON response: {e}")
        return []

    # BioPortal annotator returns a list of annotations
    if isinstance(data, list):
        return data
    else:
        if verbose:
            print(f"Unexpected response format: {type(data)}")
        return []


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
            ontology_acronym = ''
            ontology_page_url = ''
            if 'links' in result and 'ontology' in result['links']:
                ontology_url = result['links']['ontology']
                # Extract acronym from URL like "https://data.bioontology.org/ontologies/NCIT"
                if ontology_url:
                    ontology_acronym = ontology_url.split('/')[-1]
                    # Create BioPortal ontology page URL
                    ontology_page_url = f"https://bioportal.bioontology.org/ontologies/{ontology_acronym}"

            if term_id and pref_label:
                processed_results.append(
                    (term_id, pref_label, ontology_acronym, ontology_page_url))

        return processed_results

    except Exception as e:
        print(f"Error searching BioPortal: {e}")
        return []


def annotate_text(
    text: str,
    ontologies: Optional[str] = None,
    longest_only: bool = False,
    exclude_numbers: bool = False,
    whole_word_only: bool = True,
    api_key: Optional[str] = None
) -> List[Tuple[str, str, str, str, int, int]]:
    """
    Annotate text to find ontology terms mentioned in it.

    This function analyzes text and identifies mentions of ontology terms, returning
    information about each match including the matched text, class information, and location.

    Args:
        text: The text to annotate (e.g., "Melanoma is a malignant tumor of melanocytes").
        ontologies: Comma-separated list of ontology acronyms to use (e.g., "NCIT,GO,HP").
                   If None, uses all ontologies.
        longest_only: If True, return only the longest match for overlapping annotations (default: False).
        exclude_numbers: If True, exclude annotations that are purely numeric (default: False).
        whole_word_only: If True, match whole words only (default: True).
        api_key: BioPortal API key. If not provided, uses BIOPORTAL_API_KEY environment variable.

    Returns:
        List[Tuple[str, str, str, str, int, int]]: List of tuples where each tuple contains:
            - Matched text (e.g., "Melanoma")
            - Class ID (e.g., "http://purl.obolibrary.org/obo/NCIT_C3224")
            - Preferred label (e.g., "Melanoma")
            - Ontology acronym (e.g., "NCIT")
            - Start position in text (e.g., 0)
            - End position in text (e.g., 8)

    Examples:
        # Annotate medical text
        results = annotate_text("Melanoma is a malignant tumor of melanocytes")

        # Annotate with specific ontologies
        results = annotate_text("breast cancer", ontologies="NCIT,DOID")

        # Get only longest matches
        results = annotate_text("breast cancer", longest_only=True)
    """
    try:
        ontology_list = None
        if ontologies:
            ontology_list = [ont.strip() for ont in ontologies.split(",")]

        # Annotate using BioPortal API
        annotations = annotate_text_bioportal(
            text=text,
            api_key=api_key,
            ontologies=ontology_list,
            longest_only=longest_only,
            exclude_numbers=exclude_numbers,
            whole_word_only=whole_word_only,
            verbose=False
        )

        # Process annotations into simplified format
        processed_annotations = []
        for annotation in annotations:
            # Extract annotation information
            annotations_data = annotation.get('annotations', [])
            annotated_class = annotation.get('annotatedClass', {})

            # Get class information
            class_id = annotated_class.get('@id', '')
            pref_label = annotated_class.get('prefLabel', '')

            # Extract ontology from links
            ontology_acronym = ''
            if 'links' in annotated_class and 'ontology' in annotated_class['links']:
                ontology_url = annotated_class['links']['ontology']
                if ontology_url:
                    ontology_acronym = ontology_url.split('/')[-1]

            # Get all text positions for this annotation
            for annot_detail in annotations_data:
                matched_text = annot_detail.get('text', '')
                start_pos = annot_detail.get('from', 0)
                end_pos = annot_detail.get('to', 0)

                if class_id and pref_label and matched_text:
                    processed_annotations.append((
                        matched_text,
                        class_id,
                        pref_label,
                        ontology_acronym,
                        start_pos,
                        end_pos
                    ))

        return processed_annotations

    except Exception as e:
        print(f"Error annotating text with BioPortal: {e}")
        return []


# MAIN SECTION
# Create the FastMCP instance
mcp = FastMCP("bioportal_mcp")

# Register all tools
mcp.tool(search_ontology_terms)
mcp.tool(annotate_text)


def main():
    """Main entry point for the application."""
    mcp.run()


if __name__ == "__main__":
    main()

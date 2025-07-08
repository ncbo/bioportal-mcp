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
        raise ValueError("BioPortal API key is required. Provide it as a parameter or set BIOPORTAL_API_KEY environment variable.")
    
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
            print(f"Fetched {len(records)} records from page {page}; total so far: {len(all_records)}")
        
        # Check if we've hit the max_records limit
        if max_records is not None and len(all_records) >= max_records:
            all_records = all_records[:max_records]
            if verbose:
                print(f"Reached max_records limit: {max_records}. Stopping fetch.")
            break
        
        # BioPortal pagination: if we got fewer records than page size, we're done
        if len(records) < max_page_size:
            break
            
        page += 1
    
    return all_records


# MCP TOOL SECTION
def search_ontology_terms(
    query: str,
    ontologies: Optional[str] = None,
    max_results: int = 10,
    require_exact_match: bool = False,
    api_key: Optional[str] = None
) -> List[Tuple[str, str, str]]:
    """
    Search for ontology terms in BioPortal.
    
    This function searches across BioPortal ontologies for terms matching the given query.
    It returns a list of tuples containing the term ID, preferred label, and ontology.
    
    Args:
        query: The search term (e.g., "melanoma", "breast cancer", "neuron").
        ontologies: Comma-separated list of ontology acronyms to search in (e.g., "NCIT,GO,HP").
                   If None, searches across all ontologies.
        max_results: Maximum number of results to return (default: 10).
        require_exact_match: If True, only return exact matches (default: False).
        api_key: BioPortal API key. If not provided, uses BIOPORTAL_API_KEY environment variable.
    
    Returns:
        List[Tuple[str, str, str]]: List of tuples where each tuple contains:
            - Term ID (e.g., "http://purl.obolibrary.org/obo/NCIT_C4872")
            - Preferred label (e.g., "Breast Cancer")
            - Ontology acronym (e.g., "NCIT")
    
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
            if 'links' in result and 'ontology' in result['links']:
                ontology_url = result['links']['ontology']
                # Extract acronym from URL like "https://data.bioontology.org/ontologies/NCIT"
                if ontology_url:
                    ontology_acronym = ontology_url.split('/')[-1]
            
            if term_id and pref_label:
                processed_results.append((term_id, pref_label, ontology_acronym))
        
        return processed_results
        
    except Exception as e:
        print(f"Error searching BioPortal: {e}")
        return []


# MAIN SECTION
# Create the FastMCP instance
mcp = FastMCP("bioportal_mcp")

# Register all tools
mcp.tool(search_ontology_terms)


def main():
    """Main entry point for the application."""
    mcp.run()


if __name__ == "__main__":
    main()

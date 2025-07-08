import pytest
from unittest.mock import Mock, patch
from bioportal_mcp.main import search_bioportal, search_ontology_terms


def test_reality():
    assert 1 == 1


@pytest.fixture
def mock_bioportal_response():
    """Mock response for BioPortal search API."""
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "collection": [
            {
                "@id": "http://purl.obolibrary.org/obo/NCIT_C2926",
                "prefLabel": "Melanoma",
                "definition": ["A malignant tumor of melanocytes."],
                "links": {
                    "ontology": "https://data.bioontology.org/ontologies/NCIT"
                }
            },
            {
                "@id": "http://purl.obolibrary.org/obo/MONDO_0005105", 
                "prefLabel": "melanoma",
                "definition": ["A malignant neoplasm comprised of melanocytes."],
                "links": {
                    "ontology": "https://data.bioontology.org/ontologies/MONDO"
                }
            }
        ]
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_search_bioportal(mock_bioportal_response):
    """Test the basic BioPortal search functionality."""
    with patch("requests.get", return_value=mock_bioportal_response):
        results = search_bioportal(
            query="melanoma",
            api_key="test_key",
            max_page_size=10
        )
    
    assert len(results) == 2
    assert results[0]["prefLabel"] == "Melanoma"
    assert results[1]["prefLabel"] == "melanoma"


def test_search_ontology_terms(mock_bioportal_response):
    """Test the search_ontology_terms tool function."""
    with patch("requests.get", return_value=mock_bioportal_response):
        results = search_ontology_terms(
            query="melanoma",
            api_key="test_key",
            max_results=10
        )
    
    assert len(results) == 2
    # Check tuple format: (id, label, ontology)
    assert results[0] == ("http://purl.obolibrary.org/obo/NCIT_C2926", "Melanoma", "NCIT")
    assert results[1] == ("http://purl.obolibrary.org/obo/MONDO_0005105", "melanoma", "MONDO")


def test_search_ontology_terms_with_ontology_filter(mock_bioportal_response):
    """Test searching with specific ontologies."""
    with patch("requests.get", return_value=mock_bioportal_response):
        results = search_ontology_terms(
            query="melanoma",
            ontologies="NCIT,MONDO",
            api_key="test_key"
        )
    
    assert len(results) == 2


def test_search_bioportal_missing_api_key():
    """Test that missing API key raises appropriate error."""
    with patch.dict('os.environ', {}, clear=True):  # Clear environment variables
        with pytest.raises(ValueError, match="BioPortal API key is required"):
            search_bioportal(query="test")


def test_search_ontology_terms_error_handling():
    """Test error handling in search_ontology_terms."""
    with patch("bioportal_mcp.main.search_bioportal", side_effect=Exception("API Error")):
        results = search_ontology_terms(query="test", api_key="test_key")
        assert results == []

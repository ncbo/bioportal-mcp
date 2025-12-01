# bioportal-mcp

A Model Context Protocol (MCP) server for interacting with the BioPortal API to search and retrieve ontology terms.

## Features

- **Search ontology terms**: Search across BioPortal's extensive collection of biomedical ontologies
- **Search ontology properties**: Find object properties, annotation properties, and datatype properties
- **Get ontology analytics**: Access visitor statistics and usage analytics for ontologies
- **Flexible filtering**: Filter by specific ontologies (e.g., NCIT, GO, HP, MONDO)
- **Exact matching**: Option to require exact matches or allow fuzzy matching
- **Rich results**: Returns term IDs, preferred labels, ontology information, and ontology page URLs

## Installation

You can install the package from source:

```bash
pip install -e .
```

Or using uv:

```bash
uv pip install -e .
```

## Setup

Before using this MCP server, you need to obtain a BioPortal API key:

1. Visit [BioPortal](https://bioportal.bioontology.org/)
2. Create an account or sign in
3. Go to your account settings to get your API key
4. Set the API key as an environment variable:

```bash
export BIOPORTAL_API_KEY="your_api_key_here"
```

## Usage

### As an MCP Server

Run the MCP server:

```bash
bioportal-mcp
```

### Available Tools

#### `search_ontology_terms`

Search for ontology terms in BioPortal.

**Parameters:**
- `query` (str): The search term (e.g., "melanoma", "breast cancer", "neuron")
- `ontologies` (str, optional): Comma-separated list of ontology acronyms (e.g., "NCIT,GO,HP")
- `max_results` (int, default=10): Maximum number of results to return
- `require_exact_match` (bool, default=False): Whether to require exact matches
- `api_key` (str, optional): BioPortal API key (uses environment variable if not provided)

**Returns:**
List of tuples containing:
- Term ID (e.g., "http://purl.obolibrary.org/obo/NCIT_C4872")
- Preferred label (e.g., "Breast Cancer") 
- Ontology acronym (e.g., "NCIT")
- Ontology URL (e.g., "https://bioportal.bioontology.org/ontologies/NCIT")

**Examples:**
```python
# Search for cancer terms
results = search_ontology_terms("cancer")

# Search for cell types in Cell Ontology  
results = search_ontology_terms("neuron", ontologies="CL")

# Search for exact matches only
results = search_ontology_terms("melanoma", require_exact_match=True)

# Limit results
results = search_ontology_terms("disease", max_results=5)
```

#### `search_ontology_properties`

Search for ontology properties (object properties, annotation properties, datatype properties) by their labels and IDs.

**Parameters:**
- `query` (str): The search term (e.g., "has part", "related to", "has dimension")
- `ontologies` (str, optional): Comma-separated list of ontology acronyms (e.g., "NCIT,GO,HP")
- `max_results` (int, default=10): Maximum number of results to return
- `require_exact_match` (bool, default=False): Whether to require exact matches by property id, label, or generated label
- `require_definitions` (bool, default=False): If True, only return properties that have definitions
- `property_types` (str, optional): Comma-separated list of property types to filter by: "object", "annotation", "datatype"
- `api_key` (str, optional): BioPortal API key (uses environment variable if not provided)

**Returns:**
List of tuples containing:
- Property ID (e.g., "http://www.w3.org/2000/01/rdf-schema#label")
- Property label (e.g., "label")
- Ontology acronym (e.g., "NCIT")
- Ontology URL (e.g., "https://bioportal.bioontology.org/ontologies/NCIT")

**Examples:**
```python
# Search for properties containing "part"
results = search_ontology_properties("part")

# Search for object properties only
results = search_ontology_properties("related", property_types="object")

# Search for properties with definitions in specific ontologies
results = search_ontology_properties("has", ontologies="GO,CHEBI", require_definitions=True)
```

#### `get_ontology_analytics`

Get visitor analytics for BioPortal ontologies using Google Analytics data.

**Parameters:**
- `ontology_acronym` (str, optional): Ontology acronym to get analytics for (e.g., "NCIT", "GO"). If None, returns analytics for all ontologies
- `month` (int, optional): Month number (1-12) to filter analytics. Only valid when ontology_acronym is None
- `year` (int, optional): Year to filter analytics (e.g., 2024). Only valid when ontology_acronym is None
- `api_key` (str, optional): BioPortal API key (uses environment variable if not provided)

**Returns:**
Dictionary containing visitor statistics:
- For all ontologies: dict with ontology acronyms as keys and visit counts
- For single ontology: detailed analytics with monthly/yearly breakdowns

**Examples:**
```python
# Get analytics for all ontologies
analytics = get_ontology_analytics()

# Get analytics for a specific ontology
analytics = get_ontology_analytics(ontology_acronym="NCIT")

# Get analytics for all ontologies in April 2024
analytics = get_ontology_analytics(month=4, year=2024)

# Get analytics for all ontologies in 2024
analytics = get_ontology_analytics(year=2024)
```

### Integration with AI Assistants

This MCP server can be integrated with AI assistants like Claude Desktop. Add the following to your MCP configuration:

```json
{
  "mcpServers": {
    "bioportal": {
      "command": "bioportal-mcp",
      "env": {
        "BIOPORTAL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

A streamable version of this MCP is also available from the following URL:

```
https://bioportal.fastmcp.app/mcp
```

This means it may be used through any agentic framework supporting HTTP streaming of MCPs.

## API Endpoints Supported

This MCP server provides access to the following BioPortal API endpoints:

- **Search** (`/search`): Search for ontology terms/classes across all ontologies
- **Property Search** (`/property_search`): Search for ontology properties (object, annotation, datatype)
- **Analytics** (`/analytics`): Retrieve visitor statistics and usage analytics for ontologies

### Supported Ontologies

BioPortal hosts hundreds of ontologies. Some popular ones include:

- **NCIT**: NCI Thesaurus - comprehensive cancer terminology
- **GO**: Gene Ontology - gene and protein functions
- **HP**: Human Phenotype Ontology - phenotypes and clinical features
- **MONDO**: Disease ontology
- **CHEBI**: Chemical entities
- **UBERON**: Anatomy ontology
- **CL**: Cell Ontology
- **SO**: Sequence Ontology

## Development

### Local Setup

```bash
# Clone the repository
git clone https://github.com/ncbo/bioportal-mcp.git
cd bioportal-mcp

# Install development dependencies
uv pip install -e ".[dev]"
```


## License

BSD-3-Clause

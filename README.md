# bioportal-mcp

A Model Context Protocol (MCP) server for interacting with the BioPortal API to search and retrieve ontology terms.

## Features

- **Search ontology terms**: Search across BioPortal's extensive collection of biomedical ontologies
- **Flexible filtering**: Filter by specific ontologies (e.g., NCIT, GO, HP, MONDO)
- **Exact matching**: Option to require exact matches or allow fuzzy matching
- **Rich results**: Returns term IDs, preferred labels, and ontology information

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

### Examples

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

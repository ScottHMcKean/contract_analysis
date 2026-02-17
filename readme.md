# Contract Analysis

Analyze contracts using generative AI on Databricks. The pipeline parses contract documents, extracts key information, classifies them (master agreement vs. amendment vs. SOW vs. termination), and pulls detailed metadata for contract management systems.

## Notebooks

Run these in order. Each notebook has widget parameters at the top (catalog, schema, etc.) and markdown explanations before every step.

### 01_parse -- Download, Read, Parse
Downloads contract PDFs from Cook County open data, reads them into a Delta `bytes` table, parses with `AI_PARSE_DOCUMENT`, and flattens into a `flat` table with full text, preamble (first 100 words), and truncated text (first 5000 words).

### 02_extract -- References and Doc Info
Uses an LLM to extract two things from each contract: (1) referenced agreements and documents, and (2) key document info (agreement name, type, dates, master/amendment status). Outputs `references` and `doc_info` tables.

### 03_assemble -- Vector Search and Context Assembly
Creates a `sections` table from parsed documents, sets up Databricks Vector Search indexes, then assembles a comprehensive context table per contract. Each row includes the document's own info plus folder-level related documents and semantically similar documents from vector search.

### 04_classify -- Contract Classification
Classifies each document: is it a master agreement, does it have amendments, what are the initial and final expiry dates. Uses the assembled context from step 3. Outputs a `classified` table with rationale and confidence scores.

### 05_metadata -- Detailed Metadata Extraction
Extracts detailed metadata for each contract type using field definitions from `metadata.csv` and prompt templates from `prompt_{type}.md`. Supports four contract types: master_agreement, amendment, scope_of_work, termination.

## Supporting Files

- `metadata.csv` -- field definitions per contract type (name, description, allowed values)
- `prompt_{type}.md` -- base prompt templates for each contract type
- `cook_county_contracts.parquet` -- source data from Cook County open data portal
- `*_file_names.csv` -- optional file lists to filter which contracts to process
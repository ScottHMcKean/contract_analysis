# Contract Analysis 

This code base contains code for analyzing contracts using generative AI. It follows a multi-step process where we parse and extract key information from the contracts. We then bring that information back together to classify the sequence of contracts and extract pertinent metadata from them for entering into a contract management system like Icertis. The code base is meant to be simple and broken down into the following steps.

## 1: Read Contracts (01_read)
Ingest raw contract documents from the source system or storage location to ensure all relevant contracts are available for analysis. We take the bytes and save them into a delta table so we can parallelize.

## 2: Parse Contracts (02_parse)
Extract text and structure from the ingested contract files, converting them into a machine-readable format for downstream processing. This is the most compute demanding and lengthy step, since we are parsing every single contract in the database.

## 3: Backup or Sample Contracts (03_backup_sample)
Create backups or generate representative samples of the parsed contracts to safeguard data and enable efficient testing. 

## 4: Flatten Contract Data (04_flatten)
Normalize and flatten the contract data structure to simplify subsequent extraction and analysis steps. This extracts a preamble, text, and truncated text so that we have something to pass to the LLM.

## 5: Get Document Info (06_doc_info)
Identify and extract references such as parties, related agreements, and cross-referenced clauses within the contracts.

## 6: Extract Key Document Information
Use generative AI models to extract important clauses, entities, and high-level metadata from the contracts.

## 7: Set Up Vector Search Indexes
Index the extracted contract data using vector search to enable semantic search and retrieval of relevant contract sections.

## 8: Classify Agreements and Sequence Contracts
Classify contracts by type, risk, or other relevant categories, and sequence related agreements for contextual analysis.

## 9: Extract Detailed Metadata from All Agreements
Extract comprehensive metadata from each agreement to support integration with contract management systems and downstream business processes.
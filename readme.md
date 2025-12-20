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

## 5: Get Document References (05_doc_info)
Identify and extract references such as parties, related agreements, and cross-referenced clauses within the contracts.

## 6: Extract Key Document Information (06_doc_info)
Use generative AI models to extract important clauses, entities, and high-level metadata from the contracts.

## 7: Set Up Vector Search Indexes (07_vector_search)
This is a notebook that sets up vector searches for retrieving key information from the contracts. It grabs some key information.
Index the extracted contract data using vector search to enable semantic search and retrieval of relevant contract sections.

## 8: Assemble (08_assemble)
This is a tricky SQL query that pulls together the above information - it takes documents from the same folder as the document being analyzed and pulls the key information and preamble. It also runs vector search on semantically similar documents and puts the doc_info and preamble for the top 5 docs as additional metadata for the model.

## 9: Classify Master Agreements, Dates, and Sequencing (09_classify)
We pull all the above work together and use the LLM to classify the summarized documents, concisely stating whether the document being analyzed is a master agreement or not, and providing the referenced agreements. 

## 10: Extract Detailed Metadata from All Agreements (10_metadata)
Once we have all the master agreements, we focus solely on the master agreements and extract comprehensive metadata from each agreement to support integration with contract management systems and downstream business processes.
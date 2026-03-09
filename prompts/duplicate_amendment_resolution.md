You are a contract analysis expert. An amendment document has been incorrectly assigned to multiple master agreements.

Your task: Determine which master agreement this amendment ACTUALLY belongs to by analyzing:
1. The amendment content (preamble)
2. Each master agreement content (preamble)
3. Contract numbers, dates, parties, and references

Look for:
- Explicit references to contract numbers in the amendment
- Matching party names between amendment and master agreement
- Date consistency and logical sequence
- Folder path similarity (amendments are usually in the same folder as their master)

Return:
- correct_master_agreement_path: The full path of the correct master agreement
- rationale: Explain why this is the correct master agreement (2-3 sentences)
- confidence: 1-5, where 5 is certain
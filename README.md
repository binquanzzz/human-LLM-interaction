# Interaction Smells in Human-LLM Collaborative Code Generation: Phenomena, Distribution, and Mitigation


📂 Project Structure
.
├── raw_code_related_data/           # Original datasets (LMSYS-CHAT-1M, WildChat)
├── disentangled_filter_coding_data/ # Processed coding data (66,371 records)
├── disentangled_raw_data/           # Disentangled data without filtering (81,366 records)
├── sample_mult-turn/                # 378 sampled cases for analysis
├── manual_annotation/               # Labels for RQ1 and RQ2
└── MetaGPT-InCE/                    # Source code for InCE framework

📝 Detailed Description

1. raw_code_related_data
Contains the foundation datasets extracted from open-source corpora:

LMSYS-CHAT-1M.jsonl: Raw code-specific dialogue data.

WildChat.jsonl: Original interaction logs.

2. disentangled_filter_coding_data
Refined data that has been disentangled and filtered specifically for programming tasks:

disentangled_filter_coding_data_all.jsonl: The complete coding dataset (66,371 records).

disentangled_filter_coding_data_1.jsonl: Segmented files for storage and processing.

3. disentangled_raw_data
The dataset after the disentanglement process but before programming-specific filtering:

disentangled_raw_data_all.jsonl: Contains the full set of 81,366 records.

4. sample_mult-turn
A curated collection of 378 sampled multi-turn interactions used for qualitative analysis.

5. manual_annotation
Expert-labeled data used for research analysis:

RQ1 Labels: Identifying types of interaction smells.

RQ2 Labels: Mapping the distribution of these phenomena.

6. MetaGPT-InCE
The official source code for InCE (Interaction-Centered Enhancement), a framework built to mitigate interaction smells in collaborative code generation.

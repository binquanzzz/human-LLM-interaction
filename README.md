# Interaction Smells in Human-LLM Collaborative Code Generation: Phenomena, Distribution, and Mitigation

This repository contains the datasets, manual annotations, and source code for our study on interaction smells in Human-LLM Collaborative Code Generation.


# 📂 Project Structure

```text
.
├── MetaGPT-InCE/                          # Source code for InCE framework
│
├── disentangled_filter_coding_data/       # Processed coding data (66,371 records)
│
├── disentangled_raw_data/                 # Disentangled data without filtering (81,366 records)
│
├── manual_annotation/                     # Labels for RQ1 and RQ2
│
├── raw_code_related_data/                 # Original datasets (LMSYS-CHAT-1M, WildChat)
│
├── sample_mult-turn/                      # 378 sampled cases for analysis

```

# 📝 Detailed Description

## 1. **raw_code_related_data**

  Contains the foundation datasets extracted from open-source corpora:
  
  LMSYS-CHAT-1M.jsonl
  
  WildChat.jsonl

## 2. **disentangled_raw_data**

  This directory contains the full dataset after the disentanglement process. It consists of 81,366 records split across 16 files for easier handling:

  disentangled_raw_data_1.jsonl
  
  disentangled_raw_data_2.jsonl
  
  ...
  
  disentangled_raw_data_16.jsonl

## 3. **disentangled_filter_coding_data**

  This directory contains the final dataset used for analysis. These records were filtered from the disentangled data to strictly retain coding-related interactions. It consists of 66,371 records split across 14 files:
  
  disentangled_filter_coding_data_1.jsonl

  disentangled_filter_coding_data_1.jsonl

  ...

  disentangled_filter_coding_data_14.jsonl
  

## 4. **sample_mult-turn**

  A curated collection of 378 sampled multi-turn interactions used for qualitative analysis.

## 5. **manual_annotation**

  Manually Annotated Data for Research Analysis:
  
  RQ1 Annotations: Identification of interaction smell types from real-world dialogues (sourced from LMSYS-CHAT-1M and WildChat).
  
  RQ2 Annotations: Distribution of interaction smells across six mainstream LLMs.

## **6. MetaGPT-InCE**

Invariant-aware Constraint Evolution (InCE) is a dedicated framework designed to address prevalent interaction issues like Must-Do Omit and Partial Functionality Breakdown.

### ⚙️ InCE Installation & Usage

**Installation**
Ensure that Python 3.9+ (but less than 3.12) is installed. 
Using Conda:
```text
conda create -n metagpt python=3.9 && conda activate metagpt
```
Install Dependencies:
```text
pip install --upgrade metagpt
```

**Execution**
Run the multi-turn evaluation script with the following command:
```text
python InCE/main_multi_wildbench.py \
  --jsonl_file InCE/input_data/input.jsonl \
  --output_file InCE/output_data/output.jsonl \
  --n_round 11 \
  --real_time_save True
```




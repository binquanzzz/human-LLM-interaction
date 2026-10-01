# **What Hinders Effective Interaction? An Empirical Study of Interaction Smells in** Human–LLM Programming

This repository contains the datasets and manual annotations for our study on interaction smells in human–LLM collaborative code generation.

## 📂 Project Structure

```
.
├── rq1_Interaction_Smells_Taxonomy/               # Interaction smell taxonomy
│   ├── raw_data/                                  # Original datasets
│   │   ├── lmsys_chat_1m_raw.jsonl
│   │   └── wildchat_raw.jsonl
│   │
│   ├── disentangled_raw_data/                     # Disentangled data without filtering
│   │   ├── disentangled_raw_data_1.jsonl
│   │   ├── ...
│   │   └── disentangled_raw_data_16.jsonl
│   │
│   ├── disentangled_filter_coding_data/           # Filtered coding-related interactions
│   │   ├── disentangled_filter_coding_data_1.jsonl
│   │   ├── ...
│   │   └── disentangled_filter_coding_data_14.jsonl
│   │
│   ├── sampled_interactions/                      # 378 sampled multi-turn interactions
│   │   └── lmsys_wildchat_multi_turn_sample_378.jsonl
│   │
│   └── manual_annotations/                        # Manually reviewed interaction smell annotations
│       └── lmsys_wildchat_multi_turn_smell_annotations.jsonl
│
├── rq2_Cross-Model_Distribution/                  # Interaction smell distribution across models
│   ├── source_tasks/                              # 170 coding tasks selected from wildBench
│   │   └── wildbench_coding_tasks_170.jsonl
│   │
│   ├── generated_interactions/                   # Automatically generated interactions with six models
│   │   ├── gpt-5_interactions.jsonl
│   │   ├── deepseek-v3_interactions.jsonl
│   │   ├── gemini-3-flash_interactions.jsonl
│   │   ├── qwen2.5-32b_interactions.jsonl
│   │   ├── qwen2.5-72b_interactions.jsonl
│   │   └── qwen3-235b-a22b_interactions.jsonl
│   │
│   ├── interaction_smell_annotations/            # Interaction smell annotations for each model
│   │   ├── gpt-5_smell_annotations.jsonl
│   │   ├── deepseek-v3_smell_annotations.jsonl
│   │   ├── gemini-3-flash_smell_annotations.jsonl
│   │   ├── qwen2.5-32b_smell_annotations.jsonl
│   │   ├── qwen2.5-72b_smell_annotations.jsonl
│   │   └── qwen3-235b-a22b_smell_annotations.jsonl
│   │
│   └── human_validation/                        # Human validation of scoring, detection, and consistency
│       ├── scoring_reliability_and_smell_detection_adjusted.jsonl
│       └── human_sim_consistency.jsonl
│
├── rq3_Associated_Factors/                       # Factors associated with interaction smells
│   └── wildbench_task_instruction.jsonl          # Data with task and instruction dimensions
│
└── rq4_Repairability/                            # Repairability of interaction smells
    ├── LLM_self_repair_outputs/                  # Self-repair results by smell, model, and strategy
    │   ├── ambiguous_instruction/
    │   │   ├── deepseek-chat_strategy_1.jsonl
    │   │   ├── deepseek-chat_strategy_2.jsonl
    │   │   ├── deepseek-chat_strategy_3.jsonl
    │   │   └── ...                              # Same naming pattern for the other models
    │   ├── code_rollback/
    │   ├── cross_turn_inconsistency/
    │   ├── incomplete_instruction/
    │   ├── must_do_omission/
    │   ├── must_not_violation/
    │   ├── partial_functionality_breakdown/
    │   ├── repetitive_response/
    │   └── signature_mismatch/                  # Each smell folder follows the same file structure
    │
    ├── expert_guided_repair_inputs/              # Cases not successfully repaired by the three strategies
    │   ├── deepseek-chat.jsonl
    │   ├── gemini-3-flash.jsonl
    │   ├── gpt-5.jsonl
    │   ├── qwen2.5-32b.jsonl
    │   ├── qwen2.5-72b.jsonl
    │   └── qwen3-235b-a22b.jsonl
    │
    ├── expert_guided_repair_outputs/             # Expert-guided repair results by smell and model
    │   ├── ambiguous_instruction/
    │   │   ├── deepseek-chat.jsonl
    │   │   ├── gemini-3-flash.jsonl
    │   │   ├── gpt-5.jsonl
    │   │   ├── qwen2.5-32b.jsonl
    │   │   ├── qwen2.5-72b.jsonl
    │   │   └── qwen3-235b-a22b.jsonl
    │   ├── code_rollback/
    │   ├── cross_turn_inconsistency/
    │   ├── incomplete_instruction/
    │   ├── must_do_omission/
    │   ├── must_not_violation/
    │   ├── partial_functionality_breakdown/
    │   ├── repetitive_response/
    │   └── signature_mismatch/                  # Each smell folder follows the same file structure
    │
    └── repair_strategy_prompts/                 # Prompt templates for the three repair strategies
        ├── strategy_1.md
        ├── strategy_2.md
        └── strategy_3.md
```



## 📝 Detailed Description

### 1. rq1_Interaction_Smells_Taxonomy

Contains the datasets and manual annotations used to develop the interaction smell taxonomy from real-world human–LLM conversations.

#### raw_data

Contains the original data from LMSYS-CHAT-1M and WildChat:

- `lmsys_chat_1m_raw.jsonl`
- `wildchat_raw.jsonl`

#### disentangled_raw_data

Contains the data after conversation disentanglement, before filtering for coding-related interactions. The dataset contains 81,366 records distributed across 16 JSONL files, from `disentangled_raw_data_1.jsonl` to `disentangled_raw_data_16.jsonl`.

#### disentangled_filter_coding_data

Contains the coding-related interactions retained after filtering the disentangled data. The dataset contains 66,371 records distributed across 14 JSONL files, from `disentangled_filter_coding_data_1.jsonl` to `disentangled_filter_coding_data_14.jsonl`.

#### sampled_interactions

Contains 378 sampled multi-turn interactions used for manual analysis and taxonomy development. The sample was selected at a 95% confidence level with a ±5% margin of error.

- `lmsys_wildchat_multi_turn_sample_378.jsonl`

#### manual_annotations

Contains the manually reviewed interaction smell annotations used to identify and characterize smell types in the sampled conversations.

- `lmsys_wildchat_multi_turn_smell_annotations.jsonl`

### 2. rq2_Cross-Model_Distribution

Contains the source tasks, generated interactions, smell annotations, and human validation data used to examine interaction smell distributions across six LLMs.

#### source_tasks

Contains 170 coding tasks selected from WildBench to generate interactions with the evaluated models.

- `wildbench_coding_tasks_170.jsonl`

#### generated_interactions

Contains automatically generated interaction records for GPT-5, DeepSeek-V3, Gemini-3-Flash, Qwen2.5-32B, Qwen2.5-72B, and Qwen3-235B-A22B. Each model has a separate JSONL file:

- `gpt-5_interactions.jsonl`
- `deepseek-v3_interactions.jsonl`
- `gemini-3-flash_interactions.jsonl`
- `qwen2.5-32b_interactions.jsonl`
- `qwen2.5-72b_interactions.jsonl`
- `qwen3-235b-a22b_interactions.jsonl`

#### interaction_smell_annotations

Contains the interaction smell annotations corresponding to each model’s generated interactions. Files follow the naming pattern `<model>_smell_annotations.jsonl`:

- `gpt-5_smell_annotations.jsonl`
- `deepseek-v3_smell_annotations.jsonl`
- `gemini-3-flash_smell_annotations.jsonl`
- `qwen2.5-32b_smell_annotations.jsonl`
- `qwen2.5-72b_smell_annotations.jsonl`
- `qwen3-235b-a22b_smell_annotations.jsonl`

#### human_validation

Contains human validation data for scoring reliability, smell detection, and consistency between human and simulated interactions:

- `scoring_reliability_and_smell_detection_adjusted.jsonl`: Adjusted data from human checks of scoring reliability and smell detection.
- `human_sim_consistency.jsonl`: Human assessment data for consistency between human and simulated interactions.

### 3. rq3_Associated_Factors

Contains the data used to investigate task and instruction factors associated with interaction smells.

- `wildbench_task_instruction.jsonl`: WildBench data with task-level and instruction-level dimensions used in the associated-factor analysis.

### 4. rq4_Repairability

Contains LLM self-repair results, expert-guided repair inputs and outputs, and prompt templates for the three repair strategies.

#### LLM_self_repair_outputs

Contains LLM self-repair outputs organized by interaction smell type. Each smell folder contains separate files for each model under each of the three repair strategies.

The nine smell folders are:

- `ambiguous_instruction/`
- `code_rollback/`
- `cross_turn_inconsistency/`
- `incomplete_instruction/`
- `must_do_omission/`
- `must_not_violation/`
- `partial_functionality_breakdown/`
- `repetitive_response/`
- `signature_mismatch/`

Files follow the naming pattern `<model>_strategy_<number>.jsonl`. For example:

- `deepseek-chat_strategy_1.jsonl`
- `deepseek-chat_strategy_2.jsonl`
- `deepseek-chat_strategy_3.jsonl`

The same naming pattern is used for the other models in each smell folder.

#### expert_guided_repair_inputs

Contains cases that remained unresolved after the three LLM self-repair strategies and were subsequently used as inputs for expert-guided repair. Cases are grouped by model:

- `deepseek-chat.jsonl`
- `gemini-3-flash.jsonl`
- `gpt-5.jsonl`
- `qwen2.5-32b.jsonl`
- `qwen2.5-72b.jsonl`
- `qwen3-235b-a22b.jsonl`

#### expert_guided_repair_outputs

Contains the results of expert-guided repair, organized into the same nine smell folders as `LLM_self_repair_outputs/`.

Each smell folder contains one JSONL file per model, using the same model filenames as `expert_guided_repair_inputs/`.

#### repair_strategy_prompts

Contains the prompt templates used for the three LLM self-repair strategies:

- `strategy_1.md`: Prompt template for Strategy 1.
- `strategy_2.md`: Prompt template for Strategy 2.
- `strategy_3.md`: Prompt template for Strategy 3.
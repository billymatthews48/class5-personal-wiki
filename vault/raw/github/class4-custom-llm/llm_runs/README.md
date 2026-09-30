# Run folders

Each folder is one complete notebook run. It holds the config, corpus, split, tokenization,
inspection, loss history, samples, temperature comparison, checkpoint, `model.pt`,
`model_untrained.pt`, eval separation and full untrained/final language-eval results.
The results ZIPs duplicate these folders, so they are kept locally and not published.

| Label | Folder | Notebook | What it is |
|---|---|---|---|
| **A** | [20260922T231357_098765Z](20260922T231357_098765Z/) | [custom_llm_A_starter.ipynb](../custom_llm_A_starter.ipynb) | Required starter-corpus experiment (3,000 steps) |
| **B** | [20260923T003152_798951Z](20260923T003152_798951Z/) | [custom_llm_B2_extended.ipynb](../custom_llm_B2_extended.ipynb) | Required expanded-corpus experiment: v2 teaching corpus, 3,000 steps |
| B-v1 | [20260923T000319_361728Z](20260923T000319_361728Z/) | [custom_llm_B_extended.ipynb](../custom_llm_B_extended.ipynb) | First expanded-corpus attempt: v1 "strict" teaching corpus, 3,000 steps |
| A-6k | [20260923T033614_161710Z](20260923T033614_161710Z/) | [custom_llm_A_6000steps.ipynb](../custom_llm_A_6000steps.ipynb) | Control: starter corpus, 6,000 steps |
| **B-6k (final model)** | [20260923T003555_129361Z](20260923T003555_129361Z/) | [custom_llm_B2_6000steps.ipynb](../custom_llm_B2_6000steps.ipynb) | v2 teaching corpus, 6,000 steps. Used for the chat. |

The 10-step setup smoke test is not published, because it is not experiment evidence.

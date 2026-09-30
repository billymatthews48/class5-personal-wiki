---
subject_key: custom-llm
wiki_id: subj-custom-llm
topic: Projects
source_count: 12
generated_by: gemma4:e4b-it-q4_K_M
generated: '2026-09-30'
reviewed: false
---
# Custom LLM Training

Billy's coursework involved training a custom, tiny language model using Andrej Karpathy's nanoGPT from scratch. The project required selecting a corpus, training the model, and testing its performance using a set of fixed, synthetic language evaluations.

## Key ideas
- The training involved two experiments: one using a starter corpus and another including custom teaching material. ([[raw/github/class4-custom-llm/README.md|class4-custom-llm / README]])
- The model training utilized nanoGPT, a small word-token transformer implemented with PyTorch. ([[raw/github/class4-custom-llm/ASSIGNMENT.md|class4-custom-llm / ASSIGNMENT]])
- The evaluation process used 48 fixed, synthetic language evals to guide corpus changes and track progress. ([[raw/github/class4-custom-llm/EXPERIMENT_LOG.md|class4-custom-llm / EXPERIMENT_LOG]])
- The model's learned word-token embeddings were a key component to inspect during the training process. ([[raw/github/class4-custom-llm/COURSE_README.md|class4-custom-llm / COURSE_README]])
- Language evaluation scores were based on four-choice next-word selections, where 1 indicated the highest probability. ([[raw/github/class4-custom-llm/results/eval_comparison.md|results / eval_comparison]])
- The project required documenting decisions, predictions, and actual outcomes in an experiment log. ([[raw/github/class4-custom-llm/EXPERIMENT_LOG.md|class4-custom-llm / EXPERIMENT_LOG]])

## Related
- [[Technology Adoption Curves]]: Both subjects involve the implementation and testing of a specific technology (LLM vs. adoption curve concept).
- [[Quantitative Methods]]: Both subjects involve the use of structured data and metrics for evaluation and analysis.

## Sources
- [[raw/github/class4-custom-llm/ASSIGNMENT.md|class4-custom-llm / ASSIGNMENT]]
- [[raw/github/class4-custom-llm/COURSE_README.md|class4-custom-llm / COURSE_README]]
- [[raw/github/class4-custom-llm/EXPERIMENT_LOG.md|class4-custom-llm / EXPERIMENT_LOG]]
- [[raw/github/class4-custom-llm/README.md|class4-custom-llm / README]]
- [[raw/github/class4-custom-llm/STUDENT_README.md|class4-custom-llm / STUDENT_README]]
- [[raw/github/class4-custom-llm/corpus/README.md|corpus / README]]
- [[raw/github/class4-custom-llm/evals/README.md|evals / README]]
- [[raw/github/class4-custom-llm/examples/language-evals/README.md|language-evals / README]]
- [[raw/github/class4-custom-llm/legacy/README.md|legacy / README]]
- [[raw/github/class4-custom-llm/legacy/microgpt/README.md|microgpt / README]]
- [[raw/github/class4-custom-llm/llm_runs/README.md|llm_runs / README]]
- [[raw/github/class4-custom-llm/results/eval_comparison.md|results / eval_comparison]]

## My Notes


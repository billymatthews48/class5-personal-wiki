---
subject_key: custom-llm
wiki_id: subj-custom-llm
topic: Projects
source_count: 12
generated_by: gemma4:e4b-it-q4_K_M
generated: '2026-09-30'
reviewed: true
---
# Custom LLM Training

Billy's coursework involved training a custom, tiny language model using Andrej Karpathy's nanoGPT from scratch. The project required selecting a corpus, training the model, and testing its performance using a set of fixed, synthetic language evaluations.

## Key ideas
- The training involved two experiments: one using a starter corpus and another including custom teaching material. ([[raw/github/class4-custom-llm/README.md|class4-custom-llm / README]])
- The model training utilized nanoGPT, a small word-token transformer implemented with PyTorch. ([[raw/github/class4-custom-llm/ASSIGNMENT.md|class4-custom-llm / ASSIGNMENT]])
- The evaluation process used 48 fixed, synthetic language evals to guide corpus changes and track progress. ([[raw/github/class4-custom-llm/EXPERIMENT_LOG.md|class4-custom-llm / EXPERIMENT_LOG]])
- The model's learned word-token embeddings were a key component to inspect during the training process. ([[raw/github/class4-custom-llm/COURSE_README.md|class4-custom-llm / COURSE_README]])
- Each language eval is a four-choice next-word selection: a case scores 1 when the correct word has the highest probability, and 0 otherwise. ([[raw/github/class4-custom-llm/results/eval_comparison.md|results / eval_comparison]])
- The project required documenting decisions, predictions, and actual outcomes in an experiment log. ([[raw/github/class4-custom-llm/EXPERIMENT_LOG.md|class4-custom-llm / EXPERIMENT_LOG]])

## Related
- [[Quantitative Methods]]: The Cambridge machine learning lecture covers learning from data in theory; this project trains a small transformer and measures it on 48 fixed evals.
- [[Secure Networking Tracker]]: Both are Billy's GitHub software projects, documented through their READMEs.

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


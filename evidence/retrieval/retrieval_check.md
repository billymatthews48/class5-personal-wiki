# Retrieval check (no generation)

time 2026-09-30T00:51:55 | internet: reachable | embed model embeddinggemma

| Test | Method | Expected source rank(s) in top 5 |
|---|---|---|
| T1 | keyword (BM25) | [2] |
| T1 | hybrid (BM25 + embeddinggemma) | [1] |
| T2 | keyword (BM25) | MISSING |
| T2 | hybrid (BM25 + embeddinggemma) | [4] |
| T3 | keyword (BM25) | [3, 4] |
| T3 | hybrid (BM25 + embeddinggemma) | [2, 4] |
| T4 | keyword (BM25) | n/a (unsupported question) |
| T4 | hybrid (BM25 + embeddinggemma) | n/a (unsupported question) |

## Detail

### T1 - keyword (BM25)
Q: According to my personal development notes, what are the three components of career success and how much does each matter?

1. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.pdf` (page 3) bm25 17.16 cosine None
2. `raw/cambridge/Electives/Personal development/Session 1.docx` (section 'Personal development') bm25 16.85 cosine None
3. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.pdf` (page 2) bm25 16.19 cosine None
4. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.docx` (opening) bm25 15.76 cosine None
5. `raw/cambridge/Exams/MS4 Finance and accounting/Lectures/Dauderis, H. and Annand, D. (2014) Introduction to Financial Accounting.pdf` (page 653) bm25 15.68 cosine None

### T1 - hybrid (BM25 + embeddinggemma)
Q: According to my personal development notes, what are the three components of career success and how much does each matter?

1. `raw/cambridge/Electives/Personal development/Session 1.docx` (section 'Personal development') bm25 16.85 cosine 0.559
2. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.docx` (opening) bm25 13.52 cosine 0.404
3. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.docx` (opening) bm25 15.76 cosine 0.387
4. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.pdf` (page 3) bm25 17.16 cosine 0.378
5. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.pdf` (page 2) bm25 16.19 cosine 0.377

### T2 - keyword (BM25)
Q: What price gap between the US and Switzerland did I use as a real-world pricing example?

1. `raw/cambridge/First week/MS6 Marketing/Exam/Final draft.docx` (opening) bm25 15.61 cosine None
2. `raw/cambridge/Electives/Macroeconomics/Supervision 2.docx` (opening) bm25 15.12 cosine None
3. `raw/cambridge/First week/MS6 Marketing/Exam/First draft.docx` (section 'Tata Motors and the auto industry') bm25 14.77 cosine None
4. `raw/cambridge/First week/MS5 Operations Management/Lectures/Week 4 - Quality Improvement.docx` (section 'Expected service – perceived service gap'; section 'White Bread company example') bm25 14.55 cosine None
5. `raw/cambridge/First week/MS6 Marketing/Lectures/Week 5 - Pricing.docx` (section 'Measuring price sensitivity') bm25 14.33 cosine None

### T2 - hybrid (BM25 + embeddinggemma)
Q: What price gap between the US and Switzerland did I use as a real-world pricing example?

1. `raw/cambridge/First week/MS5 Operations Management/Lectures/Week 4 - Quality Improvement.docx` (section 'Expected service – perceived service gap'; section 'White Bread company example') bm25 14.55 cosine 0.334
2. `raw/mba/Group 112 Economics Memo.docx` (opening) bm25 11.72 cosine 0.392
3. `raw/cambridge/First week/MS6 Marketing/Lectures/Week 8 unfinished.docx` (section 'Scalable price targeting – Dube and Misra (2017)') bm25 11.98 cosine 0.338
4. `raw/mba/Example in the Wild 3.docx` (opening) bm25 9.56 cosine 0.547
5. `raw/cambridge/Week 2/MS3 Micro economics/Supervisions/Billy Matthews MS3 Supervision 3.docx` (section 'Supervision 3 Answers') bm25 10.15 cosine 0.353

### T3 - keyword (BM25)
Q: Who was the client for my Cambridge consulting project, and how did we plan to gather primary data?

1. `raw/cambridge/Electives/Project/Project management.docx` (section 'Project management') bm25 26.43 cosine None
2. `raw/cambridge/Electives/Project/Project management.docx` (section 'Benn Lawson lecture') bm25 20.63 cosine None
3. `raw/cambridge/Mott Project/Intro and project definition .docx` (opening) bm25 19.57 cosine None
4. `raw/cambridge/Electives/Project/PID.docx` (section 'Address:') bm25 19.31 cosine None
5. `raw/mba/Power and Pol essay.txt` (opening) bm25 18.7 cosine None

### T3 - hybrid (BM25 + embeddinggemma)
Q: Who was the client for my Cambridge consulting project, and how did we plan to gather primary data?

1. `raw/cambridge/Mott Project/Discussion draft.docx` (opening) bm25 17.68 cosine 0.429
2. `raw/cambridge/Electives/Project/PID.docx` (section 'Address:') bm25 19.31 cosine 0.397
3. `raw/cambridge/Mott Project/Notes from first few meetings.docx` (opening) bm25 12.62 cosine 0.516
4. `raw/cambridge/Mott Project/Intro and project definition .docx` (opening) bm25 19.57 cosine 0.385
5. `raw/cambridge/Electives/Project/Project management.docx` (section 'Benn Lawson lecture') bm25 20.63 cosine 0.384

### T4 - keyword (BM25)
Q: What mark did I receive for my Strategic Management individual essay?

1. `raw/cambridge/Exams/MS4 Finance and accounting/Lectures/Dauderis, H. and Annand, D. (2014) Introduction to Financial Accounting.pdf` (page 502) bm25 12.99 cosine None
2. `raw/cambridge/Week 2/OB Question/1114l_MS1_ESSAY.docx` (opening) bm25 12.25 cosine None
3. `raw/cambridge/Electives/Project/Project management.docx` (section 'Benn Lawson lecture') bm25 11.39 cosine None
4. `raw/cambridge/First week/MS6 Marketing/Lectures/Week 4 - Product.docx` (section 'Strategic brand management decisions') bm25 11.0 cosine None
5. `raw/cambridge/Electives/Negotiations/Assesment/1114L_NW_JOURNAL.pdf` (page 1) bm25 10.08 cosine None

### T4 - hybrid (BM25 + embeddinggemma)
Q: What mark did I receive for my Strategic Management individual essay?

1. `raw/cambridge/Electives/Strategic management/Supervisions & assessment/Assessment/1114L-MSE12-INDIVIDUAL-ESSAY.pdf` (page 1) bm25 9.52 cosine 0.465
2. `raw/cambridge/Electives/Strategic management/Supervisions & assessment/Assessment/1114L-MSE12-INDIVIDUAL-ESSAY.docx` (opening) bm25 7.23 cosine 0.422
3. `raw/cambridge/Electives/Strategic management/Crib sheet.docx` (section 'Reading Notes') bm25 5.15 cosine 0.411
4. `raw/cambridge/First week/MS6 Marketing/Lectures/Week 4 - Product.docx` (section 'Strategic brand management decisions') bm25 11.0 cosine 0.356
5. `raw/cambridge/Paper 1/MS1 Organizational Behaviour/Lectures/OB revision.docx` (opening) bm25 5.79 cosine 0.399

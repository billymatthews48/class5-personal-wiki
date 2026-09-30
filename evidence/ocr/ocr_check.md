# Local OCR check (optional extension)

- **Engine:** Tesseract 5.4.0.20240606 (UB-Mannheim build), `eng` language data.
- **Rendering:** pypdfium2, pages rendered at 2x scale.
- **Offline:** everything runs locally.
- **When OCR runs:** only for PDFs whose pages have no text layer.
- **Gate:** a page is indexed only if Tesseract's mean word confidence is at least 70. The per-page confidence comes from `image_to_data`.

Measured 2026-09-29 on the 10 PDFs that previously produced 0 passages:

| File | Pages | Pages kept | Median page confidence |
|---|---|---|---|
| Billy_Matthews_MS2_Supervision 1_Group 34.pdf | 6 | 0 | 46.2 |
| Billy_Matthews_MS2_Supervision2_Group34.pdf | 4 | 0 | 45.5 |
| Billy_Matthews_MS2_Supervision3_Group34.pdf | 5 | 0 | 45.8 |
| Billy_Matthews_MS2_Supervision4_Group34.pdf | 3 | 0 | 46.1 |
| Billy_Matthews_MS4_Supervision 2.pdf | 3 | 0 | 40.4 |
| Billy_Matthews_MS4_Supervision 3.pdf | 3 | 0 | 46.2 |
| Billy_Matthews_MS4_Supervision 4.pdf | 4 | 0 | 43.2 |
| MS6_Group7_BillyMatthews.pdf | 2 | 0 | 41.4 |
| Billy Matthews_MS3_Supervision 1.pdf | 8 | 0 | 39.7 |
| Marketing Summary - Sarah.pdf | 15 | **15** | **90.8** |

**Result:**
- The typed but image-only marketing summary is now searchable.
- The nine supervisions are handwritten (phone scans made with CamScanner). Tesseract reads them as noise. For example, the first OCR attempt on MS4 Supervision 2 returned
  "al 7 | é (20) LB Q 30 J ie (75 Ter i 2 ...". The confidence gate keeps that noise out of the index.

**Limitation / next step:** handwriting needs a handwriting-capable local model, such as TrOCR. Until then, those nine files stay in
`raw/` and the Source Catalog, but they are not searchable.

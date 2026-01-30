# ASR Model Conventions Analysis & Guideline Generation

## Overview

This analysis script automatically extracts formatting conventions adopted by each ASR model (e.g. Whisper, Canary, Parakeet) across different language datasets.

The objective is to make the guideline definition process scalable. 
By identifying formatting tendencies **per model and per language**, we can derive annotation conventions that are tailored to:

- The selected transcription model  
- The target language or country  
- The specific project context  

Annotation conventions do not depend solely on the model, they also depend on the linguistic conventions of the language on which the model is applied.

This tool enables empirical identification of those tendencies so that guidelines are aligned with observed usage rather than defined arbitrarily.

The goal is consistency between:

```
Annotation format ≈ Model format ≈ Production format
```

---

## Methodology Notes

- Tests were conducted on **4 datasets (300–400 instances per language: Spanish, French, Portuguese, German)** from the Google FLEURS validation set.
- Matching instances can be easily inspected (see the *Inspecting Matching Examples* section for details).

- Additional **synthetic audio test cases** were generated to:
  - Evaluate rarely occurring formats (e.g., `currency_format`, `date_format`) 
  - Test abbreviation behavior
  - Observe model responses to unclear or partially inaudible sounds

- Default conventions are used automatically when no reliable pattern can be extracted from the data. 
  This ensures that guideline generation remains stable even when a specific format never appears.

---

## Scope and Limitations

- Regex rules were designed to:
  - Generalize across languages (Spanish, French, Portuguese, German)
  - Handle plural, feminine, and declension variations
  - Avoid common false positives (some edge cases are commented directly in the code)

The objective is broad and robust coverage of frequent formatting patterns, not exhaustive linguistic modeling. Some rare constructions or edge cases may not be captured.

When dominant patterns appear with close proportions (e.g., 0.55 vs 0.45), they should be interpreted as tendencies rather than strong conventions. Such cases ideally require validation on larger corpora, real production data, or data closer to the target deployment context.

---

## Input / Output Structure

### Input

- Files must follow the naming pattern:  transcriptions_{lang}_*.csv
  Examples:  transcriptions_fr_validation.csv, transcriptions_es_dev.csv, transcriptions_de_test.csv
  
- The language code (`fr`, `es`, `de`, `pt`, etc.) is extracted directly from the filename.

- Each file must contain at least one column whose name includes one of the model identifiers defined in the script ("whisper", "canary", "parakeet"); these columns must contain the transcription text.

- The list of supported models is defined inside `analyze()` as:

  ```python
  model_identifiers = ["whisper", "canary", "parakeet"]
  ```

  To support a new model, simply add its name to this list.  

  Example:

  ```python
  model_identifiers = ["whisper", "canary", "parakeet", "new_model_name"]
  ```
 
If these conventions are not respected, model detection or language-based aggregation may fail.


### Output

The file `model_conventions_summary.csv` contains one row per (file x model).

Each row summarizes the dominant formatting conventions and stylistic tendencies identified for that model on that dataset.


---

## Column Documentation & Interpretation

This section describes the patterns extracted by the script.  
For each formatting category, we analyze all detected occurrences and retain the format that appears most frequently (majority rule).  
See the **Decision Logic** section for implementation details on how dominant values are computed.


### currency_format

Possible values:
- `symbol` → 10 €, $50  
- `word` → 10 euros, cinco pesos  
- `not_detected`

---

### percent_format

Possible values:
- `symbol_space` → 80 %  
- `symbol_no_space` → 80%  
- `word` → quatre pour cent  
- `not_detected`

---

### thousand_separator_format

Possible values:
- `space` → 1 000  
- `dot` → 1.000  
- `comma` → 1,000  
- `not_detected`

---

### unit_format

Possible values:
- `short` → 5 km, 10 kg  
- `long` → 5 kilomètres  
- `not_detected`

---

### ordinal_style

Possible values:
- `digit_suffix` → 9e, 9ème, 3º  
- `word` → neuvième, troisième  
- `not_detected`

---

### number_style

Possible values:
- `digit` → 42, 1,000, 3.14  
- `word` → forty-two, one thousand, three point one four  
- `not_detected`

---

### date_format

Possible values:
- `dd/mm/yyyy` → 25/11/2024, 01.04.2024  
- `yyyy-mm-dd` → 2024-11-25, 2024-04-01  
- `dd_month_yyyy` → 25 November 2023, 1 April 2024  
- `not_detected`

---

### Hesitation, Capitalization & Punctuation Frequencies

These metrics provide insight into the model's expressiveness and stylistic tendencies:

- **Hesitation frequency** → Does the model frequently transcribe filled pauses (e.g., "euh", "um")?
- **Capitalization rate** → Does the model tend to capitalize more or less than expected (e.g., proper nouns, sentence starts, random mid-sentence capitals)?
- **Punctuation usage** → How frequent and varied is punctuation (commas, periods, hyphens in compound words like "New-Zealand")? Does it reflect natural phrasing or appear sparse/excessive?

---

## Decision Logic

Guidelines are generated using a hierarchical fallback strategy.

When selecting conventions for a specific `(language, model)` pair, the system applies the following logic:

1. If a convention exists for that exact language–model pair → use it.  
2. Otherwise, use the dominant convention across all models for that language.  
3. If unavailable, use the dominant convention of that model across all languages.  
4. If still unavailable, fall back to the global dominant convention.  
5. If no data exists at all → apply a predefined default value.

This approach preserves language-specific norms when they are observable, respects model-specific tendencies, and prevents missing patterns from breaking the guideline generation process.

The system remains deterministic while adapting to new inputs.

---

## Inspecting Matching Examples

It is possible to print matching examples directly inside the `detect(text)` function to manually verify patterns.
It allows quick verification of which sentences trigger a rule and helps validate or refine regex patterns efficiently.

Example:

```python
if RE_UNIT_WITH_QUANTITY.search(text):
    feats["unit_mode"] = "short"
    print(text)  # <-------------------- capture short-form unit examples for manual review
elif RE_UNIT_LONG.search(text):
    feats["unit_mode"] = "long"
else:
    feats["unit_mode"] = None
```

### Example output

```
Der nördliche Teil oder die Sentinel Range hat die höchsten Berge der Antarktis, das Vinson-Massiv, dessen höchster Gipfel mit 4.892 m Höhe der Mount Vinson ist.
L'Amazone est également le fleuve le plus large de la planète, atteignant parfois 10 km de large.
L'Amazone est également le fleuve le plus large de la planète, atteignant parfois dix km de large.
Der Goldmedaillengewinner beim Olympischen Spielen sollte bei den Commons Rave Games in Disziplinen 100m und 200 m Freistil sowie in 3 Lagenstaffeln schwimmen, aber wegen seiner vielen Beschwerden wurde seine Fitness angezweifelt.
O parque abrange 19.500 km e é dividido em 14 zonas ecológicas diferentes, cada uma sustentando diferentes espécies animais.
```




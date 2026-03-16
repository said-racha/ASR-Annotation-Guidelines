import re
import os
import pandas as pd
import markdown

"""
HTML Annotation Guidelines Generator

Usage:
- Make sure the summary file "model_conventions_summary.csv" is present in the same directory.
- Run this script. It will ask you to specify:
    1. Language (either code like 'fr' or full name like 'French')
    2. Model family ('whisper', 'canary', 'parakeet')
- The script generates both Markdown and HTML representations of the guidelines.
  Only the HTML version is displayed on screen and is accessible via the variable `html_output`.

Note:
- To include detection confidence information (useful for data analysis), call the function
  generate_guidelines with `guidelines_for_ds=True`:
      generate_guidelines(lang_code='fr', model_name='whisper', guidelines_for_ds=True)
"""

# =============================
# GUIDELINE GENERATION
# =============================

def get_aggregated_value(df, lang_code, model_name, column_name, default_values):
    """
    Get value for a column with fallback aggregation rules.

    Fallback order:
    1. Specific language and model
    2. All models for the language (language majority)
    3. All languages for the model (model majority)
    4. Global majority across all data
    5. Default value

    Args:
    df: DataFrame with conventions data
    lang_code: Language code ('fr', 'es', 'pt', 'de')
    model_name: Model name ('whisper', 'canary', 'parakeet')
    column_name: Column to get value for
    default_values: Dict of default values by column

    Returns:
    Tuple of (value, confidence, source)
    """
    # Filter for specific language and model
    lang_model_filter = df["file"].str.contains(f"_{lang_code}_") & (df["model"] == model_name)
    filtered = df[lang_model_filter]

    if not filtered.empty and filtered[column_name].iloc[0] != "not_detected":
        value = filtered[column_name].iloc[0]
        conf_col = column_name.replace("_format", "_majority_pct").replace("_style", "_majority_pct")
        confidence = filtered[conf_col].iloc[0] if conf_col in filtered.columns else 0.0
        return value, confidence, "language_model"

    # Fallback 1: Language majority (all models for this language)
    lang_filter = df["file"].str.contains(f"_{lang_code}_")
    lang_df = df[lang_filter]
    if not lang_df.empty:
        # Get most common non-"not_detected" value
        lang_values = lang_df[column_name][lang_df[column_name] != "not_detected"]
        if not lang_values.empty:
            value_counts = lang_values.value_counts()
            if not value_counts.empty:
                value = value_counts.index[0]
                # Calculate confidence as proportion of this value in language data
                confidence = value_counts.iloc[0] / len(lang_values)
                return value, confidence, "language_majority"

    # Fallback 2: Model majority (all languages for this model)
    model_filter = df["model"] == model_name
    model_df = df[model_filter]
    if not model_df.empty:
        # Get most common non-"not_detected" value
        model_values = model_df[column_name][model_df[column_name] != "not_detected"]
        if not model_values.empty:
            value_counts = model_values.value_counts()
            if not value_counts.empty:
                value = value_counts.index[0]
                # Calculate confidence as proportion of this value in model data
                confidence = value_counts.iloc[0] / len(model_values)
                return value, confidence, "model_majority"

    # Fallback 3: Global majority (all data)
    global_values = df[column_name][df[column_name] != "not_detected"]
    if not global_values.empty:
        value_counts = global_values.value_counts()
        if not value_counts.empty:
            value = value_counts.index[0]
            confidence = value_counts.iloc[0] / len(global_values)
            return value, confidence, "global_majority"

    # Fallback 4: Default value
    default_value = default_values.get(column_name)
    return default_value, 0.0, "default"




def generate_guidelines(lang_code="fr", model_name="whisper", guidelines_for_ds=False):
    """
    Generates specific annotation guidelines based on detected conventions.

    Args:
    lang_code : Language code ('fr', 'es', 'pt', 'de')
    model_name : Model name ('whisper', 'canary', 'parakeet')

    Returns:
    Formatted guidelines for the specified language and model
    """

    if not os.path.exists("model_conventions_summary.csv"):
        print("First run analyze() to generate the summary file.")
        return ""

    df = pd.read_csv("model_conventions_summary.csv")

    # Filter for specified language and model (for file and model name)
    lang_filter = df["file"].str.contains(f"_{lang_code}_")
    model_filter = df["model"] == model_name
    filtered_df = df[lang_filter & model_filter]

    if filtered_df.empty:
        print(f"No data found for language '{lang_code}' and model '{model_name}'")
        return ""

    row = filtered_df.iloc[0]

    # Default values
    default_values = {
        "thousand_separator_format": "dot",
        "percent_format": "symbol_no_space",
        "unit_format": "long",
        "date_format": "dd_month_yyyy",
        "currency_format": "word",
        "ordinal_style": "word",
        "number_style": "digit"
    }

    # Get values with fallback aggregation
    thousand_sep, thousand_conf, thousand_src = get_aggregated_value(
        df, lang_code, model_name, "thousand_separator_format", default_values
    )
    percent_format, percent_conf, percent_src = get_aggregated_value(
        df, lang_code, model_name, "percent_format", default_values
    )
    unit_format, unit_conf, unit_src = get_aggregated_value(
        df, lang_code, model_name, "unit_format", default_values
    )
    date_format, date_conf, date_src = get_aggregated_value(
        df, lang_code, model_name, "date_format", default_values
    )
    currency_format, currency_conf, currency_src = get_aggregated_value(
        df, lang_code, model_name, "currency_format", default_values
    )
    ordinal_style, ordinal_conf, ordinal_src = get_aggregated_value(
        df, lang_code, model_name, "ordinal_style", default_values
    )
    number_style, number_conf, number_src = get_aggregated_value(
        df, lang_code, model_name, "number_style", default_values
    )

    # Map language codes to full names
    lang_names = {
        "fr": "French",
        "es": "Spanish",
        "pt": "Portuguese",
        "de": "German"
    }

    lang_name = lang_names.get(lang_code, lang_code.upper())

    # Format thousands separator instructions
    if thousand_sep == "space":
        sep_char = " "
        sep_name = "space"
    elif thousand_sep == "dot":
        sep_char = "."
        sep_name = "dot"
    elif thousand_sep == "comma":
        sep_char = ","
        sep_name = "comma"
    else:
        sep_char = "."
        sep_name = "dot"

    # Format percentages instruction
    if percent_format == "symbol_no_space":
        percent_instruction = "use digits with the % symbol attached to the number → 20% ✅, 20 % ❌, twenty percent ❌"
    elif percent_format == "symbol_space":
        percent_instruction = "use digits with a space before the % symbol → 20 % ✅, 20% ❌, twenty percent ❌"
    elif percent_format == "word":
        percent_instruction = "write the percentage in words → twenty percent ✅, 20% ❌"
    else:
        percent_instruction = "use digits with the % symbol attached to the number → 20% ✅, 20 % ❌, twenty percent ❌"

    # Format units instruction
    if unit_format == "short":
        unit_instruction = "use abbreviations → 10 km ✅, 10 kilometers ❌"
    elif unit_format == "long":
        unit_instruction = "use full words → 10 kilometers ✅, 10 km ❌"
    else:
        unit_instruction = "use full words → 10 kilometers ✅, 10 km ❌"

    # Format numbers instruction
    if number_style == "digit":
        number_instruction = "use digits → 100 ✅, one hundred ❌"
    elif number_style == "word":
        number_instruction = "use written words → one hundred ✅, 100 ❌"
    else:
        number_instruction = "use written words for small numbers (<1000), digits for large numbers → ten ✅, 10 ❌; 1 234 ✅, one thousand two hundred thirty-four ❌"

    # Format dates instruction
    if date_format == "dd/mm/yyyy":
        date_instruction = f"use dd/mm/yyyy format → 10/02/2023 ✅, 10 february 2023 ❌"
        date_format_str = "dd/mm/yyyy"
    elif date_format == "yyyy-mm-dd":
        date_instruction = f"use ISO yyyy-mm-dd format → 2023-02-10 ✅, 10 february 2023 ❌"
        date_format_str = "yyyy-mm-dd"
    elif date_format == "dd_month_yyyy":
        date_instruction = f"use dd month yyyy format → 10 february 2023 ✅, 10/02/2023 ❌"
        date_format_str = "dd month yyyy"
    else:
        date_instruction = f"use dd month yyyy format → 10 february 2023 ✅, 10/02/2023 ❌"
        date_format_str = "dd month yyyy"

    # Format currency instruction
    if currency_format == "symbol":
        currency_instruction = "use symbols → $ ✅, € ✅, dollars ❌, euros ❌"
    elif currency_format == "word":
        currency_instruction = "use written words → dollars ✅, euros ✅, $ ❌, € ❌"
    else:
        currency_instruction = "format as heard"

    # Format ordinal instruction
    if ordinal_style == "digit_suffix":
        ordinal_instruction = "use digits with suffix → 1st ✅, first ❌"
    elif ordinal_style == "word":
        ordinal_instruction = "use written words → first ✅, 1st ❌"
    else:
        ordinal_instruction = "format as heard"

    # Model-specific spelling
    if model_name == "whisper":
        spelling_instruction = "Spell with spaces → d a n g"
    else:
        spelling_instruction = "Spell without spaces → dang"


    # Helper function for confidence display
    def format_confidence(value, confidence, source):
        if value == "not_detected":
            if "date" in source.lower():
                return "No standard date formats detected in the text"
            elif "currency" in source.lower():
                return "No currency formats detected in the text"
            elif "ordinal" in source.lower():
                return "No ordinal numbers detected in the text"
            else:
                return f"No {source.replace('_', ' ')} detected"

        sources_display = {
            "language_model": f"based on specific {lang_name}/{model_name} data",
            "language_majority": f"based on {lang_name} language majority",
            "model_majority": f"based on {model_name} model majority",
            "global_majority": "based on global majority",
            "default": "default value"
        }

        if confidence > 0:
            return f"{confidence:.1%} confidence ({sources_display.get(source, source)})"
        else:
            return f"{sources_display.get(source, source)}"

    # Build model-specific formatting rules section
    model_rules_lines = [
        f"## 2. Model-specific Rules ({model_name.capitalize()})",
        f"- **Spelling letters**: {spelling_instruction}",
        f"- **Dates**: {date_instruction}",
        f"- **Units**: {unit_instruction}",
        f"- **Currency amounts**: {currency_instruction}",
        f"- **Ordinal numbers**: {ordinal_instruction}",
        f"- **Percentages**: {percent_instruction}",
        f"- **General number style**: {number_instruction}",
        f"- **Digit grouping**: Use {sep_name} as separator for:"
    ]

    # Only show large number examples if using digits
    if number_style == "digit":
        model_rules_lines.append(f"    - **Large numbers (≥1000)**: 1{sep_char}234")

    # Phone formatting always shown (phones are always digits)
    model_rules_lines.append(f"    - **Phone numbers**: 06{sep_char}12{sep_char}34{sep_char}56{sep_char}78")

    model_rules_section = "\n".join(model_rules_lines)


    # Generate guidelines
    guidelines = f"""# {lang_name} Annotation Guidelines for {model_name.capitalize()}

## 1. General Principles
- Everything must be written in **lowercase**, **with accents**, except for proper nouns (Cardif).
- **No punctuation**: ? ! : . , ; - _
- Keep **spoken abbreviations/contractions**: gonna, gotta, etc.

- **Personal data** (name, address, ID, SSN, passport, etc.) must be enclosed with #.
      - Example: "Hello my name is #Jane Doe# my ID is 1 2 3#"

- **Hesitations and non-speech sounds**: Put between <> expressions like "hm", "hmm", "euh", "eh", "ah"...
      - Example: "I love euhhhh sandwich hmmm" → "I love &lt;euhhhh&gt; sandwich &lt;hmmm&gt;"
      - Note: It does not matter if you put &lt;hm&gt; or &lt;hmmmmmmmmmmm&gt; we will normalize it.

---

{model_rules_section}

---

## 3. Special Cases
- **Date format variations**: While the standard format is "{date_format_str}", if the speaker pronounces the date differently, transcribe it as heard.
      - Examples of acceptable variations: "february 10", "10 de fevereiro de 2023"

- **Incomplete words**: If a person does not finish a word, transcribe exactly what is heard.
      - Example: If the speaker says "he has mar" instead of "he has marked", write "he has mar"

- **Inaudible speech handling**:
    - **Single inaudible segment**: Split the box to isolate [inaudible].
        - Example: "Bonjour je m'appelle [inaudible] bye thanks for" → Box 1: "Bonjour je m'appelle", Box 2: "[inaudible]", Box 3: "bye thanks for"

    - **Multiple inaudible segments**: Tag entire call as [inaudible].
        - Example: "Bonjour [inaudible] je [inaudible] m'appelle [inaudible] bye [inaudible] thanks for" → [inaudible]

"""


    guidelines_ds = guidelines + f"""
---

## 4. Detection Confidence
- **Currency format**: {format_confidence(currency_format, currency_conf, currency_src)}
- **Date format**: {format_confidence(date_format, date_conf, date_src)}
- **Thousand separator**: {format_confidence(thousand_sep, thousand_conf, thousand_src)}
- **Percentage format**: {format_confidence(percent_format, percent_conf, percent_src)}
- **Unit format**: {format_confidence(unit_format, unit_conf, unit_src)}
- **Ordinal style**: {format_confidence(ordinal_style, ordinal_conf, ordinal_src)}
- **Number style**: {format_confidence(number_style, number_conf, number_src)}
"""

    if guidelines_for_ds : 
        return guidelines_ds
    else :
        return guidelines


# =============================
# MAIN EXECUTION
# =============================

if __name__ == "__main__":

    filename = "model_conventions_summary.csv"
    file_path = "model_conventions_summary.csv"

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The summary file '{file_path}' was not found in the specified directory.")
        # print(f"Running analysis to generate {filename}...")
        # analyze()
        
    df = pd.read_csv(file_path)

    language_map = {
        "fr": ["fr", "french", "francais", "français"],
        "es": ["es", "spanish", "espanol", "español"],
        "pt": ["pt", "portuguese", "portugues", "português"],
        "de": ["de", "german", "allemand", "deutsch"]
    }

    language_display = {
        "fr": "French",
        "es": "Spanish",
        "pt": "Portuguese",
        "de": "German"
    }

    # Detect available languages
    available_languages = set()
    for file in df["file"].unique():
        match = re.search(r'_([a-z]{2})_', file)
        if match:
            available_languages.add(match.group(1))

    available_models = sorted(df["model"].unique())

    print("\nAvailable languages:")
    for lang in sorted(available_languages):
        print(f" - {language_display.get(lang, lang)} ({lang})")

    print("\nAvailable models:", ", ".join(available_models))

    # -------------------------
    # USER INPUT
    # -------------------------

    lang_input = input("\nEnter language (code or name): ").strip().lower()
    model_name = input("Enter model name: ").strip().lower()

    # Normalize language input
    lang_code = None
    for code, aliases in language_map.items():
        if lang_input in aliases and code in available_languages:
            lang_code = code
            break

    if lang_code is None:
        valid = ", ".join(language_display[l] for l in available_languages)
        print(f"Invalid language. Choose from: {valid}")
        exit()

    if model_name not in available_models:
        print(f"Invalid model. Choose from: {', '.join(available_models)}")
        exit()

    # Generate markdown guidelines
    guidelines_md = generate_guidelines(lang_code=lang_code, model_name=model_name)

    if not guidelines_md:
        print("No guidelines generated.")
        exit()

    # -----------------------------
    # HTML conversion
    # -----------------------------

    html_output = markdown.markdown(guidelines_md)

    print("\n" + "="*80)
    print("HTML CODE")
    print("="*80)
    print(html_output)

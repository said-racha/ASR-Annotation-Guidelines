import re
import os
import glob
import unicodedata
import pandas as pd
from pathlib import Path
from collections import Counter

# =============================
# TEXT NORMALIZATION
# =============================

def normalize(text):
    """
    Normalizes text by handling missing values, Unicode normalization,
    and whitespace standardization.
    """
    if pd.isna(text):
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00A0", " ")
    return text.strip()

# =============================
# LEXICONS
# =============================

NUMBER_WORDS_FULL_SET = set([
    "un","deux","trois","quatre","cinq","six","sept","huit","neuf","dix","onze","douze","treize","quatorze","quinze","seize","vingt","trente","quarante","cinquante","soixante","cent","mille", "million", "millions", "milliard", "milliards",
    "uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve","diez","once","doce","trece","catorce","quince","dieciséis","diecisiete","dieciocho","diecinueve","veinte","veintiuno","veintidós","veintitrés","veinticuatro","veinticinco","veintiséis","veintisiete","veintiocho","veintinueve","treinta","cuarenta","cincuenta","cien","mil","millón", "millones","millardo", "millardos", "mil millones", "billón", "billones",
    "um","dois","três","quatro","cinco","seis","sete","oito","nove","dez","onze","doze","treze","catorze","quinze","vinte","trinta","quarenta","cinquenta","cem","mil","milhão", "milhões", "bilhão", "bilhões",
    "eins","zwei","drei","vier","fünf","sechs","sieben","acht","neun","zehn","elf","zwölf","dreizehn","vierzehn","fünfzehn","sechzehn","zwanzig","dreißig","vierzig","fünfzig","hundert","tausend","million", "millionen","milliarde", "milliarden", "billion", "billionen",
])  # This list is not exhaustive, but the strategy is to include fundamental number words, since higher numbers are generally compounds (e.g., "dix-sept", "treinta y cinco").
    

AMBIGUOUS_NUMBER_WORDS = {"un","uno","um"} # Ambiguous words requiring contextual verification

NUMBER_WORDS = NUMBER_WORDS_FULL_SET - AMBIGUOUS_NUMBER_WORDS # We separate ambiguous number words (like "un"/"uno"/"um") from the full set of number words because they can function both as articles and numerals
                                                              # Example: "c'est un bel endroit" means "it's a nice place", not "it's one nice place"
                                                              # Regex patterns alone cannot distinguish these uses, so we handle them separately for accuracy

ORDINAL_WORDS = set([
    "premier","deuxième","troisième","quatrième","cinquième","sixième","septième","huitième","neuvième","dixième","onzième","douzième","treizième","quatorzième","quinzième","seizième","vingtième","trentième","quarantième","cinquantième","soixantième","centième","millième",
    "primero","segundo","tercero","cuarto","quinto","sexto","séptimo","octavo","noveno","décimo","undécimo","duodécimo","decimotercero","decimocuarto","decimoquinto","vigesimo","trigesimo","cuadragesimo","quincuagesimo","centesimo","milesimo",
    "primeiro","segundo","terceiro","quarto","quinto","sexto","sétimo","oitavo","nono","décimo","décimo primeiro","décimo segundo","vigésimo","trigésimo","quadragésimo","quinquagésimo","centésimo","milésimo",
    "erste","zweite","dritte","vierte","fünfte","sechste","siebte","achte","neunte","zehnte","elfte","zwölfte","dreizehnte","vierzehnte","fünfzehnte","sechzehnte","zwanzigste","dreißigste","vierzigste","fünfzigste","hundertste","tausendste"
])

CURRENCY_WORDS = [
    "euro", "euros", "dollar", "dollars", "dólar", "dólares",
    "livre", "livres", "libra", "libras", "pfund",
    "yen", "yens", "yenes", "iene", "ienes",
    "yuan", "yuans", "yuanes",
    "franc", "francs", "franco", "francos", "franken",
    "rouble", "roubles",
    "peso", "pesos",
    "real", "reais", "reales",
    "sol", "soles", "quetzal", "quetzales",
    "colón", "colones", "bolívar", "bolívares"
]

UNIT_SHORT = ["km","m","cm","mm","kg","hg","g","mg","l","ml","h","min","s","°c"]

UNIT_LONG = [
    "kilomètre", "kilometre", "kilómetro", "kilometer", "quilómetro",
    "mètre", "metro", "meter", "metre",
    "centimètre", "centimetro", "zentimeter", "centímetro",
    "millimètre", "milimetro", "millimeter", "milímetro",

    "gramme", "gramo", "gram", "grama",
    "kilogramme", "kilogramo", "kilogram", "quilograma",
    "hectogramme", "hectogramo", "hektogramm", "hectograma",
    "milligramme", "miligramo", "milligramm", "miligrama",

    "litre", "litro", "liter",
    "millilitre", "mililitro", "milliliter",
    "centilitre", "centilitro", "zentiliter",
    "hectolitre", "hectolitro", "hektoliter", "hectolitro",

    "seconde", "segundo", "sekunde", "second",
    "minute", "minuto",
    "heure", "hora", "stunde", "hour",

    "degré celsius", "grado celsius", "grad celsius", "grau celsius", "celsius",
]

MONTH_WORDS = [
    "janvier","février","fevrier","mars","avril","mai","juin","juillet","août","aout","septembre","octobre","novembre","décembre","decembre",
    "enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre",
    "janeiro","fevereiro","março","marco","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro",
    "januar","februar","märz","maerz","april","mai","juni","juli","august","september","oktober","november","dezember"
]

HESITATIONS = ["euh","eh","ehm","hmm","hm","ah","uh","um","äh","mmm"]


# ===============================
# STRUCTURAL REGULAR EXPRESSIONS
# ===============================

# Thousand separators
RE_THOUSAND_SPACE = re.compile(r"\b\d{1,3}( \d{3})+\b")  # Matches: "1 000", "12 345", "999 999 999"
RE_THOUSAND_DOT = re.compile(r"\b\d{1,3}(\.\d{3})+\b") # Matches: "1.000", "12.345", "999.999.999"
RE_THOUSAND_COMMA = re.compile(r"\b\d{1,3}(,\d{3})+\b") # Matches: "1,000", "12,345", "999,999,999"

# Percentage formats
RE_PERCENT_SPACE = re.compile(r"\d+ %") # Matches: "50 %", "100 %", "12.5 %"
RE_PERCENT_NO_SPACE = re.compile(r"\d+%") # Matches: "50%", "100%", "12.5%"
RE_PERCENT_WORD = re.compile(r"\b(pour cent|por ciento|por cento|prozent)\b", re.I) # Matches: "pour cent", "POR CIENTO", "Prozent"

# Ordinal number patterns
RE_ORDINAL_DIGIT = re.compile(r"\d+(e|ème|º|ª|th|st|nd|rd)\b", re.I) # Matches: "1er", "2ème", "3rd"
RE_ORDINAL_WORD = re.compile( r"\b(" + "|".join(ORDINAL_WORDS) + r")(e|es|s|a|as|er)?\b", re.I)  # Matches: "premier", "Second", "TROISIÈME" (with optional gender/number suffixes)

# Text style patterns
RE_PUNCT = re.compile(r"[,;:!?-_.]")

# Number and unit patterns
RE_DIGIT_NUMBER = r"\d+(?:[.,]\d+)?"
RE_WORD_NUMBER = r"\b(" + "|".join(NUMBER_WORDS) + r")\b"
RE_QUANTITY = rf"(?:{RE_DIGIT_NUMBER}|{RE_WORD_NUMBER})"

# Unit patterns
RE_UNIT_WITH_QUANTITY = re.compile( rf"{RE_QUANTITY}\s*\b({'|'.join(UNIT_SHORT)})\b", re.I ) # Matches: "5 g", "10,5ml", "dos litros"
                                                                                             # short units only when preceded by a quantity to avoid false positives like "Super G"
RE_UNIT_LONG = re.compile(r"\b(" + "|".join(UNIT_LONG) + r")(s|es|en)?\b",  re.I)  # Matches: "gramme", "kilogrammes" (with optional plural suffixes)

# Currency patterns
RE_CURRENCY_SYMBOL = re.compile(r"[€$£¥₹₽₺¢₩]")
RE_CURRENCY_WORD = r"\b(" + "|".join(CURRENCY_WORDS) + r")\b"
RE_CURRENCY_PATTERN = re.compile( rf"{RE_QUANTITY}\s*{RE_CURRENCY_WORD}", re.I) # Matches: "5 euros", "cinco pesos"
                                                                                # Only matches currency words that follow a number/quantity
                                                                                # This ensures we capture monetary amounts, not text containing currency words in other contexts (e.g. "vida real")
# Date patterns
RE_DATE_DD_MM_YYYY = re.compile( r"\b(?:0?[1-9]|[12][0-9]|3[01])[/.](?:0?[1-9]|1[0-2])[/.]\d{4}\b" ) # Matches: "25/11/2024", "5/6/2023", "31.01.1887"
RE_DATE_YYYY_MM_DD = re.compile( r"\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])\b" ) # Matches: "2024-11-25", "2024-06-05", "1887-01-31"
RE_DATE_DD_MONTH_YYYY = re.compile( r"\b(?:0?[1-9]|[12][0-9]|3[01])\s+(" + "|".join(MONTH_WORDS) + r")\s+\d{4}\b", re.I) # Matches: "25 décembre 2023", "5 juin 2024", "31 janvier 2025"


# Hesitation patterns
HESITATION_PATTERNS = []
for hesitation in HESITATIONS:
    pattern = r"\b" + r"+".join(re.escape(c) for c in hesitation) + r"+\b"
    HESITATION_PATTERNS.append(pattern)
RE_HESITATION_PATTERN = re.compile("|".join(HESITATION_PATTERNS), re.I) # Matches: "euuuuh","eh","ehmmm", etc


# ===================================
# DOCUMENT FORMATTING ANALYSIS
# ===================================

def detect(text):
    """
    Analyzes and extracts formatting conventions from text.

    Detects how the following elements are written:
    - Percentages (symbol, word, spacing)
    - Currencies (symbol or word)
    - Thousand separators (space, dot, comma)
    - Units (abbreviated or full)
    - Numbers (digits vs words)
    - Dates (day/month/year, ISO, literal)
    - Ordinal numbers (digits vs words)
    - Hesitation markers
    - Punctuation and capitalization patterns
    """

    text = normalize(text)
    feats = {}

    # percentage detection
    if RE_PERCENT_SPACE.search(text):
        feats["percent_mode"] = "symbol_space"
    elif RE_PERCENT_NO_SPACE.search(text):
        feats["percent_mode"] = "symbol_no_space"
    elif RE_PERCENT_WORD.search(text):
        feats["percent_mode"] = "word"
    else:
        feats["percent_mode"] = None

    # currency detection
    if RE_CURRENCY_SYMBOL.search(text):
        feats["currency_mode"] = "symbol"
    elif RE_CURRENCY_PATTERN.search(text):
        feats["currency_mode"] = "word"
    else:
        feats["currency_mode"] = None

    # thousand separator detection
    if RE_THOUSAND_SPACE.search(text):
        feats["thousand_sep_mode"] = "space"
    elif RE_THOUSAND_DOT.search(text):
        feats["thousand_sep_mode"] = "dot"
    elif RE_THOUSAND_COMMA.search(text):
        feats["thousand_sep_mode"] = "comma"
    else:
        feats["thousand_sep_mode"] = None

    # unit detection
    if RE_UNIT_WITH_QUANTITY.search(text):
        feats["unit_mode"] = "short"
    elif RE_UNIT_LONG.search(text):
        feats["unit_mode"] = "long"
    else:
        feats["unit_mode"] = None


    # ordinal number style
    feats["ordinal_style"] = detect_ordinal_style(text)

    # number style
    feats["number_style"] = detect_number_style(text)

    # hesitation markers
    feats["hesitation_plain"] = any(re.search(pattern, text, re.I) for pattern in HESITATION_PATTERNS)

    # text style features
    feats["punctuation"] = bool(RE_PUNCT.search(text))
    letters = [c for c in text if c.isalpha()]
    feats["uppercase"] = (
        sum(c.isupper() for c in letters)/len(letters)
        if letters else 0
    )

    # date format
    feats["date_format"] = detect_date_style(text)


    return feats



# =================================
# DOMINANT PATTERN ANALYSIS
# =================================

def get_primary_convention_with_percentage(series):
    """
    Identifies the most frequent writing convention in a data series
    and returns both the convention and its percentage.

    Returns:
    - (convention, percentage) tuple
    - ("not_detected", 0.0) if no conventions detected
    """
    filtered = [x for x in series if x is not None]
    if not filtered:
        return "not_detected", 0.0

    counter = Counter(filtered)
    most_common = counter.most_common(1)[0]
    convention, count = most_common
    percentage = count / len(filtered)

    return convention, percentage

def detect_ordinal_style(text):
    """
    Detects how ordinal numbers are formatted in the text.

    Returns:
    - 'digit_suffix' for forms like 9e, 9ème, 5th, 3º
    - 'word' for written forms like "premier", "first"
    - None if no ordinal numbers are found
    """
    text = normalize(text)
    if RE_ORDINAL_DIGIT.search(text):
        return "digit_suffix"
    elif RE_ORDINAL_WORD.search(text):
        return "word"
    else:
        return None

def detect_number_style(text):
  """
  Determines if numbers are represented as digits or written words.
  When both forms appear, returns the more frequent representation.

  Returns:
  - 'digit' for numerical digits (e.g., 9, 100)
  - 'word' for written numbers (e.g., "nine", "ten")
  - None    : no numbers detected
  """
  text = normalize(text)
  has_digit = bool(re.search(r"\d+", text))
  has_word_number = bool(re.search(RE_WORD_NUMBER, text, re.I))

  if has_digit and not has_word_number:
      return "digit"
  elif has_word_number and not has_digit:
      return "word"
  elif has_digit and has_word_number:
      # If both appear, choose the most frequent
      digit_count = len(re.findall(r"\d+", text))
      word_count = len(re.findall(RE_WORD_NUMBER, text, re.I))
      return "digit" if digit_count >= word_count else "word"
  else:
      return None

def detect_date_style(text):
    """
    Returns the most frequent date format among standard formats:
    - 'dd/mm/yyyy'    : day/month/year format (e.g., 25/11/2024)
    - 'yyyy-mm-dd'    : ISO year-month-day format (e.g., 2024-11-25)
    - 'dd_month_yyyy' : literal month format (e.g., 25 novembre 2024)
    - None            : if no dates are detected
    """

    text = normalize(text)

    counts = {
        "dd/mm/yyyy": len(RE_DATE_DD_MM_YYYY.findall(text)),
        "yyyy-mm-dd": len(RE_DATE_YYYY_MM_DD.findall(text)),
        "dd_month_yyyy": len(RE_DATE_DD_MONTH_YYYY.findall(text)),
    }

    total = sum(counts.values())
    if total == 0:
        return None

    return max(counts, key=counts.get)

# =============================
# DATASET ANALYSIS
# =============================

def analyze():
    """
    Main function for analyzing transcription datasets.
    Processes CSV files containing transcription outputs and extracts formatting conventions for each model.

    Input: Looks for CSV files matching 'transcriptions*.csv' pattern.
           Files must have at least one column whose name contains
           'whisper', 'canary', or 'parakeet' with transcription text.

    Output: Generates 'model_conventions_summary.csv' with one row per
            file/model combination, containing detected formatting
            conventions and text style metrics with majority percentages.

    Returns: None (results are saved to CSV file)
    """

    files = glob.glob("transcriptions*.csv")
    model_names = ["whisper","canary","parakeet"]
    results = []

    for f in files:
        df = pd.read_csv(f, dtype=str)
        filename = Path(f).name

        for col in df.columns:
            if not any(m in col.lower() for m in model_names):
                continue

            model = [m for m in model_names if m in col.lower()][0]

            all_feats = [detect(t) for t in df[col]]
            feat_df = pd.DataFrame(all_feats)

            # Get conventions with their percentages
            currency_convention, currency_pct = get_primary_convention_with_percentage(feat_df["currency_mode"])
            date_convention, date_pct = get_primary_convention_with_percentage(feat_df["date_format"])
            thousand_convention, thousand_pct = get_primary_convention_with_percentage(feat_df["thousand_sep_mode"])
            percent_convention, percent_pct = get_primary_convention_with_percentage(feat_df["percent_mode"])
            unit_convention, unit_pct = get_primary_convention_with_percentage(feat_df["unit_mode"])
            ordinal_convention, ordinal_pct = get_primary_convention_with_percentage(feat_df["ordinal_style"])
            number_convention, number_pct = get_primary_convention_with_percentage(feat_df["number_style"])

            row = {
                "file": filename,
                "model": model,

                # Convention values
                "currency_format": currency_convention,
                "date_format": date_convention,
                "thousand_separator_format": thousand_convention,
                "percent_format": percent_convention,
                "unit_format": unit_convention,
                "ordinal_style": ordinal_convention,
                "number_style": number_convention,

                # Convention percentages
                "currency_majority_pct": currency_pct,
                "date_majority_pct": date_pct,
                "thousand_separator_majority_pct": thousand_pct,
                "percent_majority_pct": percent_pct,
                "unit_majority_pct": unit_pct,
                "ordinal_majority_pct": ordinal_pct,
                "number_majority_pct": number_pct,

                # Text style metrics
                "uppercase_frequency": feat_df["uppercase"].mean(),
                "punctuation_frequency": feat_df["punctuation"].mean(),
                "hesitation_frequency": feat_df["hesitation_plain"].mean(),
            }

            results.append(row)

    pd.DataFrame(results).to_csv("model_conventions_summary.csv", index=False)
    print("Saved as model_conventions_summary.csv")


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


def generate_guidelines(lang_code="fr", model_name="whisper"):
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
        percent_instruction = "symbol attached to number → 20% ✅, 20 % ❌"
    elif percent_format == "symbol_space":
        percent_instruction = "space between number and symbol → 20 % ✅, 20% ❌"
    elif percent_format == "word":
        percent_instruction = "write in words → twenty percent ✅, 20% ❌"
    else:
        percent_instruction = "symbol attached to number → 20% ✅, 20 % ❌"

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

    # Model-specific formatting rules section
    model_rules_lines = [
        f"## 2. Model-specific Rules ({model_name.capitalize()})",
        f"- **Spelling letters**: {spelling_instruction}",
        f"- **Dates**: {date_instruction}",
        f"- **Units**: {unit_instruction}",
        f"- **Currency amounts**: {currency_instruction}",
        f"- **Ordinal numbers**: {ordinal_instruction}",
        f"- **General number style**: {number_instruction}",
        f"- **Digit grouping**: Use {sep_name} as separator for:"
    ]

    if number_style == "digit":
        model_rules_lines.append(f"  - **Large numbers (≥1000)**: 1{sep_char}234")

    model_rules_lines.append(f"  - **Phone numbers**: 06{sep_char}12{sep_char}34{sep_char}56{sep_char}78")
    model_rules_lines.append(f"- **Percentages**: {percent_instruction}")

    model_rules_section = "\n".join(model_rules_lines)

    # Generate guidelines
    guidelines = f"""# {lang_name} Annotation Guidelines for {model_name.capitalize()}

## 1. General Principles
- Everything must be written in **lowercase**, **with accents**, except for proper nouns (Cardif).
- **No punctuation**: ? ! : . , ; - _
- Keep **spoken abbreviations/contractions**: gonna, gotta, etc.

- **Personal data** (name, address, ID, SSN, passport, etc.) must be enclosed with #.
  Example: "Hello my name is #Alice Dupont# my ID is 1 2 3#"

- **Hesitations and non-speech sounds**: Put between <> expressions like "hm", "hmm", "euh", "eh", "ah"...
  Example: "I love euhhhh sandwich hmmm" → **"I love <euhhhh> sandwich <hmmm>"**
  Note: It does not matter if you put <hm> or <hmmmmmmmmmmm> we will normalize it.

---

{model_rules_section}

---

## 3. Special Cases
- **Date format variations**: While the standard format is "{date_format_str}", if the speaker pronounces the date differently, transcribe it as heard.
  Examples of acceptable variations: "february 10", "10 de fevereiro de 2023"

- **Incomplete words**: If a person does not finish a word, transcribe exactly what is heard.
  Example: "he has mar" (instead of "he has marked") → **he has mar**

- **Inaudible speech handling**:
  - **Single inaudible segment**: Split the box to isolate [inaudible].
    Example: "Bonjour je m'appele [inaudible] bye thanks for" →
    Box 1: "Bonjour je m'appele", Box 2: "[inaudible]", Box 3: "bye thanks for"

  - **Multiple inaudible segments**: Tag entire call as [inaudible].
    Example: "Bonjour [inaudible] je [inaudible] m'appele [inaudible] bye [inaudible] thanks for" → **[inaudible]**

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

    return guidelines


# =============================
# MAIN EXECUTION
# =============================

if __name__ == "__main__":
    analyze()
    
    # Display the generated analysis
    if os.path.exists("model_conventions_summary.csv"):
        model_conventions_summary = pd.read_csv("model_conventions_summary.csv")
        print(model_conventions_summary)

        # Extract available languages and models
        available_files = model_conventions_summary["file"].unique()
        available_languages = set()
        
        for file in available_files:
            match = re.search(r'_([a-z]{2})_', file)
            if match:
                available_languages.add(match.group(1))
        
        available_models = model_conventions_summary["model"].unique()
        
        print(f"\n{'='*60}")
        print("AVAILABLE DATA")
        print(f"{'='*60}")
        print(f"Languages found: {', '.join(sorted(available_languages))}")
        print(f"Models found: {', '.join(sorted(available_models))}")
        print(f"{'='*60}\n")
        
        # Generate and display guidelines for each language/model combination
        print("\n" + "="*80)
        print("GUIDELINE GENERATION")
        print("="*80)
      
        combinations = [
            ("fr", "whisper"),
            ("fr", "canary"),
            ("fr", "parakeet"),
            ("es", "whisper"),
            ("es", "canary"),
            ("es", "parakeet"),
            ("pt", "whisper"),
            ("pt", "canary"),
            ("pt", "parakeet"),
            ("de", "whisper"),
            ("de", "canary"),
            ("de", "parakeet"),
        ]
        
        for lang_code, model_name in combinations:
            print(f"\n{'='*60}")
            print(f"Generating guidelines for {lang_code.upper()} - {model_name.capitalize()}")
            print(f"{'='*60}")
            
            # Generate guidelines
            guidelines = generate_guidelines(lang_code=lang_code, model_name=model_name)
            
            if guidelines:  
                # Save to file
                filename = f"guidelines_{lang_code}_{model_name}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(guidelines)
                print(f"Saved to '{filename}'")
                
                # Display first few lines
                preview_lines = guidelines.split('\n')[:5]
                print("\n".join(preview_lines))
                print("...\n")
            else:
                print(f"  Please select one of the available languages: {', '.join(sorted(available_languages))}")
                print(f"  Available models: {', '.join(sorted(available_models))}")
                
    else:
        print("Analysis file not found. Check for errors.")
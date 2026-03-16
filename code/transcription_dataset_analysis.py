import re
import os
import glob
import unicodedata
import pandas as pd
from pathlib import Path
from collections import Counter

"""
Transcription Dataset Analysis

Usage:
- Place your transcription CSV files in the same directory. Filenames should match the pattern 'transcriptions*.csv'.
- Each CSV file should have at least one column containing model names ('whisper', 'canary', or 'parakeet') with transcription text.
- Run this script. It will analyze all matching files and extract formatting conventions and text style metrics for each model.

Output:
- Generates 'model_conventions_summary.csv' containing detected conventions and style metrics for each file/model combination.
- The summary includes majority percentages for each convention, which can later be used for generating guidelines or further analysis.

Note:
- This script only saves results to CSV; further processing (like generating Markdown or HTML guidelines) is done separately.
"""

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
# MAIN EXECUTION
# =============================

if __name__ == "__main__":
    analyze()
    

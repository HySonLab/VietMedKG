import pandas as pd
import translators as ts
from tqdm import tqdm

# Function to translate text using the translators library
def translate_text(text):
    try:
        if isinstance(text, list):  # Check if 'text' is a list
            translated_text = [translate_text(item, from_language, to_language) for item in text]  # Translate each element recursively
            return translated_text
        elif text:
            # Translate from Chinese to English
            translated_text_en = ts.translate_text(text, translator="baidu", professional_field="medicine", sleep_seconds=5, limit_of_length=500000)
            # Translate from English to Vietnamese
            translated_text_vi = ts.translate_text(translated_text_en, translator="baidu", to_language="vie", professional_field="medicine", sleep_seconds=5, limit_of_length=500000)
            return translated_text_vi
        else:
            return text  # Return the original text if it is empty or null
    except Exception as e:
        print(f"Error translating text: {text}")
        try:
            # Split text by "."
            segments = text.split(".")
            # Translate each segment individually
            translated_segments = [translate_text(segment, from_language, to_language) for segment in segments]
            # Join translated segments with "."
            translated_text = ".".join(translated_segments)
            return translated_text
        except Exception as e:
            print(f"Error splitting and translating text: {text}")
            return None

# File paths
input_csv_file = "../data_cn/raw_data.csv"
output_csv_file = "translated_data.csv"

# Read the input CSV file into a pandas DataFrame
df = pd.read_csv(input_csv_file)

# Translate all cells in the DataFrame
for i, row in tqdm(df.iterrows(), total=len(df), desc="Translating Rows", unit="row"):
    for column in df.columns:
        try:
            df.at[i, column] = translate_text(row[column], from_language="zh", to_language="vi")  # Translate Chinese to Vietnamese
        except Exception as e:
            print(f"Error translating cell at row {i}, column '{column}'")

# Save the translated DataFrame to a new CSV file
df.to_csv(output_csv_file, index=False, encoding="utf-8")
print("Translation completed. Output written to", output_csv_file)


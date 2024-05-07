import pandas as pd
import translators as ts
from tqdm import tqdm
import os

# Function to translate text using the translators library
def translate_text(text):
    try:
        if isinstance(text, list):  # Check if 'text' is a list
            translated_text = [translate_text(item) for item in text]  # Translate each element recursively
            return translated_text
        elif isinstance(text, str):
            # Translate from Chinese to English
            translated_text_en = ts.translate_text(text, translator="baidu", professional_field="medicine", sleep_seconds=5, limit_of_length=500000)
            # Translate from English to Vietnamese
            translated_text_vi = ts.translate_text(translated_text_en, translator="baidu", to_language="vie", professional_field="medicine", sleep_seconds=5, limit_of_length=500000)
            return translated_text_vi
        elif text == "" or pd.isnull(text):
            return None  # Return the original text if it is empty or null
    except Exception as e:
        print(f"Error translating text: {text}")
        try:
            # Split text by "."
            segments = text.split("。")
            # Translate each segment individually
            translated_segments = [translate_text(segment) for segment in segments]
            # Join translated segments with "."
            translated_text = ".".join(translated_segments)
            return translated_text
        except Exception as e:
            text = "LỖI CẦN SỬA SAU, DỊCH LẠI" + text
            print(f"Error splitting and translating text: {text}")
            return text

# File paths
input_csv_file = "../data_cn/raw_data.csv"
output_csv_file = "data_translated.csv"
temp_output_csv_file = "data_temp.csv"

# Read the input CSV file into a pandas DataFrame
df = pd.read_csv(input_csv_file, encoding="utf-8")

# Translate all cells in the DataFrame
translated_rows = []
for i, row in tqdm(df.iterrows(), total=len(df), desc="Translating Rows", unit="row"):
    if i <= 720:
        continue
    try:
        translated_row = [translate_text(cell) for cell in row]
        translated_rows.append(translated_row)
        if (i + 1) % 10 == 0:  # Save every 10 translated rows
            temp_df = pd.DataFrame(translated_rows, columns=df.columns)
            temp_df.to_csv(temp_output_csv_file, mode='a', index=False, encoding="utf-8")
            translated_rows = []  # Reset for next batch
    except Exception as e:
        print(f"Error translating row {i}")

# Save the remaining translated rows
if translated_rows:
    temp_df = pd.DataFrame(translated_rows, columns=df.columns)
    temp_df.to_csv(temp_output_csv_file, mode='a', index=False, header=False, encoding="utf-8")

# Concatenate all saved translated parts into a single file
all_translated_df = pd.concat(map(pd.read_csv, [temp_output_csv_file]))
all_translated_df.to_csv(output_csv_file, index=False, encoding="utf-8")

# Delete the temporary file
os.remove(temp_output_csv_file)

print("Translation completed. Output written to", output_csv_file)

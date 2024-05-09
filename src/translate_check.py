import google.generativeai as genai
import pandas as pd 
from tqdm import tqdm

genai.configure(api_key="AIzaSyA0R779UohbN7o7-ZylWh-_Cu__zQj_rt8")
 
# Set up the model
generation_config = {
  "temperature": 0,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}
 
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  }
]
 
model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

def adjust_text_with_prompt(input_text):
    # Adjusted prompt
    # chỉnh mấy cái list -> giữ nguyên format return or j đó nhé
    prompt_parts = [
        "Your task is to assist a Vietnamese doctor with deep knowledge in Chinese medicine. Your response should be a coherent text tailored to this expertise.\n\nAbstract:",
        input_text
    ]

    # Generate adjusted text
    response = model.generate_content(prompt_parts)
    adjusted_text = response.text

    return adjusted_text
def adjustment(text):
    if isinstance(text, list):
        # Convert list to string
        input_text = ' '.join(text)
    elif isinstance(text, str):
        input_text = text
    else:
        raise ValueError("Input must be a list or a string")

    # Adjust text if it's too long
    if len(input_text) > 2048:
        # Split text into chunks
        chunks = [input_text[i:i+2048] for i in range(0, len(input_text), 2048)]
        adjusted_chunks = []

        # Adjust each chunk
        for chunk in chunks:
            adjusted_chunk = adjust_text_with_prompt(chunk)
            adjusted_chunks.append(adjusted_chunk)

        adjusted_text = adjusted_chunks
    else:
        adjusted_text = adjust_text_with_prompt(input_text)

    return adjusted_text

# File paths
input_csv_file = "../data/data_vie/data_translated.csv"
output_csv_file = "data_translated_checked.csv"
temp_output_csv_file = "data_translated_checked_temp.csv"

# Read the input CSV file into a pandas DataFrame
df = pd.read_csv(input_csv_file, encoding="utf-8")

# Translate all cells in the DataFrame
translated_rows = []
for i, row in tqdm(df.iterrows(), total=len(df), desc="Translating Rows", unit="row"):
    try:
        translated_row = [adjustment(cell) for cell in row]
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
all_translated_df.drop_duplicates(inplace=True)
all_translated_df = all_translated_df[all_translated_df['disease_name']!= "disease_name"]

all_translated_df.to_csv(output_csv_file, index=False, encoding="utf-8")

# Delete the temporary file
os.remove(temp_output_csv_file)

print("Translation completed. Output written to", output_csv_file)

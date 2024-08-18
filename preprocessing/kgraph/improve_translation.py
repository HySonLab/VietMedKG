import pandas as pd
from preprocessing.llm import get_GPT
import json 

def get_prompt(raw_data, translated_data):
    json_output = {
        "vietnamese_translation_adjusted": "NULL"
    }
    prompt = f"""
    As a highly skilled doctor and Vietnamese linguist, your task is to review and improve the quality of medical texts translated from Chinese to Vietnamese. 
    You will receive both the original Chinese text and the translated Vietnamese version. Your responsibilities include:
        - Checking the quality of the translation for medical accuracy and trustworthiness.
        - Ensuring linguistic correctness and overall readability.
        - Verifying coherence between the original and translated texts.
        - Assessing whether the translated knowledge is relevant to Traditional Vietnamese Medicine (TVM).
    Here is the orginial Chinese text: {raw_data}, the translated Vietnamese text: {translated_data}. The JSON output format is {json_output}.
    """
    return prompt

def review_and_adjust_translation(vietnamese_medical_text, chinese_medical_text):
    # Simulated response from the language model
    # In practice, this should call the language model API and process its response
    json_input = {"vietnamese_medical_text": vietnamese_medical_text}
    json_raw_data = {"chinese_medical_text": chinese_medical_text}
    prompt = get_prompt(json_input, json_raw_data)
    
    # Here you should call the language model with the prompt and get the response
    # For the sake of this example, we will assume the response from the language model is the input text
    # Replace this with actual API call and processing logic
    result = get_GPT(prompt)
    try:
        json_response = json.loads(result[result.find('{'): result.rfind('}') + 1])
        adjusted_text = json_response.get("vietnamese_translation_adjusted", "NULL")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        adjusted_text = vietnamese_medical_text
    
    return adjusted_text

def save_df(adjusted_df, file_path):
    adjusted_df.to_csv(file_path, index=False)
    print(f"DataFrame saved to {file_path}")

def create_adjusted_df(raw_df, original_df, save_interval=2, file_path='adjusted_df.csv'):
    adjusted_df = original_df.copy()
    row_count = 0
    
    for column in original_df.columns:
        for index, value in original_df[column].items():
            if pd.notnull(value):
                adjusted_text = review_and_adjust_translation(raw_df[column][index], value)
                if adjusted_text != "NULL":
                    adjusted_df.at[index, column] = adjusted_text
            row_count += 1
            if row_count % save_interval == 0:
                save_df(adjusted_df, file_path)
    
    # Save the final DataFrame
    save_df(adjusted_df, file_path)
    
    return adjusted_df
if __name__ == "__main__":
    raw_df = pd.read_csv("./data/raw_data.csv")
    orginal_df = pd.read_csv("./data/data_translated.csv")
    df = create_adjusted_df(raw_df, orginal_df)

import pandas as pd
from .llm import get_GPT
import json 

def get_prompt(json_input):
    json_output = {
        "vietnamese_translation_adjusted": "NULL"
    }
    prompt = f"""
    As a highly skilled doctor and Vietnamese linguist, your task is to review and improve the quality of translated medical texts 
    from English to Vietnamese. You will receive input of Vietnamese translated version. Your job is to check the quality of translation for medical accuracy, trustworthy, linguistic correctness, 
    and overall readability. If necessary, make adjustments to ensure the Vietnamese translation is accurate and clear. If it's correct, return the origin text
    Here is the json input: {json_input} and the output json should be in json format like this{json_output}, you must replace "NULL" by prompted text.
    """
    return prompt

def review_and_adjust_translation(vietnamese_medical_text):
    # Simulated response from the language model
    # In practice, this should call the language model API and process its response
    json_input = {"vietnamese_medical_text": vietnamese_medical_text}
    prompt = get_prompt(json_input)
    
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

def create_adjusted_df(original_df, save_interval=2, file_path='adjusted_df.csv'):
    adjusted_df = original_df.copy()
    row_count = 0
    
    for column in original_df.columns:
        for index, value in original_df[column].items():
            if pd.notnull(value):
                adjusted_text = review_and_adjust_translation(value)
                if adjusted_text != "NULL":
                    adjusted_df.at[index, column] = adjusted_text
            row_count += 1
            if row_count % save_interval == 0:
                save_df(adjusted_df, file_path)
    
    # Save the final DataFrame
    save_df(adjusted_df, file_path)
    
    return adjusted_df
if __name__ == "__main__":
    orginal_df = pd.read_csv("./data/data_translated.csv")
    df = create_adjusted_df(orginal_df)
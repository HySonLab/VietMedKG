import pandas as pd
import json
import numpy as np

def create_list_of_dicts(df):
    result = []
    for _, row in df.iterrows():
        disease_name = row['disease_name']
        for col in df.columns:
            row[col] = str(row[col])
            row[col] = row[col].replace("[", "").replace("]", "").replace('\"',"").replace("\'","")
            if col != 'disease_name' and (not pd.isna(row[col]) and row[col] != [] and row[col] != "" and row[col]!="nan"):
                
                result.append({
                    "header": disease_name,
                    "relation": col,
                    "tail": row[col]
                })
    return result

df = pd.read_csv("../../data/data_translated.csv")
# Create the list of dictionaries
list_of_dicts = create_list_of_dicts(df)
# Save the list of dictionaries to a JSON file
output_file = '../../data/benchmark/output_1806.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(list_of_dicts, f, ensure_ascii=False, indent=4)
print(f"Data has been saved to {output_file}")

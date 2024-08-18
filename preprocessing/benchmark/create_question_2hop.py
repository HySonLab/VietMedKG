from utils import read_json, save_json
from preprocessing.llm import get_GPT
from collections import defaultdict
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
from itertools import combinations

# Ignore all warnings
warnings.filterwarnings("ignore")

# Function to process data and replace relation values
def process_data(data, relation_dict):
    for item in data:
        if item['relation'] in relation_dict:
            item['relation'] = relation_dict[item['relation']]
    return data

# Function to create questions based on relations
def create_question(i):
    if i['relation_1'] == 'triệu_chứng' and i['relation_2'] == 'tỉ_lệ_chữa_khỏi':
        question = f"Với những triệu chứng [{i['tail_1']}], tỉ lệ chữa khỏi bệnh là bao nhiêu?"
    elif i['relation_1'] == 'nguyên_nhân' and i['relation_2'] == 'phương_pháp_điều_trị':
        question = f"Những phương pháp điều trị bệnh với các nguyên nhân [{i['tail_1']}]?"
    elif i['relation_1'] == 'bệnh_đi_kèm' and i['relation_2'] == 'phương_pháp_điều_trị':
        question = f"Phương pháp điều trị của những bệnh đi kèm như [{i['tail_1']}]?"
    elif i['relation_1'] == 'triệu_chứng' and i['relation_2'] == 'thực_phẩm_nên_ăn':
        question = f"Với những triệu chứng [{i['tail_1']}], bệnh nhân nên ăn thực phẩm gì?"
    elif i['relation_1'] == 'triệu_chứng' and i['relation_2'] == 'thực_phẩm_không_nên_ăn':
        question = f"Với những triệu chứng [{i['tail_1']}], bệnh nhân không nên ăn thực phẩm gì?"
    elif i['relation_1'] == 'triệu_chứng' and i['relation_2'] == 'món_ăn_được_đề_xuất':
        question = f"Với những triệu chứng [{i['tail_1']}], bệnh nhân nên ăn những món ăn gì?"
    elif i['relation_1'] == 'bệnh_đi_kèm' and i['relation_2'] == 'thực_phẩm_nên_ăn':
        question = f"Nên ăn gì để tránh mắc phải những bệnh đi kèm như [{i['tail_1']}]?"
    elif i['relation_1'] == 'bệnh_đi_kèm' and i['relation_2'] == 'thực_phẩm_không_nên_ăn':
        question = f"Không nên ăn gì để tránh mắc phải những bệnh đi kèm như [{i['tail_1']}]?"
    elif i['relation_1'] == 'loại_bệnh' and i['relation_2'] == 'khoa_điều_trị':
        question = f"Loại bệnh [{i['tail_1']}] thì nên điều trị ở khoa nào?"
    elif i['relation_1'] == 'triệu_chứng' and i['relation_2'] == 'kiểm_tra':
        question = f"Gặp những triệu chứng [{i['tail_1']}] nên kiểm tra những bộ phận nào?"
    elif i['relation_2'] == 'triệu_chứng' and i['relation_1'] == 'tỉ_lệ_chữa_khỏi':
        question = f"Với những triệu chứng [{i['tail_2']}], tỉ lệ chữa khỏi bệnh là bao nhiêu?"
    elif i['relation_2'] == 'nguyên_nhân' and i['relation_1'] == 'phương_pháp_điều_trị':
        question = f"Những phương pháp điều trị bệnh với các nguyên nhân [{i['tail_2']}]?"
    else:
        return "NULL"
    return question

# Function to retrieve prompt using an AI model
def get_prompt(text):
    prompt = f"""Imagine you are a doctor, have a lot of patients and receive lots of questions everyday. 
            Create a human-like question based on the given question [{text}] and return in json format: {{"question": ""}}.
            You have to keep the bracket [] for entity in the question. Specially, if the content inside the bracket [] do not contain any specific information like "Không có thông tin cụ thể", "bệnh này", etc, return {{}}.
            There are some requirements you need to know: 
            - Length of questions have to be less than 25 words.
            - The question should be smooth, in form of a sentence. 
            For the content in bracket [], if the length is more than 20, you should do the following task: 
                + For long string, you have to summarize and take one or few points to ask questions.
                + For a list, you should take a few elements for creating questions. 
                + The content in bracket [] must be a paraphrase, not sentences. 
                + You have to retain the [] and put adjusted content in.
            - Consider adjusting carefully to ask informative, meaningful question.
            - The entity inside bracket [] is really important, please do not miss it, you have to check for it before return the result. 
            """
    result = get_GPT(prompt)
    try:
        result = eval(result[result.find('{'): result.rfind('}') + 1])
    except:
        return "NULL"
    if result == {}:
        return "NULL"
    return result['question']

# Function to process each item in data
def process_item(i):
    if i['answer'] == "Không có thông tin":
        return None
    i['question'] = get_prompt(i['question'])
    if i['question'] == "NULL":
        return None
    return i

# Main function to merge, process, and save data
def main(input_filename, output_filename):
    # Relation dictionary
    relation_dict = {
        "disease_description": "mô_tả",
        "disease_category": "loại",
        "disease_prevention": "cách_phòng_tránh",
        "disease_cause": "nguyên_nhân",
        "disease_symptom": "triệu_chứng",
        "people_easy_get": "đối_tượng_dễ_mắc_bệnh",
        "associated_disease": "bệnh_đi_kèm",
        "cure_department": "khoa_điều_trị",
        "cure_method": "phương_pháp_điều_trị",
        "cure_probability": "tỉ_lệ_chữa_khỏi",
        "check_method": "kiểm_tra",
        "nutrition_do_eat": "thực_phẩm_nên_ăn",
        "nutrition_not_eat": "thực_phẩm_không_nên_ăn",
        "nutrition_recommend_eat": "món_ăn_được_đề_xuất",
        "drug_recommend": "thuốc_đề_xuất",
        "drug_common": "thuốc_phổ_biến",
        "drug_detail": "thông_tin_về_thuốc"
    }

    # Load the JSON data
    json_data = read_json(input_filename)

    # Process the data
    processed_data = process_data(json_data, relation_dict)

    # Group data by header
    grouped_data = defaultdict(list)
    for item in processed_data:
        grouped_data[item['header']].append(item)

    # Merge pairs of dictionaries
    merged_data = []
    for header, items in grouped_data.items():
        # Check if there are pairs to merge
        if len(items) >= 2:
            # Generate all possible pairs of items
            for item1, item2 in combinations(items, 2):
                merged_item = {
                    'header': header,
                    'relation_1': item1['relation'],
                    'tail_1': item1['tail'],
                    'relation_2': item2['relation'],
                    'tail_2': item2['tail']
                }
                merged_data.append(merged_item)

    # Create questions for merged data
    data = []
    for i in merged_data:
        ques = create_question(i)
        if ques == "NULL":
            continue
        data.append({
            "question": ques,
            "question_type": f"{i['relation_1']}_đến_{i['relation_2']}",
            "answer": i['tail_2'],
        })

    # Process each item to get prompt questions
    save_data = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(process_item, i): i for i in data}
        for future in tqdm(as_completed(future_to_item), total=len(data)):
            item = future.result()
            if item is not None:
                save_data.append(item)

    # Save processed data to output file
    save_json(save_data, output_filename)

# Define input and output file names
input_filename = '../../data/benchmark/triples.json'
output_filename = '../../data/benchmark/2hop.json'

# Execute main function
if __name__ == "__main__":
    main(input_filename, output_filename)

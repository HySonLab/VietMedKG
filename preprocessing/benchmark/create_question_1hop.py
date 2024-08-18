from utils import read_json, save_json
from preprocessing.llm import get_GPT
import warnings
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import json 

# Ignore all warnings
warnings.filterwarnings("ignore")

class Question_benh_to_X:
    def __init__(self, input_filename, output_filename):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.relation_dict = {
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

    def process_data(self, data):
        """
        Replace relation values in data with new dictionary format.

        Args:
        - data (list): List of dictionaries containing medical information.

        Returns:
        - list: Processed data with updated relation values.
        """
        for item in data:
            if item['relation'] in self.relation_dict:
                item['relation'] = self.relation_dict[item['relation']]
        return data

    def create_question(self, item):
        """
        Create a question based on the given item.

        Args:
        - item (dict): Dictionary containing 'relation' and 'header' keys.

        Returns:
        - str or None: Generated question or None if relation is not recognized.
        """
        if item['relation'] == 'mô_tả':
            return f"Mô tả về [{item['header']}]?"
        elif item['relation'] == 'loại':
            return f"[{item['header']}] thuộc loại bệnh nào?"
        elif item['relation'] == 'cách_phòng_tránh':
            return f"Cách phòng tránh [{item['header']}]?"
        elif item['relation'] == 'nguyên_nhân':
            return f"Nguyên nhân dẫn đến [{item['header']}]?"
        elif item['relation'] == 'triệu_chứng':
            return f"Triệu chứng của [{item['header']}]?"
        elif item['relation'] == 'đối_tượng_dễ_mắc_bệnh':
            return f"Đối tượng dễ mắc [{item['header']}]?"
        elif item['relation'] == 'bệnh_đi_kèm':
            return f"Các bệnh thường xảy ra cùng với [{item['header']}]?"
        elif item['relation'] == 'khoa_điều_trị':
            return f"Bạn có thể đến khoa nào để điều trị [{item['header']}]?"
        elif item['relation'] == 'phương_pháp_điều_trị':
            return f"Phương pháp điều trị [{item['header']}]?"
        elif item['relation'] == 'tỉ_lệ_chữa_khỏi':
            return f"Tỉ lệ chữa khỏi [{item['header']}]?"
        elif item['relation'] == 'kiểm_tra':
            return f"Bạn cần kiểm tra những gì khi mắc [{item['header']}]?"
        elif item['relation'] == 'thực_phẩm_nên_ăn':
            return f"Thực phẩm nên ăn trong quá trình chữa [{item['header']}]?"
        elif item['relation'] == 'thực_phẩm_không_nên_ăn':
            return f"Thực phẩm không nên ăn trong quá trình chữa [{item['header']}]?"
        elif item['relation'] == 'món_ăn_được_đề_xuất':
            return f"Món ăn nên ăn trong quá trình chữa [{item['header']}]?"
        elif item['relation'] == 'thuốc_đề_xuất':
            return f"Các loại thuốc được đề xuất khi chữa [{item['header']}]?"
        elif item['relation'] == 'thuốc_phổ_biến':
            return f"Các loại thuốc phổ biến được dùng để chữa [{item['header']}]?"
        elif item['relation'] == 'thông_tin_về_thuốc':
            return f"Thông tin chi tiết về thuốc để chữa [{item['header']}]?"
        else:
            return None

    def generate_question(self, item):
        """
        Generate a human-like question based on the given question text using GPT-3.

        Args:
        - item (dict): Dictionary containing 'question' key with bracketed entity.

        Returns:
        - str or None: Generated question or None if no valid response from GPT-3.
        """
        prompt = f"""Imagine you are a doctor, have a lot of patients and receive lots of questions everyday. 
            Create a human-like question based on the given question [{item['question']}]
            and return in json format with only returned question: 
            {{
                {"question": ""}
            }}.
            For example: {{"question": "Bạn có thể cho tôi biết thêm về [Ung thư tế bào tuyến nang] không?"}}
            You have to keep the bracket [] in the question.  Specially, if the answer do not contain any information like "Không có thông tin cụ thể",etc, return {{}}"""

        result = get_GPT(prompt)
        try:
            result = eval(result[result.find('{'): result.rfind('}') + 1])
        except:
            return None

        if result == {}:
            return None
        return result['question']

    def process_item(self, item):
        """
        Process an item to generate a human-like question and update the item with the question.

        Args:
        - item (dict): Dictionary containing 'question' and 'answer' keys.

        Returns:
        - dict or None: Updated item with generated question or None if no valid question could be generated.
        """
        if item['answer'] == "Không có thông tin":
            return None

        generated_question = self.generate_question(item)
        if generated_question is None:
            return None

        item['question'] = generated_question
        return item

    def run_processing(self):
        """
        Load data, process each item to generate questions, and save valid items to output file.
        """
        json_data = read_json(self.input_filename)
        processed_data = self.process_data(json_data)

        save_data = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_item = {executor.submit(self.process_item, i): i for i in processed_data}
            for future in tqdm(as_completed(future_to_item), total=len(processed_data)):
                item = future.result()
                if item is not None:
                    save_data.append(item)
                    save_json(save_data, self.output_filename)

class Question_X_to_benh:
    def __init__(self, input_filename, output_filename):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.relation_dict = {
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

    def process_data(self, data):
        """
        Replace relation values in data with new dictionary format.

        Args:
        - data (list): List of dictionaries containing medical information.

        Returns:
        - list: Processed data with updated relation values.
        """
        for item in data:
            if item['relation'] in self.relation_dict:
                item['relation'] = self.relation_dict[item['relation']]
        return data

    def create_question(self, item):
        """
        Create a question based on the given item.

        Args:
        - item (dict): Dictionary containing 'relation' and 'header' keys.

        Returns:
        - str or None: Generated question or None if relation is not recognized.
        """
        if item['relation'] == 'mô_tả':
            return f"[{item['tail']}] là mô tả của bệnh gì?"
        elif item['relation'] == 'loại':
            return f"Các loại bệnh [{item['tail']}] có thể dùng để chỉ bệnh gì?"
        elif item['relation'] == 'cách_phòng_tránh':
            return f"Cách các phòng tránh [{item['tail']}] có thể được dùng cho bệnh gì?"
        elif item['relation'] == 'nguyên_nhân':
            return f"Các nguyên nhân [{item['tail']}] có thể dẫn đến bệnh gì?"
        elif item['relation'] == 'triệu_chứng':
            return f"Các triệu chứng [{item['tail']}] có thể dẫn đến bệnh gì?"
        elif item['relation'] == 'đối_tượng_dễ_mắc_bệnh':
            return f"Các đối tượng [{item['tail']}] thường dễ mắc các bệnh gì?"
        elif item['relation'] == 'bệnh_đi_kèm':
            return f"Các bệnh [{item['tail']}] xảy ra cùng lúc có thể là dấu hiệu của bệnh gì?"
        elif item['relation'] == 'khoa_điều_trị':
            return f"Bạn có thể đến khoa [{item['tail']}] để điều trị bệnh nào?"
        elif item['relation'] == 'phương_pháp_điều_trị':
            return f"Phương pháp điều trị [{item['tail']}] có thể dùng để điều trị bệnh nào?"
        elif item['relation'] == 'kiểm_tra':
            return f"Kiểm tra [{item['tail']}] khi bạn nghi ngờ mắc bệnh gì?"
        elif item['relation'] == 'thực_phẩm_nên_ăn':
            return f"Thực phẩm nên ăn [{item['tail']}] có thể trợ giúp trong quá trình chữa bệnh gì?"
        elif item['relation'] == 'thực_phẩm_không_nên_ăn':
            return f"Thực phẩm không nên ăn [{item['tail']}] có thể trợ giúp trong quá trình chữa bệnh gì?"
        elif item['relation'] == 'món_ăn_được_đề_xuất':
            return f"Món ăn nên ăn [{item['tail']}] có thể trợ giúp trong quá trình chữa bệnh gì?"
        elif item['relation'] == 'thuốc_đề_xuất':
            return f"Các loại thuốc [{item['tail']}] được đề xuất khi chữa bệnh gì?"
        elif item['relation'] == 'thuốc_phổ_biến':
            return f"Các loại thuốc phổ biến [{item['tail']}] được dùng để chữa bệnh gì?"
        else:
            return "NULL"

    def generate_question(self, text):
        """
        Generate a human-like question based on the given question text using GPT-3.

        Args:
        - text (str): Question text with entity in brackets.

        Returns:
        - str or None: Generated question or None if no valid response from GPT-3.
        """
        prompt = f"""Imagine you are a doctor, have a lot of patients and receive lots of questions everyday. 
            Create a human-like question based on the given question [{text}] and return in json format: {{"question": ""}}.
            For example: {{"question": "Bệnh nào có thể được mô tả trong [Bách khoa toàn thư về bệnh, nội khoa, huyết học]?"}}
            You have to keep the bracket [] for entity (it is actually a node in knowledge graph so you have to preserve its content) in the question. 
            Each question must have only 1 bracket. Specially, if the content inside the bracket [] do not contain any information like "Không có thông tin cụ thể",etc, return {{}}.
            There are some requirements you need to know: 
            - Length of questions must be less than 25 words. 
            - The question should be smooth, in form of a sentence. 
            For the content in bracket [], if the length is more than 20, you should do the following task: 
                + For long string, you have to summarize and take one or few points to ask questions.
                + For a list, you should take a few elements for creating questions. 
                + Delete the name or name-related of disease as the answer is about the name of disease
                + You have to retain the [] for entity and put adjusted content in.
            - Consider adjusting carefully to ask informative, meaningful question 
            - The entity inside bracket [] is really important, please do not miss it, you have to check for it before return the result. 
            - Check if all the requirements are met or not, if not, read the requirements and do it again.
            """
        result = get_GPT(prompt)
        try:
            result = eval(result[result.find('{'): result.rfind('}') + 1])
        except:
            return "NULL"

        if result == {}:
            return "NULL"
        return result['question']

    def process_item(self, item):
        """
        Process an item to generate a human-like question and update the item with the question.

        Args:
        - item (dict): Dictionary containing 'question' and 'answer' keys.

        Returns:
        - dict or None: Updated item with generated question or None if no valid question could be generated.
        """
        if item['answer'] == "Không có thông tin":
            return None

        generated_question = self.generate_question(item['question'])
        if generated_question == "NULL":
            return None

        item['question'] = generated_question
        return item

    def run_processing(self):
        """
        Load data, process each item to generate questions, and save valid items to output file.
        """
        json_data = read_json(self.input_filename)
        processed_data = self.process_data(json_data)

        save_data = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_item = {executor.submit(self.process_item, i): i for i in processed_data}
            for future in tqdm(as_completed(future_to_item), total=len(processed_data)):
                item = future.result()
                if item is not None:
                    save_data.append(item)

        save_json(save_data, self.output_filename)

def merge_json_files(file1, file2, output_file):
    """
    Merge two JSON files containing lists of dictionaries into a single JSON file.

    Args:
    - file1 (str): Path to the first JSON file.
    - file2 (str): Path to the second JSON file.
    - output_file (str): Path to the output JSON file where merged data will be saved.
    """
    # Read data from file1
    with open(file1, 'r', encoding='utf-8') as f:
        data1 = json.load(f)
    
    # Read data from file2
    with open(file2, 'r', encoding='utf-8') as f:
        data2 = json.load(f)
    
    # Merge data
    merged_data = data1 + data2
    
    # Write merged data to output_file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    generator1 = Question_benh_to_X('../../data/benchmark/triples.json', '../../data/benchmark/1hop_disease_to_X.json')
    generator1.run_processing()
    generator2 = Question_X_to_benh('../../data/benchmark/triples.json', '../../data/benchmark/1hop_X_to_disease.json')
    generator2.run_processing()
    merge_json_files('../../data/benchmark/1hop_disease_to_X.json', '../../data/benchmark/1hop_X_to_disease.json', '../../data/benchmark/1_hop.json')



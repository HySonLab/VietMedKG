from utils import read_json, save_json
import re
from collections import defaultdict
from sklearn.metrics import jaccard_score
from sklearn.preprocessing import MultiLabelBinarizer


class QuestionProcessor:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.grouped_data = defaultdict(list)
        self.merged_data = []

    def extract_content(self, question):
        """
        Extract content within square brackets from the question.
        
        Args:
            question (str): The question string.
            
        Returns:
            str: Extracted content in lowercase or None if not found.
        """
        try: 
            return re.search(r'\[(.*?)\]', question).group(1).lower()
        except:
            return None

    def jaccard_similarity(self, set1, set2):
        """
        Compute the Jaccard similarity score between two sets.
        
        Args:
            set1 (set): First set of elements.
            set2 (set): Second set of elements.
            
        Returns:
            float: Jaccard similarity score.
        """
        mlb = MultiLabelBinarizer()
        sets = mlb.fit_transform([set1] + [set2])
        return jaccard_score(sets[0], sets[1])

    def remove_duplicates(self, list_of_dicts):
        """
        Remove duplicate dictionaries from a list of dictionaries.
        
        Args:
            list_of_dicts (list): List of dictionaries.
            
        Returns:
            list: List of unique dictionaries.
        """
        seen = set()
        unique_dicts = []
        for d in list_of_dicts:
            dict_tuple = frozenset(d.items())
            if dict_tuple not in seen:
                seen.add(dict_tuple)
                unique_dicts.append(d)
        return unique_dicts

    def process_questions(self):
        """Process and group questions, then merge similar ones."""
        data = read_json(self.input_file)
        data = self.remove_duplicates(data)

        for item in data:
            question_type = item["question_type"]
            content = self.extract_content(item["question"])
            if content is None:
                continue
            item["content"] = content
            self.grouped_data[question_type].append(item)

        for question_type, items in self.grouped_data.items():
            merged_items = []
            while items:
                base_item = items.pop(0)
                similar_items = [base_item]
                
                for other_item in items[:]:
                    similarity = self.jaccard_similarity(set(base_item["content"].split()), set(other_item["content"].split()))
                    if similarity >= 0.9:
                        similar_items.append(other_item)
                        items.remove(other_item)
                
                merged_question = base_item["question"]
                merged_answer = "|".join(item["answer"] for item in similar_items)
                
                merged_items.append({
                    "question": merged_question,
                    "question_type": question_type,
                    "answer": merged_answer
                })
            
            self.merged_data.extend(merged_items)

    def save_processed_questions(self):
        """Save the processed and merged questions to a file."""
        self.save_json(self.merged_data, self.output_file)


def main(input_filename):
    processor = QuestionProcessor(input_filename, input_filename)
    processor.process_questions()
    processor.save_processed_questions()

if __name__ == "__main__":
    input_filename_1 = '../../data/benchmark/1_hop.json'
    input_filename_2 = '../../data/benchmark/2_hop.json'
    main(input_filename_1)
    main(input_filename_2)
    

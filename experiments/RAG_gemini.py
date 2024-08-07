import requests
from requests.auth import HTTPBasicAuth

# from config import SECTION_1_PROMPT
import os
import json
from dotenv import load_dotenv
from langchain_community.chat_models import AzureChatOpenAI
from langchain.schema import (
    HumanMessage,
)

import json
import os
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge
from nltk.translate.meteor_score import meteor_score
import nltk
from nltk.translate.bleu_score import SmoothingFunction

nltk.download("wordnet")

# Initialize ROUGE scorer
rouge = Rouge()

load_dotenv("key.env")
access_token = ""

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph

# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_community.vectorstores import Neo4jVector

import langchain

import google.generativeai as genai


uri = os.getenv("URI")
user = os.getenv("USER")
password = os.getenv("PASSWORD")

google_api_key = os.getenv("GOOGLE_API_KEY")


embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=google_api_key,
)


graph = Neo4jGraph(url=uri, username=user, password=password)


examples = [
    {
        "question": "Phương pháp điều trị cho bệnh [U lympho sau phúc mạc] là gì?",
        "query": "MATCH (b:ĐIỀU_TRỊ) WHERE b.tên_bệnh = 'U lympho sau phúc mạc' RETURN b",
    },
    {
        "question": "Nguyên nhân của bệnh [Chảy máu khoảng cách sau phúc mạc] là gì?",
        "query": "MATCH (b:BỆNH) WHERE b.tên_bệnh = 'Chảy máu khoảng cách sau phúc mạc' RETURN b",
    },
    {
        "question": "Triệu chứng của bệnh [Chảy máu khoảng cách sau phúc mạc] là gì?",
        "query": "MATCH (b:TRIỆU_CHỨNG) WHERE b.tên_bệnh = 'Chảy máu khoảng cách sau phúc mạc' RETURN b",
    },
    {
        "question": "Những bệnh lý nào có thể xuất hiện khi có triệu chứng [Khóc và đau]?",
        "query": "MATCH (b:TRIỆU_CHỨNG) WHERE b.triệu_chứng = 'Khóc và đau' RETURN b",
    },
    {
        "question": "Có những loại thuốc phổ biến nào để điều trị bệnh [Chảy máu khoảng cách sau phúc mạc]?",
        "query": "MATCH (b:THUỐC) WHERE b.tên_bệnh = 'Chảy máu khoảng cách sau phúc mạc' RETURN b",
    },
]

# {
#     "question": "Kiểm tra nào được sử dụng để chẩn đoán bệnh Chảy máu khoảng cách sau phúc mạc?",
#     "query": "MATCH (b:BỆNH {tên_bệnh: 'Chảy máu khoảng cách sau phúc mạc'}) RETURN b.kiểm_tra AS diagnostic_tests",
# },
# {
#     "question": "Bệnh U lympho sau phúc mạc thuộc loại bệnh nào?",
#     "query": "MATCH (b:BỆNH {tên_bệnh: 'U lympho sau phúc mạc'}) RETURN b.loại_bệnh AS disease_type",
# },
# {
#     "question": "Tỷ lệ chữa khỏi của bệnh Chảy máu khoảng cách sau phúc mạc là bao nhiêu?",
#     "query": "MATCH (b:BỆNH {tên_bệnh: 'Chảy máu khoảng cách sau phúc mạc'}) RETURN b.tỉ_lệ_chữa_khỏi AS cure_rate",
# },
# {
#     "question": "Các đối tượng dễ mắc bệnh Chảy máu khoảng cách sau phúc mạc là ai?",
#     "query": "MATCH (b:BỆNH {tên_bệnh: 'Chảy máu khoảng cách sau phúc mạc'}) RETURN b.đối_tượng_dễ_mắc_bệnh AS susceptible_groups",
# },
# {
#     "question": "Các khoa điều trị bệnh Chảy máu khoảng cách sau phúc mạc là gì?",
#     "query": "MATCH (b:BỆNH {tên_bệnh: 'Chảy máu khoảng cách sau phúc mạc'}) RETURN b.khoa_điều_trị AS treatment_departments",
# },
# {
#     "question": "Có những loại thuốc phổ biến nào để điều trị bệnh Chảy máu khoảng cách sau phúc mạc?",
#     "query": "MATCH (b:BỆNH {tên_bệnh: 'Chảy máu khoảng cách sau phúc mạc'}) RETURN b.thuốc_phổ_biến AS common_medications",
# },
# {
#     "question": "Các biện pháp phòng tránh bệnh Chảy máu khoảng cách sau phúc mạc là gì?",
#     "query": "MATCH (b:BỆNH {tên_bệnh: 'Chảy máu khoảng cách sau phúc mạc'}) RETURN b.cách_phòng_tránh AS prevention_methods",
# },


# Paths
results_dir = "/Users/hoanganh692004/Desktop/products-knowledge-graph/results"
logs_dir = "/Users/hoanganh692004/Desktop/products-knowledge-graph/logs"

gemini_results_path = os.path.join(results_dir, "gemini_graph_cypher.txt")
gemini_log_path = os.path.join(logs_dir, "gemini_graph_cypher.json")

# Initialize lists to store scores
gemini_scores = {"BLEU": [], "ROUGE": [], "METEOR": []}

# Logs to store answers and scores
gemini_log = []

smoothing_function = SmoothingFunction().method1


def get_scores(hypothesis, reference):
    hypothesis_tokens = hypothesis.split()
    reference_tokens = reference.split()
    bleu = sentence_bleu(
        [reference_tokens], hypothesis_tokens, smoothing_function=smoothing_function
    )
    rouge_score = rouge.get_scores(hypothesis, reference)[0]["rouge-l"]["f"]
    meteor = meteor_score([reference_tokens], hypothesis_tokens)
    return bleu, rouge_score, meteor


example_prompt = PromptTemplate.from_template(
    "User input: {question}\nCypher query: {query}"
)

PREFIX = """
    I have a knowledge graph for Vietnamese traditional medicine, where each node represents a disease "BỆNH", "ĐIỀU_TRỊ", "TRIỆU_CHỨNG", "THUỐC", "LỜI_KHUYÊN". Each node can have the following properties:
    1. BỆNH
        - mô_tả_bệnh
        - loại_bệnh
        - tên_bệnh
        - nguyên_nhân
    2. ĐIỀU_TRỊ
        - khoa_điều_trị
        - tỉ_lệ_chữa_khỏi
        - tên_bệnh
        - phương_pháp
    3. TRIỆU_CHỨNG
        - kiểm_tra
        - đối_tượng_dễ_mắc_bệnh
        - triệu_chứng
        - tên_bệnh
    4. THUỐC
        - thuốc_phổ_biến
        - thông_tin_thuốc
        - đề_xuất_thuốc
        - tên_bệnh
    5. LỜI_KHUYÊN
        - không_nên_ăn_thực_phẩm_chứa
        - nên_ăn_thực_phẩm_chứa
        - tên_bệnh
        - cách_phòng_tránh
        - đề_xuất_món_ăn
    You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\nBelow are a number of examples of questions and their corresponding Cypher queries.",
    """

prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix=PREFIX,
    suffix="User input: {question}\nCypher query: ",
    input_variables=["question", "schema"],
)

gemini_chain = GraphCypherQAChain.from_llm(
    ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key="AIzaSyCaNF1Yh50y3TKwWZvxUJ6tqmrJ8x0FSuE",
    ),
    graph=graph,
    verbose=True,
    cypher_prompt=prompt,
)


def write_log_entry(entry, file_path):
    with open(file_path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False, indent=4) + ",\n")


def run(chain, question):
    return chain.run(question)


def call_model_with_retry(model_func, prompt):
    while True:
        try:
            result = model_func(prompt)
            return result
        except Exception as e:
            print(f"Error: {e}. Retrying...")


def get_gemini(text):

    genai.configure(api_key=google_api_key)

    # Set up the model
    generation_config = {
        "temperature": 0,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 50000,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
    ]

    model = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    response = model.generate_content([text])
    response = response.text

    return response


file_path = "data/benchmark/1_hop_500.json"

# Read the JSON file
with open(file_path, "r") as file:
    data = json.load(file)


def call_model_with_retry(model_func, prompt):
    while True:
        try:
            result = model_func(prompt)
            return result
        except Exception as e:
            print(f"Error: {e}. Retrying...")


import time

gemini_inference_times = []

# Process the first 20 samples
for i, x in enumerate(data[:20]):  # Limit to the first 20 samples
    # Gemini inference
    try:
        start_time = time.time()
        gemini_result = run(gemini_chain, x["question"])
        end_time = time.time()
        gemini_inference_times.append(end_time - start_time)
    except Exception as e:
        print(f"An error occurred: {e}")
        PROMPT = f"""
        Bạn là một chuyên gia về y học cổ truyền Việt Nam. Hãy trả lời đúng trọng tâm câu hỏi, không cần bổ sung thêm thông tin.
        Câu hỏi: {x["question"]}
        """
        start_time = time.time()
        gemini_result = call_model_with_retry(get_gemini, PROMPT)
        end_time = time.time()
        gemini_inference_times.append(end_time - start_time)

    reference = x["answer"]

    if not gemini_result.strip():
        gemini_result = f"Tôi không có thông tin về: {x['question']}"

    # Calculate scores for Gemini
    gemini_bleu, gemini_rouge, gemini_meteor = get_scores(gemini_result, reference)
    gemini_scores["BLEU"].append(gemini_bleu)
    gemini_scores["ROUGE"].append(gemini_rouge)
    gemini_scores["METEOR"].append(gemini_meteor)

    log_entry = {
        "question": x["question"],
        "answer": gemini_result,
        "ground_truth": x["answer"],
        "BLEU": gemini_bleu,
        "ROUGE": gemini_rouge,
        "METEOR": gemini_meteor,
    }

    gemini_log.append(log_entry)

    write_log_entry(log_entry, gemini_log_path)

# Calculate and print the average inference times
average_gemini_inference_time = sum(gemini_inference_times) / len(
    gemini_inference_times
)

print(f"Average Inference Time for Gemini: {average_gemini_inference_time} seconds")


# Calculate mean scores and write to text files
def write_mean_scores(scores, file_path):
    mean_scores = {
        metric: sum(values) / len(values) for metric, values in scores.items()
    }
    with open(file_path, "w") as f:
        for metric, score in mean_scores.items():
            f.write(f"{metric}: {score}\n")


write_mean_scores(gemini_scores, gemini_results_path)


# Write logs to JSON files
def write_log(log, file_path):
    with open(file_path, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=4)


write_log(gemini_log, gemini_log_path)

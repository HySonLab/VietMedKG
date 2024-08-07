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

import langchain
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph

# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_community.vectorstores import Neo4jVector

import json
import os
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge
from nltk.translate.meteor_score import meteor_score
import nltk
from nltk.translate.bleu_score import SmoothingFunction


load_dotenv("key.env")
access_token = ""

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

cov_get_token_url = (
    "https://auth.api.covestro.com/oauth2/token?grant_type=client_credentials"
)
cov_get_apikey_url = "https://api.covestro.com/openai/apikey"

openai_api_base = os.getenv("OPENAI_API_BASE")
openai_api_type = os.getenv("OPENAI_API_TYPE")
openai_api_version = os.getenv("OPENAI_API_VERSION")
openai_api_deployment = os.getenv("OPENAI_MODEL_DEPLOYMENT")

azure_api_key = ""

uri = os.getenv("URI")
user = os.getenv("USER")
password = os.getenv("PASSWORD")


graph = Neo4jGraph(url=uri, username=user, password=password)


def get_authen():

    global access_token

    if access_token != "":
        return access_token

    url = "https://auth.api.covestro.com/oauth2/token?grant_type=client_credentials"

    username = "1bnt12o2j53b16id2eerklhd4a"
    password = "kuo3n1nnkngel01lloems2ipop46ovt7l7fqdmb5mcmt5bv7ub2"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(
        url, auth=HTTPBasicAuth(username, password), headers=headers, verify=True
    )

    if response.status_code == 200:
        access_token = response.json()["access_token"]
        return access_token
    return -1


def get_apiKey():
    global access_token
    global azure_api_key

    if azure_api_key != "":
        return azure_api_key

    bearer_token = get_authen()

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    response = requests.get(cov_get_apikey_url, headers=headers, verify=True)

    if response.status_code >= 200 and response.status_code < 300:
        azure_api_key = response.json()["apiKey"]
        return azure_api_key
    else:
        # invalidate access token
        access_token = ""
        logger.error(f"Error: {response.status_code} {response.reason}")
    return requests.exceptions.RequestException


def get_azureGPT_model():
    global azure_api_key

    azure_api_key = get_apiKey()

    llm = AzureChatOpenAI(
        openai_api_key=azure_api_key,
        openai_api_base=openai_api_base,
        openai_api_type=openai_api_type,
        openai_api_version=openai_api_version,
        deployment_name=openai_api_deployment,
        temperature=0,
    )

    return llm


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


nltk.download("wordnet")

# Initialize ROUGE scorer
rouge = Rouge()

# Paths
results_dir = "results"
logs_dir = "logs"

gpt4_results_path = os.path.join(results_dir, "gpt4_graph_cypher.txt")
gpt4_log_path = os.path.join(logs_dir, "gpt4_graph_cypher.json")

# Initialize lists to store scores
gpt4_scores = {"BLEU": [], "ROUGE": [], "METEOR": []}

# Logs to store answers and scores
gpt4_log = []

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


gpt4_chain = GraphCypherQAChain.from_llm(
    get_azureGPT_model(),
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


def get_azureGPT(text):
    global azure_api_key

    azure_api_key = get_apiKey()

    llm = AzureChatOpenAI(
        openai_api_key=azure_api_key,
        openai_api_base=openai_api_base,
        openai_api_type=openai_api_type,
        openai_api_version=openai_api_version,
        deployment_name=openai_api_deployment,
        temperature=0,
    )
    messages = [HumanMessage(content=text)]

    # try:
    # TODO check reposponse code. if error invalidate api key
    response = llm(messages)
    return response.content
    # except Exception as e:
    #     # invalidate api key
    #     print(e)
    #     azure_api_key = ""
    #     return -1


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

gpt4_inference_times = []

# Process the first 20 samples
for i, x in enumerate(data[:20]):  # Limit to the first 20 samples

    # GPT-4 inference
    try:
        start_time = time.time()
        gpt4_result = run(gpt4_chain, x["question"])
        end_time = time.time()
        gpt4_inference_times.append(end_time - start_time)
    except Exception as e:
        print(f"An error occurred: {e}")
        PROMPT = f"""
        Bạn là một chuyên gia về y học cổ truyền Việt Nam. Hãy trả lời đúng trọng tâm câu hỏi, không cần bổ sung thêm thông tin.
        Câu hỏi: {x["question"]}
        """
        start_time = time.time()
        gpt4_result = call_model_with_retry(get_azureGPT, PROMPT)
        end_time = time.time()
        gpt4_inference_times.append(end_time - start_time)

    reference = x["answer"]

    if not gpt4_result.strip():
        gpt4_result = f"Tôi không có thông tin về: {x['question']}"

    # Calculate scores for GPT-4
    gpt4_bleu, gpt4_rouge, gpt4_meteor = get_scores(gpt4_result, reference)
    gpt4_scores["BLEU"].append(gpt4_bleu)
    gpt4_scores["ROUGE"].append(gpt4_rouge)
    gpt4_scores["METEOR"].append(gpt4_meteor)

    gpt_log_entry = {
        "question": x["question"],
        "answer": gpt4_result,
        "ground_truth": x["answer"],
        "BLEU": gpt4_bleu,
        "ROUGE": gpt4_rouge,
        "METEOR": gpt4_meteor,
    }

    gpt4_log.append(gpt_log_entry)

    write_log_entry(gpt_log_entry, gpt4_log_path)


average_gpt4_inference_time = sum(gpt4_inference_times) / len(gpt4_inference_times)

print(f"Average Inference Time for GPT4: {average_gpt4_inference_time} seconds")


# Calculate mean scores and write to text files
def write_mean_scores(scores, file_path):
    mean_scores = {
        metric: sum(values) / len(values) for metric, values in scores.items()
    }
    with open(file_path, "w") as f:
        for metric, score in mean_scores.items():
            f.write(f"{metric}: {score}\n")


write_mean_scores(gpt4_scores, gpt4_results_path)


# Write logs to JSON files
def write_log(log, file_path):
    with open(file_path, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=4)


write_log(gpt4_log, gpt4_log_path)

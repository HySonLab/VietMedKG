from langchain_core.messages import HumanMessage, SystemMessage


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
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge
from nltk.translate.meteor_score import meteor_score
import nltk
from nltk.translate.bleu_score import SmoothingFunction

load_dotenv("key.env")
access_token = ""


cov_get_token_url = (
    "https://auth.api.covestro.com/oauth2/token?grant_type=client_credentials"
)
cov_get_apikey_url = "https://api.covestro.com/openai/apikey"

openai_api_base = os.getenv("OPENAI_API_BASE")
openai_api_type = os.getenv("OPENAI_API_TYPE")
openai_api_version = os.getenv("OPENAI_API_VERSION")
openai_api_deployment = os.getenv("OPENAI_MODEL_DEPLOYMENT")

# Set up the model
generation_config = {
    "temperature": 0,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 50000,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]


def requests_retry_session(
    retries=5,
    backoff_factor=1,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


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


def get_covGPT(text):
    api_url = "https://lengthy.api.covestro.com/openai/chat/gpt4"
    bearer_token = get_authen()
    json_data = {
        "temperature": 0,
        # "response_format": {"type": "json_object"},
        "messages": [
            # {"role": "system", "content": "You are a helpful assistant fluent in German, your task is to carefully read the given text and extract the information to the JSON format. You must return the output as the valid JSON, property name should be enclosed in double quotes."},
            {"role": "user", "content": text}
        ],
    }

    # Set headers with Bearer token
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    json_data_str = json.dumps(json_data)

    response = requests_retry_session().post(
        api_url, headers=headers, data=json_data_str, verify=True
    )
    # print(response.json())

    # Check for successful response (status code 2xx)
    if response.status_code >= 200 and response.status_code < 300:
        data = response.json()["choices"][0]["message"]["content"]
        return data
    else:
        print(response)
        print(f"Error: {response.status_code} {response.reason}")
    return requests.exceptions.RequestException


def get_covGPT_section2(text):
    api_url = "https://lengthy.api.covestro.com/openai/chat/gpt4turbo"
    bearer_token = get_authen()
    json_data = {
        "temperature": 0,
        "messages": [{"role": "user", "content": text}],
        "functions": section2_custom_functions,
        "function_call": "auto",
    }
    # Set headers with Bearer token
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    json_data_str = json.dumps(json_data)

    response = requests.post(api_url, headers=headers, data=json_data_str, verify=True)
    # print(response.json())

    # Check for successful response (status code 2xx)
    if response.status_code >= 200 and response.status_code < 300:
        data = response.json()["choices"][0]["message"]["content"]
        return data
    else:
        print(f"Error: {response.status_code} {response.reason}")
    return requests.exceptions.RequestException


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


# Define the path to the JSON file
file_path = "data/benchmark/resampled_1_hop.json"

# Read the JSON file
with open(file_path, "r") as file:
    data = json.load(file)


nltk.download("wordnet")

# Initialize ROUGE scorer
rouge = Rouge()

# Paths
results_dir = "results"
logs_dir = "logs"

gpt4_results_path = os.path.join(results_dir, "gpt4_zero_shot.txt")
gpt4_log_path = os.path.join(logs_dir, "gpt4_zero_shot.json")

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


def call_model_with_retry(model_func, prompt):
    while True:
        try:
            result = model_func(prompt)
            return result
        except Exception as e:
            print(f"Error: {e}. Retrying...")


import time

# Initialize lists to store inference times
gpt4_inference_times = []

# Process the first 20 samples
for i, x in enumerate(data[:10]):  # Limit to the first 20 samples
    PROMPT = f"""
    Bạn là một chuyên gia về y học cổ truyền Việt Nam. Hãy trả lời đúng trọng tâm câu hỏi, không cần bổ sung thêm thông tin.
    Câu hỏi: {x["question"]}
    """

    # GPT-4 inference
    start_time = time.time()
    gpt4_result = call_model_with_retry(get_azureGPT, PROMPT)
    end_time = time.time()
    gpt4_inference_times.append(end_time - start_time)

    reference = x["answer"]

    # Calculate scores for GPT-4
    gpt4_bleu, gpt4_rouge, gpt4_meteor = get_scores(gpt4_result, reference)
    gpt4_scores["BLEU"].append(gpt4_bleu)
    gpt4_scores["ROUGE"].append(gpt4_rouge)
    gpt4_scores["METEOR"].append(gpt4_meteor)
    gpt4_log.append(
        {
            "question": x["question"],
            "answer": gpt4_result,
            "BLEU": gpt4_bleu,
            "ROUGE": gpt4_rouge,
            "METEOR": gpt4_meteor,
        }
    )

average_gpt4_inference_time = sum(gpt4_inference_times) / len(gpt4_inference_times)

print(f"Average Inference Time for GPT-4: {average_gpt4_inference_time} seconds")


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

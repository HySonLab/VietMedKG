import google.generativeai as genai

import requests
from requests.auth import HTTPBasicAuth
from langchain_google_genai import ChatGoogleGenerativeAI

# from config import SECTION_1_PROMPT
import os
import json
from dotenv import load_dotenv

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


google_api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.7,
    top_p=0.85,
    google_api_key=google_api_key,
    convert_system_message_to_human=True,
)


def get_gemini(text):
    response = llm.invoke([text])
    # response = response.text

    return response


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

gemini_results_path = os.path.join(results_dir, "gemini_zero_shot.txt")
gemini_log_path = os.path.join(logs_dir, "gemini_zero_shot.json")

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


def call_model_with_retry(model_func, prompt):
    while True:
        try:
            result = model_func(prompt)
            return result
        except Exception as e:
            print(f"Error: {e}. Retrying...")


import time

# Initialize lists to store inference times
gemini_inference_times = []


# Process the first 20 samples
for i, x in enumerate(data[:10]):  # Limit to the first 20 samples
    PROMPT = f"""
    Bạn là một chuyên gia về y học cổ truyền Việt Nam. Hãy trả lời đúng trọng tâm câu hỏi, không cần bổ sung thêm thông tin.
    Câu hỏi: {x["question"]}
    """

    start_time = time.time()
    gemini_result = call_model_with_retry(get_gemini, PROMPT)

    end_time = time.time()
    gemini_inference_times.append(end_time - start_time)

    reference = x["answer"]

    gemini_bleu, gemini_rouge, gemini_meteor = get_scores(gemini_result, reference)
    gemini_scores["BLEU"].append(gemini_bleu)
    gemini_scores["ROUGE"].append(gemini_rouge)
    gemini_scores["METEOR"].append(gemini_meteor)
    gemini_log.append(
        {
            "question": x["question"],
            "answer": gemini_result,
            "BLEU": gemini_bleu,
            "ROUGE": gemini_rouge,
            "METEOR": gemini_meteor,
        }
    )

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

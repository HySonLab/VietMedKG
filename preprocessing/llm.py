import os
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai

load_dotenv()
genai.configure(api_key="<INSERT_YOUR_KEY_HERE>")

# Set up the model
generation_config = {
  "temperature": 0,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 50000,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  }
]

model = genai.GenerativeModel(model_name="gemini-1.0-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)


def get_GPT(text):
    os.environ['OPENAI_API_KEY'] = api_key
    openai.api_key = os.environ['OPENAI_API_KEY']
    client = OpenAI()
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{
        "role": "system", "content": "You are a Vietnamese and Chinease linguistic and pharmarcist and expert in 2 these fields",
        "role": "user", "content": text}],
    temperature=0,
    )
    return  response.choices[0].message.content
 
def get_gemini(text): 
    response = model.generate_content([text])
    response = response.text

    return response
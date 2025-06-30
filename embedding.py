import os
from langchain_openai import OpenAIEmbeddings
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
#MONGO_URI = os.environ.get("MONGODB_URI")
#openai_api_key = os.environ.get("OPENAI_KEY")

MONGO_URI = st.secrets["MONGODB_URI"]
openai_api_key = st.secrets["OPENAI_KEY"]

if not MONGO_URI or not openai_api_key:
    raise ValueError("MONGODB_URI and OPENAI_KEY must be set in environment variables.")

embeddings_model = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=openai_api_key)

client = MongoClient(MONGO_URI)
db = client["pdf_file"]
collection = db["animal_bites"]

def store_question_answer(ques, ans):
    ques_embedding = embeddings_model.embed_query(ques)
    document = {"new": "unanswered", "question": ques, "answer": ans, "embedding": ques_embedding}
    collection.insert_one(document)
    print(f"✅ Data inserted successfully!\nQuestion: {ques}\nAnswer: {ans}")


import os
from chatbot import DIR_PATH
from chatbot.config import OPENAI_API_KEY, GROQ_API_KEY
from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


# load vector store
# index_path_rag = os.path.join(DIR_PATH, "faiss_index_ingredients")
# print("Loading FAISS index from:", index_path_rag)
# Load the FAISS databases
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large", openai_api_key=OPENAI_API_KEY
)
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
    temperature=0.3,
)
# new_db = FAISS.load_local(
#     index_path_rag, embeddings, allow_dangerous_deserialization=True
# )

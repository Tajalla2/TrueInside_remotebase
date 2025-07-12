import os
import json
import unstructured
import pandas as pd
from langchain import hub
from dotenv import load_dotenv
from chatbot import DIR_PATH
from langchain.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from chatbot.config import OPENAI_API_KEY


class vector_store:
    """A class to create vector store from data scaped from various sources. These sources includes
    information related to harmful, prohibited ingredients, and other related information.
    """

    def __init__(self):
        self.directory = DIR_PATH
        self.root_directory = os.path.join(self.directory, "ScrapedData")
        self.all_docs = []
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            max_tokens=None,
            max_retries=2,
            api_key=OPENAI_API_KEY,
        )

    def read_files(self):
        """Reads files from the ScrapedData directory and loads them into a list of documents."""
        all_docs = self.all_docs
        print(f"Reading files from {self.root_directory}")
        # Iterate through all directories and files in the root directory
        for dir_path, _, filenames in os.walk(self.root_directory):
            print(f"\nOpening files in folder: {dir_path}")
            print(dir_path)
            for file in filenames:
                file_path = os.path.join(dir_path, file)

                if file.endswith(".md"):
                    loader = UnstructuredMarkdownLoader(file_path)
                    data = loader.load()
                    all_docs.extend(data)
                    print(f"Loaded Markdown: {file}")

                elif file.endswith(".xlsx"):
                    try:
                        df = pd.read_excel(file_path, engine="openpyxl")
                        for _, row in df.iterrows():
                            content = "\n".join(
                                f"{col}: {val}" for col, val in row.items()
                            )
                            doc = Document(page_content=content)
                            all_docs.append(doc)
                        print(f"Loaded Excel: {file}")
                    except Exception as e:
                        print(f"Error loading Excel file {file}: {e}")
        return all_docs

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def create_and_store_vector_store(self):
        """Creates a vector store from the documents read from the ScrapedData directory."""
        text_splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        all_docs = self.read_files()
        page_contents = [page.page_content for page in all_docs]

        texts = text_splitter.create_documents(page_contents)

        plain_texts = [text.page_content for text in texts]

        # Create FAISS index from texts and embeddings
        try:
            # Try to create the FAISS index again
            docsearch = FAISS.from_texts(plain_texts, self.embeddings)
        except Exception as e:
            print(f"Error: {e}")
            if hasattr(e, "response"):
                print(f"Response: {e.response}")

            retriever = docsearch.as_retriever()
            prompt = hub.pull("rlm/rag-prompt")

            rag_chain = (
                {
                    "context": retriever | self.format_docs,
                    "question": RunnablePassthrough(),
                }
                | prompt
                | self.llm
                | StrOutputParser()
            )

            print(rag_chain.invoke("common haram items"))
            docsearch.save_local("faiss_index_ingredients")
            with open("faiss_index_ingredients/metadata.json", "w") as f:
                json.dump(page_contents, f)


# vs = vector_store()
# vs.create_and_store_vector_store()

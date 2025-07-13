from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import LLMChain
from chatbot.chatlogic.prompt import prompt, cleaning_template
from flask import request
from chatbot.chatlogic.core import llm, embeddings
from chatbot.chatlogic.ocr import extract_ingredients
from langchain_community.vectorstores import FAISS
from chatbot import DIR_PATH
import os
import base64
import tempfile
import json
from flask_socketio import emit
from chatbot.socket import socketio

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# load vector store
index_path_rag = os.path.join(DIR_PATH, "faiss_index_ingredients")
new_db = FAISS.load_local(
    index_path_rag, embeddings, allow_dangerous_deserialization=True
)


# Conversation Memory
memory_rag = ConversationBufferWindowMemory(
    k=3, memory_key="chat_history", input_key="question", return_messages=True
)

# LLM Chain
chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=False,
    memory=memory_rag,
    # output_parser=output_parser,
)


def clean_ingredients(raw_ocr):
    prompt = cleaning_template.format(raw_ocr=raw_ocr)
    cleaned = llm.invoke(prompt)  # or llm(prompt) depending on your LLM interface
    return cleaned


@socketio.on("trueinside-message")
def handle_message(data):

    sid = request.sid
    user_input = data.get("message", "").strip()
    image_base64 = data.get("image", None)
    all_docs = []

    if image_base64:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
                temp_img.write(base64.b64decode(image_base64))
                temp_img_path = temp_img.name
                print(f"🖼️ Temp image saved to {temp_img_path}")

            # OCR → Clean → Search
            ingredients = extract_ingredients(temp_img_path)
            print("📦 Extracted:", ingredients)

            cleaned_ingredients = clean_ingredients(ingredients)
            print("🧼 Cleaned:", cleaned_ingredients.content)

            converted_list = json.loads(cleaned_ingredients.content)
            for ingredient in converted_list:
                query = f"Any information related to {ingredient}"
                matched_docs = new_db.similarity_search(query, k=2)
                all_docs.extend(matched_docs)

        except Exception as e:
            print("❌ Error processing image:", e)
            emit("trueinside-response", {"message": "Image processing failed."})
            return
        finally:
            # Cleanup the temp file
            if "temp_img_path" in locals() and os.path.exists(temp_img_path):
                os.remove(temp_img_path)
                print(f"🧹 Temp image deleted: {temp_img_path}")

    # === Text-only message fallback ===
    elif user_input:
        print("💬 User message:", user_input)
        matched_docs = new_db.similarity_search(user_input, k=2)
        all_docs.extend(matched_docs)
    # ingredients = extract_ingredients(image_path)
    # print("--------------------------", ingredients)
    # cleaned_ingredients = clean_ingredients(ingredients)
    # print("--------------------------", cleaned_ingredients)
    # print("--------------------------", cleaned_ingredients.content)
    # converted_list = json.loads(cleaned_ingredients.content)
    # for ingredient in converted_list:
    #     print("Searching for ingredient:", ingredient)
    #     ingredient = "is this" + ingredient + "haram/halal or ethically questionable?"
    #     matched_docs = new_db.similarity_search(ingredient, k=2)
    #     print("Matched--------------", matched_docs)
    #     all_docs.extend(matched_docs)

    unique_pages = {doc.page_content for doc in all_docs}
    context = "\n\n".join(unique_pages)
    final_question = (
        user_input
        if user_input
        else "Analyze these ingredients for safety, religious and allergy concerns."
    )
    response = chain(
        {"context": context, "question": final_question}, return_only_outputs=True
    )
    bot_response = response.get("text", "Sorry, I could not generate a response.")
    emit("trueinside-response", {"message": bot_response})
    print(bot_response)


# result = handle_message(
#     "is this product safe for use?",
#     r"D:\Projects\TrueInside_remotebase\chatbot\chatlogic\images.jpeg",
# )
# print(result)

import gradio as gr
import socketio
import time
import os
import base64

# --- WebSocket Client Setup ---
sio = socketio.Client(logger=True, engineio_logger=True)
response_received = None


def connect_to_server():
    if not sio.connected:
        try:
            sio.connect("http://127.0.0.1:8000")
            print("✅ Connected to WebSocket server")
        except Exception as e:
            print(f"❌ Failed to connect: {str(e)}")
            return f"❌ Failed to connect: {str(e)}"


# --- WebSocket Event Listener ---
@sio.on("trueinside-response")
def receive_response(data):
    global response_received
    message = data.get("message", "")
    print("💬 Response received:", message)
    response_received = message
    return response_received


# --- Text Message Send ---
def send_message(user_input, history):
    global response_received
    if not sio.connected:
        connect_to_server()

    response_received = None
    sio.emit("trueinside-message", {"message": user_input})
    print("📨 Text message emitted")

    while response_received is None:
        time.sleep(0.1)

    return response_received


def handle_text_input(text, history):
    response = send_message(text, history)
    return history + [[text, response]], ""


# --- Image Send (Base64 over WebSocket) ---
def send_image(image_path, history):
    global response_received

    if not image_path:
        return history + [["[image]", "❌ No image provided."]], None

    if not sio.connected:
        connect_to_server()

    # Read image file and encode as base64
    with open(image_path, "rb") as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # Emit base64-encoded image
    response_received = None
    sio.emit(
        "trueinside-message",
        {"image": image_base64, "filename": os.path.basename(image_path)},
    )
    print("🖼️ Base64 image emitted")

    while response_received is None:
        time.sleep(1.0)

    return history + [["[image sent]", response_received]], None, None


# --- Gradio UI ---
with gr.Blocks() as answer_bot:
    gr.Markdown("## 🌿 TrueInside: Decode Your Personal Care Products")
    gr.Markdown(
        "_Instantly scan and understand cosmetic ingredients for safety, allergies, and ethical fit—no brand bias, just facts._"
    )

    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(
                submit_btn=True,
                placeholder="Type your message...",
                label="Your Message",
            )
            input_image = gr.Image(type="filepath", label="Upload an Image")
            send_image_btn = gr.Button("Send Image")
        with gr.Column():
            chatbot = gr.Chatbot()
    input_text.submit(
        fn=handle_text_input,
        inputs=[input_text, chatbot],
        outputs=[chatbot, input_text],
    )

    send_image_btn.click(
        fn=send_image,
        inputs=[input_image, chatbot],
        outputs=[chatbot, input_text, input_image],
    )


# --- Run Gradio ---
if __name__ == "__main__":
    print("🚀 Gradio Chatbot running on http://127.0.0.1:7860/")
    answer_bot.launch(share=True, debug=True)

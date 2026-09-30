import gradio as gr

def commentary(event):
    return f"📣 Commentary: {event}"

demo = gr.Interface(fn=commentary, inputs="text", outputs="text")
demo.launch(server_name="0.0.0.0", server_port=10000)

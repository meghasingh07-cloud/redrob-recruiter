import gradio as gr

def run_demo(file):
    return "Ranking system is running. Upload processed."

demo = gr.Interface(
    fn=run_demo,
    inputs=gr.File(label="Upload candidates.jsonl"),
    outputs="text",
    title="Redrob Recruiter Ranking Sandbox"
)

demo.launch()
import gradio as gr
import pandas as pd
import subprocess

def run_demo(file):
    subprocess.run(["python", "rank.py"])

    df = pd.read_csv("submission.csv")

    return df.head(10)

demo = gr.Interface(
    fn=run_demo,
    inputs=gr.File(label="Upload candidates.jsonl"),
    outputs=gr.Dataframe(label="Top 10 Ranked Candidates"),
    title="Redrob Recruiter Ranking Sandbox"
)

demo.launch()

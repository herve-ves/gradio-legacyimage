import numpy as np

import gradio as gr
from gradio_legacyimage import LegacyImage

def process(x):
    flip = x.copy()
    flip["back"] = np.fliplr(flip["back"])
    mask = x.copy()
    mask["back"] = mask["mask"]
    return x, flip, mask

with gr.Blocks() as demo:
    with gr.Column():
        im1 = LegacyImage(source="upload", type="pil", tool="sketch")
        im2 = LegacyImage()
        im3 = LegacyImage()
        im4 = LegacyImage()

    btn = gr.Button()
    btn.click(process, inputs=im1, outputs=[im2, im3, im4])

demo.launch()

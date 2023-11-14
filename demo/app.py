
import gradio as gr
from gradio_legacyimage import LegacyImage


example = LegacyImage().example_inputs()

demo = gr.Interface(
    lambda x:x,
    LegacyImage(),  # interactive version of your component
    LegacyImage(),  # static version of your component
    # examples=[[example]],  # uncomment this line to view the "example version" of your component
)


demo.launch()

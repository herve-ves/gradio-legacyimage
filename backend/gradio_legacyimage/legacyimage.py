"""gr.LegacyImage() component."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Literal, cast, Optional, Union, TypedDict

import numpy as np

import PIL
import PIL.ImageOps
from PIL import Image as _Image  # using _ to minimize namespace pollution

from gradio import processing_utils, utils
from gradio_client import utils as client_utils
from gradio_client.documentation import document, set_documentation_group
from gradio.components.base import Component, StreamingInput
from gradio.data_classes import GradioModel
from gradio.events import Events

import gradio.image_utils as image_utils

set_documentation_group("component")
_Image.init()  # fixes https://github.com/gradio-app/gradio/issues/2843

class PreprocessData(TypedDict):
    back: Optional[Union[np.ndarray, _Image.Image, str]]
    mask: Optional[Union[np.ndarray, _Image.Image, str]]

class ImageData(GradioModel):
    back: Optional[str] = None
    mask: Optional[str] = None

@document()
class LegacyImage(StreamingInput, Component):
    """
    Creates an image component that can be used to upload images (as an input) or display images (as an output).
    Preprocessing: passes the uploaded image as a {numpy.array}, {PIL.Image} or {str} filepath depending on `type`.
    Postprocessing: expects a {numpy.array}, {PIL.Image} or {str} or {pathlib.Path} filepath to an image and displays the image.
    Examples-format: a {str} local filepath or URL to an image.
    Demos: image_mod, image_mod_default_image
    Guides: image-classification-in-pytorch, image-classification-in-tensorflow, image-classification-with-vision-transformers, create-your-own-friends-with-a-gan
    """

    EVENTS = [
        Events.clear,
        Events.change,
        Events.stream,
        Events.select,
        Events.upload,
        Events.edit,
    ]

    data_model = ImageData

    def __init__(
        self,
        value: str | _Image.Image | np.ndarray | None = None,
        *,
        height: int | None = None,
        width: int | None = None,
        image_mode: Literal[
            "1", "L", "P", "RGB", "RGBA", "CMYK", "YCbCr", "LAB", "HSV", "I", "F"
        ] = "RGB",
        type: Literal["numpy", "pil", "filepath"] = "numpy",
        label: str | None = None,
        every: float | None = None,
        show_label: bool | None = None,
        show_download_button: bool = True,
        container: bool = True,
        scale: int | None = None,
        min_width: int = 160,
        interactive: bool | None = None,
        visible: bool = True,
        streaming: bool = False,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        render: bool = True,
        mirror_webcam: bool = True,
        show_share_button: bool | None = None,

        source: Literal["upload", "webcam", "canvas"] = "upload",
        invert_colors: bool = False,
        shape: tuple[int, int] | None = None,
        tool: Literal["editor", "select", "sketch", "color-sketch"] | None = None,
        brush_radius: float | None = None,
        brush_color: str = "#000000",
        mask_opacity: float = 0.7,
    ):
        """
        Parameters:
            value: A PIL LegacyImage, numpy array, path or URL for the default value that LegacyImage component is going to take. If callable, the function will be called whenever the app loads to set the initial value of the component.
            height: Height of the displayed image in pixels.
            width: Width of the displayed image in pixels.
            image_mode: "RGB" if color, or "L" if black and white. See https://pillow.readthedocs.io/en/stable/handbook/concepts.html for other supported image modes and their meaning.
            type: The format the image is converted to before being passed into the prediction function. "numpy" converts the image to a numpy array with shape (height, width, 3) and values from 0 to 255, "pil" converts the image to a PIL image object, "filepath" passes a str path to a temporary file containing the image.
            label: The label for this component. Appears above the component and is also used as the header if there are a table of examples for this component. If None and used in a `gr.Interface`, the label will be the name of the parameter this component is assigned to.
            every: If `value` is a callable, run the function 'every' number of seconds while the client connection is open. Has no effect otherwise. Queue must be enabled. The event can be accessed (e.g. to cancel it) via this component's .load_event attribute.
            show_label: if True, will display label.
            show_download_button: If True, will display button to download image.
            container: If True, will place the component in a container - providing some extra padding around the border.
            scale: relative width compared to adjacent Components in a Row. For example, if Component A has scale=2, and Component B has scale=1, A will be twice as wide as B. Should be an integer.
            min_width: minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.
            interactive: if True, will allow users to upload and edit an image; if False, can only be used to display images. If not provided, this is inferred based on whether the component is used as an input or output.
            visible: If False, component will be hidden.
            streaming: If True when used in a `live` interface, will automatically stream webcam feed. Only valid is source is 'webcam'.
            elem_id: An optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.
            elem_classes: An optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.
            render: If False, component will not render be rendered in the Blocks context. Should be used if the intention is to assign event listeners now but render the component later.
            mirror_webcam: If True webcam will be mirrored. Default is True.
            show_share_button: If True, will show a share icon in the corner of the component that allows user to share outputs to Hugging Face Spaces Discussions. If False, icon does not appear. If set to None (default behavior), then the icon appears if this Gradio app is launched on Spaces, but not otherwise.
        """
        self.mirror_webcam = mirror_webcam
        valid_types = ["numpy", "pil", "filepath"]
        if type not in valid_types:
            raise ValueError(
                f"Invalid value for parameter `type`: {type}. Please choose from one of: {valid_types}"
            )
        self.type = type
        self.height = height
        self.width = width
        self.image_mode = image_mode

        valid_sources = ["upload", "webcam", "canvas"]
        if source not in valid_sources:
            raise ValueError(
                f"Invalid value for parameter `source`: {source}. Please choose from one of: {valid_sources}"
            )

        self.streaming = streaming
        self.show_download_button = show_download_button
        if streaming and source != "webcam":
            raise ValueError("Image streaming only available if source is 'webcam'.")

        self.show_share_button = (
            (utils.get_space() is not None)
            if show_share_button is None
            else show_share_button
        )

        self.source = source
        if tool is None:
            self.tool = "sketch" if source == "canvas" else "editor"
        else:
            self.tool = tool
        self.invert_colors = invert_colors
        self.shape = shape
        self.brush_radius = brush_radius
        self.brush_color = brush_color
        self.mask_opacity = mask_opacity

        super().__init__(
            label=label,
            every=every,
            show_label=show_label,
            container=container,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            render=render,
            value=value,
        )

    def format_image(self, im: _Image.Image) -> np.ndarray | _Image.Image | str | None:
        return image_utils.format_image(
            im, cast(Literal["numpy", "pil", "filepath"], self.type), self.GRADIO_CACHE
        )

    def preprocess(self, x: ImageData) -> PreprocessData | None:
        if x is None:
            return x

        mask_im = None
        if self.tool == "sketch" and self.source in ["upload", "webcam"]:
            mask_im = processing_utils.decode_base64_to_image(x.mask) if x.mask is not None else None
        im = processing_utils.decode_base64_to_image(x.back)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            im = im.convert(self.image_mode)
        if self.shape is not None:
            im = processing_utils.resize_and_crop(im, self.shape)
        if self.invert_colors:
            im = PIL.ImageOps.invert(im)
        if (
            self.source == "webcam"
            and self.mirror_webcam is True
            and self.tool != "color-sketch"
        ):
            im = PIL.ImageOps.mirror(im)

        if self.tool == "sketch" and self.source in ["upload", "webcam"]:
            if mask_im.mode == "RGBA":  # whiten any opaque pixels in the mask
                alpha_data = mask_im.getchannel("A").convert("L")
                mask_im = _Image.merge("RGB", [alpha_data, alpha_data, alpha_data])
            return {
                "back": self.format_image(im),
                "mask": self.format_image(mask_im)
            }

        return {
            "back": self.format_image(im),
            "mask": None
        }

    def postprocess(self, y: PreprocessData | None) -> ImageData | None:
        if y is None:
            return None

        if isinstance(y["back"], np.ndarray):
            return ImageData(
                back=processing_utils.encode_array_to_base64(y["back"]),
                mask=None,
            )
        elif isinstance(y["back"], _Image.Image):
            return ImageData(
                back=processing_utils.encode_pil_to_base64(y["back"]),
                mask=None,
            )
        elif isinstance(y["back"], (str, Path)):
            return ImageData(
                back=client_utils.encode_url_or_file_to_base64(y["back"]),
                mask=None,
            )
        else:
            raise ValueError("Cannot process this value as an Image")

    def check_streamable(self):
        if self.streaming and self.sources != ["webcam"]:
            raise ValueError(
                "LegacyImage streaming only available if sources is ['webcam']. Streaming not supported with multiple sources."
            )

    def as_example(self, input_data: str | Path | None) -> str | None:
        if input_data is None:
            return None
        return processing_utils.move_resource_to_block_cache(input_data, self)

    def example_inputs(self) -> Any:
        return "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png"

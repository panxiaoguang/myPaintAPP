"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from PIL import Image
import io
import requests
import os 
from dotenv import load_dotenv
from reflex_image_zoom import image_zoom

model_dict = {
    "dreamshaper-8-lcm": "@cf/lykon/dreamshaper-8-lcm",
    "stable-diffusion-xlbase-1.0": "@cf/stabilityai/stable-diffusion-xl-base-1.0",
    "stable-diffusion-xl-lightning": "@cf/bytedance/stable-diffusion-xl-lightning"
}
load_dotenv()
if "CLOUDFLARE_API_TOKEN" in os.environ:
    api_token = os.environ["CLOUDFLARE_API_TOKEN"]
else:
    raise ValueError("Please set the CLOUDFLARE_API_TOKEN environment variable")
if "CLOUDFLARE_ACCOUNT_ID" in os.environ:
    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
else:
    raise ValueError("Please set the CLOUDFLARE_ACCOUNT_ID environment variable")


class Paint(rx.State):
    model: str = "stable-diffusion-xl-lightning"
    prompt: str = "A photo of a cat"
    CFG_scale: int = 7
    steps: int = 20
    response_image = Image.open("assets/default.png")
    show: bool = True

    async def getResponse(self):
        model_full = model_dict[self.model]
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_full}",
            headers={"Authorization": f"Bearer {api_token}"},
            json={"prompt": self.prompt,
                  "num_steps": self.steps,
                  "guidance": self.CFG_scale
                  }
        )
        return response

    async def paint(self):
        self.show = False
        yield
        response = await self.getResponse()
        if response.status_code == 200:
            self.response_image = Image.open(io.BytesIO(response.content))
        else:
            self.response_image = Image.open("assets/default.png")
        self.show = True


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.box(rx.heading("SD painting", size="5")),
            rx.flex(
                rx.text("Select a model"),
                rx.select(
                    ["dreamshaper-8-lcm",
                     "stable-diffusion-xlbase-1.0",
                     "stable-diffusion-xl-lightning"],
                    default_value=Paint.model,
                    on_change=Paint.set_model,
                ),
                spacing="2",
                align="center",
            ),
            rx.flex(
                rx.text("Your prompt:"),
                rx.box(
                    rx.text_area(placeholder="eg: A photo of a cat",
                                 size="3",
                                 rows="5",
                                 on_blur=Paint.set_prompt),
                    width="100%",
                ),
                direction="column",
                spacing="2",
                width="100%",
            ),
            rx.flex(
                rx.text("CFG_sclae:"),
                rx.chakra.number_input(
                    value=Paint.CFG_scale,
                    on_change=Paint.set_CFG_scale,
                ),
                rx.text("Steps:"),
                rx.chakra.number_input(
                    value=Paint.steps,
                    on_change=Paint.set_steps,
                ),
                rx.button(rx.icon(tag="dna"),
                          "Generate",
                          size="3",
                          color_scheme="iris",
                          radius="medium",
                          _hover={"cursor": "pointer"},
                          on_click=Paint.paint,
                          ),
                spacing="2",
                width="100%",
                align="center",
            ),
            rx.flex(rx.divider(size="2", width="100%"),
                    class_name="my-5",
                    width="100%",
                    ),
            rx.box(
                rx.text("Generated Image:"),
                rx.card(
                    rx.cond(
                        Paint.show,
                        image_zoom(rx.image(src=Paint.response_image,
                                 alt="Generated Image")),
                        rx.box(
                            rx.chakra.spinner(color="grey", size="sm"),
                            width="100%",
                            height="400px"
                        ),
                    ),
                    variant="classic",
                    width="50%",
                    class_name="mx-auto",
                ),
                width="100%",
                height="50%",

            ),
            class_name="mt-5 border-2 border-gray-300 p-5 rounded-md",
        ),
        class_name="mt-5",
    )


app = rx.App()
app.add_page(index,title="SD painting",
             description="A simple app to generate images using Stable Diffusion models")

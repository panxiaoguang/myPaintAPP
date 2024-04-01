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


class Paint(rx.State):
    model: str = "stable-diffusion-xl-lightning"
    prompt: str = "A photo of a cat"
    CFG_scale: int = 7
    steps: int = 15
    response_image = Image.open("assets/default.png")
    account_id: str = ""
    api_token: str = ""
    show: bool = True
    show_info: bool = False

    def get_api_token(self):
        load_dotenv()
        if "CLOUDFLARE_API_TOKEN" in os.environ:
            self.api_token = os.environ["CLOUDFLARE_API_TOKEN"]
        else:
            self.show_info = True
        if "CLOUDFLARE_ACCOUNT_ID" in os.environ:
            self.account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
        else:
            self.show_info = True

    def set_keys(self, form_data: dict):
        self.account_id = form_data['AccountID']
        self.api_token = form_data['APIToken']
        if self.account_id != "" and self.api_token != "":
            self.show_info = False
        else:
            self.show_info = True

    def make_CFG_scale(self, value: str):
        try:
            self.CFG_scale = int(value)
        except ValueError:
            print(f"{value} was not parsable as an int, ignored")

    def make_steps(self, value: str):
        try:
            self.steps = int(value)
        except ValueError:
            print(f"{value} was not parsable as an int, ignored")

    async def getResponse(self):
        model_full = model_dict[self.model]
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{model_full}",
            headers={"Authorization": f"Bearer {self.api_token}"},
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
        rx.box(
            rx.flex(
                rx.cond(
                    Paint.show_info,
                    rx.callout(
                        "Please set your AccountID and API Token",
                        icon="alert_triangle",
                        color_scheme="red",
                        role="alert"),
                ),
            ),
            rx.flex(
                rx.heading("SD painting", size="5"),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.button(rx.icon(tag="settings"),
                                  variant="ghost",
                                  color_scheme="gray")),
                    rx.dialog.content(
                        rx.dialog.title("Setting Your Keys"),
                        rx.form(
                            rx.flex(
                                rx.text("AccountID",
                                        as_="div",
                                        size="2",
                                        margin_bottom="4px",
                                        weight="bold",),
                                rx.input(placeholder="Enter your AccountID",
                                         name="AccountID",),
                                rx.text("API Token",
                                        as_="div",
                                        size="2",
                                        margin_bottom="4px",
                                        weight="bold",),
                                rx.input(placeholder="Enter your API Token",
                                         name="APIToken",),
                                direction="column",
                                spacing="3",
                            ),
                            rx.flex(
                                rx.dialog.close(
                                    rx.button("Cancel",
                                              color_scheme="gray",
                                              variant="soft",
                                              ),
                                ),
                                rx.dialog.close(
                                    rx.button("Save",
                                              type="submit"),
                                ),
                                spacing="3",
                                margin_top="16px",
                                justify="end",
                            ),
                            on_submit=Paint.set_keys,
                            reset_on_submit=True,
                        ))),
                align="center",
                justify="between",
            ),
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
                rx.input(
                    type="number",
                    value=Paint.CFG_scale.to_string(),
                    on_change=lambda value: Paint.make_CFG_scale(value),
                ),
                rx.text("Steps:"),
                rx.input(
                    type="number",
                    value=Paint.steps.to_string(),
                    on_change=lambda value: Paint.make_steps(value),
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
app.add_page(index,
             on_load=Paint.get_api_token,
             title="SD painting",
             description="A simple app to generate images using Stable Diffusion models")

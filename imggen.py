from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os

def generate(name="", note="", unit=""):

    client = genai.Client(api_key="AIzaSyCqXm4HPdWlQZNtNWrv_80ThOtKnNMuqYs")

    contents = f"create a realistic image of item name:{name}, note:{note}, unit of items:{unit} in white background, ratio - 1:1"

    # contents = "i need a news card to post on my facebook news channel, its special for cinema news, so generate an atractive light theme news card, news card contain a image (regarding the news) more over logo of my channel, title of the news "

    name = name.replace(" ", "_")
    name = name.replace("/", "")
    name = name.replace('"', "")
    name = name.replace("'", "")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=contents,
            config=types.GenerateContentConfig(
              response_modalities=['TEXT', 'IMAGE']
            )
        )
    except:
        return None
    # print("response:", response)

    image_path = f"src/{name}.jpg"
    n = 0

    for part in response.candidates[0].content.parts:
      if part.inline_data is not None:
        image = Image.open(BytesIO((part.inline_data.data)))
        # Check if the file exists before attempting to delete it (optional but recommended)
        while os.path.exists(image_path):
            # try:
            os.remove(image_path)
            print(f"Image '{image_path}' deleted successfully.")
            # except OSError as e:
            #     print(f"Error deleting image '{image_path}': {e}")
            image_path = f"src/{name}{n}.jpg"
            print(image_path)
            n += 1

        image.save(image_path)
    # except:
    #     return 0
        # image.show()
    # else:
    return image_path

# generate()
from openai import OpenAI
import base64
import json
from PIL import Image
from io import BytesIO

def encode_image(image: Image.Image) -> str:
    buffered = BytesIO()
    
    image.save(buffered, format="PNG")
    buffered.seek(0) 
    
    # Read the image data and encode it to base64
    return base64.b64encode(buffered.read()).decode('utf-8')

def readBalanceSheet(image, model:OpenAI, metadata):
    base64_image = encode_image(image)
    year = metadata['year']
    response = model.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            },
            },
            {"type": "text", 
            "text": """
            Extract all the information in this image, return the result of the below year.
            Return only Json format, no further explanation, Json must be flat format not nested.
            Return the account names in English. Specify positive and negative numbers. 
            Do not use decimal number and do not add any comma or dot into the amount.
            For example:
            Ví dụ:
            {
                "Cash and gold": amount,
                "Deposits at the State Bank": amount,
                "Deposits at and loans to other credit institutions": amount,
                "Deposits at other credit institutions": amount,
                "Loans to other credit institutions": amount,
                "Provision for deposits at and loans to other credit institutions": amount,
                "Trading securities": amount,
                ...
            }
            The year is   
            """ + str(year)},
        ],
        }
    ],
    stream = False,
    response_format = { "type": "json_object" },
    max_tokens = 2048,
    )

    # for chunk in response:
    #     if chunk.choices[0].delta.content is not None:
    #         print(chunk.choices[0].delta.content, end="")
    res = response.choices[0].message.content
    res = res.replace("json","")
    res = res.replace("```","")
    res = json.loads(res)

    return res

def readIncome(image, model:OpenAI, metadata):
    base64_image = encode_image(image)
    year = metadata['year']
    response = model.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            },
            },
            {"type": "text", 
            "text": """
            Extract all the information in this image, return the result of the most recent day/year.
            Return only Json format, no further explanation, Json must be flat format not nested.
            Return the account names in English. Specify positive and negative numbers. 
            Do not use decimal number and do not add any comma or dot into the amount.
            For example:
            {
            "Interest and similar income": amount,
            "Interest and similar expenses": amount,
            "Net interest income": amount,
            "Net fee and commission income": amount,
            "Net gain/(loss) from trading foreign currencies": amount,
            "Net gain from securities trading": amount,
            "Income from other activities": amount,
            ...
            Extract all accounts
            }  
            The year is 
            """ + str(year)},
        ],
        }
    ],
    stream = False,
    response_format = { "type": "json_object" },
    max_tokens = 2048,
    )

    # for chunk in response:
    #     if chunk.choices[0].delta.content is not None:
    #         print(chunk.choices[0].delta.content, end="")
    res = response.choices[0].message.content
    res = res.replace("json","")
    res = res.replace("```","")
    res = json.loads(res)

    return res

def readCashFlow(image, model:OpenAI, metadata):
    base64_image = encode_image(image)
    year = metadata['year']
    response = model.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            },
            },
            {"type": "text", 
            "text": """
            Extract all the information in this image, return the result of the below year.
            Return only Json format, no further explanation, Json must be flat format not nested.
            Return the account names in English. Specify positive and negative numbers. 
            Do not use decimal number and do not add any comma or dot into the amount.
            For example:
            {
            "Cash flow from operating activities" : amount,
            "Cash flow from investing activities" : amount,
            "Cash flow from financing activities": amount
            ...
            Extract all information
            }
            The year is 
            """+str(year)},
        ],
        }
    ],
    stream = False,
    response_format = { "type": "json_object" },
    max_tokens = 2048,
    )

    # for chunk in response:
    #     if chunk.choices[0].delta.content is not None:
    #         print(chunk.choices[0].delta.content, end="")
    res = response.choices[0].message.content
    res = res.replace("json","")
    res = res.replace("```","")
    res = json.loads(res)

    return res

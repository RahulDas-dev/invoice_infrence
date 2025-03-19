import sys

sys.path.append("src")

import boto3
from dotenv import load_dotenv

from src.core import get_secret_keys

load_dotenv()

SYSTEM_MESSAGE_1 = """Your primary task is to extract invoice details from an image.
The extracted details should include the following information. If any detail is not present, use the reserved keyword "NOT_AVAILABLE":

1. Invoice Number
2. Invoice Date
3. Seller Details (Company Name, Address, Phone Number, Email) [if present]
4. Buyer Details (Company Name, Address, Phone Number, Email) [if present]
5. Item Details (sl.no, Description, Quantity, Price) [If multiple items are present, capture all of them]
6. Total Tax (CGST, IGST, SGST) [if present]
7. Total Charges [if present]
8. Total Discount [if present]
9. Total Amount
10. Amount Paid [if present]
11. Amount Due [if present]

If the document is not an invoice, return the reserved keyword "NO_INVOICE"

Here is One Example Response format --

```
1. Invoice Number: 1118212440009383
2. Invoice Date: 21-MAR-2022
3. Seller Details:
   - Company Name: VRRDDHI FREIGHT PVT LTD
   - Address: 28 A 116, Egato Trade Centre, New No. 318, Poonamallee High Road, Kilpauk, Chennai - 600 010, Tamil Nadu
   - Phone Number: +91 44 25003622
   - Email: seller@abc.co.in
4. Buyer Details:
   - Company Name: SUNDARAM CLAYTON LIMITED
   - Address: PADI CHENNAI - 600050
   - Phone Number: NOT_AVAILABLE
   - Email: NOT_AVAILABLE
5. Item Details:
   - 1. Description: FREIGHT CHARGE, Quantity: 1.000, Price: 8700.00
   - 2. Description: DESTINATION CHARGES, Quantity: 1.000, Price: 1600.00
   - 3. Description: ORIGIN LOCAL CHARGES, Quantity: 1.000, Price: 4702.00
   - 4. Description: FUMIGATION CHARGES, Quantity: 1.000, Price: 3500.00
6. Total Tax:
   - CGST: 0.00
   - SGST: 0.00
   - IGST: 0.00
7. Total Charges: NOT_AVAILABLE
8. Total Discount: NOT_AVAILABLE
9. Total Amount: 889397.00
10. Amount Paid: NOT_AVAILABLE
11. Amount Due: NOT_AVAILABLE
```
"""


### Bedrock Model boto3 client


MODEL_ID = "us.meta.llama3-2-90b-instruct-v1:0"

runtime = boto3.client("bedrock-runtime", **get_secret_keys())

image_name = "C:/Users/rdas6/OneDrive/Desktop/codespace/vyturr/temp/img/Invoice-Copy-12/Page_01.png"

with open(image_name, "rb") as f:
    image = f.read()

messages = [
    {
        "role": "user",
        "content": [
            {"image": {"format": "png", "source": {"bytes": image}}},
            {"text": SYSTEM_MESSAGE_1},
        ],
    },
]

response = runtime.converse(modelId=MODEL_ID, messages=messages)

response_text = response["output"]["message"]["content"][0]["text"]

print(response_text)

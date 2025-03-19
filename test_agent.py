import sys

sys.path.append("src")
import io
import logging
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image
from pydantic import BaseModel, Field, PositiveInt
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.bedrock import BedrockProvider

from src.core import get_secret_keys

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

SYSTEM_MESSAGE = """Your primary task is to extract invoice details from an image.
The extracted details should include the following information. If any detail is not present, use the reserved keyword "NOT_AVAILABLE":

1. Invoice Number
2. Invoice Date
3. Seller Details (Name, Address, Phone Number, Email) [if present]
4. Buyer Details (Name, Address, Phone Number, Email) [if present]
5. Item Details (sl.no, Description, Quantity, Price , Crrrency ) [If multiple items are present, capture all of them]
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
   - Name: VRRDDHI FREIGHT PVT LTD
   - Address: 28 A 116, Egato Trade Centre, New No. 318, Poonamallee High Road, Kilpauk, Chennai - 600 010, Tamil Nadu
   - Phone Number: +91 44 25003622
   - Email: seller@abc.co.in
4. Buyer Details:
   - Name: SUNDARAM CLAYTON LIMITED
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

USER_MESSAGE = "Please extract the invoice details from the image."


class Item(BaseModel):
    """
    Structured model for summarizing item details in the invoice.
    """

    slno: PositiveInt
    description: str = Field(default="Not Available", description="Description of the item")
    quantity: str = Field(default="Not Available", description="Quantity of the item")
    price: str = Field(default="Not Available", description="Price of the item")
    currency: str = Field(default="INR", description="Currency of the price")


class CompanyDetails(BaseModel):
    """
    Structured model for summarizing company details.
    """

    name: str = Field(default="Not Available", description="Name of the company")
    address: str = Field(default="Not Available", description="Address of the company")
    phone_number: str = Field(default="Not Available", description="Phone number of the company")
    email: str = Field(default="Not Available", description="Email of the company")


class TaxComponents(BaseModel):
    """
    Structured model for summarizing tax components.
    """

    CGST: float = Field(default=0.0, description="Central Goods and Services Tax")
    SGST: float = Field(default=0.0, description="State Goods and Services Tax")
    IGST: float = Field(default=0.0, description="Integrated Goods and Services Tax")


class Invoice(BaseModel):
    """
    Structured model for summarizing invoice details.
    """

    invoice_number: str = Field(description="Invoice number")
    invoice_date: str = Field(default="Not Available", description="Invoice date")
    seller_details: CompanyDetails = Field(
        default_factory=lambda: CompanyDetails(), description="Details of the seller"
    )
    buyer_details: CompanyDetails = Field(default_factory=lambda: CompanyDetails(), description="Details of the buyer")
    items: list[Item] = Field(default_factory=list, description="List of items in the invoice")
    total_tax: TaxComponents = Field(default_factory=lambda: TaxComponents(), description="Total tax components")
    total_charge: float = Field(default=0.0, description="Total charges")
    total_discount: float = Field(default=0.0, description="Total discount applied")
    total_amount: float = Field(default=0.0, description="Total amount of the invoice")
    amount_paid: float = Field(default=0.0, description="Amount paid")
    amount_due: float = Field(default=0.0, description="Amount due")


model = OpenAIModel("gpt-4o")


MODEL_ID = "us.meta.llama3-2-90b-instruct-v1:0"


model1 = BedrockConverseModel(
    model_name=MODEL_ID,
    provider=BedrockProvider(**get_secret_keys()),
)


agent = Agent(
    model=model1,
    system_prompt=SYSTEM_MESSAGE,
    result_type=str,
    model_settings={"temperature": 0},
)


def image_to_byte_string(image_path: str | Path) -> tuple[bytes, str]:
    image = Image.open(image_path)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")  # or 'JPEG', etc.
    img_byte_arr = img_byte_arr.getvalue()
    # image_base64 = base64.b64encode(img_byte_arr).decode("utf-8")
    # return f"data:{image.get_format_mimetype()};base64,{image_base64}"
    return img_byte_arr, image.get_format_mimetype() or "image/png"


image_name = "C:/Users/rdas6/OneDrive/Desktop/codespace/vyturr/temp/img/Deep_Learning_Spealization/Page_01.png"
img_byte, mimetype = image_to_byte_string(image_name)

input_msg = [
    USER_MESSAGE,
    # ImageUrl(img_url),
    BinaryContent(data=img_byte, media_type="image/png"),
]
result = agent.run_sync(input_msg)  # type: ignore

print(result.data)

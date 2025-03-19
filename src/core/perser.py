import re
import xml.etree.ElementTree as ET
from typing import Optional


def clean_xml(xml_data: str) -> str:
    """Clean extracted XML by removing invalid characters and fixing formats."""
    # Replace commas in numbers (e.g., "12,29,681" -> "1229681")
    xml_data = re.sub(r"(\d),(\d)", r"\1\2", xml_data)

    # Ensure valid XML entities (replace & with &amp; if not already an entity)
    return xml_data.replace("&", "&amp;")


def extract_xml_from_text(raw_text: Optional[str]) -> Optional[str]:
    """Extract XML content within <Invoice> tags from raw text."""
    if raw_text is None:
        return None
    xml_pattern = r"<Invoice>.*?</Invoice>"
    match = re.search(xml_pattern, raw_text, re.DOTALL)
    return match.group(0) if match else None


def parse_invoice(xml_data: Optional[str]) -> dict:
    """Parse extracted XML and extract invoice details."""
    # xml_data = xml_data.encode("utf-8")
    # xml_data = xml_data.decode("utf-8")
    if xml_data is None:
        return {}
    cleaned_xml = clean_xml(xml_data)
    root = ET.fromstring(cleaned_xml)

    invoice_details = {
        "invoice_number": root.findtext("InvoiceNumber", None),
        "invoice_date": root.findtext("InvoiceDate", None),
        "seller_name": root.findtext("SellerName", None),
        "buyer_name": root.findtext("BuyerName", None),
        "items": [],
        "total_amount": root.findtext("TotalAmount", None),
    }

    items = root.find("Items")
    if items:
        for item in items.findall("Item"):
            invoice_details["items"].append(
                {
                    "price": item.findtext("Price", None),
                    "quantity": item.findtext("Quantity", None),
                    "description": item.findtext("Description", None),
                }
            )

    return invoice_details


def process_invoice(raw_text: str) -> dict:
    """Process full text to extract invoice data and additional details."""
    xml_data = extract_xml_from_text(raw_text)
    if xml_data is None or xml_data.lower() == "no_invoice":
        return {}
    return parse_invoice(xml_data)


# Example usage:
raw_invoice_text = """
Transaction ID: TXN-98765
Payment Method: Credit Card
Customer Email: customer@example.com
<Invoice>
    <InvoiceNumber>SLNPN08/23-24</InvoiceNumber>
    <InvoiceDate>17-08-2023</InvoiceDate>
    <SellerName>SITICS LOGISTIC SOLUTIONS PVT. LTD</SellerName>
    <BuyerName>NIPPON PAINT (INDIA) PRIVATE LIMITED</BuyerName>
    <Items>
        <Item>
            <Price>12,29,681</Price>
            <Quantity>1</Quantity>
            <Description>Goods Transport Agency Services for Road Transport</Description>
        </Item>
    </Items>
    <TotalAmount>12,29,681</TotalAmount>
</Invoice>
Some random text outside the invoice block.
"""

if __name__ == "__main__":
    result = process_invoice(raw_invoice_text)
    print(result)

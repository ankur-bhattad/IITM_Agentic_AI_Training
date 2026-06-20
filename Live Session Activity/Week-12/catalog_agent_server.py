
import os
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.models.google_llm import Gemini
from google.genai import types

# Retry policy for transient HTTP failures
http_retry_policy = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

def fetch_product_details(item_name: str) -> str:
    """Return catalog details for a requested product."""
    inventory_snapshot = {
        "iphone 15 pro": "iPhone 15 Pro, $999, Low Stock (8 units), 128GB, Titanium finish",
        "samsung galaxy s24": "Samsung Galaxy S24, $799, In Stock (31 units), 256GB, Phantom Black",
        "dell xps 15": "Dell XPS 15, $1,299, In Stock (45 units), 15.6\" display, 16GB RAM, 512GB SSD",
        "macbook pro 14": "MacBook Pro 14\", $1,999, In Stock (22 units), M3 Pro chip, 18GB RAM, 512GB SSD",
        "sony wh-1000xm5": "Sony WH-1000XM5 Headphones, $399, In Stock (67 units), Noise-canceling, 30hr battery",
        "ipad air": "iPad Air, $599, In Stock (28 units), 10.9\" display, 64GB",
        "lg ultrawide 34": "LG UltraWide 34\" Monitor, $499, Out of Stock, Expected: Next week",
    }

    key = item_name.strip().lower()

    if key in inventory_snapshot:
        return f"Product Details: {inventory_snapshot[key]}"

    supported_items = ", ".join(name.title() for name in inventory_snapshot.keys())
    return (
        f"Details for '{item_name}' are unavailable. "
        f"Supported products include: {supported_items}"
    )

catalog_agent = LlmAgent(
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=http_retry_policy
    ),
    name="catalog_lookup_agent",
    description=(
        "An external-facing agent that supplies pricing, "
        "availability, and specifications from a vendor catalog."
    ),
    instruction="""
    You represent an external vendor's product information desk.
    For any product-related inquiry, use the fetch_product_details tool
    to retrieve catalog data.
    Ensure responses clearly include pricing, stock status, and specifications.
    When multiple products are mentioned, address each independently.
    Maintain a professional and helpful tone.
    """,
    tools=[fetch_product_details],
)

# Expose the agent using the A2A protocol
app = to_a2a(catalog_agent, port=8001)

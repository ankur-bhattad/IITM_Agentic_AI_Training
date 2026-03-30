# ---------------------------------------------
# Hands-on Exercise: Calling a Public API and Processing JSON in Python
# ---------------------------------------------

# Step 1: Import necessary libraries
# 'requests' is used to send HTTP requests and receive responses
# 'json' module is built-in and helps in parsing JSON data (not mandatory here since .json() does it)
import requests
import json


# ---------------------------------------------
# Step 2: Call a Public API (FakeStore API Example)
# ---------------------------------------------

# Define the API endpoint URL
url = "https://fakestoreapi.com/products"

# Make a GET request to the API
response = requests.get(url)

# Check the response status code (200 means 'OK')
print("Status Code:", response.status_code)

# Convert the response to JSON (Python dictionary/list)
data = response.json()

# Print the raw JSON (uncomment next line if you want to see full data)
# print(json.dumps(data, indent=4))  # Pretty print JSON


# ---------------------------------------------
# Step 3: Process the JSON Response
# ---------------------------------------------

# Let's process only the first 5 products for clarity
print("\n--- Displaying First 5 Products ---")
for product in data[:5]:
    print("Title:", product["title"])
    print("Price: $", product["price"])
    print("Category:", product["category"])
    print("-" * 40)

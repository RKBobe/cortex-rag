from google import genai

client = genai.Client(api_key="AIzaSyB7saOilqwYJypShWgcMFCQTmmoXaFRtLs")

print("Listing available models...")
for model in client.models.list():
    print(model.name)
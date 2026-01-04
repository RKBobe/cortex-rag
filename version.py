from google import genai

client = genai.Client(api_key="AIzaSyC_yRPSrWPKENsz_dIM8c3tyFqv9kZrPpI")

print("Listing available models...")
for model in client.models.list():
    print(model.name)
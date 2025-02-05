from google.cloud import language_v1
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "nlp_key.json"

client = language_v1.LanguageServiceClient()
text = "Wow. What a travesty this is"
document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
sentiment = client.analyze_sentiment(request={"document": document}).document_sentiment

print(f"Sentiment Score: {sentiment.score}, Magnitude: {sentiment.magnitude}")

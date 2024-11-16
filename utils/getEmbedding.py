from openai import OpenAI
def get_embedding(texts, model="text-embedding-3-small", client: OpenAI = None):
   texts =[text.replace("\n", " ") for text in texts]
   return client.embeddings.create(input = texts, model=model).data
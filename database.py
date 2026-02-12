import psycopg2
from sentence_transformers import SentenceTransformer

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="pass",
    host="localhost",
    port="5432"
)

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text):
    return model.encode(text).tolist()

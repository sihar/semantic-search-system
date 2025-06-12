import psycopg2
from sentence_transformers import SentenceTransformer

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dimensions

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="scraper",
    user="postgres",
    password="123456",
    host="127.0.0.1",
    port=5436
)
cur = conn.cursor()

# 1. Create extension + table
cur.execute("""
    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE IF NOT EXISTS talent_profiles_semantic (
        id SERIAL PRIMARY KEY,
        name TEXT,
        skills TEXT,
        bio TEXT,
        embedding vector(384)
    );
""")
conn.commit()

# 2. Sample data to insert
profiles = [
    ("Alice", "Python, Django", "Senior backend engineer with 5 years of experience in Python."),
    ("Bob", "React, Node.js", "Frontend developer experienced with modern JavaScript and APIs."),
    ("Carol", "Machine Learning, Python", "Data scientist passionate about machine learning and data pipelines.")
]

# 3. Insert data with embeddings
for name, skills, bio in profiles:
    full_text = f"{name}. Skills: {skills}. Bio: {bio}"
    embedding = model.encode(full_text).tolist()
    cur.execute("""
        INSERT INTO talent_profiles_semantic (name, skills, bio, embedding)
        VALUES (%s, %s, %s, %s)
    """, (name, skills, bio, embedding))

conn.commit()

# 4. Search function
def semantic_search(query, top_k=3):
    embedding = model.encode(query).tolist()

    cur.execute("""
        SELECT id, name, skills, bio
        FROM talent_profiles_semantic
        ORDER BY embedding <#> %s::vector
        LIMIT %s
    """, (embedding, top_k))

    results = cur.fetchall()
    print(f"\n🔍 Top {top_k} results for: \"{query}\"\n")
    for r in results:
        print(f"✅ {r[1]} — Skills: {r[2]}\n    {r[3]}\n")

# 5. Run a test query
semantic_search("Looking for a Python backend developer")

# Close connection
cur.close()
conn.close()

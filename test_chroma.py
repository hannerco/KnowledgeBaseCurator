import chromadb

try:
    client = chromadb.HttpClient(
        host="api.trychroma.com",
        port=443,
        ssl=True,
        headers={"x-chroma-token": "ck-EX3dSDHpKUcU3sN5p7tbMXBgLDsJwH9TtkhR93DZ2irJ"},
        tenant="cc8c705a-8238-4756-a14b-fd383d8ecc9f",
        database="integrador3",
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")

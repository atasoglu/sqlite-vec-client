"""Example demonstrating logging configuration in sqlite-vec-client."""

import logging
import os

from sqlite_vec_client import SQLiteVecClient, get_logger

# Example 1: Enable DEBUG logging via environment variable
os.environ["SQLITE_VEC_CLIENT_LOG_LEVEL"] = "DEBUG"

# Reload logger to pick up new level
logger = get_logger()
logger.setLevel(logging.DEBUG)

print("=== Example 1: DEBUG logging ===\n")

client = SQLiteVecClient(table="docs", db_path=":memory:")
client.create_table(dim=3, distance="cosine")

texts = ["hello", "world"]
embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
rowids = client.add(texts=texts, embeddings=embeddings)

results = client.similarity_search(embedding=[0.1, 0.2, 0.3], top_k=2)
client.close()

print("\n=== Example 2: INFO logging ===\n")

# Change to INFO level
os.environ["SQLITE_VEC_CLIENT_LOG_LEVEL"] = "INFO"
logger.setLevel(logging.INFO)

client2 = SQLiteVecClient(table="articles", db_path=":memory:")
client2.create_table(dim=3)
client2.add(texts=["test"], embeddings=[[0.1, 0.2, 0.3]])
client2.close()

print("\n=== Example 3: WARNING logging (default) ===\n")

# Default level (WARNING) - minimal output
os.environ["SQLITE_VEC_CLIENT_LOG_LEVEL"] = "WARNING"
logger.setLevel(logging.WARNING)

client3 = SQLiteVecClient(table="items", db_path=":memory:")
client3.create_table(dim=3)
client3.add(texts=["silent"], embeddings=[[0.1, 0.2, 0.3]])
client3.close()

print("Done! (No logs shown at WARNING level for normal operations)")

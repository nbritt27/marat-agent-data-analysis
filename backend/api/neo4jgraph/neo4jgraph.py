#Included for later feature

import os
from langchain_community.graphs import Neo4jGraph


url = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")


NEO4J_AUTH = (
    username,
    password
)


graph = Neo4jGraph(
    url=url,
    username=username,
    password=password,
)
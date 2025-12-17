"""
Le Pont de Londres - Exemple complet d'implémentation

Ce script illustre le pattern d'intégration entre un graphe de domaine (CSV)
et un graphe lexical (extraction LLM depuis PDFs).
"""

import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
import csv

from neo4j import GraphDatabase
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter

# =============================================================================
# CONNEXION NEO4J
# =============================================================================

neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)
neo4j_driver.verify_connectivity()

# =============================================================================
# ÉTAPE 1 : SPÉCIFICATION DU SCHÉMA DU GRAPHE LEXICAL
# =============================================================================

# Types de nœuds - certains simples, d'autres enrichis
NODE_TYPES = [
    "Technology",
    "Concept",
    "Example",
    "Process",
    "Challenge",
    {"label": "Benefit", "description": "A benefit or advantage of using a technology or approach."},
    {
        "label": "Resource",
        "description": "A related learning resource such as a book, article, video, or course.",
        "properties": [
            {"name": "name", "type": "STRING", "required": True}, 
            {"name": "type", "type": "STRING"}
        ]
    },
]

# Types de relations
RELATIONSHIP_TYPES = [
    "RELATED_TO",
    "PART_OF",
    "USED_IN",
    "LEADS_TO",
    "HAS_CHALLENGE",
    "CITES"
]

# Patterns - contraintes sur les triplets valides
PATTERNS = [
    ("Technology", "RELATED_TO", "Technology"),
    ("Concept", "RELATED_TO", "Technology"),
    ("Example", "USED_IN", "Technology"),
    ("Process", "PART_OF", "Technology"),
    ("Technology", "HAS_CHALLENGE", "Challenge"),
    ("Concept", "HAS_CHALLENGE", "Challenge"),
    ("Technology", "LEADS_TO", "Benefit"),
    ("Process", "LEADS_TO", "Benefit"),
    ("Resource", "CITES", "Technology"),
]

# =============================================================================
# ÉTAPE 2 : CONFIGURATION DU PIPELINE D'EXTRACTION
# =============================================================================

llm = OpenAILLM(
    model_name="gpt-4o",
    model_params={
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
)

embedder = OpenAIEmbeddings(model="text-embedding-ada-002")

text_splitter = FixedSizeSplitter(chunk_size=500, chunk_overlap=100)

kg_builder = SimpleKGPipeline(
    llm=llm,
    driver=neo4j_driver, 
    neo4j_database=os.getenv("NEO4J_DATABASE"), 
    embedder=embedder, 
    from_pdf=True,
    text_splitter=text_splitter,
    schema={
        "node_types": NODE_TYPES,
        "relationship_types": RELATIONSHIP_TYPES,
        "patterns": PATTERNS
    },
)

# =============================================================================
# ÉTAPE 3 : TRANSFORMATION DU CSV EN DICTIONNAIRES
# =============================================================================

data_path = "./data/"

docs_csv = csv.DictReader(
    open(os.path.join(data_path, "docs.csv"), encoding="utf8", newline='')
)

# =============================================================================
# ÉTAPE 5 : REQUÊTE CYPHER DE JOINTURE
# =============================================================================

cypher = """
MATCH (d:Document {path: $pdf_path})
MERGE (l:Lesson {url: $url})
SET l.name = $lesson,
    l.module = $module,
    l.course = $course
MERGE (d)-[:PDF_OF]->(l)
"""

# =============================================================================
# BOUCLE PRINCIPALE
# =============================================================================

for doc in docs_csv:

    # ÉTAPE 4 : Ajout de la clé commune au dictionnaire
    doc["pdf_path"] = os.path.join(data_path, doc["filename"])
    print(f"Processing document: {doc['pdf_path']}")

    # Génération du graphe lexical (crée Document avec path)
    result = asyncio.run(
        kg_builder.run_async(file_path=doc["pdf_path"])
    )

    # Jointure avec le graphe de domaine
    records, summary, keys = neo4j_driver.execute_query(
        cypher,
        parameters_=doc,
        database_=os.getenv("NEO4J_DATABASE")
    )
    print(result, summary.counters)

# =============================================================================
# VÉRIFICATION DU PONT
# =============================================================================

# Vérifier les documents orphelins
orphans_query = """
MATCH (d:Document)
WHERE NOT EXISTS { (d)-[:PDF_OF]->(:Lesson) }
RETURN d.path AS orphan
"""

records, _, _ = neo4j_driver.execute_query(
    orphans_query,
    database_=os.getenv("NEO4J_DATABASE")
)

if records:
    print("⚠️  Documents orphelins détectés (pont cassé) :")
    for record in records:
        print(f"   - {record['orphan']}")
else:
    print("✅ Tous les documents sont rattachés au graphe de domaine")

neo4j_driver.close()

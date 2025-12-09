from query_interpreter import QueryInterpreter
import json

nlp = QueryInterpreter()
# Force anchor date for consistent testing if needed, but the class should load it.
print(f"Anchor Date: {nlp.anchor_date}")

queries = [
    "Adidas last month",
    "Adidas 30 days",
    "Adidas last 30 days",
    "Adidas for last 7 days",
    "Adidas last week"
]

for q in queries:
    res = nlp.interpret(q)
    print(f"Query: '{q}'")
    print(f"Parsed Date Range: {res['parsed_query']['date_range']}")
    print("-" * 20)

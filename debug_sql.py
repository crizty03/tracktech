from query_interpreter import QueryInterpreter
import json

nlp = QueryInterpreter()

queries = ["adidas", "puma", "Give me last week production summary"]

print(f"Anchor Date: {nlp.anchor_date}")
print(f"Loaded Filters: {list(nlp.filters.keys())}")

for q in queries:
    print(f"\nQuery: '{q}'")
    res = nlp.interpret(q)
    print(f"SQL: {res['sql']}")
    print(f"Params: {res['params']}")
    print(f"Parsed Context: {res['parsed_query']}")

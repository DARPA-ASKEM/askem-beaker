import requests
import json
import os

# Fetch the Swagger spec
url = f"{os.environ['HMI_SERVER_URL']}/v3/api-docs"
response = requests.get(url)
swagger_spec = response.json()

# Extract ModelConfiguration schema and its references
def get_related_definitions(schema, definitions, seen):
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            if ref_name not in seen:
                seen[ref_name] = definitions[ref_name]
                get_related_definitions(definitions[ref_name], definitions, seen)
        for value in schema.values():
            if isinstance(value, (dict, list)):
                get_related_definitions(value, definitions, seen)
    elif isinstance(schema, list):
        for item in schema:
            if isinstance(item, (dict, list)):
                get_related_definitions(item, definitions, seen)

definitions = swagger_spec["components"]["schemas"]
model_configuration_schema = definitions["ModelConfiguration"]

# Dictionary to store all related definitions
schema = {"ModelConfiguration": model_configuration_schema}
get_related_definitions(model_configuration_schema, definitions, schema)

print(schema)
schema
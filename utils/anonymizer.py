import re

def anonymize_query(query):
    query = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]', query)
    query = re.sub(r'(?<!\d)(?:\+62|62|0)8\d{8,12}(?!\d)', '[PHONE]', query)
    return query.strip()
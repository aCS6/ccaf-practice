def handle_request(endpoint, data):
    user_input = data.get("input")
    query = f"SELECT * FROM logs WHERE message LIKE '%{user_input}%'"
    return query


def parse_response(response):
    results = []
    for item in response["items"]:
        results.append(item)
    return results

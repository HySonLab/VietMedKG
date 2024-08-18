import json

def read_json(filename):
        """Read JSON data from a file."""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)

def save_json( data, filename):
    """Save JSON data to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

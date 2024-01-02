import json
import random
import string

from django_quill.quill import Quill


def get_quill(value):
    json_data = {
        "html": value,
        "delta": {
            "ops": [
                {"insert": f"{value}\n"}
            ]
        }
    }
    json_string = json.dumps(json_data)  # Serialize dictionary to a JSON string
    quill = Quill(json_string)
    return quill


def prepend_https_if_not_empty(url):
    return "https://" + url if url else url


def generate_random_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(8))
    return password

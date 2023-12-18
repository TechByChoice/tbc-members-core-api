import json

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
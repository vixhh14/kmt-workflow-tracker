from dotenv import dotenv_values
import json

def check_env(file_path, output_name):
    try:
        data = dotenv_values(file_path)
        keys = list(data.keys())
        with open(output_name, "w") as f:
            json.dump(keys, f)
    except Exception as e:
        with open(output_name, "w") as f:
            f.write(str(e))

check_env(".env", "env_keys.json")
check_env(".env.production", "env_prod_keys.json")

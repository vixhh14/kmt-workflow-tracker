import os
from dotenv import dotenv_values

print("Checking .env...")
env_vars = dotenv_values(".env")
for key in env_vars:
    print(f"Key: {key}")

print("\nChecking .env.production...")
env_prod_vars = dotenv_values(".env.production")
for key in env_prod_vars:
    print(f"Key: {key}")

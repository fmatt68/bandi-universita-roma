import os

print("Test GitHub")

email = os.environ.get("EMAIL_ADDRESS")
password = os.environ.get("EMAIL_PASSWORD")

print("EMAIL_ADDRESS:", email)
print("EMAIL_PASSWORD presente:", password is not None)

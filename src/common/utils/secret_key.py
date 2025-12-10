import secrets

key = secrets.token_urlsafe(64)  # Generates a URL-safe token based on 64 random bytes
print(key)

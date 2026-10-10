
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Keep authentication keys outside GitHub and OneDrive.
key_folder = Path.home() / ".snowflake_keys"
key_folder.mkdir(mode=0o700, exist_ok=True)

private_path = key_folder / "retail_streamlit_private_key.pem"
public_path = key_folder / "retail_streamlit_public_key.pem"

# Prevent accidental overwriting.
if private_path.exists() or public_path.exists():
    raise FileExistsError("Key files already exist. No files were changed.")

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

with private_path.open("xb") as f:
    f.write(private_pem)

with public_path.open("xb") as f:
    f.write(public_pem)

print("SUCCESS: Snowflake authentication keys generated.")
print("Private key:", private_path)
print("Public key:", public_path)
print("Keep the private key secret.")

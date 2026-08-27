import os


class Config:
    """
    All settings are read from environment variables so real secrets
    never live in source code. Copy .env.example to .env for local dev.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # MongoDB Atlas
    MONGODB_URI = os.environ.get("MONGODB_URI", "")
    MONGODB_DB = os.environ.get("MONGODB_DB", "techfinix26")

    # Cloudinary (optional in dev — falls back to local disk storage)
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max upload

    # First super coordinator, created automatically on first run if
    # no coordinator exists yet. Change the password immediately after.
    BOOTSTRAP_ADMIN_USERNAME = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin")
    BOOTSTRAP_ADMIN_PASSWORD = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "techfinix26")

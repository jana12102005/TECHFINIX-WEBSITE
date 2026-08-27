"""
Photo storage abstraction.

If CLOUDINARY_CLOUD_NAME / API_KEY / API_SECRET are all set, uploads go
straight to Cloudinary and this returns the hosted https URL.

Otherwise (local dev, or before you've created a Cloudinary account),
uploads are written to app/static/uploads/ and a local URL is returned.
NOTE: Render's filesystem is ephemeral — local storage is fine for
testing on your own machine, but for the real deployment you should
set the Cloudinary env vars so photos survive restarts/redeploys.
"""
import os
import uuid
from flask import current_app, url_for

LOCAL_UPLOAD_DIR = os.path.join("app", "static", "uploads")


def _cloudinary_configured():
    cfg = current_app.config
    return bool(cfg.get("CLOUDINARY_CLOUD_NAME") and cfg.get("CLOUDINARY_API_KEY")
                and cfg.get("CLOUDINARY_API_SECRET"))


def _ensure_local_dir():
    os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)


def save_photo(file_storage, folder="gallery"):
    """
    Accepts a werkzeug FileStorage (from request.files) and returns
    a dict: {"url": <public url>, "public_id": <id used for deletion>,
    "backend": "cloudinary" | "local"}
    """
    ext = os.path.splitext(file_storage.filename or "")[1].lower() or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"

    if _cloudinary_configured():
        try:
            import cloudinary
            import cloudinary.uploader
            cfg = current_app.config
            cloudinary.config(
                cloud_name=cfg["CLOUDINARY_CLOUD_NAME"],
                api_key=cfg["CLOUDINARY_API_KEY"],
                api_secret=cfg["CLOUDINARY_API_SECRET"],
                secure=True,
            )
            result = cloudinary.uploader.upload(
                file_storage,
                folder=f"techfinix26/{folder}",
                public_id=unique_name.rsplit(".", 1)[0],
                overwrite=False,
            )
            return {"url": result["secure_url"], "public_id": result["public_id"], "backend": "cloudinary"}
        except Exception as exc:
            current_app.logger.warning(f"[storage] Cloudinary upload failed ({exc}); falling back to local disk.")

    _ensure_local_dir()
    sub_dir = os.path.join(LOCAL_UPLOAD_DIR, folder)
    os.makedirs(sub_dir, exist_ok=True)
    disk_path = os.path.join(sub_dir, unique_name)
    file_storage.seek(0)
    file_storage.save(disk_path)
    public_url = url_for("static", filename=f"uploads/{folder}/{unique_name}")
    return {"url": public_url, "public_id": f"{folder}/{unique_name}", "backend": "local"}


def save_photo_bytes(data: bytes, filename="capture.jpg", folder="gallery"):
    """
    Same as save_photo but for raw bytes — used for the coordinator's
    live-camera capture, which arrives as a base64 data URL rather than
    a multipart file upload.
    """
    ext = os.path.splitext(filename)[1].lower() or ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"

    if _cloudinary_configured():
        try:
            import cloudinary
            import cloudinary.uploader
            cfg = current_app.config
            cloudinary.config(
                cloud_name=cfg["CLOUDINARY_CLOUD_NAME"],
                api_key=cfg["CLOUDINARY_API_KEY"],
                api_secret=cfg["CLOUDINARY_API_SECRET"],
                secure=True,
            )
            result = cloudinary.uploader.upload(
                data,
                folder=f"techfinix26/{folder}",
                public_id=unique_name.rsplit(".", 1)[0],
                overwrite=False,
            )
            return {"url": result["secure_url"], "public_id": result["public_id"], "backend": "cloudinary"}
        except Exception as exc:
            current_app.logger.warning(f"[storage] Cloudinary upload_bytes failed ({exc}); falling back to local disk.")

    _ensure_local_dir()
    sub_dir = os.path.join(LOCAL_UPLOAD_DIR, folder)
    os.makedirs(sub_dir, exist_ok=True)
    disk_path = os.path.join(sub_dir, unique_name)
    with open(disk_path, "wb") as f:
        f.write(data)
    public_url = url_for("static", filename=f"uploads/{folder}/{unique_name}")
    return {"url": public_url, "public_id": f"{folder}/{unique_name}", "backend": "local"}


def delete_photo(public_id, backend):
    if backend == "cloudinary":
        import cloudinary
        import cloudinary.uploader
        cfg = current_app.config
        cloudinary.config(
            cloud_name=cfg["CLOUDINARY_CLOUD_NAME"],
            api_key=cfg["CLOUDINARY_API_KEY"],
            api_secret=cfg["CLOUDINARY_API_SECRET"],
            secure=True,
        )
        cloudinary.uploader.destroy(public_id)
    else:
        path = os.path.join("app", "static", "uploads", public_id)
        if os.path.exists(path):
            os.remove(path)

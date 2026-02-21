print("ANCHU.PY FILE STARTED")

from flask import Flask, render_template, request
import os 
import hashlib 
import magic 
from PIL import Image

from datetime import datetime

app = Flask(__name__)

# ======================
# UPLOAD FOLDER SETUP
# ======================
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ======================
# HASH FUNCTION
# ======================
def generate_hash(filepath):
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def check_real_file_type(filepath):
    try:
        file_type = magic.from_file(filepath, mime=True)
        return file_type
    except:
        return "Unknown"
    
def check_image_metadata(filepath):
    try:
        img = Image.open(filepath)
        exif_data = img._getexif()

        if exif_data:
            return True   # metadata mila
        else:
            return False  # metadata nahi mila
    except:
        return False


# ======================
# BASIC METADATA
# ======================
def get_basic_metadata(filepath):
    stats = os.stat(filepath)
    return {
        "size_kb": round(stats.st_size / 1024, 2),
        "created_time": stats.st_ctime,
        "modified_time": stats.st_mtime
    }


# ======================
# TIME FORMATTER
# ======================
def format_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# ======================
# RISK ANALYSIS
# ======================
def calculate_risk(basic_meta):
    risk_score = 0
    reasons = []

    if basic_meta["created_time"] != basic_meta["modified_time"]:
        risk_score += 30
        reasons.append("File was modified after creation")

    if basic_meta["size_kb"] > 3000:
        risk_score += 10
        reasons.append("Large file size may indicate re-export or processing")

    if risk_score >= 40:
        risk_level = "High"
    elif risk_score >= 20:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return risk_level, reasons


# ======================
# HOME ROUTE
# ======================
@app.route("/")
def home():
    return render_template("index.html")


# ======================
# UPLOAD ROUTE
# ======================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["mediafile"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

    file.save(filepath)

    # ===== File Type Check =====
    real_file_type = check_real_file_type(filepath)
    extension = file.filename.split('.')[-1].lower()

    # ===== Metadata Presence =====
    has_metadata = False
    if extension in ['jpg', 'jpeg', 'png']:
        has_metadata = check_image_metadata(filepath)

    # ===== Type Mismatch =====
    type_mismatch = False
    if extension in ['jpg', 'jpeg', 'png'] and not real_file_type.startswith("image"):
        type_mismatch = True
    elif extension in ['mp4', 'mov'] and not real_file_type.startswith("video"):
        type_mismatch = True

    # ===== Hash & Metadata =====
    file_hash = generate_hash(filepath)
    basic_meta = get_basic_metadata(filepath)

    basic_meta["created_time"] = format_time(basic_meta["created_time"])
    basic_meta["modified_time"] = format_time(basic_meta["modified_time"])

    # ===== Risk Analysis =====
    risk_level, reasons = calculate_risk(basic_meta)

    return render_template(
        "result.html",
        filename=file.filename,
        file_hash=file_hash,
        basic_meta=basic_meta,
        risk_level=risk_level,
        reasons=reasons,
        real_file_type=real_file_type,
        type_mismatch=type_mismatch,
        has_metadata=has_metadata
    )

# ======================
# APP START
# ======================
if __name__ == "__main__":
    app.run(debug=True)

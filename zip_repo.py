import os
import zipfile

def create_zip():
    exclude_dirs = {'.git', 'node_modules', '.venv', '.pytest_cache', '__pycache__', '.expo', 'dist', '.next'}
    exclude_exts = {'.zip'}
    
    with zipfile.ZipFile('TrueCost_Mobile_Scraper_Certification_Ready.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)

create_zip()
print("Zip created successfully.")

import shutil
import os

src = 'backend/services/ai_service_new.py'
dst = 'backend/services/ai_service.py'

if os.path.exists(src):
    shutil.copy(src, dst)
    print(f"✅ Copied {src} to {dst}")
else:
    print(f"❌ Source file {src} not found")

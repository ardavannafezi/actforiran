#!/usr/bin/env python3
import shutil

# Backup the old file
shutil.copy('ai_service.py', 'ai_service.py.old')

# Copy the new file over
shutil.copy('ai_service_new.py', 'ai_service.py')

print("✅ AI service updated successfully!")

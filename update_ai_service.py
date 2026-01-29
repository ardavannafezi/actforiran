#!/usr/bin/env python3

with open('backend/services/ai_service_new.py', 'r') as src:
    content = src.read()

with open('backend/services/ai_service.py', 'w') as dst:
    dst.write(content)

print("✅ AI service file updated successfully!")

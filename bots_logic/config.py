import re


ADMIN_ID = []

raw_signatures = [
   
                ]


UNWANTED_LIST = []
for signature in raw_signatures:
    escaped_signature = re.escape(signature)
    UNWANTED_LIST.append(escaped_signature)
    UNWANTED_LIST.append(escaped_signature + r'\s*\([^)]+\)')

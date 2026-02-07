import re
with open('src/trustyclaw/sdk/escrow_contract.py', 'r') as f:
    content = f.read()
content = re.sub(r'\\\\&quot;', "'", content)
content = re.sub(r'\\\\\"', "'", content)
content = re.sub(r'&quot;', "'", content)
content = re.sub(r'&amp;#x27;', "'", content)
with open('src/trustyclaw/sdk/escrow_contract.py', 'w') as f:
    f.write(content)
print('Fixed')
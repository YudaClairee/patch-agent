import sys
path = "/home/yudaclairee/project/patch-agent/apps/backend/.venv/lib/python3.13/site-packages/agno/models/litellm/chat.py"
with open(path, "r") as f:
    text = f.read()

text = text.replace(
    'msg["tool_call_id"] = m.tool_call_id or ""',
    'if m.tool_call_id:\n                    msg["tool_call_id"] = m.tool_call_id\n                else:\n                    pass # Do not set empty string',
).replace(
    'msg["name"] = m.name or ""',
    'if m.name:\n                    msg["name"] = m.name\n                else:\n                    pass # Do not set empty string',
)

with open(path, "w") as f:
    f.write(text)

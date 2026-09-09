import os

print("Files in handlers:")
if os.path.exists("handlers"):
    print(os.listdir("handlers"))

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "CommandStart" in content or "start=" in content or "command='start'" in content or 'command="start"' in content:
                    print(f"Found start handler in: {path}")

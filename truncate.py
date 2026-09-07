with open("dashboard/admin_gateway.html", "r", encoding="utf-8") as f:
    text = f.read()
    
idx = text.find("</html>")
if idx != -1:
    text = text[:idx + len("</html>")] + "\n"
    with open("dashboard/admin_gateway.html", "w", encoding="utf-8") as f:
        f.write(text)
    print("Truncated at </html>!")
else:
    print("</html> not found!")

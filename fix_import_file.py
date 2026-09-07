import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

original_file_name = "field.filename if field.filename else 'Import'"

for i in range(1276, 1285):
    if "SET first_name = ?" in lines[i]:
        lines[i] = lines[i].replace("source = 'excel'", "source = 'excel', source_file = ?")
    if "first_name, last_name, phone" in lines[i] and 'student_id))' in lines[i]:
        lines[i] = lines[i].replace("email, student_id))", f"original_file_name, email, student_id))\n")
        lines[i] = "                        original_file_name = field.filename if field.filename else 'Fichier Excel'\n" + lines[i]
    if "INSERT INTO academy_students" in lines[i]:
        lines[i] = lines[i].replace("magic_token, is_active", "source_file, magic_token, is_active")
    if "VALUES (?, ?" in lines[i]:
        lines[i] = lines[i].replace("'excel', ?, 1", "'excel', ?, ?, 1")
    if "secrets.token_urlsafe(8), created_at_val))" in lines[i]:
        lines[i] = lines[i].replace("secrets.token_urlsafe(8)", "original_file_name, secrets.token_urlsafe(8)")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

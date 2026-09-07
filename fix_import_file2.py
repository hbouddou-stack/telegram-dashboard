import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for l in lines:
    if "original_file_name = field.filename if field.filename else 'Fichier Excel'" in l and '"""' not in l:
        pass # skip it
    elif "UPDATE academy_students" in l:
        new_lines.append("                    original_file_name = field.filename if field.filename else 'Fichier Excel'\n")
        new_lines.append(l)
    else:
        new_lines.append(l)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

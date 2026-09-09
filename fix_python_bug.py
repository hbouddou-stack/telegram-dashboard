import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'await db.execute("""\n                    original_file_name = field.filename if field.filename else \'Fichier Excel\'',
    "original_file_name = field.filename if field.filename else 'Fichier Excel'\n                    await db.execute(\"\"\""
)

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

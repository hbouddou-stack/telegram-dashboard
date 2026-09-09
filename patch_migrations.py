import io

with io.open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_cols = """            ('whatsapp_error', 'TEXT'),
            ('profession', 'TEXT'),
            ('country', 'TEXT'),
            ('nationality', 'TEXT'),
            ('arabic_level', 'TEXT'),"""

text = text.replace("('whatsapp_error', 'TEXT'),", new_cols)

with io.open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Added missing columns to auto-migration')

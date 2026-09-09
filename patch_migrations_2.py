import io

with io.open('database.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_cols = """            ('excluded', 'INTEGER DEFAULT 0'),
            ('profession', 'TEXT'),
            ('country', 'TEXT'),
            ('nationality', 'TEXT'),
            ('arabic_level', 'TEXT'),"""

text = text.replace("('excluded', 'INTEGER DEFAULT 0'),", new_cols)

with io.open('database.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Added missing columns to auto-migration correctly')

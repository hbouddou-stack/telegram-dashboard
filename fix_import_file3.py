import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_import_function = False
for i in range(len(lines)):
    if "async def api_admin_gateway_import_students" in lines[i]:
        in_import_function = True
        
    if in_import_function and "UPDATE academy_students" in lines[i]:
        # Only inject the file name if we're in the import function and modifying the main details
        if "first_name" in lines[i+1]:
            lines[i] = "                    original_file_name = field.filename if field.filename else 'Fichier Excel'\n" + lines[i]
            lines[i+1] = lines[i+1].replace("source = 'excel'", "source = 'excel', source_file = ?")
            # The WHERE is on i+2, the execution params are on i+3
            lines[i+3] = lines[i+3].replace("email, student_id))", "original_file_name, email, student_id))")
            
    if in_import_function and "INSERT INTO academy_students" in lines[i]:
        if "first_name" in lines[i]:
            lines[i] = lines[i].replace("magic_token, is_active", "source_file, magic_token, is_active")
            lines[i+1] = lines[i+1].replace("'excel', ?, 1", "'excel', ?, ?, 1")
            lines[i+2] = lines[i+2].replace("secrets.token_urlsafe(8)", "original_file_name, secrets.token_urlsafe(8)")
            
    if in_import_function and "return web.json_response" in lines[i]:
        # exit the function scope roughly
        if "except" in lines[i-1]:
            in_import_function = False

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

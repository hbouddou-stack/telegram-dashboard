
import io
with io.open("sync_sheets.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i in range(len(lines)):
    if "FEMALE" in lines[i] and "c_up in" in lines[i]:
        lines[i] = "                if c_up in [\"FEMME\", \"FEMALE\", \"FILLE\", \"F\", \"????\"]:\n"
    elif "MALE" in lines[i] and "c_up in" in lines[i]:
        lines[i] = "                elif c_up in [\"HOMME\", \"MALE\", \"GARCON\", \"M\", \"???\"]:\n"
    elif "UNPAID" in lines[i] and "c_up in" in lines[i]:
        lines[i] = "                if c_up in [\"UNPAID\", \"NON\", \"ATTENTE\", \"PENDING\", \"??? ?????\"]:\n"
with io.open("sync_sheets.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

with io.open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i in range(len(lines)):
    if "FEMALE" in lines[i] and "c_up in" in lines[i]:
        lines[i] = "                    if c_up in [\"FEMME\", \"FEMALE\", \"FILLE\", \"F\", \"????\"]:\n"
    elif "MALE" in lines[i] and "c_up in" in lines[i]:
        lines[i] = "                    elif c_up in [\"HOMME\", \"MALE\", \"GARCON\", \"M\", \"???\"]:\n"
    elif "UNPAID" in lines[i] and "c_up in" in lines[i]:
        lines[i] = "                    if c_up in [\"UNPAID\", \"NON\", \"ATTENTE\", \"PENDING\", \"??? ?????\", \"???\"]:\n"
    elif "PAID" in lines[i] and "c_up in" in lines[i]:
        lines[i] = "                    elif c_up in [\"PAID\", \"PAYE\", \"VALIDE\", \"CONFIRME\", \"?????\", \"???\"]:\n"
with io.open("main.py", "w", encoding="utf-8") as f:
    f.writelines(lines)


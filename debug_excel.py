import io, sys
import openpyxl
import unicodedata

# Ce script analyse ton Excel et affiche exactement ce que Python voit
# Tu peux le glisser-déposer sur le fichier Excel dans la console

excel_path = "test_import.xlsx"  # Mets le nom de ton fichier ici

try:
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active

    with io.open('excel_debug.txt', 'w', encoding='utf-8') as out:
        out.write(f"=== ANALYSE EXCEL: {excel_path} ===\n\n")
        out.write(f"Nombre de lignes: {sheet.max_row}\n")
        out.write(f"Nombre de colonnes: {sheet.max_column}\n\n")

        for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
            if not any(row):
                continue
            if r_idx == 0:
                out.write("=== EN-TETES (Ligne 1) ===\n")
                for col_idx, cell in enumerate(row):
                    if cell:
                        out.write(f"  Col {col_idx} ({chr(65+col_idx)}): {repr(cell)}\n")
                out.write("\n")
                continue

            if r_idx > 6:  # Analyser seulement les 5 premiers eleves
                break

            out.write(f"=== ETUDIANT Ligne {r_idx+1} ===\n")
            for col_idx, cell in enumerate(row):
                if cell is not None:
                    raw = str(cell)
                    normalized = unicodedata.normalize('NFKC', raw.strip())
                    has_invisible = any(c in raw for c in ['\u200f','\u200e','\u200b','\u200c','\u200d','\ufeff','\xa0'])
                    out.write(f"  Col {col_idx} ({chr(65+col_idx)}): {repr(raw)}")
                    if has_invisible:
                        out.write(f"  ⚠️ CARACTERES INVISIBLES DETECTED")
                    out.write(f"\n  -> hex: {raw.encode('utf-8').hex()}\n")

            # Test de la detection de paiement
            row_list = [str(c) if c is not None else '' for c in row]
            UNPAID_WORDS = ['غير مسدد', 'UNPAID', 'NON PAYE', 'غير مدفوع']
            PAID_WORDS = ['مسدد', 'مدفوع', 'PAID', 'PAYÉ', 'PAYE', 'OUI', 'YES', 'VALIDE']

            payment = 'UNPAID (default)'
            found_unpaid = False
            for cell_val in row_list:
                clean = unicodedata.normalize('NFKC', cell_val.strip())
                for w in UNPAID_WORDS:
                    if w in clean:
                        payment = f'UNPAID (trouvé: "{w}" dans "{clean[:30]}")'
                        found_unpaid = True
                        break
                if found_unpaid:
                    break
            if not found_unpaid:
                for cell_val in row_list:
                    clean = unicodedata.normalize('NFKC', cell_val.strip())
                    for w in PAID_WORDS:
                        if w in clean:
                            payment = f'PAID (trouvé: "{w}" dans "{clean[:30]}")'
                            break

            out.write(f"  --> RESULTAT DETECTION: {payment}\n\n")

    print("Analyse terminée! Voir excel_debug.txt")

except FileNotFoundError:
    print(f"Erreur: Fichier '{excel_path}' introuvable!")
    print("Place ce script dans le même dossier que ton Excel et change le nom du fichier en haut du script.")
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()

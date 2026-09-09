import io, unicodedata

def clean_cell(val):
    """Nettoie une cellule Excel : espaces insecables, marques RTL/LTR, normalisation Unicode."""
    s = str(val or '').strip()
    s = unicodedata.normalize('NFKC', s)
    # Supprimer marques directionnelles arabes invisibles
    for c in ['\u200f', '\u200e', '\u200b', '\u200c', '\u200d', '\ufeff']:
        s = s.replace(c, '')
    return s.strip()

def detect_payment_status(row):
    """
    Détecte le statut de paiement de manière infaillible.
    Priorité absolue : 'غير مسدد' AVANT 'مسدد' car l'un est sous-chaine de l'autre.
    On isole d'abord la cellule H (index 7), sinon on scanne la ligne entière.
    """
    UNPAID_WORDS = ['غير مسدد', 'UNPAID', 'غير', 'NON PAYE', 'غير مدفوع']
    PAID_WORDS   = ['مسدد', 'مدفوع', 'PAID', 'PAYÉ', 'PAYE', 'OUI', 'YES', 'VALIDE', 'CONFIRME']

    # Étape 1 : isoler la cellule H (index 7) si elle existe
    cell_h = clean_cell(row[7]) if len(row) > 7 else ''

    # Étape 2 : scanner toute la ligne pour filet de sécurité
    all_cells = [clean_cell(c) for c in row]

    # RÈGLE D'OR : tester UNPAID EN PREMIER car 'مسدد' est contenu dans 'غير مسدد'
    for candidate in [cell_h] + all_cells:
        for word in UNPAID_WORDS:
            if word in candidate:
                return 'UNPAID'

    # Seulement ensuite tester PAID
    for candidate in [cell_h] + all_cells:
        for word in PAID_WORDS:
            if word in candidate:
                return 'PAID'

    # Par défaut : UNPAID (pas d'information = on ne considère pas comme payé)
    return 'UNPAID'

# TEST
test_rows = [
    ['', '', '', '', '', '', '', 'غير مسدد'],
    ['', '', '', '', '', '', '', 'مسدد'],
    ['', '', '', '', '', '', '', ''],
    ['غير مسدد', '', '', '', '', '', '', 'مسدد'],  # conflit - UNPAID doit gagner
    ['', '', '', '', '', '', '', 'PAID'],
    ['', '', '', '', '', '', '', 'UNPAID'],
]

with io.open('payment_test_results.txt', 'w', encoding='utf-8') as f:
    for row in test_rows:
        result = detect_payment_status(row)
        line = f"row[7]='{row[7]}' | all='{row[0]}' => {result}\n"
        f.write(line)

print("Test done - see payment_test_results.txt")

import io, unicodedata

# Test du bug exact
msg_unpaid = 'غير مسدد'
msg_paid   = 'مسدد'

# مسدد EST une sous-chaine de غير مسدد
is_sub = msg_paid in msg_unpaid
with io.open('debug_payment.txt', 'w', encoding='utf-8') as f:
    f.write(f"'مسدد' est sous-chaine de 'غير مسدد': {is_sub}\n")
    f.write("Donc si le match exact sur 'غير مسدد' echoue (ex: caracteres invisibles Unicode),\n")
    f.write("le elif 'مسدد' in row_str s'active quand meme car 'مسدد' IS in 'غير مسدد'!\n\n")

    # Simuler la lecture depuis Excel avec openpyxl
    # Les cellules Excel peuvent contenir des espaces insecables (U+00A0) ou des
    # caracteres RTL invisibles comme U+200F (RIGHT-TO-LEFT MARK)
    evil_val = '\u200f' + 'غير مسدد' + '\u200f'  # Avec RTL marks
    f.write(f"Valeur Excel avec RTL marks: repr = {repr(evil_val)}\n")

    row_str_evil = " ".join([str(evil_val)]).upper()
    result_code = 'غير مسدد'
    f.write(f"'غير مسدد' in row_str (avec RTL marks): {'غير مسدد' in row_str_evil}\n")
    f.write(f"Apres normalisation NFKC + strip: {'غير مسدد' in unicodedata.normalize('NFKC', row_str_evil).replace('\u200f', '').replace('\u200e', '')}\n")

print("Voir debug_payment.txt")

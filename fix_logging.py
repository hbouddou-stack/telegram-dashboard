import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Disable aiosqlite DEBUG noise
# Find logging setup and add aiosqlite suppression
for i, l in enumerate(lines):
    if 'logging.basicConfig' in l:
        # Insert after this line
        lines.insert(i+1, "logging.getLogger('aiosqlite').setLevel(logging.WARNING)  # Suppress DEBUG noise\n")
        print(f"Inserted aiosqlite suppression at line {i+2}")
        break

# 2. Remove the old debug block that was causing Railway to drop logs
# and replace with a simpler one-liner WARNING only
for i, l in enumerate(lines):
    if '[PAYMENT DEBUG]' in l:
        # Keep it but simplify - only log PAID results (not UNPAID)
        lines[i] = "                _log_tmp.warning(f'[PAY] {email} | H={repr(str(row[7] if len(row)>7 else \"\"))[:40]} | {payment_status}')\n"
        print(f"Simplified debug at line {i+1}")
        break

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

with open("database.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Remove the bad injection from log_conversation
import re
bad_injection_pattern = re.compile(r"\s*for col, col_def in \[\s*\('email_opened_at', 'TEXT'\).*?except Exception:\s*pass", re.DOTALL)
text = bad_injection_pattern.sub("", text)

# 2. Inject properly into init_db
# In init_db(), there is a block:
#         await db.execute("ALTER TABLE academy_students ADD COLUMN magic_token TEXT")
#     except Exception:
#         pass

target_str = """        except Exception:
            pass
            
        # POPULATE MISSING TOKENS"""

injection = """        except Exception:
            pass
            
        for col, col_def in [
            ('email_opened_at', 'TEXT'),
            ('email_clicked_at', 'TEXT'),
            ('whatsapp_sent', 'INTEGER DEFAULT 0'),
            ('whatsapp_sent_at', 'TEXT'),
            ('whatsapp_clicked_at', 'TEXT'),
            ('last_click_source', 'TEXT'),
            ('group_joined', 'INTEGER DEFAULT 0'),
            ('joined_at', 'TEXT')
        ]:
            try:
                await db.execute(f'ALTER TABLE academy_students ADD COLUMN {col} {col_def}')
            except Exception:
                pass
                
        # POPULATE MISSING TOKENS"""

text = text.replace(target_str, injection)

with open("database.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Fixed again!")

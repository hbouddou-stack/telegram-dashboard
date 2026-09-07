import io

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

middleware_code = """
class UsernameTrackerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        import asyncio
        if isinstance(event, Message) and event.from_user and not event.from_user.is_bot:
            asyncio.create_task(self.check_username(event.from_user))
        elif isinstance(event, CallbackQuery) and event.from_user and not event.from_user.is_bot:
            asyncio.create_task(self.check_username(event.from_user))
            
        return await handler(event, data)

    async def check_username(self, user):
        import database as db
        import aiosqlite
        from config import DATABASE_PATH
        
        telegram_id = user.id
        username = user.username or ''
        first_name = user.first_name or ''
        last_name = user.last_name or ''
        
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db_conn:
                db_conn.row_factory = aiosqlite.Row
                async with db_conn.execute("SELECT first_name, last_name, username FROM users WHERE telegram_id = ?", (telegram_id,)) as cur:
                    user_row = await cur.fetchone()
                
                if user_row:
                    old_username = user_row['username'] or ''
                    old_first = user_row['first_name'] or ''
                    old_last = user_row['last_name'] or ''
                    
                    changed = False
                    notes = []
                    
                    if old_username != username:
                        notes.append(f"• Pseudo changé : @{old_username or 'Aucun'} ➡️ @{username or 'Aucun'}")
                        changed = True
                    if old_first != first_name:
                        notes.append(f"• Prénom changé : {old_first} ➡️ {first_name}")
                        changed = True
                    if old_last != last_name:
                        notes.append(f"• Nom changé : {old_last} ➡️ {last_name}")
                        changed = True
                        
                    if changed:
                        # Mettre à jour la table users
                        await db_conn.execute(
                            "UPDATE users SET username=?, first_name=?, last_name=? WHERE telegram_id=?", 
                            (username, first_name, last_name, telegram_id)
                        )
                        
                        # Vérifier si c'est un élève lié
                        async with db_conn.execute("SELECT student_id FROM academy_students WHERE telegram_id = ?", (telegram_id,)) as cur2:
                            s = await cur2.fetchone()
                            if s:
                                student_id = s['student_id']
                                note_text = "🔄 الهوية متغيرة في تيليجرام (Changement d'identité) :\n" + "\n".join(notes)
                                # Ajouter note CRM
                                await db_conn.execute(
                                    "INSERT INTO student_logs (student_id, telegram_id, action_type, description, telegram_name, telegram_username) VALUES (?, ?, ?, ?, ?, ?)",
                                    (student_id, telegram_id, "CRM_NOTE", f"[بواسطة: النظام - SYSTEM] [نوع: IDENTITE]\n{note_text}", first_name, username)
                                )
                        await db_conn.commit()
                else:
                    # Inserer le fantôme silencieusement
                    await db_conn.execute(
                        "INSERT INTO users (telegram_id, first_name, last_name, username, created_at) VALUES (?, ?, ?, ?, datetime('now'))", 
                        (telegram_id, first_name, last_name, username)
                    )
                    await db_conn.commit()
        except Exception as e:
            import logging
            logging.getLogger('bot').error(f"UsernameTrackerMiddleware error: {e}")

"""

if 'class UsernameTrackerMiddleware' not in c:
    # Inject it before AccessCheckMiddleware
    c = c.replace('class AccessCheckMiddleware', middleware_code + '\nclass AccessCheckMiddleware')
    # Register it
    reg_code = "dp.message.outer_middleware(UsernameTrackerMiddleware())\n        dp.callback_query.outer_middleware(UsernameTrackerMiddleware())"
    if reg_code not in c:
        c = c.replace('dp.message.outer_middleware(AccessCheckMiddleware())',
                      reg_code + '\n        dp.message.outer_middleware(AccessCheckMiddleware())')
    
    with io.open('main.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Middleware injected")
else:
    print("Middleware already there")

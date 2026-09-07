import io, re

with io.open('main.py', 'r', encoding='utf-8') as f:
    c = f.read()

home_stats_api = """
async def api_admin_gateway_home_stats(request: web.Request):
    import aiosqlite
    from config import DATABASE_PATH
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            # KPIs
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL") as cur:
                total_students = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND telegram_id IS NOT NULL") as cur:
                linked_students = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND folder_clicked_at IS NOT NULL") as cur:
                in_groups = (await cur.fetchone())['cnt']
                
            async with db.execute("SELECT COUNT(*) as cnt FROM users u LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id WHERE s.telegram_id IS NULL") as cur:
                ghosts = (await cur.fetchone())['cnt']

            # Funnel Data
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND (email_sent > 0 OR whatsapp_sent > 0)") as cur:
                contacted = (await cur.fetchone())['cnt']
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND bot_started_at IS NOT NULL") as cur:
                started_bot = (await cur.fetchone())['cnt']
                
            # Demographics
            async with db.execute("SELECT school_level, COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL GROUP BY school_level") as cur:
                levels = {str(r['school_level']): r['cnt'] for r in await cur.fetchall()}
            async with db.execute("SELECT gender, COUNT(*) as cnt FROM academy_students WHERE excluded = 0 OR excluded IS NULL GROUP BY gender") as cur:
                genders = {str(r['gender']): r['cnt'] for r in await cur.fetchall()}

            # Alerts
            async with db.execute("SELECT COUNT(*) as cnt FROM academy_students WHERE (excluded = 0 OR excluded IS NULL) AND email_sent = 0 AND whatsapp_sent = 0") as cur:
                uncontacted = (await cur.fetchone())['cnt']
            
            # Ghosts from today
            async with db.execute("SELECT COUNT(*) as cnt FROM users u LEFT JOIN academy_students s ON s.telegram_id = u.telegram_id WHERE s.telegram_id IS NULL AND u.created_at >= date('now')") as cur:
                ghosts_today = (await cur.fetchone())['cnt']

            return web.json_response({
                "success": True,
                "kpis": {
                    "total": total_students,
                    "linked": linked_students,
                    "groups": in_groups,
                    "ghosts": ghosts
                },
                "funnel": {
                    "imported": total_students,
                    "contacted": contacted,
                    "started_bot": started_bot,
                    "linked": linked_students,
                    "joined": in_groups
                },
                "demographics": {
                    "levels": levels,
                    "genders": genders
                },
                "alerts": {
                    "uncontacted": uncontacted,
                    "ghosts_today": ghosts_today
                }
            })
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)})

"""
if "api_admin_gateway_home_stats" not in c:
    # Inject it before api_admin_gateway_kpi
    c = c.replace('async def api_admin_gateway_kpi', home_stats_api + '\nasync def api_admin_gateway_kpi')
    
    # Add route
    c = c.replace("app.router.add_get('/api/admin/gateway/kpi', api_admin_gateway_kpi)", 
                  "app.router.add_get('/api/admin/gateway/kpi', api_admin_gateway_kpi)\n    app.router.add_get('/api/admin/gateway/home_stats', api_admin_gateway_home_stats)")

with io.open('main.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Home stats API written.")

import asyncio
from database import get_db

async def patch():
    db = await get_db()
    try:
        await db.execute("ALTER TABLE academy_students ADD COLUMN school_level TEXT")
        await db.commit()
        print("Column school_level added")
    except Exception as e:
        print(e)
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(patch())

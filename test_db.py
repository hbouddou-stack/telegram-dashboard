import asyncio
import database as db

async def test():
    try:
        res1 = await db.get_student_global_stats(5413180491)
        print("Stats:", res1)
        res2 = await db.get_student_global_radar(5413180491)
        print("Radar:", res2)
        res3, _, _ = await db.get_detailed_subject_progress(5413180491, 'fiqh')
        print("Map Fiqh len:", len(res3))
    except Exception as e:
        print("Error:", e)

asyncio.run(test())

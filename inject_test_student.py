import asyncio
import aiosqlite
import sys
from config import DATABASE_PATH
from database import init_db

async def inject_test_student(email, dob):
    await init_db()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if already exists
        async with db.execute("SELECT student_id FROM academy_students WHERE email = ?", (email,)) as cursor:
            row = await cursor.fetchone()
            if row:
                print(f"L'étudiant avec l'email {email} existe déjà (ID: {row[0]}). Mise à jour de la DOB...")
                await db.execute("UPDATE academy_students SET dob = ? WHERE email = ?", (dob, email))
            else:
                await db.execute("""
                    INSERT INTO academy_students (email, dob, first_name, last_name, year, gender, telegram_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (email, dob, "Houssam", "Test", "1ère Année", "Homme", None))
                print(f"Étudiant de test ajouté avec l'email {email} et DOB {dob}.")
        await db.commit()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python inject_test_student.py <email> <dob>")
        print("Exemple: python inject_test_student.py test@gmail.com 12/05/1995")
        sys.exit(1)
    
    email = sys.argv[1]
    dob = sys.argv[2]
    asyncio.run(inject_test_student(email, dob))

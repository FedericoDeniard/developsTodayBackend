from enum import Enum
from re import A
from pydantic import BaseModel, Field
import asyncpg
from models.models import Cat, Mission, Target, Note, StatusType
from utils.schemas import MissionCreate, TargetCreate, NoteCreate, CatCreate, CatAssignment, SalaryUpdate, StatusUpdate
from constants.keys import KEYS


class Database:
    def __init__(self):
        self.pool = None

    async def startup(self):
        await self._ensure_database_exists()
        self.pool = await asyncpg.create_pool(KEYS["DATABASE_URL"])
        await self._create_tables()

    async def shutdown(self):
        await self.pool.close()

    async def _ensure_database_exists(self):
        try:
            conn = await asyncpg.connect(KEYS["DATABASE_URL"])
            await conn.close()
        except asyncpg.InvalidCatalogNameError:
            conn = await asyncpg.connect(KEYS["DEFAULT_DB_URL"])
            await conn.execute(f'CREATE DATABASE "{KEYS['TARGET_DB']}";')
            await conn.close()
    
    async def _create_tables(self):
        await self._create_status_type()
        await self._create_cat_table()
        await self._create_mission_table()
        await self._create_target_table()
        await self._create_note_table()

    async def _create_status_type(self):
        query = """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_type') THEN
                CREATE TYPE status_type AS ENUM ('pending', 'in_progress', 'finished', 'cancelled');
            END IF;
        END
        $$;
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query)
    
    async def _create_cat_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS cats (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, years_of_experience INT NOT NULL, breed VARCHAR(255) NOT NULL, salary INT NOT NULL)
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query)

    async def _create_mission_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS missions (id SERIAL PRIMARY KEY, assigned_cat INT NULL, status status_type NOT NULL, title VARCHAR(255) NOT NULL, FOREIGN KEY (assigned_cat) REFERENCES cats(id))
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query)
    
    async def _create_target_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS targets (id SERIAL PRIMARY KEY, assigned_mission INT NOT NULL, status status_type NOT NULL, name VARCHAR(255) NOT NULL, country VARCHAR(255) NOT NULL, FOREIGN KEY (assigned_mission) REFERENCES missions(id))
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query)

    async def _create_note_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS notes (id SERIAL PRIMARY KEY, target_id INT NOT NULL, message VARCHAR(255) NOT NULL, FOREIGN KEY (target_id) REFERENCES targets(id))
        """
        async with self.pool.acquire() as connection:
            await connection.execute(query)

    async def create_cat(self, cat: Cat):
        cat.breed = cat.breed.title()
        if not await self._validate_breed(cat.breed):
            raise ValueError("Invalid breed")
        query = "INSERT INTO cats (name, years_of_experience, breed, salary) VALUES ($1, $2, $3, $4) RETURNING id, name, years_of_experience, breed, salary"
        return await self.pool.fetchrow(query, cat.name, cat.years_of_experience, cat.breed, cat.salary)

    async def delete_cat(self, cat_id: int):
        cat_in_mission = await self.pool.fetchrow("SELECT * FROM missions WHERE assigned_cat = $1", cat_id)
        if cat_in_mission:
            raise ValueError("Cat is assigned to a mission")
        result = await self.pool.execute("DELETE FROM cats WHERE id = $1", cat_id)
        deleted_count = int(result.split()[-1])
        if deleted_count == 0:
            raise ValueError("Cat not found")
    
    async def update_cat_salary(self, cat_id: int, salary: int):
        await self.pool.execute("UPDATE cats SET salary = $1 WHERE id = $2", salary, cat_id)
    
    async def _validate_breed(self, breed: str): 
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.thecatapi.com/v1/breeds/search?q={breed}")
            if response.status_code == 200:
                results = response.json()
                for result in results:
                    if result["name"] == breed:
                        return True
            return False

    async def create_mission(self, mission: MissionCreate):
        targets = mission.targets
        if len(targets) == 0:
            raise ValueError("No targets provided")
        if len(targets) > 3:
            raise ValueError("Too many targets provided")
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                query_mission = """
                    INSERT INTO missions (assigned_cat, status, title)
                    VALUES ($1, $2, $3)
                    RETURNING id
                """
                mission_id_row = await conn.fetchrow(
                    query_mission,
                    mission.assigned_cat,
                    mission.status.value if hasattr(mission.status, "value") else mission.status,
                    mission.title,
                )
                mission_id = mission_id_row["id"]

                query_target = """
                    INSERT INTO targets (assigned_mission, status, name, country)
                    VALUES ($1, $2, $3, $4)
                """
                for target in targets:
                    await conn.execute(
                        query_target,
                        mission_id,
                        target.status.value if hasattr(target.status, "value") else target.status,
                        target.name,
                        target.country,
                    )
        return mission_id
    
    async def delete_mission(self, mission_id: int):
        mission = await self.pool.fetchrow(
            "SELECT assigned_cat FROM missions WHERE id = $1", mission_id
        )
        if not mission:
            raise ValueError("Mission does not exist")
        
        if mission["assigned_cat"] is not None:
            raise ValueError("Mission is assigned to a cat, cannot be deleted")
        
        target_count = await self.pool.fetchval(
            "SELECT COUNT(*) FROM targets WHERE assigned_mission = $1", mission_id
        )
        if target_count > 0:
            await self.pool.execute(
                "UPDATE targets SET status = $1 WHERE assigned_mission = $2",
                StatusType.CANCELLED.value, mission_id
            )

        await self.pool.execute(
            "UPDATE missions SET status = $1 WHERE id = $2",
            StatusType.CANCELLED.value, mission_id
        )
    
    async def assign_cat_to_mission(self, mission_id: int, cat_id: int):
        mission = await self.pool.fetchrow(
            "SELECT assigned_cat FROM missions WHERE id = $1", mission_id
        )
        if not mission:
            raise ValueError("Mission does not exist")
        if mission["assigned_cat"] is not None:
            raise ValueError("Mission is already assigned to a cat")
        await self.pool.execute("UPDATE missions SET assigned_cat = $1 WHERE id = $2", cat_id, mission_id)

    async def create_note(self, note: Note):
        target = await self.pool.fetchrow("SELECT * FROM targets WHERE id = $1", note.target_id)
        if not target:
            raise ValueError("Target does not exist")
        if target["status"] == StatusType.FINISHED.value or target["status"] == StatusType.CANCELLED.value:
            raise ValueError("Target is finished or cancelled")
        query = """
        INSERT INTO notes (target_id, message)
        VALUES ($1, $2)
        """
        await self.pool.execute(query, note.target_id, note.message)        
    
    async def get_cats(self):
        query = "SELECT * FROM cats"
        return await self.pool.fetch(query)
    
    async def get_cat(self, cat_id: int):
        query = "SELECT * FROM cats WHERE id = $1"
        return await self.pool.fetchrow(query, cat_id)
    
    async def get_missions(self):
        query = "SELECT * FROM missions"
        return await self.pool.fetch(query)
    
    async def get_mission(self, mission_id: int):
        query = "SELECT * FROM missions WHERE id = $1"
        return await self.pool.fetchrow(query, mission_id)
    
    async def get_notes(self):
        query = "SELECT * FROM notes"
        return await self.pool.fetch(query)
    
    async def update_target_status(self, target_id: int, status: StatusType):
        query = "UPDATE targets SET status = $1 WHERE id = $2 RETURNING assigned_mission"
        mission_id = await self.pool.fetchval(query, status.value if hasattr(status, "value") else status, target_id)
        await self._update_mission_status(mission_id)
    
    async def _update_mission_status(self, mission_id: int):
        query = "SELECT * FROM targets WHERE assigned_mission = $1"
        targets = await self.pool.fetch(query, mission_id)
        if all(target["status"] == StatusType.FINISHED.value for target in targets):
            await self.pool.execute("UPDATE missions SET status = $1 WHERE id = $2", StatusType.FINISHED.value, mission_id)

# async def prueba():
#     database = Database()
#     await database.startup()
#     await database.create_cat(Cat(name="Jacinto", years_of_experience=1, breed="persian", salary=1))
#     await database.create_cat(Cat(name="Manuel", years_of_experience=2, breed="sphynx", salary=2))
#     await database.create_mission(Mission(assigned_cat=1, status=StatusType.PENDING, title="Conquistar el mundo"), [Target(assigned_mission=1, status=StatusType.PENDING, name="Target 1", country="Argentina")])
#     await database.create_mission(Mission(status=StatusType.PENDING, title="Conquistar el mundo2"), [Target(assigned_mission=1, status=StatusType.PENDING, name="Target 1", country="Argentina")])
#     await database.create_mission(Mission(status=StatusType.PENDING, title="Conquistar el mundo3"), [Target(assigned_mission=1, status=StatusType.PENDING, name="Target 1", country="Argentina")])
#     await database.create_note(Note(target_id=1, message="avanzamos con el objetivo"))
#     await database.delete_mission(2)
#     print(await database.get_cats())
#     print(await database.get_missions())
#     print(await database.get_notes())
#     print("Mision")
#     print(await database.get_mission(1))
#     # await database.delete_cat(4)
#     await database.update_cat_salary(2, 200)
#     print("Cat deleted")
#     print(await database.get_cat(2))
#     await database.shutdown()


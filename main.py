import asyncio
from typing import Union, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union

from services.db import Database
from models.models import Cat, Mission, Target, Note, StatusType
from utils.schemas import (
    CatCreate, CatResponse, TargetCreate, MissionCreate, 
    MissionResponse, TargetResponse, NoteCreate, NoteResponse,
    SalaryUpdate, StatusUpdate, CatAssignment
)

app = FastAPI(title="Cat Mission API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            
    allow_credentials=True,           
    allow_methods=["*"],              
    allow_headers=["*"],              
)

database = Database()

async def get_database():
    return database

@app.on_event("startup")
async def startup_event():
    await database.startup()

@app.on_event("shutdown")
async def shutdown_event():
    await database.shutdown()

# Cat endpoints
@app.post("/cats", response_model=CatResponse, status_code=201)
async def create_cat(cat_data: CatCreate, db: Database = Depends(get_database)):
    """Create a new cat"""
    try:
        cat = Cat(
            name=cat_data.name,
            years_of_experience=cat_data.years_of_experience,
            breed=cat_data.breed,
            salary=cat_data.salary
        )
        result = await db.create_cat(cat)
        return CatResponse(
            id=result['id'],
            name=result['name'],
            years_of_experience=result['years_of_experience'],
            breed=result['breed'],
            salary=result['salary']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cats", response_model=List[CatResponse])
async def get_cats(db: Database = Depends(get_database)):
    """Get all cats"""
    try:
        cats = await db.get_cats()
        return [CatResponse(
            id=cat['id'],
            name=cat['name'],
            years_of_experience=cat['years_of_experience'],
            breed=cat['breed'],
            salary=cat['salary']
        ) for cat in cats]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cats/{cat_id}", response_model=CatResponse)
async def get_cat(cat_id: int, db: Database = Depends(get_database)):
    """Get a specific cat by ID"""
    try:
        cat = await db.get_cat(cat_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Cat not found")
        return CatResponse(
            id=cat['id'],
            name=cat['name'],
            years_of_experience=cat['years_of_experience'],
            breed=cat['breed'],
            salary=cat['salary']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cats/{cat_id}")
async def delete_cat(cat_id: int, db: Database = Depends(get_database)):
    """Delete a cat by ID"""
    try:
        await db.delete_cat(cat_id)
        return {"message": "Cat deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/cats/{cat_id}/salary")
async def update_cat_salary(cat_id: int, salary_update: SalaryUpdate, db: Database = Depends(get_database)):
    """Update a cat's salary"""
    try:
        if cat_id <= 0:
            raise HTTPException(status_code=400, detail="Cat ID must be positive")
        
        # Check if cat exists
        cat = await db.get_cat(cat_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Cat not found")
        
        await db.update_cat_salary(cat_id, salary_update.salary)
        return {"message": "Cat salary updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Mission endpoints
@app.post("/missions", response_model=dict, status_code=201)
async def create_mission(mission_data: MissionCreate, db: Database = Depends(get_database)):
    """Create a new mission with targets"""
    try:
        if mission_data.assigned_cat:
            cat = await db.get_cat(mission_data.assigned_cat)
            if not cat:
                raise HTTPException(status_code=400, detail="Assigned cat does not exist")
        
        mission_id = await db.create_mission(mission_data)
        return {"mission_id": mission_id, "message": "Mission created successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/missions", response_model=List[MissionResponse])
async def get_missions(db: Database = Depends(get_database)):
    """Get all missions"""
    try:
        missions = await db.get_missions()
        return [MissionResponse(
            id=mission['id'],
            assigned_cat=mission['assigned_cat'],
            status=mission['status'],
            title=mission['title']
        ) for mission in missions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/missions/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: int, db: Database = Depends(get_database)):
    """Get a specific mission by ID"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return MissionResponse(
            id=mission['id'],
            assigned_cat=mission['assigned_cat'],
            status=mission['status'],
            title=mission['title']
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/missions/{mission_id}")
async def delete_mission(mission_id: int, db: Database = Depends(get_database)):
    """Delete a mission by ID"""
    try:
        await db.delete_mission(mission_id)
        return {"message": "Mission deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/missions/{mission_id}/assign-cat")
async def assign_cat_to_mission(mission_id: int, assignment: CatAssignment, db: Database = Depends(get_database)):
    """Assign a cat to a mission"""
    try:
        if mission_id <= 0:
            raise HTTPException(status_code=400, detail="Mission ID must be positive")
        
        cat = await db.get_cat(assignment.cat_id)
        if not cat:
            raise HTTPException(status_code=404, detail="Cat not found")
        
        await db.assign_cat_to_mission(mission_id, assignment.cat_id)
        return {"message": "Cat assigned to mission successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Target endpoints
@app.patch("/targets/{target_id}/status")
async def update_target_status(target_id: int, status_update: StatusUpdate, db: Database = Depends(get_database)):
    """Update target status"""
    try:
        if target_id <= 0:
            raise HTTPException(status_code=400, detail="Target ID must be positive")
        
        await db.update_target_status(target_id, status_update.status)
        return {"message": "Target status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# Note endpoints
@app.post("/notes", status_code=201)
async def create_note(note_data: NoteCreate, db: Database = Depends(get_database)):
    """Create a new note for a target"""
    try:
        note = Note(
            target_id=note_data.target_id,
            message=note_data.message
        )
        await db.create_note(note)
        return {"message": "Note created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/notes", response_model=List[NoteResponse])
async def get_notes(db: Database = Depends(get_database)):
    """Get all notes"""
    try:
        notes = await db.get_notes()
        return [NoteResponse(
            id=note['id'],
            target_id=note['target_id'],
            message=note['message']
        ) for note in notes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Cat Mission API", "version": "1.0.0"}
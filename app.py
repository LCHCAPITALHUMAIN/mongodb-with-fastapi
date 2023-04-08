import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio
from fastapi import APIRouter, Body, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
 

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range"],
)
@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
    app.mongodb = app.mongodb_client['qwant']


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class StudentModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="id")
    source_type: str = Field(...)
    source: str = Field(...)
    medium: str = Field(...)
    term: str = Field(...)
    content: str = Field(...)
    name: str = Field(...)
    geo: str = Field(...)
    target: str = Field(...)
    cl: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }


class UpdateStudentModel(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    course: Optional[str]
    gpa: Optional[float]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }


@app.get(
    "/posts", response_description="List all students", response_model=List[StudentModel]
)
async def list_account(request: Request, response: Response):
    tasks = []
    for doc in await request.app.mongodb["config"].find().to_list(length=100):
        # print(doc.get('_id'))
        doc['id'] = doc.get('_id')
        tasks.append(doc)
        response.headers["Content-Range"] = f"0-9/{len(tasks)}"
    return tasks

@app.get(
    "/posts/{id}", response_description="Get a single student", response_model=StudentModel
)
async def show_student(id: str, request: Request, response: Response):
    print(id)
    if (student := await request.app.mongodb["config"].find_one({"_id": ObjectId(id)})) is not None:
        student['id'] = student.get('_id')
        response.headers["Content-Range"] = f"0-9/{len(student)}"
        return student

    raise HTTPException(status_code=404, detail=f"config {id} not found")

import os
from fastapi import FastAPI, Body, HTTPException, status 
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

MONGODB_URL = "mongodb+srv://Andres:Nightwish2787@cluster0.wwtd0st.mongodb.net/test"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.misiontic 

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type = "string")

class DocumentModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    Autor: str = Field(...)
    Titulo: str = Field(...)
    Editorial: str = Field(...)
    Año: int = Field (..., le=2100)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "Autor": "Leithold L.",
                "Titulo": "El cálculo con geometría analítica",
                "Editorial": "Harla. Mexico",
                "Año": "1992"
            }
        }

class UpdateDocumentModel(BaseModel):
    Autor: Optional[str]
    Titulo: Optional[str]
    Editorial: Optional[str]
    Año: Optional[str]

#Métodos 

@app.post("/", response_description="Agregue una nueva referencia", response_model=DocumentModel)
async def create_reference(reference: DocumentModel = Body(...)):
    reference = jsonable_encoder(reference)
    new_reference = await db["documentos"].insert_one(reference)
    created_reference = await db["documentos"].find_one({"_id": new_reference.inserted_id} )
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_reference)

@app.get("/", response_description="Agregue todas las referencias", response_model=List[DocumentModel])
async def list_references():
    references = await db["documentos"].find().to_list(1000)
    return references

@app.get("/{id}", response_description="Get a single reference", response_model=DocumentModel)
async def show_reference(id: str):
    if(reference:= await db["documentos"].find_one({"_id": id}) ) is not None:
        return reference

    raise HTTPException(status_code=404, detail=f"reference {id} not found")

@app.put("/{id}", response_description="Update a reference", response_model=DocumentModel )
async def update_reference(id: str, reference: UpdateDocumentModel = Body(...)):
    reference = {k: v for k, v in reference.dict().items if v is not None}

    if len(reference) >= 1:
        update_result = await db["documentos"].update_one({"_id": id}, {"$set": reference})

        if update_result.modified_count == 1:

            if(
               update_reference := await db["documentos"].find_one({"_id": id}) 
            ) is not None:
                return update_reference

    if(existing_reference:= await db["documentos"].find_one({"_id": id})) is not None:
        return existing_reference

    raise HTTPException(status_code=404, detail = f"reference {id} not found")

@app.delete("/{id}", response_description="Elimine una referencia")
async def delete_reference(id: str):
    delete_result = await db["documentos"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"reference {id} not found")
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, Response
from typing import Annotated, Any
from random import randint
from sqlmodel import Field, Session, create_engine, SQLModel

class Campaign(SQLModel, table = True):
    campaign_id : int | None = Field(default = None, primary_key= True)
    name : str = Field(index = True)
    due_date : datetime | None = Field(default = None, index = True)
    created_at : datetime = Field(default = lambda: datetime.now(timezone.utc), nullable= True, index = True)
    
sqlite_file_name ="database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread" : False}
engine = create_engine(sqlite_url, connect_args = connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    
app = FastAPI(root_path="/api/v1", lifespan=lifespan)

data : Any= [
    {
        "campaign_name" : "Summer Launch",
        "campaign_id" : 1,
        "due_date" : datetime.now(),
        "created_at" : datetime.now()    
    },
    { 
        "campaign_name" : "Black Friday",
        "campaign_id" : 2,
        "due_date" : datetime.now(),
        "created_at" : datetime.now()
    }
]

@app.get("/")
async def root():
    return {"message" : "Hello world!"}

@app.get("/campaigns")
async def read_campaigns():
    return {"campaigns" : data}

@app.get("/campaigns/{id}")
async def read_campaign(id:int):
    for campaign in data:
        if campaign.get("campaign_id") == id:
            return {"campaign" : campaign}
    raise HTTPException(status_code=404)

@app.post("/campaigns")
async def create_campaign(body: dict[str, Any]):
    new : Any = {
        "campaign_id" : randint(100, 1000),
        "name" : body.get("name"),
        "due_date" : body.get("due_date"),
        "created_at" : datetime.now()
    }
    
    data.append(new)
    return {"campaign" : new}

@app.put("/campaigns/{id}")
async def update_campaign(id: int, body: dict[str, Any]):
    for index, campaign in enumerate(data):
        if campaign.get("campaign_id") == id:
            updated : Any = {
                "campaign_id" : id,
                "campaign_name" : body.get("name"),
                "due_date" : body.get("due_date"),
                "created_at" : campaign.get("created_at")
            }
            data[index] = updated
            return {"campaign" : updated}
    raise HTTPException(status_code=404)

@app.delete("/campaigns/{id}")
async def delete_campaign(id: int):
    for index, campaign in enumerate(data):
        if campaign.get("campaign_id") == id:
            data.pop(index)
            return Response(status_code=204)
    raise HTTPException(status_code=404)
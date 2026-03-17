from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Response
from typing import Annotated, Any, Generic, TypeVar
from random import randint
from pydantic import BaseModel
from sqlmodel import Field, Session, create_engine, SQLModel, select

class Campaigns(SQLModel, table = True):
    campaign_id : int | None = Field(default = None, primary_key= True)
    name : str = Field(index = True)
    due_date : datetime | None = Field(default = None, index = True)
    created_at : datetime = Field(default_factory = lambda: datetime.now(timezone.utc), nullable= True, index = True)
    
class CampaignsCreate(SQLModel):
    name : str
    due_date : datetime | None = None     


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
    with Session(engine) as session:
        if not session.exec(select(Campaigns)).first():
            session.add_all([
                Campaigns(name="Summer Campaign", due_date=datetime.now()),
                Campaigns(name="Black Friday Sale", due_date=datetime.now())
            ])
            session.commit()
    yield
    
app = FastAPI(root_path="/api/v1", lifespan=lifespan)

# data : Any= [
#     {
#         "campaign_name" : "Summer Launch",
#         "campaign_id" : 1,
#         "due_date" : datetime.now(),
#         "created_at" : datetime.now()    
#     },
#     { 
#         "campaign_name" : "Black Friday",
#         "campaign_id" : 2,
#         "due_date" : datetime.now(),
#         "created_at" : datetime.now()
#     }
# ]

T = TypeVar("T")
class APIResponse(BaseModel, Generic[T]):
    data : T

@app.get("/campaigns", response_model=APIResponse[list[Campaigns]])
async def read_campaigns(session: SessionDep):
    data = session.exec(select(Campaigns)).all()
    return {"data" : data}

@app.get("/campaigns/{id}", response_model=APIResponse[Campaigns])
async def read_campaign(id : int, session: SessionDep):
    data = session.get(Campaigns, id)
    if not data:
        raise HTTPException(status_code=404)
    return {"data" : data}

@app.post("/campaigns", status_code=201, response_model=APIResponse[Campaigns])
async def create_campaign(campaign: CampaignsCreate, session: SessionDep):
    db_campaign = Campaigns.model_validate(campaign)
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return {"data" : db_campaign}



# @app.get("/")
# async def root():
#     return {"message" : "Hello world!"}

# @app.get("/campaigns")
# async def read_campaigns():
#     return {"campaigns" : data}

# @app.get("/campaigns/{id}")
# async def read_campaign(id:int):
#     for campaign in data:
#         if campaign.get("campaign_id") == id:
#             return {"campaign" : campaign}
#     raise HTTPException(status_code=404)

# @app.post("/campaigns")
# async def create_campaign(body: dict[str, Any]):
#     new : Any = {
#         "campaign_id" : randint(100, 1000),
#         "name" : body.get("name"),
#         "due_date" : body.get("due_date"),
#         "created_at" : datetime.now()
#     }
    
#     data.append(new)
#     return {"campaign" : new}

# @app.put("/campaigns/{id}")
# async def update_campaign(id: int, body: dict[str, Any]):
#     for index, campaign in enumerate(data):
#         if campaign.get("campaign_id") == id:
#             updated : Any = {
#                 "campaign_id" : id,
#                 "campaign_name" : body.get("name"),
#                 "due_date" : body.get("due_date"),
#                 "created_at" : campaign.get("created_at")
#             }
#             data[index] = updated
#             return {"campaign" : updated}
#     raise HTTPException(status_code=404)

# @app.delete("/campaigns/{id}")
# async def delete_campaign(id: int):
#     for index, campaign in enumerate(data):
#         if campaign.get("campaign_id") == id:
#             data.pop(index)
#             return Response(status_code=204)
#     raise HTTPException(status_code=404)
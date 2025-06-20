import json
from dataclasses import asdict
from datetime import time, datetime
from typing import Optional

from fastapi import FastAPI, Request, Query, APIRouter
from fastapi.params import Path
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from cache import NsCached
from error import TreinSchaduwError, exception_handler
from logic import Result
from main import FinalResult
from ns import Journey, Stop
from utils import response_example

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# noinspection PyTypeChecker
app.add_exception_handler(TreinSchaduwError, exception_handler)

ns = NsCached()

web_router = APIRouter(tags=["website"])
api_router = APIRouter(prefix="/api", tags=["api"])


@web_router.get("/")
async def index(request: Request):
    stations = ns.get_stations()
    return templates.TemplateResponse(
        request=request, name="index.html", context={"stations": stations}
    )


@web_router.get("/result")
async def result_page(request: Request, trip: int,
                      from_: Optional[str] = Query(None, alias='from'),
                      to: Optional[str] = None):
    journey = ns.get_result(trip, None, from_, to)
    stations = list(filter(lambda s: s.departure is not None or s.arrival is not None, journey.stops))
    return templates.TemplateResponse(
        request=request, name="result.html",
        context={
            "result": json.dumps([asdict(r) for r in journey.result], default=str),
            "journey": journey,
            "trip": trip,
            "from": from_,
            "to": to,
            "left_time": round(journey.left / 60),
            "right_time": round(journey.right / 60),
            "left_percentage": round(journey.left / journey.duration * 100),
            "right_percentage": round(journey.right / journey.duration * 100),
            "stations": stations,
        }
    )


@api_router.get("/stations", response_model=list[list[str]],
                responses=response_example([["UT", "Utrecht Centraal"], ["UTLN", "Utrecht Lunetten"]]))
async def get_stations():
    stations = ns.get_stations()
    return stations


@api_router.get("/search/{from}/{to}", response_model=list[Journey])
async def search(from_: str = Path(alias='from'), to: str = Path(...), dep_time: Optional[time] = None):
    if dep_time is not None:
        dep_timestamp = datetime.today()
        dep_timestamp = dep_timestamp.replace(hour=dep_time.hour, minute=dep_time.minute, second=0, microsecond=0)
    else:
        dep_timestamp = None
    journeys = ns.get_from_stations(from_, to, dep_timestamp)
    return journeys


class ApiResult(BaseModel):
    trip: int
    from_: str = Field(alias="from")
    to: str
    left_time: int
    right_time: int
    left_percentage: int
    right_percentage: int
    stations: list[Stop]
    journey: FinalResult

    class Config:
        validate_by_name = True


@api_router.get("/result/{trip}", response_model=ApiResult)
async def result(trip: int, from_: Optional[str] = Query(None, alias='from'),
                 to: Optional[str] = None):
    journey = ns.get_result(trip, None, from_, to)
    stations = list(filter(lambda s: s.departure is not None or s.arrival is not None, journey.stops))
    return ApiResult(
        trip=trip,
        from_=from_,
        to=to,
        left_time=round(journey.left / 60),
        right_time=round(journey.right / 60),
        left_percentage=round(journey.left / journey.duration * 100),
        right_percentage=round(journey.right / journey.duration * 100),
        stations=stations,
        journey=journey,
    )


app.include_router(web_router)
app.include_router(api_router)

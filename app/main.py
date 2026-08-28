from __future__ import annotations
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from .db import init_db, insert_vin_data, fetch_vin_data, delete_vin_data
from .vpic_client import get_vin_data
from .parquet_utils import export_to_parquet


# Basic app setup
init_db()
app = FastAPI(title="VIN lookup cache service",
              description="A simple service to cache VIN lookups from the vPIC API",
              version="0.1.0")


# To allow Pydantic to validate the responses from lookup_vin
class VINData(BaseModel):
    Input_VIN: str = Field(alias="Input VIN")
    Make: str
    Model: str
    Model_Year: str = Field(alias="Model Year")
    Body_Class: str = Field(alias="Body Class")
    cached: bool

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/lookup/{vin}", response_model=VINData)
def lookup_vin(vin: str) -> dict[str, str]:
    """
    Checks the cache for VIN data, if it is not found, then it tries to obtain the VIN data from
    the vPIC API, stores that data in the cache, and then returns the data to the user
    """
    # This validates the requirements laid out in the assessment document https://github.com/acrisuretechnology/nas-eng-assessment
    if len(vin) != 17:
        raise HTTPException(status_code=400, detail="valid VINs are 17 characters long")
    if not vin.isalnum():
        raise HTTPException(status_code=400, detail="valid VINs must be alphanumeric")

    data = fetch_vin_data(vin)
    if data is None:
        # This could raise a ValueError from insert_vin_data, but there is an exception handler below
        # to catch that and return the appropriate 500 response
        data = get_vin_data(vin)
        insert_vin_data(vin, data["Make"], data["Model"],
                        data["Model Year"], data["Body Class"])
        ret = {"Input VIN": vin, "Make": data["Make"], "Model": data["Model"],
                "Model Year": data["Model Year"], "Body Class": data["Body Class"],
                "cached": False}

    else:
        ret = {"Input VIN": vin, "Make": data["make"], "Model": data["model"],
               "Model Year": data["model_year"], "Body Class": data["body_class"],
               "cached": True}
    return ret


@app.get("/remove/{vin}")
def remove_vin(vin: str) -> dict[str, str | bool]:
    """
    Removes VIN data from the cache if it exists, returns a boolean indicating whether the deletion was successful or not
    """
    # This validates the requirements laid out in the assessment document https://github.com/acrisuretechnology/nas-eng-assessment
    if len(vin) != 17:
            raise HTTPException(status_code=400, detail="valid VINs are 17 characters long")
    if not vin.isalnum():
        raise HTTPException(status_code=400, detail="valid VINs must be alphanumeric")

    success = delete_vin_data(vin)
    # Successful being that this VIN was in the database and then removed
    # Unsuccessful being that this VIN was not in the database and therefore could not be removed
    return {"Input VIN": vin, "Delete Successful": success}


@app.get("/export")
def export_cache():
    """
    Exports the SQLite3 cache to a parquet file, then returns that file to the user as a download
    """
    # This only needs to have the most recent version of the cache, so it can overwrite the existing file if it exists
    file_path = "cache.parquet"
    # "Overwrite" by just deleting the file if it exists, then creating a new one
    Path(file_path).unlink(missing_ok=True)
    export_to_parquet(file_path)

    # application/vnd.apache.parquet might not be supported everywhere, could use application/octet-stream
    return FileResponse(path=file_path,
                        filename="VINcache.parquet",
                        media_type="application/vnd.apache.parquet")


@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc: ValueError):
    """
    FastAPI exception handler
    The ValuError can be raised by the vPIC client
    """
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error when communicating with vPIC API", "error": str(exc)},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    """
    FastAPI exception handler
    This is a catch-all for any unhandled exceptions from trying to write/read a parquet file
    """
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)},
    )

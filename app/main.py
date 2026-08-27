from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .db import init_db, insert_vin_data, fetch_vin_data, delete_vin_data
from .vpic_client import get_vin_data


init_db()
app = FastAPI(title="VIN lookup cache service",
              description="A simple service to cache VIN lookups from the vPIC API",
              version="0.1.0")


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
def lookup_vin(vin: str) -> dict[str, str] | None:
    if len(vin) != 17:
        raise HTTPException(status_code=400, detail="valid VINs are 17 characters long")
    if not vin.isalnum():
        raise HTTPException(status_code=400, detail="valid VINs must be alphanumeric")

    data = fetch_vin_data(vin)
    if data is None:
        try:
            data = get_vin_data(vin)
            # Add check here to make sure we have valid VIN data
            insert_vin_data(vin, data["Make"], data["Model"],
                            data["Model Year"], data["Body Class"])
            ret = {"Input VIN": vin, "Make": data["Make"], "Model": data["Model"],
                   "Model Year": data["Model Year"], "Body Class": data["Body Class"],
                   "cached": False}
        except ValueError as e:
            # Could probably remove the try/except block 
           raise
    else:
        ret = {"Input VIN": vin, "Make": data["make"], "Model": data["model"],
               "Model Year": data["model_year"], "Body Class": data["body_class"],
               "cached": True}
    return ret


@app.get("/remove/{vin}")
def remove_vin(vin: str) -> dict[str, str | bool]:
    if len(vin) != 17:
            raise HTTPException(status_code=400, detail="valid VINs are 17 characters long")
    if not vin.isalnum():
        raise HTTPException(status_code=400, detail="valid VINs must be alphanumeric")

    success = delete_vin_data(vin)
    # This would be where I would add logging to indicate whether the deletion was successful or not
    # Successful being that this VIN was in the database and then removed
    # Unsuccessful being that this VIN was not in the database and therefore could not be removed
    return {"Input VIN": vin, "Delete Successful": success}


# TODO - implement the exporting cache to parquet blob
@app.get("/export")
def export_cache():
    pass


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

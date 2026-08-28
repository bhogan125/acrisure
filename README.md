# VIN Data Cache Service
(Acrisure NAS backend coding task)

This is a REST service that stores data about VINs in a SQLite cache, and returns that information to users who request it. When a user requests data about a VIN, the cache is checked first, and if that VIN is not in the cache, then the service will reach out to the vPIC API to gather data about the VIN, store it, and return the relevant data to the user.

By default, the service will run on localhost over port 8000 (`http://127.0.0.1:8000/`)

## VIN Data Stored
While vPIC offers a huge amount of data for each VIN (roughly 140 different data points), this service only stores, and returns to the user, 4 data points for each VIN:

* Make
* Model
* Model Year
* Body Class

## Build and Deploy
This service currently uses the default uvicorn process to run

```
# cd to the repo, create a python virtual environment, and install the requirements
python -m venv .venv
source ./.venv/bin/activate
pip install -r requirements.txt

# To actually run the service
uvicorn app.main:app
```

It will then be available at `http://127.0.0.1:8000/`

## API Endpoints
### Lookup
`GET http://127.0.0.1:8000/lookup/{vin}`

`Example Response - {"Input VIN":"1XPWD40X1ED215307","Make":"PETERBILT","Model":"388","Model Year":"2014","Body Class":"Truck-Tractor","cached":true}`


### Remove
`GET http://127.0.0.1:8000/remove/{vin}`

`Example Response - {"Input VIN":"1XPWD40X1ED215307","Delete Successful":false}`

### Export
`GET http://127.0.0.1:8000/export`

This will send a downloadable file to the user named VINcache.parquet
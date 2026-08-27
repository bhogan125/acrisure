# Simple client to interact with the vPIC API
# In a real application, this service would undoubtedly interact with more parts of this API
# Hence why creating a dedicated client for this API
import requests

base_url = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{}?format=json"
# The only attributes that this service needs to extract and store
attrs = ['Make', 'Model', 'Model Year', 'Body Class']

def get_vin_data(vin: str) -> dict:
    ret = {"Input VIN": vin}
    resp = requests.get(base_url.format(vin))
    if resp.status_code == 200:
        data = resp.json()
        if 'Results' not in data:  # TODO - logging
            raise ValueError("Invalid response from vPIC API")

        for i in data['Results']:
            if i['Variable'] in attrs:
                ret[i['Variable']] = i['Value']
        return ret
    else:
        raise ValueError("Failed to fetch VIN data from vPIC API")

import json
import requests
import os
import sys
from blaseball_mike.models import SimulationData

def get_ballpark_data(outputpath):
    sim = SimulationData.load()
    filename = "stadiumsS{}preD{}.json".format(sim.season, sim.day + 1)
    stadium_data = requests.get("https://api.sibr.dev/chronicler/v1/stadiums").json()['data']
    stadiums = {
        row["data"]["teamId"]: {
            key: value for key, value in row["data"].items() if type(value) in (float, int)
        } for row in stadium_data
    }
    with open(os.path.join(outputpath, filename), "w") as f:
        json.dump(stadiums, f)
    return filename

if __name__ == "__main__":
    get_ballpark_data(sys.argv[1])


import json
import re

from fastapi import FastAPI

import matplotlib.pyplot as plt

from update import getYears, import_data_to_sqlalchemy

app = FastAPI()

# db = fetchDB()

event_names = {}

performance_names = {}

with open("database.json", "r") as f:
    db = json.load(f)
    for year in db:
        for event in db[year]["events"]:
            if not event_names.__contains__(re.split(r'\d', event.rstrip("Canoa"), maxsplit=1)[0]):
                event_names[re.split(r'\d', event.rstrip("Canoa"), maxsplit=1)[0]] = 1
            else:
                event_names[re.split(r'\d', event.rstrip("Canoa"), maxsplit=1)[0]] += 1

            for heat in db[year]["events"][event]["heats"]:
                for foo in db[year]["events"][event]["heats"][heat]["performances"]:
                    if not (str(foo["PlaName"]).__len__() <= 1 or str(foo["PlaSurname"]).__len__() <= 1): # per filtrare le società
                        if not performance_names.__contains__(foo["PlaName"] + " " + foo["PlaSurname"]):
                            performance_names[(foo["PlaName"] + " " + foo["PlaSurname"])] = 1
                        else:
                            performance_names[(foo["PlaName"] + " " + foo["PlaSurname"])] += 1


max = 0
max_name = ""

for name in event_names:
    if event_names[name] > max:
        max = event_names[name]
        max_name = name

print(max_name)
print(max)

max_performances = 0
max_performances_name = ""

for name in performance_names:
    if performance_names[name] > max_performances:
        max_performances = performance_names[name]
        max_performances_name = name

print(max_performances_name)
print(max_performances)

# Use the function with your database
import_data_to_sqlalchemy(db)

@app.get("/athlete/{name}")
async def get_athlete_information(name: str):
    athlete = {}
    athlete["event_performances"] = {}
    athlete["races_done"] = []
    athlete["race_count"] = 0
    athlete["placements"] = {}
    with open("database.json", "r") as f:
        db = json.load(f)
        for year in db:
            for event in db[year]["events"]:
                if not event_names.__contains__(re.split(r'\d', event.rstrip("Canoa"), maxsplit=1)[0]):
                    event_names[re.split(r'\d', event.rstrip("Canoa"), maxsplit=1)[0]] = 1
                else:
                    event_names[re.split(r'\d', event.rstrip("Canoa"), maxsplit=1)[0]] += 1

                for heat in db[year]["events"][event]["heats"]:
                    for foo in db[year]["events"][event]["heats"][heat]["performances"]:
                        performance_name = foo["PlaName"] + " " + foo["PlaSurname"]

                        if(name.lower() == performance_name.lower()):
                            if len(foo["MemQual"]) <= 1:
                                if not athlete["placements"].__contains__(foo["PlaCls"]):
                                    athlete["placements"][foo["PlaCls"]] = 1
                                else:
                                    athlete["placements"][foo["PlaCls"]] += 1

                            if not athlete["event_performances"].__contains__(db[year]["events"][event]["heats"][heat]["event"]):
                                athlete["event_performances"][db[year]["events"][event]["heats"][heat]["event"]] = []

                            actually_meaningful_data = {}
                            actually_meaningful_data["b"] = foo["b"]
                            actually_meaningful_data["PlaCls"] = foo["PlaCls"]
                            actually_meaningful_data["PlaLane"] = foo["PlaLane"]
                            actually_meaningful_data["PlaBat"] = foo["PlaBat"]
                            actually_meaningful_data["PlaCod"] = foo["PlaCod"]
                            actually_meaningful_data["PlaTeamCod"] = foo["PlaTeamCod"]
                            actually_meaningful_data["TeamDescrIta"] = foo["TeamDescrIta"]
                            actually_meaningful_data["PlaName"] = foo["PlaName"]
                            actually_meaningful_data["PlaSurname"] = foo["PlaSurname"]
                            actually_meaningful_data["PlaBirth"] = foo["PlaBirth"]
                            actually_meaningful_data["MemPrest"] = foo["MemPrest"]
                            actually_meaningful_data["MemQual"] = foo["MemQual"]

                            athlete["event_performances"][db[year]["events"][event]["heats"][heat]["event"]].append(actually_meaningful_data)

                            athlete["race_count"] += 1

                            if not athlete["races_done"].__contains__(event):
                                athlete["races_done"].append(event)

                        if str(foo["PlaName"]).__len__() <= 1 or str(foo["PlaSurname"]).__len__() <= 1:  # per filtrare le società
                            try:
                                for ath in foo["Players"]:
                                    player_name = ath["PlaName"] + " " + ath["PlaSurname"]
                                    if name.lower() == player_name.lower():
                                        if len(foo["MemQual"]) <= 1:
                                            if not athlete["placements"].__contains__(foo["PlaCls"]):
                                                athlete["placements"][foo["PlaCls"]] = 1
                                            else:
                                                athlete["placements"][foo["PlaCls"]] += 1

                                        if not athlete["event_performances"].__contains__(
                                                db[year]["events"][event]["heats"][heat]["event"]):
                                            athlete["event_performances"][
                                                db[year]["events"][event]["heats"][heat]["event"]] = []

                                        actually_meaningful_data = {}
                                        actually_meaningful_data["b"] = foo["b"]
                                        actually_meaningful_data["PlaCls"] = foo["PlaCls"]
                                        actually_meaningful_data["PlaLane"] = foo["PlaLane"]
                                        actually_meaningful_data["PlaBat"] = foo["PlaBat"]
                                        actually_meaningful_data["PlaCod"] = foo["PlaCod"]
                                        actually_meaningful_data["PlaTeamCod"] = foo["PlaTeamCod"]
                                        actually_meaningful_data["TeamDescrIta"] = foo["TeamDescrIta"]
                                        actually_meaningful_data["PlaName"] = foo["PlaName"]
                                        actually_meaningful_data["PlaSurname"] = foo["PlaSurname"]
                                        actually_meaningful_data["PlaBirth"] = foo["PlaBirth"]
                                        actually_meaningful_data["MemPrest"] = foo["MemPrest"]
                                        actually_meaningful_data["MemQual"] = foo["MemQual"]
                                        actually_meaningful_data["Players"] = foo["Players"] # TODO: ottimizzare in modo che non mandi tutti i dati inutili

                                        athlete["event_performances"][
                                            db[year]["events"][event]["heats"][heat]["event"]].append(
                                            actually_meaningful_data)

                                        athlete["race_count"] += 1

                                        if not athlete["races_done"].__contains__(event):
                                            athlete["races_done"].append(event)
                            except KeyError:
                                pass

    temp = list(athlete["placements"].keys())
    keysArray = []
    print(temp)
    for key in temp:
        if len(keysArray) == 0:
            keysArray.append(key)
            continue

        inserted = False
        for bar in range(len(keysArray)):
            if has_numbers(key):
                if has_numbers(keysArray[bar]):
                    if int(key) < int(keysArray[bar]):
                        keysArray.insert(bar, key)
                        inserted = True
                        break
                else:
                    keysArray.insert(bar, key)
                    inserted = True
                    break
            else:
                if not has_numbers(keysArray[bar]):
                    if key < keysArray[bar]:
                        keysArray.insert(bar, key)
                        inserted = True
                        break

        if not inserted:
            keysArray.append(key)






    valuesArray = []
    for key in keysArray:
        valuesArray.append(athlete["placements"][key])
    

    print(keysArray)
    print(valuesArray)

    plt.plot(keysArray, valuesArray)
    plt.style.use("ggplot")

    capitalized_name = ""
    for part in name.split(" "):
        capitalized_name += " " + part.capitalize()
    plt.title(capitalized_name + " placement history")
    plt.show()

    return athlete

@app.get("/")
async def root():
    years = ""
    for year in getYears():
        years += f"{year}, "

    years = years[:-2]
    return {"message": years}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)
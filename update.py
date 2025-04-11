import csv
import datetime
import json

import requests

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, Float, ForeignKey

# Create an engine that connects to a SQLite database file
engine = create_engine('sqlite:///database.db', echo=True)

# Create a base class for our models
Base = declarative_base()

# Create a session factory
Session = sessionmaker(bind=engine)

# Create all tables defined by our models
Base.metadata.create_all(engine)

yearURL = "https://apimanvarie.ficr.it/VAR/mpcache-30/get/schedule/{year}/*/19"

database = dict()

def getYears():
    return range(2022, datetime.datetime.now().year + 1) # prima del 2020 c'erano i PDF, prima del 2022 i codici erano diversi

def fetchDB():
    years = getYears()
    database = {}  # Initialize the database dictionary

    for year in years:
        # Initialize structure for this year
        database[year] = {"events": {}}

        # Get year data
        req = requests.get(yearURL.replace("{year}", str(year)))
        year_data = req.json()["data"]

        # Process events for this year
        for event in year_data:
            event_code = event["CodicePub"].replace(" ", "")

            # Get event details
            try:
                req = requests.get(f"https://apicanoavelocita.ficr.it/CAV/mpcache-30/get/programdate/{event_code}")
                event_data = req.json()["data"]

                # Initialize events dictionary for this event code
                database[year]["events"][event_code] = {"heats": {}}

                # Process each program date entry
                for program_date in event_data:
                    if "e" in program_date:
                        # Process each heat in this program
                        for heat in program_date["e"]:
                            heat_id = str(heat["c0"]) + "_" + str(heat["c1"]) + "_" + str(heat["c2"]) + "_" + str(heat["c3"])

                            # Initialize the heat dictionary
                            if heat_id not in database[year]["events"][event_code]["heats"]:
                                database[year]["events"][event_code]["heats"][heat_id] = {"performances": []}

                            database[year]["events"][event_code]["heats"][heat_id]["event"] = heat["d_it"]

                            # Get performance details
                            try:
                                performance_url = f"https://apicanoavelocita.ficr.it/CAV/mpcache-10/get/result/{event_code}/KY/{heat['c0']}/{heat['c1']}/{heat['c2'][1:]}/{heat['c3']}"
                                req = requests.get(performance_url)
                                result_data = req.json()["data"]

                                # Add performances to the heat
                                if isinstance(result_data, dict) and "data" in result_data:
                                    database[year]["events"][event_code]["heats"][heat_id]["performances"].extend(
                                        result_data["data"])
                            except requests.exceptions.RequestException as e:
                                print(f"Error fetching performance data: {e}")
                            except Exception as e:  # Catch other exceptions like JSON parsing errors
                                print(f"Error processing performance data: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching event data: {e}")
            except Exception as e:
                print(f"Error processing event data: {e}")

    return database



def fetch():
    # Prima di tutto serve la lista degli anni, sarebbe da usare l'api ma è fatta male e non tutti gli anni sono fatti allo stesso modo.
    years = getYears()

    events = []

    for year in years:
        req = requests.get(yearURL.replace("{year}", str(year)))
        database[year] = req.json()["data"]
        events.extend(req.json()["data"])

    print(f"fetched {len(events)} events")

    heats = {}

    for event in events:
        req = requests.get("https://apicanoavelocita.ficr.it/CAV/mpcache-30/get/programdate/" + event["CodicePub"].replace(" ", ""))
        for foo in req.json()["data"]:
            heats[event["CodicePub"]] = foo["e"]

    performances = []

    for performance in heats:
        for foo in heats[performance]:
            try:
                req = requests.get(f"https://apicanoavelocita.ficr.it/CAV/mpcache-10/get/result/{performance.replace(" ", "")}/KY/{foo["c0"]}/{foo["c1"]}/{foo["c2"][1:]}/{foo["c3"]}")
            except requests.exceptions.RequestException as e:
                print(e)
            if type(req.json()["data"]) == dict and "data" in req.json()["data"]:
                performances.extend(req.json()["data"]["data"])

    print(f"fetched {len(performances)} performances")

    with open("performances.json", "w") as f:
        f.write("{[")
        for i in range(len(performances)):
            f.write("\t" + str(performances[i]) + "\n")
            if(i != len(performances)-1):
                f.write(",")
        f.write("]}")

    for performance in performances:
        if "PlaName" in performance and "PlaSurname" in performance:
            if performance["PlaName"] == "Federico" and performance["PlaSurname"] == "TOLUZZO":
                print(f"{performance["PlaName"]} {performance["PlaSurname"]} {performance["PlaBirth"]} {performance["TeamDescrIta"]} {performance["PlaCls"]} {performance["MemPrest"]} {performance["Gap"]}")


def import_data_to_sqlalchemy(db_dict):
    session = Session()

    try:
        # Process each year
        for year_number in db_dict:
            year_obj = Year(year_number=int(year_number))
            session.add(year_obj)

            # Process each event in this year
            for event_code, event_data in db_dict[year_number]["events"].items():
                event_obj = Event(code=event_code, year=year_obj)
                session.add(event_obj)

                # Process each heat in this event
                for heat_id, heat_data in event_data["heats"].items():
                    heat_obj = Heat(heat_id=heat_id, event=event_obj)
                    session.add(heat_obj)

                    # Process each performance in this heat
                    for perf_data in heat_data["performances"]:
                        perf_obj = Performance(
                            heat=heat_obj,

                            # Using your exact field mappings
                            placement=perf_data.get("PlaCls"),
                            lane=perf_data.get("PlaLane"),
                            teamID=perf_data.get("PlaTeamCod"),
                            team=perf_data.get("TeamDescrIta"),
                            surname=perf_data.get("PlaSurname"),
                            name=perf_data.get("PlaName"),
                            birth=perf_data.get("PlaBirth"),
                            gap=perf_data.get("Gap"),
                            time=perf_data.get("MemPrest"),
                            score=perf_data.get("MemPoint"),
                            outcome=perf_data.get("MemQual")
                        )
                        session.add(perf_obj)

        session.commit()
        print("Data import completed successfully")

    except Exception as e:
        session.rollback()
        print(f"Error importing data: {e}")

    finally:
        session.close()

class Year(Base):
    __tablename__ = 'years'

    id = Column(Integer, primary_key=True)
    year_number = Column(Integer, unique=True)

    # Relationship: one year has many events
    events = relationship("Event", back_populates="year", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Year({self.year_number})"


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String)  # Optional additional data

    # Foreign key to associate with year
    year_id = Column(Integer, ForeignKey('years.id'))

    # Relationships
    year = relationship("Year", back_populates="events")
    heats = relationship("Heat", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Event({self.code})"


class Heat(Base):
    __tablename__ = 'heats'

    id = Column(Integer, primary_key=True)
    heat_id = Column(String, nullable=False)
    # Add any other heat-specific fields you might have

    # Foreign key to associate with event
    event_id = Column(Integer, ForeignKey('events.id'))

    # Relationships
    event = relationship("Event", back_populates="heats")
    performances = relationship("Performance", back_populates="heat", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Heat({self.heat_id})"


class Performance(Base):
    __tablename__ = 'performances'

    id = Column(Integer, primary_key=True)

    # The fields you specified as important
    placement = Column(Integer, nullable=True)  # PlaCls
    lane = Column(Integer, nullable=True)  # PlaLane
    team_id = Column(String, nullable=True)  # PlaTeamCod
    team_name = Column(String, nullable=True)  # TeamDescrIta
    surname = Column(String, nullable=True)  # PlaSurname
    name = Column(String, nullable=True)  # PlaName
    birth_year = Column(Integer, nullable=True)  # PlaBirth
    gap = Column(String, nullable=True)  # Gap
    time = Column(String, nullable=True)  # MemPrest
    score = Column(Float, nullable=True)  # MemPoint
    outcome = Column(String, nullable=True)  # MemQual

    # Foreign key to associate with heat
    heat_id = Column(Integer, ForeignKey('heats.id'))

    # Relationship
    heat = relationship("Heat", back_populates="performances")

    def __repr__(self):
        return f"Performance({self.name} {self.surname}, Time: {self.time}, Placement: {self.placement})"


#db = fetchDB()

#with open("database.json", "w") as f:
#    json.dump(db, f)
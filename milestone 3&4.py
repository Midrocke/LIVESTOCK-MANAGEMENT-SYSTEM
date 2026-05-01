import json, os
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict

print("\n=== WELCOME TO JKUAT FARM SYSTEM ===")

MILK_PRICE = 60
EGG_PRICE = 15
FEED_COST = 50
INITIAL_FEED = 3000
INITIAL_WATER = 4000

class HealthStatus(Enum):
    HEALTHY = "Healthy"
    SICK = "Sick"

class Species(Enum):
    COW = "COW"
    GOAT = "GOAT"
    CHICKEN = "CHICKEN"

@dataclass
class Vaccination:
    name: str
    due_day: int
    done: bool = False

class Livestock(ABC):
    def __init__(self, aid, species, weight, feed):
        self.id = aid
        self.species = species
        self.weight = weight
        self.feed = feed
        self.health = HealthStatus.HEALTHY
        self.vaccinations: List[Vaccination] = []

    def add_vaccine(self, name, day):
        self.vaccinations.append(Vaccination(name, day))

    def check_vaccine(self, day):
        return [v for v in self.vaccinations if v.due_day == day and not v.done]

    def vaccinate(self, day):
        for v in self.vaccinations:
            if v.due_day == day:
                v.done = True

    def vaccination_status(self):
        status = []
        for v in self.vaccinations:
            state = "Done" if v.done else f"Due {v.due_day}"
            status.append(f"{v.name}:{state}")
        return ", ".join(status)

    @abstractmethod
    def produce(self): pass

    @abstractmethod
    def water_usage(self): pass

class Cow(Livestock):
    def produce(self): return self.weight * 0.02
    def water_usage(self): return 30

class Goat(Livestock):
    def produce(self): return self.weight * 0.015
    def water_usage(self): return 15

class Chicken(Livestock):
    def produce(self): return 1
    def water_usage(self): return 5

class Herd:
    def __init__(self):
        self.animals: List[Livestock] = []

    def add(self, animal):
        self.animals.append(animal)

    def remove(self, aid=None):
        self.animals = [a for a in self.animals if a.id != aid]

    def find(self, aid):
        for a in self.animals:
            if a.id == aid:
                return a
        return None

class Analytics:
    def __init__(self):
        self.records: Dict[int, Dict] = {}

    def record(self, day, data):
        self.records[day] = data

    def get(self, day):
        return self.records.get(day)

def ensure_dataset():
    if not os.path.exists("animals.json"):
        data = [
            {"id":"C0","species":"COW","weight":250,"feed":6},
            {"id":"C1","species":"COW","weight":230,"feed":5.5},
            {"id":"G0","species":"GOAT","weight":80,"feed":2.5},
            {"id":"H0","species":"CHICKEN","weight":2,"feed":0.3}
        ]
        with open("animals.json","w") as f:
            json.dump(data, f, indent=2)

def load_data(herd):
    try:
        with open("animals.json") as f:
            data = json.load(f)
        for item in data:
            sp = Species[item["species"]]
            if sp == Species.COW:
                a = Cow(item["id"], sp, item["weight"], item["feed"])
            elif sp == Species.GOAT:
                a = Goat(item["id"], sp, item["weight"], item["feed"])
            else:
                a = Chicken(item["id"], sp, item["weight"], item["feed"])
            a.add_vaccine("Routine", 3)
            a.add_vaccine("Booster", 7)
            herd.add(a)
    except Exception as e:
        print(f"Error loading data: {e}")

class Farm:
    def __init__(self):
        self.day = 0
        self.feed = INITIAL_FEED
        self.water = INITIAL_WATER
        self.revenue = 0
        self.herd = Herd()
        self.analytics = Analytics()

    def simulate_day(self):
        if len(self.herd.animals) == 0:
            print("No animals to simulate")
            return
        self.day += 1
        rev = 0
        alerts = []
        total_milk = 0.0
        total_eggs = 0

        for a in self.herd.animals:
            if self.feed < a.feed:
                print("Not enough feed!")
                return
            self.feed -= a.feed
            self.water -= a.water_usage()

            prod = a.produce()

            if a.species == Species.CHICKEN:
                total_eggs += int(prod)
                rev += prod * EGG_PRICE
            else:
                total_milk += prod
                rev += prod * MILK_PRICE

            due = a.check_vaccine(self.day)
            if due:
                alerts.append(f"{a.id} due vaccination")
            a.vaccinate(self.day)

        self.revenue += rev

        livestock_snapshot = [
            {
                "id": a.id,
                "species": a.species.value,
                "weight": a.weight,
                "vaccination": a.vaccination_status()
            } for a in self.herd.animals
        ]

        self.analytics.record(self.day, {
            "revenue": rev,
            "feed": self.feed,
            "water": self.water,
            "alerts": alerts,
            "livestock": livestock_snapshot,
            "milk": round(total_milk, 2),
            "eggs": total_eggs,
        })
        print(f"Day {self.day} simulated successfully")

    def restock_feed(self, amount):
        self.feed += amount
        print(f"Feed restocked by {amount}. Total feed: {self.feed}")

    def report(self, day):
        if day > self.day:
            print("Invalid day")
            return
        r = self.analytics.get(day)
        if not r:
            print("No data")
            return
        print(f"\n=== DAY {day} REPORT ===")
        print(f"Feed: {r['feed']} | Water: {r['water']}")
        if r['feed'] < 500:
            print("⚠ RESTOCK FEED!")
        else:
            print("✅ Feed sufficient for next day")

        milk_rev  = round(r['milk']  * MILK_PRICE, 2)
        egg_rev   = round(r['eggs']  * EGG_PRICE,  2)
        total_rev = round(milk_rev + egg_rev, 2)

        print("\n╔══════════════════════════════════════════════════════╗")
        print( "║              REVENUE BREAKDOWN                       ║")
        print( "╠══════════════════════════════════════════════════════╣")
        print(f"║  Milk : {r['milk']:>7.2f} L   x  KES {MILK_PRICE:<5} = KES {milk_rev:>8.2f}  ║")
        print(f"║  Eggs : {r['eggs']:>7}     x  KES {EGG_PRICE:<5} = KES {egg_rev:>8.2f}  ║")
        print( "╠══════════════════════════════════════════════════════╣")
        print(f"║  TOTAL REVENUE                        KES {total_rev:>8.2f}  ║")
        print( "╚══════════════════════════════════════════════════════╝")

        print("\n╔════════════════ LIVESTOCK ════════════════╗")
        for a in r['livestock']:
            print(f"║ {a['id']} | {a['species']} | W:{a['weight']} | {a['vaccination']}")
        print("╚═══════════════════════════════════════════╝")

        print("\n--- ALERTS ---")
        for alert in r['alerts']:
            print("⚠", alert)

    def _next_id(self, species: Species) -> str:
        prefix_map = {
            Species.COW: "C",
            Species.GOAT: "G",
            Species.CHICKEN: "H",
        }
        prefix = prefix_map[species]
        existing = [a.id for a in self.herd.animals if a.id.startswith(prefix)]
        if not existing:
            return f"{prefix}0"
        nums = []
        for eid in existing:
            try:
                nums.append(int(eid[len(prefix):]))
            except ValueError:
                pass
        next_num = max(nums) + 1 if nums else 0
        return f"{prefix}{next_num}"

    def add_animal(self, species, weight, feed):
        new_id = self._next_id(species)
        if species == Species.COW:
            a = Cow(new_id, species, weight, feed)
        elif species == Species.GOAT:
            a = Goat(new_id, species, weight, feed)
        else:
            a = Chicken(new_id, species, weight, feed)
        a.add_vaccine("Routine", self.day + 2)
        self.herd.add(a)
        print(f"Animal added with ID: {new_id}")

    def sell_animal(self, aid, price):
        if self.herd.find(aid):
            self.herd.remove(aid)
            self.revenue += price
            print(f"Animal {aid} sold for {price}")
        else:
            print("Animal not found")

    def sell_product(self, product, qty):
        if product == "milk":
            self.revenue += qty * MILK_PRICE
        elif product == "eggs":
            self.revenue += qty * EGG_PRICE
        print(f"Sold {qty} units of {product}")

def get_species():
    while True:
        sp = input("Species(cow/goat/chicken): ").upper()
        if sp in Species.__members__:
            return Species[sp]
        print("Invalid species. Try: cow, goat, or chicken")

farm = Farm()
ensure_dataset()
load_data(farm.herd)

def menu():
    print("""
╔════════════════════════════╗
║     JKUAT FARM SYSTEM      ║
╠════════════════════════════╣
║ 1.Add Animal              ║
║ 2.Simulate Day            ║
║ 3.View Report             ║
║ 4.Sell (submenu)          ║
║ 5.Restock Feed            ║
║ 0.Exit                    ║
╚════════════════════════════╝
""")

def sell_menu():
    print("""
--- SELL MENU ---
1. Sell Animal
2. Sell Milk
3. Sell Eggs
""")

while True:
    menu()
    c = input("Select: ")

    if c == "1":
        sp = get_species()
        w = float(input("Weight: "))
        f = float(input("Feed: "))
        farm.add_animal(sp, w, f)

    elif c == "2":
        farm.simulate_day()

    elif c == "3":
        d = int(input("Day: "))
        farm.report(d)

    elif c == "4":
        sell_menu()
        sc = input("Choice: ")
        if sc == "1":
            aid = input("Animal ID: ")
            price = float(input("Price: "))
            farm.sell_animal(aid, price)
        elif sc == "2":
            qty = float(input("Milk (L): "))
            farm.sell_product("milk", qty)
        elif sc == "3":
            qty = int(input("Eggs: "))
            farm.sell_product("eggs", qty)

    elif c == "5":
        amt = float(input("Feed amount: "))
        farm.restock_feed(amt)

    elif c == "0":
        break
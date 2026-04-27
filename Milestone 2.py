import random

# =========================
# ANIMAL CLASS
# =========================
class Animal:
    def __init__(self, aid, species, breed, age, weight, health,
                 feed, water, milk=0.0, eggs=0, preg=False, preg_days=0):
        self.id, self.species, self.breed = aid, species, breed
        self.age, self.weight = age, weight
        self.health = health
        self.feed, self.water = feed, water
        self.milk, self.eggs = milk, eggs
        self.preg, self.preg_days = preg, preg_days

        self.gestation = {"Cow":280,"Goat":150,"Sheep":145,"Chicken":21}
        self.gain = {"Healthy":0.3 if species=="Cow" else 0.15 if species=="Goat" else 0.05,
                     "Sick":-0.2,"Dead":0}

    def update(self):
        if self.health == "Dead": return
        self.age += 1

        if self.health == "Healthy":
            self.weight += self.gain["Healthy"]

        elif self.health == "Sick":
            self.weight = max(1, self.weight + self.gain["Sick"])
            self.milk = max(0, self.milk - 0.5)
            if self.species == "Chicken": self.eggs = 0

        elif self.health == "Recovering":
            self.weight += self.gain["Healthy"]/2
            if self.species in ("Cow","Goat"): self.milk += 0.2

        if self.preg:
            self.preg_days += 1
            if self.preg_days >= self.gestation.get(self.species,280):
                self.preg, self.preg_days = False, 0
                return f"{self.id} gave birth!"

    def treat(self):
        if self.health == "Sick":
            self.health = "Recovering"
            return True
        return False

    def revenue(self, mp, ep):
        if self.health == "Dead": return 0
        return (self.milk * mp if self.species in ("Cow","Goat") else 0) + \
               (self.eggs * ep if self.species=="Chicken" and self.health=="Healthy" else 0)

    def cost(self, fp): return self.feed * fp

    def critical(self):
        return self.health=="Sick" or (self.weight<5 and self.species!="Chicken")

# =========================
# FARM CLASS
# =========================
class Farm:
    FP, MP, EP, MED = 50, 60, 15, 200

    def __init__(self, name, feed, water, meds):
        self.name, self.feed, self.water, self.meds = name, feed, water, meds
        self.rev = self.cost = self.day = 0
        self.herd, self.log = [], []

    def add(self, a): self.herd.append(a)

    def get(self, aid):
        return next((a for a in self.herd if a.id.upper()==aid.upper()), None)

    def simulate(self):
        self.day += 1
        d_rev = d_cost = 0

        for a in self.herd:
            if a.health == "Dead": continue

            event = a.update()
            if event: self.log.append(f"Day {self.day}: {event}")

            self.feed = max(0, self.feed - a.feed)
            self.water = max(0, self.water - a.water)

            d_cost += a.cost(self.FP)
            d_rev  += a.revenue(self.MP, self.EP)

        self.cost += d_cost
        self.rev  += d_rev
        return d_rev, d_cost

    def treat(self, aid):
        a = self.get(aid)
        if not a: return "Not found"
        if self.meds<=0: return "No medicine"
        if not a.treat(): return "Not sick"
        self.meds -= 1
        self.cost += self.MED
        return "Treated"

    def status(self):
        net = self.rev - self.cost
        print(f"\nDay {self.day} | Feed:{self.feed} | Water:{self.water} | Med:{self.meds}")
        print(f"Revenue:{self.rev} Cost:{self.cost} Net:{net}")

# =========================
# INPUT HELPERS
# =========================
def get_int(p, mn=0): 
    while True:
        try:
            v=int(input(p))
            if v<mn: raise ValueError
            return v
        except: print("Invalid")

def get_float(p, mn=0):
    while True:
        try:
            v=float(input(p))
            if v<mn: raise ValueError
            return v
        except: print("Invalid")

def yn(p): return input(p+" (y/n): ").lower().startswith("y")

# =========================
# SETUP
# =========================
def setup():
    name = input("Farm name: ") or "Farm"
    return Farm(name,
                get_float("Feed: "),
                get_float("Water: "),
                get_int("Medicine: "))

def add_animals(f):
    species_list = ["Cow","Goat","Sheep","Chicken"]

    while yn("Add animal?"):
        sp = input(f"Species {species_list}: ").capitalize()
        aid = f"{sp[:3].upper()}-{len([a for a in f.herd if a.species==sp])+1:03}"

        a = Animal(
            aid, sp,
            input("Breed: "), 
            get_int("Age: ",1),
            get_float("Weight: ",0.5),
            input("Health (Healthy/Sick/Recovering): ").capitalize(),
            get_float("Feed/day: ",0.1),
            get_float("Water/day: ",0.1),
            get_float("Milk: ",0) if sp!="Chicken" else 0,
            get_int("Eggs (0/1): ",0) if sp=="Chicken" else 0,
            yn("Pregnant?"),
            get_int("Preg days: ",0)
        )
        f.add(a)

# =========================
# MENU
# =========================
def menu(f):
    while True:
        print("\n1.Next Day 2.Multi 3.Status 4.Treat 0.Exit")
        c = input("Choice: ")

        if c=="1":
            r,cost=f.simulate()
            print("Day done:",r-cost)

        elif c=="2":
            for _ in range(get_int("Days:",1)): f.simulate()

        elif c=="3": f.status()

        elif c=="4":
            print(f.treat(input("Animal ID: ")))

        elif c=="0": break

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    farm = setup()
    add_animals(farm)
    menu(farm)

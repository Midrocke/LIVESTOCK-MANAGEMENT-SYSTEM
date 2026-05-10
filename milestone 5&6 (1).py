
import json, os
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, TypeVar, Generic
from functools import reduce
import threading
import time

print("\n=== WELCOME TO JKUAT FARM SYSTEM ===")

MILK_PRICE   = 60
EGG_PRICE    = 15
FEED_COST    = 50
INITIAL_FEED = 3000
INITIAL_WATER= 4000

class HealthStatus(Enum):
    HEALTHY = "Healthy"
    SICK    = "Sick"

class Species(Enum):
    COW     = "COW"
    GOAT    = "GOAT"
    CHICKEN = "CHICKEN"

@dataclass
class Vaccination:
    name:    str
    due_day: int
    done:    bool = False

class Livestock(ABC):
    def __init__(self, aid, species, weight, feed):
        self.id      = aid
        self.species = species
        self.weight  = weight
        self.feed    = feed
        self.health  = HealthStatus.HEALTHY
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
    def produce(self):      return self.weight * 0.02
    def water_usage(self):  return 30

class Goat(Livestock):
    def produce(self):      return self.weight * 0.015
    def water_usage(self):  return 15

class Chicken(Livestock):
    def produce(self):      return 1
    def water_usage(self):  return 5

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
            {"id":"C0","species":"COW",    "weight":250,"feed":6  },
            {"id":"C1","species":"COW",    "weight":230,"feed":5.5},
            {"id":"G0","species":"GOAT",   "weight":80, "feed":2.5},
            {"id":"H0","species":"CHICKEN","weight":2,  "feed":0.3}
        ]
        with open("animals.json","w") as f:
            json.dump(data, f, indent=2)

def load_data(herd):
    try:
        with open("animals.json") as f:
            data = json.load(f)
        for item in data:
            sp = Species[item["species"]]
            if   sp == Species.COW:     a = Cow    (item["id"], sp, item["weight"], item["feed"])
            elif sp == Species.GOAT:    a = Goat   (item["id"], sp, item["weight"], item["feed"])
            else:                       a = Chicken(item["id"], sp, item["weight"], item["feed"])
            a.add_vaccine("Routine", 3)
            a.add_vaccine("Booster", 7)
            herd.add(a)
    except Exception as e:
        print(f"Error loading data: {e}")

class Farm:
    def __init__(self):
        self.day     = 0
        self.feed    = INITIAL_FEED
        self.water   = INITIAL_WATER
        self.revenue = 0
        self.herd    = Herd()
        self.analytics = Analytics()

    def simulate_day(self):
        if len(self.herd.animals) == 0:
            print("No animals to simulate"); return
        self.day += 1
        rev = 0
        alerts = []
        total_milk = 0.0
        total_eggs = 0

        for a in self.herd.animals:
            if self.feed < a.feed:
                print("Not enough feed!"); return
            self.feed  -= a.feed
            self.water -= a.water_usage()
            prod = a.produce()

            if a.species == Species.CHICKEN:
                total_eggs += int(prod)
                rev        += prod * EGG_PRICE
            else:
                total_milk += prod
                rev        += prod * MILK_PRICE

            due = a.check_vaccine(self.day)
            if due:
                alerts.append(f"{a.id} due vaccination")
            a.vaccinate(self.day)

        self.revenue += rev

        livestock_snapshot = [
            {"id": a.id, "species": a.species.value,
             "weight": a.weight, "vaccination": a.vaccination_status()}
            for a in self.herd.animals
        ]

        self.analytics.record(self.day, {
            "revenue":   rev,
            "feed":      self.feed,
            "water":     self.water,
            "alerts":    alerts,
            "livestock": livestock_snapshot,
            "milk":      round(total_milk, 2),
            "eggs":      total_eggs,
        })
        print(f"Day {self.day} simulated successfully")

    def restock_feed(self, amount):
        self.feed += amount
        print(f"Feed restocked by {amount}. Total feed: {self.feed}")

    def report(self, day):
        if day > self.day:
            print("Invalid day"); return
        r = self.analytics.get(day)
        if not r:
            print("No data"); return

        print(f"\n=== DAY {day} REPORT ===")
        print(f"Feed: {r['feed']} | Water: {r['water']}")
        if r['feed'] < 500:
            print("⚠ RESTOCK FEED!")
        else:
            print("✅ Feed sufficient for next day")

        milk_rev  = round(r['milk'] * MILK_PRICE, 2)
        egg_rev   = round(r['eggs'] * EGG_PRICE,  2)
        total_rev = round(milk_rev + egg_rev, 2)

        print(f"\n  Milk : {r['milk']:.2f} L  x  KES {MILK_PRICE} = KES {milk_rev:.2f}")
        print(f"  Eggs : {r['eggs']}      x  KES {EGG_PRICE} = KES {egg_rev:.2f}")
        print(f"  TOTAL REVENUE: KES {total_rev:.2f}")

        for a in r['livestock']:
            print(f"  {a['id']} | {a['species']} | W:{a['weight']} | {a['vaccination']}")

        for alert in r['alerts']:
            print("⚠", alert)

    def _next_id(self, species: Species) -> str:
        prefix_map = {Species.COW:"C", Species.GOAT:"G", Species.CHICKEN:"H"}
        prefix   = prefix_map[species]
        existing = [a.id for a in self.herd.animals if a.id.startswith(prefix)]
        if not existing: return f"{prefix}0"
        nums = []
        for eid in existing:
            try:   nums.append(int(eid[len(prefix):]))
            except ValueError: pass
        return f"{prefix}{(max(nums)+1 if nums else 0)}"

    def add_animal(self, species, weight, feed):
        new_id = self._next_id(species)
        if   species == Species.COW:     a = Cow    (new_id, species, weight, feed)
        elif species == Species.GOAT:    a = Goat   (new_id, species, weight, feed)
        else:                            a = Chicken(new_id, species, weight, feed)
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
        if   product == "milk": self.revenue += qty * MILK_PRICE
        elif product == "eggs": self.revenue += qty * EGG_PRICE
        print(f"Sold {qty} units of {product}")

def get_species():
    while True:
        sp = input("Species (cow/goat/chicken): ").upper()
        if sp in Species.__members__:
            return Species[sp]
        print("Invalid. Try: cow, goat, or chicken")

farm = Farm()
ensure_dataset()
load_data(farm.herd)

T = TypeVar("T")

class ResultCache(Generic[T]):
    def __init__(self):
        self._lock  = threading.Lock()
        self._value: T = None

    def set(self, value: T):
        with self._lock:
            self._value = value

    def get(self) -> T:
        with self._lock:
            return self._value

revenue_cache: ResultCache[float] = ResultCache()

class SimMode(Enum):
    MANUAL     = "manual"
    CONCURRENT = "concurrent"

_sim_lock = threading.Lock()

def threaded_simulate(farm_obj):
    with _sim_lock:
        farm_obj.simulate_day()
        revenue_cache.set(farm_obj.revenue)

def background_sensor(farm_obj, interval=2, cycles=3):
    for i in range(cycles):
        time.sleep(interval)
        cached_rev = revenue_cache.get()
        print(f"  [SENSOR {i+1}/{cycles}] Feed={farm_obj.feed:.0f}kg | "
              f"Water={farm_obj.water:.0f}L | Revenue=KES {cached_rev or 0:.2f}")

def run_concurrent_simulation(farm_obj):
    print("\n--- Concurrent simulation starting ---")
    sim_t    = threading.Thread(target=threaded_simulate,  args=(farm_obj,), daemon=False)
    sensor_t = threading.Thread(target=background_sensor, args=(farm_obj,), daemon=True)
    sensor_t.start()
    sim_t.start()
    sim_t.join()
    print(f"[CONCURRENT] Day {farm_obj.day} done. "
          f"Cached revenue: KES {revenue_cache.get():.2f}")

milk_revenue  = lambda litres: round(litres * MILK_PRICE, 2)
egg_revenue   = lambda count:  round(count  * EGG_PRICE,  2)
total_revenue = lambda records: reduce(
    lambda acc, r: acc + r.get("revenue", 0), records, 0.0
)

def farm_summary_lambda(farm_obj):
    records = list(farm_obj.analytics.records.values())
    if not records:
        print("No simulation data yet."); return
    total    = total_revenue(records)
    avg      = round(total / len(records), 2)
    best_day = max(records, key=lambda r: r["revenue"])
    print(f"\n=== FUNCTIONAL SUMMARY (M5) ===")
    print(f"Days simulated  : {len(records)}")
    print(f"Total revenue   : KES {total:.2f}")
    print(f"Average/day     : KES {avg:.2f}")
    print(f"Best day revenue: KES {best_day['revenue']:.2f}")
    print(f"Milk revenue fn : KES {milk_revenue(best_day['milk']):.2f}")
    print(f"Egg  revenue fn : KES {egg_revenue(best_day['eggs']):.2f}")

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False


# ╔══════════════════════════════════════════════════════════════════╗
# ║         MILESTONE 6 — COSMIC DARK GUI (REDESIGNED)             ║
# ╚══════════════════════════════════════════════════════════════════╝

class FarmGUI:
    """
    JKUAT Farm Management System — Cosmic Dark Edition
    Aesthetic: Deep space / observatory — obsidian backgrounds, aurora
    accents (violet → cyan → gold), subtle star-field canvas, and
    a monospace terminal feel blended with refined serif headings.
    """

    # ── Colour palette: deep space ──────────────────────────────────
    BG          = "#07090f"   # near-black void
    PANEL       = "#0d1117"   # dark panel — GitHub-dark inspired
    CARD        = "#111827"   # raised card surface
    CARD2       = "#161f2e"   # slightly lighter card
    BORDER      = "#1e3a5f"   # muted cobalt border
    BORDER2     = "#2d4a7a"   # brighter border for active areas

    # Aurora accent colours
    VIOLET      = "#a78bfa"   # soft violet — primary accent
    CYAN        = "#22d3ee"   # electric cyan
    GOLD        = "#fbbf24"   # warm gold — money / revenue
    ROSE        = "#f43f5e"   # rose-red — sell / danger
    MINT        = "#34d399"   # mint green — success / OK
    SKY         = "#38bdf8"   # sky blue — water
    ORANGE      = "#fb923c"   # warm orange — alerts

    TEXT        = "#e2e8f0"   # near-white primary text
    TEXT2       = "#94a3b8"   # slate secondary text
    TEXT3       = "#64748b"   # dim tertiary / placeholders

    LOG_BG      = "#050709"   # terminal black
    LOG_FG      = "#7dd3fc"   # terminal sky-blue text
    ENTRY_BG    = "#0f172a"   # entry dark blue
    ENTRY_FG    = "#e2e8f0"
    SEL_BG      = "#1e40af"   # deep blue selection
    ROW_ODD     = "#0d1117"
    ROW_EVEN    = "#111827"

    # ── Typography ──────────────────────────────────────────────────
    # Palatino + Courier: observatory logbook aesthetic
    HEADING_FONT = ("Palatino Linotype", 14, "bold")
    SUBHEAD_FONT = ("Palatino Linotype", 10, "bold")
    LABEL_FONT   = ("Palatino Linotype", 9)
    BTN_FONT     = ("Palatino Linotype", 9, "bold")
    MONO_FONT    = ("Courier New", 9)
    MONO_BOLD    = ("Courier New", 9, "bold")
    SECTION_FONT = ("Courier New", 8, "bold")

    def __init__(self, root: "tk.Tk", farm_obj: Farm):
        self.root = root
        self.farm = farm_obj

        root.title("✦ JKUAT Farm · Cosmic Dashboard ✦")
        root.geometry("1120x720")
        root.minsize(920, 620)
        root.resizable(True, True)
        root.configure(bg=self.BG)

        self._setup_styles()
        self._build_ui()

    # ── ttk style configuration ─────────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        # Primary violet button
        s.configure("Farm.TButton",
            background=self.VIOLET, foreground="#0d0d1a",
            font=self.BTN_FONT, relief="flat", padding=(10, 6), borderwidth=0)
        s.map("Farm.TButton",
            background=[("active","#c4b5fd"),("pressed","#7c3aed")],
            foreground=[("active","#0d0d1a")])

        # Gold button — reports / revenue
        s.configure("Gold.TButton",
            background=self.GOLD, foreground="#1a0f00",
            font=self.BTN_FONT, relief="flat", padding=(10, 6), borderwidth=0)
        s.map("Gold.TButton",
            background=[("active","#fde68a"),("pressed","#d97706")],
            foreground=[("active","#1a0f00")])

        # Rose/red danger button
        s.configure("Danger.TButton",
            background=self.ROSE, foreground="#fff0f3",
            font=self.BTN_FONT, relief="flat", padding=(10, 6), borderwidth=0)
        s.map("Danger.TButton",
            background=[("active","#fb7185"),("pressed","#be123c")],
            foreground=[("active","#fff0f3")])

        # Cyan — concurrent / special
        s.configure("Cyan.TButton",
            background=self.CYAN, foreground="#001a1f",
            font=self.BTN_FONT, relief="flat", padding=(10, 6), borderwidth=0)
        s.map("Cyan.TButton",
            background=[("active","#67e8f9"),("pressed","#0891b2")],
            foreground=[("active","#001a1f")])

        # Entry
        s.configure("Farm.TEntry",
            fieldbackground=self.ENTRY_BG,
            foreground=self.ENTRY_FG,
            insertcolor=self.VIOLET,
            bordercolor=self.BORDER,
            lightcolor=self.BORDER2,
            darkcolor=self.BORDER,
            font=self.LABEL_FONT)

        # Treeview
        s.configure("Farm.Treeview",
            background=self.ROW_EVEN,
            fieldbackground=self.ROW_EVEN,
            foreground=self.TEXT,
            font=self.MONO_FONT,
            rowheight=26,
            borderwidth=0)
        s.configure("Farm.Treeview.Heading",
            background=self.CARD2,
            foreground=self.VIOLET,
            font=self.SECTION_FONT,
            relief="flat", borderwidth=0)
        s.map("Farm.Treeview",
            background=[("selected", self.SEL_BG)],
            foreground=[("selected","#ffffff")])

        s.configure("Farm.Vertical.TScrollbar",
            background=self.CARD, troughcolor=self.BG,
            arrowcolor=self.VIOLET, borderwidth=0)

        s.configure("Farm.TSeparator", background=self.BORDER)

    # ── Helpers ─────────────────────────────────────────────────────
    def _lbl(self, parent, text, font=None, fg=None, anchor="w", pady=0, bg=None):
        return tk.Label(parent, text=text,
                        font=font or self.LABEL_FONT,
                        fg=fg or self.TEXT2,
                        bg=bg or self.PANEL,
                        anchor=anchor, pady=pady)

    def _section_label(self, parent, text):
        """Glowing section divider label."""
        tk.Label(parent, text=text,
                 font=self.SECTION_FONT,
                 fg=self.CYAN,
                 bg=self.PANEL,
                 pady=7, padx=10, anchor="w").pack(fill="x")

    def _style_optionmenu(self, menu):
        menu.config(bg=self.ENTRY_BG, fg=self.ENTRY_FG,
                    activebackground=self.CARD2,
                    activeforeground=self.VIOLET,
                    highlightthickness=1,
                    highlightbackground=self.BORDER2,
                    relief="flat", font=self.LABEL_FONT,
                    indicatoron=True)
        menu["menu"].config(bg=self.CARD, fg=self.TEXT,
                            activebackground=self.SEL_BG,
                            activeforeground="#ffffff",
                            font=self.LABEL_FONT)

    # ── Star-field canvas background ────────────────────────────────
    def _draw_stars(self, canvas, w, h):
        """Draw random stars on a canvas for a space-field background."""
        import random
        random.seed(42)
        for _ in range(180):
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.choice([0.5, 0.5, 0.5, 1, 1, 1.5])
            brightness = random.choice(["#1e3a5f","#2d4a7a","#3b5998",
                                        "#64748b","#94a3b8","#ffffff"])
            canvas.create_oval(x-r, y-r, x+r, y+r, fill=brightness, outline="")

        # Nebula smear — a few large blurred ovals via layered circles
        for ox, oy, col in [(200,80,"#1e1040"),(500,50,"#0a2040"),(900,120,"#1a0a30")]:
            for dr in range(30, 0, -5):
                canvas.create_oval(ox-dr*2, oy-dr, ox+dr*2, oy+dr,
                                   fill=col, outline="", stipple="gray25")

    # ── Main UI builder ─────────────────────────────────────────────
    def _build_ui(self):

        # ═══════════════════════════════════════════════════════════
        # HEADER — deep space banner with star canvas
        # ═══════════════════════════════════════════════════════════
        header_frame = tk.Frame(self.root, bg=self.PANEL,
                                highlightbackground=self.BORDER2,
                                highlightthickness=1)
        header_frame.pack(fill="x")

        # Star-field canvas behind header content
        hdr_canvas = tk.Canvas(header_frame, bg=self.PANEL,
                               height=62, highlightthickness=0)
        hdr_canvas.pack(fill="x")
        hdr_canvas.update_idletasks()
        cw = hdr_canvas.winfo_reqwidth() or 1120
        self._draw_stars(hdr_canvas, cw, 62)

        # Title text on canvas
        hdr_canvas.create_text(18, 31, anchor="w",
                               text="✦  JKUAT FARM MANAGEMENT SYSTEM",
                               font=self.HEADING_FONT,
                               fill=self.VIOLET)
        hdr_canvas.create_text(20, 50, anchor="w",
                               text="Cosmic Edition · Livestock Intelligence Platform",
                               font=("Courier New", 7),
                               fill=self.TEXT3)

        # Stat cards — overlaid on canvas via a frame window
        stats_outer = tk.Frame(hdr_canvas, bg=self.PANEL)
        hdr_canvas.create_window(cw - 10, 31, anchor="e", window=stats_outer)

        self.day_var   = tk.StringVar(value="DAY  0")
        self.rev_var   = tk.StringVar(value="KES  0.00")
        self.feed_var  = tk.StringVar(value="3000 kg")
        self.water_var = tk.StringVar(value="4000 L")

        card_defs = [
            ("◷", self.day_var,   self.VIOLET, "Day"),
            ("◈", self.rev_var,   self.GOLD,   "Revenue"),
            ("⬡", self.feed_var,  self.MINT,   "Feed"),
            ("◉", self.water_var, self.SKY,    "Water"),
        ]
        for icon, var, colour, _ in card_defs:
            card = tk.Frame(stats_outer, bg=self.CARD2,
                            highlightbackground=self.BORDER2,
                            highlightthickness=1)
            card.pack(side="left", padx=3, pady=6, ipadx=8, ipady=3)
            tk.Label(card, text=icon, bg=self.CARD2,
                     fg=colour, font=("Courier New", 11)).pack(side="left", padx=(4,2))
            tk.Label(card, textvariable=var,
                     font=("Courier New", 9, "bold"),
                     fg=colour, bg=self.CARD2).pack(side="left", padx=(0,4))

        # ═══════════════════════════════════════════════════════════
        # BODY — sidebar + content
        # ═══════════════════════════════════════════════════════════
        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill="both", expand=True)

        # ── SIDEBAR ─────────────────────────────────────────────────
        sidebar = tk.Frame(body, bg=self.PANEL, width=230,
                           highlightbackground=self.BORDER,
                           highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(6,3), pady=6)
        sidebar.pack_propagate(False)

        # Thin colour bar along the left edge of the sidebar
        accent_bar = tk.Frame(sidebar, bg=self.VIOLET, width=3)
        accent_bar.place(x=0, y=0, relheight=1)

        # ── SIMULATION section ──
        self._section_label(sidebar, "⬡  SIMULATION")

        ttk.Button(sidebar, text="▶  Simulate Day",
                   style="Farm.TButton",
                   command=self._on_simulate).pack(fill="x", padx=(14,10), pady=(0,3))
        ttk.Button(sidebar, text="⚡  Concurrent  [M5]",
                   style="Cyan.TButton",
                   command=self._on_concurrent).pack(fill="x", padx=(14,10), pady=(0,6))

        ttk.Separator(sidebar, style="Farm.TSeparator",
                      orient="horizontal").pack(fill="x", padx=10, pady=4)

        # ── REPORTS section ──
        self._section_label(sidebar, "◈  REPORTS")

        ttk.Button(sidebar, text="◎  View Day Report",
                   style="Gold.TButton",
                   command=self._on_report).pack(fill="x", padx=(14,10), pady=(0,3))
        ttk.Button(sidebar, text="∑  Func. Summary  [M5]",
                   style="Gold.TButton",
                   command=self._on_summary).pack(fill="x", padx=(14,10), pady=(0,6))

        ttk.Separator(sidebar, style="Farm.TSeparator",
                      orient="horizontal").pack(fill="x", padx=10, pady=4)

        # ── ADD ANIMAL section ──
        self._section_label(sidebar, "✦  ADD ANIMAL")

        self._lbl(sidebar, "Species").pack(anchor="w", padx=14)
        self.species_var = tk.StringVar(value="COW")
        sp_menu = tk.OptionMenu(sidebar, self.species_var, "COW","GOAT","CHICKEN")
        self._style_optionmenu(sp_menu)
        sp_menu.pack(fill="x", padx=(14,10), pady=(0,3))

        self._lbl(sidebar, "Weight (kg)").pack(anchor="w", padx=14)
        self.weight_entry = ttk.Entry(sidebar, style="Farm.TEntry")
        self.weight_entry.insert(0,"200")
        self.weight_entry.pack(fill="x", padx=(14,10), pady=(0,3))

        self._lbl(sidebar, "Feed (kg/day)").pack(anchor="w", padx=14)
        self.feed_entry = ttk.Entry(sidebar, style="Farm.TEntry")
        self.feed_entry.insert(0,"5")
        self.feed_entry.pack(fill="x", padx=(14,10), pady=(0,4))

        ttk.Button(sidebar, text="＋  Add Animal",
                   style="Farm.TButton",
                   command=self._on_add_animal).pack(fill="x", padx=(14,10), pady=(0,6))

        ttk.Separator(sidebar, style="Farm.TSeparator",
                      orient="horizontal").pack(fill="x", padx=10, pady=4)

        # ── RESTOCK FEED section ──
        self._section_label(sidebar, "⬡  RESTOCK FEED")

        self.restock_entry = ttk.Entry(sidebar, style="Farm.TEntry")
        self.restock_entry.insert(0,"500")
        self.restock_entry.pack(fill="x", padx=(14,10), pady=(0,3))
        ttk.Button(sidebar, text="↑  Restock Feed",
                   style="Farm.TButton",
                   command=self._on_restock).pack(fill="x", padx=(14,10), pady=(0,6))

        ttk.Separator(sidebar, style="Farm.TSeparator",
                      orient="horizontal").pack(fill="x", padx=10, pady=4)

        # ── SELL ANIMAL section ──
        self._section_label(sidebar, "◉  SELL ANIMAL")

        self._lbl(sidebar, "Animal ID").pack(anchor="w", padx=14)
        self.sell_id_entry = ttk.Entry(sidebar, style="Farm.TEntry")
        self.sell_id_entry.pack(fill="x", padx=(14,10), pady=(0,3))

        self._lbl(sidebar, "Price (KES)").pack(anchor="w", padx=14)
        self.sell_price_entry = ttk.Entry(sidebar, style="Farm.TEntry")
        self.sell_price_entry.insert(0,"5000")
        self.sell_price_entry.pack(fill="x", padx=(14,10), pady=(0,4))

        ttk.Button(sidebar, text="↗  Sell Animal",
                   style="Danger.TButton",
                   command=self._on_sell_animal).pack(fill="x", padx=(14,10), pady=(0,8))

        # ── CONTENT AREA ────────────────────────────────────────────
        content = tk.Frame(body, bg=self.BG)
        content.pack(side="right", fill="both", expand=True, padx=(3,6), pady=6)

        # ── Herd table card ──
        tbl_card = tk.Frame(content, bg=self.CARD,
                            highlightbackground=self.BORDER2,
                            highlightthickness=1)
        tbl_card.pack(fill="x", pady=(0,5))

        # Card header strip
        tbl_head = tk.Frame(tbl_card, bg=self.CARD2)
        tbl_head.pack(fill="x")
        tk.Label(tbl_head, text="◷  HERD REGISTER",
                 font=("Courier New", 9, "bold"),
                 fg=self.VIOLET, bg=self.CARD2,
                 pady=6, padx=12, anchor="w").pack(side="left")
        # Coloured right-side pill
        tk.Label(tbl_head, text=" LIVESTOCK  ",
                 font=("Courier New", 7, "bold"),
                 fg=self.BG, bg=self.VIOLET,
                 pady=2, padx=6).pack(side="right", padx=8, pady=6)

        cols = ("ID", "Species", "Weight (kg)", "Vaccinations")
        self.tree = ttk.Treeview(tbl_card, columns=cols,
                                 show="headings", height=5,
                                 style="Farm.Treeview")
        widths = {"ID":55, "Species":90, "Weight (kg)":100, "Vaccinations":380}
        for c in cols:
            self.tree.heading(c, text=c.upper())
            self.tree.column(c, width=widths[c], anchor="center")

        self.tree.tag_configure("odd",  background=self.ROW_ODD)
        self.tree.tag_configure("even", background=self.ROW_EVEN)

        vsb = ttk.Scrollbar(tbl_card, orient="vertical",
                             command=self.tree.yview,
                             style="Farm.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="x", expand=True, padx=(8,0), pady=(4,8))
        vsb.pack(side="right", fill="y", pady=(4,8), padx=(0,6))

        # ── Output log card ──
        log_card = tk.Frame(content, bg=self.CARD,
                            highlightbackground=self.BORDER2,
                            highlightthickness=1)
        log_card.pack(fill="both", expand=True)

        log_head = tk.Frame(log_card, bg=self.CARD2)
        log_head.pack(fill="x")
        tk.Label(log_head, text="⌨  SYSTEM LOG",
                 font=("Courier New", 9, "bold"),
                 fg=self.CYAN, bg=self.CARD2,
                 pady=6, padx=12, anchor="w").pack(side="left")
        tk.Label(log_head, text=" LIVE  ",
                 font=("Courier New", 7, "bold"),
                 fg=self.BG, bg=self.MINT,
                 pady=2, padx=6).pack(side="right", padx=8, pady=6)

        self.log = scrolledtext.ScrolledText(
            log_card, state="disabled",
            font=self.MONO_FONT,
            bg=self.LOG_BG, fg=self.LOG_FG,
            insertbackground=self.CYAN,
            selectbackground=self.SEL_BG,
            selectforeground="#ffffff",
            relief="flat", borderwidth=0,
            wrap="word")
        self.log.pack(fill="both", expand=True, padx=8, pady=(0,8))

        # ── Status footer ──
        footer = tk.Frame(self.root, bg=self.CARD2,
                          highlightbackground=self.BORDER,
                          highlightthickness=1)
        footer.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="System ready. All subsystems online.")
        # Left status
        tk.Label(footer, textvariable=self.status_var,
                 font=("Courier New", 8),
                 fg=self.TEXT2, bg=self.CARD2,
                 pady=4, padx=12, anchor="w").pack(side="left", fill="x", expand=True)
        # Right badge
        tk.Label(footer, text="JKUAT FMS · Cosmic v6.0  ",
                 font=("Courier New", 7),
                 fg=self.TEXT3, bg=self.CARD2,
                 pady=4, padx=8).pack(side="right")

        # Populate on startup
        self._refresh_table()
        self._log("  ╔══════════════════════════════════════════════╗\n")
        self._log("  ║  JKUAT Farm Management System  — Cosmic GUI  ║\n")
        self._log("  ║  All systems nominal. Welcome, operator.      ║\n")
        self._log("  ╚══════════════════════════════════════════════╝\n\n")

    # ── Event handlers ──────────────────────────────────────────────
    def _on_simulate(self):
        self.farm.simulate_day()
        self._refresh_all()
        self._log(f"  ▶  Day {self.farm.day} complete. "
                  f"Revenue: KES {self.farm.revenue:,.2f}\n")
        self._set_status(f"Day {self.farm.day} simulated successfully.")

    def _on_concurrent(self):
        self._set_status("⚡ Concurrent simulation running…")
        t = threading.Thread(target=self._run_concurrent_bg, daemon=False)
        t.start()

    def _run_concurrent_bg(self):
        run_concurrent_simulation(self.farm)
        self.root.after(0, self._refresh_after_concurrent)

    def _refresh_after_concurrent(self):
        self._refresh_all()
        self._log(f"  ⚡  Concurrent day {self.farm.day} done. "
                  f"Cached revenue: KES {revenue_cache.get():.2f}\n")
        self._set_status(f"Concurrent day {self.farm.day} complete.")

    def _on_report(self):
        if self.farm.day == 0:
            messagebox.showinfo("No Data", "Simulate at least one day first.")
            return
        day = self._ask_int("View Report", f"Enter day (1 – {self.farm.day}):")
        if day is None: return
        self._capture_and_log(lambda: self.farm.report(day))
        self._set_status(f"Report for day {day} displayed.")

    def _on_summary(self):
        self._capture_and_log(lambda: farm_summary_lambda(self.farm))
        self._set_status("Functional summary displayed.")

    def _on_add_animal(self):
        try:
            sp     = Species[self.species_var.get()]
            weight = float(self.weight_entry.get())
            feed   = float(self.feed_entry.get())
        except (ValueError, KeyError) as e:
            messagebox.showerror("Input Error", str(e)); return
        self.farm.add_animal(sp, weight, feed)
        self._refresh_table()
        self._log(f"  ＋  Added {sp.value}  wt={weight}kg  feed={feed}kg/day\n")
        self._set_status(f"Added {sp.value} to herd.")

    def _on_sell_animal(self):
        aid = self.sell_id_entry.get().strip()
        try:   price = float(self.sell_price_entry.get())
        except ValueError:
            messagebox.showerror("Input Error","Enter a numeric price."); return
        if not aid:
            messagebox.showerror("Input Error","Enter an animal ID."); return
        self.farm.sell_animal(aid, price)
        self._refresh_all()
        self._log(f"  ↗  Sold {aid} → KES {price:.2f}\n")
        self._set_status(f"Sold {aid} for KES {price:.2f}.")

    def _on_restock(self):
        try:   amt = float(self.restock_entry.get())
        except ValueError:
            messagebox.showerror("Input Error","Enter a numeric amount."); return
        self.farm.restock_feed(amt)
        self._refresh_all()
        self._log(f"  ↑  Restocked +{amt}kg → total {self.farm.feed:.0f}kg\n")
        self._set_status(f"Feed restocked. Total: {self.farm.feed:.0f} kg.")

    # ── Helpers ─────────────────────────────────────────────────────
    def _log(self, text: str):
        self.log.config(state="normal")
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.config(state="disabled")

    def _capture_and_log(self, fn):
        import io, sys
        buf = io.StringIO()
        old, sys.stdout = sys.stdout, buf
        fn()
        sys.stdout = old
        self._log(buf.getvalue())

    def _set_status(self, msg: str):
        self.status_var.set(f"  {msg}")

    def _refresh_all(self):
        self.day_var.set(  f"DAY  {self.farm.day}")
        self.rev_var.set(  f"KES  {self.farm.revenue:,.2f}")
        self.feed_var.set( f"{self.farm.feed:.0f} kg")
        self.water_var.set(f"{self.farm.water:.0f} L")
        self._refresh_table()

    def _refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, a in enumerate(self.farm.herd.animals):
            tag = "odd" if i % 2 == 0 else "even"
            self.tree.insert("", tk.END, tags=(tag,),
                             values=(a.id, a.species.value,
                                     f"{a.weight:.1f}", a.vaccination_status()))

    def _ask_int(self, title: str, prompt: str):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.PANEL)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Decorative top strip
        tk.Frame(dialog, bg=self.VIOLET, height=3).pack(fill="x")

        tk.Label(dialog, text=prompt,
                 font=self.LABEL_FONT,
                 fg=self.TEXT, bg=self.PANEL,
                 padx=24, pady=14).pack()

        entry = ttk.Entry(dialog, style="Farm.TEntry", width=14)
        entry.pack(padx=24, pady=(0,12)); entry.focus()

        result = [None]

        def _ok(event=None):
            try:   result[0] = int(entry.get())
            except ValueError:
                messagebox.showerror("Error","Enter a whole number.",parent=dialog); return
            dialog.destroy()

        ttk.Button(dialog, text="CONFIRM",
                   style="Farm.TButton",
                   command=_ok).pack(pady=(0,16))
        dialog.bind("<Return>", _ok)
        dialog.wait_window()
        return result[0]


def launch_gui(farm_obj: Farm):
    if not TKINTER_AVAILABLE:
        print("Tkinter is not available on this system.")
        print("Install: sudo apt install python3-tk  (Linux)")
        return
    root = tk.Tk()
    FarmGUI(root, farm_obj)
    root.mainloop()


# ── Main menu ──────────────────────────────────────────────────────
def menu():
    print("""
╔═════════════════════════════════╗
║      JKUAT FARM SYSTEM          ║
╠═════════════════════════════════╣
║ 1. Add Animal                   ║
║ 2. Simulate Day          [M1-4] ║
║ 3. View Report           [M1-4] ║
║ 4. Sell (submenu)        [M1-4] ║
║ 5. Restock Feed          [M1-4] ║
║ 6. Concurrent Day        [M5]   ║
║ 7. Functional Summary    [M5]   ║
║ 8. Launch GUI            [M6]   ║
║ 0. Exit                         ║
╚═════════════════════════════════╝
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
    c = input("Select: ").strip()

    if c == "1":
        sp = get_species()
        w  = float(input("Weight (kg): "))
        f  = float(input("Feed (kg/day): "))
        farm.add_animal(sp, w, f)

    elif c == "2":
        farm.simulate_day()

    elif c == "3":
        d = int(input("Day: "))
        farm.report(d)

    elif c == "4":
        sell_menu()
        sc = input("Choice: ").strip()
        if sc == "1":
            aid   = input("Animal ID: ")
            price = float(input("Price: "))
            farm.sell_animal(aid, price)
        elif sc == "2":
            qty = float(input("Milk (L): "))
            farm.sell_product("milk", qty)
        elif sc == "3":
            qty = int(input("Eggs: "))
            farm.sell_product("eggs", qty)

    elif c == "5":
        amt = float(input("Feed amount (kg): "))
        farm.restock_feed(amt)

    elif c == "6":
        run_concurrent_simulation(farm)

    elif c == "7":
        farm_summary_lambda(farm)

    elif c == "8":
        launch_gui(farm)

    elif c == "0":
        print("Goodbye!")
        break

"""Mock data tools for Travel Planner sub-agents.

Each function is deterministic per (origin, destination, date) so the same
query returns the same options. Replace these with real API calls (Amadeus,
Booking, OpenWeather, Google Places) when you're ready.
"""
from __future__ import annotations
from datetime import datetime, timedelta
import hashlib
import random

USD_TO_INR = 83.0

AIRLINES = [
    "Air India", "IndiGo", "Vistara", "Emirates",
    "Singapore Airlines", "ANA", "Lufthansa", "Qatar Airways",
]

HOTEL_TIERS = [
    {"name": "Grand {city} Hotel", "rating": 4.6, "tier": "Luxury",
     "price_usd": 280, "neighborhood": "City Center"},
    {"name": "{city} Comfort Suites", "rating": 4.2, "tier": "Mid-range",
     "price_usd": 140, "neighborhood": "Downtown"},
    {"name": "Backpacker {city}", "rating": 3.9, "tier": "Budget",
     "price_usd": 65,  "neighborhood": "Old Town"},
]

ATTRACTIONS_DB: dict[str, list[tuple[str, str, int]]] = {
    "tokyo": [
        ("Senso-ji Temple", "Cultural", 0),
        ("Shibuya Crossing", "Landmark", 0),
        ("Tokyo Skytree", "Observation", 28),
        ("teamLab Planets", "Art", 32),
        ("Tsukiji Outer Market", "Food", 20),
    ],
    "paris": [
        ("Eiffel Tower", "Landmark", 30),
        ("Louvre Museum", "Museum", 22),
        ("Notre-Dame Quarter", "Cultural", 0),
        ("Seine River Cruise", "Activity", 18),
        ("Montmartre", "Neighborhood", 0),
    ],
    "dubai": [
        ("Burj Khalifa", "Observation", 50),
        ("Desert Safari", "Activity", 75),
        ("Dubai Mall + Fountain", "Landmark", 0),
        ("Old Dubai Souks", "Cultural", 5),
        ("Palm Jumeirah Drive", "Scenic", 10),
    ],
    "bali": [
        ("Uluwatu Temple", "Cultural", 5),
        ("Tegallalang Rice Terraces", "Scenic", 3),
        ("Ubud Monkey Forest", "Nature", 6),
        ("Tanah Lot Sunset", "Landmark", 5),
        ("Mount Batur Sunrise Trek", "Adventure", 45),
    ],
    "default": [
        ("City Walking Tour", "Activity", 25),
        ("Local History Museum", "Museum", 15),
        ("Old Town Square", "Landmark", 0),
        ("Sunset Viewpoint", "Scenic", 0),
        ("Local Food Market", "Food", 20),
    ],
}


def _seed(*parts) -> int:
    h = hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()
    return int(h[:8], 16)


def search_flights(origin: str, destination: str, depart_date: str,
                   return_date: str, pax: int) -> dict:
    rng = random.Random(_seed(origin, destination, depart_date))
    options = []
    for _ in range(3):
        airline = rng.choice(AIRLINES)
        base = rng.randint(450, 1100)
        stops = rng.choice([0, 0, 1, 1, 2])
        dur_h = rng.randint(8, 22)
        dep = f"{rng.randint(0, 23):02d}:{rng.choice(['00', '15', '30', '45'])}"
        arr = f"{rng.randint(0, 23):02d}:{rng.choice(['00', '15', '30', '45'])}"
        options.append({
            "airline": airline,
            "flight_no": f"{airline[:2].upper()}{rng.randint(100, 999)}",
            "depart": f"{depart_date} {dep}",
            "arrive": f"{depart_date} {arr}",
            "duration_hours": dur_h,
            "stops": stops,
            "price_usd_per_pax": base,
            "price_usd_total": base * pax,
            "price_inr_total": int(base * pax * USD_TO_INR),
        })
    options.sort(key=lambda x: x["price_usd_total"])
    return {
        "origin": origin, "destination": destination,
        "depart_date": depart_date, "return_date": return_date,
        "pax": pax, "options": options,
    }


def search_hotels(destination: str, check_in: str, check_out: str,
                  pax: int) -> dict:
    nights = max(
        (datetime.fromisoformat(check_out) - datetime.fromisoformat(check_in)).days,
        1,
    )
    rng = random.Random(_seed(destination, check_in))
    rooms = max(1, (pax + 1) // 2)
    options = []
    for tpl in HOTEL_TIERS:
        wobble = rng.uniform(0.85, 1.15)
        per_night = round(tpl["price_usd"] * wobble)
        total = per_night * nights * rooms
        options.append({
            "name": tpl["name"].format(city=destination.title()),
            "rating": tpl["rating"],
            "tier": tpl["tier"],
            "neighborhood": tpl["neighborhood"],
            "rooms_required": rooms,
            "nights": nights,
            "price_usd_per_night": per_night,
            "price_usd_total": total,
            "price_inr_total": int(total * USD_TO_INR),
        })
    return {
        "destination": destination, "check_in": check_in,
        "check_out": check_out, "pax": pax, "options": options,
    }


def check_weather(destination: str, start_date: str, end_date: str) -> dict:
    rng = random.Random(_seed(destination, "weather"))
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    days = min(max((end - start).days + 1, 1), 14)
    conds = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Showers", "Clear", "Hazy"]
    forecast = []
    for i in range(days):
        d = start + timedelta(days=i)
        high_c = rng.randint(18, 34)
        low_c = high_c - rng.randint(5, 10)
        forecast.append({
            "date": d.strftime("%Y-%m-%d"),
            "conditions": rng.choice(conds),
            "high_c": high_c,
            "high_f": round(high_c * 9 / 5 + 32),
            "low_c": low_c,
            "low_f": round(low_c * 9 / 5 + 32),
            "precip_pct": rng.choice([0, 5, 10, 20, 40, 60]),
        })
    return {"destination": destination, "forecast": forecast}


def search_attractions(destination: str) -> dict:
    key = destination.lower().split(",")[0].strip()
    items = ATTRACTIONS_DB.get(key, ATTRACTIONS_DB["default"])
    return {
        "destination": destination,
        "attractions": [
            {
                "name": n, "type": t,
                "est_cost_usd_per_pax": c,
                "est_cost_inr_per_pax": int(c * USD_TO_INR),
            }
            for (n, t, c) in items
        ],
    }

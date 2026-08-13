from strands import tool

RESTAURANTS = [
    {"id": "r1", "name": "Trattoria Bella", "cuisine": "Italian",  "rating": 4.6},
    {"id": "r2", "name": "Osteria Romana",  "cuisine": "Italian",  "rating": 4.4},
    {"id": "r3", "name": "Sakura Garden",   "cuisine": "Japanese", "rating": 4.7},
    {"id": "r4", "name": "Ramen Yuki",      "cuisine": "Japanese", "rating": 4.9},
    {"id": "r5", "name": "El Mercado",      "cuisine": "Mexican",  "rating": 4.3},
    {"id": "r6", "name": "Spice Route",     "cuisine": "Indian",   "rating": 4.6},
    {"id": "r7", "name": "Le Bistro",       "cuisine": "French",   "rating": 4.8},
    {"id": "r8", "name": "The Grill House", "cuisine": "American", "rating": 4.2},
]

AVAILABILITY = {
    "r1": True,
    "r2": False,
    "r3": True,
    "r4": False,
    "r5": True,
    "r6": True,
    "r7": False,
    "r8": True,
}


@tool
def get_cuisines() -> dict:
    """Return the list of cuisine types available."""
    cuisines = sorted(set(r["cuisine"] for r in RESTAURANTS))
    return {"cuisines": cuisines}


@tool
def search_restaurants(cuisine: str = "") -> dict:
    """Search for restaurants. Returns all restaurants if no cuisine is specified.

    Args:
        cuisine: The cuisine type to filter by (e.g. "Italian", "Japanese").
            Leave empty to return all restaurants.
    """
    cuisine = cuisine.lower()
    if cuisine:
        restaurants = [r for r in RESTAURANTS if r["cuisine"].lower() == cuisine]
        if not restaurants:
            return {"error": f"No {cuisine.title()} restaurants found."}
        return {"restaurants": restaurants}
    return {"restaurants": RESTAURANTS}


@tool
def get_availability(restaurant_id: str) -> dict:
    """Check whether a specific restaurant has availability for tonight.

    Args:
        restaurant_id: The unique ID of the restaurant.
    """
    available = AVAILABILITY.get(restaurant_id, False)
    return {"restaurant_id": restaurant_id, "available": available}
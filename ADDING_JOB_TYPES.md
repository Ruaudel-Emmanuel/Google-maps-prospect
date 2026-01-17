# Adding Job Types / Métiers to the Google Maps Lead Scraper

## Overview

The Google Maps Lead Scraper allows you to easily add new job types (métiers) to the application. This guide explains how to do it in just a few simple steps.

## What are Job Types?

Job types are the categories of businesses you want to search for, such as "Restaurant", "Plumber", "Hotel", etc. They appear in the dropdown menu on the web interface and are sent to the Google Places API.

## How to Add a New Job Type

### Step 1: Open `app.py`

Open the main application file `app.py` in your code editor (VS Code, PyCharm, Sublime Text, etc.).

### Step 2: Locate the `JOB_TYPES` Dictionary

Find the `JOB_TYPES` dictionary near the top of the file (around line 50-80). It looks like this:

```python
JOB_TYPES = {
    "restaurant": "Restaurant",
    "cafe": "Cafe",
    "hotel": "Hotel",
    "bar": "Bar",
    "florist": "Fleuriste",
    "grocery_or_supermarket": "Supermarche",
    "shopping_mall": "Centre commercial",
    "bakery": "Boulangerie",
    "pharmacy": "Pharmacie",
    "park": "Parc",
    "police": "Police",
    "library": "Bibliotheque",
    "gas_station": "Station-service",
    "gym": "Salle de sport",
    "dentist": "Dentiste",
    "electrician": "Electricien",
    "plumber": "Plombier",
    "hair_care": "Salon de coiffure",
    "laundry": "Laverie",
    "movie_theater": "Cinema",
    "museum": "Musee",
    "night_club": "Boite de nuit",
    "post_office": "Bureau de poste",
    "real_estate_agency": "Agence immobiliere",
    "school": "Ecole",
    "shoe_store": "Magasin de chaussures",
    "spa": "Spa",
    "store": "Magasin",
    "taxi_stand": "Station de taxi",
    "travel_agency": "Agence de voyage",
    "zoo": "Zoo",
}
```

### Step 3: Add Your New Job Type

Add a new line inside the dictionary with the following format:

```python
"api_value": "French Label",
```

**Important:** 
- Replace `api_value` with the Google Places API type (use underscores for spaces, all lowercase)
- Replace `French Label` with the label that will appear in the dropdown (use ASCII characters, no accents)
- Make sure each line ends with a comma (except the last one)

### Step 4: Example - Adding a Veterinarian

Before (last existing entry):
```python
    "zoo": "Zoo",
}
```

After (adding veterinarian):
```python
    "zoo": "Zoo",
    "veterinary_care": "Veterinaire",
}
```

### Step 5: Restart the Application

Save the file and restart the Flask application:

```bash
python app.py
```

You should see the output:
```
Application started on http://localhost:5000
```

### Step 6: Verify the Change

1. Open your browser and go to `http://localhost:5000`
2. Click on the "Type de commerce" dropdown
3. Scroll through the list - your new job type should appear!

## Reference: Google Places API Types

The `api_value` must be a valid Google Places API type. Here are some common ones:

| API Type | Description |
|----------|-------------|
| `restaurant` | Restaurant |
| `cafe` | Cafe |
| `bar` | Bar |
| `hotel` | Hotel |
| `gas_station` | Gas station |
| `pharmacy` | Pharmacy |
| `grocery_or_supermarket` | Grocery/Supermarket |
| `shopping_mall` | Shopping mall |
| `bakery` | Bakery |
| `dentist` | Dentist |
| `doctor` | Doctor |
| `hospital` | Hospital |
| `bank` | Bank |
| `atm` | ATM |
| `post_office` | Post office |
| `library` | Library |
| `police` | Police |
| `fire_station` | Fire station |
| `gym` | Gym |
| `park` | Park |
| `museum` | Museum |
| `movie_theater` | Movie theater |
| `school` | School |
| `zoo` | Zoo |
| `plumber` | Plumber |
| `electrician` | Electrician |
| `hair_care` | Hair salon |
| `laundry` | Laundry |

**Full list:** See [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service/supported_types)

## Common Mistakes to Avoid

### ❌ Wrong: Adding accented characters
```python
"boulangerie": "Boulangérie",  # NO - avoid accents
```

### ✅ Correct: Use ASCII characters
```python
"bakery": "Boulangerie",  # YES - no accents
```

### ❌ Wrong: Using spaces in API value
```python
"hair salon": "Salon de coiffure",  # NO - use underscores
```

### ✅ Correct: Use underscores for spaces
```python
"hair_care": "Salon de coiffure",  # YES - use underscores
```

### ❌ Wrong: Forgetting the comma
```python
"zoo": "Zoo"
"museum": "Musee",  # ERROR - missing comma above
```

### ✅ Correct: All lines need commas (except last)
```python
"zoo": "Zoo",
"museum": "Musee",
```

## Bulk Adding Multiple Job Types

If you want to add several new types at once:

```python
JOB_TYPES = {
    # ... existing types ...
    "zoo": "Zoo",
    "veterinary_care": "Veterinaire",
    "car_rental": "Location de voiture",
    "car_repair": "Reparation automobile",
    "parking": "Parking",
    "pet_store": "Animalerie",
}
```

Then restart the app once and all new types will be available.

## Testing Your Addition

After adding a new job type:

1. **Check the dropdown** - Does it appear?
2. **Try a search** - Can you search using the new type?
3. **Check the console** - Any error messages?

If something goes wrong:
- Check that you don't have syntax errors (mismatched quotes, missing commas)
- Verify the `api_value` is a valid Google Places type
- Make sure there are no accented characters in the French label
- Restart the app again

## Troubleshooting

### Error: "SyntaxError: invalid syntax"

**Cause:** Typo in the dictionary (missing quote, comma, or bracket)

**Solution:** 
1. Check the line you added for typos
2. Make sure quotes are matching: `"key": "value",`
3. Verify commas are in place

### Error: "Bad Request 400"

**Cause:** The `api_value` is not recognized by Google Places API

**Solution:**
1. Double-check the API type name
2. Refer to the [Google Places API documentation](https://developers.google.com/maps/documentation/places/web-service/supported_types)
3. Use only valid type names

### New type doesn't appear in dropdown after restarting

**Cause:** Flask cache or browser cache

**Solution:**
1. Hard refresh the browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Restart the app with `python app.py`

## Summary

Adding a new job type is as simple as:

1. Open `app.py`
2. Find `JOB_TYPES` dictionary
3. Add one line: `"api_value": "French Label",`
4. Save and restart: `python app.py`
5. Refresh browser and check dropdown

Enjoy prospecting! 🎯

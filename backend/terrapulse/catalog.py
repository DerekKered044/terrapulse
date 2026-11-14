"""Supported regions and variables.

Regions are latitude/longitude boxes no larger than 10 x 10 degrees (the NASA
POWER regional API limit). Variables are NASA POWER monthly parameters whose
source is the MERRA-2 reanalysis.
"""

from __future__ import annotations

START_YEAR = 1981
END_YEAR = 2025

# bbox = [lon_min, lat_min, lon_max, lat_max]
REGIONS: dict[str, dict] = {
    "upper-colorado": {
        "name": "Upper Colorado River Basin",
        "country": "United States",
        "bbox": [-109.0, 37.0, -102.0, 41.0],
        "setting": "Semi-arid mountain headwaters that supply water to the US Southwest.",
    },
    "north-slope": {
        "name": "Alaska North Slope",
        "country": "United States",
        "bbox": [-160.0, 66.0, -150.0, 71.0],
        "setting": "Arctic tundra and permafrost on the edge of the Arctic Ocean.",
    },
    "rondonia": {
        "name": "Southwestern Amazon (Rondonia)",
        "country": "Brazil",
        "bbox": [-66.0, -13.0, -60.0, -8.0],
        "setting": "Tropical rainforest with extensive land clearing since the 1980s.",
    },
    "moroccan-atlas": {
        "name": "Moroccan Atlas",
        "country": "Morocco",
        "bbox": [-10.0, 30.0, -2.0, 35.0],
        "setting": "Mediterranean-to-desert transition across the Atlas Mountains.",
    },
    "central-sahel": {
        "name": "Central Sahel",
        "country": "Niger / Nigeria",
        "bbox": [0.0, 12.0, 10.0, 17.0],
        "setting": "Semi-arid belt between the Sahara and the West African savanna.",
    },
    "punjab-plain": {
        "name": "Punjab Plain",
        "country": "Pakistan / India",
        "bbox": [71.0, 28.0, 78.0, 33.0],
        "setting": "Intensively irrigated farmland of the upper Indus and Ganges plains.",
    },
    "malay-peninsula": {
        "name": "Malay Peninsula",
        "country": "Malaysia",
        "bbox": [99.0, 1.0, 105.0, 7.0],
        "setting": "Humid equatorial land and coastal seas with two monsoon seasons.",
    },
    "murray-darling": {
        "name": "Murray-Darling Basin (south)",
        "country": "Australia",
        "bbox": [140.0, -37.0, 149.0, -30.0],
        "setting": "Australia's main agricultural river basin, prone to multi-year drought.",
    },
}

VARIABLES: dict[str, dict] = {
    "T2M": {
        "name": "Air temperature",
        "long_name": "Temperature at 2 Meters",
        "units": "°C",
        "definition": "Average air temperature two meters above the ground, about head height.",
        "decimals": 2,
    },
    "PRECTOTCORR": {
        "name": "Precipitation",
        "long_name": "Precipitation Corrected",
        "units": "mm/day",
        "definition": "Average rain and melted snow reaching the surface each day. "
        "MERRA-2 adjusts its modelled precipitation toward gauge and satellite observations.",
        "decimals": 3,
    },
    "QV2M": {
        "name": "Humidity",
        "long_name": "Specific Humidity at 2 Meters",
        "units": "g/kg",
        "definition": "Grams of water vapor in each kilogram of air near the ground.",
        "decimals": 3,
    },
    "WS10M": {
        "name": "Wind speed",
        "long_name": "Wind Speed at 10 Meters",
        "units": "m/s",
        "definition": "Average wind speed ten meters above the ground.",
        "decimals": 3,
    },
    "GWETROOT": {
        "name": "Root-zone soil wetness",
        "long_name": "Root Zone Soil Wetness",
        "units": "fraction (0-1)",
        "definition": "How full of water the top meter of soil is: 0 is completely dry, 1 is saturated.",
        "decimals": 4,
    },
}

SOURCE = {
    "dataset": "MERRA-2 (Modern-Era Retrospective analysis for Research and Applications, Version 2)",
    "producer": "NASA Global Modeling and Assimilation Office (GMAO)",
    "access": "NASA POWER Monthly and Annual API (NASA Langley Research Center)",
    "access_url": "https://power.larc.nasa.gov/",
    "api_endpoint": "https://power.larc.nasa.gov/api/temporal/monthly/regional",
    "native_grid": "0.5° latitude x 0.625° longitude",
    "kind": "Reanalysis: a global model constrained by satellite and ground observations. "
    "Values are model-based estimates, not direct instrument readings.",
}

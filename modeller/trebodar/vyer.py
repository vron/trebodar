"""Vyer för rendering (Blender) och webbvisaren: kamera och mål i husets koordinater (mm), sol (azimut från +y
medurs, höjd i grader). `dolj`: delar av sökvägar som inte visas."""

VYER = {
    "ute-sydost": {"kamera": [-9000, -9000, 6500], "mal": [6500, 6500, 1500], "brannvidd": 30, "sol": [210, 30]},
    "ute-nordvast": {"kamera": [23000, 21000, 7000], "mal": [7000, 6500, 1000], "brannvidd": 30, "sol": [240, 30]},
    "ute-nordost": {"kamera": [4000, -14000, 3500], "mal": [7000, 5000, 1500], "brannvidd": 32, "sol": [140, 35]},
    "detalj-fasad": {"kamera": [6500, -4200, 1700], "mal": [8200, 0, 1500], "brannvidd": 40, "sol": [150, 30]},
    "detalj-sten": {"kamera": [11800, -2600, -600], "mal": [12600, 900, -1100], "brannvidd": 40, "sol": [150, 30]},
    "stomme": {"kamera": [-8000, -9000, 9000], "mal": [6500, 6500, 1800], "brannvidd": 30, "sol": [210, 40],
               "dolj": ["Hus/Tak/", "Hus/Fasad", "Hus/Isolering", "Hus/Invändigt", "Fönster och dörrar", "Mark/",
                        "Hus/Grund", "Installationer"]},
    "inne-mittre": {"kamera": [5200, 1200, 1600], "mal": [8000, 7000, 2400], "brannvidd": 18, "sol": [200, 30],
                    "inne": True},
    "inne-vanster": {"kamera": [1000, 15000, 1600], "mal": [2600, 9000, 2200], "brannvidd": 18, "sol": [240, 25],
                     "inne": True},
}

# delar som inte tas med i webbvisaren (stora nät)
WEBB_UTOM = ["Golvvärme"]

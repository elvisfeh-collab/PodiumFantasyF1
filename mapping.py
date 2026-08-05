# mapping.py

def get_mapa_pilotos():
    """
    Diccionario que relaciona fragmentos de texto comunes en la web 
    con su respectivo trigrama oficial para la temporada.
    """
    return {
        "max verstappen": "ver",
        "verstappen": "ver",
        "lando norris": "nor",
        "norris": "nor",
        "charles leclerc": "lec",
        "leclerc": "lec",
        "oscar piastri": "pia",
        "piastri": "pia",
        "carlos sainz": "sai",
        "sainz": "sai",
        "lewis hamilton": "ham",
        "hamilton": "ham",
        "george russell": "rus",
        "russell": "rus",
        "fernando alonso": "alo",
        "alonso": "alo",
        "lance stroll": "str",
        "stroll": "str",
        "sergio perez": "per",
        "perez": "per",
        "alexander albon": "alb",
        "albon": "alb",
        "liam lawson": "law",
        "lawson": "law",
        "nico hulkenberg": "hul",
        "hulkenberg": "hul",
        "ollie bearman": "bea",
        "bearman": "bea",
        "gabriel bortoleto": "bor",
        "bortoleto": "bor",
        "isack hadjar": "had",
        "hadjar": "had",
        "andrea kimi antonelli": "ant",
        "antonelli": "ant",
        "esteban ocon": "oco",
        "ocon": "oco",
        "pierre gasly": "gas",
        "gasly": "gas",
        "franco colapinto": "col",
        "colapinto": "col",
        "Valtteri Bottas": "bot",
        "bottas": "bot",
        "Arvid Lindblad": "lin",
        "Lindblad": "lin",
    }

def normalize_names(raw_data):
    """
    Asegura que los datos crudos del scraper mantengan un formato 
    estándar listo para procesar en la lógica de puntos.
    """
    if not raw_data:
        return ""
    if isinstance(raw_data, list):
        return ",".join([p.strip().lower() for p in raw_data if p.strip()])
    return raw_data.strip().lower()

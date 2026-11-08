tarifa = {
    "kisaruszallito": (8000, 320, 18000),
    "3.5t": (12000, 430, 25000),
    "darus": (18000, 650, 35000),
}

def fuvardij(jarmu:str, km:float) ->str:
    """Fuvardíj számítása.

    Args:
         jarmu: kisaruszallito, 3.5t vagy darus; km: oda-vissza km
    """
    if jarmu not in tarifa:
        return f"Ismeretlen jármű. Választható: {', '.join(tarifa)}"
    alap, kmdij, minimum = tarifa[jarmu]
    return f"A fuvardíj rakodás nélkül: {max(alap + km * kmdij, minimum):.0f} FT"

"""if __name__ == "__main__":
    print(fuvardij("3.5t", 40))"""
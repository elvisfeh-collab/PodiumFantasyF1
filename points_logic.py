ESCALA_MASTER = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

def motor_calculo_puntos_oficial(pred_text, real_text, limite_puestos):
    """
    Calcula puntos basados en tres niveles:
    - Simples: Piloto en Top real (Top 8 en Sprint, Top 10 en Carrera) pero posición incorrecta.
    - Dobles: Posición exacta acertada por el usuario.
    - Triples: Racha activa (Requiere obligatoriamente P1, P2 y P3 exactos).
    
    REGLAS DE ENTRADA:
    - Quali: Usuario mete 1 piloto. Se compara con P1 real.
    - Sprint: Usuario mete 3 pilotos. Se busca en el Top 8 real.
    - Carrera: Usuario mete 5 pilotos. Se busca en el Top 10 real.
    """
    if not pred_text or not real_text or not real_text.strip():
        return 0
        
    p_arr = [p.strip().lower() for p in pred_text.split(",") if p.strip()]
    r_arr = [p.strip().lower() for p in real_text.split(",") if p.strip()]
    
    # 1. Validamos la racha para los Puntos Triples (Podio perfecto)
    podio_perfecto = False
    if len(p_arr) >= 3 and len(r_arr) >= 3:
        if p_arr[0] == r_arr[0] and p_arr[1] == r_arr[1] and p_arr[2] == r_arr[2]:
            podio_perfecto = True

    pts = 0
    racha_triples_viva = podio_perfecto 

    # El bucle barre las predicciones del usuario y las contrasta con el límite real
    for i in range(min(len(p_arr), limite_puestos)):
        piloto = p_arr[i]
        p_predicha = i + 1  
        
        p_real = r_arr.index(piloto) + 1 if piloto in r_arr else -1
        
        if p_real > 0 and p_real <= len(r_arr):
            puntos_base = ESCALA_MASTER[p_real - 1]
            
            # CASO A: Posición exacta
            if p_real == p_predicha:
                if (p_predicha <= 3 and podio_perfecto) or (p_predicha > 3 and racha_triples_viva):
                    pts += puntos_base * 3
                else:
                    pts += puntos_base * 2
            
            # CASO B: Piloto mezclado (Suma puntos simples del 1 al 10 en carrera)
            else:
                pts += puntos_base  
                if p_predicha > 3:
                    racha_triples_viva = False  
                    
        # CASO C: Fuera de la zona de puntos real / DNF
        else:
            if p_predicha > 3:
                racha_triples_viva = False  

    return pts

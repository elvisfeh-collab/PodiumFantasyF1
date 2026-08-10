# points_logic.py

ESCALA_MASTER = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

def motor_calculo_puntos_oficial(pred_text, real_text, limite_puestos):
    """
    Calcula puntos basados en tres niveles:
    - Simples: Piloto en Top real (Top 8 en Sprint, Top 10 en Carrera) pero posición incorrecta.
    - Dobles: Posición exacta acertada por el usuario.
    - Triples: Racha activa (Requiere obligatoriamente P1, P2 y P3 exactos).
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

    for i in range(min(len(p_arr), limite_puestos)):
        piloto = p_arr[i]
        p_predicha = i + 1  
        
        p_real = r_arr.index(piloto) + 1 if piloto in r_arr else -1
        
        if p_real > 0 and p_real <= len(r_arr):
            puntos_base = ESCALA_MASTER[p_real - 1] if (p_real - 1) < len(ESCALA_MASTER) else 0
            
            # CASO A: Posición exacta
            if p_real == p_predicha:
                if (p_predicha <= 3 and podio_perfecto) or (p_predicha > 3 and racha_triples_viva):
                    pts += puntos_base * 3
                else:
                    pts += puntos_base * 2
            
            # CASO B: Piloto mezclado (Suma puntos simples)
            else:
                pts += puntos_base  
                if p_predicha > 3:
                    racha_triples_viva = False  
                    
        # CASO C: Fuera de la zona de puntos real / DNF
        else:
            if p_predicha > 3:
                racha_triples_viva = False  

    return pts

def procesar_puntos_gp(supabase, gp_id, tipo_sesion):
    """
    Función puente que conecta la base de datos con el motor oficial de cálculo.
    tipo_sesion puede ser 'carrera', 'sprint', o 'quali'
    limite_puestos: Quali = 1, Sprint = 8, Carrera = 10
    """
    print(f"--- Procesando puntos oficiales para GP ID: {gp_id} [{tipo_sesion}] ---")
    
    # Definir límites según la sesión
    limites = {
        "quali": 1,
        "sprint": 8,
        "carrera": 10
    }
    limite_puestos = limites.get(tipo_sesion, 10)

    # 1. Buscar el resultado real en Supabase para este GP y sesión
    res = supabase.table("resultados") \
                  .select("*") \
                  .eq("gp_id", gp_id) \
                  .eq("sesion", tipo_sesion) \
                  .execute()
                  
    if not res.data:
        print(f"❌ No hay resultados reales en la BD para la sesión {tipo_sesion}.")
        return

    resultado_real = res.data[0]['posiciones_texto'] # Asumiendo el campo donde guardas el string de pilotos

    # 2. Obtener las predicciones de los usuarios para este GP
    preds = supabase.table("predicciones") \
                    .select("*") \
                    .eq("gp_id", gp_id) \
                    .eq("sesion", tipo_sesion) \
                    .execute()
                    
    if not preds.data:
        print(f"❌ No hay predicciones registradas para esta sesión.")
        return

    # 3. Calcular y actualizar puntos por usuario usando el motor oficial
    for p in preds.data:
        puntos_calculados = motor_calculo_puntos_oficial(
            pred_text=p['prediccion_texto'], 
            real_text=resultado_real, 
            limite_puestos=limite_puestos
        )
        
        # Guardar o actualizar en la tabla de puntuaciones de Supabase
        supabase.table("puntuaciones").upsert({
            "user_id": p['user_id'],
            "gp_id": gp_id,
            "sesion": tipo_sesion,
            "puntos": puntos_calculados
        }, on_conflict="user_id,gp_id,sesion").execute()

    print(f"✅ Puntos calculados y guardados con éxito para {len(preds.data)} usuarios.")

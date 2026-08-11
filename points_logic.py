def procesar_puntos_gp(supabase, gp_id, tipo_sesion):
    print(f"--- Procesando puntos oficiales para GP ID: {gp_id} [{tipo_sesion}] ---")
    
    # Definir límites según la sesión
    limites = {
        "quali": 1,
        "sprint": 8,
        "carrera": 10
    }
    limite_puestos = limites.get(tipo_sesion, 10)

    # Mapeo exacto con los nombres reales de tus tablas en Supabase
    mapeo_tablas = {
        "quali": "resultados_quali",
        "sprint": "resultados_spring",
        "carrera": "resultados_oficiales"  # <-- Aquí apuntamos directo a tu tabla actual
    }
    
    nombre_tabla_resultados = mapeo_tablas.get(tipo_sesion)

    # 1. Buscar el resultado real en la tabla correspondiente
    res = supabase.table(nombre_tabla_resultados) \
                  .select("*") \
                  .eq("gp_id", gp_id) \
                  .execute()
                  
    if not res.data:
        print(f"❌ No hay resultados reales en la tabla '{nombre_tabla_resultados}' para el GP ID {gp_id}.")
        return

    resultado_real = res.data[0]['posiciones_texto']

    # 2. Obtener las predicciones de los usuarios
    preds = supabase.table("predicciones") \
                    .select("*") \
                    .eq("gp_id", gp_id) \
                    .eq("sesion", tipo_sesion) \
                    .execute()
                    
    if not preds.data:
        print(f"❌ No hay predicciones registradas para esta sesión.")
        return

    # 3. Calcular y actualizar puntos
    for p in preds.data:
        puntos_calculados = motor_calculo_puntos_oficial(
            pred_text=p['prediccion_texto'], 
            real_text=resultado_real, 
            limite_puestos=limite_puestos
        )
        
        supabase.table("puntuaciones").upsert({
            "user_id": p['user_id'],
            "gp_id": gp_id,
            "sesion": tipo_sesion,
            "puntos": puntos_calculados
        }, on_conflict="user_id,gp_id,sesion").execute()

    print(f"✅ Puntos calculados y guardados con éxito para {len(preds.data)} usuarios.")

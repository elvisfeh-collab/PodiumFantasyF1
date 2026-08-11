import os
from supabase import create_client

# Escala de puntos oficial
ESCALA_MASTER = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

def motor_calculo_puntos_oficial(pred_text, real_text, limite_puestos):
    if not pred_text or not real_text or not real_text.strip():
        return 0
        
    p_arr = [p.strip().lower() for p in pred_text.split(",") if p.strip()]
    r_arr = [p.strip().lower() for p in real_text.split(",") if p.strip()]
    
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
            
            if p_real == p_predicha:
                if (p_predicha <= 3 and podio_perfecto) or (p_predicha > 3 and racha_triples_viva):
                    pts += puntos_base * 3
                else:
                    pts += puntos_base * 2
            else:
                pts += puntos_base  
                if p_predicha > 3:
                    racha_triples_viva = False  
        else:
            if p_predicha > 3:
                racha_triples_viva = False  

    return pts

def procesar_sesion_gp(supabase, gp_id, tipo_sesion):
    print(f"--- Procesando [{tipo_sesion}] para GP ID: {gp_id} ---")
    
    # Límites y mapeo exacto a tus tablas de resultados score
    limites = {
        "quali": 1,
        "sprint": 8,
        "carrera": 10
    }
    
    mapeo_tablas = {
        "quali": "resultados_score_quali",
        "sprint": "resultados_score_sprint",
        "carrera": "resultados_score_oficiales"
    }
    
    limite_puestos = limites.get(tipo_sesion, 10)
    nombre_tabla = mapeo_tablas.get(tipo_sesion)

    # 1. Obtener resultado oficial de la sesión
    res = supabase.table(nombre_tabla).select("*").eq("gp_id", gp_id).execute()
    if not res.data:
        print(f"❌ No hay registros en '{nombre_tabla}' para el GP ID {gp_id}.")
        return

    resultado_real = res.data[0]['posiciones_texto']

    # 2. Obtener predicciones de los usuarios para esta sesión
    preds = supabase.table("predicciones").select("*").eq("gp_id", gp_id).eq("sesion", tipo_sesion).execute()
    if not preds.data:
        print(f"⚠️ No hay predicciones para la sesión {tipo_sesion} en este GP.")
        return

    # 3. Calcular e impactar la tabla central 'puntuaciones_gp' con desglose
    for p in preds.data:
        user_id = p['user_id']
        puntos_calculados = motor_calculo_puntos_oficial(
            pred_text=p['prediccion_texto'], 
            real_text=resultado_real, 
            limite_puestos=limite_puestos
        )
        
        # Consultar si ya existe un registro previo para este usuario en este GP
        existente = supabase.table("puntuaciones_gp") \
                            .select("*") \
                            .eq("user_id", user_id) \
                            .eq("gp_id", gp_id) \
                            .execute()
        
        # Valores actuales por defecto
        p_quali = 0
        p_sprint = 0
        p_carrera = 0
        
        if existente.data:
            row = existente.data[0]
            p_quali = row.get("puntos_quali", 0) or 0
            p_sprint = row.get("puntos_sprint", 0) or 0
            p_carrera = row.get("puntos_carrera", 0) or 0

        # Actualizar la sesión correspondiente
        if tipo_sesion == "quali":
            p_quali = puntos_calculados
        elif tipo_sesion == "sprint":
            p_sprint = puntos_calculados
        elif tipo_sesion == "carrera":
            p_carrera = puntos_calculados
            
        puntos_total = p_quali + p_sprint + p_carrera

        # Guardar consolidado en puntuaciones_gp
        supabase.table("puntuaciones_gp").upsert({
            "user_id": user_id,
            "gp_id": gp_id,
            "puntos_quali": p_quali,
            "puntos_sprint": p_sprint,
            "puntos_carrera": p_carrera,
            "puntos_total": puntos_total
        }, on_conflict="user_id,gp_id").execute()

    print(f"✅ Puntuaciones de {tipo_sesion} guardadas y desglosadas con éxito.")

if __name__ == "__main__":
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Error: Faltan credenciales de Supabase en el entorno.")
        exit(1)
        
    supabase = create_client(url, key)
    print("🚀 Conexión establecida. Iniciando procesamiento integral de puntuaciones...")
    
    sesiones = ["quali", "sprint", "carrera"]
    
    for sesion in sesiones:
        tabla = f"resultados_score_{'oficiales' if sesion == 'carrera' else sesion}"
        # Ajuste de nombre de tabla para sprint si es 'resultados_score_sprint'
        if sesion == "sprint":
            tabla = "resultados_score_sprint"
            
        try:
            res_all = supabase.table(tabla).select("gp_id").execute()
            if res_all.data:
                gps_procesados = set()
                for r in res_all.data:
                    gp_id = r['gp_id']
                    if gp_id not in gps_procesados:
                        gps_procesados.add(gp_id)
                        procesar_sesion_gp(supabase, gp_id, sesion)
        except Exception as e:
            print(f"⚠️ Aviso al escanear {tabla}: {e}")
                
    print("🏁 Sincronización y cálculo de puntos finalizados.")

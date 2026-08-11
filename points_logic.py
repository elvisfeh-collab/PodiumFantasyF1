import os
from supabase import create_client

ESCALA_MASTER = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

def motor_calculo_puntos_oficial(pred_text, real_text, limite_puestos):
    if not pred_text or not real_text or not real_text.strip():
        return 0
        
    p_arr = [p.strip().lower() for p in pred_text.split(",") if p.strip()]
    r_arr = [p.strip().lower() for p in real_text.split(",") if p.strip()]
    
    if not p_arr or not r_arr:
        return 0

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

def procesar_todo(supabase):
    print("🚀 Iniciando procesamiento de puntos con estructura real...")

    # 1. Obtener todas las predicciones de los usuarios
    preds_res = supabase.table("predicciones").select("*").execute()
    if not preds_res.data:
        print("⚠️ No hay predicciones registradas.")
        return

    for pred in preds_res.data:
        usuario_id = pred['usuario_id']
        gran_premio = pred['gran_premio']
        pred_id = pred['id']

        puntos_quali = 0
        puntos_sprint = 0
        puntos_carrera = 0

        # --- A. PROCESAR QUALI ---
        # En predicciones, la quali usa 'poleman'. En resultados_quali, la columna se llama 'quali'
        if pred.get('poleman'):
            res_q = supabase.table("resultados_quali").select("quali").eq("gran_premio", gran_premio).execute()
            if res_q.data:
                piloto_real_pole = res_q.data[0]['quali']
                # Si el poleman predicho coincide con el real, otorga puntos base de P1 (25 pts o regla simplificada dequali)
                if pred['poleman'].strip().lower() == piloto_real_pole.strip().lower():
                    puntos_quali = 25 # O el valor que corresponda a la lógica de quali

        # --- B. PROCESAR SPRINT ---
        sprint_preds = [pred.get('sprint_p1'), pred.get('sprint_p2'), pred.get('sprint_p3')]
        if any(sprint_preds):
            pred_sprint_text = ",".join([str(p) for p in sprint_preds if p])
            res_s = supabase.table("resultados_sprint").select("sprint").eq("gran_premio", gran_premio).execute()
            if res_s.data:
                real_sprint_text = res_s.data[0]['sprint']
                puntos_sprint = motor_calculo_puntos_oficial(pred_sprint_text, real_sprint_text, limite_puestos=8)

        # --- C. PROCESAR CARRERA OFICIAL ---
        carrera_preds = [pred.get('carrera_p1'), pred.get('carrera_p2'), pred.get('carrera_p3'), pred.get('carrera_p4'), pred.get('carrera_p5')]
        if any(carrera_preds):
            pred_carrera_text = ",".join([str(p) for p in carrera_preds if p])
            res_c = supabase.table("resultados_oficiales").select("carrera").eq("gran_premio", gran_premio).execute()
            if res_c.data:
                real_carrera_text = res_c.data[0]['carrera']
                puntos_carrera = motor_calculo_puntos_oficial(pred_carrera_text, real_carrera_text, limite_puestos=10)

        puntos_total = puntos_quali + puntos_sprint + puntos_carrera

        # Actualizar la tabla de predicciones con sus puntos parciales y totales individuales
        supabase.table("predicciones").update({
            "puntos_qualy": puntos_quali,
            "puntos_sprint": puntos_sprint,
            "puntos_carrera": puntos_carrera,
            "total_fin_de_semana": puntos_total
        }).eq("id", pred_id).execute()

        print(f"✅ GP: {gran_premio} | Usuario: {usuario_id} -> Q:{puntos_quali} S:{puntos_sprint} C:{puntos_carrera} Total:{puntos_total}")

if __name__ == "__main__":
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Error: Faltan credenciales.")
        exit(1)
        
    supabase = create_client(url, key)
    procesar_todo(supabase)
    print("🏁 Cálculo finalizado con éxito.")

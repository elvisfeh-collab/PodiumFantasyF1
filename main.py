import os
import sys

# Añade la carpeta actual al path para que Python encuentre los módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
import f1_tracks
import points_logic
import utils

def main():
    print("--- Iniciando Orquestador EFEH tech ---")
    
    # 1. Configuración de Supabase
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Credenciales de Supabase no configuradas.")
        sys.exit(1)
        
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # 2. Determinar evento activo usando el módulo calendar unificado
        evento = f1_tracks.get_current_event(supabase)
        if not evento:
            print("❌ No hay ningún evento activo en la BD.")
            return
            
        gp_nombre = evento['name']
        sesion = evento['sesion']
        print(f"📡 Procesando GP: {gp_nombre} | Sesión: {sesion}")

        # 3. Obtener el resultado oficial manual directamente desde Supabase
        # (Buscamos los trigramas ingresados previamente por el panel maestro)
        res_oficial = supabase.table("resultados") \
                              .select("posiciones_texto") \
                              .eq("gran_premio", gp_nombre) \
                              .eq("sesion", sesion) \
                              .execute()

        if not res_oficial.data or not res_oficial.data[0].get('posiciones_texto'):
            print(f"❌ No hay resultados manuales registrados en la BD para {gp_nombre} [{sesion}]. Abortando.")
            return
            
        clean_data = res_oficial.data[0]['posiciones_texto']
        print(f"📋 Resultado oficial recuperado (Trigramas): {clean_data}")
        
        # 4. Obtener las predicciones de los usuarios para este GP desde Supabase
        registros_predicciones = utils.get_user_predictions(supabase, gp_nombre)
        if not registros_predicciones:
            print("⚠️ No se encontraron predicciones de usuarios para este evento.")
            return

        # Definir límites de puestos según la sesión
        limites = {"quali": 1, "sprint": 8, "carrera": 10}
        limite_puestos = limites.get(sesion, 10)

        print(f"📊 Procesando puntos para {len(registros_predicciones)} pronósticos...")

        # 5. Bucle de cálculo e inyección por cada usuario registrado
        for reg in registros_predicciones:
            usuario_id = reg.get("usuario_id")
            
            # Extraer el texto de la predicción según la sesión activa
            if sesion == "quali":
                pred_text = reg.get("poleman")
            elif sesion == "sprint":
                p1 = reg.get("sprint_p1") or ""
                p2 = reg.get("sprint_p2") or ""
                p3 = reg.get("sprint_p3") or ""
                pred_text = f"{p1},{p2},{p3}"
            else: # carrera
                p1 = reg.get("carrera_p1") or ""
                p2 = reg.get("carrera_p2") or ""
                p3 = reg.get("carrera_p3") or ""
                p4 = reg.get("carrera_p4") or ""
                p5 = reg.get("carrera_p5") or ""
                pred_text = f"{p1},{p2},{p3},{p4},{p5}"
            
            # Ejecutar el motor de cálculo oficial con trigramas
            pts = points_logic.motor_calculo_puntos_oficial(pred_text, clean_data, limite_puestos)
            
            print(f"👤 Usuario ID {usuario_id} | Sesión {sesion} -> Puntos: {pts}")

            # 6. Mapeo dinámico de puntos hacia la tabla unificada de desgloses
            columna_punto_sesion = {
                "quali": "puntos_pole",
                "sprint": "puntos_sprint",
                "carrera": "puntos_carrera"
            }.get(sesion, "puntos_carrera")

            datos_actualizacion = {
                "usuario_id": usuario_id,
                "gran_premio": gp_nombre,
                columna_punto_sesion: pts
            }
            
            supabase.table("puntuaciones_gp").upsert(
                datos_actualizacion, 
                on_conflict="usuario_id,gran_premio"
            ).execute()

            # 7. Inyección a la tabla histórica correspondiente en Supabase
            tabla_destino = f"resultados_{sesion}"
            fila_registro = {
                "usuario_id": usuario_id,
                "gran_premio": gp_nombre,
                "sesion": sesion,
                "puntos_usuario": pts,
                "fuente_origen": "EFEH_tech_Systems"
            }
            
            supabase.table(tabla_destino).upsert(fila_registro).execute()

    except Exception as e:
        print(f"❌ Error durante la ejecución del proceso: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

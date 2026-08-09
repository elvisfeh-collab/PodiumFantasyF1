import os
import sys
from supabase import create_client
import scraper
import calendar
import points_logic
import mapping
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
        evento = calendar.get_current_event(supabase)
        if not evento:
            print("❌ No hay ningún evento activo en la BD.")
            return
            
        gp_nombre = evento['name']
        sesion = evento['sesion']
        url_evento = evento['url']
        print(f"📡 Procesando GP: {gp_nombre} | Sesión: {sesion}")

        # 3. Raspado de datos utilizando la sesión para el filtrado correcto
        clean_data = scraper.extract_data(url_evento, sesion)
        if not clean_data:
            print("❌ No se obtuvieron datos del scraper. Abortando.")
            return
        
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
            
            # (Aquí procesas las predicciones según la sesión: quali, sprint o carrera)
            # ...
            pts = points_logic.motor_calculo_puntos_oficial(...)
            
            print(f"👤 Usuario ID {usuario_id} | Sesión {sesion} -> Puntos: {pts}")

            # 6. Mapeo dinámico de puntos hacia la tabla unificada de desgloses
            columna_punto_sesion = {
                "quali": "puntos_pole",
                "sprint": "puntos_sprint",
                "carrera": "puntos_carrera"
            }.get(sesion, "puntos_carrera")

            # Hacemos un upsert inteligente en puntuaciones_gp
            # Primero consultamos si ya existe registro para este usuario y GP, o usamos la función de incremento de Supabase
            datos_actualizacion = {
                "usuario_id": usuario_id,
                "gran_premio": gp_nombre,
                columna_punto_sesion: pts
            }
            
            supabase.table("puntuaciones_gp").upsert(
                datos_actualizacion, 
                on_conflict="usuario_id,gran_premio"
            ).execute()

            # 6. Inyección a la tabla correspondiente en Supabase
            tabla_destino = f"resultados_{sesion}"
            fila_registro = {
                "user_id": user_id,
                "gran_premio": gp_nombre,
                "sesion": sesion,
                "puntos_usuario": pts,
                "fuente_origen": "EFEH_tech_Prod"
            }
            
            supabase.table(tabla_destino).upsert(fila_registro).execute()

        print("✅ ¡ÉXITO TOTAL: Ciclo de procesamiento y actualización completado!")

    except Exception as e:
        print(f"❌ Error crítico en el flujo principal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

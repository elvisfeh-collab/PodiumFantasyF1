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
            user_id = reg.get("user_id")
            pred_text = reg.get("prediccion")
            
            # Cálculo mediante la regla maestra
            pts = points_logic.motor_calculo_puntos_oficial(
                pred_text=pred_text,
                real_text=clean_data,
                limite_puestos=limite_puestos
            )
            
            print(f"👤 Usuario ID {user_id} -> Puntos: {pts}")

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

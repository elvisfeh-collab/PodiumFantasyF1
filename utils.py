def get_user_predictions(supabase, event_name):
    """
    Busca en la tabla 'predicciones' las apuestas de los usuarios 
    para un evento específico (gran_premio).
    """
    try:
        # Consultamos la tabla donde guardas las predicciones
        # Asumo que la columna se llama 'gran_premio' para filtrar
        response = supabase.table("predicciones") \
                           .select("user_id, prediccion") \
                           .eq("gran_premio", event_name) \
                           .execute()
        
        # Devolvemos la data lista para procesar
        return response.data
    except Exception as e:
        print(f"❌ Error al obtener predicciones de la DB: {e}")
        return []

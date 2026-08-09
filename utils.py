def get_user_predictions(supabase, event_name):
    """
    Busca en la tabla 'predicciones' las apuestas de los usuarios 
    para un evento específico (gran_premio).
    """
    try:
        response = supabase.table("predicciones") \
                           .select("usuario_id, poleman, carrera_p1, carrera_p2, carrera_p3, carrera_p4, carrera_p5, sprint_p1, sprint_p2, sprint_p3") \
                           .eq("gran_premio", event_name) \
                           .execute()
        return response.data
    except Exception as e:
        print(f"❌ Error al obtener predicciones de la DB: {e}")
        return []

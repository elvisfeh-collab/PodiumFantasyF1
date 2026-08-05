import requests
from bs4 import BeautifulSoup
import mapping

def extract_data(url, sesion="carrera"):
    """
    Orquestador de extracción: Descarga y procesa el HTML para devolver 
    la cadena de trigramas según la sesión (quali, sprint, carrera).
    """
    print(f"DEBUG: Conectando a {url} para sesión '{sesion}'...")
    
    html_content = _get_html_content(url)
    if not html_content:
        return None

    return _parse_trigrams(html_content, sesion)

def _get_html_content(url):
    """Manejo de conexión HTTP profesional con User-Agent."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error crítico conectando a {url}: {e}")
        return None

def _parse_trigrams(html_content, sesion):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        trigramas_encontrados = []
        
        cuerpo_tabla = soup.find("tbody")
        if not cuerpo_tabla:
            print("⚠️ Alerta: No se encontró la tabla de posiciones (tbody).")
            return None
            
        filas = cuerpo_tabla.find_all("tr")
        print(f"📊 Analizando {len(filas)} filas de la tabla oficial...")
        
        mapa_pilotos = mapping.get_mapa_pilotos()
        
        for fila in filas:
            texto_fila = " ".join(fila.get_text().split()).lower()
            
            for apellido_clave, trigrama_oficial in mapa_pilotos.items():
                if apellido_clave in texto_fila:
                    if trigrama_oficial not in trigramas_encontrados:
                        trigramas_encontrados.append(trigrama_oficial)
                    break 
                    
        print(f"📋 Trigramas mapeados en orden correlativo: {trigramas_encontrados}")
        
        # Filtros de empaquetado según la sesión solicitada
        if sesion == "quali" and len(trigramas_encontrados) >= 1:
            return trigramas_encontrados[0]
        elif sesion == "sprint" and len(trigramas_encontrados) >= 8:
            return ",".join(trigramas_encontrados[:8])
        elif sesion == "carrera" and len(trigramas_encontrados) >= 10:
            return ",".join(trigramas_encontrados[:10])
            
        print(f"⚠️ Alerta: Se hallaron {len(trigramas_encontrados)} pilotos. Insuficientes para la sesión '{sesion}'.")
        return None
        
    except Exception as e:
        print(f"❌ Fallo procesando el HTML en el scraper: {e}")
        return None

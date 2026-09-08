import httpx
import json

class ClienteLLM:
  def __init__(self):
    # LM Studio corre por defecto en el puerto 1234
    self.url_lm_studio = "http://localhost:1234/v1/chat/completions"
    self.cliente = httpx.Client(timeout=60.0) # Puede tardar un poco en procesar

  def analizar_estudiante(self, nombre_estudiante, alertas_texto):
    """
    Envía el historial de alertas al modelo Llama 3 en LM Studio
    para obtener un veredicto de fraude en formato JSON.
    """
    prompt = f"""Eres un juez estricto de exámenes. 
Analiza el comportamiento de este estudiante llamado {nombre_estudiante}.
Historial de alertas:
{alertas_texto}

Evalúa la probabilidad de que haya hecho trampa. 
Responde ÚNICAMENTE con un JSON válido usando este formato estricto:
{{"probabilidad_fraude_porcentaje": 0, "resumen_comportamiento": "...", "veredicto_final": "..."}}
"""

    payload = {
      "model": "meta-llama-3.1-8b-instruct",
      "messages": [
        {"role": "system", "content": "Eres un sistema de análisis de fraude en exámenes. Respondes SIEMPRE en formato JSON."},
        {"role": "user", "content": prompt}
      ],
      "temperature": 0.2,
      "max_tokens": 500,
      "response_format": {"type": "json_object"}
    }

    try:
      print("[LLM] Conectando con LM Studio...")
      respuesta = self.cliente.post(self.url_lm_studio, json=payload)
      if respuesta.status_code == 200:
        contenido = respuesta.json()["choices"][0]["message"]["content"]
        return True, json.loads(contenido)
      else:
        return False, {"error": f"Error del servidor LM Studio: {respuesta.status_code}"}
    except Exception as e:
      return False, {"error": f"No se pudo conectar a LM Studio. Asegúrate de que el servidor local está iniciado. Detalles: {str(e)}"}

cliente_llm = ClienteLLM()

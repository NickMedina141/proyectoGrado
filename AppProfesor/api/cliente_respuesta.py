# api/rest_client.py
import httpx
from utils.gestor_sesion import sesion_actual
from config.configuracion import url_login_profesor

class ClienteApi:
  def __init__(self):
    # Mantenemos una sesión abierta para no gastar recursos abriendo y cerrando conexiones
    self.cliente = httpx.Client(timeout=10.0) 

  def _obtener_cabecera_token(self):
    #Se inyecta el token en la sesión del profesor al momento de logearse
    cabeceras = {"Content-Type": "application/json"}
    #Obtenemos el token de la sesión
    token = sesion_actual.obtener_token()
    if token:
      cabeceras["Authorization"] = f"Bearer {token}"
    return cabeceras


  def login_profesor(self, email: str, password: str):
    
    carga_util = {
      "email": email,
      "password": password
    }
    
    try:
      #Petición a la API de Spring boot
      respuesta = self.cliente.post(url_login_profesor, json=carga_util)
      
      if respuesta.status_code == 200:
        datos = respuesta.json()
        #Guardamos el token y el ID del profesor en la memoria
        from utils.gestor_sesion import sesion_actual
        prof_id_real = datos.get("profesorId", email) # Fallback al email por si acaso
        sesion_actual.guardar_sesion(datos.get("token"), prof_id_real)
        return True, "Inicio de sesión exitoso"
      elif respuesta.status_code == 401:
        return False, "Credenciales incorrectas"
      else:
        return False, f"Error del servidor: {respuesta.status_code}"
        
    except httpx.RequestError as e:
      return False, f"Error de red: No se pudo conectar a Spring boot {str(e)}"

  def crear_examen(self, profesor_id, moodle_curso_id, moodle_quiz_id, materia_codigo, fechaExamen=None):
    carga_util = {
      "profesorId": profesor_id,
      "moodleCursoId": moodle_curso_id,
      "moodleQuizId": moodle_quiz_id,
      "materiaCodigo": materia_codigo
    }
    if fechaExamen:
      carga_util["fechaExamen"] = fechaExamen
    try:
      from config.configuracion import url_crear_examen
      res = self.cliente.post(url_crear_examen, json=carga_util, headers=self._obtener_cabecera_token())
      if res.status_code == 200:
        return True, res.json()
      else:
        return False, f"Error al crear examen: {res.text}"
    except httpx.RequestError as e:
      return False, f"Error de red: {str(e)}"

  def configurar_examen(self, codigo_examen, configuracion_payload):
    try:
      from config.configuracion import url_examenes
      respuesta = self.cliente.put(
        f"{url_examenes}/{codigo_examen}/configurar",
        json=configuracion_payload,
        headers=self._obtener_cabecera_token()
      )
      if respuesta.status_code == 200:
        return True, respuesta.json()
      return False, f"Error: {respuesta.status_code} - {respuesta.text}"
    except Exception as e:
      return False, f"Excepción de conexión: {str(e)}"

  def abrir_examen(self, codigo_examen):
    try:
      from config.configuracion import url_examenes
      respuesta = self.cliente.post(f"{url_examenes}/{codigo_examen}/abrir", headers=self._obtener_cabecera_token())
      if respuesta.status_code == 200:
        return True, "Sala abierta exitosamente"
      return False, f"Error: {respuesta.status_code} - {respuesta.text}"
    except Exception as e:
      return False, f"Excepción de conexión: {str(e)}"

  def cerrar_examen(self, codigo_examen):
    try:
      from config.configuracion import url_examenes
      respuesta = self.cliente.post(f"{url_examenes}/{codigo_examen}/cerrar", headers=self._obtener_cabecera_token())
      if respuesta.status_code == 200:
        return True, "Sala cerrada exitosamente"
      return False, f"Error: {respuesta.status_code} - {respuesta.text}"
    except Exception as e:
      return False, f"Excepción de conexión: {str(e)}"

  def obtener_mis_examenes(self, profesor_id):
    try:
      from config.configuracion import url_examenes
      url = f"{url_examenes}/profesor/{profesor_id}"
      res = self.cliente.get(url, headers=self._obtener_cabecera_token())
      if res.status_code == 200:
        return True, res.json()
      else:
        return False, f"Error: {res.text}"
    except httpx.RequestError as e:
      return False, f"Error de red: {str(e)}"

  def obtener_sesiones_examen(self, codigo_examen, todas=False):
    try:
      from config.configuracion import url
      endpoint = f"{url}/supervision/examen/{codigo_examen}/sesiones"
      params = {"todas": "true"} if todas else {}
      res = self.cliente.get(endpoint, params=params, headers=self._obtener_cabecera_token())
      if res.status_code == 200:
        return True, res.json()
      else:
        return False, f"Error: {res.text}"
    except httpx.RequestError as e:
      return False, f"Error de red: {str(e)}"

  def obtener_alertas_examen(self, codigo_examen):
    try:
      from config.configuracion import url
      endpoint = f"{url}/supervision/examen/{codigo_examen}/alertas"
      res = self.cliente.get(endpoint, headers=self._obtener_cabecera_token())
      if res.status_code == 200:
        return True, res.json()
      else:
        return False, f"Error: {res.text}"
    except httpx.RequestError as e:
      return False, f"Error de red: {str(e)}"

  def obtener_apelaciones_pendientes(self, profesor_id):
    try:
      from config.configuracion import url
      endpoint = f"{url}/apelaciones/profesor/{profesor_id}/pendientes"
      res = self.cliente.get(endpoint, headers=self._obtener_cabecera_token())
      if res.status_code == 200:
        return True, res.json()
      else:
        return False, f"Error: {res.text}"
    except httpx.RequestError as e:
      return False, f"Error de red: {str(e)}"

  def resolver_apelacion(self, sesion_id, resolucion_comite, estado_apelacion):
    try:
      from config.configuracion import url
      endpoint = f"{url}/apelaciones/{sesion_id}/resolver"
      params = {
        "resolucionComite": resolucion_comite,
        "estadoApelacion": estado_apelacion
      }
      res = self.cliente.put(endpoint, params=params, headers=self._obtener_cabecera_token())
      if res.status_code == 200:
        return True, res.text
      else:
        return False, f"Error {res.status_code}: {res.text}"
    except httpx.RequestError as e:
      return False, f"Error de red: {str(e)}"

  def obtener_alertas(self, sesion_id):
    try:
      from config.configuracion import url
      endpoint = f"{url}/supervision/{sesion_id}/alertas"
      res = self.cliente.get(endpoint, headers=self._obtener_cabecera_token())
      if res.status_code == 200:
        return True, res.json()
      else:
        return False, f"Error: {res.text}"
    except httpx.RequestError as e:
      return False, f"Error de red: {str(e)}"

#Instancia global lista para usarse en las vistas
cliente_api = ClienteApi()
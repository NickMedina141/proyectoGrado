import os
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import pyqtSignal
from PyQt6 import uic
from api.cliente_respuesta import cliente_api
from utils.gestor_sesion import sesion_actual
from datetime import datetime, timedelta

class ConfiguracionExamen(QWidget):
  anterior = pyqtSignal()
  finalizado = pyqtSignal()

  def __init__(self):
    super().__init__()
    
    base_path = os.path.dirname(__file__)
    uic.loadUi(os.path.join(base_path, "configuracion_examen.xml"), self)
    
    # Conectar botones
    self.btn_anterior.clicked.connect(self.emitir_anterior)
    self.btn_finalizar.clicked.connect(self.procesar_finalizar)
    
    # Ocultar campos de edición por defecto (solo se muestran al modificar)
    if hasattr(self, 'widget_info_basica'):
        self.widget_info_basica.setVisible(False)
    
    # Diccionario para almacenar los datos del paso 1
    self.datos_paso_1 = {}
    
    # Por defecto sensibilidad Media (Index 1)
    self.entrada_sensibilidad.setCurrentIndex(1)

  def cargar_datos(self, datos):
    self.datos_paso_1 = datos

  def emitir_anterior(self):
    self.anterior.emit()

  def procesar_finalizar(self):
    # 1. Recuperamos los datos del paso 1
    materia = self.datos_paso_1.get("materia")
    fecha_str = self.datos_paso_1.get("fecha")
    fecha_fin_str = self.datos_paso_1.get("fecha_fin", fecha_str)
    hora_str = self.datos_paso_1.get("hora")
    duracion_minutos = int(self.datos_paso_1.get("duracion", 60))
    
    profesor_id = sesion_actual.obtener_profesor_id()

    # Construir FechaExamen exacto
    # FechaExamen en Spring Boot espera: creacion, horaInicio, horaFin en formato YYYY-MM-DDTHH:MM:SS
    try:
      hora_inicio = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
      # Para la hora fin, tomamos la fecha de finalización y le sumamos la duración a la hora de inicio original
      hora_fin_base = datetime.strptime(f"{fecha_fin_str} {hora_str}", "%Y-%m-%d %H:%M")
      hora_fin = hora_fin_base + timedelta(minutes=duracion_minutos)
      
      fechaExamen_payload = {
        "creacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "horaInicio": hora_inicio.strftime("%Y-%m-%dT%H:%M:%S"),
        "horaFin": hora_fin.strftime("%Y-%m-%dT%H:%M:%S")
      }
    except Exception as e:
      QMessageBox.critical(self, "Error de Fecha", f"Hubo un error procesando las fechas: {str(e)}")
      return

    # 2. Llamada a la API para crear el examen básico
    exito_crear, respuesta_crear = cliente_api.crear_examen(
      profesor_id=profesor_id,
      materia_codigo=materia,
      fechaExamen=fechaExamen_payload
    )
    
    if not exito_crear:
      QMessageBox.critical(self, "Error al Crear Examen", respuesta_crear)
      return
      
    codigo_examen = respuesta_crear.get("codigoExamen")
    if not codigo_examen:
      QMessageBox.critical(self, "Error Interno", "La API no devolvió el código del examen.")
      return

    # 3. Preparar datos de Configuración (Paso 2)
    sensibilidad_map = {0: "BAJA", 1: "MEDIA", 2: "ALTA"}
    sensibilidad = sensibilidad_map.get(self.entrada_sensibilidad.currentIndex(), "MEDIA")
    reintentos = self.entrada_reintentos.value()
    
    # Convertir URLs y programas permitidos en listas limpias
    urls_raw = self.entrada_urls.toPlainText()
    urls_list = [u.strip() for u in urls_raw.split(',') if u.strip()]
    
    prog_raw = self.entrada_programas.toPlainText()
    prog_list = [p.strip() for p in prog_raw.split(',') if p.strip()]
    
    configuracion_payload = {
      "activarReconocimientoFacial": self.chk_facial.isChecked(),
      "activarDeteccionObjetos": self.chk_objetos.isChecked(),
      "activarAnalisisAudio": self.chk_audio.isChecked(),
      "activarMonitoreoProcesos": getattr(self, "chk_procesos").isChecked() if hasattr(self, "chk_procesos") else True,
      "activarAnalisisTeclado": getattr(self, "chk_teclado").isChecked() if hasattr(self, "chk_teclado") else True,
      "sensibilidadIA": sensibilidad,
      "duracionExamen": duracion_minutos,
      "permitirReintentos": reintentos,
      "procesosPermitidos": prog_list,
      "urlsPermitidas": urls_list
    }
    
    # 4. Llamada a la API para enviar la configuración
    exito_conf, respuesta_conf = cliente_api.configurar_examen(codigo_examen, configuracion_payload)
    
    if not exito_conf:
      QMessageBox.warning(self, "Examen Creado a Medias", f"Se creó el examen pero falló la configuración: {respuesta_conf}")
    else:
      QMessageBox.information(self, "Examen Creado", "¡El examen y sus configuraciones de IA fueron guardados con éxito en la base de datos!")
      
    # Emitir señal de finalizado para que VentanaPrincipal vuelva al dashboard y recargue
    self.finalizado.emit()

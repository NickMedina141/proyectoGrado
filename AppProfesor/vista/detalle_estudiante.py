import os
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QMessageBox, QInputDialog
from PyQt6.QtCore import Qt
from PyQt6 import uic
from api.cliente_respuesta import cliente_api

class DetalleEstudiante(QWidget):
  def __init__(self, main_window):
    super().__init__()
    self.main_window = main_window
    base_path = os.path.dirname(__file__)
    uic.loadUi(os.path.join(base_path, "detalle_estudiante.xml"), self)
    
    # Conectar botones
    self.btn_volver.clicked.connect(self.volver_sala)
    self.btn_advertencia.clicked.connect(self.enviar_advertencia)
    self.btn_marcar_fraude.clicked.connect(self.marcar_fraude)
    
    self.sesion_actual_id = ""
    import time
    self.ultimo_frame_tiempo = time.time()

  def cargar_datos(self, nombre_estudiante, id_sesion):
    self.sesion_actual_id = id_sesion
    self.lbl_nombre_estudiante.setText(nombre_estudiante)
    # Forzar el color explícitamente para que no quede blanco sobre blanco en tema claro
    self.lbl_nombre_estudiante.setStyleSheet("color: #2c3e50; font-size: 24px; font-weight: bold;")
    
    if hasattr(self, 'timer_alertas') and self.timer_alertas:
      self.timer_alertas.stop()
      
    # Limpiar historial previo
    while self.lista_alertas.count():
      item = self.lista_alertas.takeAt(0)
      widget = item.widget()
      if widget:
        widget.deleteLater()
        
    # --- LÓGICA DE TÚNEL DE VIDEO ON-DEMAND ---
    from api.cliente_ws import HiloWebSocket
    from PyQt6.QtCore import QTimer
    
    # Si ya hay un túnel abierto, lo cerramos
    if hasattr(self, 'hilo_stream') and self.hilo_stream:
      self.detener_stream()
      
    self.lbl_video_placeholder.setText("Conectando con la cámara del estudiante...\nEsperando frames...")
    
    # Escuchamos el canal de video
    self.hilo_stream = HiloWebSocket(ruta_sala=id_sesion, topico_base="/topic/stream")
    
    # Timer para asegurar que el comando llega al estudiante (reintento robusto)
    self.timer_reintento = QTimer(self)
    self.timer_reintento.setInterval(2000) # Reintenta cada 2 seg
    self.timer_reintento.timeout.connect(lambda: self.hilo_stream.enviar_comando(f"/topic/comandos/{id_sesion}", {"comando": "START_STREAM"}) if self.hilo_stream and self.hilo_stream.corriendo else self.timer_reintento.stop())
    
    def al_recibir_frame(base64_str):
      if self.timer_reintento.isActive():
        self.timer_reintento.stop() # Ya llegó el primer frame, cancelamos reintentos
      self.actualizar_frame_video(base64_str)
      
    self.hilo_stream.frame_recibido.connect(al_recibir_frame)
    
    # Una vez conectado, iniciamos el timer de reintentos
    self.hilo_stream.conectado.connect(self.timer_reintento.start)
    self.hilo_stream.start()
    # -------------------------------------------
        
    self.timer_alertas = QTimer(self)
    self.timer_alertas.setInterval(3000)
    self.timer_alertas.timeout.connect(self.refrescar_alertas)
    self.ultima_cantidad_alertas = -1
    
    # Llamar a la API la primera vez
    self.refrescar_alertas()
    
    # Arrancar timer de auto-refresco
    self.timer_alertas.start()

  def refrescar_alertas(self):
    # --- Revisar estado de conexión si no llegan frames ---
    import time
    ahora = time.time()
    
    if hasattr(self, 'ultimo_frame_tiempo'):
        dt = ahora - self.ultimo_frame_tiempo
        if dt > 5.0:
            self.badge_conexion.setText("Mala")
            self.badge_conexion.setStyleSheet("color: #E74C3C; font-weight: bold;")
        elif dt > 2.0:
            self.badge_conexion.setText("Regular")
            self.badge_conexion.setStyleSheet("color: #F39C12; font-weight: bold;")
        else:
            self.badge_conexion.setText("Buena")
            self.badge_conexion.setStyleSheet("color: #27AE60; font-weight: bold;")
    else:
        self.badge_conexion.setText("Mala")
        self.badge_conexion.setStyleSheet("color: #E74C3C; font-weight: bold;")
    # ----------------------------------------------------
    
    exito, alertas = cliente_api.obtener_alertas(self.sesion_actual_id)
    
    if not exito or not isinstance(alertas, list):
      alertas = []
      
    total_alertas = len(alertas)
    if total_alertas == self.ultima_cantidad_alertas:
      return # No hay alertas nuevas, no recargar
      
    self.ultima_cantidad_alertas = total_alertas
    
    # Limpiar historial previo para refrescar limpio
    while self.lista_alertas.count():
      item = self.lista_alertas.takeAt(0)
      widget = item.widget()
      if widget:
        widget.deleteLater()
        
    riesgo_ia = "Bajo"
    color_riesgo = "#27AE60"
    bg_riesgo = "#E8F8F5"
    
    if total_alertas>= 5:
      riesgo_ia = "Alto"
      color_riesgo = "#E74C3C"
      bg_riesgo = "#FDEDEC"
    elif total_alertas>0:
      riesgo_ia = "Medio"
      color_riesgo = "#F39C12"
      bg_riesgo = "#FEF5E7"
      
    # Actualizar Tarjeta "Resumen de Sesión"
    self.badge_alertas.setText(str(total_alertas))
    self.badge_riesgo.setText(riesgo_ia)
    self.badge_riesgo.setStyleSheet(f"color: {color_riesgo}; font-weight: bold;")
    
    # Inyectar las alertas
    for al in alertas:
      titulo = al.get("claseAlerta", "Alerta General")
      
      # Formatear la descripción dinámicamente según el tipo de alerta
      if titulo == "VISION":
        obj = al.get("objetoDetectado", "")
        tipo = al.get("tipoEvidencia", "")
        descripcion = f"Detectado: {obj} ({tipo})" if obj else "Anomalía visual detectada."
      elif titulo == "AUDIO":
        voces = al.get("vocesDetectadas", 1)
        texto = al.get("transcripcion", "")
        descripcion = f"Voces: {voces}. Texto: '{texto}'"
      elif titulo == "PROCESO":
        proc = al.get("nombreProceso", "Desconocido")
        cat = al.get("categoriaProceso", "")
        descripcion = f"Proceso prohibido: {proc} ({cat})"
      elif titulo == "TECLADO":
        patron = al.get("patronSospechoso", "")
        teclas = al.get("combinacionTeclas", "")
        descripcion = f"Detectado: {teclas}"
      else:
        descripcion = "Comportamiento detectado por la IA."
        
      hora_str = al.get("horaCaptura", "00:00")
      if "T" in hora_str:
        hora_str = hora_str.split("T")[1][:5]
        
      nivel = al.get("nivelRiesgo", "BAJO")
      tipo_alerta = "roja" if nivel == "ALTO" else ("naranja" if nivel == "MEDIO" else "verde")
      
      self.agregar_alerta_historial(titulo, descripcion, hora_str, tipo_alerta)

  def agregar_alerta_historial(self, titulo, descripcion, hora, tipo="verde"):
    frame = QFrame()
    # Asignar estilo basado en tipo
    if tipo == "roja":
      frame.setStyleSheet("background-color: transparent; border-bottom: 1px solid #E0E0E0; border-radius: 0px;")
      color_tit = "#333333"
      icono = ""
    elif tipo == "naranja":
      frame.setStyleSheet("background-color: transparent; border-bottom: 1px solid #E0E0E0; border-radius: 0px;")
      color_tit = "#333333"
      icono = ""
    else:
      frame.setStyleSheet("background-color: transparent; border-bottom: 1px solid #E0E0E0; border-radius: 0px;")
      color_tit = "#333333"
      icono = ""
      
    layout = QVBoxLayout(frame)
    layout.setSpacing(5)
    layout.setContentsMargins(15, 10, 15, 10)
    
    row_top = QHBoxLayout()
    lbl_tit = QLabel(f"{icono} {titulo}")
    lbl_tit.setStyleSheet(f"color: {color_tit}; font-weight: bold; font-size: 13px; border: none;")
    
    spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    lbl_hora = QLabel(hora)
    lbl_hora.setStyleSheet("color: #7F8C8D; font-size: 11px; border: none;")
    
    row_top.addWidget(lbl_tit)
    row_top.addItem(spacer)
    row_top.addWidget(lbl_hora)
    
    lbl_desc = QLabel(descripcion)
    lbl_desc.setWordWrap(True)
    lbl_desc.setStyleSheet("color: #333333; font-size: 12px; border: none;")
    
    layout.addLayout(row_top)
    layout.addWidget(lbl_desc)
    
    self.lista_alertas.addWidget(frame)

  def volver_sala(self):
    # Detenemos el stream SOLO al salir explícitamente de la vista (no al minimizar)
    self.detener_stream()
    self.main_window.cambiar_vista(1)
    
  def enviar_advertencia(self):
    opciones = [
      "Por favor, mira a la cámara.",
      "Evita el ruido ambiente excesivo.",
      "Cierra pestañas o programas no autorizados.",
      "Otra (escribir mensaje)..."
    ]
    seleccion, ok = QInputDialog.getItem(self, "Enviar Advertencia", "Seleccione o escriba la advertencia:", opciones, 0, False)
    
    if ok and seleccion:
      mensaje = seleccion
      if seleccion == "Otra (escribir mensaje)...":
        texto_libre, ok_texto = QInputDialog.getText(self, "Mensaje Personalizado", "Escribe la advertencia:")
        if ok_texto and texto_libre.strip():
          mensaje = texto_libre
        else:
          return
      
      # Enviar por WS al estudiante
      if hasattr(self, 'hilo_stream') and self.hilo_stream:
        self.hilo_stream.enviar_comando(f"/topic/comandos/{self.sesion_actual_id}", {"comando": "ADVERTENCIA", "mensaje": mensaje})
        QMessageBox.information(self, "Advertencia Enviada", f"Se ha enviado el siguiente mensaje al estudiante:\n\n'{mensaje}'")
      else:
        QMessageBox.warning(self, "Error", "No hay conexión activa con el estudiante para enviar la advertencia.")

  def marcar_fraude(self):
    motivo, ok = QInputDialog.getText(self, "Marcar Fraude", "Escribe el motivo del fraude (ej. Suplantación evidente):")
    if ok and motivo.strip():
      if hasattr(self, 'hilo_stream') and self.hilo_stream:
        self.hilo_stream.enviar_comando(f"/topic/comandos/{self.sesion_actual_id}", {"comando": "FRAUDE", "mensaje": motivo})
        QMessageBox.critical(self, "Fraude Marcado", f"El examen ha sido marcado como fraude por: {motivo}.\nEl estudiante será notificado inmediatamente y su examen será cerrado.")
      else:
        QMessageBox.warning(self, "Error", "No hay conexión activa con el estudiante para anular el examen.")
      
  def actualizar_frame_video(self, base64_str):
    import base64
    from PyQt6.QtGui import QPixmap
    import time
    try:
      ahora = time.time()
      dt = ahora - self.ultimo_frame_tiempo
      self.ultimo_frame_tiempo = ahora
      if dt > 2.0:
          self.badge_conexion.setText("Mala")
          self.badge_conexion.setStyleSheet("color: #E74C3C; font-weight: bold;")
      elif dt > 0.5:
          self.badge_conexion.setText("Regular")
          self.badge_conexion.setStyleSheet("color: #F39C12; font-weight: bold;")
      else:
          self.badge_conexion.setText("Buena")
          self.badge_conexion.setStyleSheet("color: #27AE60; font-weight: bold;")

      image_data = base64.b64decode(base64_str)
      pixmap = QPixmap()
      if pixmap.loadFromData(image_data):
        # Escalar para que encaje en el label sin deformarse
        w = self.lbl_video_placeholder.width()
        h = self.lbl_video_placeholder.height()
        self.lbl_video_placeholder.setPixmap(pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
    except Exception as e:
      pass

  def detener_stream(self):
    if hasattr(self, 'hilo_stream') and self.hilo_stream:
      # Enviamos orden de apagar el stream al estudiante
      self.hilo_stream.enviar_comando(f"/topic/comandos/{self.sesion_actual_id}", {"comando": "STOP_STREAM"})
      self.hilo_stream.detener()
      self.hilo_stream = None
      self.lbl_video_placeholder.setText("Transmisión finalizada.")

  

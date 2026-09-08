# vista/sala_supervision.py
import os
from PyQt6.QtWidgets import QWidget, QMessageBox, QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6 import uic

from api.cliente_ws import HiloWebSocket

class SalaSupervision(QWidget):
  def __init__(self, id_sesion=""):
    super().__init__()
    
    base_path = os.path.dirname(__file__)
    uic.loadUi(os.path.join(base_path, "sala_supervision.xml"), self)
    
    self.boton_finalizar.clicked.connect(self.finalizar_examen)
    
    self.tarjetas_estudiantes = {}
    self.codigo_examen_actual = ""
    self.estado_vacio(True)

  def estado_vacio(self, vacio, texto="Actualmente no se esta supervisando nada"):
    self.etiqueta_vacia.setVisible(vacio)
    self.etiqueta_vacia.setText(texto)
    self.area_scroll_grupos.setVisible(not vacio)
    self.badge_envivo.setVisible(not vacio)
    self.etiqueta_titulo.setVisible(not vacio)
    self.boton_finalizar.setVisible(not vacio)
    self.frame_feed_alertas.setVisible(not vacio)
    if vacio:
      self.limpiar_sala()

  def limpiar_sala(self):
    # Eliminar tarjetas de estudiantes
    for i in reversed(range(self.layout_grupos.count())):
      item = self.layout_grupos.itemAt(i)
      if item.widget() and item.widget() != self.etiqueta_vacia:
        item.widget().setParent(None)
        
    # Eliminar alertas del feed
    for i in reversed(range(self.layout_feed.count())):
      item = self.layout_feed.itemAt(i)
      if item.widget():
        item.widget().setParent(None)
    
    self.tarjetas_estudiantes.clear()
    if hasattr(self, 'hilo_ws') and self.hilo_ws.corriendo:
      self.hilo_ws.detener()

  def cargar_estudiantes(self, codigo_examen, nombre_materia=""):
    self.limpiar_sala()
    self.codigo_examen_actual = codigo_examen
    self.estado_vacio(False)
    
    titulo = nombre_materia if nombre_materia else codigo_examen
    self.etiqueta_titulo.setText(f"Monitoreo de Examen: {titulo}")
    
    from api.cliente_respuesta import cliente_api
    exito, datos = cliente_api.obtener_sesiones_examen(codigo_examen)
    
    if exito and isinstance(datos, list) and len(datos)>0:
      for sesion in datos:
        self.crear_tarjeta_estudiante(sesion)
      self.area_scroll_grupos.setVisible(True)
      self.etiqueta_vacia.setVisible(False)
    else:
      self.area_scroll_grupos.setVisible(False)
      self.etiqueta_vacia.setVisible(True)
      self.etiqueta_vacia.setText("No hay estudiantes aun presentando el examen")
        
    self.iniciar_conexion_en_vivo(codigo_examen)
    
    # Cargar el historial global de alertas de este examen
    exito_alertas, alertas = cliente_api.obtener_alertas_examen(codigo_examen)
    if exito_alertas and isinstance(alertas, list):
        for alerta in reversed(alertas): # reversed para que las más recientes queden arriba al insertarlas
            self.agregar_tarjeta_alerta(alerta)

  def crear_tarjeta_estudiante(self, sesion):
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
    
    estudiante_id = sesion.get("estudianteId", "Desconocido")
    nombre = sesion.get("nombreEstudiante", f"Estudiante {estudiante_id[:5]}") 
    
    tarjeta = QFrame()
    tarjeta.setObjectName("tarjeta_e1")
    tarjeta.setMinimumSize(220, 280)
    tarjeta.setMaximumSize(220, 280)
    
    lay_t = QVBoxLayout(tarjeta)
    lay_t.setSpacing(10)
    lay_t.setContentsMargins(20, 20, 20, 20)
    
    # TOP ROW
    top_row = QHBoxLayout()
    lbl_titulo = QLabel(nombre)
    lbl_titulo.setObjectName("titulo_e1")
    lbl_titulo.setStyleSheet("font-weight: bold; font-size: 16px;")
    lbl_titulo.setWordWrap(True)
    
    lbl_badge = QLabel("En Vivo")
    lbl_badge.setObjectName("badge_verde_1")
    
    top_row.addWidget(lbl_titulo)
    top_row.addWidget(lbl_badge)
    lay_t.addLayout(top_row)
    
    lay_t.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
    
    # INTEGRIDAD
    row_int = QHBoxLayout()
    lbl_i1 = QLabel("Integridad IA")
    lbl_i1.setObjectName("label_est_1")
    
    integridad = sesion.get("porcentajeIntegridad", 100)
    lbl_val_int = QLabel(f"{integridad}%")
    lbl_val_int.setObjectName("val_norm_1")
    
    if integridad >= 80:
        lbl_val_int.setStyleSheet("font-weight: bold; color: #003B13;")
    elif integridad >= 50:
        lbl_val_int.setStyleSheet("font-weight: bold; color: #d35400;")
    else:
        lbl_val_int.setStyleSheet("font-weight: bold; color: #c0392b;")
        
    row_int.addWidget(lbl_i1)
    row_int.addStretch()
    row_int.addWidget(lbl_val_int)
    lay_t.addLayout(row_int)
    
    # ALERTAS
    row_al = QHBoxLayout()
    lbl_a1 = QLabel("Alertas")
    lbl_a1.setObjectName("label_al_1")
    
    alertas = sesion.get("cantidadAlertas", 0)
    lbl_val_al = QLabel(str(alertas))
    lbl_val_al.setObjectName("val_norm_2")
    
    if alertas == 0:
        lbl_val_al.setStyleSheet("font-weight: bold; color: #003B13;")
    elif alertas <= 3:
        lbl_val_al.setStyleSheet("font-weight: bold; color: #d35400;")
    else:
        lbl_val_al.setStyleSheet("font-weight: bold; color: #c0392b;")
        
    row_al.addWidget(lbl_a1)
    row_al.addStretch()
    row_al.addWidget(lbl_val_al)
    lay_t.addLayout(row_al)
    
    # CONEXION
    row_cx = QHBoxLayout()
    lbl_c1 = QLabel("Estado de Conexión")
    lbl_c1.setObjectName("label_cx_1")
    lbl_c1.setWordWrap(True)
    
    estado_db = sesion.get("estadoSesion", "")
    if estado_db == "EN_CURSO":
        texto_conexion = "Buena"
        color_cx = "#27AE60"
    else:
        texto_conexion = "Mala"
        color_cx = "#E74C3C"
        
    lbl_val_cx = QLabel(texto_conexion)
    lbl_val_cx.setObjectName("val_green_1")
    lbl_val_cx.setStyleSheet(f"font-weight: bold; color: {color_cx};")
    row_cx.addWidget(lbl_c1)
    row_cx.addWidget(lbl_val_cx)
    lay_t.addLayout(row_cx)
    
    lay_t.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
    
    btn_cam = QPushButton("Ver Cámara")
    btn_cam.setObjectName("btn_e1")
    btn_cam.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_cam.setMinimumHeight(35)
    sesion_id = sesion.get("sesionId") or sesion.get("id") or ""
    btn_cam.clicked.connect(lambda checked, n=nombre, sid=sesion_id: self.abrir_estudiante(n, sid))
    lay_t.addWidget(btn_cam)
    
    self.layout_grupos.addWidget(tarjeta)
    
    self.tarjetas_estudiantes[sesion_id] = {
      "widget": tarjeta,
      "lbl_alertas": lbl_val_al,
      "lbl_integridad": lbl_val_int,
      "badge": lbl_badge,
      "alertas_count": alertas,
      "integridad": integridad
    }

  def abrir_estudiante(self, nombre, sesion_id):
    parent = self.window()
    if hasattr(parent, "abrir_detalle_estudiante"):
      parent.abrir_detalle_estudiante(nombre, sesion_id)

  def iniciar_conexion_en_vivo(self, id_sesion):
    ruta_especifica = f"/{id_sesion}" if id_sesion else ""
    self.hilo_ws = HiloWebSocket(ruta_especifica)
    
    self.hilo_ws.alerta_recibida.connect(self.mostrar_nueva_alerta)
    self.hilo_ws.conexion_perdida.connect(self.notificar_desconexion)
    
    self.hilo_ws.start()

  def mostrar_nueva_alerta(self, datos_alerta):
    if datos_alerta.get("tipoEvento") == "ESTUDIANTE_UNIDO":
        self.cargar_estudiantes(self.codigo_examen_actual)
        return
        
    # Cuando entra por websocket
    datos_alerta["nueva_alerta_ws"] = True
    self.agregar_tarjeta_alerta(datos_alerta)
      
  def agregar_tarjeta_alerta(self, alerta):
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt6.QtCore import Qt
    
    tarjeta = QFrame()
    tarjeta.setObjectName("tarjeta_alerta_limpia")
    tarjeta.setStyleSheet("""
        QFrame#tarjeta_alerta_limpia { 
            border: 1px solid #dcdde1; 
            border-radius: 6px;
            background-color: #ffffff;
            margin-bottom: 8px; 
        }
    """)
    
    layout = QVBoxLayout(tarjeta)
    layout.setSpacing(6)
    layout.setContentsMargins(12, 10, 12, 12)
    
    # Extraer datos
    clase_alerta = alerta.get("claseAlerta", alerta.get("tipo", "DESCONOCIDO")).upper()
    nombre_est = alerta.get("nombreEstudiante", alerta.get("estudiante", "Desconocido"))
    
    # Hora de captura
    hora_str = alerta.get("horaCaptura", alerta.get("hora", ""))
    if "T" in hora_str:
        hora_str = hora_str.split("T")[1][:5]
    
    nivel_riesgo = alerta.get("nivelRiesgo", "MEDIO").upper()
    
    # Colores
    color_riesgo = "#2c3e50"
    if nivel_riesgo == "ALTO":
        color_riesgo = "#c0392b"
    elif nivel_riesgo == "MEDIO":
        color_riesgo = "#d35400"
    elif nivel_riesgo == "BAJO":
        color_riesgo = "#27ae60"
        
    top_row = QHBoxLayout()
    
    # Texto de tipo de alerta sin recuadro (fondo transparente)
    lbl_tipo = QLabel(clase_alerta)
    lbl_tipo.setStyleSheet(f"""
        color: {color_riesgo}; 
        background-color: transparent;
        font-weight: bold; 
        font-size: 13px;
    """)
    
    lbl_hora = QLabel(hora_str)
    lbl_hora.setStyleSheet("color: #95a5a6; font-size: 11px;")
    
    top_row.addWidget(lbl_tipo)
    top_row.addStretch()
    top_row.addWidget(lbl_hora)
    layout.addLayout(top_row)
    
    lbl_nombre = QLabel(nombre_est)
    lbl_nombre.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
    layout.addWidget(lbl_nombre)
    
    # Extraer descrpcion dinamica
    desc = alerta.get("descripcion", alerta.get("mensaje", ""))
    if not desc:
        obj = alerta.get("objetoDetectado", "")
        if obj:
            desc = f"Objeto: {obj}"
    
    if desc:
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(lbl_desc)
        
    # Boton Ver Evidencia
    est_id = alerta.get("estudianteId", alerta.get("sesionId", ""))
    btn_link = QPushButton("Ver Evidencia")
    btn_link.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_link.setStyleSheet(f"""
        QPushButton {{
            color: {color_riesgo}; 
            background-color: transparent;
            text-align: left;
            border: none;
            text-decoration: underline;
            font-size: 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            color: #2980b9;
        }}
    """)
    btn_link.clicked.connect(lambda checked, n=nombre_est, sid=est_id: self.abrir_estudiante(n, sid))
    layout.addWidget(btn_link)
    
    self.layout_feed.insertWidget(0, tarjeta)
    
    # Actualizar tarjeta del estudiante si existe
    est_id = alerta.get("estudianteId", alerta.get("sesionId", ""))
    if est_id and est_id in self.tarjetas_estudiantes:
      tarjeta_est = self.tarjetas_estudiantes[est_id]
      
      # Actualizar el numero de alertas sumando 1 si es una nueva alerta (vía WebSocket)
      # Las alertas del historial REST ya vienen contabilizadas en la carga inicial
      if alerta.get("nueva_alerta_ws", False):
          lbl_al = tarjeta_est["widget"].findChild(QLabel, "val_norm_2")
          if lbl_al:
              try:
                  actual = int(lbl_al.text())
                  lbl_al.setText(str(actual + 1))
                  lbl_al.setStyleSheet("font-weight: bold; color: #c0392b;")
              except:
                  pass
      
      tipo = alerta.get("claseAlerta", alerta.get("tipo", ""))
      if "VISION" in tipo.upper() or "AUDIO" in tipo.upper() or "PROCESO" in tipo.upper():
        
        # Bajar integridad dinámicamente si llega por websocket
        if alerta.get("nueva_alerta_ws", False):
            try:
                texto_int = tarjeta_est["lbl_integridad"].text().replace("%", "")
                integridad_actual = int(texto_int)
                nivel = alerta.get("nivelRiesgo", "MEDIO").upper()
                descuento = 15
                if nivel == "ALTO": descuento = 30
                elif nivel == "BAJO": descuento = 5
                
                nueva_int = max(0, integridad_actual - descuento)
                tarjeta_est["lbl_integridad"].setText(f"{nueva_int}%")
                
                if nueva_int < 50:
                    tarjeta_est["lbl_integridad"].setStyleSheet("font-weight: bold; color: #c0392b;")
                elif nueva_int < 80:
                    tarjeta_est["lbl_integridad"].setStyleSheet("font-weight: bold; color: #d35400;")
            except Exception as e:
                pass
        
        # Cambiar badge a Alerta
        tarjeta_est["badge"].setText("Alerta")
        tarjeta_est["badge"].setObjectName("badge_rojo_1")
        tarjeta_est["widget"].setStyleSheet(tarjeta_est["widget"].styleSheet())

  def notificar_desconexion(self, mensaje):
    QMessageBox.warning(self, "Problema de Red", mensaje)
    self.badge_envivo.setText(" OFFLINE")

  def finalizar_examen(self):
    respuesta = QMessageBox.question(self, "Cerrar Sala", "¿Seguro que desea finalizar el monitoreo?", 
                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if respuesta == QMessageBox.StandardButton.Yes:
      from api.cliente_respuesta import cliente_api
      exito, mensaje = cliente_api.cerrar_examen(self.codigo_examen_actual)
      
      if exito:
        self.estado_vacio(True)
        QMessageBox.information(self, "Examen Finalizado", "El examen ha sido cerrado en el servidor.")
        # Avisar al parent (ventana principal) que recargue el dashboard
        parent = self.window()
        if hasattr(parent, "cargar_mis_examenes"):
          parent.cargar_mis_examenes()
      else:
        QMessageBox.warning(self, "Error", mensaje)
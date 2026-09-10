# vista/ventana_principal.py
import os
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6 import uic
from utils.gestor_sesion import sesion_actual

from vista.sala_supervision import SalaSupervision
from vista.panel_apelaciones import PanelApelaciones
from vista.detalle_estudiante import DetalleEstudiante
from vista.reporte_ia import ReporteIA
from vista.crear_examen import CrearExamen
from vista.configuracion_examen import ConfiguracionExamen

class VentanaPrincipal(QWidget):
  def __init__(self):
    super().__init__()
    
    # Cargamos el archivo unificado usando ruta absoluta dinámica
    base_path = os.path.dirname(__file__)
    uic.loadUi(os.path.join(base_path, "ventana_principal.xml"), self)
    
    logo_path = os.path.join(base_path, "recursos", "logo_upc.png").replace("\\", "/")
    if os.path.exists(logo_path):
        self.label_logo_placeholder.setText("")
        self.label_logo_placeholder.setStyleSheet(f"border-image: url('{logo_path}'); border-radius: 50px;")
    
    # Instanciamos las demás vistas
    self.vista_sala = SalaSupervision()
    self.vista_apelaciones = PanelApelaciones()
    self.vista_detalle_est = DetalleEstudiante(self)
    self.vista_reporte = ReporteIA()
    self.vista_crear = CrearExamen()
    self.vista_configuracion = ConfiguracionExamen()
    
    # contenedor_vistas ya tiene la pagina_dashboard en el índice 0 desde el XML.
    # Agregamos las vistas (Índice 1, 2, 3)
    self.contenedor_vistas.addWidget(self.vista_sala)     
    self.contenedor_vistas.addWidget(self.vista_apelaciones) 
    self.contenedor_vistas.addWidget(self.vista_detalle_est)
    
    # Envolver ReporteIA en un ScrollArea para evitar bug de geometría por altura mínima excedida
    from PyQt6.QtWidgets import QScrollArea
    self.scroll_reporte = QScrollArea()
    self.scroll_reporte.setWidgetResizable(True)
    self.scroll_reporte.setFrameShape(QScrollArea.Shape.NoFrame)
    self.scroll_reporte.setWidget(self.vista_reporte)
    self.contenedor_vistas.addWidget(self.scroll_reporte) # Índice 4
    
    self.scroll_crear = QScrollArea()
    self.scroll_crear.setWidgetResizable(True)
    self.scroll_crear.setFrameShape(QScrollArea.Shape.NoFrame)
    self.scroll_crear.setWidget(self.vista_crear)
    self.contenedor_vistas.addWidget(self.scroll_crear) # Índice 5
    
    self.scroll_config = QScrollArea()
    self.scroll_config.setWidgetResizable(True)
    self.scroll_config.setFrameShape(QScrollArea.Shape.NoFrame)
    self.scroll_config.setWidget(self.vista_configuracion)
    self.contenedor_vistas.addWidget(self.scroll_config) # Índice 6
    
    # Conectamos Navbar (Actualizado con Reportes)
    self.btn_nav_dashboard.clicked.connect(lambda: self.cambiar_vista(0))
    self.btn_nav_reportes.clicked.connect(lambda: self.cambiar_vista(4))
    self.btn_nav_sala.clicked.connect(lambda: self.cambiar_vista(1))
    self.btn_nav_apelaciones.clicked.connect(lambda: self.cambiar_vista(2))
    
    self.btn_nav_salir.clicked.connect(self.cerrar_sesion)
    self.btn_nav_tema.clicked.connect(self.alternar_tema)
    
    # Conectamos eventos del Flujo de Crear Examen
    self.boton_crear_examen.clicked.connect(lambda: self.cambiar_vista(5))
    self.vista_crear.cancelado.connect(lambda: self.cambiar_vista(0))
    self.vista_crear.siguiente.connect(self.ir_a_configuracion_examen)
    
    self.vista_configuracion.anterior.connect(lambda: self.cambiar_vista(5))
    self.vista_configuracion.finalizado.connect(self.examen_creado_exito)
    
    self.modo_oscuro = False
    
    self.cambiar_vista(0) # Inicializar en Dashboard
    self.aplicar_tema_claro()
    
    # FIX GEOMETRÍA WINDOWS: Evitar que el ScrollArea o cualquier widget fuerce un tamaño mínimo que colapse al maximizar
    self.setMinimumSize(900, 600)
    if hasattr(self, 'area_scroll'):
      self.area_scroll.setMinimumSize(0, 0)
      self.area_scroll.setWidgetResizable(True)
      
    self.cargar_mis_examenes()

  def cargar_mis_examenes(self):
    from api.cliente_respuesta import cliente_api
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt6.QtCore import Qt

    prof_id = sesion_actual.obtener_profesor_id()
    if not prof_id:
      return

    exito, examenes = cliente_api.obtener_mis_examenes(prof_id)
    if not exito:
      print("Error cargando examenes:", examenes)
      return

    # Ocultamos la tarjeta estática de prueba
    if hasattr(self, 'tarjeta_1'):
      self.tarjeta_1.hide()

    # Limpiar elementos generados dinámicamente si los hay
    if not hasattr(self, 'tarjetas_generadas'):
      self.tarjetas_generadas = []
    for widget in self.tarjetas_generadas:
      widget.setParent(None)
      widget.deleteLater()
    self.tarjetas_generadas.clear()

    # Detenemos timer viejo si existe
    if hasattr(self, 'timer_contadores'):
        self.timer_contadores.stop()
    self.etiquetas_tiempo = [] # Para guardar (label, horaFin)
    
    from datetime import datetime
    
    row = 0
    col = 0
    
    for examen in examenes:
      tarjeta = QFrame()
      tarjeta.setMinimumSize(280, 260)
      tarjeta.setMaximumSize(280, 260)
      tarjeta.setObjectName("tarjeta_dinamica") # Para que el CSS la pinte como blanca

      lay_v = QVBoxLayout(tarjeta)
      lay_v.setSpacing(10)
      lay_v.setContentsMargins(20, 20, 20, 20)

      # --- TOP ---
      top_lay = QHBoxLayout()
      
      materia = examen.get("materiaCodigo") or "Materia Desconocida"
      
      lbl_titulo_top = QLabel(materia)
      lbl_titulo_top.setObjectName("titulo_dinamico")
      lbl_titulo_top.setStyleSheet("font-weight: bold; font-size: 18px;")
      
      control_acceso = examen.get("controlAcceso") or {}
      estado_pin = control_acceso.get("estadoPin", "FINALIZADO")
        
      # --- AUTOMATIZACIÓN DE TIEMPO ---
      # Si la fecha actual está entre horaInicio y horaFin, forzamos visualmente a que esté ACTIVO (abierto)
      fecha_dict = examen.get("fechaExamen") or {}
      hora_fin_str = fecha_dict.get("horaFin")
      hora_inicio_str = fecha_dict.get("horaInicio")
        
      import datetime
      try:
          if hora_inicio_str and hora_fin_str:
              ahora = datetime.datetime.now().astimezone()
              dt_inicio = datetime.datetime.fromisoformat(hora_inicio_str).astimezone()
              dt_fin = datetime.datetime.fromisoformat(hora_fin_str).astimezone()
              
              if dt_inicio <= ahora <= dt_fin:
                  estado_pin = "ACTIVO"
              elif ahora > dt_fin:
                  estado_pin = "FINALIZADO"
              elif ahora < dt_inicio:
                  estado_pin = "PROGRAMADO"
      except Exception as e:
          pass
        
      texto_badge = "EN CURSO" if estado_pin == "ACTIVO" else ("PROGRAMADO" if estado_pin == "PROGRAMADO" else "FINALIZADO")
      badge = QLabel(texto_badge)
      if estado_pin == "ACTIVO":
        badge.setStyleSheet("background-color: #C1F032; color: #003B13; border-radius: 4px; padding: 4px; font-weight: bold;")
      elif estado_pin == "PROGRAMADO":
        badge.setStyleSheet("background-color: #3498DB; color: #FFFFFF; border-radius: 4px; padding: 4px; font-weight: bold;")
      else:
        badge.setStyleSheet("background-color: #E0E0E0; color: #333333; border-radius: 4px; padding: 4px; font-weight: bold;")

      top_lay.addWidget(lbl_titulo_top)
      top_lay.addStretch()
      top_lay.addWidget(badge)
      lay_v.addLayout(top_lay)

      # --- FECHA ---
      fecha_dict = examen.get("fechaExamen") or {}
      fecha_str = fecha_dict.get("horaInicio", "Sin Fecha")
      if "T" in fecha_str:
        try:
            import datetime
            dt_local = datetime.datetime.fromisoformat(fecha_str).astimezone()
            fecha_str = dt_local.strftime("%Y-%m-%d")
        except:
            fecha_str = fecha_str.split("T")[0]
      lbl_fecha = QLabel(f" {fecha_str}")
      lbl_fecha.setObjectName("fecha_dinamico")
      lay_v.addWidget(lbl_fecha)
      
      # --- ID EXAMEN ---
      id_ex = examen.get("codigoExamen") or examen.get("id") or "---"
      lbl_id = QLabel(f" ID: {id_ex[:8]}...")
      lbl_id.setObjectName("id_dinamico")
      lay_v.addWidget(lbl_id)

      # --- CONTADOR DE TIEMPO (NUEVO) ---
      hora_fin = fecha_dict.get("horaFin")
      lbl_tiempo = QLabel()
      lbl_tiempo.setStyleSheet("color: #e74c3c; font-weight: bold; font-family: Consolas;")
      lay_v.addWidget(lbl_tiempo)
      
      if estado_pin == "ACTIVO" and hora_fin_str:
          self.etiquetas_tiempo.append((lbl_tiempo, hora_fin_str, "Cierra en: "))
      elif estado_pin == "PROGRAMADO" and hora_inicio_str:
          self.etiquetas_tiempo.append((lbl_tiempo, hora_inicio_str, "Inicia en: "))
      elif estado_pin == "FINALIZADO":
          lbl_tiempo.setText(" Examen Finalizado")
          lbl_tiempo.setStyleSheet("color: #7f8c8d; font-weight: bold;")
      else:
          lbl_tiempo.setText(" Sin Límite")
          
      # --- SEPARADOR ---
      from PyQt6.QtWidgets import QFrame as QF
      linea = QF()
      linea.setFrameShape(QF.Shape.HLine)
      linea.setFrameShadow(QF.Shadow.Sunken)
      lay_v.addWidget(linea)

      # --- BOTON ENTRAR Y TOGGLE ---
      bot_lay = QHBoxLayout()
      
      btn_configuracion = QPushButton("⚙")
      btn_configuracion.setToolTip("Configurar Examen")
      btn_configuracion.setCursor(Qt.CursorShape.PointingHandCursor)
      btn_configuracion.setStyleSheet("QPushButton { font-size: 16px; border: none; background: transparent; } QPushButton:hover { color: #2980b9; }")
      # El botón se conecta a un modal que implementaré ahora
      btn_configuracion.clicked.connect(lambda checked, ex=examen: self.abrir_configuracion_examen(ex))
      bot_lay.addWidget(btn_configuracion)
      
      bot_lay.addStretch()
      
      btn_toggle = QPushButton(" Abrir" if estado_pin != "ACTIVO" else " Cerrar")
      btn_toggle.setObjectName("btn_toggle_dinamico")
      btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
      btn_toggle.clicked.connect(lambda checked, eid=id_ex, st=estado_pin: self.alternar_estado_examen(eid, st))

      btn_entrar = QPushButton("Entrar a Supervisar ")
      btn_entrar.setObjectName("btn_dinamico")
      btn_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
      # Pasamos el id y la materia por defecto en el lambda
      btn_entrar.clicked.connect(lambda checked, eid=id_ex, mat=materia: self.entrar_supervisar_dinamico(eid, mat))
      
      bot_lay.addWidget(btn_toggle)
      bot_lay.addWidget(btn_entrar)
      lay_v.addLayout(bot_lay)

      # Agregamos la tarjeta al layout_examenes (un QGridLayout)
      # Reemplazamos los índices estáticos
      self.layout_examenes.addWidget(tarjeta, row, col, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
      self.tarjetas_generadas.append(tarjeta)

      col += 1
      if col > 3: # 4 columnas máximo
        col = 0
        row += 1
        
    # Iniciar Timer de Cuenta Regresiva
    from PyQt6.QtCore import QTimer
    self.timer_contadores = QTimer(self)
    self.timer_contadores.timeout.connect(self._actualizar_contadores_examenes)
    self.timer_contadores.start(1000)
    self._actualizar_contadores_examenes()
      
  def _actualizar_contadores_examenes(self):
      from datetime import datetime, timezone
      
      ahora_utc = datetime.now(timezone.utc)
      ahora_local = datetime.now()
      
      for lbl, hora_objetivo_str, prefijo in self.etiquetas_tiempo:
          try:
              # '2026-09-30T23:59:59.000Z' o '2026-09-30T23:59:59'
              iso_str = hora_objetivo_str.replace("Z", "+00:00")
              if "." in iso_str and not "+" in iso_str:
                 iso_str = iso_str.split(".")[0]
              
              fin = datetime.fromisoformat(iso_str)
              
              if fin.tzinfo is not None:
                  ahora_comparar = ahora_utc
              else:
                  ahora_comparar = ahora_local
                  
              faltan = (fin - ahora_comparar).total_seconds()
              
              if faltan > 0:
                  dias = int(faltan // 86400)
                  horas = int((faltan % 86400) // 3600)
                  mins = int((faltan % 3600) // 60)
                  segs = int(faltan % 60)
                  
                  if dias > 0:
                      lbl.setText(f" {prefijo}{dias}d {horas:02d}:{mins:02d}:{segs:02d}")
                  else:
                      lbl.setText(f" {prefijo}{horas:02d}:{mins:02d}:{segs:02d}")
              else:
                  lbl.setText(" Actualizando...")
          except Exception as e:
              lbl.setText(" Error de tiempo")

  def alternar_estado_examen(self, id_sesion, estado_actual):
    from api.cliente_respuesta import cliente_api
    if estado_actual == "ACTIVO":
      exito, mensaje = cliente_api.cerrar_examen(id_sesion)
      if not exito: QMessageBox.warning(self, "Error", mensaje)
    else:
      exito, mensaje = cliente_api.abrir_examen(id_sesion)
      if not exito: QMessageBox.warning(self, "Error", mensaje)
    
    # Recargar dashboard para ver el cambio
    self.cargar_mis_examenes()

  def abrir_detalle_estudiante(self, nombre, id_sesion):
    self.vista_detalle_est.cargar_datos(nombre, id_sesion)
    self.cambiar_vista(3)

  def entrar_supervisar_dinamico(self, id_sesion, materia):
    self.vista_sala.cargar_estudiantes(id_sesion, materia)
    self.cambiar_vista(1)

  def abrir_configuracion_examen(self, examen):
    from PyQt6.QtWidgets import QDialog, QMessageBox, QWidget, QVBoxLayout, QStackedWidget, QScrollArea
    from PyQt6 import uic
    from PyQt6.QtCore import Qt, QDate, QTime
    import os
    
    dialogo = QDialog(self)
    dialogo.setWindowTitle("Editar Examen")
    dialogo.resize(800, 550)
    
    # Bug visual arreglado: Windows 11 ignora el color de QDialog. Pintamos el ScrollArea que cubre todo.
    color_fondo = "#0F172A" if hasattr(self, 'modo_oscuro') and self.modo_oscuro else "#F4F6F6"
    
    layout_main = QVBoxLayout(dialogo)
    layout_main.setContentsMargins(0, 0, 0, 0)
    
    scroll = QScrollArea(dialogo)
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet(f"""
        QScrollArea {{ border: none; background-color: {color_fondo}; }}
        QWidget#qt_scrollarea_viewport {{ background-color: {color_fondo}; }}
    """)
    
    stack = QStackedWidget()
    stack.setObjectName("MainConfigStack")
    stack.setStyleSheet(f"QWidget#MainConfigStack {{ background-color: {color_fondo}; }}")
    scroll.setWidget(stack)
    
    layout_main.addWidget(scroll)
    
    base_path = os.path.dirname(__file__)
    
    # --- PASO 1: Información Básica (crear_examen.xml) ---
    widget_paso1 = QWidget()
    uic.loadUi(os.path.join(base_path, "crear_examen.xml"), widget_paso1)
    stack.addWidget(widget_paso1)
    
    # Adaptar textos del paso 1
    if hasattr(widget_paso1, 'titulo_principal'):
        widget_paso1.titulo_principal.setText("Editar Examen")
    
    widget_paso1.entrada_materia.setText(examen.get("materiaCodigo", ""))
    widget_paso1.entrada_materia.setReadOnly(True) # La materia no se debería cambiar fácilmente
    widget_paso1.entrada_materia.setStyleSheet("background-color: #e0e0e0; color: #555;")
    
    # Cargar valores actuales del examen
    config_actual = examen.get("configuracionExamen") or {}
    fecha_examen = examen.get("fechaExamen") or {}
    
    if fecha_examen.get("horaInicio"):
        import datetime
        from PyQt6.QtCore import QDate, QTime
        try:
            # Parsear la cadena ISO (con timezone) y convertir a la zona horaria local
            dt_local = datetime.datetime.fromisoformat(fecha_examen.get("horaInicio")).astimezone()
            
            fecha_obj = QDate(dt_local.year, dt_local.month, dt_local.day)
            hora_obj = QTime(dt_local.hour, dt_local.minute)
            
            if fecha_obj.isValid(): widget_paso1.entrada_fecha.setDate(fecha_obj)
            if hora_obj.isValid():
                  hour12 = hora_obj.hour() % 12
                  if hour12 == 0: hour12 = 12
                  from PyQt6.QtCore import QTime
                  widget_paso1.entrada_hora_texto.setTime(QTime(hour12, hora_obj.minute()))
                  widget_paso1.entrada_hora_ampm.setCurrentText('PM' if hora_obj.hour() >= 12 else 'AM')
            
            if fecha_examen.get("horaFin") and hasattr(widget_paso1, 'entrada_fecha_fin'):
                dt_fin_local = datetime.datetime.fromisoformat(fecha_examen.get("horaFin")).astimezone()
                fecha_fin_obj = QDate(dt_fin_local.year, dt_fin_local.month, dt_fin_local.day)
                if fecha_fin_obj.isValid(): widget_paso1.entrada_fecha_fin.setDate(fecha_fin_obj)
            elif hasattr(widget_paso1, 'entrada_fecha_fin'):
                widget_paso1.entrada_fecha_fin.setDate(fecha_obj)
                
        except Exception as e:
            print("Error procesando fecha:", e)
        
    if hasattr(widget_paso1, 'entrada_duracion'):
        widget_paso1.entrada_duracion.setValue(config_actual.get("duracionExamen", 120))
        
    # Desconectar botones si tienen conexiones previas del UI, y reconectarlos
    try: widget_paso1.btn_cancelar.clicked.disconnect()
    except TypeError: pass
    
    try: widget_paso1.btn_siguiente.clicked.disconnect()
    except TypeError: pass
    
    widget_paso1.btn_cancelar.clicked.connect(dialogo.reject)
    widget_paso1.btn_siguiente.clicked.connect(lambda: stack.setCurrentIndex(1))

    # --- PASO 2: Configuración IA (configuracion_examen.xml) ---
    widget_paso2 = QWidget()
    uic.loadUi(os.path.join(base_path, "configuracion_examen.xml"), widget_paso2)
    stack.addWidget(widget_paso2)
    
    # Ocultar campos de edición básicos inyectados anteriormente (ya que ahora están en el paso 1)
    if hasattr(widget_paso2, 'widget_info_basica'):
        widget_paso2.widget_info_basica.setVisible(False)
        
    # Adaptar textos del paso 2
    widget_paso2.titulo_principal.setText("Ajustes de Supervisión IA")
    widget_paso2.subtitulo_principal.setText("Modifique los parámetros de proctoring automatizado para este examen.")
    widget_paso2.btn_finalizar.setText("Guardar y Actualizar")
    
    # Toggles de IA
    facial_val = config_actual.get("activarReconocimientoFacial")
    widget_paso2.chk_facial.setChecked(True if facial_val is None else bool(facial_val))
    
    objetos_val = config_actual.get("activarDeteccionObjetos")
    widget_paso2.chk_objetos.setChecked(True if objetos_val is None else bool(objetos_val))
    
    audio_val = config_actual.get("activarAnalisisAudio")
    widget_paso2.chk_audio.setChecked(False if audio_val is None else bool(audio_val))
    
    procesos_val = config_actual.get("activarMonitoreoProcesos")
    if hasattr(widget_paso2, "chk_procesos"):
        widget_paso2.chk_procesos.setChecked(True if procesos_val is None else bool(procesos_val))
        
    teclado_val = config_actual.get("activarAnalisisTeclado")
    if hasattr(widget_paso2, "chk_teclado"):
        widget_paso2.chk_teclado.setChecked(True if teclado_val is None else bool(teclado_val))
    
    sensibilidad_actual = config_actual.get("sensibilidadIA", "MEDIA")
    idx = {"BAJA": 0, "MEDIA": 1, "ALTA": 2}.get(sensibilidad_actual, 1)
    widget_paso2.entrada_sensibilidad.setCurrentIndex(idx)
    
    reintentos = config_actual.get("permitirReintentos", 3)
    widget_paso2.entrada_reintentos.setValue(reintentos)
    
    urls = config_actual.get("urlsPermitidas", [])
    widget_paso2.entrada_urls.setText(", ".join(urls))
    
    programas = config_actual.get("procesosPermitidos", [])
    widget_paso2.entrada_programas.setText(", ".join(programas))
    
    try: widget_paso2.btn_anterior.clicked.disconnect()
    except TypeError: pass
    
    try: widget_paso2.btn_finalizar.clicked.disconnect()
    except TypeError: pass
    
    widget_paso2.btn_anterior.clicked.connect(lambda: stack.setCurrentIndex(0))
    
    def guardar_cambios():
        from api.cliente_respuesta import cliente_api
        
        sensibilidad_map = {0: "BAJA", 1: "MEDIA", 2: "ALTA"}
        sensibilidad = sensibilidad_map.get(widget_paso2.entrada_sensibilidad.currentIndex(), "MEDIA")
        reintentos_nuevos = widget_paso2.entrada_reintentos.value()
        
        urls_raw = widget_paso2.entrada_urls.toPlainText()
        urls_list = [u.strip() for u in urls_raw.split(',') if u.strip()]
        
        prog_raw = widget_paso2.entrada_programas.toPlainText()
        prog_list = [p.strip() for p in prog_raw.split(',') if p.strip()]
                
        payload = {
              "fechaString": widget_paso1.entrada_fecha.date().toString("yyyy-MM-dd"),
              "fechaFinString": widget_paso1.entrada_fecha_fin.date().toString("yyyy-MM-dd") if hasattr(widget_paso1, 'entrada_fecha_fin') else widget_paso1.entrada_fecha.date().toString("yyyy-MM-dd"),
              "horaInicioString": f"{widget_paso1.entrada_hora_texto.time().hour() + (12 if widget_paso1.entrada_hora_ampm.currentText() == 'PM' and widget_paso1.entrada_hora_texto.time().hour() < 12 else (-12 if widget_paso1.entrada_hora_ampm.currentText() == 'AM' and widget_paso1.entrada_hora_texto.time().hour() == 12 else 0)):02d}:{widget_paso1.entrada_hora_texto.time().minute():02d}",
              "activarReconocimientoFacial": widget_paso2.chk_facial.isChecked(),
            "activarDeteccionObjetos": widget_paso2.chk_objetos.isChecked(),
            "activarAnalisisAudio": widget_paso2.chk_audio.isChecked(),
            "activarMonitoreoProcesos": getattr(widget_paso2, "chk_procesos").isChecked() if hasattr(widget_paso2, "chk_procesos") else True,
            "activarAnalisisTeclado": getattr(widget_paso2, "chk_teclado").isChecked() if hasattr(widget_paso2, "chk_teclado") else True,
            "sensibilidadIA": sensibilidad,
            "duracionExamen": widget_paso1.entrada_duracion.value() if hasattr(widget_paso1, 'entrada_duracion') else config_actual.get("duracionExamen", 120),
            "permitirReintentos": reintentos_nuevos,
            "procesosPermitidos": prog_list,
            "urlsPermitidas": urls_list
        }
        
        # Filtrar valores nulos
        payload = {k: v for k, v in payload.items() if v is not None}
        
        exito, msg = cliente_api.configurar_examen(examen.get("codigoExamen"), payload)
        if exito:
            QMessageBox.information(dialogo, "Éxito", "Configuración actualizada correctamente.")
            dialogo.accept()
            self.cargar_mis_examenes()
        else:
            QMessageBox.warning(dialogo, "Error", f"No se pudo actualizar: {msg}")
            
    widget_paso2.btn_finalizar.clicked.connect(guardar_cambios)
    
    dialogo.exec()

  def crear_examen(self):
    from api.cliente_respuesta import cliente_api
    
    prof_id = sesion_actual.obtener_profesor_id()
    if not prof_id:
      QMessageBox.warning(self, "Error", "No se encontró el ID del profesor en sesión.")
      return
    exito, respuesta = cliente_api.crear_examen(
      profesor_id=prof_id,
      moodle_curso_id="CURSO-2026",
      moodle_quiz_id="QUIZ-01",
      materia_codigo="MAT-101"
    )
    
    if exito:
      codigo_pin = respuesta.get("controlAcceso", {}).get("pinSesion", "NO_PIN")
      QMessageBox.information(self, "Exito", f"Examen creado correctamente.\nEl PIN para los estudiantes es: {codigo_pin}")
      self.cargar_mis_examenes() # Recargar la lista de exámenes visualmente
    else:
      QMessageBox.warning(self, "Error", f"No se pudo crear el examen:\n{respuesta}")

  def entrar_supervisar(self):
    # Cambiamos a la Sala de Supervisión (Índice 1)
    self.cambiar_vista(1)

  def cambiar_vista(self, indice):
    self.contenedor_vistas.setCurrentIndex(indice)
    self.actualizar_estilos_sidebar(indice)
    
    # Cargas dinámicas
    if indice == 2:
      self.vista_apelaciones.cargar_apelaciones_reales()
    if indice == 4:
      self.vista_reporte.cargar_examenes()

  def actualizar_estilos_sidebar(self, indice_activo):
    estilo_inactivo = """
      QPushButton { background-color: transparent; border: none; text-align: left; font-weight: bold; font-size: 14px; padding-left: 15px; color: white; border-radius: 6px; } 
      QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
    """
    estilo_activo = """
      QPushButton { background-color: #C1F032; border: none; text-align: left; font-weight: bold; font-size: 14px; padding-left: 15px; color: #003B13; border-radius: 6px; } 
    """
    self.btn_nav_dashboard.setStyleSheet(estilo_activo if indice_activo == 0 else estilo_inactivo)
    self.btn_nav_reportes.setStyleSheet(estilo_activo if indice_activo == 4 else estilo_inactivo)
    self.btn_nav_sala.setStyleSheet(estilo_activo if indice_activo == 1 else estilo_inactivo)
    self.btn_nav_apelaciones.setStyleSheet(estilo_activo if indice_activo == 2 else estilo_inactivo)
    self.btn_nav_tema.setStyleSheet(estilo_inactivo)
    self.btn_nav_salir.setStyleSheet(estilo_inactivo)

  def ir_a_configuracion_examen(self, datos):
    self.vista_configuracion.cargar_datos(datos)
    self.cambiar_vista(6)

  def examen_creado_exito(self):
    # Cuando el examen se crea exitosamente, recargamos el dashboard y volvemos a la vista 0
    from utils.gestor_sesion import sesion_actual
    self.cargar_mis_examenes()
    self.cambiar_vista(0)

  def alternar_tema(self):
    self.modo_oscuro = not self.modo_oscuro
    if self.modo_oscuro:
      self.aplicar_tema_oscuro()
    else:
      self.aplicar_tema_claro()

  def aplicar_tema_claro(self):
    self.btn_nav_tema.setText(" Modo Noche")
    try:
      base_path = os.path.dirname(__file__)
      with open(os.path.join(base_path, "tema_claro.css"), "r", encoding="utf-8") as f:
        estilo = f.read()
        self.setStyleSheet(estilo)
        self.vista_sala.setStyleSheet(estilo)
        self.vista_apelaciones.setStyleSheet(estilo)
        self.vista_detalle_est.setStyleSheet(estilo)
        self.vista_reporte.setStyleSheet(estilo)
    except Exception as e:
      print(f"Error cargando CSS Claro: {e}")
    self.actualizar_estilos_sidebar(self.contenedor_vistas.currentIndex())

  def aplicar_tema_oscuro(self):
    self.btn_nav_tema.setText(" Modo Día")
    try:
      base_path = os.path.dirname(__file__)
      with open(os.path.join(base_path, "tema_oscuro.css"), "r", encoding="utf-8") as f:
        estilo = f.read()
        self.setStyleSheet(estilo)
        self.vista_sala.setStyleSheet(estilo)
        self.vista_apelaciones.setStyleSheet(estilo)
        self.vista_detalle_est.setStyleSheet(estilo)
        self.vista_reporte.setStyleSheet(estilo)
    except Exception as e:
      print(f"Error cargando CSS Oscuro: {e}")
    self.actualizar_estilos_sidebar(self.contenedor_vistas.currentIndex())

  def cerrar_sesion(self):
    resp = QMessageBox.question(self, "Cerrar Sesión", "¿Está seguro de cerrar sesión?", 
                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if resp == QMessageBox.StandardButton.Yes:
      sesion_actual.cerrar_sesion()
      self.close()

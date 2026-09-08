import os
import math
from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem, QHBoxLayout, QLabel, QPushButton, QInputDialog, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6 import uic
from utils.gestor_sesion import sesion_actual
from api.cliente_respuesta import cliente_api

class PanelApelaciones(QWidget):
  def __init__(self):
    super().__init__()
    base_path = os.path.dirname(__file__)
    uic.loadUi(os.path.join(base_path, "panel_apelaciones.xml"), self)
    
    self.todas_las_apelaciones = []
    self.pagina_actual = 1
    self.elementos_por_pagina = 6
    
    self.btn_pag_prev.clicked.connect(self.pagina_anterior)
    self.btn_pag_next.clicked.connect(self.pagina_siguiente)
    
    self.cargar_apelaciones_reales()

  def cargar_apelaciones_reales(self):
    self.todas_las_apelaciones = []
    profesor_id = sesion_actual.obtener_profesor_id()
    if not profesor_id:
      return
      
    exito, datos = cliente_api.obtener_apelaciones_pendientes(profesor_id)
    
    if exito and isinstance(datos, list):
      self.todas_las_apelaciones = datos
      
    self.pagina_actual = 1
    self.renderizar_pagina()

  def renderizar_pagina(self):
    total_elementos = len(self.todas_las_apelaciones)
    
    self.tabla_apelaciones.setVisible(True)
    self.frame_paginacion.setVisible(total_elementos>0)
    self.etiqueta_vacia.setVisible(False)
    
    if total_elementos == 0:
      self.tabla_apelaciones.setRowCount(1)
      self.tabla_apelaciones.setColumnCount(6)
      self.tabla_apelaciones.clearSpans()
      self.tabla_apelaciones.setSpan(0, 0, 1, 6)
      
      item_vacio = QTableWidgetItem("No existen apelaciones pendientes")
      item_vacio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      # Aplicamos estilo gris claro cursiva simulando la etiqueta_vacia
      font = item_vacio.font()
      font.setItalic(True)
      font.setPointSize(12)
      item_vacio.setFont(font)
      
      from PyQt6.QtGui import QColor, QBrush
      item_vacio.setForeground(QBrush(QColor("#7F8C8D")))
      
      self.tabla_apelaciones.setItem(0, 0, item_vacio)
      return
      
    self.tabla_apelaciones.clearSpans()
    
    total_paginas = math.ceil(total_elementos / self.elementos_por_pagina)
    self.lbl_paginacion.setText(f"{self.pagina_actual} / {total_paginas}")
    
    self.btn_pag_prev.setEnabled(self.pagina_actual>1)
    self.btn_pag_next.setEnabled(self.pagina_actual < total_paginas)
    
    inicio = (self.pagina_actual - 1) * self.elementos_por_pagina
    fin = inicio + self.elementos_por_pagina
    apelaciones_pagina = self.todas_las_apelaciones[inicio:fin]
    
    self.tabla_apelaciones.setRowCount(0)
    self.tabla_apelaciones.setRowCount(len(apelaciones_pagina))
    
    for fila, sesion in enumerate(apelaciones_pagina):
      id_apelacion = sesion.get("sesionId") or sesion.get("id") or "---"
      estudiante_id = sesion.get("estudianteId", "Desconocido")
      estudiante_nombre = sesion.get("nombreEstudiante") or estudiante_id
      examen = sesion.get("examenId", "---")
      
      apelacion_obj = sesion.get("apelacion", {})
      motivo = apelacion_obj.get("argumentoEstudiante", "Sin argumento")
      estado = apelacion_obj.get("estadoApelacion", "PENDIENTE")

      # Mostrar el ID del estudiante en la columna ID, y el nombre real en la columna Estudiante
      item_id = QTableWidgetItem(estudiante_id)
      item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      self.tabla_apelaciones.setItem(fila, 0, item_id)
      
      item_est = QTableWidgetItem(estudiante_nombre)
      item_est.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      self.tabla_apelaciones.setItem(fila, 1, item_est)
      
      item_exa = QTableWidgetItem(examen)
      item_exa.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      self.tabla_apelaciones.setItem(fila, 2, item_exa)
      
      item_mot = QTableWidgetItem(motivo[:30] + "..." if len(motivo)>30 else motivo)
      item_mot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
      self.tabla_apelaciones.setItem(fila, 3, item_mot)
      
      widget_estado = QWidget()
      layout_estado = QHBoxLayout(widget_estado)
      layout_estado.setContentsMargins(15, 5, 15, 5)
      
      lbl_pendiente = QLabel("Pendiente")
      lbl_pendiente.setStyleSheet("color: #F39C12; font-weight: bold; font-size: 14px;")
      lbl_pendiente.setAlignment(Qt.AlignmentFlag.AlignCenter)
      
      layout_estado.addWidget(lbl_pendiente)
      layout_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
      self.tabla_apelaciones.setCellWidget(fila, 4, widget_estado)
      
      widget_acciones = QWidget()
      layout_acc = QHBoxLayout(widget_acciones)
      layout_acc.setContentsMargins(0, 0, 0, 0)
      layout_acc.setSpacing(10)
      layout_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
      
      btn_ver = QPushButton("Ver Evidencia")
      btn_ver.setCursor(Qt.CursorShape.PointingHandCursor)
      btn_ver.setStyleSheet("""
        QPushButton { color: #2C3E50; border: none; font-weight: bold; padding: 6px 12px; font-size: 13px; text-decoration: underline; }
        QPushButton:hover { color: #1A252F; }
      """)
      btn_ver.clicked.connect(lambda checked, m=motivo: self.ver_evidencia(m))
      
      btn_rechazar = QPushButton("Rechazar")
      btn_rechazar.setCursor(Qt.CursorShape.PointingHandCursor)
      btn_rechazar.setStyleSheet("""
        QPushButton { color: #C0392B; border: none; font-weight: bold; padding: 6px 12px; font-size: 13px; }
        QPushButton:hover { color: #922B21; text-decoration: underline; }
      """)
      btn_rechazar.clicked.connect(lambda checked, s=id_apelacion: self.rechazar_apelacion(s))
      
      btn_aprobar = QPushButton("Aprobar")
      btn_aprobar.setCursor(Qt.CursorShape.PointingHandCursor)
      btn_aprobar.setStyleSheet("""
        QPushButton { color: #1E8449; border: none; font-weight: bold; padding: 6px 12px; font-size: 13px; }
        QPushButton:hover { color: #145A32; text-decoration: underline; }
      """)
      btn_aprobar.clicked.connect(lambda checked, s=id_apelacion: self.aprobar_apelacion(s))
      
      layout_acc.addWidget(btn_ver)
      layout_acc.addWidget(btn_rechazar)
      layout_acc.addWidget(btn_aprobar)
      
      self.tabla_apelaciones.setCellWidget(fila, 5, widget_acciones)
      
    self.tabla_apelaciones.setColumnWidth(0, 100) 
    self.tabla_apelaciones.setColumnWidth(1, 150)
    self.tabla_apelaciones.setColumnWidth(2, 120)
    self.tabla_apelaciones.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
    self.tabla_apelaciones.setColumnWidth(4, 120)
    self.tabla_apelaciones.setColumnWidth(5, 320)
    
    self.tabla_apelaciones.verticalHeader().setVisible(False)
    self.tabla_apelaciones.verticalHeader().setDefaultSectionSize(65)
    self.tabla_apelaciones.setFocusPolicy(Qt.FocusPolicy.NoFocus)

  def pagina_anterior(self):
    if self.pagina_actual>1:
      self.pagina_actual -= 1
      self.renderizar_pagina()

  def pagina_siguiente(self):
    total_paginas = math.ceil(len(self.todas_las_apelaciones) / self.elementos_por_pagina)
    if self.pagina_actual < total_paginas:
      self.pagina_actual += 1
      self.renderizar_pagina()

  def ver_evidencia(self, motivo_completo):
    QMessageBox.information(self, "Evidencia / Motivo del Estudiante", f"El estudiante escribió:\n\n'{motivo_completo}'")

  def aprobar_apelacion(self, sesion_id):
    motivo, ok = QInputDialog.getText(self, "Aprobar Segunda Revisión", "Motivo de la aprobación:")
    if ok and motivo:
      exito, msg = cliente_api.resolver_apelacion(sesion_id, motivo, "APROBADA_A_FAVOR")
      if exito:
        QMessageBox.information(self, "Éxito", "Apelación aprobada y estado actualizado.")
        self.cargar_apelaciones_reales()
      else:
        QMessageBox.warning(self, "Error", msg)
        
  def rechazar_apelacion(self, sesion_id):
    motivo, ok = QInputDialog.getText(self, "Rechazar Segunda Revisión", "Motivo para mantener la decisión:")
    if ok and motivo:
      exito, msg = cliente_api.resolver_apelacion(sesion_id, motivo, "RECHAZADA_FRAUDE_MANTENIDO")
      if exito:
        QMessageBox.information(self, "Éxito", "Apelación rechazada y estado actualizado.")
        self.cargar_apelaciones_reales()
      else:
        QMessageBox.warning(self, "Error", msg)
import os
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import pyqtSignal, QDate, QTime
from PyQt6 import uic

class CrearExamen(QWidget):
  cancelado = pyqtSignal()
  siguiente = pyqtSignal(dict)

  def __init__(self):
    super().__init__()
    
    base_path = os.path.dirname(__file__)
    uic.loadUi(os.path.join(base_path, "crear_examen.xml"), self)
    
    # Conectar botones
    self.btn_cancelar.clicked.connect(self.emitir_cancelar)
    self.btn_siguiente.clicked.connect(self.procesar_siguiente)
    
    # Valores por defecto
    self.entrada_fecha.setDate(QDate.currentDate())
    self.entrada_hora.setTime(QTime.currentTime())
    
  def emitir_cancelar(self):
    # Limpiar formulario
    self.entrada_materia.clear()
    self.entrada_moodle.clear()
    self.entrada_grupo.setCurrentIndex(0)
    self.entrada_fecha.setDate(QDate.currentDate())
    self.entrada_hora.setTime(QTime.currentTime())
    self.entrada_duracion.setValue(60)
    
    self.cancelado.emit()

  def procesar_siguiente(self):
    materia = self.entrada_materia.text().strip()
    grupo = self.entrada_grupo.currentText()
    id_moodle = self.entrada_moodle.text().strip()
    fecha = self.entrada_fecha.date().toString("yyyy-MM-dd")
    hora = self.entrada_hora.time().toString("HH:mm")
    duracion = self.entrada_duracion.value()
    
    if not materia or not id_moodle or self.entrada_grupo.currentIndex() == 0:
      QMessageBox.warning(self, "Campos Incompletos", "Por favor, complete todos los campos (Materia, Grupo e ID Cuestionario).")
      return
      
    # Agrupar los datos en un diccionario para mandarlos al Paso 2
    datos_examen = {
      "materia": materia,
      "grupo": grupo,
      "id_moodle": id_moodle,
      "fecha": fecha,
      "hora": hora,
      "duracion": duracion
    }
    
    # Emitimos la señal con los datos para ir al paso 2
    self.siguiente.emit(datos_examen)

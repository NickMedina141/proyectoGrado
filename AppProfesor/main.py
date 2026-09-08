# main.py
import sys
from PyQt6.QtWidgets import QApplication
from vista.ventana_login import VentanaLogin
from vista.sala_supervision import SalaSupervision # Quitar despues
from vista.panel_apelaciones import PanelApelaciones # Quitar despues
from vista.ventana_principal import VentanaPrincipal # Quitar despues
if __name__ == '__main__':
  aplicacion = QApplication(sys.argv)
  
  ventana = VentanaLogin()
  
  #ventana = VentanaDashboard()
  #ventana = VentanaPrincipal()
  #ventana = SalaSupervision()
  #ventana = PanelApelaciones()
  ventana.show()

  # Bucle infinito para mantener la ventana viva
  sys.exit(aplicacion.exec())
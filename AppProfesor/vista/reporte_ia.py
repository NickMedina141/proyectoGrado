import os
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6 import uic
from api.cliente_respuesta import cliente_api
from utils.gestor_sesion import sesion_actual

class ReporteIA(QWidget):
  senal_llm_exito = pyqtSignal(dict)
  senal_llm_error = pyqtSignal(str)

  def __init__(self):
    super().__init__()
    self.senal_llm_exito.connect(self.mostrar_resultado_llm)
    self.senal_llm_error.connect(self.mostrar_error_llm)
    
    base_path = os.path.dirname(__file__)
    uic.loadUi(os.path.join(base_path, "reporte_ia.xml"), self)
    
    self.btn_descargar_pdf.setText("Analizar con IA y descargar reportes")
    self.btn_descargar_pdf.setMinimumSize(320, 40)
    self.btn_descargar_pdf.setStyleSheet("background-color: #8E44AD; color: white; border-radius: 6px; font-weight: bold; font-size: 13px;")
    self.btn_descargar_pdf.clicked.connect(self.generar_reporte_llm_global)
    
    self.examenes_ids = []
    self.sesiones_actuales = []
    
    self.combo_examenes.currentIndexChanged.connect(self.actualizar_reporte)

    self.ranking_item_1.setVisible(False)
    self.ranking_item_2.setVisible(False)
    self.ranking_item_3.setVisible(False)
    
  def cargar_examenes(self):
    profesor_id = sesion_actual.obtener_profesor_id()
    if not profesor_id:
      return
      
    self.combo_examenes.blockSignals(True)
    self.combo_examenes.clear()
    self.examenes_ids.clear()
    
    exito, examenes = cliente_api.obtener_mis_examenes(profesor_id)
    if exito and isinstance(examenes, list):
      for ex in examenes:
        control = ex.get("controlAcceso") or {}
        estado = control.get("estadoPin", "")
        if estado == "FINALIZADO":
          materia = ex.get("materiaCodigo") or "Desconocida"
          fecha_dict = ex.get("fechaExamen") or {}
          fecha = fecha_dict.get("horaInicio", "Sin Fecha")
          if "T" in fecha:
            fecha = fecha.split("T")[0]
            
          texto = f"Examen: {materia} - Finalizado el {fecha}"
          self.combo_examenes.addItem(texto)
          id_ex = ex.get("codigoExamen") or ex.get("id")
          self.examenes_ids.append(id_ex)
          
    self.combo_examenes.blockSignals(False)
    
    if self.combo_examenes.count()>0:
      self.actualizar_reporte()

  def actualizar_reporte(self):
    idx = self.combo_examenes.currentIndex()
    if idx < 0 or idx>= len(self.examenes_ids):
      return
      
    codigo_examen = self.examenes_ids[idx]
    exito, sesiones = cliente_api.obtener_sesiones_examen(codigo_examen, todas=True)
    
    if not exito or not isinstance(sesiones, list):
      QMessageBox.warning(self, "Error", "No se pudieron cargar los datos del examen.")
      return
      
    self.sesiones_actuales = sesiones
    
    alumnos_rojos = 0
    alumnos_naranjas = 0
    alumnos_verdes = 0
    
    anomalias_audio = 0
    objetos = 0
    procesos = 0
    teclado = 0
    total_anomalias = 0
    
    ranking = []
    
    for sesion in sesiones:
      sesion_id = sesion.get("sesionId") or sesion.get("id") or ""
      estudiante_id = sesion.get("estudianteId", "Desconocido")
      # Usar el nombre real si viene, si no usar el ID
      nombre_est = sesion.get("nombreEstudiante") or estudiante_id
      
      exito_al, alertas = cliente_api.obtener_alertas(sesion_id)
      if not exito_al or not isinstance(alertas, list):
        alertas = []
        
      cant_alertas = len(alertas)
      if cant_alertas >= 5:
        alumnos_rojos += 1
      elif cant_alertas > 0:
        alumnos_naranjas += 1
      else:
        alumnos_verdes += 1
        
      for al in alertas:
        total_anomalias += 1
        clase = al.get("claseAlerta", "")
        if "AUDIO" in clase:
          anomalias_audio += 1
        elif "VISION" in clase:
          objetos += 1
        elif "PROCESO" in clase:
          procesos += 1
        elif "TECLADO" in clase:
          teclado += 1
          
      if cant_alertas > 0:
        ranking.append({"nombre": f"{nombre_est} ({estudiante_id})", "alertas": cant_alertas, "id": sesion_id})
        
    # Tarjetas Superiores
    self.val_top_rojo.setText(f"{alumnos_rojos} Alumnos")
    self.val_top_naranja.setText(f"{alumnos_naranjas} Alumnos")
    self.val_top_verde.setText(f"{alumnos_verdes} Alumnos")
    
    # Barras
    def calc_pct(valor, total):
      return int((valor / total) * 100) if total>0 else 0
      
    pct_audio = calc_pct(anomalias_audio, total_anomalias)
    pct_objetos = calc_pct(objetos, total_anomalias)
    pct_procesos = calc_pct(procesos, total_anomalias)
    pct_teclado = calc_pct(teclado, total_anomalias)
    
    self.val_an1.setText(f"{pct_audio}%")
    self.bar_an1.setValue(pct_audio)
    
    self.val_an2.setText(f"{pct_objetos}%")
    self.bar_an2.setValue(pct_objetos)
    
    self.val_an3.setText(f"{pct_procesos}%")
    self.bar_an3.setValue(pct_procesos)
    
    try:
      self.val_an4.setText(f"{pct_teclado}%")
      self.bar_an4.setValue(pct_teclado)
    except:
      pass
    
    # Ranking
    ranking.sort(key=lambda x: x["alertas"], reverse=True)
    
    if len(ranking)>0:
      self.ranking_item_1.setVisible(True)
      self.rank_name_1.setText(ranking[0]["nombre"])
      self.rank_al_1.setText(f"{ranking[0]['alertas']} Alertas")
      try: self.btn_ap_1.clicked.disconnect()
      except: pass
      self.btn_ap_1.clicked.connect(lambda checked, name=ranking[0]["nombre"], eid=ranking[0]["id"]: self.ver_detalle(name, eid))
    else:
      self.ranking_item_1.setVisible(False)
      
    if len(ranking)>1:
      self.ranking_item_2.setVisible(True)
      self.rank_name_2.setText(ranking[1]["nombre"])
      self.rank_al_2.setText(f"{ranking[1]['alertas']} Alertas")
      try: self.btn_ap_2.clicked.disconnect()
      except: pass
      self.btn_ap_2.clicked.connect(lambda checked, name=ranking[1]["nombre"], eid=ranking[1]["id"]: self.ver_detalle(name, eid))
    else:
      self.ranking_item_2.setVisible(False)
      
    if len(ranking)>2:
      self.ranking_item_3.setVisible(True)
      self.rank_name_3.setText(ranking[2]["nombre"])
      self.rank_al_3.setText(f"{ranking[2]['alertas']} Alertas")
      try: self.btn_ap_3.clicked.disconnect()
      except: pass
      self.btn_ap_3.clicked.connect(lambda checked, name=ranking[2]["nombre"], eid=ranking[2]["id"]: self.ver_detalle(name, eid))
    else:
      self.ranking_item_3.setVisible(False)
      
    # Veredicto Generativo de IA
    self.texto_veredicto.setText("El análisis global de la clase aparecerá aquí una vez que se genere el reporte con IA.")

  def ver_detalle(self, nombre, id_estudiante):
    parent = self.window()
    if hasattr(parent, "abrir_detalle_estudiante"):
      parent.abrir_detalle_estudiante(nombre, id_estudiante)

  def generar_reporte_llm_global(self):
    """
    Genera un reporte consolidado usando Llama 3 para el examen seleccionado.
    """
    idx = self.combo_examenes.currentIndex()
    if idx < 0 or len(self.sesiones_actuales) == 0:
      from PyQt6.QtWidgets import QMessageBox
      QMessageBox.warning(self, "Atención", "No hay ningún examen o sesión seleccionada para analizar.")
      return
      
    self.btn_descargar_pdf.setEnabled(False)
    self.btn_descargar_pdf.setText("Generando reportes (IA)...")
    
    texto_global = ""
    self.alertas_por_estudiante = {}
    self.mapa_id_corto = {}
    
    for sesion in self.sesiones_actuales:
      s_id = sesion.get("sesionId")
      est_id = sesion.get("estudianteId", "Desc")
      from api.cliente_respuesta import cliente_api
      ex, alertas = cliente_api.obtener_alertas(s_id)
      if ex and isinstance(alertas, list) and len(alertas)>0:
        self.alertas_por_estudiante[est_id] = alertas
        texto_global += f"\n--- Estudiante: {est_id} ---\n"
        for i, al in enumerate(alertas):
          desc = al.get('objetoDetectado', '') or al.get('nombreProceso', '') or al.get('combinacionTeclas', '') or "Comportamiento sospechoso"
          id_real = str(al.get('idAlerta', '0'))
          id_corto = f"E{i+1}"
          self.mapa_id_corto[id_real] = id_corto
          texto_global += f"- ID_{id_corto}: {al.get('claseAlerta', '')} - {desc}\n"
          
    if not texto_global:
      from PyQt6.QtWidgets import QMessageBox
      QMessageBox.information(self, "Clase Limpia", "Ningún estudiante cometió infracciones.")
      self.btn_descargar_pdf.setEnabled(True)
      self.btn_descargar_pdf.setText("Analizar con IA y descargar reportes")
      return

    import threading
    def tarea_llm():
      import json
      import urllib.request
      from PyQt6.QtWidgets import QMessageBox
      from PyQt6.QtCore import QTimer
      
      try:
        print("[LLM] Iniciando hilo para conectar con LM Studio...")
        prompt = f"""Eres un inspector academico. Analiza este registro de incidencias:\n{texto_global}\n
Devuelve UNICAMENTE un JSON valido. En 'resumen_comportamiento' y 'veredicto_final' escribe un análisis general de la CLASE. Para cada estudiante, evalúa CADA ALERTA (usando su ID exacto, por ejemplo ID_E1) en máximo 2 o 3 líneas, indicando si es [FRAUDE], [SOSPECHOSO] o [NORMAL] y una breve justificación.

Usa este formato EXACTO:
{{
  "probabilidad_fraude_porcentaje": 80,
  "resumen_comportamiento": "Analisis del grupo...",
  "veredicto_final": "Conclusion detallada...",
  "estudiantes": [
    {{
      "id": "ID del estudiante",
      "conclusion_general": "Analisis general del estudiante",
      "analisis_evidencias": {{
        "ID_E1": "[FRAUDE] Breve explicacion en 2 lineas...",
        "ID_E2": "[SOSPECHOSO] Breve explicacion..."
      }}
    }}
  ]
}}"""
        
        payload = {
          "model": "local-model",
          "messages": [
            {"role": "system", "content": "Eres un sistema de analisis de fraude en examenes. Respondes SIEMPRE en formato JSON."},
            {"role": "user", "content": prompt}
          ],
          "temperature": 0.2, 
          "max_tokens": 4000
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request("http://127.0.0.1:1234/v1/chat/completions", data=data)
        req.add_header('Content-Type', 'application/json')
        
        print("[LLM] Haciendo POST a LM Studio...")
        try:
          response = urllib.request.urlopen(req, timeout=600.0) # 10 minutos para reportes gigantes
          resp_body = response.read().decode('utf-8')
          print("[LLM] Respuesta recibida exitosamente")
        except urllib.error.URLError as e:
          print(f"[LLM ERROR URL] {e}")
          self.senal_llm_error.emit(f"No se pudo conectar a LM Studio.\n\nAsegurate de que el servidor local de LM Studio este iniciado en el puerto 1234.\nDetalle: {e.reason}")
          return
        except Exception as e:
          print(f"[LLM ERROR EXTRA] {e}")
          self.senal_llm_error.emit(str(e))
          return
        
        resp_json = json.loads(resp_body)
        contenido = resp_json["choices"][0]["message"]["content"].strip()
        
        if contenido.startswith("```json"):
          contenido = contenido[7:]
        elif contenido.startswith("```"):
          contenido = contenido[3:]
        if contenido.endswith("```"):
          contenido = contenido[:-3]
        contenido = contenido.strip()
        
        try:
          datos = json.loads(contenido)
          self.senal_llm_exito.emit(datos)
        except json.JSONDecodeError:
          self.senal_llm_error.emit("LM Studio no devolvio un JSON valido. Intentalo de nuevo.")
          
      except Exception as e:
        self.senal_llm_error.emit(str(e))
        
    t = threading.Thread(target=tarea_llm, daemon=True)
    t.start()

  def mostrar_error_llm(self, mensaje):
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.critical(self, "Error LM Studio", mensaje)
    self.btn_descargar_pdf.setEnabled(True)
    self.btn_descargar_pdf.setText("Analizar con IA y descargar reportes")

  def mostrar_resultado_llm(self, datos_json):
    from PyQt6.QtWidgets import QMessageBox
    self.btn_descargar_pdf.setEnabled(True)
    self.btn_descargar_pdf.setText("Analizar con IA y descargar reportes")
    
    prob = datos_json.get("probabilidad_fraude_porcentaje", 0)
    resumen = datos_json.get("resumen_comportamiento", "Sin resumen")
    veredicto = datos_json.get("veredicto_final", "Inconcluso")
    
    texto_ui = f"Riesgo Promedio: {prob}%\n\nResumen: {resumen}\n\nVeredicto: {veredicto}"
    try:
        self.texto_veredicto.setText(texto_ui)
    except:
        pass
    
    ruta_pdf = self.generar_pdf_reporte(datos_json)
    QMessageBox.information(self, "PDF Generado", f"El reporte con evidencias se guardó en:\n{ruta_pdf}")

  def generar_pdf_reporte(self, datos_json):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    import os
    import textwrap
    
    prob = datos_json.get("probabilidad_fraude_porcentaje", 0)
    resumen = datos_json.get("resumen_comportamiento", "Sin resumen")
    veredicto = datos_json.get("veredicto_final", "Inconcluso")
    estudiantes = datos_json.get("estudiantes", [])

    descargas = os.path.join(os.path.expanduser('~'), 'Downloads', 'Reportes_Fraude_IA')
    os.makedirs(descargas, exist_ok=True)
    
    idx = self.combo_examenes.currentIndex()
    if idx >= 0:
      nombre_examen = self.combo_examenes.currentText().split(" - ")[0].replace("Examen: ", "")
    else:
      nombre_examen = "General"
      
    ruta_pdf = os.path.join(descargas, f"Reporte_Clase_{nombre_examen}.pdf")
    
    c = canvas.Canvas(ruta_pdf, pagesize=letter)
    ancho, alto = letter
    
    # Colores
    color_upc = colors.Color(0, 59/255.0, 19/255.0) # Verde
    color_amarillo = colors.Color(241/255.0, 196/255.0, 15/255.0) # Amarillo UPC
    color_gris = colors.Color(235/255.0, 237/255.0, 239/255.0)
    
    def dibujar_cabecera(c, titulo, subtitulo):
        # Fondo gris claro
        c.setFillColor(color_gris)
        c.rect(0, 0, ancho, alto, fill=1, stroke=0)
        
        # Franja Verde
        c.setFillColor(color_upc)
        c.rect(0, alto - 80, ancho, 80, fill=1, stroke=0)
        # Linea amarilla
        c.setFillColor(color_amarillo)
        c.rect(0, alto - 85, ancho, 5, fill=1, stroke=0)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, alto - 25, "UNIVERSIDAD POPULAR DEL CESAR")
        c.setFont("Helvetica-Bold", 22)
        c.drawString(40, alto - 60, titulo)
        
        c.setFillColor(color_amarillo)
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(ancho - 40, alto - 45, subtitulo)
        c.setFillColor(colors.black)

    # Pagina 1: Analisis Global
    dibujar_cabecera(c, "REPORTE OFICIAL DE I.A.", f"Examen: {nombre_examen}")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, alto - 130, f"Riesgo Promedio de Fraude: {prob}%")
    
    # Caja blanca para el contenido
    c.setFillColor(colors.white)
    c.rect(40, 40, ancho - 80, alto - 200, fill=1, stroke=1)
    c.setFillColor(colors.black)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, alto - 180, "Resumen Global del Comportamiento (Generado por IA):")
    
    c.setFont("Helvetica", 12)
    texto = c.beginText(50, alto - 205)
    
    for parrafo in str(resumen).split('\n'):
        for linea in textwrap.wrap(parrafo, width=85):
            texto.textLine(linea)
            if texto.getY() < 80:
                c.drawText(texto)
                c.showPage()
                dibujar_cabecera(c, "REPORTE OFICIAL DE I.A. (Cont.)", "")
                c.setFillColor(colors.white)
                c.rect(40, 40, ancho - 80, alto - 120, fill=1, stroke=1)
                c.setFillColor(colors.black)
                texto = c.beginText(50, alto - 100)
                texto.setFont("Helvetica", 12)
        texto.moveCursor(0, 10)
        
    texto.moveCursor(0, 15)
    texto.setFont("Helvetica-Bold", 14)
    texto.textLine("Veredicto y Recomendación Final:")
    texto.setFont("Helvetica", 12)
    for parrafo in str(veredicto).split('\n'):
        for linea in textwrap.wrap(parrafo, width=85):
            texto.textLine(linea)
            if texto.getY() < 80:
                c.drawText(texto)
                c.showPage()
                dibujar_cabecera(c, "REPORTE OFICIAL DE I.A. (Cont.)", "")
                c.setFillColor(colors.white)
                c.rect(40, 40, ancho - 80, alto - 120, fill=1, stroke=1)
                c.setFillColor(colors.black)
                texto = c.beginText(50, alto - 100)
                texto.setFont("Helvetica", 12)
        texto.moveCursor(0, 10)
        
    c.drawText(texto)
    
    # Paginas por estudiante
    for est in estudiantes:
      c.showPage()
      id_est = str(est.get("id", "Desconocido"))
      conclusion = str(est.get("conclusion_general", "Sin datos"))
      dict_evidencias = est.get("analisis_evidencias", {})
      
      dibujar_cabecera(c, "Análisis Individual", f"Estudiante: {id_est}")
      
      c.setFillColor(colors.white)
      c.rect(40, 40, ancho - 80, alto - 140, fill=1, stroke=0)
      c.setFillColor(colors.black)
      
      c.setFont("Helvetica-Bold", 14)
      c.drawString(50, alto - 120, "Perfil Psicológico y Conductual (Generado por IA):")
      
      c.setFont("Helvetica", 12)
      texto_est = c.beginText(50, alto - 145)
      for p in conclusion.split('\n'):
          for linea in textwrap.wrap(p, width=85):
              texto_est.textLine(linea)
          texto_est.moveCursor(0, 5)
      c.drawText(texto_est)
      
      y_pos = texto_est.getY() - 30
      
      alertas_est = self.alertas_por_estudiante.get(id_est, [])
      if not alertas_est:
        for k, v in self.alertas_por_estudiante.items():
            if id_est in k or k in id_est:
                alertas_est = v
                break

      for al in alertas_est:
        if y_pos < 300: 
            c.showPage()
            dibujar_cabecera(c, "Evidencias", f"Estudiante: {id_est}")
            c.setFillColor(colors.white)
            c.rect(40, 40, ancho - 80, alto - 140, fill=1, stroke=0)
            c.setFillColor(colors.black)
            y_pos = alto - 120
            
        id_alerta = str(al.get('idAlerta', '0'))
        clase_al = al.get('claseAlerta', '')
        desc = al.get('objetoDetectado', '') or al.get('nombreProceso', '') or al.get('combinacionTeclas', '') or "Evidencia"
        
        # 1. Dibujar Imagen
        img_path = al.get('urlFotoWebcam') or al.get('urlCapturaPantalla')
        if img_path:
            abs_path = os.path.join(os.path.expanduser('~'), 'Documents', 'evidencias_examenes', img_path.replace("/", os.sep).replace("\\", os.sep))
            if os.path.exists(abs_path):
                c.drawImage(abs_path, (ancho - 320)/2, y_pos - 180, width=320, height=180, preserveAspectRatio=True)
                y_pos -= 190
            else:
                c.setFont("Helvetica-Oblique", 10)
                c.setFillColor(colors.gray)
                c.drawString(50, y_pos, "(Imagen guardada en el servidor, no disponible localmente)")
                c.setFillColor(colors.black)
                y_pos -= 20
        else:
            y_pos -= 10
            
        # 2. Dibujar Titulo debajo
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(color_upc)
        
        tipo_ev = ""
        if clase_al == "VISION":
            tipo_ev = "Cámara de Video"
        elif clase_al == "PROCESO":
            tipo_ev = "Programa Bloqueado"
        elif clase_al == "TECLADO":
            tipo_ev = "Atajo Bloqueado"
        elif clase_al == "AUDIO":
            tipo_ev = "Micrófono (Voz)"
        else:
            tipo_ev = clase_al
            
        id_corto = self.mapa_id_corto.get(id_alerta, id_alerta)
        c.drawString(50, y_pos, f"Evidencia {id_corto}: {tipo_ev} - {desc}")
        c.setFillColor(colors.black)
        y_pos -= 20
        
        # 3. Dibujar Analisis IA
        analisis_ia = dict_evidencias.get(f"ID_{id_corto}") or dict_evidencias.get(id_corto) or "La IA no proporcionó un análisis detallado para esta captura."
        c.setFont("Helvetica", 11)
        txt_ev = c.beginText(50, y_pos)
        for p in str(analisis_ia).split('\n'):
            for linea in textwrap.wrap(p, width=95):
                txt_ev.textLine(linea)
        c.drawText(txt_ev)
        
        y_pos = txt_ev.getY() - 40
        
    c.save()
    return ruta_pdf

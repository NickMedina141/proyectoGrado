# Guía Definitiva de Desarrollo: Sistema de Supervisión con IA

Esta guía es el plan de acción maestro para construir el proyecto desde cero, integrando las bases del backend, la evaluación académica y las aplicaciones de supervisión.

---

## 1. Arquitectura Central (El Cerebro del Sistema)

### 1.1. Backend Java y Base de Datos
*   **Java + Spring Boot:** API REST principal para gestión de usuarios, seguridad (JWT), validación de códigos de sesión y recepción de evidencias.
*   **MongoDB (NoSQL):** Base de datos principal seleccionada por su alta velocidad de consulta, flexibilidad para manejar documentos JSON anidados (alertas) y bajo consumo de recursos en grandes volúmenes de eventos.
*   **Gestor de Archivos (Sistema de Archivos Local):** Para el prototipo funcional (MVP) se implementó almacenamiento directo en el disco del servidor (Carpetas locales), un sistema de gestión de objetos muy ligero y gratuito que se instala localmente. Funciona igual que AWS S3, garantizando que el almacenamiento sea rápido, seguro y escalable sin necesidad de programar un gestor desde cero.

### 1.2. Ecosistema Académico
*   **Moodle:** Motor de exámenes y temporizador. Nuestro sistema supervisa mientras el alumno rinde la prueba aquí.

---

## 2. Aplicación del Profesor (El Centro de Control)

**Rol:** Interfaz para que los docentes gestionen sus evaluaciones y auditen los resultados.
*   **Tecnología:** Python (PyQt6 / PySide6).

### Flujo Operativo (Estilo Kahoot):
1.  **Creación:** El profesor inicia sesión, selecciona el examen (conectado a Moodle) y crea una "Sesión de Supervisión".
2.  **Generación de Código:** El sistema genera un código PIN único e irrepetible (estilo Kahoot).
3.  **Distribución:** El profesor comparte este código con sus estudiantes habilitados.
4.  **Auditoría y Reportes:** Al finalizar el examen, la app permite al profesor descargar reportes PDF consolidados con las alertas generadas y el nivel de riesgo de cada estudiante.

---

## 3. Aplicación del Estudiante (El Motor de Proctoring Local)

**Rol:** Cliente de supervisión en tiempo real, seguro y privado.
*   **Tecnología:** Python (PyQt6 / PySide6) con `QWebEngineView` para embeber Moodle.

### Flujo de Acceso:
1.  **Login:** El estudiante ingresa con sus credenciales.
2.  **Validación de Sesión:** Ingresa el código PIN provisto por el profesor. El backend valida que el estudiante pertenezca al curso y autoriza el inicio.
3.  **Evaluación:** Se abre Moodle dentro del navegador embebido (no se puede usar Chrome/Edge normal).

### El Ecosistema Interno (Microservicios Locales):
Para que la interfaz gráfica no se congele mientras se analiza cámara y audio, la aplicación estudiantil se divide en varias capas que corren en el mismo computador del alumno:

1.  **Multihilo Nativo (QThread):** Arquitectura asíncrona dentro del mismo proceso de la app (PyQt6). Es el verdadero "músculo". Su misión vital es recibir los frames y audios, enviarlos a los modelos de IA, y procesar resultados en milisegundos sin trabar la interfaz. 
2.  **Módulo de Biometría e Identidad (DeepFace / FaceNet):** Modelos locales, gratuitos y altamente seguros que **no envían información a internet**. Al iniciar la app, toman la foto del estudiante por la webcam y la comparan matemáticamente con la foto de registro para confirmar su identidad (Anti-Suplantación).
3.  **Módulos de Supervisión (Heredados del Pre-Alfa):**
    *   **MediaPipe:** Postura y movimiento de mirada.
    *   **YOLO11n (Nano):** Detección de objetos prohibidos (celulares, libros).
    *   **PyAudio + Silero VAD + Whisper local:** Grabación local y transcripción de voz silenciada.
    *   **Control de Sistema (`psutil`):** Bloqueo de aplicaciones no permitidas y teclas trampa.

---

## 4. Hoja de Ruta: Orden de Desarrollo

1.  **Backend Core y MongoDB (Semanas 1-2):** Configurar Spring Boot, MongoDB y la lógica de generación de códigos "estilo Kahoot".
2.  **Sistema de Archivos Almacenamiento Local (Carpetas) (Semana 3):** Desplegar Almacenamiento Local (Carpetas) y conectarlo al Backend para la subida fluida de archivos.
3.  **App Estudiante - Base (Semana 4):** Interfaz PyQt, login, validación de código PIN y embeber Moodle.
4.  **App Estudiante - Integración Multihilo (QThread) e IA (Semanas 5-7):** Desplegar tu código pre-alfa dentro de Multihilo (QThread) localmente. Implementar validación de biometría con DeepFace.
5.  **Sincronización (Semana 8):** Conectar la App Estudiante con Spring Boot para el envío de alertas JSON a MongoDB y binarios a Almacenamiento Local (Carpetas).
6.  **App Profesor (Semanas 9-10):** Panel de creación de sesiones y generación de reportes.

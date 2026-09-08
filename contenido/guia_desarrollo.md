# Guía Definitiva de Desarrollo: Sistema de Supervisión con IA

Esta guía es el plan de acción maestro para construir el proyecto desde cero, integrando las bases del backend, la evaluación académica y la aplicación de supervisión (basada en tu versión pre-alfa). Todo está alineado con la Ley 1581 de 2012 de Protección de Datos de Colombia.

---

## 1. Plan de Optimización y Eficiencia
Para garantizar que el software funcione de manera fluida en equipos de bajos recursos sin sacrificar seguridad:
*   **Procesamiento por Intervalos (Frame Skipping):** Modelos como YOLO y MediaPipe no procesarán 30 cuadros por segundo, sino 1 o 2 imágenes por segundo. Esto reduce el consumo de CPU en más del 80%.
*   **Modelos "Nano":** Se usarán exclusivamente versiones ligeras (YOLO11n, Whisper Base).
*   **Asincronismo Local:** El uso de Multihilo Nativo (QThread) evitará que la interfaz visual (PyQt) se congele mientras se analiza la cámara.

---

## 2. Hoja de Ruta: ¿Por dónde empezamos?

El orden de desarrollo debe seguir una lógica de "Adentro hacia Afuera" (Core -> Cliente). 

**Recomendación de inicio: El Backend (Java / Spring Boot) y la Base de Datos.**
¿Por qué? Porque ambas aplicaciones (Docente y Estudiante) comparten el mismo servidor central. Sin el backend listo, ninguna de las dos apps podrá iniciar sesión o interactuar.

### Orden cronológico sugerido:
1.  **Cimientos de Datos (Backend - Semanas 1-2):** Configurar Spring Boot, conectar la base de datos única (**MongoDB**), crear los modelos compartidos gestionados por Roles (Profesor, Estudiante) y configurar la seguridad JWT extrema (con Rotación de Refresh Tokens).
2.  **Gestor de Archivos y Moodle (Semana 3):** Configurar el almacenamiento local en Spring Boot. Levantar el Moodle de prueba y configurar Single Sign-On (SSO).
3.  **App Docente (Semana 4):** Crear la interfaz base (PyQt6). Integrar el navegador embebido para que el profe cree exámenes directamente en Moodle desde la app. Panel de control para lanzar sesiones.
4.  **App Estudiante: Esqueleto (Semana 5):** Interfaz en Python (PyQt6) con login, validación de PIN y Moodle embebido. Implementar **Persistencia de Sesión (Offline-First)** para caídas de internet.
5.  **App Estudiante: Integración Pre-Alfa (Semanas 6-7):** Migrar tus módulos (`deteccion`, `audio`, `control_sistema`) a **Multihilo (QThread)** local. Integrar biometría (**DeepFace**) y modelos open-source de **Hugging Face**.
6.  **Análisis Final y Reportes (Semanas 8-9):** Conectar la App Estudiante para subir archivos al Backend vía HTTP Multipart. Integración de **IA Agnóstica** en el servidor para analizar alertas.

---

## 3. Clasificación de Tecnologías y sus Roles

### 3.1. Backend Central (El Cerebro Único para Ambas Apps)
Habrá una única Base de Datos y un solo servidor manejado por **Roles** (Docente vs. Estudiante).
*   **Java 17+ y Spring Boot:** API REST principal.
*   **Seguridad y Legalidad (Ley 1581 de 2012):** 
    *   **HTTPS:** Obligatorio para proteger los datos en tránsito.
    *   **Cifrado en Reposo (AES-256):** Los datos biométricos (vectores faciales) y Rutas locales se guardarán cifrados en MongoDB usando una "Llave Maestra" en Spring Boot.
    *   **Mitigación Robo de Tokens:** Rotación de Tokens de Acceso cortos y Refresh Tokens seguros.
    *   **Contraseñas:** Cifradas con **Argon2**.
*   **MongoDB (NoSQL):** Base de datos compartida y rapidísima, estructurada para manejar **Polimorfismo** en las alertas (Audio, Visión, Procesos y Teclado viven en la misma colección). Además, gestiona estados como `PFU` (Por Fuera de la Universidad).
*   **Sistema de Archivos Local (MVP):** Almacenamiento directo en disco para optimizar recursos en la demostración.

### 3.2. Ecosistema Académico
*   **Moodle:** Motor de exámenes. El backend validará el `moodle_course_id` antes de dar acceso.
*   **Single Sign-On (SSO):** Autenticación transparente. Al iniciar sesión en nuestra app (Python), se entrará al Moodle embebido ya logueado.

### 3.3. App Docente (Centro de Control y Creación)
*   **Tecnología:** Python (`PyQt6` + `QWebEngineView`).
*   **Creador de Exámenes (Moodle Embebido):** El docente entrará a Moodle sin salir de la app para armar los exámenes interactivos.
*   **Gestión de Sesiones (Control por PIN):** Tras crear el examen, la app genera el PIN de sesión para los alumnos.
*   **Auditoría con IA Agnóstica:** Al terminar, el profe consulta el comportamiento. El servidor usará un modelo de IA (Ej. Ollama Phi-3, GPT-4, configurable a futuro) para leer el historial y redactar el veredicto.

### 3.4. App Estudiante (Motor de Proctoring)
*   **Tecnología:** Python (`PyQt6` + `QWebEngineView`). Requiere login y el PIN de la sesión.
*   **Persistencia de Sesión (Resiliencia Offline-First):** Si el internet se cae, El motor de IA guarda las fotos y alertas en una cola local encriptada y las sincroniza al volver la red.
*   **Procesamiento en Hilos (QThread):** Ejecución paralela nativa. Recibe cámara/audio y procesa a toda velocidad enviando datos a la IA sin congelar la interfaz.
*   **Inteligencia Artificial y Control:**
    *   **DeepFace / FaceNet:** Valida la identidad y detecta **Suplantación**.
    *   **MediaPipe + YOLO11n:** Malla facial, múltiples rostros y celulares.
    *   **PyAudio + Whisper local:** Grabación inteligente por voz y transcripción (incluye nivel de confianza).
    *   **psutil + APIs nativas:** Bloqueo de aplicaciones trampa, registrando el PID (ID del Proceso).

### 3.5. Respaldo Legal (Proceso de Apelación)
Para evitar disputas académicas y legales, el sistema permite que si un estudiante es marcado por fraude, pueda iniciar un **Proceso de Apelación**. El sistema registrará su argumento, la fecha, y permitirá que un comité humano revise las evidencias polimórficas (audio/video) para emitir una resolución final a favor o en contra.

---

## 4. Análisis de tu App Pre-Alfa (`AppSupervision`)

Tu aplicación pre-alfa (`proctoring_app`) está muy bien modularizada. **Evolución:**
1.  **Refactorización hacia Multihilo (QThread):** Tu `ejecutador` actual envolverá `/deteccion` y `/audio` en endpoints locales.
2.  **Identidad Biométrica:** Agregaremos `/biometria` usando DeepFace antes de abrir Moodle.
3.  **Refuerzo Anti-Fraude:** En `/deteccion`, sumaremos modelos gratuitos de Hugging Face a MediaPipe.
4.  **Sincronización:** `/reportes` integrará el sistema **Offline-First**, enviando JSONs a MongoDB y fotos al Backend.
5.  **Seguridad Anti-Cierre:** `/control_sistema` vigilará también el estado de VPN y si se fuerza el cierre, el Moodle embebido bloqueará la sesión.

---

## 5. Anexo: Características "WOW" para la App Docente
Para garantizar que la aplicación del profesor no sea solo funcional, sino un producto de software premium que impresione a la universidad, se deben implementar las siguientes funcionalidades:

*   **Dashboard en Vivo (Estilo Panóptico):** Una vista de cuadrícula donde cada alumno es una tarjeta. Si el motor local detecta fraude, la tarjeta parpadea en rojo en tiempo real en la pantalla del profesor.
*   **Veredicto de la IA (Resumen Ejecutivo):** Un botón que lee todas las alertas de un alumno y genera un reporte humano: *"Riesgo Alto (95%). El alumno miró fuera de la pantalla 15 veces y se detectó audio transcrito de una segunda persona."*
*   **Línea de Tiempo Forense:** Una barra de tiempo (como en un editor de video) para cada alumno. Las alertas son puntos rojos en la línea. Al hacer clic, muestra la foto de la cámara, el audio y el proceso bloqueado en ese segundo exacto.
*   **Centro de Visualización de Evidencias:** El profesor puede reproducir audios sospechosos y ver capturas de pantalla directamente dentro de la App, sin tener que descargar los archivos ni abrir programas externos.
*   **Flujo "Kahoot" Interactivo:** Una sala de espera animada donde el profesor ve cómo se van uniendo los estudiantes mediante su PIN antes de presionar el botón "Iniciar Examen para Todos".
*   **Reportes Legales en 1 Clic:** Generación automática de un PDF formal con el logo de la universidad, fechas, firmas digitales y los enlaces a las evidencias, listo para ser entregado al comité disciplinario.
*   **Intervención en Vivo (Live Override):** El profesor puede enviar un mensaje emergente que bloquea la pantalla de un alumno específico (Ej: *"Por favor, enciende la luz de tu habitación para que la IA pueda ver tu rostro"*).
*   **Moodle Nativo Embebido:** Creación y configuración del examen navegando Moodle como si fuera un navegador web moderno directamente integrado en la app de escritorio.

package com.example.AppSegurity.Services;

import com.example.AppSegurity.Enums.Estado_pin;
import com.example.AppSegurity.Enums.Sensibilidad_IA;
import com.example.AppSegurity.Models.Examen;
import com.example.AppSegurity.Repositorys.ExamenRepository;
import com.example.AppSegurity.Sub_Clases.ConfiguracionExamen;
import com.example.AppSegurity.Sub_Clases.ControlAcceso;
import com.example.AppSegurity.Sub_Clases.FechaExamen;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.example.AppSegurity.Repositorys.SesionSupervisionRepository;

@Service
public class ExamenService {

    //Metodos
    /*
    IniciarExamen() 
    SincronizacionMoodle()
     */
    @Autowired
    private ExamenRepository examenRepository;

    public Examen crearExamen(String codigoProfesor, String moodleCurseId, String moodleQuizId, String materiaCodigo, FechaExamen fecha) {
        //Generamos el PIN de manera aleatoria e irrepetible
        String PIN_aleatorio = UUID.randomUUID().toString().substring(0, 6).toUpperCase();

        //Creamos control de acceso e introducimos el PIN recien generado
        ControlAcceso controlAcceso = new ControlAcceso();
        controlAcceso.setPinSesion(PIN_aleatorio);
        controlAcceso.setEstadoPin(Estado_pin.FINALIZADO); //Cerrado por defecto

        //Creamos una configuración por defecto para el examen en caso de que el profe se olvide
        ConfiguracionExamen configuracionExamenPorDefecto = new ConfiguracionExamen(
                true, // Reconocimiento Facial
                true, // Detección Objetos
                false, // Análisis de Audio
                true, // Monitoreo de Procesos
                true, // Análisis de Teclado
                Sensibilidad_IA.MEDIA,
                120,
                0,
                new ArrayList<String>(),
                new ArrayList<String>());

        //Creamos y armamos al examen con todos los datos listos
        Examen examen = new Examen(
                null,
                codigoProfesor,
                moodleCurseId,
                moodleQuizId,
                materiaCodigo,
                controlAcceso,
                fecha,
                configuracionExamenPorDefecto);

        // guardamos el examen creado y lo retornamos
        return examenRepository.save(examen);

    }

    public Examen configurarRestricciones(String codigoExamen, ConfiguracionExamen nuevConfiguracionExamen) {
        //Se busca el examen creado y se trae de la base de datos
        Examen examen = examenRepository.findById(codigoExamen)
                .orElseThrow(() -> new RuntimeException("Error al traer la información del examenv"));

        //Reemplazamos la configuración del examen creado por la nueva que llega
        examen.setConfiguracionExamen(nuevConfiguracionExamen);

        //Guardamos la configuración en la base de datos
        return examenRepository.save(examen);
    }

    @Autowired
    private SesionSupervisionRepository sesionSupervisionRepository;

    public void abrirSalaExamen(String codigoExamen) {
        //Buscar y traer el examen de la base de datos
        Examen examen = examenRepository.findById(codigoExamen)
                .orElseThrow(() -> new RuntimeException("Error al traer la información del examenv"));

        // Limpiar sesiones previas (fantasmas) para que el examen inicie en blanco
        List<com.example.AppSegurity.Models.SesionSupervision> sesionesViejas = sesionSupervisionRepository.findByExamenId(codigoExamen);
        for (com.example.AppSegurity.Models.SesionSupervision sesion : sesionesViejas) {
            if (sesion.getEstadoSesion() == com.example.AppSegurity.Enums.EstadoSesion.INICIADA) {
                sesion.setEstadoSesion(com.example.AppSegurity.Enums.EstadoSesion.FINALIZADA);
                sesionSupervisionRepository.save(sesion);
            }
        }

        //Cambiamos el estado del PIN del examen a activo
        examen.getControlAcceso().setEstadoPin(Estado_pin.ACTIVO);

        //Guardamos cambios
        examenRepository.save(examen);

    }

    public void cerrarSalaExamen(String codigoExamen) {
        //Buscamos y traemos la info del examen creado de la base de datos
        Examen examen = examenRepository.findById(codigoExamen)
                .orElseThrow(() -> new RuntimeException("Error al traer la información del examenv"));

        //Cambiamos el estado del PIN del examen a finalizado
        examen.getControlAcceso().setEstadoPin(Estado_pin.FINALIZADO);

        //Guardamos cambios
        examenRepository.save(examen);
    }

    public List<Examen> obtenerExamenesProfesor(String profesorId) {
        //Busca y trae todos los examenes que tenga el ID del profesor
        return examenRepository.findByProfesorId(profesorId);
    }
    
    @org.springframework.scheduling.annotation.Scheduled(fixedRate = 60000)
    public void verificarExamenesExpirados() {
        List<Examen> todosExamenes = examenRepository.findAll();
        java.time.LocalDateTime ahora = java.time.LocalDateTime.now();
        
        for (Examen examen : todosExamenes) {
            if (examen.getControlAcceso() != null && examen.getControlAcceso().getEstadoPin() == Estado_pin.ACTIVO) {
                if (examen.getFechaExamen() != null && examen.getFechaExamen().getHoraFin() != null) {
                    if (ahora.isAfter(examen.getFechaExamen().getHoraFin())) {
                        System.out.println("[CRON] Finalizando examen expirado: " + examen.getCodigoExamen());
                        examen.getControlAcceso().setEstadoPin(Estado_pin.FINALIZADO);
                        examenRepository.save(examen);
                        
                        // Cerrar también las sesiones activas
                        List<com.example.AppSegurity.Models.SesionSupervision> sesionesActivas = sesionSupervisionRepository.findByExamenId(examen.getCodigoExamen());
                        for (com.example.AppSegurity.Models.SesionSupervision sesion : sesionesActivas) {
                            if (sesion.getEstadoSesion() == com.example.AppSegurity.Enums.EstadoSesion.INICIADA) {
                                sesion.setEstadoSesion(com.example.AppSegurity.Enums.EstadoSesion.FINALIZADA);
                                sesionSupervisionRepository.save(sesion);
                            }
                        }
                    }
                }
            }
        }
    }

}

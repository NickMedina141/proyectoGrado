package com.example.AppSegurity.Services;

import org.springframework.stereotype.Service;
import java.io.File;
import java.io.FileOutputStream;
import java.time.LocalDate;
import java.util.Base64;
import java.util.UUID;

@Service
public class FileStorageService {

    // Apuntamos a la carpeta de Documentos del usuario actual para respetar su privacidad y sistema de archivos
    private final String BASE_DIR = System.getProperty("user.home") + "/Documents/evidencias_examenes/";

    public String guardarEvidenciaBase64(String base64String, String sesionId, String prefijo, String nombreEstudiante) {
        if (base64String == null || base64String.isEmpty()) {
            return null;
        }

        try {
            // Eliminar cabecera si existe (ej. data:image/webp;base64,...)
            if (base64String.contains(",")) {
                base64String = base64String.split(",")[1];
            }

            byte[] decodedBytes = Base64.getDecoder().decode(base64String);

            // Crear jerarquía de carpetas: C:/evidencias_examenes/NombreEstudiante/sesionId/tipo/
            String pathJerarquia = nombreEstudiante + "/" + sesionId + "/" + prefijo + "/";
            File directorio = new File(BASE_DIR + pathJerarquia);
            
            if (!directorio.exists()) {
                directorio.mkdirs();
            }

            // Generar nombre único con extensión dinámica
            String extension = prefijo.equals("audio") ? ".wav" : ".webp";
            String fileName = prefijo + "_" + UUID.randomUUID().toString().substring(0, 8) + extension;
            File archivo = new File(directorio, fileName);

            try (FileOutputStream fos = new FileOutputStream(archivo)) {
                fos.write(decodedBytes);
            }

            // Retornar la ruta relativa o absoluta para la BD
            return pathJerarquia + fileName;
            
        } catch (Exception e) {
            System.err.println("Error al guardar la evidencia: " + e.getMessage());
            return null;
        }
    }
}

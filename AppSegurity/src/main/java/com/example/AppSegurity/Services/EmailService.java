package com.example.AppSegurity.Services;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
public class EmailService {

    @Autowired
    private JavaMailSender javaMailSender;

    @Async
    public void enviarResolucionApelacion(String correoEstudiante, String nombreEstudiante, String codigoExamen, boolean esAprobada, String motivoProfesor) {
        try {
            MimeMessage mensaje = javaMailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mensaje, true, "UTF-8");

            helper.setTo(correoEstudiante);
            helper.setSubject("Resolucion de Segunda Revision - Examen: " + codigoExamen);

            String colorEstado = esAprobada ? "#27AE60" : "#E74C3C";
            String textoEstado = esAprobada ? "APROBADA A FAVOR" : "RECHAZADA (Sancion Mantenida)";

            String htmlTemplate = "<div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;\">"
                    + "<div style=\"background-color: #003B13; padding: 20px; text-align: center;\">"
                    + "<h2 style=\"color: white; margin: 0;\">Comit&eacute; de Supervisi&oacute;n de Evaluaciones</h2>"
                    + "</div>"
                    + "<div style=\"padding: 30px; background-color: #f9f9f9;\">"
                    + "<p style=\"font-size: 16px; color: #333;\">Estimado/a <strong>" + nombreEstudiante + "</strong>,</p>"
                    + "<p style=\"font-size: 15px; color: #555; line-height: 1.5;\">Le informamos que su solicitud de segunda revisi&oacute;n para el examen <strong>" + codigoExamen + "</strong> ha sido evaluada.</p>"
                    + "<div style=\"margin: 25px 0; padding: 15px; border-left: 5px solid " + colorEstado + "; background-color: white;\">"
                    + "<h3 style=\"margin-top: 0; color: " + colorEstado + ";\">Estado Final: " + textoEstado + "</h3>"
                    + "<p style=\"margin-bottom: 0; font-size: 14px; color: #444;\"><strong>Comentarios del profesor:</strong><br><br><i>\"" + motivoProfesor + "\"</i></p>"
                    + "</div>"
                    + "<p style=\"font-size: 14px; color: #666; margin-top: 30px;\">Este es un mensaje generado autom&aacute;ticamente, por favor no responda a esta direcci&oacute;n.</p>"
                    + "</div>"
                    + "<div style=\"background-color: #eee; padding: 15px; text-align: center; font-size: 12px; color: #888;\">"
                    + "Plataforma de Supervisi&oacute;n Acad&eacute;mica - Universidad Popular del Cesar"
                    + "</div>"
                    + "</div>";

            helper.setText(htmlTemplate, true);
            javaMailSender.send(mensaje);

        } catch (MessagingException e) {
            System.err.println("Error enviando el correo a: " + correoEstudiante);
            e.printStackTrace();
        }
    }
}
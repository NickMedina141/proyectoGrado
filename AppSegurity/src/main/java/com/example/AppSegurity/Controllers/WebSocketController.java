package com.example.AppSegurity.Controllers;

import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.stereotype.Controller;
import java.util.Map;

@Controller
public class WebSocketController {

    @MessageMapping("/comando/{sesionId}")
    @SendTo("/topic/comandos/{sesionId}")
    public Map<String, Object> reenviarComando(@DestinationVariable String sesionId, Map<String, Object> comando) {
        // Simplemente reenviamos el comando tal cual al tópico del estudiante
        return comando;
    }
}

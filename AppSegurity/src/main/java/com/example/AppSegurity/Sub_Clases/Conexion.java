package com.example.AppSegurity.Sub_Clases;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter

public class Conexion {
    //Parametros de la clase
    private String ipEstudiante;
    private String sistemaOperativo;
    private Boolean vpnDetectada;
    private String protocoloConexion;
    
    //Constructor sin parametros
    public Conexion(){
        
    }
    
    //Constructor con parametros
    public Conexion(String ipEstudiante, String sistemaOperativo, Boolean vpnDetectada, String protocoloConexion){
        this.ipEstudiante = ipEstudiante;
        this.sistemaOperativo = sistemaOperativo;
        this.vpnDetectada = vpnDetectada;
        this.protocoloConexion = protocoloConexion; 
    }
    
}

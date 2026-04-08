#include <Servo.h>

// Nombramos los motores
Servo servoPulgar;  // Pin 2
Servo servoIndice;  // Pin 3 (Gira al revés)
Servo servoMedio;   // Pin 4 (AHORA GIRA AL REVÉS)
Servo servoAnular;  // Pin 5
Servo servoMenique; // Pin 6 (Gira al revés)

void setup() {
  Serial.begin(9600); 
  
  servoPulgar.attach(2);
  servoIndice.attach(3);
  servoMedio.attach(4);
  servoAnular.attach(5);
  servoMenique.attach(6);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n'); 
    
    int coma1 = data.indexOf(',');
    int coma2 = data.indexOf(',', coma1 + 1);
    int coma3 = data.indexOf(',', coma2 + 1);
    int coma4 = data.indexOf(',', coma3 + 1);

    if (coma1 > 0 && coma2 > 0 && coma3 > 0 && coma4 > 0) {
      int anguloPulgar  = data.substring(0, coma1).toInt();
      int anguloIndice  = data.substring(coma1 + 1, coma2).toInt();
      int anguloMedio   = data.substring(coma2 + 1, coma3).toInt();
      int anguloAnular  = data.substring(coma3 + 1, coma4).toInt();
      int anguloMenique = data.substring(coma4 + 1).toInt();

      // --- AQUÍ ESTÁ LA MAGIA DE LA INVERSIÓN ---
      servoPulgar.write(anguloPulgar);               // Normal (Pin 2)
      servoIndice.write(180 - anguloIndice);         // ¡Gira al revés! (Pin 3)
      servoMedio.write(180 - anguloMedio);           // ¡NUEVO: Gira al revés! (Pin 4)
      servoAnular.write(anguloAnular);               // Normal (Pin 5)
      servoMenique.write(180 - anguloMenique);       // ¡Gira al revés! (Pin 6)
    }
  }
}
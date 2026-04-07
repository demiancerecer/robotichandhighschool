import cv2
import mediapipe as mp
import serial
import time
import math

# --- CONFIGURACIÓN DEL ARDUINO ---
puerto_arduino = 'COM3' 

try:
    arduino = serial.Serial(puerto_arduino, 9600, timeout=1)
    print("Conectado al Arduino exitosamente.")
    time.sleep(2) 
    
    # Mandamos todo a 0 (Mano Abierta) al arrancar para calibrar
    print("Forzando posición inicial: MANO ABIERTA (0 grados para todos)...")
    arduino.write("0,0,0,0,0\n".encode())
    time.sleep(3) 
    
except Exception as e:
    print(f"Error al conectar con Arduino: {e}")
    print("El programa funcionará en pantalla, pero no mandará señal a motores.")
    arduino = None

# --- CONFIGURACIÓN DE MEDIAPIPE ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

def calcular_distancia(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def mapear(valor, in_min, in_max, out_min, out_max):
    if in_min < in_max:
        valor = max(min(valor, in_max), in_min)
    else:
        valor = max(min(valor, in_min), in_max)
    return int((valor - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def escalonar_angulo(angulo_calculado, tipo_dedo):
    if tipo_dedo == 'pulgar':
        # ¡NUEVO: Solo 2 etapas y menos giro!
        if angulo_calculado < 90: 
            return 0    # Etapa 1: Totalmente abierto
        else: 
            return 90   # Etapa 2: Cerrado (Pero solo a la mitad del giro para que no jale tanto)
            
    elif tipo_dedo == 'menique':
        if angulo_calculado < 90: return 0
        else: return 180
            
    else:
        # Los demás dedos siguen teniendo sus etapas normales
        if angulo_calculado < 30: return 0
        elif angulo_calculado < 90: return 60
        elif angulo_calculado < 150: return 120
        else: return 180

# --- INICIAR CÁMARA ---
cap = cv2.VideoCapture(0)

puntas = [4, 8, 12, 16, 20]
bases = [2, 5, 9, 13, 17]

while True:
    success, img = cap.read()
    if not success:
        break

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            lista_angulos = []
            muneca = hand_landmarks.landmark[0]
            
            base_medio = hand_landmarks.landmark[9]
            tamano_mano = calcular_distancia(muneca, base_medio)

            for i in range(5):
                if i != 0:
                    punta = hand_landmarks.landmark[puntas[i]]
                    base = hand_landmarks.landmark[bases[i]]
                    dist_doblez = calcular_distancia(punta, base)
                    proporcion = dist_doblez / tamano_mano if tamano_mano > 0 else 0

                if i == 0: 
                    punta_pulgar = hand_landmarks.landmark[4]
                    base_menique = hand_landmarks.landmark[17]
                    dist_pulgar = calcular_distancia(punta_pulgar, base_menique)
                    proporcion_pulgar = dist_pulgar / tamano_mano if tamano_mano > 0 else 0
                    
                    angulo_bruto = mapear(proporcion_pulgar, 0.65, 1.0, 180, 0)
                    angulo_final = escalonar_angulo(angulo_bruto, 'pulgar')
                    
                elif i == 1:
                    angulo_bruto = mapear(proporcion, 0.25, 0.70, 180, 0)
                    angulo_final = escalonar_angulo(angulo_bruto, 'normal')
                    
                elif i == 4:
                    angulo_bruto = mapear(proporcion, 0.20, 0.65, 180, 0)
                    angulo_final = escalonar_angulo(angulo_bruto, 'menique')
                    
                else: 
                    angulo_bruto = mapear(proporcion, 0.3, 0.75, 180, 0)
                    angulo_final = escalonar_angulo(angulo_bruto, 'normal')
                
                lista_angulos.append(angulo_final)

            # --- ENVIAR DATOS ---
            mensaje = f"{lista_angulos[0]},{lista_angulos[1]},{lista_angulos[2]},{lista_angulos[3]},{lista_angulos[4]}\n"
            
            if arduino:
                arduino.write(mensaje.encode())
            
            cv2.putText(img, f"Enviando: {mensaje.strip()}", (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
            time.sleep(0.05) 

    cv2.imshow("Camara", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
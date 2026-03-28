import cv2
import mediapipe as mp

# Inicializar Face Mesh de MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("No se puede abrir la camara")
    exit()

print("Buscando cara... Pulsa ESC para salir.")

while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    
    # MediaPipe necesita formato RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        # Cara detectada!
        cv2.putText(frame, "Cara detectada", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Prueba Face Mesh", frame)

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()

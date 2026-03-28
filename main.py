import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("No se puede abrir la camara")
    exit()

print("Calculando ratio de iris... Pulsa ESC para salir.")

while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        # Puntos de referencia de los parpados
        left_eye = [landmarks[145], landmarks[159]]
        right_eye = [landmarks[374], landmarks[386]]

        lx = int((left_eye[0].x + left_eye[1].x) / 2 * width)
        ly = int((left_eye[0].y + left_eye[1].y) / 2 * height)
        rx = int((right_eye[0].x + right_eye[1].x) / 2 * width)
        ry = int((right_eye[0].y + right_eye[1].y) / 2 * height)

        box_size = 45
        cv2.rectangle(frame, (lx - box_size, ly - box_size), (lx + box_size, ly + box_size), (10, 255, 0), 2)
        cv2.rectangle(frame, (rx - box_size, ry - box_size), (rx + box_size, ry + box_size), (10, 255, 0), 2)

        # Iris: 468 (izquierdo), 473 (derecho)
        l_iris = landmarks[468]
        r_iris = landmarks[473]

        # Calculo de la altura del iris respecto al parpado superior e inferior
        l_ratio = (l_iris.y - left_eye[1].y) / (left_eye[0].y - left_eye[1].y + 1e-6)
        r_ratio = (r_iris.y - right_eye[1].y) / (right_eye[0].y - right_eye[1].y + 1e-6)
        avg_ratio = (l_ratio + r_ratio) / 2.0

        # Si el valor baja mucho, es que esta mirando hacia abajo (hacia el movil)
        cv2.putText(frame, f"Ratio mirada: {avg_ratio:.2f}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("Ratio del Iris", frame)

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()

import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("No se puede abrir la camara")
    exit()

print("Buscando ojos... Pulsa ESC para salir.")

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
        # Ojo izquierdo: inferior (145), superior (159)
        # Ojo derecho: inferior (374), superior (386)
        left_eye = [landmarks[145], landmarks[159]]
        right_eye = [landmarks[374], landmarks[386]]

        # Centro de cada ojo en pixeles
        lx = int((left_eye[0].x + left_eye[1].x) / 2 * width)
        ly = int((left_eye[0].y + left_eye[1].y) / 2 * height)
        rx = int((right_eye[0].x + right_eye[1].x) / 2 * width)
        ry = int((right_eye[0].y + right_eye[1].y) / 2 * height)

        # Dibujar cajitas verdes alrededor de los ojos
        box_size = 45
        cv2.rectangle(frame, (lx - box_size, ly - box_size), (lx + box_size, ly + box_size), (10, 255, 0), 2)
        cv2.rectangle(frame, (rx - box_size, ry - box_size), (rx + box_size, ry + box_size), (10, 255, 0), 2)

    cv2.imshow("Seguimiento de Ojos", frame)

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()

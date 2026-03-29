import cv2
import mediapipe as mp

def draw_warning(frame, text="LOCK IN TWIN"):
    """Dibuja un rectangulo semitransparente arriba con mensaje de aviso."""
    h, w = frame.shape[:2]
    box_w, box_h = 500, 70
    x1 = (w - box_w) // 2
    y1 = 24
    x2 = x1 + box_w
    y2 = y1 + box_h

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (15, 0, 15), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    cv2.rectangle(frame, (x1 - 2, y1 - 2), (x2 + 2, y2 + 2), (80, 255, 160), 4)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 255, 160), 2)

    cv2.putText(
        frame,
        text.upper(),
        (x1 + 26, y1 + 48),
        cv2.FONT_HERSHEY_DUPLEX,
        1.1,
        (255, 255, 255),
        3,
        cv2.LINE_AA,
    )

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("No se puede abrir la camara")
    exit()

# Umbral inicial para considerar que mira hacia abajo
looking_down_threshold = 0.25

while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    is_looking_down = False

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark

        left_eye = [landmarks[145], landmarks[159]]
        right_eye = [landmarks[374], landmarks[386]]

        lx = int((left_eye[0].x + left_eye[1].x) / 2 * width)
        ly = int((left_eye[0].y + left_eye[1].y) / 2 * height)
        rx = int((right_eye[0].x + right_eye[1].x) / 2 * width)
        ry = int((right_eye[0].y + right_eye[1].y) / 2 * height)

        box_size = 45
        cv2.rectangle(frame, (lx - box_size, ly - box_size), (lx + box_size, ly + box_size), (10, 255, 0), 2)
        cv2.rectangle(frame, (rx - box_size, ry - box_size), (rx + box_size, ry + box_size), (10, 255, 0), 2)

        l_iris = landmarks[468]
        r_iris = landmarks[473]

        l_ratio = (l_iris.y - left_eye[1].y) / (left_eye[0].y - left_eye[1].y + 1e-6)
        r_ratio = (r_iris.y - right_eye[1].y) / (right_eye[0].y - right_eye[1].y + 1e-6)
        avg_ratio = (l_ratio + r_ratio) / 2.0

        is_looking_down = avg_ratio < looking_down_threshold
        cv2.putText(frame, f"Ratio: {avg_ratio:.2f}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    if is_looking_down:
        draw_warning(frame, "DOOMSCROLLING DETECTED")

    cv2.imshow("Skeleton Meme - Aviso", frame)

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()

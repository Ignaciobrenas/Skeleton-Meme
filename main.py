import os
import platform
import subprocess
import time
from pathlib import Path
import cv2
import mediapipe as mp

IS_MACOS = platform.system() == "Darwin"
_video_cap = None

def osascript(script: str) -> None:
    if not IS_MACOS:
        return
    subprocess.run(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

def play_video(video_path: Path) -> None:
    global _video_cap
    if IS_MACOS:
        absolute_path = str(video_path.resolve())
        script = f'''
        tell application "QuickTime Player"
            activate
            set doc to open POSIX file "{absolute_path}"
            tell doc
                play
                set presenting to false
                tell front window
                    set bounds to {{25, 45, 415, 825}}
                end tell
            end tell
        end tell
        '''
        osascript(script)
    else:
        # En Windows abrimos el video con OpenCV para no necesitar programas externos
        if _video_cap is None:
            _video_cap = cv2.VideoCapture(str(video_path.resolve()))

def render_video_alarm() -> None:
    global _video_cap
    if IS_MACOS or _video_cap is None:
        return

    ret, vid_frame = _video_cap.read()
    if not ret or vid_frame is None:
        # Repetir el video en bucle
        _video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, vid_frame = _video_cap.read()

    if ret and vid_frame is not None:
        h, w = vid_frame.shape[:2]
        target_w = 360
        target_h = int(h * (target_w / w))
        resized = cv2.resize(vid_frame, (target_w, target_h))
        cv2.imshow("Doomscroll Alarm - Skyrim Skeleton", resized)

def close_video(video_path: Path) -> None:
    global _video_cap
    if IS_MACOS:
        video_name = video_path.name
        script = f'''
        tell application "QuickTime Player"
            repeat with d in documents
                try
                    if (name of d) is "{video_name}" then
                        stop d
                        close d saving no
                    end if
                end try
            end repeat
        end tell
        '''
        osascript(script)
    else:
        if _video_cap is not None:
            _video_cap.release()
            _video_cap = None
        try:
            cv2.destroyWindow("Doomscroll Alarm - Skyrim Skeleton")
        except cv2.error:
            pass

def draw_warning(frame, text="LOCK IN TWIN"):
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

skyrim_skeleton_video = Path("./assets/skyrim-skeleton.mp4").resolve()
if not skyrim_skeleton_video.exists():
    print(f"No se encuentra el video en {skyrim_skeleton_video}")
    exit()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("No se puede abrir la camara")
    exit()

timer = 2.0
looking_down_threshold = 0.25

doomscroll_start = None
video_playing = False

while True:
    ret, frame = cam.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    now = time.time()
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

        if is_looking_down:
            if doomscroll_start is None:
                doomscroll_start = now

            tiempo_mirando = now - doomscroll_start
            if tiempo_mirando >= timer:
                if not video_playing:
                    play_video(skyrim_skeleton_video)
                    video_playing = True
        else:
            doomscroll_start = None
            if video_playing:
                close_video(skyrim_skeleton_video)
                video_playing = False

        cv2.putText(frame, f"Ratio: {avg_ratio:.2f}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    else:
        doomscroll_start = None
        if video_playing:
            close_video(skyrim_skeleton_video)
            video_playing = False

    if video_playing:
        render_video_alarm()
        draw_warning(frame, "DOOMSCROLLING ALARM")

    cv2.imshow("Skeleton Meme", frame)

    if cv2.waitKey(1) == 27:
        break

if video_playing:
    close_video(skyrim_skeleton_video)

cam.release()
cv2.destroyAllWindows()

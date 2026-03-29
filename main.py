import os
import platform
import subprocess
import sys
import time
from pathlib import Path
import cv2
import mediapipe as mp

# Ensure utf-8 encoding for console prints on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Platform detection
IS_MACOS = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

# Global video capture object for Windows / Linux playback
_video_cap = None


def osascript(script: str) -> None:
    """Executes an AppleScript command on macOS."""
    if not IS_MACOS:
        return
    subprocess.run(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def play_video(video_path: Path) -> None:
    """
    Triggers video playback when doomscrolling is detected.
    - On macOS: Controls QuickTime Player via AppleScript.
    - On Windows / Linux: Initializes an OpenCV video capture stream.
    """
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
        if _video_cap is None:
            _video_cap = cv2.VideoCapture(str(video_path.resolve()))


def render_video_alarm() -> None:
    """Renders the video frame-by-frame in an OpenCV window on Windows/Linux."""
    global _video_cap
    if IS_MACOS or _video_cap is None:
        return

    ret, vid_frame = _video_cap.read()
    if not ret or vid_frame is None:
        # Loop video from the beginning
        _video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, vid_frame = _video_cap.read()

    if ret and vid_frame is not None:
        # Scale to a neat phone-like portrait dimension (360x640)
        h, w = vid_frame.shape[:2]
        target_w = 360
        target_h = int(h * (target_w / w))
        resized = cv2.resize(vid_frame, (target_w, target_h))
        cv2.imshow("Doomscroll Alarm - Skyrim Skeleton", resized)


def close_video(video_path: Path) -> None:
    """
    Closes the video player when user looks back up.
    - On macOS: Closes QuickTime document via AppleScript.
    - On Windows / Linux: Releases video stream and destroys OpenCV window.
    """
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


def draw_warning(frame, text: str = "LOCK IN TWIN") -> None:
    """Draws a stylized translucent cyberpunk-themed warning banner on top of the webcam feed."""
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


def main() -> None:
    """Main computer vision loop tracking eyes and triggering the meme alarm."""
    # Threshold & timing settings
    timer = 2.0                    # Seconds user must look down continuously before alarm fires
    looking_down_threshold = 0.25  # Sensitivity: iris ratio below this triggers looking down state
    debounce_threshold = 0.45      # Hysteresis: iris ratio above this required to deactivate alarm

    # Validate asset
    assets_dir = Path(__file__).resolve().parent / "assets"
    skyrim_skeleton_video = assets_dir / "skyrim-skeleton.mp4"
    if not skyrim_skeleton_video.exists():
        print(f"Error: Could not locate video asset at {skyrim_skeleton_video}")
        return

    # Initialize MediaPipe Face Mesh model with iris landmarks enabled
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # Open webcam
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Error: Could not access webcam. Please check your camera permissions.")
        return

    print("==================================================")
    print(" [!] Skeleton Meme - Doomscroll Stopper Active! [!]")
    print(" Tracking iris movement. Press ESC in window to exit.")
    print("==================================================")

    doomscroll_start_time = None
    video_playing = False

    try:
        while True:
            ret, frame = cam.read()
            if not ret:
                continue

            # Mirror webcam feed horizontally for intuitive user experience
            frame = cv2.flip(frame, 1)
            height, width, _ = frame.shape

            # MediaPipe requires RGB format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = face_mesh.process(rgb_frame)
            face_landmark_points = processed.multi_face_landmarks

            current_time = time.time()

            if face_landmark_points:
                landmarks = face_landmark_points[0].landmark

                # Eye corner reference landmarks
                # Left eye: lower eyelid (145), upper eyelid (159)
                # Right eye: lower eyelid (374), upper eyelid (386)
                left_eye = [landmarks[145], landmarks[159]]
                right_eye = [landmarks[374], landmarks[386]]

                # Draw green eye tracking bounding boxes
                lx = int((left_eye[0].x + left_eye[1].x) / 2 * width)
                ly = int((left_eye[0].y + left_eye[1].y) / 2 * height)
                rx = int((right_eye[0].x + right_eye[1].x) / 2 * width)
                ry = int((right_eye[0].y + right_eye[1].y) / 2 * height)

                box_size = 45
                cv2.rectangle(frame, (lx - box_size, ly - box_size), (lx + box_size, ly + box_size), (10, 255, 0), 2)
                cv2.rectangle(frame, (rx - box_size, ry - box_size), (rx + box_size, ry + box_size), (10, 255, 0), 2)

                # Irises: Left iris center (468), Right iris center (473)
                l_iris = landmarks[468]
                r_iris = landmarks[473]

                # Vertical iris ratio: relative position between upper and lower eyelids
                l_ratio = (l_iris.y - left_eye[1].y) / (left_eye[0].y - left_eye[1].y + 1e-6)
                r_ratio = (r_iris.y - right_eye[1].y) / (right_eye[0].y - right_eye[1].y + 1e-6)
                avg_ratio = (l_ratio + r_ratio) / 2.0

                # Determine gaze state with hysteresis debouncing
                if video_playing:
                    is_looking_down = avg_ratio < debounce_threshold
                else:
                    is_looking_down = avg_ratio < looking_down_threshold

                # Handle timer and triggering
                if is_looking_down:
                    if doomscroll_start_time is None:
                        doomscroll_start_time = current_time

                    if (current_time - doomscroll_start_time) >= timer:
                        if not video_playing:
                            play_video(skyrim_skeleton_video)
                            video_playing = True
                else:
                    doomscroll_start_time = None
                    if video_playing:
                        close_video(skyrim_skeleton_video)
                        video_playing = False
            else:
                # No face in frame - reset timer and close video
                doomscroll_start_time = None
                if video_playing:
                    close_video(skyrim_skeleton_video)
                    video_playing = False

            # Display warning HUD and render video frame if triggered
            if video_playing:
                render_video_alarm()
                draw_warning(frame, "DOOMSCROLLING ALARM")

            cv2.imshow("Skeleton Meme - Lock In", frame)
            key = cv2.waitKey(1)
            if key == 27:  # ESC key
                break

    finally:
        if video_playing:
            close_video(skyrim_skeleton_video)
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

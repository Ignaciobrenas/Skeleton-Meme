import cv2

# Abrir camara por defecto
cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("No se puede abrir la camara")
    exit()

print("Camara funcionando. Pulsa ESC para salir.")

while True:
    ret, frame = cam.read()
    if not ret:
        break

    # Voltear la imagen horizontalmente para que sea como un espejo
    frame = cv2.flip(frame, 1)

    cv2.imshow("Prueba Camara", frame)

    # Tecla ESC para salir
    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()

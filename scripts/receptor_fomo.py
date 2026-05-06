import socket

UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))

print(f"Escuchando mensajes del ESP32-S3 en puerto {UDP_PORT}...")
print("Presiona Ctrl+C para salir\n")

while True:
    data, addr = sock.recvfrom(1024)
    mensaje = data.decode("utf-8", errors="ignore").strip()

    # Colorear alertas en terminal
    if "ALERTA" in mensaje or "RIESGO" in mensaje:
        print(f"\033[91m{mensaje}\033[0m")   # rojo
    elif "OK" in mensaje:
        print(f"\033[92m{mensaje}\033[0m")   # verde
    else:
        print(mensaje)
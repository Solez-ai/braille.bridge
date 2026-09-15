import socket
import threading
import pyautogui

# Adjust sensitivity multiplier to your preference (higher = faster cursor)
SENSITIVITY = 1.3

# Configure PyAutoGUI settings for high performance
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

DISCOVERY_PORT = 9998
CONTROL_PORT = 9999

def get_computer_ip():
    """Finds the actual active local IP address of this computer."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not need to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def run_discovery_listener():
    """Listens for 'DISCOVER_REQUEST' broadcasts on 9998 and replies to pair the phone."""
    discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    discover_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    discover_socket.bind(('', DISCOVERY_PORT))
    print(f"[Discovery] Listening for pairing broadcasts on UDP port {DISCOVERY_PORT}...")

    while True:
        try:
            data, addr = discover_socket.recvfrom(1024)
            message = data.decode('utf-8').strip()
            if message == "DISCOVER_REQUEST":
                print(f"[Discovery] Received discovery request from phone at {addr[0]}. Replying...")
                response = f"DISCOVER_RESPONSE,{CONTROL_PORT}"
                discover_socket.sendto(response.encode('utf-8'), addr)
        except Exception as e:
            print(f"[Discovery] Error: {e}")

def run_control_listener():
    """Listens for touch events and shortcuts on 9999 and acts on them."""
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    control_socket.bind(('', CONTROL_PORT))
    print(f"[Control] Command receiver bound to UDP port {CONTROL_PORT}...")
    print("[Status] Ready to receive touch inputs!\n")

    while True:
        try:
            data, addr = control_socket.recvfrom(1024)
            cmd = data.decode('utf-8').strip()

            # 1. Heartbeat packet (Keep connection alive, quiet log)
            if cmd == "h":
                continue

            print(f"[Event] Received action: {cmd}")

            # 2. Movement / Drag events -> "m,dx,dy"
            if cmd.startswith("m,"):
                parts = cmd.split(",")
                if len(parts) == 3:
                    dx = int(float(parts[1]) * SENSITIVITY)
                    dy = int(float(parts[2]) * SENSITIVITY)
                    pyautogui.moveRel(dx, dy)

            # 3. Mouse Wheel / Scroll -> "s,dx,dy"
            elif cmd.startswith("s,"):
                parts = cmd.split(",")
                if len(parts) == 3:
                    dy = int(parts[2])
                    pyautogui.scroll(dy * 120)

            # 4. Button Click States (Left, Middle, Right down/up)
            elif cmd == "ld":
                pyautogui.mouseDown(button='left')
            elif cmd == "lu":
                pyautogui.mouseUp(button='left')
            elif cmd == "md":
                pyautogui.mouseDown(button='middle')
            elif cmd == "mu":
                pyautogui.mouseUp(button='middle')
            elif cmd == "rd":
                pyautogui.mouseDown(button='right')
            elif cmd == "ru":
                pyautogui.mouseUp(button='right')

            # 5. Hotkeys -> "k,key"
            elif cmd.startswith("k,"):
                key = cmd.split(",")[1].lower()
                print(f"  -> Pressing shortcut: {key}")
                pyautogui.press(key)

        except Exception as e:
            print(f"[Control] Error processing command: {e}")

if __name__ == "__main__":
    computer_ip = get_computer_ip()
    print("=========================================")
    print("      CAD TOUCHPAD COMPANION APP         ")
    print("=========================================")
    print(f" COMPUTER IP: {computer_ip}")
    print(f" CONTROL PORT: {CONTROL_PORT}")
    print("=========================================\n")

    # Run auto-discovery responder on a background thread
    discovery_thread = threading.Thread(target=run_discovery_listener, daemon=True)
    discovery_thread.start()

    # Run control receiver on the main thread
    run_control_listener()

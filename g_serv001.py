import socket
import select
import network
import json

# Wi-Fi credentials
WIFI_SSID = "Vodafone-91D4"
WIFI_PASSWORD = "G632fR6zeT2bH7bc"

# Server Port (Must match your router's internal port forwarding configuration)
SERVER_PORT = 12346
enter_data = {}

def connect_to_wifi():
    """Connect to Wi-Fi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connecting to Wi-Fi...")
    
    while not wlan.isconnected():
        pass

    print("Wi-Fi connected!")
    print("IP Address:", wlan.ifconfig()[0])

def start_server():
    """Start the server and handle multiple clients without threading."""
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', SERVER_PORT))
    server_socket.listen(5)
    server_socket.setblocking(False)  # Set non-blocking mode
    print(f"Server is listening on port {SERVER_PORT}")

    # List of sockets to monitor for incoming data
    sockets_list = [server_socket]

    # Dictionary to store client addresses
    clients = {}

    try:
        while True:
            # Use select to monitor sockets for readability
            readable, _, _ = select.select(sockets_list, [], [], 0.5)

            for notified_socket in readable:
                if notified_socket == server_socket:
                    # Handle new connection
                    client_socket, client_address = server_socket.accept()
                    client_socket.setblocking(False)  # Set non-blocking mode for the client
                    sockets_list.append(client_socket)
                    clients[client_socket] = client_address
                    print(f"New connection from {client_address}")
                else:
                    # Handle data from an existing client
                    try:
                        data = notified_socket.recv(1024).decode('utf-8')
                        if data:
                            print(f"Received from {clients[notified_socket]}: {data}")
                            responses = data.splitlines()
                            # Check if data starts and ends with valid JSON characters
                            for res in responses:
                                try:
                                    json_data = json.loads(res)
                                    enter_data.update({client_address[0]: json_data})
                                    response = enter_data

                                    # Echo the response to all connected clients
                                    for client in clients.keys():
                                        client.send(json.dumps(response).encode('utf-8'))
                                    # Acquire lock before modifying shared data
                                except json.JSONDecodeError as e:
                                    print(f"Error decoding JSON: {e}")
                        else:
                            # No data means client disconnected
                            print(f"Client {clients[notified_socket]} disconnected.")
                            sockets_list.remove(notified_socket)
                            del clients[notified_socket]
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from {clients[notified_socket]}: {e}")
                    except Exception as e:
                        print(f"Error with client {clients[notified_socket]}: {e}")
                        sockets_list.remove(notified_socket)
                        del clients[notified_socket]

    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        server_socket.close()

# Main Execution
try:
    connect_to_wifi()
    start_server()
except KeyboardInterrupt:
    print("Server stopped.")

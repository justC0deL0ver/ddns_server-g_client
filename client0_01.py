import socket
import threading
import pygame
import sys
import json

# Server details
SERVER_HOST = "esp32hostgame.hopto.org"  # Your DDNS hostname
SERVER_PORT = 12346  # External port set in your router


class rect:
    def __init__(self, position_X: int, position_Y: int, Color: str, OWner):
        self.owner = OWner
        self.color = Color
        self.position_x = position_X
        self.position_y = position_Y

    def show(self, surface, positionx: int, positiony: int):
        self.position_x = positionx
        self.position_y = positiony
        pygame.draw.rect(surface, self.color, (self.position_x, self.position_y, 10, 10))


# Global variables
received_data = {'client1':{'position_X': 100, 'position_Y': 200, 'color': 2555}}
self_data = {'position_X': 50, 'position_Y': 50, 'color': [0,255,0]}
square_position = [300, 300]  # Initial square position (x, y)
lock = threading.Lock()  # Lock for synchronizing shared data

def receive_data(client_socket):
    """Thread for receiving data from the server."""
    global self_data
    global received_data
    try:
        while True:
            # Receive the data from the socket
            response = client_socket.recv(1024).decode('utf-8')
            if not response:
                print("Server closed the connection.")
                break
            print(f"Response from server: {response}")

            # Check if we have multiple JSON objects in the response
            # Split the response by some delimiter (e.g., newline, space) if necessary
            responses = response.splitlines()  # Assumes each JSON object is on a new line

            # Process each received dictionary
            for res in responses:
                try:
                    received_dict = json.loads(res)
                    # Acquire lock before modifying shared data
                    with lock:
                        received_data.update(received_dict)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"Error receiving data: {e}")
    finally:
        client_socket.close()



def send_data(client_socket):
    global self_data
    global received_data
    """Thread for sending data to the server."""
    try:
        while True:
            with lock:  # Lock data before sending
                message = json.dumps(self_data) + '\n'
            client_socket.send(message.encode('utf-8'))
            print(f"Sent to server: {message}")
    except Exception as e:
        print(f"Error sending data: {e}")
    finally:
        client_socket.close()


def displaying():
    """Pygame thread to display and move a square."""
    global self_data
    global received_data
    global square_position

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((600, 600))  # Window size
    pygame.display.set_caption("Square Movement")

    clock = pygame.time.Clock()
    square_size = 50  # Square size

    while True:
        # Acquire lock before accessing shared data
        with lock:
            # Handle received data (update shape if necessary)
            for client in received_data:
                if 'shape' not in received_data[client]:
                    received_data[client].update({'shape': rect(
                        received_data[client]['position_X'],
                        received_data[client]['position_Y'],
                        received_data[client]['color'],
                        client
                    )})
                else:
                    received_data[client]['shape'].show(screen,
                                                         received_data[client]['position_X'],
                                                         received_data[client]['position_Y'])

        # Pygame event loop for user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Check for key presses
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            with lock:  # Lock before modifying shared data
                self_data['position_Y'] -= 5  # Move up
        if keys[pygame.K_DOWN]:
            with lock:
                self_data['position_Y'] += 5  # Move down
        if keys[pygame.K_LEFT]:
            with lock:
                self_data['position_X'] -= 5  # Move left
        if keys[pygame.K_RIGHT]:
            with lock:
                self_data['position_X'] += 5  # Move right

        # Clear screen
        screen.fill((0, 0, 0))  # Black background
        # Draw the square
        pygame.draw.rect(screen, self_data['color'], (self_data['position_X'], self_data['position_Y'], square_size, square_size))

        # Update the display
        pygame.display.flip()
        clock.tick(30)  # Limit to 30 frames per second


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")

        # Start threads for sending, receiving, and displaying data
        thread_receive = threading.Thread(target=receive_data, args=(client_socket,))
        thread_display = threading.Thread(target=displaying)
        thread_send = threading.Thread(target=send_data, args=(client_socket,))

        thread_receive.start()
        thread_display.start()
        thread_send.start()

        # Wait for threads to complete
        thread_receive.join()
        thread_send.join()
        thread_display.join()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()

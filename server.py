import socket, threading, json, random, re, os

players, clients, chat_history, banned_ips = {}, [], [], []
HOST, PORT, MAX_DIST = '0.0.0.0', 55555, 50
lock = threading.Lock()
BANNED_IPS_FILE = "banned_ips.json"

# Load banned IPs from file
if os.path.exists(BANNED_IPS_FILE):
    with open(BANNED_IPS_FILE, "r") as f:
        banned_ips = json.load(f)

# Save banned IPs to file
def save_banned_ips():
    with open(BANNED_IPS_FILE, "w") as f:
        json.dump(banned_ips, f)

# Validate username (max 15 chars, only a-z, A-Z, 0-9, _, -, +, .)
def validate_username(name):
    return len(name) <= 15 and re.match(r'^[a-zA-Z0-9_\-+.]+$', name) and name != "Console"

# Resolve duplicate username by appending a suffix
def resolve_duplicate_username(base_name):
    suffix = 1
    new_name = base_name
    while new_name in players:
        new_name = f"{base_name}[{suffix}]"
        suffix += 1
    return new_name

# Broadcast function to send updates to all clients
def broadcast():
    data = json.dumps({'players': players, 'chat': chat_history}).encode('utf-8')
    with lock:
        for client in clients:
            try:
                client.sendall(data)
            except:
                clients.remove(client)
                client.close()

# Process slash commands
def process_command(command, username, client):
    try:
        if command in ['/help', '/?']:
            help_text = "Commands:\n/help or /?: Show all commands\n/bye, /exit, /leave: Disconnect and restart\n/rename <new_name>: Change your username\n"
            client.sendall(json.dumps({'command_result': help_text}).encode('utf-8'))
            return True

        elif command in ['/bye', '/exit', '/leave']:
            client.sendall(json.dumps({'command_result': "Goodbye!"}).encode('utf-8'))
            # Disconnect the client after sending a goodbye message
            clients.remove(client)
            del players[username]
            client.close()
            return True

        elif command.startswith('/rename'):
            parts = command.split()
            if len(parts) == 2:
                new_name = parts[1]
                if validate_username(new_name):
                    new_name = resolve_duplicate_username(new_name)
                    client.sendall(json.dumps({'command_result': f"Renamed to {new_name}. Reconnect with new name."}).encode('utf-8'))
                    clients.remove(client)
                    del players[username]
                    client.close()
                else:
                    client.sendall(json.dumps({'command_result': "Invalid username. Max 15 chars, use a-z, A-Z, 0-9, _, -, +, ."}).encode('utf-8'))
                return True
            else:
                client.sendall(json.dumps({'command_result': "Usage: /rename <new_name>"}).encode('utf-8'))
                return True

        return False  # Command not processed
    except Exception as e:
        print(f"Error processing command: {e}")
        return False

def handle_client(client):
    try:
        addr = client.getpeername()[0]  # Get client IP address

        if addr in banned_ips:  # Check if the client's IP is banned
            client.sendall(json.dumps({'command_result': "You are banned from this server."}).encode('utf-8'))
            client.close()
            return

        username = client.recv(1024).decode('utf-8')
        if not validate_username(username):
            client.sendall(json.dumps({'command_result': "Invalid username. Max 15 chars, use a-z, A-Z, 0-9, _, -, +, ."}).encode('utf-8'))
            client.close()
            return

        username = resolve_duplicate_username(username)

        with lock:
            chat_history.append(f"Server: {username} has joined the game.")
            if len(chat_history) > 3:
                chat_history.pop(0)
        players[username] = {
            'x': 400, 'y': 300,
            'color': (random.randint(180, 255), random.randint(180, 255), random.randint(180, 255))
        }
        last_pos = (400, 300)

        broadcast()  # Let others know about the new player

        while True:
            try:
                message = json.loads(client.recv(1024).decode('utf-8'))

                # Check if the message contains a command
                if 'command' in message:
                    if process_command(message['command'], username, client):
                        continue  # Command processed, skip further handling

                # Handle chat messages
                elif 'chat_message' in message:
                    trimmed_message = message['chat_message'][:60]
                    with lock:
                        chat_history.append(f"{username}: {trimmed_message}")
                        if len(chat_history) > 3:
                            chat_history.pop(0)

                # Handle player movement input
                if 'input' in message:
                    new_x, new_y = players[username]['x'], players[username]['y']

                    if message['input']['horizontal'] == 'left':
                        new_x -= 5
                    elif message['input']['horizontal'] == 'right':
                        new_x += 5

                    if message['input']['vertical'] == 'up':
                        new_y -= 5
                    elif message['input']['vertical'] == 'down':
                        new_y += 5

                    if ((new_x - last_pos[0]) ** 2 + (new_y - last_pos[1]) ** 2) ** 0.5 <= MAX_DIST:
                        players[username]['x'], players[username]['y'] = new_x, new_y
                        last_pos = (new_x, new_y)

                broadcast()  # Send updated state to all clients
            except (ConnectionResetError, json.JSONDecodeError):
                break  # Client disconnected or sent invalid data

    except Exception as e:
        print(f"Error: {e}")  # Log any errors

    # Clean up after client disconnects
    with lock:
        if username in players:
            del players[username]
            chat_history.append(f"Server: {username} has left the game.")
            if len(chat_history) > 3:
                chat_history.pop(0)
        if client in clients:
            clients.remove(client)

    broadcast()  # Notify others about the player leaving
    client.close()

# Send a message from the Console
def send_console_message(message):
    with lock:
        chat_history.append(f"Console: {message}")
        if len(chat_history) > 3:
            chat_history.pop(0)
    broadcast()

# Kick a player by username
def kick_player(username):
    with lock:
        if username in players:
            for client in clients:
                if players[username]['client'] == client:
                    clients.remove(client)
                    del players[username]
                    client.sendall(json.dumps({'command_result': "You have been kicked by the console."}).encode('utf-8'))
                    client.close()
                    chat_history.append(f"Console: {username} has been kicked.")
                    if len(chat_history) > 3:
                        chat_history.pop(0)
                    broadcast()
                    return True
    return False

# Ban a player by IP
def ban_player(username):
    with lock:
        if username in players:
            for client in clients:
                if players[username]['client'] == client:
                    addr = client.getpeername()[0]
                    banned_ips.append(addr)
                    save_banned_ips()  # Save banned IPs to file
                    clients.remove(client)
                    del players[username]
                    client.sendall(json.dumps({'command_result': "You have been banned by the console."}).encode('utf-8'))
                    client.close()
                    chat_history.append(f"Console: {username} and their IP {addr} have been banned.")
                    if len(chat_history) > 3:
                        chat_history.pop(0)
                    broadcast()
                    return True
    return False

# Accept connections from new clients
def receive_connections():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server started on {HOST}:{PORT}")
    
    while True:
        client, addr = server.accept()
        print(f"Connection established with {addr}")
        if addr[0] in banned_ips:  # Check if IP is banned
            client.sendall(json.dumps({'command_result': "You are banned from this server."}).encode('utf-8'))
            client.close()
            continue
        with lock:
            clients.append(client)
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()

# Console command input
def console_input():
    while True:
        command = input("Console> ")
        if command.startswith("/kick"):
            parts = command.split()
            if len(parts) == 2:
                username = parts[1]
                if not kick_player(username):
                    print(f"Console: No such player '{username}'")
        elif command.startswith("/ban"):
            parts = command.split()
            if len(parts) == 2:
                username = parts[1]
                if not ban_player(username):
                    print(f"Console: No such player '{username}'")
        else:
            send_console_message(command)

if __name__ == "__main__":
    threading.Thread(target=receive_connections, daemon=True).start()
    console_input()  # Start console input thread

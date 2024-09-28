import pygame, sys, socket, threading, json, time, os

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
BLACK, WHITE, RED = (0, 0, 0), (255, 255, 255), (255, 0, 0)
DEFAULT_FONT_NAME = 'Courier'
DEFAULT_FONT_SIZE = 24
FONT = pygame.font.SysFont(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)  # Ensure FONT is defined
FONT_CACHE = {}  # Cache to store loaded fonts
FONT_SPACING = 2  # Default spacing between characters
CHAT_HEIGHT, SERVER_PORT = 150, 55555
MAX_CHAT_MESSAGES = 10  # Increased to show more chat messages
MSG_CHAR_LIMIT = 60     # Limit input message to 60 characters

class Client:
    def __init__(self, username, server_host):
        self.username = username
        self.server_host = server_host
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_host, SERVER_PORT))
        self.sock.sendall(self.username.encode('utf-8'))
        self.running = True
        self.chat_messages, self.players, self.lock = [], {}, threading.Lock()
        self.last_message_sender = None  # Track the last message sender
        self.last_message_timestamp = 0  # Track when the last message was received
        self.full_message_display = False  # To toggle full message display
        self.current_popup = None  # To store current popup message
        self.render_text_elements = []  # List to store renderable text elements

    def listen_for_messages(self):
        while self.running:
            try:
                message = self.sock.recv(4096).decode('utf-8')  # Increased buffer size
                if message:
                    with self.lock:
                        data = json.loads(message)
                        if 'command_result' in data:
                            self.current_popup = data['command_result']  # Set popup message
                            self.popup_start_time = time.time()
                        elif 'render_text' in data:
                            # Handle render_text instructions
                            self.handle_render_text(data['render_text'])
                        else:
                            self.players = data['players']
                            self.chat_messages = data['chat']
            except:
                self.running = False
                self.sock.close()

    def handle_render_text(self, render_text_data):
        """
        Process the render_text data from the server.
        Each item in render_text_data should be a dictionary with properties:
        - text: string to render
        - position: [x, y] coordinates
        - font: (optional) font name
        - size: (optional) font size
        - colors: (optional) list of color tuples per character
        - spacing: (optional) spacing between characters
        - duration: (optional) time in seconds to display the text
        """
        for text_item in render_text_data:
            element = {
                'text': text_item.get('text', ''),
                'position': text_item.get('position', [0, 0]),
                'font_name': text_item.get('font', DEFAULT_FONT_NAME),
                'font_size': text_item.get('size', DEFAULT_FONT_SIZE),
                'colors': text_item.get('colors', []),  # List of color tuples per character
                'spacing': text_item.get('spacing', FONT_SPACING),
                'start_time': time.time(),
                'duration': text_item.get('duration', 10)  # Default duration 10 seconds
            }
            self.render_text_elements.append(element)

    def send_message(self, message):
        try:
            if message.strip():
                # Send as a command if it starts with '/'
                if message.startswith('/'):
                    self.sock.sendall(json.dumps({'command': message}).encode('utf-8'))
                else:
                    self.sock.sendall(json.dumps({'chat_message': message}).encode('utf-8'))
        except:
            self.running = False
            self.sock.close()

    def send_input(self, horizontal, vertical):
        try:
            self.sock.sendall(json.dumps({'input': {'horizontal': horizontal, 'vertical': vertical}}).encode('utf-8'))
        except:
            self.running = False
            self.sock.close()

def wrap_text(text, font, max_width):
    """ Helper function to wrap text for the popup """
    words = text.split(' ')
    wrapped_lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            wrapped_lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        wrapped_lines.append(' '.join(current_line))
    return wrapped_lines

def get_font(font_name, font_size):
    """
    Retrieve a font from the cache or load it if not present.
    """
    key = (font_name, font_size)
    if key not in FONT_CACHE:
        try:
            FONT_CACHE[key] = pygame.font.SysFont(font_name, font_size)
        except:
            print(f"Font '{font_name}' not found. Using default font.")
            FONT_CACHE[key] = pygame.font.SysFont(DEFAULT_FONT_NAME, font_size)
    return FONT_CACHE[key]

def draw_popup(screen, message):
    """ Draw the popup on the screen """
    popup_width, popup_height = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    popup_rect = pygame.Rect(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, popup_width, popup_height)
    max_line_width = popup_width - 40  # Padding for text inside popup
    font = get_font(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)
    wrapped_message = wrap_text(message, font, max_line_width)  # Wrap the text

    # Semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # Semi-transparent black
    screen.blit(overlay, (0, 0))

    pygame.draw.rect(screen, WHITE, popup_rect, 2)

    # Display the wrapped text inside the popup
    y_offset = popup_rect.y + 20
    for line in wrapped_message:
        text_surface = font.render(line, True, WHITE)
        screen.blit(text_surface, (popup_rect.x + 20, y_offset))
        y_offset += text_surface.get_height() + 5

    return popup_rect  # Return the rect to detect clicks

def render_custom_text(screen, client_obj):
    """
    Render all custom text elements received from the server.
    """
    current_time = time.time()
    elements_to_remove = []
    for element in client_obj.render_text_elements:
        # Check if the text element has expired
        if current_time - element['start_time'] > element['duration']:
            elements_to_remove.append(element)
            continue

        text = element['text']
        pos_x, pos_y = element['position']
        font_name = element['font_name']
        font_size = element['font_size']
        spacing = element['spacing']
        colors = element['colors']

        font = get_font(font_name, font_size)

        # Render each character with its respective color
        for i, char in enumerate(text):
            char_color = colors[i] if i < len(colors) else WHITE  # Default to white if not specified
            char_surface = font.render(char, True, char_color)
            screen.blit(char_surface, (pos_x, pos_y))
            pos_x += char_surface.get_width() + spacing

    # Remove expired elements
    for element in elements_to_remove:
        client_obj.render_text_elements.remove(element)

def draw_chat(screen, chat_messages):
    chat_rect = pygame.Rect(0, SCREEN_HEIGHT - CHAT_HEIGHT, SCREEN_WIDTH, CHAT_HEIGHT)
    pygame.draw.rect(screen, (30, 30, 30), chat_rect)  # Removed alpha for simplicity
    y_offset = SCREEN_HEIGHT - CHAT_HEIGHT + 10
    chat_font = get_font(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)  # Use get_font for consistency
    for message in chat_messages[-MAX_CHAT_MESSAGES:]:
        chat_surface = chat_font.render(message, True, WHITE)
        screen.blit(chat_surface, (10, y_offset))
        y_offset += 30

def draw_speech_bubble(screen, player_x, player_y, message, hover=False, clicked=False):
    if clicked:
        message_display = message[:150]  # Display up to 150 characters when clicked
    elif hover:
        message_display = message[:60]  # Show up to 60 characters when hovering
    else:
        message_display = message[:15] + '...'  # Default trimmed message

    speech_font = get_font(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)  # Use get_font for consistency
    speech_surface = speech_font.render(message_display, True, WHITE)
    bubble_rect = speech_surface.get_rect(midbottom=(player_x, player_y - 20))
    pygame.draw.rect(screen, BLACK, bubble_rect.inflate(10, 10))  # Bubble background
    screen.blit(speech_surface, bubble_rect.topleft)

def draw_players(screen, players, client_obj):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    for username, player_info in players.items():
        # Retrieve the font for rendering player characters and usernames
        player_font = get_font(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)
        player_surface = player_font.render('@', True, player_info['color'])
        username_surface = player_font.render(username, True, player_info['color'])

        # Draw the player's character '@'
        screen.blit(player_surface, (player_info['x'], player_info['y']))

        # Draw the username above the character in the same color
        screen.blit(username_surface, (player_info['x'], player_info['y'] - 20))

        # If this player is the last to send a message, show a speech bubble
        if client_obj.last_message_sender and client_obj.last_message_sender[0] == username:
            time_elapsed = time.time() - client_obj.last_message_timestamp
            if time_elapsed < 5 or client_obj.full_message_display:  # Show for 5 seconds or when clicked
                hover = False
                clicked = client_obj.full_message_display

                if not client_obj.full_message_display:  # Check if the mouse is hovering
                    if player_info['x'] <= mouse_x <= player_info['x'] + 30 and player_info['y'] - 40 <= mouse_y <= player_info['y']:
                        hover = True

                draw_speech_bubble(screen, player_info['x'], player_info['y'], client_obj.last_message_sender[1], hover, clicked)

def get_user_input(screen, clock, prompt_text="", default_text=''):
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20, 200, 40)
    color_inactive, color_active, color, active = WHITE, (100, 100, 255), WHITE, True
    user_text = default_text
    prompt_font = get_font(DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE)  # Use get_font for prompt
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return user_text
                elif event.key == pygame.K_BACKSPACE:
                    user_text = user_text[:-1]
                else:
                    if len(user_text) < MSG_CHAR_LIMIT:
                        user_text += event.unicode
        screen.fill(BLACK)
        txt_surface = FONT.render(user_text, True, color)  # You can also use get_font here if needed
        width = max(200, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)
        prompt_surface = prompt_font.render(prompt_text, True, WHITE)
        screen.blit(prompt_surface, (SCREEN_WIDTH // 2 - prompt_surface.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
        pygame.display.flip()
        clock.tick(30)

def restart_client():
    # Restart the client script
    os.execl(sys.executable, sys.executable, *sys.argv)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ASCII Game with Chat")
    clock = pygame.time.Clock()

    SERVER_HOST = get_user_input(screen, clock, "Enter the server IP:", 'localhost')
    username = get_user_input(screen, clock, "Enter your name:")

    client_obj = Client(username, SERVER_HOST)
    threading.Thread(target=client_obj.listen_for_messages, daemon=True).start()

    chat_input, typing_message, running = '', False, True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif client_obj.current_popup:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        client_obj.current_popup = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    # Check if click is inside popup area
                    popup_rect = pygame.Rect(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                    if popup_rect.collidepoint(mouse_pos):
                        client_obj.current_popup = None
            elif event.type == pygame.KEYDOWN:
                if typing_message:
                    if event.key == pygame.K_RETURN:
                        if chat_input.strip() in ['/bye', '/exit', '/leave']:
                            client_obj.send_message(chat_input)
                            running = False
                        else:
                            client_obj.send_message(chat_input)
                        chat_input, typing_message = '', False  # Exit typing mode after sending message
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    else:
                        if len(chat_input) < MSG_CHAR_LIMIT:
                            chat_input += event.unicode
                elif event.key == pygame.K_SPACE:
                    typing_message = True

        # Handle closing popup after a certain time
        if client_obj.current_popup:
            # Automatically close popup after 5 seconds
            if time.time() - getattr(client_obj, 'popup_start_time', 0) > 5:
                client_obj.current_popup = None

        keys = pygame.key.get_pressed()
        if not typing_message and not client_obj.current_popup:  # Allow movement if not in typing mode or popup
            horizontal, vertical = '', ''
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                horizontal = 'left'
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                horizontal = 'right'

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                vertical = 'up'
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                vertical = 'down'

            if horizontal or vertical:  # Only send input if there's actual movement
                client_obj.send_input(horizontal, vertical)

        screen.fill(BLACK)
        draw_players(screen, client_obj.players, client_obj)  # Draw all players
        draw_chat(screen, client_obj.chat_messages)  # Draw chat messages
        render_custom_text(screen, client_obj)  # Draw custom render_text elements

        if client_obj.current_popup:
            popup_rect = draw_popup(screen, client_obj.current_popup)
        elif typing_message:
            chat_input_surface = FONT.render(">" + chat_input, True, RED)
            screen.blit(chat_input_surface, (10, SCREEN_HEIGHT - 30))

        pygame.display.flip()

    client_obj.sock.close()
    pygame.quit()

    restart_client()

if __name__ == "__main__":
    main()

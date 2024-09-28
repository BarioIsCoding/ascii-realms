# ASCII Realms

Welcome to **ASCII Realms**, a Python-based multiplayer game that leverages Pygame for graphics and socket programming for network communication. Dive into a dynamic world where players interact in real-time, engage in lively chats, and experience customizable text rendering controlled by the server. Immerse yourself in the retro charm of ASCII art while enjoying modern multiplayer features.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Server](#running-the-server)
- [Running the Client](#running-the-client)
- [Game Controls](#game-controls)
- [Customizing Text Rendering](#customizing-text-rendering)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multiplayer Support**: Connect multiple clients to a central server for seamless real-time interaction.
- **Chat System**: Engage in text-based conversations with friends and other players, complete with character limits and command support.
- **Customizable Text Rendering**: The server can display text with various fonts, sizes, colors, spacing, and positions anywhere within the game window.
- **Dynamic Popups**: Receive and interact with pop-up messages that enhance gameplay and provide important information.
- **Player Interaction**: Navigate your character using intuitive keyboard controls and interact with other players in the shared environment.
- **ASCII Art Style**: Embrace the nostalgic feel of ASCII art combined with modern multiplayer dynamics.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.7 or higher
- **Pygame**: Installed for the client
- **Socket Programming Knowledge**: Basic understanding for running the server

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/BarioIsCoding/ascii-realms.git
   cd ascii-realms
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Required Python Packages**

   ```bash
   pip install pygame
   ```

## Running the Server

The server manages player connections, handles chat messages, and sends customizable text rendering commands to all connected clients.

1. **Navigate to the Project Directory**

   Ensure you're in the project root directory where `server.py` is located.

2. **Run the Server Script**

   ```bash
   python server.py
   ```

   **Server Configuration Options:**

   - **Port**: The server listens on port `55555` by default. You can change this by modifying the `SERVER_PORT` variable in `server.py`.
   - **Fonts**: Ensure that the fonts you intend to use for custom text rendering are installed on the server machine.

3. **Server Commands**

   The server can accept commands to broadcast messages or render custom text. Example commands include:

   - **Broadcast Chat Message**

     ```bash
     /chat Hello, players!
     ```

   - **Render Custom Text**

     ```bash
     /render_text {"text": "Welcome!", "position": [100, 150], "font": "Arial", "size": 24, "colors": [[255, 0, 0]], "spacing": 2, "duration": 10}
     ```

   **Note:** The exact command format may vary based on the server implementation. Refer to `server.py` for detailed command handling.

## Running the Client

Each player runs a client instance to connect to the server and participate in the game.

1. **Navigate to the Project Directory**

   Ensure you're in the project root directory where `client.py` (or `main.py`) is located.

2. **Run the Client Script**

   ```bash
   python client.py
   ```

3. **Client Setup**

   - **Server IP**: When prompted, enter the IP address of the server. If running locally, you can use `localhost`.
   - **Username**: Enter a unique name to represent you in the game.

## Game Controls

Use the following keyboard controls to navigate and interact within the game:

- **Movement:**
  - **Left Arrow** or **A**: Move left
  - **Right Arrow** or **D**: Move right
  - **Up Arrow** or **W**: Move up
  - **Down Arrow** or **S**: Move down

- **Chat:**
  - **Spacebar**: Activate chat typing mode
  - **Enter**: Send chat message
  - **Backspace**: Delete the last character in your chat input

- **Popups:**
  - **Escape (ESC)**: Close any active popup messages

## Customizing Text Rendering

The server can send commands to display text with various properties. Here's how you can utilize this feature:

1. **Sending a Render Text Command**

   The server can send a JSON-formatted command to instruct clients to render text with specific attributes. Example command structure:

   ```json
   {
       "render_text": [
           {
               "text": "Hello, World!",
               "position": [100, 150],
               "font": "Arial",
               "size": 24,
               "colors": [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
               "spacing": 2,
               "duration": 15
           },
           {
               "text": "Welcome to ASCII Realms!",
               "position": [300, 400],
               "font": "Courier",
               "size": 30,
               "colors": [],
               "spacing": 1,
               "duration": 20
           }
       ]
   }
   ```

   **Field Descriptions:**

   - **`text`**: The string to render.
   - **`position`**: `[x, y]` coordinates on the screen.
   - **`font`**: (Optional) Font name. Defaults to `Courier` if not specified or invalid.
   - **`size`**: (Optional) Font size. Defaults to `24` if not specified.
   - **`colors`**: (Optional) List of RGB color tuples for each character. If not provided or shorter than the text length, missing characters default to white.
   - **`spacing`**: (Optional) Space in pixels between characters. Defaults to `2`.
   - **`duration`**: (Optional) Time in seconds the text should remain on the screen. Defaults to `10` seconds.

2. **Server Example: Rendering Custom Text**

   Here's how the server can send a custom text rendering command:

   ```python
   import socket
   import json

   SERVER_HOST = 'localhost'
   SERVER_PORT = 55555

   with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
       s.connect((SERVER_HOST, SERVER_PORT))
       render_command = {
           "render_text": [
               {
                   "text": "Game Started!",
                   "position": [200, 100],
                   "font": "Verdana",
                   "size": 28,
                   "colors": [[0, 255, 0]] * 12,  # Green color for each character
                   "spacing": 1,
                   "duration": 10
               }
           ]
       }
       s.sendall(json.dumps(render_command).encode('utf-8'))
   ```

## Troubleshooting

If you encounter any issues while setting up or running the game, consider the following solutions:

- **Font Recognition Issues:**
  - Ensure that the fonts specified in `render_text` commands are installed on both the server and client machines.
  - Check for typos in font names.
  - Use default fonts like `Courier` or `Arial` to minimize issues.

- **Connection Problems:**
  - Verify that the server is running and listening on the correct IP and port.
  - Ensure that firewall settings allow traffic through the specified port (`55555` by default).
  - Use the correct server IP when prompted by the client.

- **Pygame Errors:**
  - Ensure Pygame is installed correctly by running `pip install pygame`.
  - Check for any missing dependencies or incompatible Python versions.

- **Script Crashes:**
  - Run scripts in a terminal to view error messages.
  - Ensure that no other application is using the server port.
  - Verify that all required Python packages are installed.

- **Popups Not Displaying Correctly:**
  - Ensure that the server sends `render_text` commands in the correct JSON format.
  - Check that the `colors` array matches the length of the `text` string or provides defaults.

## Contributing

Contributions are welcome! If you'd like to improve this project, please follow these steps:

1. **Fork the Repository**

2. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Make Your Changes**

4. **Commit Your Changes**

   ```bash
   git commit -m "Add your message here"
   ```

5. **Push to the Branch**

   ```bash
   git push origin feature/YourFeature
   ```

6. **Open a Pull Request**

## License

This project is licensed under the [MIT License](LICENSE).

---

**Enjoy exploring the realms of ASCII Realms! If you have any questions or need further assistance, feel free to open an issue or contact the maintainer.**

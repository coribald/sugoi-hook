"""
Renji WebSocket Plugin for Sugoi Hook
======================================

This plugin creates a WebSocket server that Renji (https://renji-xd.github.io/texthooker-ui/)
connects to for receiving extracted Japanese text for learning and display.

Renji is a web-based texthooker UI that displays Japanese text with features like:
- Text display with customizable fonts
- Character counting and milestones
- Text history and export
- Replacements and presets for text cleaning
"""

import threading
import time
from plugins import TextractorPlugin

# Try to import required libraries
WEBSOCKET_AVAILABLE = False
try:
    from websocket_server import WebsocketServer
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False


class RenjiWebSocketPlugin(TextractorPlugin):
    name = "Renji WebSocket"
    description = "WebSocket server that sends extracted text to Renji for Japanese learning"
    version = "1.1"
    author = "Sugoi Toolkit"

    def __init__(self):
        super().__init__()
        self.server_port = 6677
        self.server_host = "0.0.0.0"  # Listen on all interfaces
        self.ws_server = None
        self.server_thread = None
        self.server_running = False
        self.connected_clients = []
        self.send_lock = threading.Lock()

    def on_enable(self):
        """Called when plugin is enabled - start WebSocket server"""
        if not WEBSOCKET_AVAILABLE:
            print("[Renji WebSocket] Error: websocket-server library not found!")
            print("[Renji WebSocket] Please install it with: pip install websocket-server")
            return
        
        self.start_server()

    def on_disable(self):
        """Called when plugin is disabled - stop WebSocket server"""
        self.stop_server()

    def reset(self):
        """Reset plugin state"""
        super().reset()
        # Don't stop server on reset, just clear state

    def start_server(self):
        """Start the WebSocket server"""
        if not WEBSOCKET_AVAILABLE:
            return

        if self.server_running:
            return

        try:
            # Create WebSocket server
            self.ws_server = WebsocketServer(
                host=self.server_host,
                port=self.server_port
            )

            # Set up callbacks
            self.ws_server.set_fn_new_client(self._on_client_connect)
            self.ws_server.set_fn_client_left(self._on_client_disconnect)
            self.ws_server.set_fn_message_received(self._on_message_received)

            # Start server in a separate thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            self.server_running = True
            print(f"[Renji WebSocket] ✓ Server started on {self.server_host}:{self.server_port}")
            print(f"[Renji WebSocket] Waiting for Renji to connect...")

        except Exception as e:
            print(f"[Renji WebSocket] Failed to start server: {e}")
            self.server_running = False

    def _run_server(self):
        """Run WebSocket server (called in separate thread)"""
        try:
            self.ws_server.run_forever()
        except Exception as e:
            print(f"[Renji WebSocket] Server error: {e}")
            self.server_running = False

    def _on_client_connect(self, client, server):
        """Called when a client (Renji) connects"""
        self.connected_clients.append(client)
        print(f"[Renji WebSocket] ✓ Renji connected! (Client ID: {client['id']})")

    def _on_client_disconnect(self, client, server):
        """Called when a client (Renji) disconnects"""
        if client in self.connected_clients:
            self.connected_clients.remove(client)
        print(f"[Renji WebSocket] Renji disconnected (Client ID: {client['id']})")

    def _on_message_received(self, client, server, message):
        """Called when receiving a message from client"""
        # Renji might send commands or acknowledgments
        pass

    def stop_server(self):
        """Stop the WebSocket server"""
        self.server_running = False
        
        if self.ws_server:
            try:
                self.ws_server.shutdown()
            except:
                pass
            self.ws_server = None
        
        self.connected_clients = []
        print("[Renji WebSocket] Server stopped")

    def send_to_renji(self, text: str):
        """Send text to all connected Renji clients"""
        if not self.server_running or not self.connected_clients:
            return False

        try:
            with self.send_lock:
                # Send to all connected clients
                for client in self.connected_clients[:]:  # Use copy to avoid modification during iteration
                    try:
                        self.ws_server.send_message(client, text)
                    except Exception as e:
                        # Remove disconnected client
                        if client in self.connected_clients:
                            self.connected_clients.remove(client)
                return True
        except Exception as e:
            print(f"[Renji WebSocket] Send error: {e}")
            return False

    def process_text(self, text: str) -> str:
        """Process text and send to Renji"""
        if not text or not text.strip():
            return text

        # Check if websocket library is available
        if not WEBSOCKET_AVAILABLE:
            # Don't filter out text, just pass through
            return text

        stripped_text = text.strip()

        # Filter out system messages and UI elements
        # Don't send hook previews (when no hook is selected)
        if stripped_text.startswith('[Hook ') or stripped_text.startswith('[Hook #'):
            return text

        # Don't send system messages
        system_keywords = (
            'Selected Hook', 'Attached to', 'Detached', 'Waiting for',
            'Function:', 'Manual hook', 'Process Name', 'PID:',
            'Interact with', 'Hook at', 'Console', 'Auto-selected',
            'Auto-attached', 'Game ready', 'Found saved profile'
        )

        if any(keyword in stripped_text for keyword in system_keywords):
            return text

        # Check for lines starting with emoji/symbols (system messages)
        if stripped_text and stripped_text[0] in '✓●○🎮🎯🔌📝⏳🔗⏹️🗑️💾🔄📂🔽🚀⚠️🔍':
            return text

        # Check for console messages
        if stripped_text.startswith('[Console]'):
            return text

        # Don't send separator lines
        if len(stripped_text) > 3:
            separator_chars = '─═━-_'
            separator_count = sum(1 for c in stripped_text if c in separator_chars)
            if separator_count / len(stripped_text) > 0.8:
                return text

        # Send the actual game text to Renji
        if self.enabled and self.server_running:
            if self.connected_clients:
                # Send clean text (remove trailing newlines for cleaner display in Renji)
                clean_text = text.rstrip()
                self.send_to_renji(clean_text)

        # Always return the text to continue the plugin chain
        return text

    def process_clipboard_text(self, text: str) -> str:
        """Keep clipboard processing free of Renji side effects."""
        return text

    def get_settings(self) -> dict:
        """Return configurable settings for the plugin"""
        if not WEBSOCKET_AVAILABLE:
            return {
                'error': (
                    'websocket-server not installed',
                    'str',
                    'Error: Please install websocket-server library (pip install websocket-server)'
                )
            }

        return {
            'server_port': (
                self.server_port,
                'int',
                'Server Port (default: 6677)'
            )
        }

    def set_setting(self, name: str, value) -> bool:
        """Update a plugin setting"""
        if name == 'server_port':
            if isinstance(value, int) and 1024 <= value <= 65535:
                old_port = self.server_port
                self.server_port = value
                # Restart server with new port if running
                if self.server_running and old_port != value:
                    self.stop_server()
                    time.sleep(0.5)
                    self.start_server()
                return True
            return False

        return False


# Create plugin instance
plugin = RenjiWebSocketPlugin()

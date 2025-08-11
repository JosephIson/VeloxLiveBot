import asyncio
import logging
import websockets
from .config import config

class TwitchChatClient:
    """
    Handles connection and communication with Twitch's IRC chat.
    """
    def __init__(self, message_queue=None):
        """
        Initializes the client.
        :param message_queue: An asyncio.Queue to put received messages into.
        """
        self.twitch_config = config.get_section('twitch')
        self.is_connected = False
        self.websocket = None
        self._listen_task = None
        self.message_queue = message_queue

    async def connect(self):
        """
        Connects to Twitch IRC server and authenticates.
        """
        if self.is_connected:
            logging.warning("Already connected to Twitch chat.")
            return

        if not all(self.twitch_config.get(k) for k in ['username', 'oauthtoken', 'channel']):
            logging.error("Twitch configuration is missing or incomplete. Please check your config.ini file.")
            return False

        uri = "wss://irc-ws.chat.twitch.tv:443"
        try:
            self.websocket = await websockets.connect(uri)
            self.is_connected = True
            logging.info("Successfully connected to Twitch IRC server.")

            # Authenticate
            oauth = self.twitch_config['oauthtoken']
            if not oauth.startswith('oauth:'):
                oauth = f"oauth:{oauth}"

            await self.websocket.send(f"PASS {oauth}")
            await self.websocket.send(f"NICK {self.twitch_config['username']}")

            # Join the channel
            await self.websocket.send(f"JOIN {self.twitch_config['channel']}")
            logging.info(f"Attempting to join Twitch channel: {self.twitch_config['channel']}")

            # Request capabilities for more detailed messages (e.g., user info, badges)
            await self.websocket.send("CAP REQ :twitch.tv/tags twitch.tv/commands")

            return True

        except Exception as e:
            logging.error(f"Failed to connect to Twitch: {e}")
            self.is_connected = False
            self.websocket = None
            return False

    async def disconnect(self):
        """
        Disconnects from the server and cancels the listening task.
        """
        if self._listen_task:
            self._listen_task.cancel()
        if self.is_connected and self.websocket:
            await self.websocket.close()
            self.is_connected = False
            self.websocket = None
            logging.info("Disconnected from Twitch chat.")

    async def _listen(self):
        """
        The core loop that listens for messages from the server.
        """
        if not self.is_connected or not self.websocket:
            logging.error("Cannot listen, not connected to Twitch chat.")
            return

        try:
            while self.is_connected:
                message = await self.websocket.recv()
                logging.debug(f"< {message.strip()}") # Log raw messages at debug level

                if message.startswith("PING"):
                    await self.websocket.send("PONG :tmi.twitch.tv")
                    logging.info("Responded to PING with PONG")
                elif "PRIVMSG" in message:
                    if self.message_queue:
                        await self.message_queue.put(message)
                # You can add more message handling here (e.g., JOIN, PART, NOTICE)
        except websockets.exceptions.ConnectionClosed as e:
            logging.warning(f"Twitch connection closed: {e}")
            self.is_connected = False
        except asyncio.CancelledError:
            logging.info("Listen task was cancelled.")
        except Exception as e:
            logging.error(f"An error occurred while listening to Twitch chat: {e}")
            self.is_connected = False

    def start_listening(self):
        """
        Starts the listening task in the background.
        """
        if self.is_connected and not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen())
            logging.info("Started listening for chat messages.")

# This part is for standalone testing and won't be run from the main app.
if __name__ == "__main__":
    print("This is a module for VeloxLiveBot and is not meant to be run directly.")
    print("To test this module, you would typically import TwitchChatClient and run it within an asyncio event loop.")

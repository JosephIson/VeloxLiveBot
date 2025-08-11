import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import queue
import re
import logging

from .config import config
from .chat_client import TwitchChatClient

def parse_twitch_message(raw_message):
    """
    Parses a raw Twitch IRC message and returns the username and message content.
    Example: @... :username!user@user.tmi.twitch.tv PRIVMSG #channel :Hello
    """
    match = re.search(r':(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.*)', raw_message)
    if match:
        username, message = match.groups()
        return username, message.strip()
    return None, None

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("VeloxLiveBot Dashboard")
        self.master.geometry("1200x800")
        self.pack(fill=tk.BOTH, expand=True)

        self.message_queue = queue.Queue()
        self.async_queue = asyncio.Queue()

        self.create_widgets()

        # Start the asyncio event loop in a separate thread
        self.asyncio_thread = threading.Thread(target=self.start_asyncio_loop, daemon=True)
        self.asyncio_thread.start()

        # Start polling the queue for messages from the asyncio thread
        self.master.after(100, self.process_message_queue)

    def start_asyncio_loop(self):
        """
        Runs the asyncio event loop in a separate thread.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.chat_client = TwitchChatClient(message_queue=self.async_queue)
        loop.run_until_complete(self.run_chat_client())
        loop.close()

    async def run_chat_client(self):
        """
        Connects the chat client and bridges the asyncio queue to the thread-safe queue.
        """
        if await self.chat_client.connect():
            self.chat_client.start_listening()
            # Bridge the queues
            while True:
                message = await self.async_queue.get()
                self.message_queue.put(message)
                self.async_queue.task_done()

    def process_message_queue(self):
        """
        Checks the queue for new messages and displays them in the UI.
        This runs in the main Tkinter thread.
        """
        try:
            while not self.message_queue.empty():
                raw_message = self.message_queue.get_nowait()
                username, message = parse_twitch_message(raw_message)
                if username and message:
                    formatted_message = f"{username}: {message}\n"
                    self.display_message(formatted_message)
        except queue.Empty:
            pass
        finally:
            # Reschedule itself
            self.master.after(100, self.process_message_queue)

    def display_message(self, message):
        """
        Displays a message in the chat text widget.
        """
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, message)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END) # Auto-scroll

    def create_widgets(self):
        # ... (rest of the create_widgets function is the same)
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_paned_window, width=400)
        main_paned_window.add(left_frame, weight=1)
        right_frame = ttk.Frame(main_paned_window, width=800)
        main_paned_window.add(right_frame, weight=2)

        left_notebook = ttk.Notebook(left_frame)
        left_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        chat_feed_frame = ttk.Frame(left_notebook)
        logs_frame = ttk.Frame(left_notebook)
        left_notebook.add(chat_feed_frame, text="Live Chat")
        left_notebook.add(logs_frame, text="Logs")

        chat_label = ttk.Label(chat_feed_frame, text="Live Chat Feed")
        chat_label.pack(pady=5)
        self.chat_text = tk.Text(chat_feed_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        logs_label = ttk.Label(logs_frame, text="Application Logs")
        logs_label.pack(pady=5)
        self.logs_text = tk.Text(logs_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        right_notebook = ttk.Notebook(right_frame)
        right_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        weather_frame = ttk.Frame(right_notebook)
        schedule_frame = ttk.Frame(right_notebook)
        settings_frame = ttk.Frame(right_notebook)
        right_notebook.add(weather_frame, text="Weather Radar")
        right_notebook.add(schedule_frame, text="Scheduler")
        right_notebook.add(settings_frame, text="Settings")

        status_bar = ttk.Frame(self, height=25)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        self.api_status_label = ttk.Label(status_bar, text="API Status: Disconnected")
        self.api_status_label.pack(side=tk.LEFT, padx=10)

def main():
    """Main function to run the VeloxLiveBot application."""
    # A config.ini file is required for the application to run
    if config.config is None:
        # In a real app, show a popup. For now, log to console.
        logging.error("Could not find config.ini. The application cannot start.")
        return

    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()

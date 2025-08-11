import tkinter as tk

def main():
    """Main function to run the VeloxLiveBot application."""
    root = tk.Tk()
    root.title("VeloxLiveBot")
    root.geometry("800x600")

    label = tk.Label(root, text="Welcome to VeloxLiveBot!")
    label.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()

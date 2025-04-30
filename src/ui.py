from typing import Callable, Dict

import customtkinter
from customtkinter import CTkImage
from PIL import Image

customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("dark-blue")


class UI(customtkinter.CTk):
    def __init__(self, callbacks_commands: Dict[str, Callable]):
        super().__init__()

        self.title("Drone Controller")
        self.geometry("600x400")

        # Set grid weights for responsiveness
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Body
        self.grid_rowconfigure(2, weight=0)  # Footer
        self.grid_columnconfigure(0, weight=1)

        # Store callbacks
        self.takeoff_callback_leader = callbacks_commands["takeoff_leader"]
        self.land_callback_leader = callbacks_commands["land_leader"]
        self.follow_me_callback = callbacks_commands["follow_me"]
        self.takeoff_callback_follower = callbacks_commands["takeoff_follower"]
        self.land_callback_follower = callbacks_commands["land_follower"]

        # --- Header ---
        self.header = customtkinter.CTkFrame(master=self)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.header.grid_columnconfigure(1, weight=1)

        # App Icon Switch
        self.black_logo = Image.open("doc/drone.png").resize((50, 50))
        self.white_logo = Image.open("doc/drone_2.png").resize((50, 50))
        self.drone_image = CTkImage(light_image=self.white_logo, dark_image=self.black_logo)
        self.switch_button = customtkinter.CTkButton(
            master=self.header,
            image=self.drone_image,
            command=self.switch_appearance,
            width=50,
            height=50,
            text="",
        )
        self.switch_button.grid(row=0, column=0, padx=10)

        self.header_title = customtkinter.CTkLabel(
            master=self.header,
            text="Drone Controller",
            font=("Roboto Medium", 20),
            anchor="center",
        )
        self.header_title.grid(row=0, column=1, padx=10)

        # --- Body ---
        self.body = customtkinter.CTkFrame(master=self)
        self.body.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)

        self.follow_button = customtkinter.CTkButton(
            master=self.body,
            text="Follow Me",
            command=self.follow_me_callback,
            height=50,
        )
        self.follow_button.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        # --- Footer ---
        self.footer = customtkinter.CTkFrame(master=self)
        self.footer.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.footer.grid_columnconfigure((0, 1), weight=1)

        self.takeoff_leader_button = customtkinter.CTkButton(
            master=self.footer,
            text="Takeoff Leader",
            command=self.takeoff_callback_leader,
        )
        self.takeoff_leader_button.grid(row=0, column=0, padx=10, pady=5)

        self.land_leader_button = customtkinter.CTkButton(
            master=self.footer,
            text="Land Leader",
            command=self.land_callback_leader,
        )
        self.land_leader_button.grid(row=1, column=0, padx=10, pady=5)

        self.takeoff_follower_button = customtkinter.CTkButton(
            master=self.footer,
            text="Takeoff Follower",
            command=self.takeoff_callback_follower,
        )
        self.takeoff_follower_button.grid(row=0, column=1, padx=10, pady=5)

        self.land_follower_button = customtkinter.CTkButton(
            master=self.footer,
            text="Land Follower",
            command=self.land_callback_follower,
        )
        self.land_follower_button.grid(row=1, column=1, padx=10, pady=5)

    def switch_appearance(self):
        if customtkinter.get_appearance_mode() == "dark":
            customtkinter.set_appearance_mode("light")
        else:
            customtkinter.set_appearance_mode("dark")


if __name__ == "__main__":
    callbacks_commands = {
        "takeoff_leader": lambda: print("takeoff leader"),
        "land_leader": lambda: print("land leader"),
        "follow_me": lambda: print("follow me"),
        "takeoff_follower": lambda: print("takeoff follower"),
        "land_follower": lambda: print("land follower"),
    }
    ui = UI(callbacks_commands)
    ui.mainloop()

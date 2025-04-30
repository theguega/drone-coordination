import tkinter

import customtkinter
from customtkinter import CTkImage

customtkinter.set_appearance_mode("dark")


class UI(customtkinter.CTk):
    def __init__(
        self,
        drone_type_options,
        takeoff_callback=None,
        land_callback=None,
        follow_me_callback=None,
    ):
        super().__init__()

        self.title("Drone Controller")
        self.geometry("600x400")

        self.takeoff_callback = takeoff_callback
        self.land_callback = land_callback
        self.follow_me_callback = follow_me_callback

        self.drone_image = CTkImage(file="doc/drone-svgrepo-com.svg", size=(100, 100))
        self.image_label = customtkinter.CTkLabel(self, image=self.drone_image, text="")
        self.image_label.pack(pady=10)

        self.leader_frame = customtkinter.CTkFrame(self, fg_color="#333333")
        self.leader_frame.pack(side="left", padx=10, pady=10)

        self.shared_frame = customtkinter.CTkFrame(self, fg_color="#333333")
        self.shared_frame.pack(side="left", padx=10, pady=10)

        self.follower_frame = customtkinter.CTkFrame(self, fg_color="#333333")
        self.follower_frame.pack(side="left", padx=10, pady=10)

        # Shared Frame
        self.follow_me_var = tkinter.BooleanVar(value=False)
        self.follow_me_checkbox = customtkinter.CTkCheckBox(
            self.shared_frame,
            text="Follow Me",
            variable=self.follow_me_var,
            fg_color="#333333",
        )
        self.follow_me_checkbox = customtkinter.CTkCheckBox(
            self.shared_frame,
            text="Follow Me",
            variable=self.follow_me_var,
            fg_color="#333333",
            command=self.toggle_follow_me,
        )
        self.follow_me_checkbox.pack(pady=10)

        self.button1 = customtkinter.CTkButton(
            self.shared_frame, text="Button 1", fg_color="#333333"
        )
        self.button1.pack(pady=5)

    def toggle_follow_me(self):
        if self.follow_me_callback:
            self.follow_me_callback(self.follow_me_var.get())

        self.button2 = customtkinter.CTkButton(
            self.shared_frame, text="Button 2", fg_color="#333333"
        )
        self.button2.pack(pady=5)

        self.theme_button = customtkinter.CTkButton(
            self.shared_frame,
            text="Toggle Theme",
            command=self.toggle_theme,
            fg_color="#333333",
        )
        self.theme_button.pack(pady=5)

    def get_ip_address(self):
        return self.ip_entry.get()

    def get_drone_type(self):
        return self.drone_type_combobox.get()

    def is_follow_me_enabled(self):
        return self.follow_me_var.get()

    def toggle_theme(self):
        if customtkinter.get_appearance_mode() == "Dark":
            customtkinter.set_appearance_mode("light")
        else:
            customtkinter.set_appearance_mode("dark")

        # Follower Frame
        self.ip_label = customtkinter.CTkLabel(
            self.follower_frame, text="Follower Drone IP:", fg_color="#333333"
        )
        self.ip_label.pack()
        self.ip_entry = customtkinter.CTkEntry(self.follower_frame, fg_color="#333333")
        self.ip_entry.pack()

        self.drone_type_label = customtkinter.CTkLabel(
            self.follower_frame, text="Follower Drone Type:", fg_color="#333333"
        )
        self.drone_type_label.pack()
        self.drone_type_combobox = customtkinter.CTkComboBox(
            self.follower_frame, values=drone_type_options, fg_color="#333333"
        )
        self.drone_type_combobox.pack()

        self.takeoff_button = customtkinter.CTkButton(
            self.follower_frame,
            text="Takeoff",
            fg_color="#333333",
            command=self.takeoff,
        )
        self.takeoff_button.pack(pady=5)

        self.land_button = customtkinter.CTkButton(
            self.follower_frame, text="Land", fg_color="#333333", command=self.land
        )
        self.land_button.pack(pady=5)


if __name__ == "__main__":
    app = UI(["Bebop", "Mavsdk", "Olympe"])
    app.mainloop()

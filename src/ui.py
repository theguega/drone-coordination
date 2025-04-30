import tkinter

import customtkinter


class UI(customtkinter.CTk):
    def __init__(self, drone_type_options):
        super().__init__()

        self.title("Drone Controller")
        self.geometry("400x300")

        self.follow_me_var = tkinter.BooleanVar(value=False)
        self.follow_me_checkbox = customtkinter.CTkCheckBox(
            self, text="Follow Me", variable=self.follow_me_var
        )
        self.follow_me_checkbox.pack(pady=10)

        self.button1 = customtkinter.CTkButton(self, text="Button 1")
        self.button1.pack(pady=5)

        self.button2 = customtkinter.CTkButton(self, text="Button 2")
        self.button2.pack(pady=5)

        self.ip_label = customtkinter.CTkLabel(self, text="Follower Drone IP:")
        self.ip_label.pack()
        self.ip_entry = customtkinter.CTkEntry(self)
        self.ip_entry.pack()

        self.drone_type_label = customtkinter.CTkLabel(
            self, text="Follower Drone Type:"
        )
        self.drone_type_label.pack()
        self.drone_type_combobox = customtkinter.CTkComboBox(
            self, values=drone_type_options
        )
        self.drone_type_combobox.pack()

    def get_ip_address(self):
        return self.ip_entry.get()

    def get_drone_type(self):
        return self.drone_type_combobox.get()

    def is_follow_me_enabled(self):
        return self.follow_me_var.get()


if __name__ == "__main__":
    app = UI(["Bebop", "Mavsdk", "Olympe"])
    app.mainloop()

import customtkinter

app = customtkinter.CTk()
app.geometry("300x200")

frame = customtkinter.CTkFrame(master=app)
frame.grid(row=0, column=0, padx=10, pady=10)

app.mainloop()

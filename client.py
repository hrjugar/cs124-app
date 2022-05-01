import os
import re
import socket
from constants import *
from otp import *
from tkinter import *
from smtplib import *
from ctypes import windll
from email.message import EmailMessage
from tkinter import font
from tkinter import messagebox


def send_email_code(email, code):
    try:
        sock = socket.create_connection(('www.google.com', 80))
        if sock is not None:
            sock.close()
    except OSError:
        return ErrorMessage.NO_CONNECTION
    
    message = EmailMessage()
    message["From"] = SERVER_ACCOUNT_EMAIL
    message["To"] = email
    message["Subject"] = "OTP Code"
    message.set_content(
        f"""Your six-digit code is {code}
        Note: It will only be valid for {EXPIRATION_TIME} seconds.
        """
    )
    
    try:
        with SMTP_SSL("smtp.gmail.com") as server:
            server.login(SERVER_ACCOUNT_EMAIL, SERVER_ACCOUNT_PASSWORD)
            server.send_message(message)
    except SMTPRecipientsRefused:
        return ErrorMessage.INVALID_EMAIL
    
    return ErrorMessage.NO_ERROR


class MainFrame(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.current_page = None

        self.secret = None
        self.email = None

        self.title_font = font.Font(family="Roboto", size=20, weight=font.BOLD)
        self.paragraph_font = font.Font(family="Roboto", size=10, weight=font.NORMAL)
    
        self.place(bordermode=OUTSIDE, anchor=CENTER, relx=0.5, rely=0.5, width=600, height=400)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for P in (LoginPage, VerificationPage, AccountPage):
            page_name = P.__name__
            page = P(self)
            self.frames[page_name] = page
            page.grid(row=0,column=0, sticky=NSEW)
        
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        self.current_page = page_name            
        frame = self.frames[page_name]
        frame.tkraise()


class LoginPage(Frame):
    def __init__(self, master: MainFrame):
        super().__init__(master)

        self.title = Label(
            self, 
            text="Login Page", 
            font=master.title_font
        )

        self.email_label = Label(
            self,
            text="E-mail",
            font=master.paragraph_font
        )

        self.email_entry = Entry(
            self,
            width=30,
            justify="center",
            font=master.paragraph_font
        )

        self.login_button = Button(
            self, 
            text="Login",
            width=20,
            command=lambda: self.login(),
            font=master.paragraph_font
        )
    
        self.title.place(anchor=CENTER, relx=0.5, rely=0.15)
        self.email_label.place(anchor=CENTER, relx=0.5, rely=0.45)
        self.email_entry.place(anchor=CENTER, relx=0.5, rely=0.55)
        self.login_button.place(bordermode=OUTSIDE, anchor=CENTER, relx=0.5, rely=0.8)
    
    def login(self):
        email = self.email_entry.get()
        if not re.fullmatch("[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", ErrorMessage.INVALID_INPUT)
            return
        
        self.master.secret = OTP.generate_secret()
        with socket.socket() as s:
            s.connect((socket.gethostname(), PORT))
            s.send(f"{Instruction.GET_SECRET}\n".encode())
            s.send(f"{self.master.secret}\n".encode())

        code = TOTP(self.master.secret).now()
        result = send_email_code(email, code)
        if result == ErrorMessage.NO_ERROR:
            self.master.email = email
            self.master.show_frame("VerificationPage")
            self.master.frames["VerificationPage"].update_timer(EXPIRATION_TIME)
        else:
            messagebox.showerror("Error", result)


class VerificationPage(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.title = Label(
            self, 
            text="Enter code", 
            font=master.title_font
        )

        self.description = Message(
            self,
            text=f"We have sent you a six-digit code on your e-mail. Enter it below to verify your account. Note that the code will expire after {EXPIRATION_TIME} seconds.",
            font=master.paragraph_font,
            width=500
        )

        self.timer_header = Label(
            self,
            text="Expiration countdown:",
            font=master.paragraph_font
        )

        self.timer_data = IntVar()
        self.timer = Label(
            self,
            textvariable=self.timer_data,
            font=master.title_font
        )

        self.code_entry = Entry(
            self,
            justify="center",
            font=master.paragraph_font
        )

        self.back_button = Button(
            self,
            text="Back",
            command=lambda: self.master.show_frame("LoginPage"),
            font = master.paragraph_font
        )

        self.get_new_code_button = Button(
            self,
            text="Get new code",
            command=lambda: self.get_new_code(),
            font = master.paragraph_font,
            state=DISABLED
        )        

        self.verify_button = Button(
            self,
            text="Confirm",
            command=lambda: self.verify(),
            font=master.paragraph_font
        )

        self.title.place(anchor=NW, relx=0.05, rely=0.025)
        self.description.place(anchor=NW, relx=0.05, rely=0.15)
        self.timer_header.place(anchor=CENTER, relx=0.5, rely=0.475)
        self.timer.place(anchor=CENTER, relx=0.5, rely=0.6)
        self.code_entry.place(anchor=CENTER, relx=0.5, rely=0.75)
        self.back_button.place(anchor=CENTER, relx=0.1, rely=0.9)
        self.get_new_code_button.place(anchor=CENTER, relx=0.675, rely=0.9)
        self.verify_button.place(anchor=CENTER, relx=0.9, rely=0.9)

    def update_timer(self, count):
        if self.master.current_page != "VerificationPage":
            return
        
        self.timer_data.set(count)
        
        if count > 0:
            self.master.master.after(1000, self.update_timer, count - 1)
        else:
            self.get_new_code_button["state"] = NORMAL
            self.verify_button["state"] = DISABLED

    def get_new_code(self):
        code = TOTP(self.master.secret).now()
        result = send_email_code(self.master.email, code)
        if result == ErrorMessage.NO_ERROR:
            self.get_new_code_button["state"] = DISABLED
            self.verify_button["state"] = NORMAL
            self.update_timer(EXPIRATION_TIME)
        else:
            messagebox.showerror("Error", result)
        
        self.code_entry.delete(0, END)
    
    def verify(self):
        with socket.socket() as s:
            s.connect((socket.gethostname(), PORT))
            s.send(f"{Instruction.VERIFY}\n".encode())
            s.send(f"{self.code_entry.get()}\n".encode())
            verified = s.recv(1024).decode() == "1"
        
        if verified:
            self.master.current_page = "AccountPage"
            self.master.show_frame("AccountPage")
            self.code_entry.delete(0, END)
        else:
            messagebox.showerror("Error", ErrorMessage.INVALID_CODE)

class AccountPage(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.description = Label(
            self, 
            text="You have successfully logged in!",
            font=master.paragraph_font
        )

        self.back_button = Button(
            self,
            text="Sign out",
            command=lambda: self.master.show_frame("LoginPage"),
            font = master.paragraph_font
        )

        self.description.place(anchor=CENTER, relx=0.5, rely=0.5)
        self.back_button.place(anchor=CENTER, relx=0.5, rely=0.8)


if __name__ == "__main__":
    # Improve text quality. NOTE: This block of code is ignored on macOS.
    if os.name == 'nt':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    root = Tk()
    root.title("TAOTP Generator Using SHA-2 Algorithm App")
    
    window_width, window_height = 600, 400
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = int((screen_width/2) - (window_width/2))
    y = int((screen_height/2) - (window_height/2))

    root.geometry("{}x{}+{}+{}".format(window_width, window_height, x, y))

    main_frame = MainFrame(root)
    root.resizable(False, False)
    root.mainloop()

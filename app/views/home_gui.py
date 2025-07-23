# app/views/home_gui.py
import customtkinter as ctk


class HomeGUI(ctk.CTkFrame):
    """
    View para a tela inicial (Home) da aplicação.
    """

    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")

        # A própria view se posiciona no master
        self.pack(fill="both", expand=True)

        # Adiciona o label de boas-vindas
        label_boas_vindas = ctk.CTkLabel(self,
                                         text="Seja Bem-vindo à Aplicação!",
                                         font=("Roboto", 24))
        label_boas_vindas.pack(pady=40, padx=20)
# app/views/main_view.py

import customtkinter as ctk
from app.widgets.custom_button import StandardButton

class MainView:
    """
    Classe responsável pela construção da interface gráfica principal.
    Utiliza a classe StandardButton para criar botões padronizados.
    """
    def __init__(self, master):
        # --- Estrutura de Layout (Frames) ---
        self.menu_frame = ctk.CTkFrame(master=master, width=180, corner_radius=0)
        self.menu_frame.pack(side="left", fill="y", expand=False, pady=10, padx=10)

        # O frame principal agora não tem nada dentro, será preenchido dinamicamente
        self.main_frame = ctk.CTkFrame(master=master, corner_radius=10, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, pady=10, padx=10)

        # --- Widgets do Menu Vertical ---
        self.menu_label = ctk.CTkLabel(master=self.menu_frame, text="Menu", font=("Roboto", 16))
        self.menu_label.pack(pady=15, padx=10)

        self.buttons = {}
        button_configs = [
            ("Home", "home"),
            ("Aco Militar", "aco_militar"),
            ("Monitor de Arquivos", "monitor"),
            ("Análise Folha", "analise")
        ]

        # Loop para criar os botões usando a nossa nova classe
        for text, key in button_configs:
            button = StandardButton(master=self.menu_frame, text=text, variant="primary")
            button.pack(pady=10, padx=20, fill="x")
            self.buttons[key] = button

        # Botão Sair
        self.btn_quit = StandardButton(
            master=self.menu_frame,
            text="Sair",
            variant="danger"
        )
        self.btn_quit.pack(pady=10, padx=20, fill="x", side="bottom")


# main.py

import customtkinter as ctk
from app.views.main_view import MainView
from app.logic.main_logic import MainLogic

class App(ctk.CTk):
    """
    Classe principal da aplicação que herda de ctk.CTk.
    Serve como o controlador que conecta a View e a Logic.
    """
    def __init__(self):
        super().__init__()

        # --- Configuração da Janela ---
        self.title("Sistema de Automação de Atividades")
        self.geometry("1100x750") # Aumentei um pouco o tamanho para a nova tela
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # --- Instanciar View e Logic ---
        self.main_view = MainView(master=self)
        self.main_logic = MainLogic(view=self.main_view)

        # --- Conectar (Wiring) View e Logic ---
        self.connect_commands()

        # --- Exibir a tela inicial ---
        self.main_logic.show_home()

    def connect_commands(self):
        """
        Mapeia e conecta os comandos dos botões da view aos métodos da lógica.
        """
        command_map = {
            "home": self.main_logic.show_home,
            "aco_militar": self.main_logic.show_aco_militar,
            "monitor": self.main_logic.show_monitor,
            "analise": self.main_logic.show_analise_folha
        }

        for key, button in self.main_view.buttons.items():
            if key in command_map:
                button.configure(command=command_map[key])

        # Conecta o botão de sair
        self.main_view.btn_quit.configure(command=self.quit)

if __name__ == "__main__":
    app = App()
    app.mainloop()


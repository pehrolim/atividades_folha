# main.py

import customtkinter as ctk
from app.views.main_view import MainView
from app.logic.main_logic import MainLogic

# --- CORREÇÃO APLICADA (MONKEY-PATCH) ---
# Esta seção corrige um bug interno do CustomTkinter em certas configurações de
# escala de tela, onde ele passa um valor float (ex: 200.0) para o Tkinter,
# que só aceita inteiros para dimensões de pixels.
try:
    # Guarda o método original
    original_apply_scaling = ctk.CTkBaseClass._apply_widget_scaling

    # Define uma nova função que força o resultado a ser um inteiro
    def new_apply_scaling(self, value):
        scaled_value = original_apply_scaling(self, value)
        return int(scaled_value)

    # Substitui o método original pelo nosso método corrigido
    ctk.CTkBaseClass._apply_widget_scaling = new_apply_scaling
    print("INFO: CustomTkinter scaling patch aplicado com sucesso.")
except Exception as e:
    print(f"AVISO: Não foi possível aplicar o patch de scaling do CustomTkinter: {e}")
# --- FIM DA CORREÇÃO ---


class App(ctk.CTk):
    """
    Classe principal da aplicação que herda de ctk.CTk.
    Serve como o controlador que conecta a View e a Logic.
    """
    def __init__(self):
        super().__init__()

        # --- Configuração da Janela ---
        self.title("Sistema de Automação de Atividades")
        self.geometry("1100x750")
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
            "analise": self.main_logic.show_analise_folha,
            "calc_aco": self.main_logic.show_calc_aco,
            "junta_arquivos": self.main_logic.show_junta_arquivos,
            "honorarios": self.main_logic.show_honorarios
        }

        for key, button in self.main_view.buttons.items():
            if key in command_map:
                button.configure(command=command_map[key])

        # Conecta o botão de sair
        self.main_view.btn_quit.configure(command=self.quit)

if __name__ == "__main__":
    app = App()
    app.mainloop()
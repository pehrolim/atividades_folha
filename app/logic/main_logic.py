# app/logic/main_logic.py
import customtkinter as ctk

# Importa a nova view que queremos exibir
from app.views.aco_militar_gui import AcoMilitarGUI
from app.views.file_monitor_gui import FileMonitorGUI
from app.views.analise_folha_gui import AnaliseView

class MainLogic:
    """
    Classe que contém a lógica de negócio e o controle de navegação.
    """
    def __init__(self, view):
        self.view = view
        self.current_frame = None # Mantém referência do frame atual

    def _clear_main_frame(self):
        """Limpa todos os widgets do frame principal."""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    def show_home(self):
        """Exibe a tela inicial."""
        self._clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.view.main_frame, fg_color="transparent")
        self.current_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.current_frame, text="Seja Bem-vindo à Aplicação!", font=("Roboto", 24)).pack(pady=40)

    def show_monitor(self):
        """Exibe a tela de configurações."""
        self._clear_main_frame()
        self.current_frame = FileMonitorGUI(master=self.view.main_frame)
        self.current_frame.pack(fill="both", expand=True)

    def show_aco_militar(self):
        """Exibe a tela de processamento do Aco Militar."""
        self._clear_main_frame()
        # Instancia a nossa view AcoMilitarGUI dentro do frame principal
        self.current_frame = AcoMilitarGUI(master=self.view.main_frame)
        self.current_frame.pack(fill="both", expand=True)

    def show_analise_folha(self):
        self._clear_main_frame()
        self.current_frame = AnaliseView(master=self.view.main_frame)
        self.current_frame.pack(fill="both", expand=True)
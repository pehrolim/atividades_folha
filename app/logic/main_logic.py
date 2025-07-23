# app/logic/main_logic.py
import customtkinter as ctk

# Importa as views
from app.views.aco_militar_gui import AcoMilitarGUI
from app.views.file_monitor_gui import FileMonitorGUI
from app.views.analise_folha_gui import AnaliseView
from app.views.calc_aco_gui import CalcAcoGUI
from app.views.junta_arquivos_gui import JuntaArquivosGUI
from app.views.honorarios_gui import HonorariosGUI
from app.views.home_gui import HomeGUI  # <-- NOVO IMPORT


class MainLogic:
    """
    Classe que contém a lógica de negócio e o controle de navegação.
    """

    def __init__(self, view):
        self.view = view
        self.current_frame = None

    def _clear_main_frame(self):
        """Limpa todos os widgets do frame principal."""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None

    # --- ALTERAÇÃO AQUI ---
    def show_home(self):
        """Exibe a tela inicial instanciando sua própria classe."""
        self._clear_main_frame()
        self.current_frame = HomeGUI(master=self.view.main_frame)

    def show_monitor(self):
        self._clear_main_frame()
        self.current_frame = FileMonitorGUI(master=self.view.main_frame)

    def show_aco_militar(self):
        self._clear_main_frame()
        self.current_frame = AcoMilitarGUI(master=self.view.main_frame)

    def show_analise_folha(self):
        self._clear_main_frame()
        self.current_frame = AnaliseView(master=self.view.main_frame)

    def show_calc_aco(self):
        self._clear_main_frame()
        self.current_frame = CalcAcoGUI(master=self.view.main_frame)

    def show_junta_arquivos(self):
        self._clear_main_frame()
        self.current_frame = JuntaArquivosGUI(master=self.view.main_frame)

    def show_honorarios(self):
        self._clear_main_frame()
        self.current_frame = HonorariosGUI(master=self.view.main_frame)
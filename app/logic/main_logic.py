# app/logic/main_logic.py
import customtkinter as ctk

# Importa as views
from app.views.aco_militar_gui import AcoMilitarGUI
from app.views.file_monitor_gui import FileMonitorGUI
from app.views.analise_folha_gui import AnaliseView
from app.views.calc_aco_gui import CalcAcoGUI
from app.views.junta_arquivos_gui import JuntaArquivosGUI
from app.views.honorarios_gui import HonorariosGUI
from app.views.home_gui import HomeGUI
from app.views.aco_demais_cat_gui import AcoDemaisCatGUI


class MainLogic:
    """
    Classe que contém a lógica de negócio e o controle de navegação.
    """

    def __init__(self, view):
        self.view = view
        self.current_frame = None

    def _clear_main_frame(self):
        """Destrói todos os widgets filhos do frame principal."""
        for widget in self.view.main_frame.winfo_children():
            widget.destroy()
        self.current_frame = None

    # --- MECANISMO DE CORREÇÃO ---
    def _show_frame(self, frame_class):
        """
        Limpa o frame principal e exibe uma nova tela após um pequeno delay
        para garantir que a destruição da tela anterior seja concluída.
        """
        self._clear_main_frame()
        # O uso de 'after(5, ...)' agenda a criação do novo frame para 5ms no futuro.
        # Isso permite que o loop de eventos do Tkinter processe a destruição
        # dos widgets antigos antes de criar os novos, evitando o conflito.
        self.view.main_frame.after(5, lambda: self._create_frame(frame_class))

    def _create_frame(self, frame_class):
        """Cria a instância do novo frame."""
        self.current_frame = frame_class(master=self.view.main_frame)

    # --- Métodos de navegação agora usam o mecanismo de correção ---
    def show_home(self):
        self._show_frame(HomeGUI)

    def show_monitor(self):
        self._show_frame(FileMonitorGUI)

    def show_aco_militar(self):
        self._show_frame(AcoMilitarGUI)

    def show_analise_folha(self):
        self._show_frame(AnaliseView)

    def show_calc_aco(self):
        self._show_frame(CalcAcoGUI)

    def show_junta_arquivos(self):
        self._show_frame(JuntaArquivosGUI)

    def show_honorarios(self):
        self._show_frame(HonorariosGUI)
    
    def show_demais_cat(self):
        self._show_frame(AcoDemaisCatGUI)
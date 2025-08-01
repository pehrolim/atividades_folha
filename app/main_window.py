# app/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QStackedWidget
from PySide6.QtCore import QSize

# Importa os widgets de tela
from app.views.home_gui import HomeGUI
from app.views.aco_militar_gui import AcoMilitarGUI
from app.views.aco_demais_cat_gui import AcoDemaisCatGUI
from app.views.file_monitor_gui import FileMonitorGUI
from app.views.analise_folha_gui import AnaliseView
from app.views.calc_aco_gui import CalcAcoGUI
from app.views.junta_arquivos_gui import JuntaArquivosGUI
from app.views.honorarios_gui import HonorariosGUI
from app.views.acordo_prestadores_gui import AcordoPrestadoresGUI
from app.views.acordo_prof_aposentados_gui import AcordoProfAposentadosGUI
from app.views.implantacoes_gui import ImplantacoesGUI # <-- **IMPORTAÇÃO CORRETA**
from app.widgets.styled_widgets import StyledButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Automação de Atividades")
        self.resize(1200, 800)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        menu_frame = QFrame()
        menu_layout = QVBoxLayout(menu_frame)
        menu_frame.setFixedWidth(200)
        
        self.pages_widget = QStackedWidget()

        main_layout.addWidget(menu_frame)
        main_layout.addWidget(self.pages_widget)

        # Mapeamento de botões para as classes de tela
        self.view_map = {
            "Home": HomeGUI,
            "Implantações": ImplantacoesGUI, # <-- **NOVA TELA ADICIONADA**
            "ACO Militar": AcoMilitarGUI,
            "ACO (GPC-PENAL)": AcoDemaisCatGUI,
            "Monitor de Arquivos": FileMonitorGUI,
            "Análise Folha": AnaliseView,
            "Cálculo ACO": CalcAcoGUI,
            "Juntar Arquivos": JuntaArquivosGUI,
            "Honorários": HonorariosGUI,
            "Acordo Prestadores": AcordoPrestadoresGUI,
            "Acordo Prof Aposentados": AcordoProfAposentadosGUI,
        }

        # --- CORREÇÃO APLICADA AQUI ---
        # Criar e adicionar os botões e as instâncias das telas
        for text, view_class in self.view_map.items():
            # Esta linha cria a INSTÂNCIA (o objeto) da classe da view
            view_instance = view_class() 
            
            # Adiciona a INSTÂNCIA ao QStackedWidget
            self.pages_widget.addWidget(view_instance)
            
            button = StyledButton(text, variant="primary")
            button.clicked.connect(lambda checked=False, widget=view_instance: self.pages_widget.setCurrentWidget(widget))
            menu_layout.addWidget(button)

        menu_layout.addStretch()
        
        btn_quit = StyledButton("Sair", variant="danger")
        btn_quit.clicked.connect(self.close)
        menu_layout.addWidget(btn_quit)

        if self.pages_widget.count() > 0:
            self.pages_widget.setCurrentIndex(0)
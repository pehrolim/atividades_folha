# app/views/analise_folha_gui.py
import os
import threading
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QFileDialog, 
                               QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget)
from PySide6.QtCore import Slot, Signal, QObject

from app.logic.analise_folha_processor import analisar_arquivos
from app.logic.data_manager import DataManager
from app.widgets.styled_widgets import StyledButton

class WorkerSignals(QObject):
    finished = Signal(object)

class AnaliseView(QWidget):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.caminho_inf_completo = ""
        self.caminho_folha_completo = ""
        
        self.signals = WorkerSignals()
        self.signals.finished.connect(self._atualizar_ui_com_resultados)
        
        self._criar_interface()

    def _criar_interface(self):
        main_layout = QVBoxLayout(self)

        # --- Seção de Seleção de Arquivos ---
        frame_selecao = QFrame()
        frame_selecao.setObjectName("container")
        frame_selecao.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        selecao_layout = QVBoxLayout(frame_selecao)
        
        btn_inf = StyledButton("Selecionar Arquivo de Implantação (.xlsx)", "primary")
        self.lbl_inf = QLabel("Nenhum arquivo selecionado.")
        
        btn_folha = StyledButton("Selecionar Arquivo de Retorno (.txt, .csv)", "primary")
        self.lbl_folha = QLabel("Nenhum arquivo selecionado.")

        selecao_layout.addWidget(QLabel("<b>Passo 1: Selecione os Arquivos</b>"))
        selecao_layout.addWidget(btn_inf)
        selecao_layout.addWidget(self.lbl_inf)
        selecao_layout.addWidget(btn_folha)
        selecao_layout.addWidget(self.lbl_folha)

        # --- Botão de Ação e Abas de Resultado ---
        self.btn_analisar = StyledButton("Analisar Arquivos", "processing")
        
        self.tab_widget = QTabWidget()
        self.tab_sucesso = QWidget()
        self.tab_falhou = QWidget()
        self.tab_widget.addTab(self.tab_sucesso, "Sucesso")
        self.tab_widget.addTab(self.tab_falhou, "Falhou")

        self.lbl_status = QLabel("Pronto para começar.")

        main_layout.addWidget(frame_selecao)
        main_layout.addWidget(self.btn_analisar)
        main_layout.addWidget(self.tab_widget, 1) # O '1' faz o widget expandir
        main_layout.addWidget(self.lbl_status)

        # Conexões
        btn_inf.clicked.connect(self._selecionar_arquivo_inf)
        btn_folha.clicked.connect(self._selecionar_arquivo_folha)
        self.btn_analisar.clicked.connect(self._iniciar_analise)

    @Slot()
    def _selecionar_arquivo_inf(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo de implantação", "", "Arquivos Excel (*.xlsx)")
        if caminho:
            self.caminho_inf_completo = caminho
            self.lbl_inf.setText(os.path.basename(caminho))
            
    @Slot()
    def _selecionar_arquivo_folha(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo de retorno", "", "Arquivos de Texto (*.txt *.csv)")
        if caminho:
            self.caminho_folha_completo = caminho
            self.lbl_folha.setText(os.path.basename(caminho))

    @Slot()
    def _iniciar_analise(self):
        if not self.caminho_inf_completo or not self.caminho_folha_completo:
            self.lbl_status.setText("<font color='red'>Erro: Por favor, selecione ambos os arquivos.</font>")
            return
            
        self.btn_analisar.setEnabled(False)
        self.btn_analisar.setText("Analisando...")
        self.lbl_status.setText("Analisando, por favor aguarde...")
        
        threading.Thread(target=self._executar_analise, daemon=True).start()

    def _executar_analise(self):
        resultado = analisar_arquivos(self.caminho_inf_completo, self.caminho_folha_completo)
        self.signals.finished.emit(resultado)

    @Slot(object)
    def _atualizar_ui_com_resultados(self, resultado):
        if isinstance(resultado, pd.DataFrame):
            df_sucesso = resultado[resultado['TESTE'] == 'SUCESSO'].copy()
            df_falhou = resultado[resultado['TESTE'] == 'FALHOU'].copy()

            self._criar_aba_de_resultado(self.tab_sucesso, df_sucesso, "Sucesso")
            self._criar_aba_de_resultado(self.tab_falhou, df_falhou, "Falhou")
            
            self.lbl_status.setText("<font color='green'>Análise concluída com sucesso!</font>")
        else: # É uma string de erro
            self.lbl_status.setText(f"<font color='red'>Erro na análise: {resultado}</font>")
            
        self.btn_analisar.setEnabled(True)
        self.btn_analisar.setText("Analisar Arquivos")
        
    def _criar_aba_de_resultado(self, tab, df, tipo):
        layout = QVBoxLayout(tab)
        # Limpa layout antigo
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"{len(df)} registros encontrados."))
        header_layout.addStretch()
        btn_download = StyledButton("Baixar Relatório (.xlsx)", "primary")
        if df.empty:
            btn_download.setEnabled(False)
        btn_download.clicked.connect(lambda: self._baixar_arquivo_excel(df, tipo))
        header_layout.addWidget(btn_download)
        
        tabela = QTableWidget()
        if not df.empty:
            colunas = [col for col in df.columns if col != '_merge']
            tabela.setColumnCount(len(colunas))
            tabela.setHorizontalHeaderLabels(colunas)
            tabela.setRowCount(len(df))
            
            for i, row in enumerate(df[colunas].itertuples(index=False)):
                for j, val in enumerate(row):
                    tabela.setItem(i, j, QTableWidgetItem(str(val)))
            tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        layout.addLayout(header_layout)
        layout.addWidget(tabela)

    def _baixar_arquivo_excel(self, df, tipo):
        nome_sugerido = DataManager.generate_report_filename(f"relatorio_{tipo.lower()}", "xlsx")
        filepath, _ = QFileDialog.getSaveFileName(self, f"Salvar Relatório de {tipo}", nome_sugerido, "Arquivo Excel (*.xlsx)")
        if not filepath: return
        
        try:
            colunas_para_salvar = [col for col in df.columns if col != '_merge']
            df_to_save = df[colunas_para_salvar]
            DataManager.save_df_to_xlsx(df_to_save, filepath)
            self.lbl_status.setText(f"Arquivo salvo com sucesso em: {os.path.basename(filepath)}")
        except Exception as e:
            self.lbl_status.setText(f"<font color='red'>Falha ao salvar o arquivo: {e}</font>")
# app/views/acordo_prestadores_gui.py
import os
import datetime
import threading
import pandas as pd
import sys
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTextEdit, 
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Slot, Signal, QObject

from app.logic.acordo_prestadores_processor import AcordoPrestadoresProcessor
from app.widgets.styled_widgets import StyledButton

# Classe para comunicação segura entre a thread de processamento e a GUI
class WorkerSignals(QObject):
    log_message = Signal(str)
    finished = Signal(dict)

class AcordoPrestadoresGUI(QWidget):
    """
    View para o processamento de Acordos de Prestadores, convertida para PySide6.
    """
    def __init__(self, master=None):
        super().__init__(master)

        self.caminhos_arquivos = {'cadastro': "", 'advogados': "", '116': "", '898_csv': ""}
        self.labels_arquivos = {}
        self.caminho_base_saida = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../data/acordos_prestadores'))
        os.makedirs(self.caminho_base_saida, exist_ok=True)

        self.signals = WorkerSignals()
        self.signals.log_message.connect(self._append_log_message)
        self.signals.finished.connect(self._pos_processamento_gui)

        self.processor = AcordoPrestadoresProcessor(logger_callback=self._log_mensagem_thread_safe)
        
        self._criar_interface()

    def _criar_interface(self):
        main_layout = QVBoxLayout(self)

        # --- Frame de Seleção de Arquivos ---
        file_selection_frame = QFrame()
        file_selection_frame.setObjectName("container")
        file_selection_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        selection_layout = QVBoxLayout(file_selection_frame)
        selection_layout.addWidget(QLabel("<b>Selecione os Arquivos Necessários</b>"))

        # Criando os seletores de arquivo
        self._criar_seletor_arquivo(selection_layout, "1. Cadastro Geral (.xlsx):", 'cadastro', "Arquivos Excel (*.xlsx)")
        self._criar_seletor_arquivo(selection_layout, "2. Lista de Advogados (.xlsx):", 'advogados', "Arquivos Excel (*.xlsx)")
        self._criar_seletor_arquivo(selection_layout, "3. Código 116 (.csv):", '116', "Arquivos CSV (*.csv)")
        self._criar_seletor_arquivo(selection_layout, "4. Código 898 (.csv):", '898_csv', "Arquivos CSV (*.csv)")
        
        # --- Frame de Saída ---
        output_frame = QFrame()
        output_frame.setObjectName("container")
        output_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        output_layout = QVBoxLayout(output_frame)

        self.lbl_caminho_base = QLabel(f"<b>Pasta de Saída:</b> {self.caminho_base_saida}")
        self.lbl_caminho_base.setWordWrap(True)
        btn_selecionar_pasta = StyledButton("Selecionar Pasta de Saída", "primary")
        output_layout.addWidget(QLabel("<b>5. Escolha a Pasta para Salvar os Resultados:</b>"))
        output_layout.addWidget(self.lbl_caminho_base)
        output_layout.addWidget(btn_selecionar_pasta)

        # --- Botão de Processamento e Log ---
        self.btn_processar = StyledButton("⚙️ Iniciar Processamento", "processing")
        self.caixa_log = QTextEdit()
        self.caixa_log.setReadOnly(True)

        main_layout.addWidget(file_selection_frame)
        main_layout.addWidget(output_frame)
        main_layout.addWidget(self.btn_processar)
        main_layout.addWidget(QLabel("<b>Log de Processamento:</b>"))
        main_layout.addWidget(self.caixa_log, 1)

        # --- Conexões ---
        btn_selecionar_pasta.clicked.connect(self._selecionar_diretorio_saida)
        self.btn_processar.clicked.connect(self._iniciar_processamento_threaded)

    def _criar_seletor_arquivo(self, parent_layout, label_text, tipo_arquivo, file_filter):
        frame = QFrame()
        # --- CORREÇÃO AQUI ---
        layout = QHBoxLayout() # Cria o layout
        frame.setLayout(layout)  # Aplica o layout ao frame
        # --------------------
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        label.setFixedWidth(200)
        
        self.labels_arquivos[tipo_arquivo] = QLabel("Nenhum arquivo selecionado.")
        self.labels_arquivos[tipo_arquivo].setStyleSheet("color: gray;")
        
        btn = StyledButton("...", "primary")
        btn.setFixedWidth(40)
        btn.clicked.connect(lambda: self._selecionar_arquivo(tipo_arquivo, label_text, file_filter))

        layout.addWidget(label)
        layout.addWidget(self.labels_arquivos[tipo_arquivo], 1)
        layout.addWidget(btn)
        parent_layout.addWidget(frame)

    @Slot()
    def _selecionar_arquivo(self, tipo_arquivo, titulo, file_filter):
        caminho, _ = QFileDialog.getOpenFileName(self, titulo, "", file_filter)
        if caminho:
            self.caminhos_arquivos[tipo_arquivo] = caminho
            self.labels_arquivos[tipo_arquivo].setText(os.path.basename(caminho))
            self.labels_arquivos[tipo_arquivo].setStyleSheet("color: blue;")
            self._log_mensagem_thread_safe(f"Arquivo '{tipo_arquivo}' selecionado: {os.path.basename(caminho)}")
        else:
            self.caminhos_arquivos[tipo_arquivo] = ""
            self.labels_arquivos[tipo_arquivo].setText("Nenhum arquivo selecionado.")
            self.labels_arquivos[tipo_arquivo].setStyleSheet("color: gray;")
            self._log_mensagem_thread_safe(f"Seleção de arquivo '{tipo_arquivo}' cancelada.")

    @Slot()
    def _selecionar_diretorio_saida(self):
        caminho = QFileDialog.getExistingDirectory(self, "Escolha a Pasta para Salvar os Resultados", self.caminho_base_saida)
        if caminho:
            self.caminho_base_saida = caminho
            self.lbl_caminho_base.setText(f"<b>Pasta de Saída:</b> {caminho}")
            self._log_mensagem_thread_safe(f"Pasta de saída selecionada: {caminho}")

    def _validar_selecoes(self):
        for nome, caminho in self.caminhos_arquivos.items():
            if not caminho or not os.path.exists(caminho):
                msg = f"Por favor, selecione o arquivo de '{nome.replace('_csv', '')}' e verifique se ele existe."
                QMessageBox.warning(self, "Arquivos Faltando", msg)
                self._log_mensagem_thread_safe(f"Erro: Arquivo '{nome}' não selecionado ou não existe.")
                return False
        return True

    @Slot()
    def _iniciar_processamento_threaded(self):
        if not self._validar_selecoes(): return
        
        self.btn_processar.setEnabled(False)
        self.btn_processar.setText("Processando...")
        self._log_mensagem_thread_safe("Iniciando o processamento... Isso pode levar um momento.")
        
        threading.Thread(target=self._executar_processamento, daemon=True).start()

    def _executar_processamento(self):
        try:
            resultado_msg = self.processor.processar_acordo_prestadores(
                self.caminhos_arquivos['cadastro'], self.caminhos_arquivos['advogados'],
                self.caminhos_arquivos['116'], self.caminhos_arquivos['898_csv'],
                self.caminho_base_saida
            )
            self.signals.finished.emit({"status": "sucesso", "mensagem": resultado_msg})
        except Exception as e:
            self.signals.finished.emit({"status": "erro", "mensagem": f"Ocorreu um erro durante o processamento:\n{e}"})

    @Slot(dict)
    def _pos_processamento_gui(self, resultado):
        if resultado["status"] == "sucesso":
            QMessageBox.information(self, "Sucesso", resultado["mensagem"])
            self._log_mensagem_thread_safe(f"✅ {resultado['mensagem']}")
        else:
            QMessageBox.critical(self, "Erro no Processamento", resultado["mensagem"])
            self._log_mensagem_thread_safe(f"🚨 Erro no Processamento: {resultado['mensagem']}")
        
        self.btn_processar.setEnabled(True)
        self.btn_processar.setText("⚙️ Iniciar Processamento")

    def _log_mensagem_thread_safe(self, mensagem):
        self.signals.log_message.emit(mensagem)

    @Slot(str)
    def _append_log_message(self, mensagem):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.caixa_log.append(f"[{timestamp}] {mensagem}")
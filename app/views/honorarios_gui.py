# app/views/honorarios_gui.py
import os
import datetime
import threading
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFrame, QLabel, QTextEdit, 
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Slot, Signal, QObject

from app.logic.honorarios_processor import HonorariosProcessor
from app.widgets.styled_widgets import StyledButton

class WorkerSignals(QObject):
    finished = Signal(dict)
    log_message = Signal(str)

class HonorariosGUI(QWidget):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.caminho_arquivo_excel = ""
        self.pasta_destino_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/honorarios_reports'))
        os.makedirs(self.pasta_destino_pdf, exist_ok=True)
        
        self.signals = WorkerSignals()
        self.signals.finished.connect(self._on_processing_finished)
        self.signals.log_message.connect(self._append_log_message)
        
        self.processor = HonorariosProcessor(logger_callback=self._log_mensagem_thread_safe)
        
        self._criar_interface()

    def _criar_interface(self):
        main_layout = QVBoxLayout(self)

        settings_frame = QFrame()
        settings_frame.setObjectName("container")
        settings_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        settings_layout = QVBoxLayout(settings_frame)
        
        self.lbl_nome_arquivo = QLabel("Nenhum arquivo selecionado.")
        btn_sel_arquivo = StyledButton("Selecionar Arquivo Excel", "primary")
        
        self.lbl_pasta_destino = QLabel(f"<b>Pasta de Destino:</b> {self.pasta_destino_pdf}")
        self.lbl_pasta_destino.setWordWrap(True)
        btn_sel_pasta = StyledButton("Selecionar Pasta de Destino", "primary")
        
        settings_layout.addWidget(QLabel("<b>Configuração do Relatório de Honorários</b>"))
        settings_layout.addWidget(QLabel("Arquivo Excel de Honorários:"))
        settings_layout.addWidget(self.lbl_nome_arquivo)
        settings_layout.addWidget(btn_sel_arquivo)
        settings_layout.addWidget(self.lbl_pasta_destino)
        settings_layout.addWidget(btn_sel_pasta)
        
        self.btn_gerar_relatorio = StyledButton("📈 Gerar Relatório de Honorários", "processing")
        
        self.caixa_log = QTextEdit()
        self.caixa_log.setReadOnly(True)

        main_layout.addWidget(settings_frame)
        main_layout.addWidget(self.btn_gerar_relatorio)
        main_layout.addWidget(QLabel("<b>Log de Processamento:</b>"))
        main_layout.addWidget(self.caixa_log, 1)

        # Conexões
        btn_sel_arquivo.clicked.connect(self._selecionar_arquivo_excel)
        btn_sel_pasta.clicked.connect(self._selecionar_pasta_destino)
        self.btn_gerar_relatorio.clicked.connect(self._iniciar_geracao_relatorio)

    @Slot()
    def _selecionar_arquivo_excel(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo de honorários", "", "Arquivos Excel (*.xlsx *.xls)")
        if caminho:
            self.caminho_arquivo_excel = caminho
            self.lbl_nome_arquivo.setText(os.path.basename(caminho))
            self._log_mensagem_thread_safe(f"Arquivo selecionado: {os.path.basename(caminho)}")

    @Slot()
    def _selecionar_pasta_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione a pasta de destino", self.pasta_destino_pdf)
        if pasta:
            self.pasta_destino_pdf = pasta
            self.lbl_pasta_destino.setText(f"<b>Pasta de Destino:</b> {pasta}")
            os.makedirs(pasta, exist_ok=True)
            
    @Slot()
    def _iniciar_geracao_relatorio(self):
        if not self.caminho_arquivo_excel:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um arquivo Excel primeiro.")
            return
            
        self.btn_gerar_relatorio.setEnabled(False)
        self.btn_gerar_relatorio.setText("Gerando Relatório...")
        self._log_mensagem_thread_safe("Iniciando a geração do relatório...")
        
        threading.Thread(target=self._executar_geracao_relatorio, daemon=True).start()

    def _executar_geracao_relatorio(self):
        try:
            resultado_msg = self.processor.processar_honorarios_e_gerar_pdf(
                self.caminho_arquivo_excel, self.pasta_destino_pdf
            )
            self.signals.finished.emit({"status": "sucesso", "mensagem": resultado_msg})
        except Exception as e:
            self.signals.finished.emit({"status": "erro", "mensagem": str(e)})

    @Slot(dict)
    def _on_processing_finished(self, resultado):
        if resultado["status"] == "sucesso":
            QMessageBox.information(self, "Sucesso", resultado["mensagem"])
            self._log_mensagem_thread_safe(f"✅ {resultado['mensagem']}")
        else:
            QMessageBox.critical(self, "Erro", resultado["mensagem"])
            self._log_mensagem_thread_safe(f"❌ Erro: {resultado['mensagem']}")
            
        self.btn_gerar_relatorio.setEnabled(True)
        self.btn_gerar_relatorio.setText("📈 Gerar Relatório de Honorários")

    def _log_mensagem_thread_safe(self, mensagem):
        self.signals.log_message.emit(mensagem)

    @Slot(str)
    def _append_log_message(self, mensagem):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.caixa_log.append(f"[{timestamp}] {mensagem}")
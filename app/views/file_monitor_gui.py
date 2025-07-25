# app/views/file_monitor_gui.py
import os
import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTextEdit, 
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Slot, Signal, QObject, QTimer

from app.logic.data_manager import DataManager
from app.logic.file_monitor import FileMonitor
from app.widgets.styled_widgets import StyledButton

class WorkerSignals(QObject):
    log_message = Signal(str)
    file_processed = Signal()

class FileMonitorGUI(QWidget):
    def __init__(self, master=None):
        super().__init__(master)

        # --- Lógica de negócio ---
        self.pasta_origem_monitoramento = os.path.expanduser("~/Downloads")
        self.pasta_destino_processados = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/processados'))
        self.colunas_folha = ['MATRICULA', 'NOME', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO',
                              'ORGAO', 'CLF', 'SIMBOLO', 'SITUACAO', 'SAIDA', 'DATA_AFAST', 'GRUPO', 'REGIME']
        
        self.signals = WorkerSignals()
        self.signals.log_message.connect(self._append_log_message)
        self.signals.file_processed.connect(self._atualizar_info_dados)

        self.data_manager = DataManager(self.colunas_folha)
        self.file_monitor = FileMonitor(
            data_manager=self.data_manager,
            logger_callback=self._log_mensagem_thread_safe,
            arquivo_processado_callback=self.signals.file_processed.emit
        )

        self._criar_interface()
        self._atualizar_info_dados()

    def _criar_interface(self):
        main_layout = QVBoxLayout(self)

        folders_frame = QFrame()
        folders_frame.setObjectName("container")
        folders_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        folders_layout = QVBoxLayout(folders_frame)
        
        self.lbl_pasta_origem = QLabel(f"<b>Pasta de Origem:</b> {self.pasta_origem_monitoramento}")
        btn_sel_origem = StyledButton("Selecionar Pasta de Origem", "primary")
        
        self.lbl_pasta_destino = QLabel(f"<b>Pasta de Destino:</b> {self.pasta_destino_processados}")
        btn_sel_destino = StyledButton("Selecionar Pasta de Destino", "primary")

        folders_layout.addWidget(self.lbl_pasta_origem)
        folders_layout.addWidget(btn_sel_origem)
        folders_layout.addWidget(self.lbl_pasta_destino)
        folders_layout.addWidget(btn_sel_destino)

        self.btn_alternar_monitoramento = StyledButton("▶ Iniciar Monitoramento", "success")
        
        info_actions_frame = QFrame()
        info_actions_frame.setObjectName("container")
        info_actions_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        info_actions_layout = QVBoxLayout(info_actions_frame)
        
        self.lbl_info_dados = QLabel("Dados Acumulados: 0 registros")
        
        botoes_layout = QHBoxLayout()
        btn_csv = StyledButton("💾 Salvar CSV", "primary")
        btn_xlsx = StyledButton("💾 Salvar XLSX", "primary")
        btn_limpar = StyledButton("🧹 Limpar Dados", "danger")
        botoes_layout.addWidget(btn_csv)
        botoes_layout.addWidget(btn_xlsx)
        botoes_layout.addWidget(btn_limpar)

        info_actions_layout.addWidget(self.lbl_info_dados)
        info_actions_layout.addLayout(botoes_layout)
        
        self.caixa_log = QTextEdit()
        self.caixa_log.setReadOnly(True)

        main_layout.addWidget(folders_frame)
        main_layout.addWidget(self.btn_alternar_monitoramento)
        main_layout.addWidget(info_actions_frame)
        main_layout.addWidget(QLabel("<b>Log de Eventos:</b>"))
        main_layout.addWidget(self.caixa_log)

        # Conexões
        btn_sel_origem.clicked.connect(self._selecionar_pasta_origem)
        btn_sel_destino.clicked.connect(self._selecionar_pasta_destino)
        self.btn_alternar_monitoramento.clicked.connect(self._alternar_monitoramento)
        btn_csv.clicked.connect(self._salvar_csv)
        btn_xlsx.clicked.connect(self._salvar_xlsx)
        btn_limpar.clicked.connect(self._limpar_dados)

    @Slot()
    def _selecionar_pasta_origem(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione a pasta de origem", self.pasta_origem_monitoramento)
        if pasta:
            self.pasta_origem_monitoramento = pasta
            self.lbl_pasta_origem.setText(f"<b>Pasta de Origem:</b> {pasta}")
            self._log_mensagem_thread_safe(f"Pasta de origem selecionada: {pasta}")

    @Slot()
    def _selecionar_pasta_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione a pasta de destino", self.pasta_destino_processados)
        if pasta:
            self.pasta_destino_processados = pasta
            self.lbl_pasta_destino.setText(f"<b>Pasta de Destino:</b> {pasta}")
            self._log_mensagem_thread_safe(f"Pasta de destino selecionada: {pasta}")

    @Slot()
    def _alternar_monitoramento(self):
        if self.file_monitor.obter_status_monitoramento():
            if self.file_monitor.parar_monitoramento():
                self.btn_alternar_monitoramento.setText("▶ Iniciar Monitoramento")
                self.btn_alternar_monitoramento.setStyleSheet(StyledButton.STYLES["success"])
        else:
            if self.file_monitor.iniciar_monitoramento(self.pasta_origem_monitoramento, self.pasta_destino_processados):
                self.btn_alternar_monitoramento.setText("⏹ Parar Monitoramento")
                self.btn_alternar_monitoramento.setStyleSheet(StyledButton.STYLES["danger"])

    @Slot()
    def _salvar_csv(self):
        if self.data_manager.esta_vazio():
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", self.pasta_destino_processados, "Arquivos CSV (*.csv)")
        if path:
            try:
                self.data_manager.salvar_para_csv(path)
                QMessageBox.information(self, "Sucesso", f"Arquivo salvo em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{e}")

    @Slot()
    def _salvar_xlsx(self):
        if self.data_manager.esta_vazio():
            QMessageBox.warning(self, "Aviso", "Não há dados para salvar."); return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Excel", self.pasta_destino_processados, "Arquivos Excel (*.xlsx)")
        if path:
            try:
                self.data_manager.salvar_para_xlsx(path)
                QMessageBox.information(self, "Sucesso", f"Arquivo salvo em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{e}")

    @Slot()
    def _limpar_dados(self):
        if self.data_manager.esta_vazio():
            self._log_mensagem_thread_safe("🧹 Dados já estão limpos."); return
        reply = QMessageBox.question(self, "Confirmação", "Deseja realmente limpar todos os dados acumulados?")
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager.limpar_dados()
            self._log_mensagem_thread_safe("🧹 Dados acumulados foram limpos.")
            self._atualizar_info_dados()

    @Slot()
    def _atualizar_info_dados(self):
        num_registros = len(self.data_manager.obter_dados_acumulados())
        self.lbl_info_dados.setText(f"Dados Acumulados: {num_registros} registros")
        
    def _log_mensagem_thread_safe(self, mensagem):
        self.signals.log_message.emit(mensagem)

    @Slot(str)
    def _append_log_message(self, mensagem):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.caixa_log.append(f"[{timestamp}] {mensagem}")
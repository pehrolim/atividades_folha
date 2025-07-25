# app/views/acordo_prof_aposentados_gui.py
import os
import datetime
import threading
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QTextEdit, 
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Slot, Signal, QObject

from app.logic.acordo_prof_aposentados_processor import AcordoProfAposentadosProcessor
from app.widgets.styled_widgets import StyledButton

# Classe para comunicação segura entre a thread de processamento e a GUI
class WorkerSignals(QObject):
    log_message = Signal(str)
    finished = Signal(dict)

class AcordoProfAposentadosGUI(QWidget):
    """
    View para o processamento de Acordos de Professores Aposentados, convertida para PySide6.
    """
    def __init__(self, master=None):
        super().__init__(master)

        self.novos_input_path = ""
        self.bloqueados_input_path = ""
        
        self.signals = WorkerSignals()
        self.signals.log_message.connect(self._append_log_message)
        self.signals.finished.connect(self._pos_processamento_gui)

        self.processor = AcordoProfAposentadosProcessor()
        self._criar_interface()

    def _criar_interface(self):
        main_layout = QVBoxLayout(self)

        # --- Frame de Seleção de Arquivos ---
        file_selection_frame = QFrame()
        file_selection_frame.setObjectName("container")
        file_selection_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        selection_layout = QVBoxLayout(file_selection_frame)
        selection_layout.addWidget(QLabel("<b>1. Selecione os Arquivos de Entrada (Opcional)</b>"))

        # Seletores de arquivo
        self.lbl_novos_path = self._criar_seletor_arquivo(selection_layout, "Novos Acordos (.xlsx):", self._selecionar_arquivo_novos)
        self.lbl_bloqueados_path = self._criar_seletor_arquivo(selection_layout, "Bloqueados (.xlsx):", self._selecionar_arquivo_bloqueados)
        
        # --- Botão de Processamento e Log ---
        self.btn_processar = StyledButton("⚙️ Iniciar Processamento", "processing")
        self.caixa_log = QTextEdit()
        self.caixa_log.setReadOnly(True)

        main_layout.addWidget(file_selection_frame)
        main_layout.addWidget(self.btn_processar)
        main_layout.addWidget(QLabel("<b>Log de Processamento:</b>"))
        main_layout.addWidget(self.caixa_log, 1)

        # --- Conexões ---
        self.btn_processar.clicked.connect(self._iniciar_processamento_threaded)

    def _criar_seletor_arquivo(self, parent_layout, label_text, slot_function):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0,0,0,0)
        
        label = QLabel(label_text)
        label.setFixedWidth(150)
        
        path_label = QLabel("Nenhum arquivo selecionado.")
        path_label.setStyleSheet("color: gray;")
        
        btn = StyledButton("...", "primary")
        btn.setFixedWidth(40)
        btn.clicked.connect(slot_function)

        layout.addWidget(label)
        layout.addWidget(path_label, 1)
        layout.addWidget(btn)
        parent_layout.addWidget(frame)
        return path_label

    @Slot()
    def _selecionar_arquivo_novos(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione a planilha de Novos Acordos", "", "Arquivos Excel (*.xlsx *.xls)")
        if arquivo:
            self.novos_input_path = arquivo
            self.lbl_novos_path.setText(os.path.basename(arquivo))
            self.lbl_novos_path.setStyleSheet("color: blue;")
            self._log_mensagem_thread_safe(f"Arquivo de Novos Acordos selecionado: {os.path.basename(arquivo)}")
        else:
            self.novos_input_path = ""
            self.lbl_novos_path.setText("Nenhum arquivo selecionado.")
            self.lbl_novos_path.setStyleSheet("color: gray;")

    @Slot()
    def _selecionar_arquivo_bloqueados(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione a planilha de Bloqueados", "", "Arquivos Excel (*.xlsx *.xls)")
        if arquivo:
            self.bloqueados_input_path = arquivo
            self.lbl_bloqueados_path.setText(os.path.basename(arquivo))
            self.lbl_bloqueados_path.setStyleSheet("color: blue;")
            self._log_mensagem_thread_safe(f"Arquivo de Bloqueados selecionado: {os.path.basename(arquivo)}")
        else:
            self.bloqueados_input_path = ""
            self.lbl_bloqueados_path.setText("Nenhum arquivo selecionado.")
            self.lbl_bloqueados_path.setStyleSheet("color: gray;")

    def _validar_selecoes(self):
        if not self.novos_input_path and not self.bloqueados_input_path:
            QMessageBox.warning(self, "Nenhum Arquivo", "Por favor, selecione pelo menos um arquivo para processar.")
            return False
        return True

    @Slot()
    def _iniciar_processamento_threaded(self):
        if not self._validar_selecoes(): return
        
        self.btn_processar.setEnabled(False)
        self.btn_processar.setText("Processando...")
        self._log_mensagem_thread_safe("Iniciando o processamento...")
        
        threading.Thread(target=self._executar_processamento, daemon=True).start()

    def _executar_processamento(self):
        resultados = {'novos': {}, 'bloqueados': {}}
        try:
            if self.novos_input_path:
                self.signals.log_message.emit("="*50 + "\nProcessando arquivo de NOVOS ACORDOS...")
                df_input_novos = pd.read_excel(self.novos_input_path)
                df_apos, df_pensao, df_calculos = self.processor.tratar_novos(df_input_novos)
                resultados['novos'] = {'apos': df_apos, 'pensao': df_pensao, 'calculos': df_calculos}
                self.signals.log_message.emit("Dados de Novos Acordos processados.")

            if self.bloqueados_input_path:
                self.signals.log_message.emit("="*50 + "\nProcessando arquivo de BLOQUEADOS...")
                df_input_bloqueados = pd.read_excel(self.bloqueados_input_path)
                df_apos, df_pensao, df_calculos = self.processor.tratar_bloqueados(df_input_bloqueados)
                resultados['bloqueados'] = {'apos': df_apos, 'pensao': df_pensao, 'calculos': df_calculos}
                self.signals.log_message.emit("Dados de Bloqueados processados.")
            
            self.signals.finished.emit({"status": "sucesso", "data": resultados})
        except Exception as e:
            self.signals.finished.emit({"status": "erro", "mensagem": str(e)})

    @Slot(dict)
    def _pos_processamento_gui(self, resultado):
        if resultado["status"] == "erro":
            QMessageBox.critical(self, "Erro no Processamento", f"Ocorreu um erro:\n{resultado['mensagem']}")
            self._log_mensagem_thread_safe(f"🚨 Erro no Processamento: {resultado['mensagem']}")
        else:
            self._log_mensagem_thread_safe("Processamento em memória concluído. Solicitando locais para salvar os arquivos...")
            # Salva os resultados para NOVOS
            if resultado['data']['novos']:
                self._salvar_resultados(resultado['data']['novos'], "NOVOS")
            # Salva os resultados para BLOQUEADOS
            if resultado['data']['bloqueados']:
                self._salvar_resultados(resultado['data']['bloqueados'], "BLOQUEADOS")
            
            self._log_mensagem_thread_safe("✅ Processamento concluído com sucesso!")
            QMessageBox.information(self, "Sucesso", "Processamento concluído com sucesso!")

        self.btn_processar.setEnabled(True)
        self.btn_processar.setText("⚙️ Iniciar Processamento")

    def _salvar_resultados(self, dataframes, prefixo):
        output_dir = None
        
        df_apos = dataframes.get('apos')
        if df_apos is not None and not df_apos.empty:
            path, _ = QFileDialog.getSaveFileName(self, f"Salvar LANÇAMENTO APOSENTADOS ({prefixo})", f"LANCAMENTO_APOSENTADOS_{prefixo}.xlsx", "Arquivos Excel (*.xlsx)")
            if path:
                df_apos.to_excel(path, index=False)
                self._log_mensagem_thread_safe(f"Arquivo de aposentados ({prefixo}) salvo em: {path}")
                output_dir = os.path.dirname(path)
        
        df_pensao = dataframes.get('pensao')
        if df_pensao is not None and not df_pensao.empty:
            path, _ = QFileDialog.getSaveFileName(self, f"Salvar LANÇAMENTO PENSIONISTAS ({prefixo})", f"LANCAMENTO_PENSIONISTAS_{prefixo}.xlsx", "Arquivos Excel (*.xlsx)")
            if path:
                df_pensao.to_excel(path, index=False)
                self._log_mensagem_thread_safe(f"Arquivo de pensionistas ({prefixo}) salvo em: {path}")
                if not output_dir: output_dir = os.path.dirname(path)

        df_calculos = dataframes.get('calculos')
        if df_calculos is not None and not df_calculos.empty and output_dir:
            path_calculos = os.path.join(output_dir, f"CALCULOS_COMPLETOS_{prefixo}.xlsx")
            df_calculos.to_excel(path_calculos, index=False)
            self._log_mensagem_thread_safe(f"Arquivo com cálculos completos ({prefixo}) salvo em: {path_calculos}")

    def _log_mensagem_thread_safe(self, mensagem):
        self.signals.log_message.emit(mensagem)

    @Slot(str)
    def _append_log_message(self, mensagem):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.caixa_log.append(f"[{timestamp}] {mensagem}")
# app/views/junta_arquivos_gui.py
import os
import datetime
import threading
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTreeWidget, 
                               QHeaderView, QTreeWidgetItem, QFileDialog, QMessageBox, QTextEdit, QLabel)
from PySide6.QtCore import Slot, Signal, QObject

from app.logic.junta_arquivos_processor import ExcelProcessor
from app.widgets.styled_widgets import StyledButton

# Classe para emitir sinais de uma thread secundária para a GUI principal
class WorkerSignals(QObject):
    log_message = Signal(str)
    finished = Signal(dict)

class JuntaArquivosGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.arquivos_selecionados = []
        self.pasta_destino_saida = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/excel_processed'))
        os.makedirs(self.pasta_destino_saida, exist_ok=True)
        self.processor = ExcelProcessor(logger_callback=self._log_mensagem_thread_safe)
        
        self.signals = WorkerSignals()
        self.signals.log_message.connect(self._append_log_message)
        self.signals.finished.connect(self._on_processing_finished)
        
        self._criar_interface()

    def _criar_interface(self):
        main_layout = QVBoxLayout(self)

        # --- Frame Superior com botões e lista ---
        top_frame = QFrame()
        top_layout = QVBoxLayout(top_frame)
        top_frame.setStyleSheet("QFrame { border: 1px solid #dcdcdc; border-radius: 5px; }")
        
        actions_layout = QHBoxLayout()
        self.btn_adicionar = StyledButton("➕ Adicionar Arquivo(s)", variant="success")
        self.btn_remover = StyledButton("🗑️ Remover Selecionado", variant="danger")
        actions_layout.addWidget(self.btn_adicionar)
        actions_layout.addWidget(self.btn_remover)
        actions_layout.addStretch()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Arquivos na Fila para Processamento"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        top_layout.addLayout(actions_layout)
        top_layout.addWidget(self.tree)
        
        # --- Frame Inferior com configurações ---
        bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_frame.setStyleSheet("QFrame { border: 1px solid #dcdcdc; border-radius: 5px; }")

        self.lbl_pasta_destino = QLabel(f"Pasta de Destino: {self.pasta_destino_saida}")
        self.lbl_pasta_destino.setWordWrap(True)
        btn_selecionar_pasta = StyledButton("Selecionar Pasta", variant="primary")
        
        bottom_layout.addWidget(self.lbl_pasta_destino)
        bottom_layout.addWidget(btn_selecionar_pasta)

        # --- Botão de processamento e Log ---
        self.btn_processar = StyledButton("🚀 Processar Arquivos", variant="processing")
        self.caixa_log = QTextEdit()
        self.caixa_log.setReadOnly(True)

        main_layout.addWidget(top_frame)
        main_layout.addWidget(bottom_frame)
        main_layout.addWidget(self.btn_processar)
        main_layout.addWidget(QLabel("Log de Processamento:"))
        main_layout.addWidget(self.caixa_log)

        # --- Conexões (Sinais e Slots) ---
        self.btn_adicionar.clicked.connect(self._adicionar_arquivo)
        self.btn_remover.clicked.connect(self._remover_arquivo_selecionado)
        btn_selecionar_pasta.clicked.connect(self._selecionar_pasta_destino)
        self.btn_processar.clicked.connect(self._iniciar_processamento_threaded)

    @Slot()
    def _adicionar_arquivo(self):
        arquivos, _ = QFileDialog.getOpenFileNames(self, "Selecione um ou mais arquivos", "", "Arquivos Excel (*.xlsx *.xls)")
        if not arquivos: return
        
        novos_adicionados = 0
        for path in arquivos:
            if not any(d['caminho'] == path for d in self.arquivos_selecionados):
                self.arquivos_selecionados.append({'caminho': path, 'nome_amigavel': os.path.basename(path)})
                novos_adicionados += 1
        
        if novos_adicionados > 0:
            self._log_mensagem_thread_safe(f"📁 {novos_adicionados} arquivo(s) adicionado(s).")
            self._atualizar_tabela()

    @Slot()
    def _remover_arquivo_selecionado(self):
        selected_item = self.tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo para remover.")
            return

        nome_para_remover = selected_item.text(0)
        self.arquivos_selecionados = [d for d in self.arquivos_selecionados if d['nome_amigavel'] != nome_para_remover]
        self._log_mensagem_thread_safe(f"🗑️ Arquivo removido: {nome_para_remover}")
        self._atualizar_tabela()

    def _atualizar_tabela(self):
        self.tree.clear()
        for item_data in self.arquivos_selecionados:
            tree_item = QTreeWidgetItem([item_data['nome_amigavel']])
            self.tree.addTopLevelItem(tree_item)

    @Slot()
    def _selecionar_pasta_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione a pasta de saída", self.pasta_destino_saida)
        if pasta:
            self.pasta_destino_saida = pasta
            self.lbl_pasta_destino.setText(f"Pasta de Destino: {self.pasta_destino_saida}")

    @Slot()
    def _iniciar_processamento_threaded(self):
        if not self.arquivos_selecionados:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um arquivo para processar."); return
            
        self.btn_processar.setEnabled(False)
        self.btn_processar.setText("Processando...")
        
        lista_caminhos = [d['caminho'] for d in self.arquivos_selecionados]
        
        # Executa o processamento em uma thread separada
        thread = threading.Thread(target=self._executar_processamento, args=(lista_caminhos,), daemon=True)
        thread.start()

    def _executar_processamento(self, lista_de_arquivos):
        try:
            df_consolidado = self.processor.processar_arquivos_excel(lista_de_arquivos)
            self.processor.salvar_consolidado_excel(self.pasta_destino_saida, df_consolidado)
            self.processor.gerar_resumo_e_pdf_log(self.pasta_destino_saida, df_consolidado)
            resultado = {"status": "sucesso", "mensagem": "Processamento concluído com sucesso!"}
        except Exception as e:
            resultado = {"status": "erro", "mensagem": str(e)}
        
        self.signals.finished.emit(resultado)

    @Slot(dict)
    def _on_processing_finished(self, resultado):
        if resultado["status"] == "sucesso":
            QMessageBox.information(self, "Sucesso", resultado["mensagem"])
            self._log_mensagem_thread_safe("🎉 Processamento finalizado!")
        else:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro: {resultado['mensagem']}")
            self._log_mensagem_thread_safe(f"❌ Erro: {resultado['mensagem']}")
            
        self.btn_processar.setEnabled(True)
        self.btn_processar.setText("🚀 Processar Arquivos")
    
    def _log_mensagem_thread_safe(self, mensagem):
        self.signals.log_message.emit(mensagem)

    @Slot(str)
    def _append_log_message(self, mensagem):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.caixa_log.append(f"[{timestamp}] {mensagem}")
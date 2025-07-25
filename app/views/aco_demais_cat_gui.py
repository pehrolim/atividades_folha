# app/views/aco_demais_cat_gui.py
import os
import datetime
import threading
import sys
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QLabel, QCheckBox, 
                               QLineEdit, QFileDialog, QMessageBox, QTextEdit)
from PySide6.QtCore import Slot, Signal, QObject, Qt
from PySide6.QtGui import QIntValidator

# Importa a lógica e os nossos componentes padronizados
from app.logic.aco_demais_cat_processor import AcoDemaisCatProcessor
from app.widgets.styled_widgets import StyledButton

# Classe para comunicação segura entre threads e a GUI
class WorkerSignals(QObject):
    log_message = Signal(str)
    validation_finished = Signal(int)
    processing_finished = Signal(dict)

class AcoDemaisCatGUI(QWidget):
    """
    View para o processamento de Acordos de Custo para as demais categorias,
    com estrutura padronizada e visual de tabela para a lista de arquivos.
    """
    def __init__(self, master=None):
        super().__init__(master)

        self.arquivos_selecionados = []
        self.pasta_destino_saida = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../data/demais_categorias_outputs'))
        os.makedirs(self.pasta_destino_saida, exist_ok=True)
        
        self.signals = WorkerSignals()
        self.signals.log_message.connect(self._append_log_message)
        self.signals.validation_finished.connect(self._on_validation_finished)
        self.signals.processing_finished.connect(self._pos_processamento_gui)

        self.processor = AcoDemaisCatProcessor(logger_callback=self._log_mensagem_thread_safe)
        
        self._criar_interface()

    def _criar_interface(self):
        """Cria e organiza todos os componentes visuais da tela."""
        main_layout = QVBoxLayout(self)
        
        # --- Frame Principal para Arquivos (Seleção e Lista) ---
        files_main_frame = QFrame()
        files_main_frame.setObjectName("container")
        files_main_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        files_layout = QVBoxLayout(files_main_frame)
        
        self.btn_adicionar = StyledButton("➕ Adicionar Arquivo Excel", variant="success")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.frame_lista_arquivos = QWidget()
        self.lista_layout = QVBoxLayout(self.frame_lista_arquivos)
        self.lista_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.frame_lista_arquivos)

        files_layout.addWidget(self.btn_adicionar)
        files_layout.addWidget(QLabel("<b>Arquivos Adicionados:</b>"))
        files_layout.addWidget(scroll_area)

        # --- Frame para Configurações de Saída ---
        output_frame = QFrame()
        output_frame.setObjectName("container")
        output_frame.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; }")
        output_layout = QVBoxLayout(output_frame)

        self.lbl_pasta_destino = QLabel(f"<b>Pasta de Destino:</b> {self.pasta_destino_saida}")
        self.lbl_pasta_destino.setWordWrap(True)
        btn_selecionar_pasta = StyledButton("Selecionar Outra Pasta", variant="primary")
        self.var_gerar_analise = QCheckBox("Gerar arquivo de análise consolidada")
        self.var_gerar_analise.setChecked(True)

        output_layout.addWidget(QLabel("<b>Configurações de Saída</b>"))
        output_layout.addWidget(self.lbl_pasta_destino)
        output_layout.addWidget(btn_selecionar_pasta)
        output_layout.addWidget(self.var_gerar_analise)
        
        # --- Botão de Processamento e Log ---
        self.btn_processar = StyledButton("⚙️ Iniciar Processamento", variant="processing")
        self.caixa_log = QTextEdit()
        self.caixa_log.setReadOnly(True)

        main_layout.addWidget(files_main_frame)
        main_layout.addWidget(output_frame)
        main_layout.addWidget(self.btn_processar)
        main_layout.addWidget(QLabel("<b>Log de Processamento:</b>"))
        main_layout.addWidget(self.caixa_log)

        # --- Conexões ---
        self.btn_adicionar.clicked.connect(self._adicionar_arquivo)
        btn_selecionar_pasta.clicked.connect(self._selecionar_pasta_destino)
        self.btn_processar.clicked.connect(self._iniciar_processamento_threaded)

    @Slot()
    def _adicionar_arquivo(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo Excel", "", "Arquivos Excel (*.xlsx *.xls)")
        if not arquivo: return

        nome_amigavel = os.path.basename(arquivo)
        if any(item['caminho'] == arquivo for item in self.arquivos_selecionados):
            self._log_mensagem_thread_safe(f"⚠️ Aviso: Arquivo '{nome_amigavel}' já foi adicionado."); return
        
        arquivo_info = {
            'caminho': arquivo, 'origem_manual': nome_amigavel,
            'limite_horas': self.processor.LIMITE_PADRAO_HORAS, 'nome_amigavel': nome_amigavel,
            'status_validacao': 'Pendente'
        }
        self.arquivos_selecionados.append(arquivo_info)
        
        index = len(self.arquivos_selecionados) - 1
        threading.Thread(target=self._validar_arquivo_background, args=(index,), daemon=True).start()
        
        self._atualizar_lista_arquivos_gui()
        self._log_mensagem_thread_safe(f"📁 Arquivo adicionado: {nome_amigavel}")

    def _validar_arquivo_background(self, index):
        try:
            arquivo_info = self.arquivos_selecionados[index]
            resultado = self.processor.validar_e_padronizar_arquivo(arquivo_info['caminho'])
            if resultado['status'] == 'sucesso':
                arquivo_info['status_validacao'] = 'Válido ✅'
            else:
                arquivo_info['status_validacao'] = 'Erro ❌'
                self.signals.log_message.emit(f"❌ Erro de validação em '{arquivo_info['nome_amigavel']}': {resultado.get('mensagem')}")
        except Exception as e:
            arquivo_info['status_validacao'] = 'Erro ❌'
            self.signals.log_message.emit(f"🚨 Erro inesperado na validação de '{arquivo_info['nome_amigavel']}': {e}")
        finally:
            self.signals.validation_finished.emit(index)

    @Slot(int)
    def _on_validation_finished(self, index):
        self._atualizar_lista_arquivos_gui()

    @Slot(int)
    def _remover_arquivo(self, index):
        if 0 <= index < len(self.arquivos_selecionados):
            nome_removido = self.arquivos_selecionados[index]['nome_amigavel']
            del self.arquivos_selecionados[index]
            self._log_mensagem_thread_safe(f"🗑️ Arquivo removido: {nome_removido}")
            self._atualizar_lista_arquivos_gui()

    @Slot()
    def _atualizar_entry(self, index, entry_type):
        sender = self.sender()
        new_value = sender.text().strip()
        try:
            if entry_type == 'limite_horas':
                default_value = self.processor.LIMITE_PADRAO_HORAS
                value = int(new_value) if new_value else default_value
                if value < 0: raise ValueError("Limite não pode ser negativo.")
                self.arquivos_selecionados[index][entry_type] = value
                sender.setText(str(value))
            else: # origem_manual
                if not new_value: new_value = self.arquivos_selecionados[index]['nome_amigavel']
                self.arquivos_selecionados[index][entry_type] = new_value
                sender.setText(new_value)
        except (ValueError, IndexError) as e:
            QMessageBox.critical(self, "Entrada Inválida", str(e))
            sender.setText(str(self.arquivos_selecionados[index][entry_type]))
    
    def _atualizar_lista_arquivos_gui(self):
        while self.lista_layout.count():
            item = self.lista_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        if not self.arquivos_selecionados:
            self.lista_layout.addWidget(QLabel("Nenhum arquivo selecionado."))
            return

        for i, info in enumerate(self.arquivos_selecionados):
            item_frame = QFrame()
            item_frame.setStyleSheet("QFrame { border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f9f9f9; }")
            item_layout = QHBoxLayout(item_frame)

            item_layout.addWidget(QLabel("Origem:"))
            entry_origem = QLineEdit(info['origem_manual'])
            entry_origem.editingFinished.connect(lambda idx=i: self._atualizar_entry(idx, 'origem_manual'))
            item_layout.addWidget(entry_origem, 1) # O '1' faz este widget expandir
            
            item_layout.addWidget(QLabel("Limite (h):"))
            entry_limite = QLineEdit(str(info['limite_horas']))
            entry_limite.setValidator(QIntValidator())
            entry_limite.setFixedWidth(60)
            entry_limite.editingFinished.connect(lambda idx=i: self._atualizar_entry(idx, 'limite_horas'))
            item_layout.addWidget(entry_limite)
            
            status_color = "green" if "✅" in info['status_validacao'] else "red" if "❌" in info['status_validacao'] else "orange"
            lbl_status = QLabel(f"<font color='{status_color}'>{info['status_validacao']}</font>")
            item_layout.addWidget(lbl_status)
            
            btn_remover = StyledButton("🗑️", variant="danger")
            btn_remover.setFixedSize(40, 30)
            btn_remover.clicked.connect(lambda checked=False, idx=i: self._remover_arquivo(idx))
            item_layout.addWidget(btn_remover)
            
            self.lista_layout.addWidget(item_frame)

    @Slot()
    def _selecionar_pasta_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione a pasta de saída", self.pasta_destino_saida)
        if pasta:
            self.pasta_destino_saida = pasta
            self.lbl_pasta_destino.setText(f"<b>Pasta de Destino:</b> {self.pasta_destino_saida}")
            os.makedirs(self.pasta_destino_saida, exist_ok=True)

    @Slot()
    def _iniciar_processamento_threaded(self):
        if not self.arquivos_selecionados:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um arquivo."); return
        if any("Pendente" in a['status_validacao'] or "Erro" in a['status_validacao'] for a in self.arquivos_selecionados):
            QMessageBox.critical(self, "Validação Incompleta", "Existem arquivos com erro ou pendentes de validação."); return

        self.btn_processar.setEnabled(False)
        self.btn_processar.setText("Processando...")
        self._limpar_log_gui()
        self._log_mensagem_thread_safe("Iniciando processamento...")
        threading.Thread(target=self._executar_processamento, daemon=True).start()

    def _executar_processamento(self):
        try:
            arquivos_para_proc = [
                {'caminho': arq['caminho'], 'limite_horas': arq['limite_horas'], 'nome_amigavel': arq['origem_manual']}
                for arq in self.arquivos_selecionados]
            resultado = self.processor.processar_arquivos(arquivos_para_proc, self.pasta_destino_saida, self.var_gerar_analise.isChecked())
            self.signals.processing_finished.emit(resultado)
        except Exception as e:
            self.signals.processing_finished.emit({"status": "erro", "mensagem": f"Ocorreu um erro inesperado: {e}"})

    @Slot(dict)
    def _pos_processamento_gui(self, resultado):
        if resultado["status"] == "sucesso":
            QMessageBox.information(self, "Sucesso", resultado["mensagem"])
            reply = QMessageBox.question(self, "Abrir Pasta", "Deseja abrir a pasta com os arquivos gerados?")
            if reply == QMessageBox.StandardButton.Yes:
                if sys.platform == "win32":
                    os.startfile(self.pasta_destino_saida)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, self.pasta_destino_saida])
        else:
            QMessageBox.critical(self, "Erro", resultado.get("mensagem", "Erro desconhecido."))
        
        self.btn_processar.setEnabled(True)
        self.btn_processar.setText("⚙️ Iniciar Processamento")

    def _log_mensagem_thread_safe(self, mensagem):
        self.signals.log_message.emit(mensagem)

    @Slot(str)
    def _append_log_message(self, mensagem):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.caixa_log.append(f"[{timestamp}] {mensagem}")

    def _limpar_log_gui(self):
        self.caixa_log.clear()
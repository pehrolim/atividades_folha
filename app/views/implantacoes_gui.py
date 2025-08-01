# atividades_folha/app/views/implantacoes_gui.py
import os
import sys
import threading
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
                               QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QCheckBox,
                               QHeaderView, QFileDialog, QMessageBox)
from PySide6.QtCore import Slot, Signal, QObject, Qt # <-- Importação do Qt

# Importa a classe de lógica e widgets padronizados
from app.logic.implantacoes_processor import ImplantacoesProcessor
from app.widgets.styled_widgets import StyledButton

try:
    import pandas as pd
except ImportError:
    print("AVISO: A biblioteca 'pandas' não está instalada. Execute: pip install pandas openpyxl")

try:
    import pyperclip
except ImportError:
    print("AVISO: A biblioteca 'pyperclip' não está instalada. Execute: pip install pyperclip")

class ImplantacoesGUI(QWidget):
    def __init__(self, master=None):
        super().__init__(master)
        self.colunas_arquivo = ['Operacao', 'Matricula', 'Codigo', 'Valor', 'Referencia', 'Prazo', 'Observacao']
        self.colunas_tabela = self.colunas_arquivo + ['Data']
        self.item_selecionado_para_edicao_row = -1
        self.indice_implantacao_atual = 0
        self.em_modo_implantacao = False # <-- Variável de estado para o atalho

        self.processor = ImplantacoesProcessor()
        self._criar_interface()

    # --- INÍCIO DA ALTERAÇÃO: Captura de Teclas ---
    def keyPressEvent(self, event):
        """ Sobrescreve o evento de pressionar tecla para capturar o SHIFT. """
        # Verifica se estamos em modo de implantação e se a tecla SHIFT foi pressionada
        if self.em_modo_implantacao and event.key() == Qt.Key.Key_Shift:
            self._processar_proxima_linha()
            event.accept() # Indica que o evento foi tratado
        else:
            super().keyPressEvent(event) # Passa o evento para o comportamento padrão
    # --- FIM DA ALTERAÇÃO ---

    def _criar_interface(self):
        main_layout = QVBoxLayout(self)

        # Frame de Dados de Entrada
        frame_entradas = QFrame()
        frame_entradas.setObjectName("container")
        frame_entradas.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; padding: 10px; }")
        layout_entradas = QVBoxLayout(frame_entradas)
        layout_entradas.addWidget(QLabel("<b>Dados de Entrada</b>"))

        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(1, 1)

        campos = ["Operacao", "Matricula", "Codigo", "Valor", "Referencia", "Prazo", "Observacao"]
        self.entries = {}
        self.keep_checks = {}

        label_info_keep = QLabel("Manter:")
        label_info_keep.setStyleSheet("font-size: 8pt; color: gray;")
        grid_layout.addWidget(label_info_keep, 0, 2)

        for idx, campo in enumerate(campos):
            label = QLabel(f"{campo}:")
            entry = QLineEdit()
            check = QCheckBox()
            self.keep_checks[campo.lower()] = check
            
            grid_layout.addWidget(label, idx + 1, 0)
            grid_layout.addWidget(entry, idx + 1, 1)
            grid_layout.addWidget(check, idx + 1, 2)
            self.entries[campo.lower()] = entry
        
        layout_entradas.addLayout(grid_layout)

        frame_botoes_entrada = QHBoxLayout()
        self.btn_adicionar = StyledButton("Adicionar", variant="success")
        self.btn_importar = StyledButton("Importar Arquivo", variant="primary")
        self.btn_salvar = StyledButton("Salvar Alterações", variant="primary")
        self.btn_cancelar = StyledButton("Cancelar", variant="danger")
        frame_botoes_entrada.addStretch()
        frame_botoes_entrada.addWidget(self.btn_adicionar)
        frame_botoes_entrada.addWidget(self.btn_importar)
        frame_botoes_entrada.addWidget(self.btn_salvar)
        frame_botoes_entrada.addWidget(self.btn_cancelar)
        layout_entradas.addLayout(frame_botoes_entrada)
        
        # Frame da Tabela e Ações
        frame_tabela = QFrame()
        layout_tabela = QVBoxLayout(frame_tabela)
        layout_tabela.addWidget(QLabel("<b>Implantações (Dê um duplo-clique em um item para editar)</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.colunas_tabela))
        self.table.setHorizontalHeaderLabels(self.colunas_tabela)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout_tabela.addWidget(self.table)
        
        frame_copia = QFrame()
        layout_copia = QVBoxLayout(frame_copia)
        layout_copia.addWidget(QLabel("<b>Texto Copiado Automaticamente</b>"))
        self.text_para_copiar = QTextEdit()
        self.text_para_copiar.setReadOnly(True)
        self.text_para_copiar.setFixedHeight(100)
        self.text_para_copiar.setStyleSheet("font-family: Courier; font-size: 9pt;")
        layout_copia.addWidget(self.text_para_copiar)

        frame_acoes_tabela = QHBoxLayout()
        self.btn_implantar = StyledButton("▶ Iniciar Implantação", variant="primary")
        self.btn_parar_implantar = StyledButton("Parar Implantação", variant="danger")
        self.btn_exportar = StyledButton("Exportar para Excel", variant="primary")
        self.btn_limpar = StyledButton("Limpar Dados", variant="danger")
        
        frame_acoes_tabela.addWidget(self.btn_limpar)
        frame_acoes_tabela.addStretch()
        frame_acoes_tabela.addWidget(self.btn_exportar)
        frame_acoes_tabela.addWidget(self.btn_implantar)
        frame_acoes_tabela.addWidget(self.btn_parar_implantar)
        
        self.status_label = QLabel("Pronto.")
        
        main_layout.addWidget(frame_entradas)
        main_layout.addWidget(frame_tabela, 1)
        main_layout.addWidget(frame_copia)
        main_layout.addLayout(frame_acoes_tabela)
        main_layout.addWidget(self.status_label)

        self._setup_connections()
        self._alternar_modo_edicao(editar=False)
        self._gerenciar_estado_controles(implantando=False)

    def _setup_connections(self):
        self.btn_adicionar.clicked.connect(self._adicionar_implantacao)
        self.btn_importar.clicked.connect(self._importar_arquivo)
        self.btn_salvar.clicked.connect(self._salvar_edicao)
        self.btn_cancelar.clicked.connect(self._cancelar_edicao)
        self.table.cellDoubleClicked.connect(self._iniciar_edicao_item)
        self.btn_implantar.clicked.connect(self._implantar_dados)
        self.btn_parar_implantar.clicked.connect(self._finalizar_processo_implantacao)
        self.btn_exportar.clicked.connect(self._exportar_para_excel)
        self.btn_limpar.clicked.connect(self._limpar_tabela)
    
    @Slot()
    def _adicionar_implantacao(self):
        dados = [self.entries[c].text() for c in ['operacao', 'matricula', 'codigo', 'valor', 'referencia', 'prazo', 'observacao']]
        if not all([dados[0], dados[1], dados[2], dados[6]]):
            QMessageBox.critical(self, "Erro de Validação", "Os campos 'Operacao', 'Matricula', 'Codigo' e 'Observacao' são obrigatórios.")
            return

        try:
            valor_float = float(dados[3].replace(',', '.')) if dados[3] else 0.0
            dados[3] = f"{valor_float:.2f}".replace('.', ',')
        except (ValueError, TypeError):
            dados[3] = "0,00"

        dados.append(datetime.now().strftime('%d/%m/%Y'))
        
        rowCount = self.table.rowCount()
        self.table.insertRow(rowCount)
        for col, value in enumerate(dados):
            self.table.setItem(rowCount, col, QTableWidgetItem(str(value)))

        for campo, entry in self.entries.items():
            if not self.keep_checks[campo].isChecked():
                entry.clear()

        self.entries['operacao'].setFocus()

    @Slot()
    def _implantar_dados(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Implantar", "Não há dados na tabela.")
            return
        
        self.indice_implantacao_atual = 0
        self._gerenciar_estado_controles(implantando=True)
        self._processar_proxima_linha()

    def _processar_proxima_linha(self):
        if self.indice_implantacao_atual >= self.table.rowCount():
            self._finalizar_processo_implantacao()
            return

        linha_dados = [self.table.item(self.indice_implantacao_atual, col).text() for col in range(self.table.columnCount())]
        texto = self.processor.formatar_linha_para_txt(linha_dados)
        try:
            pyperclip.copy(texto)
            self.status_label.setText(f"Linha {self.indice_implantacao_atual + 1} copiada. Pressione SHIFT para a próxima.")
        except Exception as e:
            self.status_label.setText(f"Erro ao copiar para a área de transferência: {e}")

        self.table.selectRow(self.indice_implantacao_atual)
        self.text_para_copiar.setText(texto)
        self.indice_implantacao_atual += 1
    
    def _gerenciar_estado_controles(self, implantando=False):
        self.em_modo_implantacao = implantando # Atualiza o estado
        estado_normal = not implantando
        self.btn_adicionar.setEnabled(estado_normal)
        self.btn_importar.setEnabled(estado_normal)
        self.btn_limpar.setEnabled(estado_normal)
        self.btn_exportar.setEnabled(estado_normal)
        self.btn_implantar.setVisible(estado_normal)
        self.table.setDisabled(implantando)
        
        self.btn_parar_implantar.setVisible(implantando)
        
        if implantando:
            self.status_label.setText("Modo de implantação ativo. Pressione SHIFT para copiar a próxima linha.")
            self.setFocus() # Garante que o widget receba eventos de teclado
        else:
            self.status_label.setText("Pronto.")

    def _finalizar_processo_implantacao(self):
        self.status_label.setText("Processo de implantação finalizado.")
        self.text_para_copiar.clear()
        self.table.clearSelection()
        self._gerenciar_estado_controles(implantando=False)

    @Slot()
    def _limpar_tabela(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Limpar", "A tabela já está vazia.")
            return
        
        if QMessageBox.question(self, "Confirmar", "Deseja realmente limpar todos os dados da tabela?") == QMessageBox.StandardButton.Yes:
            self.table.setRowCount(0)
            self.text_para_copiar.clear()
            self.status_label.setText("Tabela limpa.")

    def _alternar_modo_edicao(self, editar=False):
        self.btn_adicionar.setVisible(not editar)
        self.btn_importar.setVisible(not editar)
        self.btn_salvar.setVisible(editar)
        self.btn_cancelar.setVisible(editar)
    
    # ... (Os métodos restantes como _importar_arquivo, _exportar_para_excel, _salvar_edicao, etc. permanecem os mesmos) ...

    @Slot()
    def _importar_arquivo(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo", "", "Ficheiros Excel (*.xlsx *.xls)")
        if not filepath: return
        try:
            df = pd.read_excel(filepath, dtype=str)
            df.columns = [str(col).lower() for col in df.columns]
            colunas_esperadas_lower = [col.lower() for col in self.colunas_arquivo]
            colunas_faltando = [col for col in colunas_esperadas_lower if col not in df.columns]
            if colunas_faltando:
                mapa_lower_original = {col.lower(): col for col in self.colunas_arquivo}
                nomes_originais_faltando = [mapa_lower_original[col] for col in colunas_faltando]
                QMessageBox.critical(self, "Erro de Colunas", f"O arquivo não contém as seguintes colunas obrigatórias: {', '.join(nomes_originais_faltando)}")
                return
            mapa_renomear = {col.lower(): col for col in self.colunas_arquivo}
            df = df.rename(columns=mapa_renomear)
            df = df[self.colunas_arquivo]
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')
            df.fillna({'Valor': 0.0, 'Operacao': '', 'Matricula': '', 'Codigo': '', 'Referencia': '', 'Prazo': '', 'Observacao': ''}, inplace=True)
            if self.table.rowCount() > 0:
                resposta = QMessageBox.question(self, "Confirmar Importação",
                    "A tabela já contém dados. Deseja limpá-la antes de importar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
                if resposta == QMessageBox.StandardButton.Cancel: return
                if resposta == QMessageBox.StandardButton.Yes: self.table.setRowCount(0)
            for _, row in df.iterrows():
                row['Valor'] = f"{row['Valor']:.2f}".replace('.', ',')
                linha = row.tolist() + [datetime.now().strftime('%d/%m/%Y')]
                rowCount = self.table.rowCount()
                self.table.insertRow(rowCount)
                for col, value in enumerate(linha):
                    self.table.setItem(rowCount, col, QTableWidgetItem(str(value)))
            QMessageBox.information(self, "Importado", f"{self.table.rowCount()} linhas importadas com sucesso.")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Importar", f"Ocorreu um erro inesperado: {str(e)}")

    @Slot()
    def _exportar_para_excel(self):
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Exportar", "Não há dados para exportar.")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Salvar como", "", "Ficheiros Excel (*.xlsx);;Todos os ficheiros (*.*)")
        if not filepath: return
        try:
            dados = []
            for row in range(self.table.rowCount()):
                linha = [self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(self.table.columnCount())]
                dados.append(linha)
            df = pd.DataFrame(dados, columns=self.colunas_tabela)
            df['Valor'] = df['Valor'].str.replace(',', '.', regex=False)
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0.0)
            df.to_excel(filepath, index=False)
            QMessageBox.information(self, "Sucesso", f"Dados exportados com sucesso para {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Exportar", str(e))

    @Slot(int, int)
    def _iniciar_edicao_item(self, row, column):
        self.item_selecionado_para_edicao_row = row
        for i, campo in enumerate(['operacao', 'matricula', 'codigo', 'valor', 'referencia', 'prazo', 'observacao']):
            self.entries[campo].setText(self.table.item(row, i).text())
        self._alternar_modo_edicao(editar=True)

    @Slot()
    def _salvar_edicao(self):
        if self.item_selecionado_para_edicao_row < 0: return
        dados = [self.entries[c].text() for c in ['operacao', 'matricula', 'codigo', 'valor', 'referencia', 'prazo', 'observacao']]
        if not all([dados[0], dados[1], dados[2], dados[6]]):
            QMessageBox.critical(self, "Erro", "Os campos 'Operacao', 'Matricula', 'Codigo' e 'Observacao' são obrigatórios.")
            return
        try:
            valor_float = float(dados[3].replace(',', '.')) if dados[3] else 0.0
            dados[3] = f"{valor_float:.2f}".replace('.', ',')
        except (ValueError, TypeError):
            dados[3] = "0,00"
        data_original = self.table.item(self.item_selecionado_para_edicao_row, 7).text()
        dados.append(data_original)
        for col, value in enumerate(dados):
            self.table.setItem(self.item_selecionado_para_edicao_row, col, QTableWidgetItem(str(value)))
        self._cancelar_edicao()
        self.status_label.setText("Item atualizado com sucesso.")

    @Slot()
    def _cancelar_edicao(self):
        self.item_selecionado_para_edicao_row = -1
        for entry in self.entries.values(): entry.clear()
        for check in self.keep_checks.values(): check.setChecked(False)
        self._alternar_modo_edicao(editar=False)
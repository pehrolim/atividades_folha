# app/views/calc_aco_gui.py
import os
import datetime
import threading
import pandas as pd
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel, 
                               QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox)
from PySide6.QtCore import Slot, Signal, QObject
from PySide6.QtGui import QFont

from app.logic.calc_aco_processor import CalcAcoProcessor
from app.widgets.styled_widgets import StyledButton

class WorkerSignals(QObject):
    import_finished = Signal(dict)

class CalcAcoGUI(QWidget):
    def __init__(self, master=None):
        super().__init__(master)

        self.processor = CalcAcoProcessor()
        self.colunas_tabela = ['Matrícula', 'CLF', 'Código', 'Referencia (Horas)', 'H. Normal',
                               'Tarifa Normal', 'H. Majorada', 'Tarifa Majorada', 'Valor Total', 'Observação']
        self.dados_para_exibicao = []
        self.valores_calculados = None

        self.signals = WorkerSignals()
        self.signals.import_finished.connect(self._finalizar_importacao)

        self._criar_interface()

    def _criar_interface(self):
        main_layout = QHBoxLayout(self)

        # --- Frame Esquerdo (Entradas e Tabela) ---
        frame_esquerdo = QFrame()
        layout_esquerdo = QVBoxLayout(frame_esquerdo)
        
        frame_entradas = QFrame()
        frame_entradas.setObjectName("container")
        frame_entradas.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; padding: 10px; }")
        layout_entradas = QGridLayout(frame_entradas)
        
        self.entry_matricula = QLineEdit()
        self.entry_clf = QLineEdit()
        self.entry_codigo = QLineEdit()
        self.entry_referencia = QLineEdit()
        self.entry_observacao = QLineEdit()

        layout_entradas.addWidget(QLabel("<b>1. Preencha os Dados</b>"), 0, 0, 1, 2)
        layout_entradas.addWidget(QLabel("Matrícula:"), 1, 0)
        layout_entradas.addWidget(self.entry_matricula, 1, 1)
        layout_entradas.addWidget(QLabel("CLF:"), 2, 0)
        layout_entradas.addWidget(self.entry_clf, 2, 1)
        layout_entradas.addWidget(QLabel("Código:"), 3, 0)
        layout_entradas.addWidget(self.entry_codigo, 3, 1)
        layout_entradas.addWidget(QLabel("Referencia (Horas):"), 4, 0)
        layout_entradas.addWidget(self.entry_referencia, 4, 1)
        layout_entradas.addWidget(QLabel("Observação:"), 5, 0)
        layout_entradas.addWidget(self.entry_observacao, 5, 1)
        layout_entradas.setColumnStretch(1, 1)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.colunas_tabela))
        self.table.setHorizontalHeaderLabels(self.colunas_tabela)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        acoes_layout = QHBoxLayout()
        btn_importar = StyledButton("Importar", "primary")
        btn_exportar = StyledButton("Exportar", "primary")
        btn_limpar = StyledButton("Limpar", "danger")
        acoes_layout.addWidget(btn_importar)
        acoes_layout.addWidget(btn_exportar)
        acoes_layout.addWidget(btn_limpar)
        acoes_layout.addStretch()

        layout_esquerdo.addWidget(frame_entradas)
        layout_esquerdo.addWidget(self.table, 1)
        layout_esquerdo.addLayout(acoes_layout)

        # --- Frame Direito (Cálculo) ---
        frame_direito = QFrame()
        layout_direito = QVBoxLayout(frame_direito)

        frame_calc = QFrame()
        frame_calc.setObjectName("container")
        frame_calc.setStyleSheet("#container { border: 1px solid #dcdcdc; border-radius: 5px; padding: 10px; }")
        layout_calc = QVBoxLayout(frame_calc)
        
        bold_font = QFont(); bold_font.setBold(True)
        valor_font = QFont(); valor_font.setBold(True); valor_font.setPointSize(16)
        total_font = QFont(); total_font.setBold(True); total_font.setPointSize(28)
        
        self.lbl_status_busca = QLabel("Aguardando CLF...")
        self.lbl_tarifa_normal = QLabel("R$ 0,00"); self.lbl_tarifa_normal.setFont(valor_font)
        self.lbl_tarifa_majorada = QLabel("R$ 0,00"); self.lbl_tarifa_majorada.setFont(valor_font)
        self.lbl_hn = QLabel("0.0"); self.lbl_hn.setFont(valor_font)
        self.lbl_hm = QLabel("0.0"); self.lbl_hm.setFont(valor_font)
        self.lbl_vt = QLabel("R$ 0,00"); self.lbl_vt.setFont(total_font); self.lbl_vt.setStyleSheet("color: #2ECC71;")
        
        layout_calc.addWidget(QLabel("<b>2. Demonstrativo do Cálculo</b>"))
        layout_calc.addWidget(self.lbl_status_busca)
        layout_calc.addSpacing(10)
        layout_calc.addWidget(QLabel("Tarifa Normal:"))
        layout_calc.addWidget(self.lbl_tarifa_normal)
        layout_calc.addSpacing(10)
        layout_calc.addWidget(QLabel("Tarifa Majorada:"))
        layout_calc.addWidget(self.lbl_tarifa_majorada)
        layout_calc.addSpacing(10)
        layout_calc.addWidget(QLabel("Horas Normais:"))
        layout_calc.addWidget(self.lbl_hn)
        layout_calc.addSpacing(10)
        layout_calc.addWidget(QLabel("Horas Majoradas:"))
        layout_calc.addWidget(self.lbl_hm)
        layout_calc.addSpacing(15)
        layout_calc.addWidget(QLabel("<b>VALOR TOTAL CALCULADO</b>"))
        layout_calc.addWidget(self.lbl_vt)
        
        btn_adicionar = StyledButton("⬇️ Adicionar à Tabela", "success")
        
        layout_direito.addWidget(frame_calc)
        layout_direito.addWidget(btn_adicionar)
        layout_direito.addStretch()

        main_layout.addWidget(frame_esquerdo, 2) # 2/3 do espaço
        main_layout.addWidget(frame_direito, 1) # 1/3 do espaço

        # --- Conexões ---
        self.entry_clf.editingFinished.connect(self._buscar_tarifas_e_calcular)
        self.entry_codigo.editingFinished.connect(self._buscar_tarifas_e_calcular)
        self.entry_referencia.editingFinished.connect(self._calcular_valores)
        btn_adicionar.clicked.connect(self._adicionar_item)
        btn_importar.clicked.connect(self._iniciar_importacao_threaded)
        btn_exportar.clicked.connect(self._exportar_excel)
        btn_limpar.clicked.connect(self._limpar_tabela)

    def _limpar_resultados(self):
        self.valores_calculados = None
        self.lbl_tarifa_normal.setText("R$ 0,00")
        self.lbl_tarifa_majorada.setText("R$ 0,00")
        self.lbl_status_busca.setText("Aguardando CLF...")
        self.lbl_hn.setText("0.0")
        self.lbl_hm.setText("0.0")
        self.lbl_vt.setText("R$ 0,00")

    @Slot()
    def _buscar_tarifas_e_calcular(self):
        self._limpar_resultados()
        clf = self.entry_clf.text()
        codigo = self.entry_codigo.text()
        if not clf:
            return

        resultado = self.processor.buscar_tarifas(clf, codigo)
        if resultado['status'] == 'sucesso':
            self.lbl_tarifa_normal.setText(f"R$ {resultado['tarifa_normal']:.2f}")
            self.lbl_tarifa_majorada.setText(f"R$ {resultado['tarifa_majorada']:.2f}")
            self.lbl_status_busca.setText("Tarifas encontradas.")
            # Se já houver referência, calcula os valores
            if self.entry_referencia.text():
                self._calcular_valores()
        else:
            self.lbl_status_busca.setText(f"<font color='red'>{resultado['mensagem']}</font>")

    @Slot()
    def _calcular_valores(self):
        clf = self.entry_clf.text()
        codigo = self.entry_codigo.text()
        referencia_horas = self.entry_referencia.text()

        if not all([clf, referencia_horas]):
            if referencia_horas: QMessageBox.warning(self, "Dados Faltando", "Preencha o 'CLF'.")
            return
        
        try:
            resultado = self.processor.calcular_tudo(clf, referencia_horas, codigo)
            if resultado['status'] == 'sucesso':
                self.valores_calculados = resultado
                self.lbl_hn.setText(f"{resultado['h_normal']:.1f}")
                self.lbl_hm.setText(f"{resultado['h_majorada']:.1f}")
                self.lbl_vt.setText(f"R$ {resultado['valor_total']:.2f}")
                self.lbl_tarifa_normal.setText(f"R$ {resultado['tarifa_normal']:.2f}")
                self.lbl_tarifa_majorada.setText(f"R$ {resultado['tarifa_majorada']:.2f}")
                self.lbl_status_busca.setText("<font color='green'>Cálculo realizado com sucesso!</font>")
            else:
                QMessageBox.critical(self, "Erro no Cálculo", resultado['mensagem'])
                self.lbl_status_busca.setText(f"<font color='red'>{resultado['mensagem']}</font>")
        except Exception as e:
            QMessageBox.critical(self, "Erro Inesperado", str(e))

    @Slot()
    def _adicionar_item(self):
        if not self.valores_calculados:
            QMessageBox.warning(self, "Ação Inválida", "Calcule os valores antes de adicionar.")
            return
        if not self.entry_matricula.text():
            QMessageBox.warning(self, "Matrícula Faltando", "Informe a Matrícula.")
            return

        nova_linha = {
            'Matrícula': self.entry_matricula.text(), 'CLF': self.entry_clf.text(),
            'Código': self.entry_codigo.text(), 'Referencia (Horas)': self.entry_referencia.text(),
            'H. Normal': self.valores_calculados['h_normal'], 
            'Tarifa Normal': f"R$ {self.valores_calculados['tarifa_normal']:.2f}",
            'H. Majorada': self.valores_calculados['h_majorada'], 
            'Tarifa Majorada': f"R$ {self.valores_calculados['tarifa_majorada']:.2f}",
            'Valor Total': f"R$ {self.valores_calculados['valor_total']:.2f}", 
            'Observação': self.entry_observacao.text()
        }
        self.dados_para_exibicao.append(nova_linha)
        self._atualizar_tabela()
        self._limpar_campos_de_entrada()

    def _limpar_campos_de_entrada(self):
        self.entry_matricula.clear()
        self.entry_clf.clear()
        self.entry_codigo.clear()
        self.entry_referencia.clear()
        self.entry_observacao.clear()
        self._limpar_resultados()
        self.entry_matricula.setFocus()
    
    @Slot()
    def _iniciar_importacao_threaded(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Importar Arquivo", "", "Arquivos Excel (*.xlsx)")
        if not caminho: return
        threading.Thread(target=self._executar_importacao, args=(caminho,), daemon=True).start()

    def _executar_importacao(self, caminho_arquivo):
        resultado = self.processor.processar_arquivo_importado(caminho_arquivo)
        self.signals.import_finished.emit(resultado)

    @Slot(dict)
    def _finalizar_importacao(self, resultado):
        if resultado['status'] == 'sucesso':
            self.dados_para_exibicao.extend(resultado['dados'])
            self._atualizar_tabela()
            sucesso_msg = f"{len(resultado['dados'])} linhas importadas."
            if resultado['erros']:
                erros_msg = "\n\nOcorreram erros:\n" + "\n".join(resultado['erros'])
                QMessageBox.warning(self, "Importação Parcial", sucesso_msg + erros_msg)
            else:
                QMessageBox.information(self, "Importação Concluída", sucesso_msg)
        else:
            QMessageBox.critical(self, "Erro na Importação", resultado['mensagem'])
        
    def _atualizar_tabela(self):
        self.table.setRowCount(len(self.dados_para_exibicao))
        for i, item in enumerate(self.dados_para_exibicao):
            for j, col_name in enumerate(self.colunas_tabela):
                self.table.setItem(i, j, QTableWidgetItem(str(item.get(col_name, ""))))

    @Slot()
    def _exportar_excel(self):
        if not self.dados_para_exibicao:
            QMessageBox.warning(self, "Aviso", "Não há dados para exportar.")
            return
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar para Excel", "", "Arquivos Excel (*.xlsx)")
        if caminho:
            df = pd.DataFrame(self.dados_para_exibicao)
            df.to_excel(caminho, index=False)
            QMessageBox.information(self, "Sucesso", f"Dados exportados com sucesso para:\n{caminho}")

    @Slot()
    def _limpar_tabela(self):
        if not self.dados_para_exibicao: return
        reply = QMessageBox.question(self, "Confirmar", "Limpar todos os dados da tabela?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.dados_para_exibicao.clear()
            self._atualizar_tabela()
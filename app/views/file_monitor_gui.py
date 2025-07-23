import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import threading
import sys
import pandas as pd

# Importa as classes da camada logic e os nossos widgets padrão
from app.logic.data_manager import DataManager
from app.logic.file_monitor import FileMonitor
from app.widgets.custom_button import StandardButton
from app.widgets.custom_labels import TitleLabel, InfoLabel, ValueLabel
from app.widgets.custom_frames import StandardFrame, TransparentFrame

class FileMonitorGUI(ctk.CTkFrame):
    """
    View para o monitoramento de arquivos, construída com CustomTkinter
    e utilizando componentes padronizados.
    """

    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")

        # --- Lógica de negócio (permanece a mesma) ---
        self.pasta_origem_monitoramento = os.path.expanduser("~/Downloads")
        self.pasta_destino_processados = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../data/processados'))
        self.colunas_folha = ['MATRICULA', 'NOME', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO',
                              'ORGAO', 'CLF', 'SIMBOLO', 'SITUACAO', 'SAIDA', 'DATA_AFAST', 'GRUPO', 'REGIME']
        self.data_manager = DataManager(self.colunas_folha)
        self.file_monitor = FileMonitor(
            data_manager=self.data_manager,
            logger_callback=self._log_mensagem,
            arquivo_processado_callback=self._atualizar_info_dados
        )

        # --- Configuração do Layout e Inicialização ---
        # --- ALTERAÇÃO AQUI ---
        # Adicionado para que a própria view se posicione.
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self._criar_interface()
        self._atualizar_info_dados()

    def _criar_interface(self):
        # Frame para as configurações de pastas, agora usando StandardFrame
        folders_frame = StandardFrame(self)
        folders_frame.pack(pady=10, padx=10, fill="x")

        InfoLabel(folders_frame, text="📥 Pasta de Origem (onde o .txt aparece):").pack(pady=(10, 0))
        self.lbl_pasta_origem = ValueLabel(folders_frame, text=self.pasta_origem_monitoramento)
        self.lbl_pasta_origem.pack()
        StandardButton(folders_frame, text="Selecionar Pasta de Origem", variant="primary", command=self._selecionar_pasta_origem).pack(pady=5)

        InfoLabel(folders_frame, text="📤 Pasta de Destino (arquivos processados e salvos):").pack(pady=(10, 0))
        self.lbl_pasta_destino = ValueLabel(folders_frame, text=self.pasta_destino_processados)
        self.lbl_pasta_destino.pack()
        StandardButton(folders_frame, text="Selecionar Pasta de Destino", variant="primary", command=self._selecionar_pasta_destino).pack(pady=5)

        # Botão principal de monitoramento
        self.btn_alternar_monitoramento = StandardButton(
            self, text="▶ Iniciar Monitoramento", command=self._alternar_monitoramento,
            variant="success"
        )
        self.btn_alternar_monitoramento.pack(pady=15, ipady=5)

        # Frame de informações e ações, agora usando StandardFrame
        info_actions_frame = StandardFrame(self)
        info_actions_frame.pack(pady=10, padx=10, fill="x")

        self.lbl_info_dados = TitleLabel(info_actions_frame, text="Dados Acumulados: 0 registros", font=("Roboto", 12, "bold"))
        self.lbl_info_dados.pack(pady=(5, 10))

        # Usa TransparentFrame para agrupar os botões sem um fundo visível
        frame_botoes = TransparentFrame(info_actions_frame)
        frame_botoes.pack(pady=5)
        StandardButton(frame_botoes, text="💾 Salvar CSV", variant="primary", command=self._salvar_csv).pack(side="left", padx=5)
        StandardButton(frame_botoes, text="💾 Salvar XLSX", variant="primary", command=self._salvar_xlsx).pack(side="left", padx=5)
        StandardButton(frame_botoes, text="🧹 Limpar Dados", variant="danger", command=self._limpar_dados).pack(side="left", padx=5)

        # Log de eventos
        TitleLabel(self, text="Log de Eventos:", anchor='w').pack(fill="x", padx=10, pady=(10, 0))
        self.caixa_log = ctk.CTkTextbox(self, height=150, state='disabled', wrap='word')
        self.caixa_log.pack(fill="both", expand=True, padx=10, pady=5)

    def cleanup(self):
        if self.file_monitor.obter_status_monitoramento():
            self._log_mensagem("Aplicação fechando: Parando monitoramento...")
            self.file_monitor.parar_monitoramento()

    def _selecionar_pasta_origem(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_origem_monitoramento)
        if pasta:
            self.pasta_origem_monitoramento = pasta
            self.lbl_pasta_origem.configure(text=pasta)
            self._log_mensagem(f"Pasta de origem selecionada: {pasta}")

    def _selecionar_pasta_destino(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_destino_processados)
        if pasta:
            self.pasta_destino_processados = pasta
            self.lbl_pasta_destino.configure(text=pasta)
            self._log_mensagem(f"Pasta de destino selecionada: {pasta}")

    # --- MÉTODO ATUALIZADO ---
    def _alternar_monitoramento(self):
        if self.file_monitor.obter_status_monitoramento():
            if self.file_monitor.parar_monitoramento():
                # Restaura a aparência do botão para "Iniciar" (estilo 'success')
                self.btn_alternar_monitoramento.configure(text="▶ Iniciar Monitoramento")
                self.btn_alternar_monitoramento.configure_variant("success")
        else:
            if self.file_monitor.iniciar_monitoramento(self.pasta_origem_monitoramento, self.pasta_destino_processados):
                # Altera a aparência do botão para "Parar" (estilo 'danger')
                self.btn_alternar_monitoramento.configure(text="⏹ Parar Monitoramento")
                self.btn_alternar_monitoramento.configure_variant("danger")

    def _salvar_csv(self):
        if self.data_manager.esta_vazio(): messagebox.showwarning("Aviso", "Não há dados para salvar."); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")],
                                            initialdir=self.pasta_destino_processados, title="Salvar CSV")
        if path:
            try:
                self.data_manager.salvar_para_csv(path)
                self._log_mensagem(f"💾 Dados salvos em CSV: {path}")
                messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{path}")
            except Exception as e:
                self._log_mensagem(f"[❌] Erro ao salvar CSV: {e}")
                messagebox.showerror("Erro", f"Erro ao salvar:\n{e}")

    def _salvar_xlsx(self):
        if self.data_manager.esta_vazio(): messagebox.showwarning("Aviso", "Não há dados para salvar."); return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Arquivos Excel", "*.xlsx")],
                                            initialdir=self.pasta_destino_processados, title="Salvar Excel")
        if path:
            try:
                self.data_manager.salvar_para_xlsx(path)
                self._log_mensagem(f"💾 Dados salvos em XLSX: {path}")
                messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{path}")
            except Exception as e:
                self._log_mensagem(f"[❌] Erro ao salvar XLSX: {e}")
                messagebox.showerror("Erro", f"Erro ao salvar:\n{e}")

    def _limpar_dados(self):
        if self.data_manager.esta_vazio(): self._log_mensagem("🧹 Dados já estão limpos."); return
        if messagebox.askyesno("Confirmação", "Deseja realmente limpar todos os dados acumulados?"):
            self.data_manager.limpar_dados()
            self._log_mensagem("🧹 Dados acumulados foram limpos.")
            self._atualizar_info_dados()

    def _log_mensagem(self, mensagem: str):
        self.caixa_log.configure(state='normal')
        self.caixa_log.insert('end', f"{datetime.now().strftime('%H:%M:%S')} - {mensagem}\n")
        self.caixa_log.see('end')
        self.caixa_log.configure(state='disabled')

    def _atualizar_info_dados(self):
        num_registros = len(self.data_manager.obter_dados_acumulados())
        self.lbl_info_dados.configure(text=f"Dados Acumulados: {num_registros} registros")
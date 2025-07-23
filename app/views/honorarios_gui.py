# app/views/honorarios_gui.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import threading

from app.logic.honorarios_processor import HonorariosProcessor
from app.widgets.custom_button import StandardButton
from app.widgets.custom_labels import TitleLabel, InfoLabel, ValueLabel
from app.widgets.custom_frames import StandardFrame


class HonorariosGUI(ctk.CTkFrame):
    """
    View para gerar relatórios de honorários a partir de um arquivo Excel.
    """

    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=10, pady=10)

        self.caminho_arquivo_excel = ctk.StringVar(value="")
        self.nome_arquivo_display = ctk.StringVar(value="Nenhum arquivo selecionado.")
        self.pasta_destino_pdf = ctk.StringVar(value=os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../data/honorarios_reports')))
        os.makedirs(self.pasta_destino_pdf.get(), exist_ok=True)

        self.honorarios_processor = HonorariosProcessor(logger_callback=self._log_mensagem)
        self._criar_interface()

    def _criar_interface(self):
        """Cria e organiza todos os widgets da interface gráfica."""
        # Frame de Configurações
        settings_frame = StandardFrame(self)
        settings_frame.pack(pady=10, padx=10, fill="x")

        TitleLabel(settings_frame, text="Configuração do Relatório de Honorários").pack(pady=10)

        InfoLabel(settings_frame, text="📊 Arquivo Excel de Honorários:").pack(pady=(10, 0))
        ValueLabel(settings_frame, textvariable=self.nome_arquivo_display, text_color=("blue", "cyan")).pack()
        StandardButton(settings_frame, text="Selecionar Arquivo Excel", command=self._selecionar_arquivo_excel).pack(
            pady=(5, 15))

        InfoLabel(settings_frame, text="📁 Pasta de Destino para o Relatório PDF:").pack(pady=(10, 0))
        ValueLabel(settings_frame, textvariable=self.pasta_destino_pdf, wraplength=800).pack()
        StandardButton(settings_frame, text="Selecionar Pasta de Destino", command=self._selecionar_pasta_destino).pack(
            pady=(5, 15))

        # Botão de Ação Principal
        self.btn_gerar_relatorio = StandardButton(self, text="📈 Gerar Relatório de Honorários",
                                                  command=self._iniciar_geracao_relatorio_threaded,
                                                  variant="processing")
        self.btn_gerar_relatorio.pack(pady=20, ipady=5)

        # Log de Eventos
        log_frame = StandardFrame(self)
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        TitleLabel(log_frame, text="Log de Processamento").pack(pady=5)
        self.caixa_log = ctk.CTkTextbox(log_frame, state='disabled', wrap='word')
        self.caixa_log.pack(fill="both", expand=True, padx=10, pady=10)

    def _selecionar_arquivo_excel(self):
        arquivo = filedialog.askopenfilename(title="Selecione o arquivo Excel de honorários",
                                             filetypes=[("Arquivos Excel", "*.xlsx *.xls")])
        if arquivo:
            self.caminho_arquivo_excel.set(arquivo)
            self.nome_arquivo_display.set(os.path.basename(arquivo))
            self._log_mensagem(f"Arquivo selecionado: {os.path.basename(arquivo)}")

    def _selecionar_pasta_destino(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_destino_pdf.get(),
                                        title="Selecione a pasta para salvar o relatório PDF")
        if pasta:
            self.pasta_destino_pdf.set(pasta)
            self._log_mensagem(f"Pasta de destino selecionada: {pasta}")
            os.makedirs(self.pasta_destino_pdf.get(), exist_ok=True)

    def _iniciar_geracao_relatorio_threaded(self):
        if not self.caminho_arquivo_excel.get():
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo Excel primeiro.")
            return

        self.btn_gerar_relatorio.configure(state="disabled", text="Gerando Relatório...")
        self._log_mensagem("Iniciando a geração do relatório...")

        threading.Thread(target=self._executar_geracao_relatorio, daemon=True).start()

    def _executar_geracao_relatorio(self):
        try:
            resultado_msg = self.honorarios_processor.processar_honorarios_e_gerar_pdf(
                self.caminho_arquivo_excel.get(),
                self.pasta_destino_pdf.get()
            )
            self.after(0, lambda: messagebox.showinfo("Sucesso", resultado_msg))
            self._log_mensagem(f"✅ {resultado_msg}")
        except Exception as e:
            self._log_mensagem(f"❌ Erro: {e}")
            self.after(0, lambda: messagebox.showerror("Erro no Processamento", str(e)))
        finally:
            self.after(0, lambda: self.btn_gerar_relatorio.configure(state="normal",
                                                                     text="📈 Gerar Relatório de Honorários"))

    def _log_mensagem(self, mensagem: str):
        if self.winfo_exists():
            self.after(0, self._append_log_message, mensagem)

    def _append_log_message(self, mensagem: str):
        self.caixa_log.configure(state='normal')
        self.caixa_log.insert(ctk.END, f"{datetime.now().strftime('%H:%M:%S')} - {mensagem}\n")
        self.caixa_log.see(ctk.END)
        self.caixa_log.configure(state='disabled')
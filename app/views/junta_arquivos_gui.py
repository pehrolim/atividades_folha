# app/views/junta_arquivos_gui.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
import threading

# Importa a lógica do processador e os widgets padronizados
from app.logic.junta_arquivos_processor import ExcelProcessor
from app.widgets.custom_button import StandardButton
from app.widgets.custom_labels import TitleLabel, InfoLabel, ValueLabel
from app.widgets.custom_frames import StandardFrame


class JuntaArquivosGUI(ctk.CTkFrame):
    """
    View para a consolidação de múltiplos arquivos Excel, permitindo
    a seleção individual de arquivos.
    """

    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=10, pady=10)

        self.arquivos_selecionados = []
        self.pasta_destino_saida = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../data/excel_processed'))
        os.makedirs(self.pasta_destino_saida, exist_ok=True)

        self.excel_processor = ExcelProcessor(logger_callback=self._log_mensagem)
        self._criar_interface()

    def _criar_interface(self):
        """Cria e organiza os widgets da interface gráfica."""
        # --- Frame Principal para Arquivos ---
        files_main_frame = StandardFrame(self)
        files_main_frame.pack(pady=10, padx=10, fill="both", expand=True)

        StandardButton(files_main_frame, text="➕ Adicionar Arquivo(s) Excel",
                       command=self._adicionar_arquivo,
                       variant="success").pack(pady=15)

        self.frame_lista_arquivos = ctk.CTkScrollableFrame(files_main_frame,
                                                           label_text="Arquivos na Fila para Processamento")
        self.frame_lista_arquivos.pack(fill="both", expand=True, padx=10, pady=10)
        self._atualizar_lista_arquivos_gui()

        # --- Frame para Configurações de Saída ---
        output_frame = StandardFrame(self)
        output_frame.pack(pady=10, padx=10, fill="x")

        InfoLabel(output_frame, text="📂 Pasta de Destino para Consolidados e Logs:").pack(pady=(10, 0))
        self.lbl_pasta_destino = ValueLabel(output_frame, text=self.pasta_destino_saida, wraplength=900)
        self.lbl_pasta_destino.pack(padx=10)
        StandardButton(output_frame, text="Selecionar Pasta de Destino", command=self._selecionar_pasta_destino).pack(
            pady=10)

        # --- Botão de Processamento e Log ---
        self.btn_processar = StandardButton(self, text="🚀 Processar Arquivos da Fila",
                                            command=self._iniciar_processamento_threaded,
                                            variant="processing")
        self.btn_processar.pack(pady=20, ipady=5)

        self.caixa_log = ctk.CTkTextbox(self, height=150, state='disabled', wrap='word')
        self.caixa_log.pack(fill="both", expand=True, padx=10, pady=5)

    def _adicionar_arquivo(self):
        """Abre o diálogo para selecionar um ou mais arquivos Excel."""
        arquivos = filedialog.askopenfilenames(
            title="Selecione um ou mais arquivos Excel",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls")]
        )
        if not arquivos: return

        novos_adicionados = 0
        for arquivo_path in arquivos:
            if any(item['caminho'] == arquivo_path for item in self.arquivos_selecionados):
                self.log(f"⚠️ Aviso: Arquivo '{os.path.basename(arquivo_path)}' já está na lista.")
                continue

            arquivo_info = {
                'caminho': arquivo_path,
                'nome_amigavel': os.path.basename(arquivo_path)
            }
            self.arquivos_selecionados.append(arquivo_info)
            novos_adicionados += 1

        if novos_adicionados > 0:
            self.log(f"📁 {novos_adicionados} arquivo(s) adicionado(s) à fila.")
            self._atualizar_lista_arquivos_gui()

    def _remover_arquivo(self, index_para_remover):
        """Remove um arquivo da lista de selecionados."""
        if 0 <= index_para_remover < len(self.arquivos_selecionados):
            nome_removido = self.arquivos_selecionados[index_para_remover]['nome_amigavel']
            del self.arquivos_selecionados[index_para_remover]
            self.log(f"🗑️ Arquivo removido da fila: {nome_removido}")
            self._atualizar_lista_arquivos_gui()

    def _atualizar_lista_arquivos_gui(self):
        """Limpa e recria a lista de arquivos na interface."""
        for widget in self.frame_lista_arquivos.winfo_children():
            widget.destroy()

        if not self.arquivos_selecionados:
            InfoLabel(self.frame_lista_arquivos, text="Nenhum arquivo na fila.").pack(pady=20)
            return

        for i, arquivo_info in enumerate(self.arquivos_selecionados):
            item_frame = ctk.CTkFrame(self.frame_lista_arquivos, fg_color="transparent")
            item_frame.pack(fill="x", pady=2, padx=5)

            label = InfoLabel(item_frame, text=f"📄 {arquivo_info['nome_amigavel']}")
            label.pack(side="left", padx=5, expand=True, anchor="w")

            remove_button = StandardButton(item_frame, text="Remover", command=lambda idx=i: self._remover_arquivo(idx),
                                           variant="danger", width=80, height=25)
            remove_button.pack(side="right", padx=5)

    def _selecionar_pasta_destino(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_destino_saida,
                                        title="Selecione a pasta para salvar os arquivos de saída")
        if pasta:
            self.pasta_destino_saida = pasta
            self.lbl_pasta_destino.configure(text=pasta)
            self.log(f"Pasta de destino selecionada: {pasta}")
            os.makedirs(self.pasta_destino_saida, exist_ok=True)

    def _iniciar_processamento_threaded(self):
        if not self.arquivos_selecionados:
            messagebox.showwarning("Nenhum Arquivo", "Por favor, adicione pelo menos um arquivo Excel para processar.")
            return

        self.btn_processar.configure(state="disabled", text="Processando...")
        self.log("Iniciando o processamento... Isso pode levar um momento.")

        lista_de_caminhos = [item['caminho'] for item in self.arquivos_selecionados]

        process_thread = threading.Thread(target=self._executar_processamento, args=(lista_de_caminhos,))
        process_thread.daemon = True
        process_thread.start()

    def _executar_processamento(self, lista_de_arquivos):
        try:
            df_consolidado = self.excel_processor.processar_arquivos_excel(lista_de_arquivos)
            self.excel_processor.salvar_consolidado_excel(self.pasta_destino_saida, df_consolidado)
            self.excel_processor.gerar_resumo_e_pdf_log(self.pasta_destino_saida, df_consolidado)

            self.after(0, lambda: messagebox.showinfo("Sucesso", "Processamento concluído com sucesso!"))
            self.log("🎉 Processamento de arquivos Excel finalizado!")
        except Exception as e:
            self.log(f"❌ Erro: {e}")
            self.after(0, lambda: messagebox.showerror("Erro no Processamento", f"Ocorreu um erro: {e}"))
        finally:
            self.after(0, lambda: self.btn_processar.configure(state="normal", text="🚀 Processar Arquivos da Fila"))

    def _log_mensagem(self, mensagem: str):
        if self.winfo_exists():
            self.after(0, self._append_log_message, mensagem)

    def _append_log_message(self, mensagem: str):
        self.caixa_log.configure(state='normal')
        self.caixa_log.insert(ctk.END, f"{datetime.now().strftime('%H:%M:%S')} - {mensagem}\n")
        self.caixa_log.see(ctk.END)
        self.caixa_log.configure(state='disabled')
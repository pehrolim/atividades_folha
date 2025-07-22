
import customtkinter as ctk
from tkinter import ttk, filedialog
import pandas as pd
import threading
import os

# Importa a lógica e os nossos componentes padronizados
from app.logic.analise_folha_processor import analisar_arquivos
from app.logic.data_manager import DataManager  # <-- Importa o DataManager
from app.widgets.custom_button import StandardButton
from app.widgets.custom_frames import StandardFrame, TransparentFrame
from app.widgets.custom_labels import TitleLabel, InfoLabel, ValueLabel


class AnaliseView(ctk.CTkFrame):
    """
    A view principal da aplicação de análise, construída com CustomTkinter
    e utilizando componentes padronizados.
    """

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # --- Variáveis de Estado ---
        self.caminho_inf_display = ctk.StringVar(value="Nenhum arquivo selecionado")
        self.caminho_folha_display = ctk.StringVar(value="Nenhum arquivo selecionado")
        self.status_texto = ctk.StringVar(value="Pronto para começar.")

        self.caminho_inf_completo = ""
        self.caminho_folha_completo = ""

        # --- Configuração do Layout Principal ---
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Inicialização da Interface ---
        self._criar_widgets()

    def _criar_widgets(self):
        """Cria e organiza todos os componentes visuais da tela."""

        # --- Seção 1: Seleção de Arquivos ---
        frame_selecao = StandardFrame(self)
        frame_selecao.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        frame_selecao.grid_columnconfigure(1, weight=1)

        TitleLabel(frame_selecao, text="Passo 1: Selecione os Arquivos").grid(row=0, column=0, columnspan=2, pady=10)

        StandardButton(frame_selecao, text="Arquivo de Implantação (.xlsx)", variant="primary",
                       command=self._selecionar_arquivo_inf).grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ValueLabel(frame_selecao, textvariable=self.caminho_inf_display, wraplength=600).grid(row=1, column=1, padx=10,
                                                                                              pady=5, sticky="w")

        StandardButton(frame_selecao, text="Arquivo de Retorno (.txt, .csv)", variant="primary",
                       command=self._selecionar_arquivo_folha).grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ValueLabel(frame_selecao, textvariable=self.caminho_folha_display, wraplength=600).grid(row=2, column=1,
                                                                                                padx=10, pady=5,
                                                                                                sticky="w")

        # --- Seção 2: Botão de Ação ---
        self.btn_analisar = StandardButton(self, text="Analisar Arquivos", variant="processing",
                                           command=self._iniciar_analise)
        self.btn_analisar.grid(row=1, column=0, padx=5, pady=15, sticky="ew", ipady=5)

        # --- Seção 3: Resultados em Abas ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        self.tab_view.add("Sucesso")
        self.tab_view.add("Falhou")

        # --- Seção 4: Barra de Status ---
        InfoLabel(self, textvariable=self.status_texto, anchor="w").grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    def _selecionar_arquivo_inf(self):
        """Abre o diálogo para selecionar o arquivo .xlsx de implantação."""
        caminho = filedialog.askopenfilename(title="Selecione o arquivo de implantação",
                                             filetypes=[("Arquivos Excel", "*.xlsx")])
        if caminho:
            self.caminho_inf_completo = caminho
            self.caminho_inf_display.set(os.path.basename(caminho))

    def _selecionar_arquivo_folha(self):
        """Abre o diálogo para selecionar o arquivo .txt ou .csv de retorno."""
        caminho = filedialog.askopenfilename(title="Selecione o arquivo de retorno da folha",
                                             filetypes=[("Arquivos de Texto", "*.csv *.txt"),
                                                        ("Todos os arquivos", "*.*")])
        if caminho:
            self.caminho_folha_completo = caminho
            self.caminho_folha_display.set(os.path.basename(caminho))

    def _iniciar_analise(self):
        """Valida os inputs e inicia a análise em uma thread separada para não travar a UI."""
        if not self.caminho_inf_completo or not self.caminho_folha_completo:
            self.status_texto.set("Erro: Por favor, selecione ambos os arquivos antes de analisar.")
            return

        self.btn_analisar.configure(state="disabled")
        self.status_texto.set("Analisando, por favor aguarde...")
        threading.Thread(target=self._executar_analise, daemon=True).start()

    def _executar_analise(self):
        """Função executada na thread. Chama a lógica de negócio e agenda a atualização da UI."""
        resultado = analisar_arquivos(self.caminho_inf_completo, self.caminho_folha_completo)
        self.after(0, self._atualizar_ui_com_resultados, resultado)

    def _atualizar_ui_com_resultados(self, resultado_df):
        """Atualiza a interface com os resultados da análise. Executada na thread principal."""
        if isinstance(resultado_df, pd.DataFrame):
            df_sucesso = resultado_df[resultado_df['TESTE'] == 'SUCESSO'].copy()
            df_falhou = resultado_df[resultado_df['TESTE'] == 'FALHOU'].copy()

            self._criar_aba_de_resultado(self.tab_view.tab("Sucesso"), df_sucesso, "Sucesso")
            self._criar_aba_de_resultado(self.tab_view.tab("Falhou"), df_falhou, "Falhou")

            self.status_texto.set("Análise concluída com sucesso!")
        else:
            self.status_texto.set(f"Erro na análise: {resultado_df}")

        self.btn_analisar.configure(state="normal")

    def _criar_aba_de_resultado(self, tab, df, tipo):
        """Limpa uma aba e a preenche com uma tabela (Treeview) dos dados do DataFrame."""
        for widget in tab.winfo_children():
            widget.destroy()

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        frame_cabecalho = TransparentFrame(tab)
        frame_cabecalho.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        total_registros = len(df)
        InfoLabel(frame_cabecalho, text=f"{total_registros} registros encontrados.").pack(side="left")

        btn_download = StandardButton(frame_cabecalho, text="Baixar Relatório (.xlsx)", variant="primary",
                                      command=lambda d=df, t=tipo: self._baixar_arquivo_excel(d, t))
        btn_download.pack(side="right")
        if df.empty:
            btn_download.configure(state="disabled")

        if df.empty:
            InfoLabel(tab, text="Nenhum registro para exibir.").grid(row=1, column=0, pady=20)
            return

        # --- Tabela (Treeview) ---
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Roboto", 10, "bold"))

        colunas_para_mostrar = [col for col in df.columns if col != '_merge']
        tree = ttk.Treeview(tab, columns=colunas_para_mostrar, show='headings', style="Treeview")

        v_scroll = ctk.CTkScrollbar(tab, command=tree.yview)
        h_scroll = ctk.CTkScrollbar(tab, command=tree.xview, orientation="horizontal")
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        tree.grid(row=1, column=0, sticky="nsew")
        v_scroll.grid(row=1, column=1, sticky="ns")
        h_scroll.grid(row=2, column=0, sticky="ew")

        for col_name in colunas_para_mostrar:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=120, anchor='w', stretch=tk.NO)

        tree.tag_configure('oddrow', background="#EAEAEA")
        tree.tag_configure('evenrow', background="#FFFFFF")

        for i, row in enumerate(df[colunas_para_mostrar].itertuples(index=False)):
            tag = 'oddrow' if i % 2 != 0 else 'evenrow'
            tree.insert('', 'end', values=row, tags=(tag,))

    def _baixar_arquivo_excel(self, df, tipo):
        """Salva o conteúdo de um DataFrame em um arquivo .xlsx, delegando a lógica para o DataManager."""
        if df.empty:
            self.status_texto.set("Não há dados para baixar.")
            return

        # Usa o DataManager para gerar um nome de arquivo padronizado
        nome_sugerido = DataManager.generate_report_filename(f"relatorio_{tipo.lower()}", "xlsx")

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx")],
            title=f"Salvar Relatório de {tipo}",
            initialfile=nome_sugerido
        )

        if not filepath:
            self.status_texto.set("Operação de download cancelada.")
            return

        try:
            # Prepara o DataFrame final e chama o método estático do DataManager
            colunas_para_salvar = [col for col in df.columns if col != '_merge']
            df_to_save = df[colunas_para_salvar]
            DataManager.save_df_to_xlsx(df_to_save, filepath)
            self.status_texto.set(f"Arquivo salvo com sucesso em: {os.path.basename(filepath)}")
        except Exception as e:
            self.status_texto.set(f"Falha ao salvar o arquivo: {e}")


# --- Bloco de Execução Principal (para testes isolados) ---
if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Analisador de Arquivos da Folha")
    root.geometry("900x700")
    root.minsize(800, 600)

    app_view = AnaliseView(master=root)

    root.mainloop()


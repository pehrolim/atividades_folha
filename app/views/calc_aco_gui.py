import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import threading
from app.logic.calc_aco_processor import CalcAcoProcessor
from app.widgets.custom_button import StandardButton
from app.widgets.custom_frames import StandardFrame, TransparentFrame
from app.widgets.custom_labels import TitleLabel, InfoLabel, ValueLabel

class CalcAcoGUI(ctk.CTkFrame):
    def __init__(self, master=None):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True)

        self.processor = CalcAcoProcessor()
        self.colunas_tabela = ['Matrícula', 'CLF', 'Código', 'Referencia (Horas)', 'H. Normal',
                               'Tarifa Normal', 'H. Majorada', 'Tarifa Majorada', 'Valor Total', 'Observação']
        self.dados_para_exibicao = []
        self.valores_calculados = None

        self.var_tarifa_normal = ctk.StringVar(value="R$ 0,00")
        self.var_tarifa_majorada = ctk.StringVar(value="R$ 0,00")
        self.var_status_busca = ctk.StringVar(value="Aguardando CLF...")
        self.var_hn = ctk.StringVar(value="0.0")
        self.var_hm = ctk.StringVar(value="0.0")
        self.var_vt = ctk.StringVar(value="R$ 0,00")

        self._criar_interface()

    def _criar_interface(self):
        main_grid = TransparentFrame(self)
        main_grid.pack(fill="both", expand=True, padx=10, pady=10)
        main_grid.grid_columnconfigure(0, weight=1)
        main_grid.grid_columnconfigure(1, weight=1)
        main_grid.grid_rowconfigure(1, weight=1)

        frame_esquerdo = TransparentFrame(main_grid)
        frame_esquerdo.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="nsew")
        frame_esquerdo.grid_rowconfigure(1, weight=1)
        frame_esquerdo.grid_columnconfigure(0, weight=1)

        frame_direito = TransparentFrame(main_grid)
        frame_direito.grid(row=0, column=1, sticky="new")
        frame_direito.grid_columnconfigure(0, weight=1)

        frame_entradas = StandardFrame(frame_esquerdo)
        frame_entradas.grid(row=0, column=0, sticky="ew")
        TitleLabel(frame_entradas, text="1. Preencha os Dados").pack(pady=(10, 15), padx=20)

        grid_entradas = TransparentFrame(frame_entradas)
        grid_entradas.pack(fill='x', padx=10, pady=5)
        grid_entradas.grid_columnconfigure((1, 3), weight=1)

        InfoLabel(grid_entradas, text="Matrícula:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.entry_matricula = ctk.CTkEntry(grid_entradas)
        self.entry_matricula.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky='ew')
        self.entry_matricula.bind("<Return>", self._adicionar_item_event) # Atalho Enter

        InfoLabel(grid_entradas, text="CLF:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.entry_clf = ctk.CTkEntry(grid_entradas)
        self.entry_clf.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        self.entry_clf.bind("<FocusOut>", self._buscar_tarifas_e_calcular)
        self.entry_clf.bind("<Return>", self._adicionar_item_event) # Atalho Enter

        InfoLabel(grid_entradas, text="Código:").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.entry_codigo = ctk.CTkEntry(grid_entradas)
        self.entry_codigo.grid(row=1, column=3, padx=5, pady=5, sticky='ew')
        self.entry_codigo.bind("<FocusOut>", self._buscar_tarifas_e_calcular)
        self.entry_codigo.bind("<Return>", self._adicionar_item_event) # Atalho Enter

        InfoLabel(grid_entradas, text="Referencia (Horas):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.entry_referencia = ctk.CTkEntry(grid_entradas)
        self.entry_referencia.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky='ew')
        self.entry_referencia.bind("<FocusOut>", self._calcular_valores)
        self.entry_referencia.bind("<Return>", self._adicionar_item_event) # Atalho Enter

        InfoLabel(grid_entradas, text="Observação:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.entry_observacao = ctk.CTkEntry(grid_entradas)
        self.entry_observacao.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky='we')
        self.entry_observacao.bind("<Return>", self._adicionar_item_event) # Atalho Enter
        self.entry_observacao.pack_propagate(False)

        frame_calc = StandardFrame(frame_direito, fg_color=("#EAEAEA", "#2B2B2B"))
        frame_calc.grid(row=0, column=0, sticky="ew")
        TitleLabel(frame_calc, text="2. Demonstrativo do Cálculo").pack(pady=(10, 5), padx=20)
        ValueLabel(frame_calc, textvariable=self.var_status_busca, text_color="gray", font=("Roboto", 10, "italic")).pack(pady=(0, 10))

        frame_tarifas = TransparentFrame(frame_calc)
        frame_tarifas.pack(fill="x", padx=20, pady=5)
        frame_tarifas.grid_columnconfigure((0,1), weight=1)
        InfoLabel(frame_tarifas, text="Tarifa Normal").grid(row=0, column=0)
        ValueLabel(frame_tarifas, textvariable=self.var_tarifa_normal, font=("Roboto", 16, "bold")).grid(row=1, column=0)
        InfoLabel(frame_tarifas, text="Tarifa Majorada").grid(row=0, column=1)
        ValueLabel(frame_tarifas, textvariable=self.var_tarifa_majorada, font=("Roboto", 16, "bold")).grid(row=1, column=1)

        ctk.CTkFrame(frame_calc, height=1, fg_color="gray").pack(fill="x", padx=20, pady=10)

        frame_horas = TransparentFrame(frame_calc)
        frame_horas.pack(fill="x", padx=20, pady=5)
        frame_horas.grid_columnconfigure((0,1), weight=1)
        InfoLabel(frame_horas, text="Horas Normais").grid(row=0, column=0)
        ValueLabel(frame_horas, textvariable=self.var_hn, font=("Roboto", 16, "bold")).grid(row=1, column=0)
        InfoLabel(frame_horas, text="Horas Majoradas").grid(row=0, column=1)
        ValueLabel(frame_horas, textvariable=self.var_hm, font=("Roboto", 16, "bold")).grid(row=1, column=1)

        ctk.CTkFrame(frame_calc, height=2, fg_color="gray").pack(fill="x", padx=20, pady=10)

        TitleLabel(frame_calc, text="VALOR TOTAL CALCULADO", font=("Roboto", 14, "bold")).pack()
        ValueLabel(frame_calc, textvariable=self.var_vt, font=("Roboto", 32, "bold"), text_color="#2ECC71").pack(pady=(0, 20))

        self.btn_adicionar = StandardButton(frame_direito, text="⬇️ Adicionar à Tabela", command=self._adicionar_item, variant="success")
        self.btn_adicionar.grid(row=1, column=0, pady=10, sticky="ew")

        frame_tabela_container = StandardFrame(frame_esquerdo)
        frame_tabela_container.grid(row=1, column=0, pady=(10,0), sticky="nsew")
        frame_tabela_container.grid_rowconfigure(0, weight=1)
        frame_tabela_container.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=("Roboto", 10))
        style.configure("Treeview.Heading", font=("Roboto", 10, "bold"))
        self.tree = ttk.Treeview(frame_tabela_container, columns=self.colunas_tabela, show='headings')
        vsb = ctk.CTkScrollbar(frame_tabela_container, command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ctk.CTkScrollbar(frame_tabela_container, orientation="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        for col in self.colunas_tabela:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor='w')

        frame_acoes = TransparentFrame(frame_esquerdo)
        frame_acoes.grid(row=2, column=0, pady=10, sticky="ew")
        self.btn_importar = StandardButton(frame_acoes, text="Importar", command=self._iniciar_importacao_threaded)
        self.btn_importar.pack(side='left', padx=(0,5))
        self.btn_exportar = StandardButton(frame_acoes, text="Exportar", command=self._exportar_excel)
        self.btn_exportar.pack(side='left', padx=5)
        self.btn_limpar = StandardButton(frame_acoes, text="Limpar", command=self._limpar_tabela, variant="danger")
        self.btn_limpar.pack(side='left', padx=5)

    def _adicionar_item_event(self, event=None):
        """Wrapper para o evento de atalho, que chama a função principal."""
        self._adicionar_item()

    def _buscar_tarifas_e_calcular(self, event=None):
        self._buscar_tarifas_por_clf()
        if self.entry_referencia.get():
            self._calcular_valores()

    def _buscar_tarifas_por_clf(self, event=None):
        self._limpar_resultados()
        clf = self.entry_clf.get()
        codigo = self.entry_codigo.get()
        if not clf:
            self.var_status_busca.set("Aguardando CLF...")
            return

        resultado = self.processor.buscar_tarifas(clf, codigo)
        if resultado['status'] == 'sucesso':
            self.var_tarifa_normal.set(f"R$ {resultado['tarifa_normal']:.2f}")
            self.var_tarifa_majorada.set(f"R$ {resultado['tarifa_majorada']:.2f}")
            self.var_status_busca.set("Tarifas encontradas.")
        else:
            self.var_tarifa_normal.set("R$ 0,00")
            self.var_tarifa_majorada.set("R$ 0,00")
            self.var_status_busca.set(resultado['mensagem'])

    def _calcular_valores(self, event=None):
        self.var_hn.set("0.0"); self.var_hm.set("0.0"); self.var_vt.set("R$ 0,00")
        self.valores_calculados = None
        clf = self.entry_clf.get(); codigo = self.entry_codigo.get()
        referencia_horas = self.entry_referencia.get()

        if not all([clf, referencia_horas]):
            if referencia_horas: messagebox.showwarning("Dados Faltando", "Preencha o 'CLF'.")
            return

        try:
            resultado = self.processor.calcular_tudo(clf, referencia_horas, codigo)
            if resultado['status'] == 'sucesso':
                self.valores_calculados = resultado
                self.var_hn.set(f"{resultado['h_normal']:.1f}")
                self.var_hm.set(f"{resultado['h_majorada']:.1f}")
                self.var_vt.set(f"R$ {resultado['valor_total']:.2f}")
                self.var_tarifa_normal.set(f"R$ {resultado['tarifa_normal']:.2f}")
                self.var_tarifa_majorada.set(f"R$ {resultado['tarifa_majorada']:.2f}")
                self.var_status_busca.set("Cálculo realizado com sucesso!")
            else:
                messagebox.showerror("Erro no Cálculo", resultado['mensagem'])
                self.var_status_busca.set(resultado['mensagem'])
        except Exception as e:
            messagebox.showerror("Erro Inesperado", str(e))

    def _adicionar_item(self):
        if not self.valores_calculados:
            messagebox.showwarning("Ação Inválida", "Preencha CLF e Referencia para calcular os valores antes de adicionar."); return
        if not self.entry_matricula.get():
            messagebox.showwarning("Matrícula Faltando", "Informe a Matrícula."); return

        nova_linha = {
            'Matrícula': self.entry_matricula.get(), 'CLF': self.entry_clf.get(),
            'Código': self.entry_codigo.get(), 'Referencia (Horas)': self.entry_referencia.get(),
            'H. Normal': self.valores_calculados['h_normal'], 'Tarifa Normal': self.valores_calculados['tarifa_normal'],
            'H. Majorada': self.valores_calculados['h_majorada'], 'Tarifa Majorada': self.valores_calculados['tarifa_majorada'],
            'Valor Total': self.valores_calculados['valor_total'], 'Observação': self.entry_observacao.get()
        }
        self.dados_para_exibicao.append(nova_linha)
        self._atualizar_tabela()
        self._limpar_campos_de_entrada()

    def _atualizar_tabela(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for item in self.dados_para_exibicao:
            tn_f = f"R$ {item['Tarifa Normal']:.2f}"; tm_f = f"R$ {item['Tarifa Majorada']:.2f}"; vt_f = f"R$ {item['Valor Total']:.2f}"
            valores = [item['Matrícula'], item['CLF'], item['Código'], item['Referencia (Horas)'],
                       item['H. Normal'], tn_f, item['H. Majorada'], tm_f, vt_f, item['Observação']]
            self.tree.insert("", "end", values=valores)

    def _limpar_resultados(self):
        self.valores_calculados = None
        self.var_tarifa_normal.set("R$ 0,00"); self.var_tarifa_majorada.set("R$ 0,00")
        self.var_status_busca.set("Aguardando CLF...")
        self.var_hn.set("0.0"); self.var_hm.set("0.0"); self.var_vt.set("R$ 0,00")

    def _limpar_campos_de_entrada(self):
        self.entry_matricula.delete(0, 'end'); self.entry_clf.delete(0, 'end')
        self.entry_codigo.delete(0, 'end'); self.entry_referencia.delete(0, 'end')
        self.entry_observacao.delete(0, 'end'); self._limpar_resultados()
        self.entry_matricula.focus()

    def _limpar_tabela(self):
        if self.dados_para_exibicao and messagebox.askyesno("Confirmar", "Limpar a tabela?"):
            self.dados_para_exibicao.clear(); self._atualizar_tabela()

    def _iniciar_importacao_threaded(self):
        caminho_arquivo = filedialog.askopenfilename(filetypes=[("Arquivos Excel", "*.xlsx")])
        if not caminho_arquivo: return
        if self.dados_para_exibicao and messagebox.askyesno("Confirmar", "Limpar dados antes de importar?"):
            self.dados_para_exibicao.clear(); self._atualizar_tabela()
        threading.Thread(target=self._executar_importacao, args=(caminho_arquivo,), daemon=True).start()

    def _executar_importacao(self, caminho_arquivo):
        resultado = self.processor.processar_arquivo_importado(caminho_arquivo);
        self.after(0, self._finalizar_importacao, resultado)

    def _finalizar_importacao(self, resultado):
        if resultado['status'] == 'sucesso':
            self.dados_para_exibicao.extend(resultado['dados']); self._atualizar_tabela()
            sucesso_msg = f"{len(resultado['dados'])} linhas importadas."
            if resultado['erros']:
                erros_msg = "\n\nOcorreram erros:\n" + "\n".join(resultado['erros'])
                messagebox.showwarning("Importação Parcial", sucesso_msg + erros_msg)
            else:
                messagebox.showinfo("Importação Concluída", sucesso_msg)
        else:
            messagebox.showerror("Erro na Importação", resultado['mensagem'])

    def _exportar_excel(self):
        if not self.dados_para_exibicao: messagebox.showwarning("Aviso", "Não há dados para exportar."); return
        caminho = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Arquivos Excel", "*.xlsx")])
        if caminho:
            df = pd.DataFrame(self.dados_para_exibicao)
            df.to_excel(caminho, index=False)
            messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{caminho}")

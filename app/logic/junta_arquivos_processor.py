# app/logic/junta_arquivos_processor.py
import pandas as pd
import os
from datetime import datetime
from fpdf import FPDF


class ExcelProcessor:
    """
    Gerencia a consolidação de múltiplos arquivos Excel e a geração de
    relatórios de processamento em PDF.
    """

    def __init__(self, logger_callback=None):
        """
        Inicializa o processador.

        Args:
            logger_callback (callable, optional): Função para logar mensagens.
                                                  Usa print se for None.
        """
        self.log = logger_callback if logger_callback else print

    def processar_arquivos_excel(self, lista_de_arquivos: list) -> pd.DataFrame:
        """
        Lê uma lista de caminhos de arquivos Excel, consolida seus conteúdos
        e retorna um único DataFrame.

        Args:
            lista_de_arquivos (list): Uma lista de strings contendo os caminhos
                                      completos para os arquivos Excel.

        Returns:
            pd.DataFrame: O DataFrame consolidado com uma coluna de rastreabilidade.

        Raises:
            ValueError: Se a lista de arquivos estiver vazia ou se nenhum arquivo
                        puder ser lido com sucesso.
        """
        if not lista_de_arquivos:
            raise ValueError("Nenhum arquivo foi selecionado para processamento.")

        self.log(f"Iniciando a consolidação de {len(lista_de_arquivos)} arquivo(s)...")
        lista_de_dataframes = []

        for arquivo_path in lista_de_arquivos:
            nome_arquivo = os.path.basename(arquivo_path)
            try:
                self.log(f"Lendo o arquivo: {nome_arquivo}")
                # Lê a primeira aba de cada arquivo Excel
                df_temp = pd.read_excel(arquivo_path)
                # Adiciona uma coluna de origem para rastreabilidade, que é muito útil
                df_temp['ARQUIVO_ORIGEM'] = nome_arquivo
                lista_de_dataframes.append(df_temp)
            except Exception as e:
                self.log(f"⚠️ Erro ao ler o arquivo {nome_arquivo}: {e}. O arquivo será ignorado.")
                continue

        if not lista_de_dataframes:
            raise ValueError("Nenhum dos arquivos selecionados pôde ser lido com sucesso.")

        df_consolidado = pd.concat(lista_de_dataframes, ignore_index=True)
        self.log(f"Consolidação concluída. Total de {len(df_consolidado)} linhas processadas.")
        return df_consolidado

    def salvar_consolidado_excel(self, pasta_destino: str, df: pd.DataFrame):
        """Salva o DataFrame consolidado em um novo arquivo Excel com timestamp."""
        if df.empty:
            self.log("Nenhum dado consolidado para salvar.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_saida = os.path.join(pasta_destino, f"consolidado_{timestamp}.xlsx")

        try:
            df.to_excel(caminho_saida, index=False)
            self.log(f"✅ Arquivo consolidado salvo com sucesso em: {caminho_saida}")
        except Exception as e:
            self.log(f"❌ Erro ao salvar o arquivo consolidado: {e}")
            raise

    def gerar_resumo_e_pdf_log(self, pasta_destino: str, df: pd.DataFrame):
        """
        Gera um resumo do processamento e salva em um arquivo PDF limpo e informativo.
        """
        if df.empty or 'ARQUIVO_ORIGEM' not in df.columns:
            self.log("Nenhum dado para gerar o resumo em PDF.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho_pdf = os.path.join(pasta_destino, f"log_processamento_{timestamp}.pdf")

        # Cria um resumo de quantas linhas vieram de cada arquivo
        resumo = df.groupby('ARQUIVO_ORIGEM').size().reset_index(name='LINHAS_PROCESSADAS')

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Relatório de Consolidação de Arquivos", align='C', new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)

            pdf.set_font("Helvetica", size=11)
            pdf.cell(0, 8, f"Data do Processamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", new_x="LMARGIN",
                     new_y="NEXT")
            pdf.cell(0, 8, f"Total de Arquivos Processados: {len(resumo)}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"Total de Linhas Consolidadas: {len(df)}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)

            # Cabeçalho da tabela no PDF
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(130, 10, 'Arquivo de Origem', border=1)
            pdf.cell(50, 10, 'Linhas Processadas', border=1, align='C')
            pdf.ln()

            # Corpo da tabela
            pdf.set_font("Helvetica", size=10)
            for _, row in resumo.iterrows():
                pdf.cell(130, 10, str(row['ARQUIVO_ORIGEM']), border=1)
                pdf.cell(50, 10, str(row['LINHAS_PROCESSADAS']), border=1, align='C')
                pdf.ln()

            pdf.output(caminho_pdf)
            self.log(f"📄 Relatório em PDF gerado com sucesso em: {caminho_pdf}")
        except Exception as e:
            self.log(f"❌ Erro ao gerar o relatório em PDF: {e}")
            raise
# app/logic/honorarios_processor.py
import pandas as pd
import locale
from num2words import num2words
from fpdf import FPDF
import datetime
import os
import sys
import subprocess

# As regras de negócio (filtros) são mantidas como constantes
FILTROS_HONORARIOS = {
    "PRESTADORES": {
        "CODIGO": 898,
        "isin": {"coluna": "CLF", "valores": [10021, 10033, 10015, 49911, 49921]}
    },
    "MAG APOSENTADOS": {
        "CODIGO": 898, "GRUPO": "MAG", "COD_ORGAO": 29
    },
    "MAG PENSAO": {
        "CODIGO": 898, "COD_ORGAO": 8, "range": {"coluna": "CLF", "valores": [40001, 49107]}
    },
    "SFT APOSENTADOS": {
        "CODIGO": 898, "GRUPO": "SFT", "COD_ORGAO": 29
    },
    "SFT PENSAO": {
        "CODIGO": 898, "COD_ORGAO": 8, "range": {"coluna": "CLF", "valores": [55111, 55257]}
    },
    "SFT ATIVOS": {
        "CODIGO": 898, "GRUPO": "SFT", "not_in": {"coluna": "COD_ORGAO", "valores": [8, 29]}
    }
}


class HonorariosProcessor:
    """
    Processa dados de honorários, aplica filtros e gera relatórios em PDF.
    """

    def __init__(self, logger_callback=None):
        self.log = logger_callback if logger_callback else self._default_logger
        self._configurar_locale()

    def _default_logger(self, message):
        print(message)

    def _configurar_locale(self):
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
            except locale.Error:
                self.log("Aviso: Locale pt_BR não pôde ser configurado.")

    def _formatar_valor_por_extenso(self, valor: float) -> str:
        if valor == 0: return "Zero reais"
        valor_arredondado = round(valor, 2)
        reais = int(valor_arredondado)
        centavos = int(round((valor_arredondado - reais) * 100))
        texto_reais = num2words(reais, lang='pt_BR') if reais > 0 else ""
        texto_centavos = num2words(centavos, lang='pt_BR') if centavos > 0 else ""
        partes = []
        if reais > 0: partes.append(f"{texto_reais} {'reais' if reais > 1 else 'real'}")
        if centavos > 0: partes.append(f"{texto_centavos} {'centavos' if centavos > 1 else 'centavo'}")
        return " e ".join(partes) if partes else "Zero reais"

    def _gerar_pdf_relatorio(self, conteudo_texto: str, caminho_arquivo: str):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(w=0, h=10, text="Relatório de Honorários", new_x="LMARGIN", new_y="NEXT", align='C')
            pdf.ln(5)
            data_geracao = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
            pdf.set_font("Helvetica", '', 10)
            pdf.cell(w=0, h=10, text=f"Gerado em: {data_geracao}", new_x="LMARGIN", new_y="NEXT", align='C')
            pdf.ln(10)
            pdf.set_font("Helvetica", '', 12)
            # Codifica para 'latin-1' para compatibilidade com fontes padrão do FPDF
            texto_compativel = conteudo_texto.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(w=0, h=7, text=texto_compativel)
            pdf.output(caminho_arquivo)
            self.log(f"PDF gerado em: {caminho_arquivo}")
            self._abrir_arquivo_no_os(caminho_arquivo)
        except Exception as e:
            self.log(f"Erro ao gerar o PDF: {e}")
            raise

    def _abrir_arquivo_no_os(self, caminho_arquivo: str):
        try:
            if sys.platform == "win32":
                os.startfile(caminho_arquivo)
            elif sys.platform == "darwin":
                subprocess.call(["open", caminho_arquivo])
            else:
                subprocess.call(["xdg-open", caminho_arquivo])
        except Exception as e:
            self.log(f"Aviso: PDF salvo, mas não pôde ser aberto automaticamente. Erro: {e}")

    def processar_honorarios_e_gerar_pdf(self, caminho_arquivo_excel: str, pasta_destino_pdf: str):
        if not caminho_arquivo_excel or not os.path.exists(caminho_arquivo_excel):
            raise FileNotFoundError(f"Arquivo Excel não encontrado: {caminho_arquivo_excel}")

        os.makedirs(pasta_destino_pdf, exist_ok=True)
        self.log(f"Lendo arquivo Excel: {os.path.basename(caminho_arquivo_excel)}")
        try:
            df = pd.read_excel(caminho_arquivo_excel)
        except Exception as e:
            raise IOError(f"Erro ao ler o arquivo Excel: {e}")

        resultados_finais = []
        for nome_filtro, condicoes in FILTROS_HONORARIOS.items():
            df_filtrado = df.copy()
            # Aplica os filtros sequencialmente
            for chave, valor in condicoes.items():
                if chave in ['CODIGO', 'GRUPO', 'COD_ORGAO']:
                    df_filtrado = df_filtrado[df_filtrado[chave] == valor]
                elif chave == 'isin':
                    df_filtrado = df_filtrado[df_filtrado[valor['coluna']].isin(valor['valores'])]
                elif chave == 'not_in':
                    df_filtrado = df_filtrado[~df_filtrado[valor['coluna']].isin(valor['valores'])]
                elif chave == 'range':
                    col_range = valor['coluna']
                    df_filtrado[col_range] = pd.to_numeric(df_filtrado[col_range], errors='coerce')
                    df_filtrado = df_filtrado[df_filtrado[col_range].between(valor['valores'][0], valor['valores'][1])]

            # Calcula o valor final
            valor_final = pd.to_numeric(df_filtrado['VALOR'], errors='coerce').fillna(0).sum() / 100
            valor_extenso = self._formatar_valor_por_extenso(valor_final).capitalize()
            valor_formatado = locale.currency(valor_final, grouping=True)

            resultados_finais.append(f"--- {nome_filtro.upper()} ---\n"
                                     f"Valor Total: {valor_formatado}\n"
                                     f"Valor por Extenso: {valor_extenso}")

        mensagem_final = "\n\n".join(resultados_finais)
        data_hora_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo_pdf = f"relatorio_honorarios_{data_hora_str}.pdf"
        caminho_completo_pdf = os.path.join(pasta_destino_pdf, nome_arquivo_pdf)

        self._gerar_pdf_relatorio(mensagem_final, caminho_completo_pdf)
        return f"Relatório gerado com sucesso: {nome_arquivo_pdf}"
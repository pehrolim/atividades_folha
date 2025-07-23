import pandas as pd
import os

class CalcAcoProcessor:
    """
    Processador para calcular a Ajuda de Custo (ACO) com base em dados de um
    arquivo Excel de tarifas.
    """

    def __init__(self, logger_callback=None):
        self.log = logger_callback if logger_callback else self._default_logger
        self.df_dados = None
        self._carregar_dados()

    def _default_logger(self, mensagem: str):
        print(mensagem)

    def _carregar_dados(self):
        try:
            caminho_arquivo = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../data/dados_ajuda_de_custo.xlsx'))

            if not os.path.exists(caminho_arquivo):
                self.log(f"⚠️ AVISO: O arquivo de dados não foi encontrado em: {caminho_arquivo}")
                self.df_dados = pd.DataFrame(columns=['CLF', 'CODIGO', 'VALOR'])
                return

            self.df_dados = pd.read_excel(caminho_arquivo, dtype=str)
            self.df_dados['CLF'] = self.df_dados['CLF'].astype(str).str.strip()
            self.df_dados['CODIGO'] = self.df_dados['CODIGO'].astype(str).str.strip()
            self.log("✅ Base de dados de ajuda de custo carregada com sucesso.")
        except Exception as e:
            self.log(f"🚨 ERRO CRÍTICO ao tentar carregar a base de dados: {e}")
            self.df_dados = pd.DataFrame(columns=['CLF', 'CODIGO', 'VALOR'])

    def _calcular_horas(self, horas_str: str) -> tuple[float, float]:
        horas_str = str(horas_str).strip().replace('.0', '')
        if not horas_str.isdigit():
            return 0.0, 0.0
        return (float(horas_str), 0.0) if len(horas_str) <= 3 else (float(horas_str[-3:]), float(horas_str[:-3]))

    def buscar_tarifas(self, clf: str, codigo: str = None) -> dict:
        if self.df_dados is None or self.df_dados.empty:
            return {'status': 'erro', 'mensagem': 'Base de dados não carregada.'}

        clf_str = str(clf).strip()
        codigo_str = str(codigo).strip() if codigo else None

        resultado_busca = self.df_dados[self.df_dados['CLF'] == clf_str]

        if resultado_busca.empty:
            return {'status': 'erro', 'mensagem': f"CLF '{clf_str}' não encontrado."}

        if len(resultado_busca) > 1 and codigo_str:
            resultado_busca = resultado_busca[resultado_busca['CODIGO'] == codigo_str]
            if resultado_busca.empty:
                return {'status': 'erro', 'mensagem': f"CLF '{clf_str}' com código '{codigo_str}' não encontrado."}

        if len(resultado_busca) > 1:
            return {'status': 'ambíguo', 'mensagem': f"CLF '{clf_str}' é ambíguo. Forneça um Código."}

        valor_base_str = resultado_busca['VALOR'].iloc[0].replace(',', '.')
        tarifa_normal = float(valor_base_str)
        tarifa_majorada = tarifa_normal * 1.3

        return {'status': 'sucesso', 'tarifa_normal': tarifa_normal, 'tarifa_majorada': tarifa_majorada}


    def calcular_tudo(self, clf: str, horas_str: str, codigo: str = None) -> dict:
        resultado_tarifas = self.buscar_tarifas(clf, codigo)
        if resultado_tarifas['status'] != 'sucesso':
            return resultado_tarifas

        tarifa_normal = resultado_tarifas['tarifa_normal']
        tarifa_majorada = resultado_tarifas['tarifa_majorada']

        h_normal, h_majorada = self._calcular_horas(horas_str)
        valor_total = (h_normal * tarifa_normal) + (h_majorada * tarifa_majorada)

        return {
            'status': 'sucesso', 'tarifa_normal': tarifa_normal, 'tarifa_majorada': tarifa_majorada,
            'h_normal': h_normal, 'h_majorada': h_majorada, 'valor_total': valor_total
        }


    def processar_arquivo_importado(self, caminho_arquivo_importado: str) -> dict:
        try:
            df_importado = pd.read_excel(caminho_arquivo_importado, dtype=str).fillna('')
        except Exception as e:
            return {'status': 'erro', 'mensagem': f"Não foi possível ler o arquivo Excel: {e}"}

        colunas_obrigatorias = ['MATRICULA', 'CLF', 'REFERENCIA']
        if not all(col in df_importado.columns for col in colunas_obrigatorias):
            return {'status': 'erro', 'mensagem': f"Colunas obrigatórias (MATRICULA, CLF, REFERENCIA) não encontradas."}

        dados_processados = []; erros_importacao = []

        for index, row in df_importado.iterrows():
            try:
                matricula = str(row.get('MATRICULA', '')).strip()
                clf = str(row.get('CLF', '')).strip()
                referencia = str(row.get('REFERENCIA', '')).strip()
                codigo = str(row.get('CODIGO', '')).strip()
                observacao = str(row.get('OBSERVACAO', '')).strip()

                if not all([matricula, clf, referencia]):
                    erros_importacao.append(f"Linha {index + 2}: Dados obrigatórios faltando.")
                    continue

                resultado_calculo = self.calcular_tudo(clf, referencia, codigo)

                if resultado_calculo['status'] == 'sucesso':
                    linha_processada = {
                        'Matrícula': matricula, 'CLF': clf, 'Código': codigo,
                        'Referencia (Horas)': referencia,
                        'H. Normal': resultado_calculo['h_normal'], 'Tarifa Normal': resultado_calculo['tarifa_normal'],
                        'H. Majorada': resultado_calculo['h_majorada'], 'Tarifa Majorada': resultado_calculo['tarifa_majorada'],
                        'Valor Total': resultado_calculo['valor_total'], 'Observação': observacao
                    }
                    dados_processados.append(linha_processada)
                else:
                    erros_importacao.append(f"Linha {index + 2} (Matrícula {matricula}): {resultado_calculo['mensagem']}")
            except Exception as e:
                erros_importacao.append(f"Linha {index + 2}: Erro inesperado - {e}")

        return {'status': 'sucesso', 'dados': dados_processados, 'erros': erros_importacao}
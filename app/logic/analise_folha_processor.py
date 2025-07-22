import pandas as pd
import numpy as np


def analisar_arquivos(arquivo_inf, arquivo_folha):
    """
    Processa os arquivos de informações e da folha, cruza os dados
    e retorna um DataFrame com uma coluna de teste 'SUCESSO'/'FALHOU'.
    """
    try:
        # --- Leitura e Processamento Base ---
        cabecalho_dados = ['MATRICULA', 'NOME', 'CODIGO', 'VALOR', 'REFERENCIA', 'PRAZO', 'ORGAO', 'CLF', 'SIMBOLO',
                           'SITUACAO', 'SAIDA', 'DATA_AFAST', 'GRUPO', 'REGIME']

        # Força as chaves de união a serem do tipo string para um merge seguro
        tipos_de_dados_chave = {'MATRICULA': str, 'CODIGO': str}

        df_transp = pd.read_excel(arquivo_inf, dtype=tipos_de_dados_chave)
        df_dados = pd.read_csv(arquivo_folha, header=None, names=cabecalho_dados, sep=',', dtype=tipos_de_dados_chave)

        # --- Cruzamento dos Dados ---
        df_final = pd.merge(
            df_transp,
            df_dados,
            on=['MATRICULA', 'CODIGO'],
            how='left',
            indicator=True,
            suffixes=('_transp', '_dados')
        )

        #
        # CORREÇÃO APLICADA AQUI:
        # Converte as colunas de VALOR para um formato numérico.
        # 'errors='coerce'' transforma qualquer valor que não seja um número em Nulo (NaN).
        #
        df_final['VALOR_transp'] = pd.to_numeric(df_final['VALOR_transp'], errors='coerce')
        df_final['VALOR_dados'] = pd.to_numeric(df_final['VALOR_dados'], errors='coerce')

        # Agora, preenchemos os valores nulos (que eram do 'left_only' ou que falharam na conversão) com 0.
        df_final['VALOR_transp'] = df_final['VALOR_transp'].fillna(0)
        df_final['VALOR_dados'] = df_final['VALOR_dados'].fillna(0)

        # --- Lógica para a Coluna 'TESTE' ---
        # Agora as comparações matemáticas funcionarão corretamente.
        condicoes = [
            # Condição 1: OP 7/8, Valor > 0. Deve existir em ambos e os valores devem ser iguais.
            (df_final['OPERACAO'].isin([7, 8])) &
            (df_final['VALOR_transp'] > 0) &
            (df_final['_merge'] == 'both') &
            (df_final['VALOR_transp'] == df_final['VALOR_dados']),

            # Condição 2: OP 7/8, Valor = 0. Deve existir em ambos e o valor na folha deve ser > 0.
            (df_final['OPERACAO'].isin([7, 8])) &
            (df_final['VALOR_transp'] == 0) &
            (df_final['_merge'] == 'both') &
            (df_final['VALOR_dados'] > 0),

            # Condição 3: OP 9. Não pode aparecer no arquivo de dados.
            (df_final['OPERACAO'] == 9) &
            (df_final['_merge'] == 'left_only')
        ]

        resultados = ['SUCESSO', 'SUCESSO', 'SUCESSO']

        df_final['TESTE'] = np.select(condicoes, resultados, default='FALHOU')

        return df_final

    except FileNotFoundError:
        return "Erro: Um dos arquivos não foi encontrado. Verifique os caminhos."
    except ValueError as e:
        return f"Erro de valor nos dados. Verifique as colunas e tipos. Detalhe: {e}"
    except Exception as e:
        return f"Ocorreu um erro inesperado na análise: {e}"
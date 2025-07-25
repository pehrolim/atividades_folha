import pandas as pd
import numpy as np
from datetime import date


class AcordoProfAposentadosProcessor:
    """
    CAMADA DE LÓGICA DE NEGÓCIO.
    Encapsula todos os cálculos e manipulações de dados para o acordo
    de professores aposentados. Não contém código de interface.
    """

    def tratar_novos(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Processa um DataFrame de entrada, aplicando as regras de negócio.

        Args:
            df (pd.DataFrame): O DataFrame de entrada com os dados brutos.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: Uma tupla contendo três DataFrames:
                                               (df_lancamento_aposentados,
                                                df_lancamento_pensionistas,
                                                df_calculos_completos).
        """
        # 1. Copia e trata os tipos de dados das colunas numéricas
        df_tratado = df.copy()
        cols_numericas = ['VAL_INCORP', 'CARGA_HORA']
        for col in cols_numericas:
            df_tratado[col] = pd.to_numeric(df_tratado[col], errors='coerce').fillna(0)

        if df_tratado.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # 2. Realiza os cálculos de valores de forma vetorizada (regras de negócio)
        val_incorp_decimal = df_tratado['VAL_INCORP'] / 100.0
        df_tratado['V_56_2023'] = (val_incorp_decimal / 1.4) * (((df_tratado['CARGA_HORA'] / 100.0) * 2) + 1)
        df_tratado['V_56_2024_0105'] = df_tratado['V_56_2023'] * 1.0362
        df_tratado['V_56_2024_0612'] = df_tratado['V_56_2024_0105'] + df_tratado['V_56_2023']
        df_tratado['V_56_2025_0105'] = df_tratado['V_56_2024_0612'] * 1.0627
        df_tratado['V_56_2025_0612'] = df_tratado['V_56_2025_0105'] + df_tratado['V_56_2023']

        hoje = date.today()
        meses_retroativo_2025 = 0
        if hoje.year == 2025 and hoje.month > 6:
            meses_retroativo_2025 = hoje.month - 6
        elif hoje.year > 2025:
            meses_retroativo_2025 = 6

        retroativo = ((df_tratado['V_56_2023'] * 8) + (df_tratado['V_56_2024_0105'] * 5) +
                      (df_tratado['V_56_2024_0612'] * 8) + (df_tratado['V_56_2025_0105'] * 5) +
                      (df_tratado['V_56_2025_0612'] * meses_retroativo_2025))
        honorario = (df_tratado['V_56_2023'] * 8)
        df_tratado['RETROATIVO'] = retroativo
        df_tratado['HONORARIO'] = honorario
        df_tratado['PARCELAS'] = np.where((df_tratado['RETROATIVO'] / 4) > 2500.0, 4, 3)

        # 3. Gera as linhas de lançamento com base nos cálculos
        linhas_aposentados = []
        linhas_pensionistas = []

        for index, row in df_tratado.iterrows():
            if row['PARCELAS'] == 0:
                continue

            valor_parcela_retroativo = int((row['RETROATIVO'] / row['PARCELAS']) * 100)
            valor_parcela_honorario = int((row['HONORARIO'] / row['PARCELAS']) * 100)

            if pd.isna(row['MAT_FALEC']) or row['MAT_FALEC'] == '':
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '67',
                    'VALOR': valor_parcela_retroativo, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '898',
                    'VALOR': valor_parcela_honorario, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '56',
                    'VALOR': '', 'REFERENCIA': '', 'PRAZO': ''
                })
            else:
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MAT_FALEC'], 'CODIGO': '56',
                    'VALOR': '', 'REFERENCIA': '', 'PRAZO': ''
                })
                linhas_pensionistas.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '65',
                    'VALOR': valor_parcela_retroativo, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })
                linhas_pensionistas.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '898',
                    'VALOR': valor_parcela_honorario, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })

        # 4. Cria e retorna os DataFrames de resultado
        df_apos = pd.DataFrame(linhas_aposentados)
        df_pensao = pd.DataFrame(linhas_pensionistas)

        return df_apos, df_pensao, df_tratado

    def tratar_bloqueados(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        df_tratado = df.copy()
        cols_numericas = ['VAL_INCORP', 'CARGA_HORA']
        for col in cols_numericas:
            df_tratado[col] = pd.to_numeric(df_tratado[col], errors='coerce').fillna(0)

        if df_tratado.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # 2. Realiza os cálculos de valores de forma vetorizada (regras de negócio)
        val_incorp_decimal = df_tratado['VAL_INCORP'] / 100.0
        df_tratado['V_56_2023'] = (val_incorp_decimal / 1.4) * (((df_tratado['CARGA_HORA'] / 100.0) * 2) + 1)
        df_tratado['V_56_2024_0105'] = df_tratado['V_56_2023'] * 1.0362
        df_tratado['V_56_2024_0612'] = df_tratado['V_56_2024_0105'] + df_tratado['V_56_2023']
        df_tratado['V_56_2025_0105'] = df_tratado['V_56_2024_0612'] * 1.0627
        df_tratado['V_56_2025_0612'] = df_tratado['V_56_2025_0105'] + df_tratado['V_56_2023']

        hoje = date.today()
        meses_retroativo_2025 = 0
        if hoje.year == 2025 and hoje.month > 6:
            meses_retroativo_2025 = hoje.month - 6
        elif hoje.year > 2025:
            meses_retroativo_2025 = 6

        honorario_total = (df_tratado['V_56_2023'] * 8)

        honorario_bloqueado = ((honorario_total/16)*5)

        honorario_restante = honorario_total - honorario_bloqueado

        ressarcimento = ((df_tratado['V_56_2023'] * 8) + (df_tratado['V_56_2024_0105'] * 4) - honorario_bloqueado)

        retroativo = ((df_tratado['V_56_2024_0105']) +
                      (df_tratado['V_56_2024_0612'] * 8) + (df_tratado['V_56_2025_0105'] * 5) +
                      (df_tratado['V_56_2025_0612'] * meses_retroativo_2025))

        df_tratado['RETROATIVO'] = retroativo
        df_tratado['HONORARIO'] = honorario_total
        df_tratado['HONORARIO_RESTANTE'] = honorario_restante
        df_tratado['RESSARCIMENTO'] = ressarcimento
        df_tratado['HONORARIO_BLOQUEADO'] = honorario_bloqueado
        df_tratado['PARCELAS'] = np.where((df_tratado['RETROATIVO'] / 4) > 2500.0, 4, 3)

        # 3. Gera as linhas de lançamento com base nos cálculos
        linhas_aposentados = []
        linhas_pensionistas = []

        for index, row in df_tratado.iterrows():
            if row['PARCELAS'] == 0:
                continue

            valor_parcela_retroativo = int((row['RETROATIVO'] / row['PARCELAS']) * 100)
            valor_parcela_honorario = int((row['HONORARIO_RESTANTE'] / row['PARCELAS']) * 100)

            if pd.isna(row['MAT_FALEC']) or row['MAT_FALEC'] == '':
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '67',
                    'VALOR': valor_parcela_retroativo, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '898',
                    'VALOR': valor_parcela_honorario, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '56',
                    'VALOR': '', 'REFERENCIA': '', 'PRAZO': ''
                })
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '663',
                    'VALOR': row['RESSARCIMENTO'], 'REFERENCIA': '', 'PRAZO': '1'
                })
            else:
                linhas_aposentados.append({
                    'OPERACAO': '7', 'MATRICULA': row['MAT_FALEC'], 'CODIGO': '56',
                    'VALOR': '', 'REFERENCIA': '', 'PRAZO': ''
                })
                linhas_pensionistas.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '65',
                    'VALOR': valor_parcela_retroativo, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })
                linhas_pensionistas.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '898',
                    'VALOR': valor_parcela_honorario, 'REFERENCIA': '', 'PRAZO': row['PARCELAS']
                })
                linhas_pensionistas.append({
                    'OPERACAO': '7', 'MATRICULA': row['MATRICULA'], 'CODIGO': '663',
                    'VALOR': row['RESSARCIMENTO'], 'REFERENCIA': '', 'PRAZO': '1'
                })

        df_apos = pd.DataFrame(linhas_aposentados)
        df_pensao = pd.DataFrame(linhas_pensionistas)

        return df_apos, df_pensao, df_tratado
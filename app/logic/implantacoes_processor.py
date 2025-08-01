class ImplantacoesProcessor:
    """
    Contém a lógica de negócio para formatar os dados de implantação.
    """

    def formatar_linha_para_txt(self, linha_dados):
        """
        Formata uma linha de dados para o formato de texto específico.

        Args:
            linha_dados (list or tuple): Uma coleção contendo os dados na seguinte ordem:
                - Ignorado (índice 0)
                - Matrícula (índice 1)
                - Código (índice 2)
                - Valor (índice 3)
                - Referência (índice 4)
                - Prazo (índice 5)
                - Observação (índice 6)

        Returns:
            str: O texto formatado pronto para ser guardado num ficheiro.
        """
        # 1. Extração e limpeza dos dados da linha
        matricula = str(linha_dados[1]).strip() or '_'
        codigo = str(linha_dados[2]).strip() or '_'
        valor_da_linha = linha_dados[3]
        referencia = str(linha_dados[4]).strip() or '_'
        prazo = str(linha_dados[5]).strip() or '_'
        observacao = str(linha_dados[6]).strip() or '_'

        # 2. Tratamento do valor numérico
        try:
            # Converte para float, tratando tanto '.' como ',' como separador decimal
            valor_float = float(str(valor_da_linha).replace(',', '.'))
        except (ValueError, TypeError):
            # Se a conversão falhar, assume 0
            valor_float = 0.0

        # Converte o valor para centavos (ex: 15.25 -> 1525) e depois para string
        valor_formatado = str(int(round(valor_float * 100)))

        # 3. A CORREÇÃO PRINCIPAL: Verifica se o valor é "0" e substitui por "_"
        # A variável `valor_formatado` é um texto (string), então comparamos com o texto '0'.
        if valor_formatado == '0':
            valor_formatado = '_'

        # 4. Formatação da referência com zeros à esquerda
        if not referencia or referencia == '_':
            referencia_formatada = '_'
        else:
            # Garante que a referência tenha 7 dígitos, preenchendo com zeros à esquerda
            referencia_formatada = referencia.zfill(7)

        if not prazo or prazo == '_':
            prazo_formatado = '_'
        else:
            # Garante que a referência tenha 7 dígitos, preenchendo com zeros à esquerda
            prazo_formatado = prazo.zfill(3)

        # 5. Montagem do texto final
        texto_formatado = (
            f"{matricula}\n"
            f"{codigo}\n"
            f"{valor_formatado}\n"
            f"{referencia_formatada}\n"
            f"{prazo_formatado}\n"
            "_______\n"
            f"{observacao}"
        )
        return texto_formatado
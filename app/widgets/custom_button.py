# app/widgets/custom_button.py

import customtkinter as ctk

class StandardButton(ctk.CTkButton):
    """
    Uma classe de botão customizada que herda de CTkButton.
    Define estilos padrão através de "variantes" para diferentes
    tipos de botões (ex: primário, perigo, sucesso, processamento).
    """
    def __init__(self, master, text, command=None, variant="primary", **kwargs):
        """
        Construtor do StandardButton.

        Args:
            master: O widget pai.
            text: O texto a ser exibido no botão.
            command: A função a ser executada ao clicar.
            variant (str): O tipo de estilo do botão ('primary', 'danger', 'success', 'processing').
            **kwargs: Outros argumentos para sobrescrever o estilo padrão.
        """
        # Dicionário de estilos pré-definidos
        styles = {
            "primary": {
                "corner_radius": 8,
                "fg_color": "#3498db",      # Azul
                "hover_color": "#2980b9",
                "text_color": "#ffffff",
                "font": ("Roboto", 13)
            },
            "danger": {
                "corner_radius": 8,
                "fg_color": "#e74c3c",      # Vermelho
                "hover_color": "#c0392b",
                "text_color": "#ffffff",
                "font": ("Roboto", 13)
            },
            "success": {
                "corner_radius": 8,
                "fg_color": "#2ecc71",      # Verde
                "hover_color": "#27ae60",
                "text_color": "#ffffff",
                "font": ("Roboto", 13)
            },
            "processing": { # <-- A VARIANTE CORRETA ESTÁ AQUI
                "corner_radius": 8,
                "fg_color": "#FFA500",      # Laranja
                "hover_color": "#E69500",   # Laranja mais escuro
                "text_color": "#000000",    # Texto preto
                "font": ("Roboto", 13, "bold")
            }
        }

        # Seleciona o estilo com base na variante, ou usa 'primary' como padrão
        current_style = styles.get(variant, styles["primary"])

        # Atualiza o estilo selecionado com quaisquer argumentos extras passados
        final_style = {**current_style, **kwargs}

        # Chama o construtor da classe pai (ctk.CTkButton) com os parâmetros
        super().__init__(master=master, text=text, command=command, **final_style)


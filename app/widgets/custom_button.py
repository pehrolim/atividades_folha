# app/widgets/custom_button.py

import customtkinter as ctk

class StandardButton(ctk.CTkButton):
    """
    Uma classe de botão customizada que herda de CTkButton.
    Define estilos padrão através de "variantes" para diferentes
    tipos de botões (ex: primário, perigo, sucesso, processamento).
    """
    # Estilos definidos como um atributo de classe para serem reutilizados
    _styles = {
        "primary": {
            "fg_color": "#3498db", "hover_color": "#2980b9",
            "text_color": "#ffffff", "font": ("Roboto", 13)
        },
        "danger": {
            "fg_color": "#e74c3c", "hover_color": "#c0392b",
            "text_color": "#ffffff", "font": ("Roboto", 13)
        },
        "success": {
            "fg_color": "#2ecc71", "hover_color": "#27ae60",
            "text_color": "#ffffff", "font": ("Roboto", 13)
        },
        "processing": {
            "fg_color": "#FFA500", "hover_color": "#E69500",
            "text_color": "#000000", "font": ("Roboto", 13, "bold")
        }
    }

    def __init__(self, master, text, command=None, variant="primary", **kwargs):
        current_style = self._styles.get(variant, self._styles["primary"])
        final_style = {**current_style, **kwargs}
        super().__init__(master=master, text=text, command=command, **final_style)

    # --- MÉTODO NOVO ADICIONADO ---
    def configure_variant(self, variant: str):
        """
        Altera a aparência do botão com base em uma nova variante.

        Args:
            variant (str): O novo estilo a ser aplicado ('primary', 'danger', etc.).
        """
        try:
            new_style = self._styles[variant]
            self.configure(**new_style)
        except KeyError:
            print(f"Aviso: Variante de botão '{variant}' não reconhecida.")
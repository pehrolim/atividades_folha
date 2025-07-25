# app/widgets/styled_widgets.py
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt # <-- MUDANÇA AQUI: Importação adicionada

class StyledButton(QPushButton):
    """Um QPushButton com estilos pré-definidos para consistência."""
    
    STYLES = {
        "primary": "background-color: #3498db; color: white; border-radius: 5px; padding: 8px;",
        "success": "background-color: #2ecc71; color: white; border-radius: 5px; padding: 8px;",
        "danger": "background-color: #e74c3c; color: white; border-radius: 5px; padding: 8px;",
        "processing": "background-color: #FFA500; color: black; border-radius: 5px; padding: 12px;"
    }

    def __init__(self, text, variant="primary"):
        super().__init__(text)
        self.setStyleSheet(self.STYLES.get(variant, self.STYLES["primary"]))
        self.setFont(QFont("Roboto", 11))
        self.setCursor(Qt.PointingHandCursor) # Agora 'Qt' é reconhecido
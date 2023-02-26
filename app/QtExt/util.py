from PyQt6.QtWidgets import QLayout


def clear_layout(layout: QLayout) -> None:
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()

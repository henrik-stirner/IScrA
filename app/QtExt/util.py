from PyQt6.QtCore import Qt, QObject
from PyQt6.QtWidgets import QLayout, QLabel


def clear_layout(layout: QLayout) -> None:
    while layout.count():
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()


def get_text_of_child_labels(q_object: QObject, seperator: str = ' ') -> str:
    text = ''

    for label in q_object.findChildren(QLabel, options=Qt.FindChildOption.FindChildrenRecursively):
        text += f'{label.text()}{seperator}'

    return text

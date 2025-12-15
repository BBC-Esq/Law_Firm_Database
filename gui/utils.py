from PySide6.QtCore import QObject, QTimer, QEvent


class SpinBoxSelectAllFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            QTimer.singleShot(0, obj.selectAll)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)


def select_all_on_focus(spinbox):
    filter = SpinBoxSelectAllFilter(spinbox)
    spinbox.lineEdit().installEventFilter(filter)
    return filter
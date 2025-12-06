from gui.widgets.base_crud_widget import BaseCRUDWidget
from gui.dialogs.client_dialog import ClientDialog
from core.queries import ClientQueries

class ClientWidget(BaseCRUDWidget):
    entity_name = "Client"
    entity_name_plural = "Clients"
    column_headers = ["ID", "Last Name", "First Name", "Phone(s)", "Email(s)", "Address", "Billing Rate"]
    delete_warning = "Are you sure you want to delete this client? This will also delete all associated cases and billing entries."

    def __init__(self, client_queries: ClientQueries):
        super().__init__(client_queries)

    def item_to_row(self, client):
        return [
            str(client.id),
            client.last_name,
            client.first_name,
            client.phone or "",
            client.email or "",
            client.address or "",
            f"${client.billing_rate_cents / 100:.2f}"
        ]

    def get_dialog(self, client=None):
        return ClientDialog(self, client)

    def get_entity_from_dialog(self, dialog):
        return dialog.get_client()
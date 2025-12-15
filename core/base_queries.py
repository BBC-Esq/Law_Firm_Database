from typing import TypeVar, Generic, Optional, List, Type

T = TypeVar('T')


class BaseQueries(Generic[T]):
    table_name: str = ""
    model_class: Type[T] = None
    columns: str = "*"
    order_by: str = "id"

    def __init__(self, db):
        self.db = db

    def delete(self, id: int):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE id=?", (id,))

    def get_by_id(self, id: int) -> Optional[T]:
        row = self.db.fetchone(
            f"SELECT {self.columns} FROM {self.table_name} WHERE id=?", (id,)
        )
        return self.model_class(**dict(row)) if row else None

    def get_all(self) -> List[T]:
        rows = self.db.fetchall(
            f"SELECT {self.columns} FROM {self.table_name} ORDER BY {self.order_by}"
        )
        return [self.model_class(**dict(row)) for row in rows]
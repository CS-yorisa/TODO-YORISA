from ninja import Schema


class TodoCreate(Schema):
    title: str
    description: str = ""
    status: str = "todo"
    category: int | None = None


class TodoPatch(Schema):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    category: int | None = None


class TodoList(Schema):
    id: int
    title: str
    description: str
    status: str
    category: int | None
    member: int | None

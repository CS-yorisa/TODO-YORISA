from ninja import Schema


class CategoryCreate(Schema):
    name: str


class CategoryPatch(Schema):
    name: str | None = None


class CategoryOut(Schema):
    id: int
    name: str
    member_id: int | None


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
    category_id: int | None
    member_id: int | None

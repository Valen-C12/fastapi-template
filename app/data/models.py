from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.data.database import Base


class User(Base):  # 假设我们有一个 User 模型用于演示关系
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    items: Mapped[list["Item"]] = relationship(back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    # --- 基础用法 ---
    # Python 类型是 int，数据库列是主键
    id: Mapped[int] = mapped_column(primary_key=True)

    # Python 类型是 str，数据库列是 VARCHAR(255)，并建了索引
    title: Mapped[str] = mapped_column(String(255), index=True)

    # --- 处理可选/可空字段 ---
    # Python 类型是 str 或 None，数据库列是 TEXT，可以为 NULL
    # 如果不指定数据库类型，SQLAlchemy 会根据 Python 类型推断
    description: Mapped[str | None] = mapped_column()

    # --- 处理带默认值的字段 ---
    # Python 类型是 bool，数据库列是 BOOLEAN，默认值为 True，使用text是跨数据库写法，且避免旧数据报错无法升级
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))

    # --- 处理外键和关系 ---
    # Python 类型是 int 或 None，数据库列是外键
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # 这是一个关系属性，它在数据库中没有对应的列！
    # Python 类型是一个 User 实例，或者 None
    # 它只存在于 ORM层面，用于方便地访问关联对象
    owner: Mapped[User | None] = relationship(back_populates="items")

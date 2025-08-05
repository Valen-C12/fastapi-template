from typing import Optional, TypeVar

from pydantic import BaseModel, create_model

# 定义一个类型变量，用于表示任何 Pydantic 基类
BaseSchemaType = TypeVar("BaseSchemaType", bound=BaseModel)


def create_dynamic_schemas(base_schema: type[BaseSchemaType]):
    """
    一个工厂函数，根据一个 Base Schema 动态创建 Create, Read, 和 Update Schemas。
    使用 Python 3.10+ 的联合类型语法。
    """

    # --- 1. 创建 Create Schema ---
    # 通常 Create Schema 与 Base Schema 相同，或增加字段。
    # 在这个简单工厂里，我们假设它与 Base 相同。
    create_schema = base_schema

    # --- 2. 创建 Update Schema ---
    # Update Schema 的所有字段都应该是可选的。
    update_fields = {}
    for field_name, field_info in base_schema.model_fields.items():
        # 获取原始的类型注解
        original_type = field_info.annotation

        # 使用 typing.Optional 将其变为可选类型
        # e.g., str -> Optional[str]
        # e.g., int -> Optional[int]
        optional_type = Optional[original_type]  # noqa: UP045

        # 将新类型和默认值 None 添加到字典中
        update_fields[field_name] = (optional_type, None)

    # 使用 Pydantic 的 create_model 动态创建一个新类
    update_schema = create_model(
        f"{base_schema.__name__}Update",
        **update_fields,
        __base__=BaseModel,  # 确保它是一个 Pydantic 模型
    )

    # --- 3. 创建 Read Schema ---
    # Read Schema 通常在 Base Schema 的基础上增加一个 id 字段。
    read_schema = create_model(
        f"{base_schema.__name__}Read",
        id=(int, ...),  # 添加一个必需的 id 字段
        __base__=base_schema,  # 继承自 Base Schema
    )
    read_schema.model_config = {"from_attributes": True}

    return create_schema, update_schema, read_schema

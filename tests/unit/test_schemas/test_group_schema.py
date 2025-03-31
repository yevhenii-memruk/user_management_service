from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas.group import GroupBase, GroupCreate, GroupInDB


class TestGroupBase:
    def test_valid_group_base(self) -> None:
        data = {"name": "Test Group"}
        group = GroupBase(**data)
        assert group.name == data["name"]

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            ("", "String should have at least 1 character"),
            ("a" * 101, "String should have at most 100 characters"),
        ],
    )
    def test_invalid_group_name(self, value: str, expected_error: str) -> None:
        with pytest.raises(ValidationError) as exc_info:
            GroupBase(name=value)
        assert expected_error in str(exc_info.value)


class TestGroupCreate:
    def test_group_create_same_as_base(self) -> None:
        data = {"name": "Test Group"}
        group_base = GroupBase(**data)
        group_create = GroupCreate(**data)
        assert group_create.name == group_base.name


class TestGroupInDB:
    def test_valid_group_in_db(self) -> None:
        data = {"name": "Test Group", "id": 1, "created_at": datetime.now()}
        group = GroupInDB(**data)
        assert group.name == data["name"]
        assert group.id == data["id"]
        assert isinstance(group.created_at, datetime)

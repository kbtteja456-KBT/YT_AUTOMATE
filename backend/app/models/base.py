"""Base models and ObjectId handling for MongoDB documents."""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId


class PyObjectId(str):
    """Custom type to serialize/deserialize BSON ObjectId cleanly in Pydantic v2."""
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        from pydantic_core import core_schema

        def validate(val: Any) -> str:
            if isinstance(val, ObjectId):
                return str(val)
            if isinstance(val, str) and ObjectId.is_valid(val):
                return val
            if isinstance(val, str):
                return val
            raise ValueError(f"Invalid ObjectId: {val}")

        return core_schema.no_info_plain_validator_function(validate)


class MongoBaseModel(BaseModel):
    """Base model for all MongoDB persisted documents with standard timestamps."""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_mongo_dict(self) -> dict[str, Any]:
        """Convert model to MongoDB-compatible dictionary."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is not None:
            if isinstance(data["_id"], str) and ObjectId.is_valid(data["_id"]):
                data["_id"] = ObjectId(data["_id"])
        return data

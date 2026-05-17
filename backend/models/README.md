# `backend/models/`

Pydantic models for request validation, response serialization, and Mongo document shapes.

## Convention

Per domain, split into three classes:

```python
# models/listing.py
class ListingBase(BaseModel):       # shared fields
    title: str
    price_pkr: int

class ListingCreate(ListingBase):   # incoming payload
    pass

class ListingOut(ListingBase):      # outgoing payload (response_model)
    id: str
    created_at: datetime
```

- Use `model_config = ConfigDict(extra="forbid")` on incoming models to reject unknown fields.
- Keep Mongo `_id` out of `*Out` models — map to `id` explicitly.

See [`/DOCS/architecture.md`](../../DOCS/architecture.md) for the canonical entity diagram.

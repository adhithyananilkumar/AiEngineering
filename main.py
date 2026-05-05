from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


items = {}
next_id = 1


class Item(BaseModel):
    name: str
    description: str | None = None



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/items")
async def create_item(item: Item):
    global next_id
    item_dict = {"id": next_id, **item.dict()}
    items[next_id] = item_dict
    next_id += 1
    return item_dict


@app.get("/items")
async def get_items():
    return list(items.values())


app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = {"id": item_id, **item.dict()}
    items[item_id] = updated
    return updated



@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    deleted = items.pop(item_id)
    return {"message": "Deleted successfully", "item": deleted}
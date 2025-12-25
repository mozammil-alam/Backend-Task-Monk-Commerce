from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()


data_store: Dict[str, Any] = {}
cart_wise_dict = {}
product_wise_dict = {}
total_price = 0
bxgy_list = []

def calculate_cart_total_price(items):
    return sum(item['price'] * item['quantity'] for item in items)

def calculate_bxgy_discount(items, coupon):
    buy_rules = coupon['details']['buy_products']
    get_rules = coupon['details']['get_products']
    limit = coupon['details'].get('repetition_limit', 1)

    cart_map = {}
    for item in items:
        product_id = item['product_id']
        cart_map[product_id] = cart_map.get(product_id, 0) + item['quantity']

    buy_count_possible = float("inf")
    for rule in buy_rules:
        product_id = rule['product_id']
        needed_per_cycle = rule["quantity"]
        available = cart_map.get(product_id, 0)
        cycles_for_product = available // needed_per_cycle
        buy_count_possible = min(buy_count_possible, cycles_for_product)

    if buy_count_possible <= 0:
        return 0
    
    repeat_times = min(buy_count_possible, limit)

    discount = 0
    for rule in get_rules:
        product_id = rule['product_id']
        free_qty = rule['quantity'] * repeat_times
        cart_item = next((x for x in items if x['product_id']== product_id), None)
        if cart_item:
            discount += cart_item['price'] * free_qty

    return discount

def find_applicable_coupons(items):
    applicable = []
    total_price = calculate_cart_total_price(items)

    for item in items:
        product_id, qty, price = item['product_id'], item['quantity'], item['price']
        if product_id in product_wise_dict:
            coupon = product_wise_dict[product_id]
            d = (price * qty) * coupon['details']['discount']/100
            applicable.append({
                "coupon_id" : coupon['id'],
                "type" : "product-wise",
                "discount" : d
            })

    for thr, coupon in cart_wise_dict.items():
        if total_price >= thr:
            d = (total_price * coupon['details']['discount'])/100
            applicable.append({
                "coupon_id" : coupon['id'],
                "type" : "cart-wise",
                "discount" : d
            })

    for coupon in bxgy_list:
        d = calculate_bxgy_discount(items, coupon)
        if d > 0 :
            applicable.append({
                "coupon_id" : coupon['id'],
                "type" : "bxgy",
                "discount" : d
            })
    
    return applicable

@app.post("/coupons")
def store_data(json_body: Dict[str, Any] = Body(...)):
    record_id = str(json_body['id']) 
    if  record_id in data_store:
        raise HTTPException(status_code=404, detail = "Coupon with same id already exists!")
    data_store[record_id] = json_body
    if('details' in json_body):
        if('threshold' in json_body['details']):
            cart_wise_dict[json_body['details']['threshold']] = json_body
        elif('product_id' in json_body['details']):
            product_wise_dict[json_body['details']['product_id']] = json_body
        else:
            bxgy_list.append(json_body)
    
    return {"message": "Coupon stored successfully", "stored": data_store[record_id]}


@app.get("/coupons")
def compute_data():
    return data_store

@app.get("/coupons/{record_id}")
def compute_data(record_id):
    print(data_store)
    return data_store[str(record_id)]

@app.put("/coupons/{record_id}")
def compute_data(record_id, json_body: Dict[str, Any] = Body(...)):
    data_store[str(record_id)] = json_body
    return data_store[str(record_id)]

@app.delete("/coupons/{record_id}")
def compute_data(record_id):
    if record_id not in data_store:
        raise HTTPException(status_code=404, detail="Coupon not found")
    removed = data_store.pop(record_id)
    if 'threshold' in removed['details']:
        cart_wise_dict.pop(removed['details']['threshold'], None)
    elif 'product_id' in removed['details']:
        product_wise_dict.pop(removed['details']['product_id'], None)
    else:
        bxgy_list.remove(removed)
    return {"deleted": removed}

@app.post("/applicable-coupons")
def store_data(json_body: Dict[str, Any] = Body(...)):
    items = json_body["cart"]["items"]
    return find_applicable_coupons(items)

@app.post("/apply-coupon/{record_id}")
def apply_coupon(record_id: str, json_body: Dict[str, Any] = Body(...)):
    if record_id not in data_store:
        raise HTTPException(status_code=404, detail="Coupon not found")
    coupon = data_store[record_id]
    items = json_body["cart"]["items"]
    total_price_before = calculate_cart_total_price(items)
    total_discount = 0
    
    updated_items = [dict(i) for i in items]

    if coupon["type"] == "product-wise":
        pid = coupon["details"]["product_id"]
        percent = coupon["details"]["discount"]
        for item in updated_items:
            if item["product_id"] == pid:
                discount_amt = (item["price"] * item["quantity"]) * percent / 100
                item["total_discount"] = discount_amt
                total_discount += discount_amt

    elif coupon["type"] == "cart-wise":
        threshold = coupon["details"]["threshold"]
        percent = coupon["details"]["discount"]

        if total_price_before >= threshold:
            total_discount = (total_price_before * percent) / 100
        for item in updated_items:
            item["total_discount"] = 0

    elif coupon["type"] == "bxgy":
        buy_rules = coupon["details"]["buy_products"]
        get_rules = coupon["details"]["get_products"]
        limit = coupon["details"].get("repetition_limit", 1)

        cart_map = {}
        for item in updated_items:
            pid = item["product_id"]
            cart_map[pid] = cart_map.get(pid, 0) + item["quantity"]

        buy_cycles = float("inf")
        for rule in buy_rules:
            pid = rule["product_id"]
            needed = rule["quantity"]
            available = cart_map.get(pid, 0)
            buy_cycles = min(buy_cycles, available // needed)

        if buy_cycles > 0:
            repeat_times = min(buy_cycles, limit)

            for rule in get_rules:
                pid = rule["product_id"]
                free_qty = rule["quantity"] * repeat_times

                for item in updated_items:
                    if item["product_id"] == pid:
                        free_total = item["price"] * free_qty
                        item["total_discount"] = free_total + item.get("total_discount", 0)
                        total_discount += free_total

                        item["quantity"] += free_qty
    for item in updated_items:
        if "total_discount" not in item:
            item["total_discount"] = 0

    final_price = total_price_before - total_discount

    return {
        "updated_cart": {
            "items": updated_items,
            "total_price": total_price_before,
            "total_discount": total_discount,
            "final_price": final_price
        }
    }

    

@app.get("/")
def home():
    return {"message": "FastAPI is running!"}
# Backend-Task-Monk-Commerce


This project implements a coupon management engine for an e-commerce platform.
It supports multiple coupon types, evaluates eligibility, and applies pricing logic
to cart items.

The goal is to design a scalable system that allows new coupon types to be added
easily in the future.


Features Implemented

Cart-wise Coupons  
Apply a percentage discount to the entire cart total when a threshold is met.

Product-wise Coupons  
Apply percentage discount in the cart.

BxGy Coupons (Buy X Get Y Free) — FULL Implementation
Supports:
-	Multiple BUY product IDs
-	Multiple GET product IDs
-	Combined buy quantities
-	Repetition limit (b1g1, b2g1, b3g2 etc.)
-	Product price-based discount
-	Adds free quantity to cart during `/apply-coupon`


Architecture & Data Structure

All coupons are stored in-memory for simplicity:
-	`data_store` → master dictionary of all coupons
-	`cart_wise_dict` → lookup for cart-wise coupons
-	`product_wise_dict` → lookup for product coupons
-	`bxgy_list` → list for BxGy coupons

API Endpoints

POST - /coupons -Create coupon 
GET - /coupons - List all coupons 
GET - /coupons/{id} - Get a coupon 
PUT  - /coupons/{id} - Update coupon 
DELETE - /coupons/{id} - Delete coupon 
POST - /applicable-coupons - Return list of all coupons that apply to a cart 
POST  - /apply-coupon/{id} - Apply a specific coupon and return cart after discount 



Assumptions
-	Cart is valid and contains product_id, price, and quantity
-	All discounts are percentage-based except BxGy which is free-item based
-	GET products must exist in cart to provide value
-	Coupons do not expire unless deleted
-	No stacking rules enforced — all valid coupons are returned
-	Apply endpoint applies only one selected coupon

Known Limitations
-	Data resets on server restart (no persistent DB)
-	No coupon expiry, usage count, or customer history
-	Discounts are not capped
-	System does not resolve conflicts when multiple coupons apply
-	BxGy only counts GET items present in cart

Future Enhancements
-	Database support (MongoDB or Postgres)
-	Coupon priority and exclusivity rules
-	Max discount caps
-	Coupon expiry dates and scheduling
-	Customer-specific restrictions
-	Category-based coupon filtering
-	Bulk cart-level coupon stacking backend logic

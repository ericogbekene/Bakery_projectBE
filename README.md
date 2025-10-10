### Bakery Project Backend (Django + DRF)

Backend API for an e‑commerce bakery store. It exposes endpoints for browsing categories and products, managing a session cart, placing orders, and handling payments. Authentication uses JWT; API documentation is available via Swagger UI.

## Tech Stack
- Django, Django REST Framework
- JWT auth via `rest_framework_simplejwt`
- Filtering, search, ordering via `django-filter` and DRF filters
- Pagination: PageNumberPagination (default page size 20)
- Media storage: Cloudinary
- API docs: drf-yasg (Swagger / Redoc)

## Authentication
- JWT is the default authentication method.
- Obtain tokens at `POST /api/accounts/login/` (access + refresh).
- Include the token in requests:
  - `Authorization: Bearer <access_token>`

Public endpoints support anonymous read. Sensitive actions (e.g., stock updates, bulk operations) require authentication and can be further restricted to staff/admin if desired.

## Core Concepts and Logic
- Categories and Products are exposed via DRF `ModelViewSet`s with `slug` lookups.
- Search and filtering: products can be queried by name/description, category, price range, and stock state.
- Stock logic (on the `Product` model):
  - `is_in_stock()` and `is_low_stock()` derive from `track_inventory`, `stock_quantity`, and `low_stock_threshold`.
  - Write actions like `update_stock` run in a transaction; consider row locking (`select_for_update`) for high contention scenarios.
- Pagination is enabled for list and search endpoints; default page size is 20.
- Images: Cloudinary-backed URLs (original, thumbnail, medium, large) are exposed as read-only fields in list/detail serializers.

## API Base URLs
- API root: `/api/`
- Swagger UI: `/` (root path)
- Swagger JSON: `/swagger<format>/` (e.g., `/swagger.json`)

## Accounts (Auth)
- `POST /api/accounts/register/` — create account
- `POST /api/accounts/login/` — obtain JWT pair
- `POST /api/accounts/password-reset/request/` — start password reset
- `POST /api/accounts/password-reset/confirm/` — confirm password reset
- `GET  /api/accounts/verify-email/<token>/` — verify email

## Products & Categories
Mounted under `/api/products/` with a DRF router.

### Categories
- `GET  /api/products/categories/` — list categories (search `?search=...`, order `?ordering=name`)
- `POST /api/products/categories/` — create category (auth)
- `GET  /api/products/categories/<slug>/` — retrieve category detail
- `PUT/PATCH /api/products/categories/<slug>/` — update (auth)
- `DELETE /api/products/categories/<slug>/` — delete (auth)
- `GET  /api/products/categories/<slug>/products/` — products in category
  - Filters: `?min_price=...&max_price=...&in_stock=true`
- `GET  /api/products/categories/<slug>/stats/` — counts, average price, stock stats

Query params (list):
- `?has_products=true|false` — filter categories by whether they contain products

### Products
- `GET  /api/products/products/` — list products
- `POST /api/products/products/` — create product (auth)
- `GET  /api/products/products/<slug>/` — retrieve product detail
- `PUT/PATCH /api/products/products/<slug>/` — update (auth)
- `DELETE /api/products/products/<slug>/` — delete (auth)

Custom actions:
- `GET  /api/products/products/search/?q=...` — search products
  - Optional: `&category_slug=...&min_price=...&max_price=...`
- `POST /api/products/products/<slug>/update_stock/` — increase/decrease/set stock (auth)
  - Body: `{ "action": "increase|decrease|set", "quantity": <int>, "reason": "..." }`
- `POST /api/products/products/bulk_update/` — activate/deactivate/delete/update_category (auth)
  - Body: `{ "product_ids": [1,2], "action": "activate|deactivate|delete|update_category", "category_id": 3 }`
- `GET  /api/products/products/low_stock/` — low stock products
- `GET  /api/products/products/out_of_stock/` — out of stock products
- `GET  /api/products/products/featured/` — featured products (latest available)
- `GET  /api/products/products/<slug>/related/` — related by category

Query params (list):
- `?min_price=...&max_price=...`
- `?in_stock=true|false`
- `?low_stock=true`
- `?category_slug=<slug>`
- `?search=...` (DRF SearchFilter on name/description)
- `?ordering=name|price|created_at|stock_quantity` (prefix with `-` for desc)

Pagination:
- `?page=<n>`; default page size is 20

## Cart
Mounted under `/api/cart/`.

- `POST /api/cart/cart/add/` — add or update line items
- `POST /api/cart/cart/remove/` — remove a line item
- `GET  /api/cart/cart/` — current cart details
- `POST /api/cart/cart/clear/` — clear cart

Note: these endpoints are session-based (server-side session key `CART_SESSION_ID`).

## Orders
Mounted under `/api/orders/`.

- `POST /api/orders/create/` — create an order from the current cart
- `GET  /api/orders/<order_id>/` — retrieve order summary

## Payments (Paystack)
Mounted under `/api/payments/`.

- `POST /api/payments/initialize/` — initialize payment
- `GET  /api/payments/verify/<reference>/` — verify transaction
- `POST /api/payments/refund/<reference>/` — refund transaction
- `POST /api/payments/webhook/` — Paystack webhook endpoint

## Error Handling & Responses
- Standard DRF error responses with 4xx/5xx codes.
- Validation errors include field-specific messages.

## Running Locally (Quickstart)
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Authors
- Ogbekene Eric
- Ogbu Cyprian
- Ebube Anywanwu
- Hanifah Ali

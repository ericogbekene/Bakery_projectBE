# Cart Application API Documentation

This document outlines the core functionality of the `cart` Django application's API, focusing on the "add to cart" and "checkout" processes. It provides details on the most important endpoints, expected payloads, and a basic setup for frontend consumption.

## Core Cart Functionality Overview

The `cart` application is responsible for managing a user's shopping cart. It primarily utilizes session-based logic (implemented in `cart/cart.py`) to store cart contents. The application exposes a RESTful API for various cart operations.

## Most Important Endpoints & Payloads

Below are the key API endpoints relevant to the "add to cart" and "checkout" flow:

### 1. Add Product to Cart

*   **Endpoint:** `POST /api/cart/add_to_cart/`
*   **Purpose:** This endpoint allows you to add a specified quantity of a product to the user's shopping cart. If the product is already in the cart, its quantity will be updated accordingly.
*   **Authentication:** Not explicitly required by the `CartViewSet` for this action, but typically, cart operations might be associated with a session or a user.
*   **Expected Payload (JSON Body):**
    ```json
    {
        "product_id": <integer>,  // **Required:** The unique identifier of the product to be added.
        "quantity": <integer>     // **Required:** The quantity of the product to add.
    }
    ```
*   **Example Request (using `curl`):
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -H "X-CSRFToken: <your_csrf_token>" \
         -d '{"product_id": 123, "quantity": 1}' \
         http://localhost:8000/api/cart/add_to_cart/
    ```
*   **Expected Response (Success - JSON):**
    ```json
    {
        "id": 1,
        "product": {
            "id": 123,
            "name": "Example Product",
            "price": "10.00"
        },
        "quantity": 1,
        "total_price": "10.00"
    }
    ```
    *   *Note: The exact response structure might vary based on `CartItemSerializer`.*

### 2. Retrieve Cart Contents

*   **Endpoint:** `GET /api/cart/`
*   **Purpose:** This endpoint allows you to fetch the current contents of the user's shopping cart. It provides a comprehensive overview, including all individual cart items, the total price of all items, and the total count of distinct items.
*   **Authentication:** Not explicitly required by the `CartViewSet` for this action.
*   **Expected Payload:** None (This is a GET request, so no request body is sent).
*   **Example Request (using `curl`):
    ```bash
    curl -X GET http://localhost:8000/api/cart/
    ```
*   **Expected Response (Success - JSON):**
    ```json
    {
        "cart_items": [
            {
                "id": 1,
                "product": {
                    "id": 123,
                    "name": "Example Product",
                    "price": "10.00"
                },
                "quantity": 1,
                "total_price": "10.00"
            },
            {
                "id": 2,
                "product": {
                    "id": 456,
                    "name": "Another Product",
                    "price": "25.50"
                },
                "quantity": 2,
                "total_price": "51.00"
            }
        ],
        "total_price": "61.00",
        "total_items": 2
    }
    ```
    *   *Note: The `product` object within `cart_items` will contain details serialized by `ProductListSerializer`.*

### 3. Checkout

*   **Endpoint:** `POST /api/cart/checkout/`
*   **Purpose:** This endpoint initiates the order creation process. It converts the current contents of the user's shopping cart into a formal order. This action typically requires the user to be authenticated.
*   **Authentication:** **Required** (`IsAuthenticated` permission class is applied to `CartCheckoutView`). You must send a valid authentication token (e.g., JWT) in the `Authorization` header.
*   **Expected Payload:** None. The backend relies on the authenticated user's session cart to create the order. No request body is needed.
*   **Example Request (using `curl`):
    ```bash
    curl -X POST -H "Content-Type: application/json" \
         -H "Authorization: Bearer <your_jwt_token>" \
         -H "X-CSRFToken: <your_csrf_token>" \
         http://localhost:8000/api/cart/checkout/
    ```
*   **Expected Response (Success - JSON):**
    ```json
    {
        "detail": "Checkout successful!",
        "order_id": 12345
    }
    ```
    *   *Note: In a full production environment, this step would typically integrate with a payment gateway (like Paystack, as configured in `settings.py`). The cart would only be cleared upon successful payment processing.*

## Frontend Consumption Setup

To effectively interact with the `cart` API from your frontend application, consider the following:

1.  **API Base URL:**
    *   All cart-related API endpoints are rooted under `/api/cart/`. For example, to add to cart, you would target `YOUR_BACKEND_URL/api/cart/add_to_cart/`.

2.  **Authentication (for protected endpoints):**
    *   For endpoints that require authentication (e.g., `/api/cart/checkout/`), you must include an `Authorization` header in your HTTP requests.
    *   If using JWTs (as indicated by `rest_framework_simplejwt` in `settings.py`), the header format is:
        `Authorization: Bearer <your_json_web_token>`
    *   Ensure your frontend securely stores and retrieves the JWT after user login.

3.  **CSRF Token Handling (for state-changing requests):**
    *   Django's `CsrfViewMiddleware` is active, meaning `POST`, `PUT`, `PATCH`, and `DELETE` requests require a CSRF token.
    *   **How to get the token:** Django typically sets a `csrftoken` cookie in the user's browser. Your frontend JavaScript can read this cookie.
    *   **How to send the token:** Include the token in your request headers as `X-CSRFToken`.
    *   **Example (JavaScript Fetch API):**
        ```javascript
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        const csrftoken = getCookie('csrftoken');

        fetch('http://localhost:8000/api/cart/add_to_cart/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                // 'Authorization': 'Bearer <your_jwt_token>' // Include if endpoint requires authentication
            },
            body: JSON.stringify({
                product_id: 123,
                quantity: 1
            })
        })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.error('Error:', error));
        ```

## End-to-End Frontend Flow Example

Here's a conceptual flow for how a frontend application would interact with the `cart` API:

1.  **User Browses Products:**
    *   The frontend fetches product data from the `/api/products/` endpoint (from the `products` app).

2.  **User Adds Item to Cart:**
    *   When a user clicks an "Add to Cart" button, the frontend constructs a JSON payload with `product_id` and `quantity`.
    *   It then sends a `POST` request to `/api/cart/add_to_cart/`.
    *   The frontend updates its UI (e.g., cart icon, notification) based on the API response.

3.  **User Views Shopping Cart:**
    *   When the user navigates to their cart page, the frontend sends a `GET` request to `/api/cart/`.
    *   The received cart data is then rendered to display the current items, quantities, and totals.

4.  **User Proceeds to Checkout:**
    *   The frontend ensures the user is authenticated (e.g., by checking for a valid JWT).
    *   A `POST` request is sent to `/api/cart/checkout/`. No request body is typically needed, as the backend will use the session cart associated with the authenticated user.
    *   The frontend handles the API response:
        *   On success, it might redirect the user to an order confirmation page or a payment gateway.
        *   On failure, it displays an appropriate error message.

This documentation should serve as a comprehensive guide for integrating your frontend with the `cart` application's API.

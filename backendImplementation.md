# Frontend Implementation Guide for Bakery API

This comprehensive guide provides detailed examples for consuming the Bakery API (`api.mandccakes.com`) from frontend applications. It covers authentication, product management, cart operations, checkout, and error handling.

## Table of Contents
1. [API Configuration](#api-configuration)
2. [Authentication](#authentication)
3. [Products & Categories](#products--categories)
4. [Cart Management](#cart-management)
5. [Orders & Checkout](#orders--checkout)
6. [Error Handling](#error-handling)
7. [Complete Examples](#complete-examples)

## API Configuration

### Base Configuration
```javascript
// config/api.js
const API_CONFIG = {
  BASE_URL: 'https://api.mandccakes.com/api',
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/accounts/login/',
      REGISTER: '/accounts/register/',
      REFRESH: '/accounts/token/refresh/',
    },
    PRODUCTS: {
      LIST: '/products/products/',
      DETAIL: '/products/products/',
      SEARCH: '/products/products/search/',
      FEATURED: '/products/products/featured/',
      LOW_STOCK: '/products/products/low_stock/',
    },
    CATEGORIES: {
      LIST: '/products/categories/',
      DETAIL: '/products/categories/',
    },
    CART: {
      ADD: '/cart/cart/add/',
      REMOVE: '/cart/cart/remove/',
      LIST: '/cart/cart/',
      CLEAR: '/cart/cart/clear/',
    },
    ORDERS: {
      CREATE: '/orders/create/',
      DETAIL: '/orders/',
    },
    PAYMENTS: {
      INITIALIZE: '/payments/initialize/',
      VERIFY: '/payments/verify/',
    }
  }
};

export default API_CONFIG;
```

### HTTP Client Setup
```javascript
// utils/httpClient.js
import API_CONFIG from '../config/api';

class HttpClient {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  getHeaders(includeAuth = true) {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (includeAuth && this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getHeaders(options.requireAuth !== false),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(response.status, errorData, response.statusText);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(0, {}, 'Network error or request failed');
    }
  }

  // Convenience methods
  async get(endpoint, options = {}) {
    return this.request(endpoint, { method: 'GET', ...options });
  }

  async post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
      ...options,
    });
  }

  async put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
      ...options,
    });
  }

  async patch(endpoint, data, options = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
      ...options,
    });
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { method: 'DELETE', ...options });
  }
}

// Custom error class
class APIError extends Error {
  constructor(status, data, message) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'APIError';
  }
}

export const httpClient = new HttpClient();
export { APIError };
```

## Authentication

### Login Implementation
```javascript
// services/authService.js
import { httpClient } from '../utils/httpClient';
import API_CONFIG from '../config/api';

class AuthService {
  async login(email, password) {
    try {
      const response = await httpClient.post(API_CONFIG.ENDPOINTS.AUTH.LOGIN, {
        email,
        password,
      });

      // Store tokens
      httpClient.setToken(response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      return {
        success: true,
        user: response.user,
        tokens: {
          access: response.access,
          refresh: response.refresh,
        },
      };
    } catch (error) {
      return {
        success: false,
        error: this.handleAuthError(error),
      };
    }
  }

  async register(userData) {
    try {
      const response = await httpClient.post(API_CONFIG.ENDPOINTS.AUTH.REGISTER, {
        email: userData.email,
        password: userData.password,
        first_name: userData.firstName,
        last_name: userData.lastName,
      });

      return {
        success: true,
        message: 'Registration successful. Please check your email for verification.',
      };
    } catch (error) {
      return {
        success: false,
        error: this.handleAuthError(error),
      };
    }
  }

  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await httpClient.post(API_CONFIG.ENDPOINTS.AUTH.REFRESH, {
        refresh: refreshToken,
      });

      httpClient.setToken(response.access);
      return response.access;
    } catch (error) {
      this.logout();
      throw error;
    }
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    httpClient.setToken(null);
  }

  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  }

  handleAuthError(error) {
    if (error.status === 401) {
      return 'Invalid credentials';
    } else if (error.status === 400) {
      return error.data.detail || 'Invalid request data';
    } else if (error.status === 0) {
      return 'Network error. Please check your connection.';
    }
    return 'Authentication failed';
  }
}

export const authService = new AuthService();
```

### React Authentication Hook
```javascript
// hooks/useAuth.js
import { useState, useEffect, createContext, useContext } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (authService.isAuthenticated()) {
        try {
          // You might want to fetch user profile here
          setUser({ authenticated: true });
        } catch (error) {
          authService.logout();
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const result = await authService.login(email, password);
    if (result.success) {
      setUser({ authenticated: true });
    }
    return result;
  };

  const register = async (userData) => {
    return await authService.register(userData);
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      isAuthenticated: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

## Products & Categories

### Product Service
```javascript
// services/productService.js
import { httpClient } from '../utils/httpClient';
import API_CONFIG from '../config/api';

class ProductService {
  // Get all products with filtering and pagination
  async getProducts(filters = {}) {
    const queryParams = new URLSearchParams();
    
    // Apply filters
    if (filters.search) queryParams.append('search', filters.search);
    if (filters.category) queryParams.append('category_slug', filters.category);
    if (filters.minPrice) queryParams.append('min_price', filters.minPrice);
    if (filters.maxPrice) queryParams.append('max_price', filters.maxPrice);
    if (filters.inStock !== undefined) queryParams.append('in_stock', filters.inStock);
    if (filters.ordering) queryParams.append('ordering', filters.ordering);
    if (filters.page) queryParams.append('page', filters.page);

    const endpoint = `${API_CONFIG.ENDPOINTS.PRODUCTS.LIST}?${queryParams}`;
    return await httpClient.get(endpoint);
  }

  // Get single product by slug
  async getProduct(slug) {
    return await httpClient.get(`${API_CONFIG.ENDPOINTS.PRODUCTS.DETAIL}${slug}/`);
  }

  // Search products
  async searchProducts(query, filters = {}) {
    const queryParams = new URLSearchParams({ q: query });
    
    if (filters.category) queryParams.append('category_slug', filters.category);
    if (filters.minPrice) queryParams.append('min_price', filters.minPrice);
    if (filters.maxPrice) queryParams.append('max_price', filters.maxPrice);

    const endpoint = `${API_CONFIG.ENDPOINTS.PRODUCTS.SEARCH}?${queryParams}`;
    return await httpClient.get(endpoint);
  }

  // Get featured products
  async getFeaturedProducts() {
    return await httpClient.get(API_CONFIG.ENDPOINTS.PRODUCTS.FEATURED);
  }

  // Get related products
  async getRelatedProducts(slug) {
    return await httpClient.get(`${API_CONFIG.ENDPOINTS.PRODUCTS.DETAIL}${slug}/related/`);
  }

  // Get low stock products (admin only)
  async getLowStockProducts() {
    return await httpClient.get(API_CONFIG.ENDPOINTS.PRODUCTS.LOW_STOCK, {
      requireAuth: true,
    });
  }
}

export const productService = new ProductService();
```

### Category Service
```javascript
// services/categoryService.js
import { httpClient } from '../utils/httpClient';
import API_CONFIG from '../config/api';

class CategoryService {
  // Get all categories
  async getCategories(filters = {}) {
    const queryParams = new URLSearchParams();
    
    if (filters.search) queryParams.append('search', filters.search);
    if (filters.hasProducts !== undefined) {
      queryParams.append('has_products', filters.hasProducts);
    }
    if (filters.ordering) queryParams.append('ordering', filters.ordering);

    const endpoint = `${API_CONFIG.ENDPOINTS.CATEGORIES.LIST}?${queryParams}`;
    return await httpClient.get(endpoint);
  }

  // Get single category by slug
  async getCategory(slug) {
    return await httpClient.get(`${API_CONFIG.ENDPOINTS.CATEGORIES.DETAIL}${slug}/`);
  }

  // Get products in category
  async getCategoryProducts(slug, filters = {}) {
    const queryParams = new URLSearchParams();
    
    if (filters.minPrice) queryParams.append('min_price', filters.minPrice);
    if (filters.maxPrice) queryParams.append('max_price', filters.maxPrice);
    if (filters.inStock !== undefined) queryParams.append('in_stock', filters.inStock);

    const endpoint = `${API_CONFIG.ENDPOINTS.CATEGORIES.DETAIL}${slug}/products/?${queryParams}`;
    return await httpClient.get(endpoint);
  }

  // Get category statistics
  async getCategoryStats(slug) {
    return await httpClient.get(`${API_CONFIG.ENDPOINTS.CATEGORIES.DETAIL}${slug}/stats/`);
  }
}

export const categoryService = new CategoryService();
```

### React Product Components
```javascript
// components/ProductList.jsx
import React, { useState, useEffect } from 'react';
import { productService } from '../services/productService';
import ProductCard from './ProductCard';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

const ProductList = ({ filters = {} }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    loadProducts();
  }, [filters]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await productService.getProducts(filters);
      
      if (response.results) {
        // Paginated response
        setProducts(response.results);
        setPagination({
          current: response.current_page,
          total: response.total_pages,
          count: response.count,
        });
      } else {
        // Non-paginated response
        setProducts(response);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} onRetry={loadProducts} />;

  return (
    <div className="product-list">
      <div className="products-grid">
        {products.map(product => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
      
      {pagination && (
        <Pagination 
          current={pagination.current}
          total={pagination.total}
          onPageChange={(page) => loadProducts({ ...filters, page })}
        />
      )}
    </div>
  );
};

export default ProductList;
```

```javascript
// components/ProductCard.jsx
import React from 'react';
import { useCart } from '../hooks/useCart';

const ProductCard = ({ product }) => {
  const { addToCart, isInCart } = useCart();

  const handleAddToCart = async () => {
    try {
      await addToCart(product.id, 1);
      // Show success message
    } catch (error) {
      // Show error message
      console.error('Failed to add to cart:', error);
    }
  };

  return (
    <div className="product-card">
      <div className="product-image">
        <img 
          src={product.image_url || product.thumbnail_url} 
          alt={product.name}
          loading="lazy"
        />
        {product.is_low_stock && (
          <span className="low-stock-badge">Low Stock</span>
        )}
      </div>
      
      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        <p className="product-category">{product.category_name}</p>
        <p className="product-price">${product.price}</p>
        
        <div className="stock-info">
          {product.track_inventory ? (
            <span className={`stock-status ${product.is_in_stock ? 'in-stock' : 'out-of-stock'}`}>
              {product.is_in_stock ? 'In Stock' : 'Out of Stock'}
            </span>
          ) : (
            <span className="stock-status available">Available</span>
          )}
        </div>
        
        <button 
          onClick={handleAddToCart}
          disabled={!product.is_in_stock}
          className="add-to-cart-btn"
        >
          {isInCart(product.id) ? 'In Cart' : 'Add to Cart'}
        </button>
      </div>
    </div>
  );
};

export default ProductCard;
```

## Cart Management

### Cart Service
```javascript
// services/cartService.js
import { httpClient } from '../utils/httpClient';
import API_CONFIG from '../config/api';

class CartService {
  // Add item to cart
  async addToCart(productId, quantity = 1) {
    return await httpClient.post(API_CONFIG.ENDPOINTS.CART.ADD, {
      product_id: productId,
      quantity: quantity,
    });
  }

  // Remove item from cart
  async removeFromCart(productId) {
    return await httpClient.post(API_CONFIG.ENDPOINTS.CART.REMOVE, {
      product_id: productId,
    });
  }

  // Get cart contents
  async getCart() {
    return await httpClient.get(API_CONFIG.ENDPOINTS.CART.LIST);
  }

  // Clear entire cart
  async clearCart() {
    return await httpClient.post(API_CONFIG.ENDPOINTS.CART.CLEAR);
  }

  // Update item quantity
  async updateQuantity(productId, quantity) {
    if (quantity <= 0) {
      return await this.removeFromCart(productId);
    }
    return await this.addToCart(productId, quantity);
  }
}

export const cartService = new CartService();
```

### React Cart Hook
```javascript
// hooks/useCart.js
import { useState, useEffect, createContext, useContext } from 'react';
import { cartService } from '../services/cartService';

const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadCart = async () => {
    try {
      setLoading(true);
      const cartData = await cartService.getCart();
      setCart(cartData);
    } catch (error) {
      console.error('Failed to load cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (productId, quantity = 1) => {
    try {
      await cartService.addToCart(productId, quantity);
      await loadCart(); // Refresh cart
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Failed to add to cart' 
      };
    }
  };

  const removeFromCart = async (productId) => {
    try {
      await cartService.removeFromCart(productId);
      await loadCart(); // Refresh cart
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Failed to remove from cart' 
      };
    }
  };

  const updateQuantity = async (productId, quantity) => {
    try {
      await cartService.updateQuantity(productId, quantity);
      await loadCart(); // Refresh cart
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Failed to update quantity' 
      };
    }
  };

  const clearCart = async () => {
    try {
      await cartService.clearCart();
      setCart(null);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Failed to clear cart' 
      };
    }
  };

  const isInCart = (productId) => {
    if (!cart?.cart_items) return false;
    return cart.cart_items.some(item => item.product.id === productId);
  };

  const getCartItem = (productId) => {
    if (!cart?.cart_items) return null;
    return cart.cart_items.find(item => item.product.id === productId);
  };

  const getTotalItems = () => {
    if (!cart?.cart_items) return 0;
    return cart.cart_items.reduce((total, item) => total + item.quantity, 0);
  };

  const getTotalPrice = () => {
    return cart?.total_price || '0.00';
  };

  useEffect(() => {
    loadCart();
  }, []);

  return (
    <CartContext.Provider value={{
      cart,
      loading,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart,
      isInCart,
      getCartItem,
      getTotalItems,
      getTotalPrice,
      refreshCart: loadCart,
    }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};
```

### Cart Component
```javascript
// components/Cart.jsx
import React from 'react';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';

const Cart = () => {
  const { cart, loading, removeFromCart, updateQuantity, clearCart } = useCart();
  const { isAuthenticated } = useAuth();

  const handleQuantityChange = async (productId, newQuantity) => {
    const result = await updateQuantity(productId, newQuantity);
    if (!result.success) {
      alert(result.error);
    }
  };

  const handleRemoveItem = async (productId) => {
    const result = await removeFromCart(productId);
    if (!result.success) {
      alert(result.error);
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to clear your cart?')) {
      const result = await clearCart();
      if (!result.success) {
        alert(result.error);
      }
    }
  };

  if (loading) {
    return <div className="loading">Loading cart...</div>;
  }

  if (!cart || !cart.cart_items || cart.cart_items.length === 0) {
    return (
      <div className="empty-cart">
        <h2>Your cart is empty</h2>
        <p>Add some products to get started!</p>
      </div>
    );
  }

  return (
    <div className="cart">
      <div className="cart-header">
        <h2>Shopping Cart</h2>
        <button onClick={handleClearCart} className="clear-cart-btn">
          Clear Cart
        </button>
      </div>

      <div className="cart-items">
        {cart.cart_items.map(item => (
          <div key={item.id} className="cart-item">
            <div className="item-image">
              <img 
                src={item.product.image_url || item.product.thumbnail_url} 
                alt={item.product.name}
              />
            </div>
            
            <div className="item-details">
              <h3>{item.product.name}</h3>
              <p className="item-category">{item.product.category_name}</p>
              <p className="item-price">${item.product.price}</p>
            </div>

            <div className="item-quantity">
              <label>Quantity:</label>
              <input
                type="number"
                min="1"
                value={item.quantity}
                onChange={(e) => handleQuantityChange(item.product.id, parseInt(e.target.value))}
              />
            </div>

            <div className="item-total">
              <p>Total: ${item.total_price}</p>
            </div>

            <button 
              onClick={() => handleRemoveItem(item.product.id)}
              className="remove-item-btn"
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="cart-summary">
        <div className="cart-totals">
          <p>Total Items: {cart.total_items}</p>
          <p className="total-price">Total: ${cart.total_price}</p>
        </div>

        {isAuthenticated ? (
          <button className="checkout-btn">
            Proceed to Checkout
          </button>
        ) : (
          <div className="checkout-login">
            <p>Please log in to proceed to checkout</p>
            <button className="login-btn">Login</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Cart;
```

## Orders & Checkout

### Order Service
```javascript
// services/orderService.js
import { httpClient } from '../utils/httpClient';
import API_CONFIG from '../config/api';

class OrderService {
  // Create order from cart
  async createOrder(orderData) {
    return await httpClient.post(API_CONFIG.ENDPOINTS.ORDERS.CREATE, {
      shipping_address: orderData.shippingAddress,
      billing_address: orderData.billingAddress,
      payment_method: orderData.paymentMethod,
      notes: orderData.notes,
    }, {
      requireAuth: true,
    });
  }

  // Get order details
  async getOrder(orderId) {
    return await httpClient.get(`${API_CONFIG.ENDPOINTS.ORDERS.DETAIL}${orderId}/`, {
      requireAuth: true,
    });
  }

  // Get user's orders
  async getUserOrders() {
    return await httpClient.get(API_CONFIG.ENDPOINTS.ORDERS.LIST, {
      requireAuth: true,
    });
  }
}

export const orderService = new OrderService();
```

### Checkout Component
```javascript
// components/Checkout.jsx
import React, { useState } from 'react';
import { useCart } from '../hooks/useCart';
import { useAuth } from '../hooks/useAuth';
import { orderService } from '../services/orderService';

const Checkout = () => {
  const { cart, clearCart } = useCart();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [orderData, setOrderData] = useState({
    shippingAddress: {
      street: '',
      city: '',
      state: '',
      zipCode: '',
      country: '',
    },
    billingAddress: {
      street: '',
      city: '',
      state: '',
      zipCode: '',
      country: '',
    },
    paymentMethod: 'card',
    notes: '',
  });

  const handleInputChange = (section, field, value) => {
    setOrderData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!cart || !cart.cart_items || cart.cart_items.length === 0) {
      alert('Your cart is empty');
      return;
    }

    setLoading(true);
    
    try {
      const result = await orderService.createOrder(orderData);
      
      if (result.success) {
        // Clear cart after successful order
        await clearCart();
        
        // Redirect to order confirmation
        window.location.href = `/order-confirmation/${result.order_id}`;
      } else {
        alert(result.error || 'Failed to create order');
      }
    } catch (error) {
      alert(error.message || 'An error occurred during checkout');
    } finally {
      setLoading(false);
    }
  };

  if (!cart || !cart.cart_items || cart.cart_items.length === 0) {
    return (
      <div className="empty-cart">
        <h2>Your cart is empty</h2>
        <p>Add some products before checking out.</p>
      </div>
    );
  }

  return (
    <div className="checkout">
      <h2>Checkout</h2>
      
      <div className="checkout-content">
        <div className="order-summary">
          <h3>Order Summary</h3>
          {cart.cart_items.map(item => (
            <div key={item.id} className="order-item">
              <span>{item.product.name} x {item.quantity}</span>
              <span>${item.total_price}</span>
            </div>
          ))}
          <div className="order-total">
            <strong>Total: ${cart.total_price}</strong>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="checkout-form">
          <div className="form-section">
            <h3>Shipping Address</h3>
            <div className="form-row">
              <input
                type="text"
                placeholder="Street Address"
                value={orderData.shippingAddress.street}
                onChange={(e) => handleInputChange('shippingAddress', 'street', e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <input
                type="text"
                placeholder="City"
                value={orderData.shippingAddress.city}
                onChange={(e) => handleInputChange('shippingAddress', 'city', e.target.value)}
                required
              />
              <input
                type="text"
                placeholder="State"
                value={orderData.shippingAddress.state}
                onChange={(e) => handleInputChange('shippingAddress', 'state', e.target.value)}
                required
              />
            </div>
            <div className="form-row">
              <input
                type="text"
                placeholder="ZIP Code"
                value={orderData.shippingAddress.zipCode}
                onChange={(e) => handleInputChange('shippingAddress', 'zipCode', e.target.value)}
                required
              />
              <input
                type="text"
                placeholder="Country"
                value={orderData.shippingAddress.country}
                onChange={(e) => handleInputChange('shippingAddress', 'country', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-section">
            <h3>Payment Method</h3>
            <select
              value={orderData.paymentMethod}
              onChange={(e) => setOrderData(prev => ({ ...prev, paymentMethod: e.target.value }))}
            >
              <option value="card">Credit Card</option>
              <option value="paypal">PayPal</option>
              <option value="bank_transfer">Bank Transfer</option>
            </select>
          </div>

          <div className="form-section">
            <h3>Additional Notes</h3>
            <textarea
              placeholder="Any special instructions..."
              value={orderData.notes}
              onChange={(e) => setOrderData(prev => ({ ...prev, notes: e.target.value }))}
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="submit-order-btn"
          >
            {loading ? 'Processing...' : 'Place Order'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Checkout;
```

## Error Handling

### Global Error Handler
```javascript
// utils/errorHandler.js
import { APIError } from './httpClient';

export const handleAPIError = (error) => {
  if (error instanceof APIError) {
    switch (error.status) {
      case 400:
        return {
          type: 'validation',
          message: 'Please check your input and try again.',
          details: error.data,
        };
      case 401:
        return {
          type: 'auth',
          message: 'Please log in to continue.',
          action: 'redirect_to_login',
        };
      case 403:
        return {
          type: 'permission',
          message: 'You do not have permission to perform this action.',
        };
      case 404:
        return {
          type: 'not_found',
          message: 'The requested resource was not found.',
        };
      case 422:
        return {
          type: 'validation',
          message: 'Invalid data provided.',
          details: error.data,
        };
      case 500:
        return {
          type: 'server',
          message: 'Server error. Please try again later.',
        };
      default:
        return {
          type: 'unknown',
          message: error.message || 'An unexpected error occurred.',
        };
    }
  }
  
  return {
    type: 'network',
    message: 'Network error. Please check your connection.',
  };
};

export const showErrorNotification = (error) => {
  const errorInfo = handleAPIError(error);
  
  // You can integrate with your notification system here
  console.error('API Error:', errorInfo);
  
  // Example with a simple alert (replace with your notification system)
  alert(`${errorInfo.message}${errorInfo.details ? '\nDetails: ' + JSON.stringify(errorInfo.details) : ''}`);
};
```

### Error Boundary Component
```javascript
// components/ErrorBoundary.jsx
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>We're sorry, but something unexpected happened.</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

## Complete Examples

### Main App Component
```javascript
// App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { CartProvider } from './hooks/useCart';
import ErrorBoundary from './components/ErrorBoundary';

// Components
import Header from './components/Header';
import ProductList from './components/ProductList';
import ProductDetail from './components/ProductDetail';
import Cart from './components/Cart';
import Checkout from './components/Checkout';
import Login from './components/Login';
import Register from './components/Register';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <CartProvider>
          <Router>
            <div className="app">
              <Header />
              
              <main className="main-content">
                <Routes>
                  <Route path="/" element={<ProductList />} />
                  <Route path="/products/:slug" element={<ProductDetail />} />
                  <Route path="/cart" element={<Cart />} />
                  <Route path="/checkout" element={<Checkout />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                </Routes>
              </main>
            </div>
          </Router>
        </CartProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
```

### Sample Payloads

#### Product List Response
```json
{
  "count": 25,
  "next": "https://api.mandccakes.com/api/products/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Chocolate Cake",
      "slug": "chocolate-cake",
      "image": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/cake.jpg",
      "image_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/cake.jpg",
      "thumbnail_url": "https://res.cloudinary.com/your-cloud/image/upload/w_150,h_150/v1234567890/cake.jpg",
      "medium_image_url": "https://res.cloudinary.com/your-cloud/image/upload/w_400,h_400/v1234567890/cake.jpg",
      "large_image_url": "https://res.cloudinary.com/your-cloud/image/upload/w_800,h_800/v1234567890/cake.jpg",
      "price": "25.99",
      "available": true,
      "category_name": "Cakes",
      "stock_quantity": 10,
      "is_in_stock": true,
      "is_low_stock": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Cart Response
```json
{
  "cart_items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Chocolate Cake",
        "price": "25.99",
        "image_url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/cake.jpg"
      },
      "quantity": 2,
      "total_price": "51.98"
    }
  ],
  "total_price": "51.98",
  "total_items": 2
}
```

#### Order Creation Request
```json
{
  "shipping_address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zipCode": "10001",
    "country": "USA"
  },
  "billing_address": {
    "street": "123 Main St",
    "city": "New York", 
    "state": "NY",
    "zipCode": "10001",
    "country": "USA"
  },
  "payment_method": "card",
  "notes": "Please deliver after 5 PM"
}
```

This comprehensive guide provides everything needed to implement a frontend that consumes the Bakery API effectively, with proper error handling, authentication, and user experience considerations.

# User Service API Examples

This document provides sample `cURL` requests and responses for the User Service API.

**Base URL:** `http://127.0.0.1:8000`

---

### 1. Register a New User

Registers a new user account.

**Endpoint:** `POST /api/v1/auth/register`

**Request:**

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
-H "Content-Type: application/json" \
-d '{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "password": "Password123!",
  "full_name": "John Doe",
  "phone_number": "+8801712345678",
  "address": "123 Main St, Anytown"
}'
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "is_verified": false,
    "created_at": "2023-10-28T10:00:00.000Z"
  },
  "timestamp": "2023-10-28T10:00:00.123Z"
}
```

**Error Response (400 Bad Request - User Exists):**

```json
{
  "detail": "Email already registered"
}
```

---

### 2. User Login

Authenticates a user and returns JWT tokens.

**Endpoint:** `POST /api/v1/auth/login`

**Request:**

Note: The login endpoint uses `application/x-www-form-urlencoded` as it depends on `OAuth2PasswordRequestForm`.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=john.doe@example.com&password=Password123!"
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "ey...",
    "refresh_token": "ey...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john.doe@example.com",
      "role": "user",
      "is_active": true,
      "is_verified": false,
      "full_name": "John Doe",
      "phone_number": "+8801712345678",
      "address": "123 Main St, Anytown",
      "created_at": "2023-10-28T10:00:00.000Z",
      "updated_at": "2023-10-28T10:00:00.000Z",
      "last_login_at": "2023-10-28T10:05:00.000Z"
    }
  },
  "timestamp": "2023-10-28T10:05:00.123Z"
}
```

---

### 3. Get User Profile

Retrieves the profile of the currently authenticated user.

**Endpoint:** `GET /api/v1/profile/`

**Request:**

Replace `<ACCESS_TOKEN>` with the token from the login response.

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/profile/" \
-H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "phone_number": "+8801712345678",
    "address": "123 Main St, Anytown",
    "role": "user",
    "is_active": true,
    "is_verified": false,
    "created_at": "2023-10-28T10:00:00Z",
    "updated_at": "2023-10-28T10:00:00Z",
    "last_login_at": "2023-10-28T10:05:00Z"
  },
  "timestamp": "2023-10-28T10:10:00.123Z"
}
```

---

### 4. Update User Profile

Updates the profile of the currently authenticated user.

**Endpoint:** `PUT /api/v1/profile/`

**Request:**

Replace `<ACCESS_TOKEN>` with a valid token.

```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/profile/" \
-H "Authorization: Bearer <ACCESS_TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "full_name": "Johnathan Doe",
  "address": "456 New Ave, Sometown"
}'
```

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "full_name": "Johnathan Doe",
    "phone_number": "+8801712345678",
    "address": "456 New Ave, Sometown",
    "role": "user",
    "is_active": true,
    "is_verified": false,
    "created_at": "2023-10-28T10:00:00Z",
    "updated_at": "2023-10-28T10:15:00Z",
    "last_login_at": "2023-10-28T10:05:00Z"
  },
  "timestamp": "2023-10-28T10:15:00.123Z"
}
```

---

### 5. Refresh Access Token

Generates a new set of tokens using a valid refresh token.

**Endpoint:** `POST /api/v1/auth/refresh`

**Request:**

Replace `<REFRESH_TOKEN>` with the token from the login response.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/refresh" \
-H "Content-Type: application/json" \
-d '{
  "refresh_token": "<REFRESH_TOKEN>"
}'
```

**Success Response (200 OK):**

The response is identical in structure to the `/login` response, containing new tokens.

```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "ey... (new)",
    "refresh_token": "ey... (new)",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": { ... }
  },
  "timestamp": "2023-10-28T11:00:00.123Z"
}
```

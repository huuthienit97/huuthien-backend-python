# Users Module

## Tổng quan
Module Users cung cấp các chức năng quản lý người dùng với các tính năng nâng cao như:
- Xác thực và phân quyền
- Quản lý thông tin cá nhân
- Tìm kiếm và gợi ý thông minh
- Xác thực email
- Quản lý phiên đăng nhập

## Cấu trúc dữ liệu

### User Model
```python
class User:
    username: str        # Tên đăng nhập, unique
    email: str          # Email, unique
    password: str       # Mật khẩu đã được mã hóa
    first_name: str     # Tên
    last_name: str      # Họ
    is_active: bool     # Trạng thái kích hoạt
    is_staff: bool      # Quyền quản trị
    date_joined: date   # Ngày tạo tài khoản
```

### UserProfile Model
```python
class UserProfile:
    user: User          # Liên kết với User
    avatar: image       # Ảnh đại diện
    bio: str           # Tiểu sử
    phone: str         # Số điện thoại
    address: str       # Địa chỉ
```

## API Endpoints

### 1. Authentication
```
POST /api/users/login/
- Đăng nhập
- Body: {username/email, password}
- Response: {access_token, refresh_token}

POST /api/users/register/
- Đăng ký tài khoản mới
- Body: {username, email, password, first_name, last_name}
- Response: {user_data, access_token}

POST /api/users/logout/
- Đăng xuất
- Headers: Authorization Bearer
- Response: {success: true}

POST /api/users/token/refresh/
- Làm mới access token
- Body: {refresh_token}
- Response: {access_token}
```

### 2. User Management
```
GET /api/users/me/
- Lấy thông tin user hiện tại
- Headers: Authorization Bearer
- Response: {user_data, profile_data}

PUT /api/users/me/
- Cập nhật thông tin cá nhân
- Headers: Authorization Bearer
- Body: {first_name, last_name, email, profile: {bio, phone, address}}
- Response: {updated_user_data}

PATCH /api/users/me/change-password/
- Đổi mật khẩu
- Headers: Authorization Bearer
- Body: {old_password, new_password}
- Response: {success: true}

POST /api/users/me/avatar/
- Upload avatar
- Headers: Authorization Bearer
- Body: FormData with 'avatar' file
- Response: {avatar_url}
```

### 3. Email Verification
```
POST /api/users/verify-email/
- Xác thực email
- Query params: ?token=verification_token
- Response: {success: true}

POST /api/users/resend-verification/
- Gửi lại email xác thực
- Body: {email}
- Response: {success: true}
```

### 4. Search & Suggestions
```
GET /api/users/search/
- Tìm kiếm users
- Query params:
  - q: từ khóa tìm kiếm
  - page: số trang (default: 1)
  - page_size: số kết quả mỗi trang (default: 10)
- Response: {
    total: số lượng kết quả,
    results: [
      {
        id: user_id,
        username: tên đăng nhập,
        email: email,
        full_name: họ và tên,
        date_joined: ngày tạo,
        score: độ phù hợp
      }
    ],
    page: trang hiện tại,
    page_size: số kết quả mỗi trang
  }

GET /api/users/suggest/
- Gợi ý tìm kiếm
- Query params:
  - q: từ khóa
  - limit: số lượng gợi ý (default: 5)
- Response: [
    {
      text: nội dung gợi ý,
      type: loại (email/username),
      score: độ phù hợp
    }
  ]
```

## Tính năng nổi bật

### 1. Tìm kiếm thông minh
- Hỗ trợ tìm kiếm gần đúng (fuzzy search)
- Tìm kiếm theo nhiều trường (username, email, full_name)
- Kết quả được xếp hạng theo độ phù hợp
- Hỗ trợ tiếng Việt

### 2. Bảo mật
- JWT Authentication
- Password hashing
- Email verification
- Session management
- Rate limiting

### 3. Profile & Avatar
- Upload và quản lý avatar
- Thông tin profile mở rộng
- Validation dữ liệu

### 4. Performance
- Caching
- Pagination
- Optimized queries
- Elasticsearch integration

## Hướng dẫn tích hợp Frontend

### 1. Authentication Flow
1. Đăng ký user mới:
```javascript
const response = await axios.post('/api/users/register/', userData);
const { access_token } = response.data;
// Lưu token và redirect
```

2. Đăng nhập:
```javascript
const response = await axios.post('/api/users/login/', credentials);
const { access_token, refresh_token } = response.data;
// Lưu tokens và redirect
```

3. Automatic token refresh:
```javascript
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response.status === 401) {
      const response = await axios.post('/api/users/token/refresh/', {
        refresh_token: getStoredRefreshToken()
      });
      const { access_token } = response.data;
      // Cập nhật token và retry request
    }
    return Promise.reject(error);
  }
);
```

### 2. Search Implementation
```javascript
// Tìm kiếm với debounce
const searchUsers = debounce(async (query) => {
  const response = await axios.get('/api/users/search/', {
    params: { q: query }
  });
  return response.data;
}, 300);

// Auto-complete
const getSuggestions = debounce(async (query) => {
  const response = await axios.get('/api/users/suggest/', {
    params: { q: query }
  });
  return response.data;
}, 300);
```

### 3. Profile Management
```javascript
// Upload avatar
const uploadAvatar = async (file) => {
  const formData = new FormData();
  formData.append('avatar', file);
  const response = await axios.post('/api/users/me/avatar/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

// Update profile
const updateProfile = async (profileData) => {
  const response = await axios.put('/api/users/me/', profileData);
  return response.data;
};
```

## Error Handling

Tất cả API endpoints đều trả về lỗi theo format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Chi tiết lỗi",
    "details": {} // Thông tin bổ sung nếu có
  }
}
```

Các mã lỗi phổ biến:
- `AUTH_FAILED`: Lỗi xác thực
- `INVALID_DATA`: Dữ liệu không hợp lệ
- `NOT_FOUND`: Không tìm thấy resource
- `PERMISSION_DENIED`: Không có quyền truy cập
- `SERVER_ERROR`: Lỗi server

## Rate Limiting

- API có giới hạn số lượng request:
  - Authentication APIs: 5 requests/minute
  - Search APIs: 20 requests/minute
  - Other APIs: 60 requests/minute

## Môi trường phát triển

### Requirements
- Python 3.8+
- PostgreSQL 12+
- Elasticsearch 7.x
- Redis (cho caching)

### Environment Variables
```
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6379
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
# Users App Documentation

## Tổng quan
Users app là một module quản lý người dùng nâng cao với các tính năng bảo mật, hiệu năng và quản lý quyền linh hoạt. Module này mở rộng từ Django's built-in User model và cung cấp thêm nhiều tính năng mới.

## Cấu trúc Models

### 1. User Model
```python
class User(AbstractUser):
```
Mở rộng từ AbstractUser với các tính năng bổ sung:

#### Các trường chính:
- `email`: Email (unique, required)
- `phone_number`: Số điện thoại
- `avatar`: Ảnh đại diện
- `birth_date`: Ngày sinh
- `role`: Vai trò mặc định (admin/staff/user)
- `custom_roles`: Các vai trò tùy chỉnh (ManyToMany với Role)
- `last_password_change`: Thời điểm đổi mật khẩu gần nhất
- `failed_login_attempts`: Số lần đăng nhập thất bại
- `last_failed_login`: Thời điểm đăng nhập thất bại gần nhất
- `search_vector`: Trường đánh chỉ mục full-text search

#### Indexes:
```python
class Meta:
    indexes = [
        models.Index(fields=['username']),
        models.Index(fields=['email']),
        models.Index(fields=['role']),
        models.Index(fields=['date_joined']),
        GinIndex(fields=['search_vector']),
    ]
```
- Tối ưu tìm kiếm với các index trên các trường thường được query
- GinIndex cho full-text search

#### Methods:
```python
def get_permissions(self):
    """Lấy tất cả quyền của user"""
```
- Trả về set các quyền từ cả role mặc định và custom roles
- Superuser có tất cả quyền ('all')
- Phân cấp quyền: admin > staff > user

```python
def has_permission(self, permission):
    """Kiểm tra quyền cụ thể"""
```
- Kiểm tra nhanh một quyền cụ thể
- Sử dụng cache để tối ưu hiệu năng

### 2. Role Model
```python
class Role(models.Model):
```
Quản lý các vai trò tùy chỉnh:

#### Các trường:
- `name`: Tên vai trò (unique)
- `description`: Mô tả
- `permissions`: JSONField lưu các quyền
- `created_at/updated_at`: Timestamps

### 3. UserProfile Model
```python
class UserProfile(models.Model):
```
Thông tin bổ sung của user:

#### Các trường:
- `user`: OneToOne với User
- `bio`: Tiểu sử
- `position`: Chức vụ
- `department`: Phòng ban
- `address`: Địa chỉ

### 4. AuditLog Model
```python
class AuditLog(models.Model):
```
Ghi lại lịch sử thay đổi:

#### Các trường:
- `user`: ForeignKey tới User
- `action`: Loại hành động (create/update/delete/login/logout)
- `changes`: JSONField lưu chi tiết thay đổi
- `ip_address`: IP của request
- `user_agent`: User agent của request
- `timestamp`: Thời điểm thực hiện

#### Indexes:
```python
class Meta:
    indexes = [
        models.Index(fields=['user', '-timestamp']),
        models.Index(fields=['action', '-timestamp']),
    ]
```
Tối ưu cho truy vấn lịch sử

## Serializers

### 1. UserSerializer
```python
class UserSerializer(serializers.ModelSerializer):
```
Serializer chính cho User model:

#### Các trường bổ sung:
- `profile`: Nested UserProfileSerializer
- `full_name`: SerializerMethodField
- `custom_roles`: Nested RoleSerializer
- `permissions`: Danh sách quyền
- `statistics`: Thống kê hoạt động từ cache

#### Tính năng:
- Cache thống kê người dùng (1 giờ)
- Tính toán tỷ lệ đăng nhập thành công
- Lấy 5 hoạt động gần nhất

### 2. UserCreateSerializer
```python
class UserCreateSerializer(serializers.ModelSerializer):
```
Xử lý tạo user mới:

#### Validation:
- Mật khẩu tối thiểu 8 ký tự
- Yêu cầu xác nhận mật khẩu
- Validate email unique

## Filters

### UserFilter
```python
class UserFilter(filters.FilterSet):
```
Filter phức tạp cho User model:

#### Các filter:
- Full-text search với ranking
- Filter theo role, trạng thái
- Filter theo khoảng thời gian
- Filter có/không có custom role

#### Tính năng search:
- Sử dụng PostgreSQL full-text search
- Fallback tới tìm kiếm thông thường
- Sắp xếp kết quả theo độ phù hợp

## Signals

### 1. Pre-save Signal
```python
@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
```
- Lưu trạng thái trước khi thay đổi
- Phục vụ cho audit log

### 2. Post-save Signal
```python
@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
```
- Tạo audit log cho create/update
- Cập nhật last_password_change
- Xóa cache khi có thay đổi

### 3. Login/Logout Signals
```python
@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
```
- Reset failed_login_attempts
- Ghi log đăng nhập

```python
@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
```
- Ghi log đăng xuất

## Cấu hình

### Cache
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
        }
    }
}
```
- Sử dụng Redis làm backend
- Cấu hình timeout và retry
- Pool connections để tối ưu hiệu năng

### JWT
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```
- Token access ngắn hạn (30 phút)
- Refresh token 1 ngày
- Rotation để tăng bảo mật

### REST Framework
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}
```
- JWT authentication
- Filter và search backends
- Rate limiting để bảo vệ API

## Migrations

### Search Vector Trigger
```sql
CREATE OR REPLACE FUNCTION users_update_search_vector_trigger() 
RETURNS trigger AS $$
begin
    new.search_vector := setweight(to_tsvector('simple', coalesce(new.username, '')), 'A') ||
                        setweight(to_tsvector('simple', coalesce(new.email, '')), 'B') ||
                        setweight(to_tsvector('simple', coalesce(new.first_name, '')), 'C') ||
                        setweight(to_tsvector('simple', coalesce(new.last_name, '')), 'C');
    return new;
end
$$ LANGUAGE plpgsql;
```
- Tự động cập nhật search_vector
- Trọng số khác nhau cho các trường
- Trigger chạy khi insert/update

## Sử dụng

### 1. Tạo User
```python
user = User.objects.create_user(
    username='username',
    email='email@example.com',
    password='password',
    role='user'
)
```

### 2. Thêm Custom Role
```python
role = Role.objects.create(
    name='custom_role',
    permissions={'can_view_reports': True}
)
user.custom_roles.add(role)
```

### 3. Kiểm tra Quyền
```python
if user.has_permission('can_view_reports'):
    # Do something
```

### 4. Tìm kiếm User
```python
# Full-text search
users = User.objects.annotate(
    rank=SearchRank(F('search_vector'), SearchQuery('keyword'))
).filter(search_vector=SearchQuery('keyword')).order_by('-rank')

# Filter
users = UserFilter(request.GET, queryset=User.objects.all()).qs
```

### 5. Xem Audit Log
```python
# Lấy lịch sử thay đổi của user
logs = user.audit_logs.all().order_by('-timestamp')

# Lấy các lần đăng nhập
logins = user.audit_logs.filter(action=AuditLog.ACTION_LOGIN)
```

## Tích hợp với NextJS

### 1. Cài đặt Dependencies
```bash
# Cài đặt các package cần thiết
npm install @tanstack/react-query axios jwt-decode
npm install @mui/material @emotion/react @emotion/styled  # (Tùy chọn, nếu dùng MUI)
```

### 2. Cấu hình API Client
```typescript
// lib/axios.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor để thêm token vào header
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor để refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await apiClient.post('/api/token/refresh/', {
          refresh: refreshToken,
        });
        const { access } = response.data;
        localStorage.setItem('access_token', access);
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (error) {
        // Redirect to login if refresh fails
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 3. Custom Hooks

#### useAuth Hook
```typescript
// hooks/useAuth.ts
import { create } from 'zustand';
import { User } from '@/types';
import apiClient from '@/lib/axios';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  getProfile: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post('/api/token/', { username, password });
      const { access, refresh } = response.data;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      // Lấy thông tin user
      const userResponse = await apiClient.get('/api/users/me/');
      set({ user: userResponse.data, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Đăng nhập thất bại', 
        isLoading: false 
      });
    }
  },

  logout: () => {
    localStorage.clear();
    set({ user: null });
  },

  getProfile: async () => {
    try {
      const response = await apiClient.get('/api/users/me/');
      set({ user: response.data });
    } catch (error) {
      set({ user: null });
    }
  },
}));
```

#### useUsers Hook
```typescript
// hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/axios';
import { User, UserFilter } from '@/types';

export const useUsers = () => {
  const queryClient = useQueryClient();

  // Lấy danh sách users với filter
  const getUsers = (filter: UserFilter) => {
    return useQuery({
      queryKey: ['users', filter],
      queryFn: async () => {
        const params = new URLSearchParams();
        if (filter.search) params.append('search', filter.search);
        if (filter.role) params.append('role', filter.role);
        if (filter.is_active !== undefined) {
          params.append('is_active', filter.is_active.toString());
        }
        
        const response = await apiClient.get(`/api/users/?${params}`);
        return response.data;
      },
    });
  };

  // Tạo user mới
  const createUser = useMutation({
    mutationFn: (data: Partial<User>) => 
      apiClient.post('/api/users/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Cập nhật user
  const updateUser = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<User> }) =>
      apiClient.patch(`/api/users/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Xóa user
  const deleteUser = useMutation({
    mutationFn: (id: number) => 
      apiClient.delete(`/api/users/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  return {
    getUsers,
    createUser,
    updateUser,
    deleteUser,
  };
};
```

### 4. Components

#### Protected Route
```typescript
// components/ProtectedRoute.tsx
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';

export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, getProfile } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    
    if (!user) {
      getProfile();
    }
  }, [user, router, getProfile]);

  if (!user) return null;

  return <>{children}</>;
};
```

#### Login Form
```typescript
// components/LoginForm.tsx
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';

export const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(username, password);
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      <div>
        <label>Username:</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
      </div>
      <div>
        <label>Password:</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Đang đăng nhập...' : 'Đăng nhập'}
      </button>
    </form>
  );
};
```

#### Users List
```typescript
// components/UsersList.tsx
import { useState } from 'react';
import { useUsers } from '@/hooks/useUsers';
import { UserFilter } from '@/types';

export const UsersList = () => {
  const [filter, setFilter] = useState<UserFilter>({});
  const { getUsers } = useUsers();
  const { data, isLoading } = getUsers(filter);

  const handleSearch = (search: string) => {
    setFilter(prev => ({ ...prev, search }));
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <div className="filters">
        <input
          type="text"
          placeholder="Tìm kiếm..."
          onChange={(e) => handleSearch(e.target.value)}
        />
      </div>

      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {data?.results.map((user) => (
            <tr key={user.id}>
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                {/* Add your actions here */}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### 5. Types
```typescript
// types/index.ts
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  custom_roles: Role[];
  permissions: string[];
  statistics: UserStatistics;
  profile?: UserProfile;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  permissions: Record<string, boolean>;
}

export interface UserProfile {
  bio: string;
  position: string;
  department: string;
  address: string;
}

export interface UserStatistics {
  total_logins: number;
  last_activities: Activity[];
  login_success_rate: number;
}

export interface Activity {
  action: string;
  timestamp: string;
}

export interface UserFilter {
  search?: string;
  role?: string;
  is_active?: boolean;
}
```

### 6. Middleware
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token');
  const publicPaths = ['/login', '/register'];
  
  if (!token && !publicPaths.includes(request.nextUrl.pathname)) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
```

### 7. Ví dụ Sử dụng

#### Layout với Authentication
```typescript
// components/Layout.tsx
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from './ProtectedRoute';

export const Layout = ({ children }: { children: React.ReactNode }) => {
  const { user, logout } = useAuth();

  return (
    <ProtectedRoute>
      <div>
        <header>
          {user && (
            <div>
              Welcome, {user.full_name}
              <button onClick={logout}>Đăng xuất</button>
            </div>
          )}
        </header>
        <main>{children}</main>
      </div>
    </ProtectedRoute>
  );
};
```

#### Trang Users
```typescript
// pages/users/index.tsx
import { UsersList } from '@/components/UsersList';
import { Layout } from '@/components/Layout';

export default function UsersPage() {
  return (
    <Layout>
      <h1>Quản lý người dùng</h1>
      <UsersList />
    </Layout>
  );
}
```

#### API Provider
```typescript
// pages/_app.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { AppProps } from 'next/app';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App({ Component, pageProps }: AppProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <Component {...pageProps} />
    </QueryClientProvider>
  );
}
```

### 8. Environment Variables
```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 9. Xử lý Permissions trong Components
```typescript
// components/PermissionGate.tsx
import { useAuth } from '@/hooks/useAuth';

interface Props {
  permission: string;
  children: React.ReactNode;
}

export const PermissionGate = ({ permission, children }: Props) => {
  const { user } = useAuth();
  
  if (!user?.permissions.includes(permission)) {
    return null;
  }

  return <>{children}</>;
};

// Sử dụng
<PermissionGate permission="can_view_reports">
  <ReportsComponent />
</PermissionGate>
```

### 10. Custom Error Boundary
```typescript
// components/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div>
          <h2>Đã có lỗi xảy ra</h2>
          <button onClick={() => this.setState({ hasError: false })}>
            Thử lại
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

## API Documentation

### Authentication Endpoints

#### 1. Đăng nhập
```http
POST /api/token/

Request:
{
    "username": "string",
    "password": "string"
}

Response: 200 OK
{
    "access": "string",  // JWT access token
    "refresh": "string"  // JWT refresh token
}

Error: 401 Unauthorized
{
    "detail": "No active account found with the given credentials"
}
```

#### 2. Refresh Token
```http
POST /api/token/refresh/

Request:
{
    "refresh": "string"  // Refresh token
}

Response: 200 OK
{
    "access": "string"  // New access token
}

Error: 401 Unauthorized
{
    "detail": "Token is invalid or expired"
}
```

### User Endpoints

#### 1. Lấy thông tin user hiện tại
```http
GET /api/users/me/

Headers:
Authorization: Bearer <access_token>

Response: 200 OK
{
    "id": number,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "full_name": "string",
    "role": "string",
    "custom_roles": [
        {
            "id": number,
            "name": "string",
            "description": "string",
            "permissions": object
        }
    ],
    "permissions": ["string"],
    "statistics": {
        "total_logins": number,
        "last_activities": [
            {
                "action": "string",
                "timestamp": "string"
            }
        ],
        "login_success_rate": number
    },
    "profile": {
        "bio": "string",
        "position": "string",
        "department": "string",
        "address": "string"
    }
}

Error: 401 Unauthorized
{
    "detail": "Authentication credentials were not provided"
}
```

#### 2. Danh sách users
```http
GET /api/users/

Headers:
Authorization: Bearer <access_token>

Query Parameters:
- search: string (tìm kiếm full-text)
- role: string (admin|staff|user)
- is_active: boolean
- page: number
- page_size: number
- ordering: string (username|-username|email|-email|date_joined|-date_joined)

Response: 200 OK
{
    "count": number,
    "next": "string|null",
    "previous": "string|null",
    "results": [
        {
            // User object như trên
        }
    ]
}
```

#### 3. Tạo user mới
```http
POST /api/users/

Headers:
Authorization: Bearer <access_token>

Request:
{
    "username": "string",
    "email": "string",
    "password": "string",
    "confirm_password": "string",
    "first_name": "string",
    "last_name": "string",
    "phone_number": "string",
    "role": "string",
    "custom_roles": [number],  // ID của các custom role
    "profile": {
        "bio": "string",
        "position": "string",
        "department": "string",
        "address": "string"
    }
}

Response: 201 Created
{
    // User object như trên
}

Error: 400 Bad Request
{
    "username": ["Username already exists"],
    "email": ["Email already exists"],
    "confirm_password": ["Passwords do not match"]
}
```

#### 4. Cập nhật user
```http
PATCH /api/users/{id}/

Headers:
Authorization: Bearer <access_token>

Request:
{
    // Các trường cần cập nhật
    "first_name": "string",
    "last_name": "string",
    "role": "string",
    "custom_roles": [number]
}

Response: 200 OK
{
    // User object đã cập nhật
}
```

#### 5. Xóa user
```http
DELETE /api/users/{id}/

Headers:
Authorization: Bearer <access_token>

Response: 204 No Content

Error: 403 Forbidden
{
    "detail": "You do not have permission to perform this action"
}
```

### Role Endpoints

#### 1. Danh sách roles
```http
GET /api/roles/

Headers:
Authorization: Bearer <access_token>

Response: 200 OK
{
    "count": number,
    "results": [
        {
            "id": number,
            "name": "string",
            "description": "string",
            "permissions": {
                "permission_key": boolean
            },
            "created_at": "string",
            "updated_at": "string"
        }
    ]
}
```

#### 2. Tạo role mới
```http
POST /api/roles/

Headers:
Authorization: Bearer <access_token>

Request:
{
    "name": "string",
    "description": "string",
    "permissions": {
        "can_view_reports": true,
        "can_edit_users": true
    }
}

Response: 201 Created
{
    // Role object như trên
}
```

### Audit Log Endpoints

#### 1. Lấy lịch sử hoạt động
```http
GET /api/audit-logs/

Headers:
Authorization: Bearer <access_token>

Query Parameters:
- user_id: number
- action: string (create|update|delete|login|logout)
- from_date: string (YYYY-MM-DD)
- to_date: string (YYYY-MM-DD)
- page: number
- page_size: number

Response: 200 OK
{
    "count": number,
    "results": [
        {
            "id": number,
            "user": {
                "id": number,
                "username": "string"
            },
            "action": "string",
            "changes": object,
            "ip_address": "string",
            "user_agent": "string",
            "timestamp": "string"
        }
    ]
}
```

### Error Responses

#### 1. Validation Error
```http
400 Bad Request
{
    "field_name": [
        "Error message"
    ]
}
```

#### 2. Authentication Error
```http
401 Unauthorized
{
    "detail": "Invalid token" | "Token has expired" | "Authentication credentials were not provided"
}
```

#### 3. Permission Error
```http
403 Forbidden
{
    "detail": "You do not have permission to perform this action"
}
```

#### 4. Not Found Error
```http
404 Not Found
{
    "detail": "Not found"
}
```

### Rate Limiting

API có giới hạn số lượng request:
- Anonymous: 100 requests/day
- Authenticated: 1000 requests/day

Response khi vượt quá giới hạn:
```http
429 Too Many Requests
{
    "detail": "Request was throttled. Expected available in 86400 seconds."
}
```

### Websocket Events

Các events realtime được gửi qua websocket:

```javascript
// Kết nối
const ws = new WebSocket(`ws://localhost:8000/ws/users/?token=${access_token}`);

// Events
{
    "type": "user.updated",
    "data": {
        "user_id": number,
        "changes": object
    }
}

{
    "type": "user.logged_in",
    "data": {
        "user_id": number,
        "timestamp": "string"
    }
}

{
    "type": "user.logged_out",
    "data": {
        "user_id": number,
        "timestamp": "string"
    }
}
```

### Pagination

Tất cả các endpoint trả về danh sách đều hỗ trợ pagination:

Query Parameters:
- `page`: Số trang (default: 1)
- `page_size`: Số item mỗi trang (default: 10, max: 100)

Response format:
```json
{
    "count": number,      // Tổng số items
    "next": string|null,  // URL trang tiếp theo
    "previous": string|null,  // URL trang trước
    "results": []         // Danh sách items
}
```

### Filtering & Sorting

Các endpoint danh sách hỗ trợ:

1. Filtering:
```
GET /api/users/?search=keyword
GET /api/users/?role=admin
GET /api/users/?is_active=true
GET /api/users/?created_after=2024-01-01
```

2. Sorting:
```
GET /api/users/?ordering=username  // Tăng dần
GET /api/users/?ordering=-username  // Giảm dần
```

### Caching

API sử dụng Redis để cache:
- User statistics: 1 giờ
- Role permissions: 30 phút
- Search results: 5 phút

Cache được tự động invalidate khi có thay đổi liên quan. 

## Cấu hình JWT

### 1. Biến môi trường
Tạo file `.env` từ `.env.example` và cấu hình các biến sau:

```env
# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=30  # Thời gian sống của access token (phút)
JWT_REFRESH_TOKEN_LIFETIME=1  # Thời gian sống của refresh token (ngày)
JWT_ROTATE_REFRESH_TOKENS=True  # Tạo refresh token mới mỗi lần refresh
JWT_BLACKLIST_AFTER_ROTATION=True  # Đưa refresh token cũ vào blacklist
JWT_ALGORITHM=HS256  # Thuật toán mã hóa
JWT_SIGNING_KEY=your-jwt-secret-key  # Key để ký token (nên khác với SECRET_KEY)
JWT_VERIFYING_KEY=  # Key để verify token (cho thuật toán bất đối xứng)
JWT_AUDIENCE=  # Đối tượng sử dụng token (optional)
JWT_ISSUER=  # Đơn vị phát hành token (optional)
```

### 2. Cấu hình trong code
```python
# settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 30))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 1))),
    'ROTATE_REFRESH_TOKENS': os.getenv('JWT_ROTATE_REFRESH_TOKENS', 'True') == 'True',
    'BLACKLIST_AFTER_ROTATION': os.getenv('JWT_BLACKLIST_AFTER_ROTATION', 'True') == 'True',
    'ALGORITHM': os.getenv('JWT_ALGORITHM', 'HS256'),
    'SIGNING_KEY': os.getenv('JWT_SIGNING_KEY', SECRET_KEY),
    # ... các cấu hình khác
}
```

### 3. Sử dụng trong Frontend

```typescript
// lib/axios.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Thêm interceptor để tự động refresh token
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            try {
                const refreshToken = localStorage.getItem('refresh_token');
                const response = await axios.post(
                    `${API_URL}/api/token/refresh/`,
                    { refresh: refreshToken }
                );
                
                const { access } = response.data;
                localStorage.setItem('access_token', access);
                
                originalRequest.headers.Authorization = `Bearer ${access}`;
                return apiClient(originalRequest);
            } catch (error) {
                // Nếu refresh token cũng hết hạn, logout user
                localStorage.clear();
                window.location.href = '/login';
                return Promise.reject(error);
            }
        }
        
        return Promise.reject(error);
    }
);

export default apiClient;
```

### 4. Bảo mật

1. **Lưu trữ token:**
```typescript
// Không lưu trực tiếp token vào localStorage trong production
const saveTokens = (access: string, refresh: string) => {
    if (process.env.NODE_ENV === 'production') {
        // Sử dụng httpOnly cookies
        document.cookie = `access_token=${access}; path=/; secure; samesite=strict`;
        document.cookie = `refresh_token=${refresh}; path=/; secure; samesite=strict`;
    } else {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
    }
};
```

2. **CORS Settings:**
```python
# settings.py
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]
```

3. **Security Headers:**
```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```
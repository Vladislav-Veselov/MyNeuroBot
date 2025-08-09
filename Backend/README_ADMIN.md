# Admin Panel Documentation

## Overview

The admin panel provides secure balance management functionality that allows only the admin user to increase user balances when they transfer money.

## Security Features

- **Admin-only access**: Only the admin user can access balance management
- **Session-based authentication**: Secure login required
- **Audit trail**: All balance changes are logged as transactions
- **Input validation**: Amounts must be positive
- **Error handling**: Comprehensive error handling and user feedback

## Configuration

### Admin Credentials

To set up the admin account, modify the following constants in `Backend/auth.py`:

```python
# Change these to your desired admin credentials
ADMIN_USERNAME = "your_admin_username"  # Change this
ADMIN_PASSWORD_HASH = "your_password_hash"  # Change this
```

### Generate Password Hash

To generate your password hash, use this Python code:

```python
import hashlib
password = "your_admin_password"
password_hash = hashlib.sha256(password.encode()).hexdigest()
print(password_hash)
```

## Usage

### Accessing Admin Panel

1. **Login as admin**: Navigate to `/login` and use your admin credentials
2. **Access admin panel**: Navigate to `/admin` when logged in as admin
3. **View all balances**: See all user balances in real-time
4. **Increase balance**: Select user, enter amount, and submit

### Admin Panel Features

#### User Balances Display
- Shows all user balances in real-time
- Color-coded balance status (green for positive, red for negative, yellow for zero)
- Displays total costs, token usage, and last update time
- Shows current model for each user

#### Balance Increase Form
- Dropdown to select user (excludes admin)
- Amount input with validation
- Optional reason field
- Real-time feedback on success/failure

### API Endpoints

#### Admin Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin` | Admin panel page |
| `GET` | `/api/admin/users` | Get all users (admin only) |
| `GET` | `/api/admin/balances` | Get all user balances (admin only) |
| `POST` | `/api/admin/balance/increase` | Increase user balance (admin only) |
| `GET` | `/api/admin/user/<username>/balance` | Get specific user balance (admin only) |

#### Balance Increase API

**Endpoint**: `POST /api/admin/balance/increase`

**Request Body**:
```json
{
    "username": "user123",
    "amount_rub": 1000.0,
    "reason": "Payment for services"
}
```

**Response**:
```json
{
    "success": true,
    "message": "Balance increased by ₽1000.00",
    "old_balance": 500.0,
    "new_balance": 1500.0,
    "increase_amount": 1000.0
}
```

## Implementation Details

### Authentication System

The admin system extends the existing authentication with:

- `is_admin()` method to check admin status
- `admin_required` decorator for API routes
- `admin_required_web` decorator for web routes
- Admin user handling in login process

### Balance Management

The balance manager includes admin methods:

- `admin_increase_balance()`: Increase user balance
- `admin_get_all_balances()`: Get all user balances
- Enhanced transaction recording for admin actions

### Frontend

The admin panel includes:

- **Admin template**: `Frontend/templates/admin.html`
- **Admin JavaScript**: `Frontend/static/js/admin.js`
- Real-time balance updates
- Form validation and error handling

## Testing

Run the admin functionality test:

```bash
cd Backend
python test_admin.py
```

## Security Considerations

1. **Change default credentials**: Always change the default admin username and password
2. **Secure environment**: Ensure the application runs in a secure environment
3. **Access control**: Only trusted individuals should have admin access
4. **Audit logging**: All admin actions are logged for audit purposes
5. **Session management**: Admin sessions are managed securely

## Troubleshooting

### Common Issues

1. **Admin access denied**: Check if you're logged in as admin
2. **User not found**: Verify the username exists
3. **Balance not updated**: Check for file permissions
4. **API errors**: Check server logs for detailed error messages

### Debug Mode

Enable debug logging by setting the log level in your application:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Bulk operations**: Increase multiple user balances at once
- **Balance history**: View balance change history
- **Notifications**: Email notifications for balance changes
- **Advanced reporting**: Detailed financial reports
- **User management**: Add/remove users from admin panel 
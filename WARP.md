# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a comprehensive restaurant management system built with Flask that supports multiple user roles:
- **Customers**: Place orders, track status, manage favorites
- **Staff**: Manage orders, update status, handle kitchen operations  
- **Couriers**: Manage deliveries, track locations
- **Admins/Super Admins**: System management, analytics, reports

The application features multilingual support (Uzbek, Russian, English, Turkish, Arabic), real-time order tracking, location services, and comprehensive business analytics.

## Development Commands

### Environment Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Create virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
```

### Running the Application
```powershell
# Main application entry point
python app.py

# Alternative entry point
python run.py

# Development mode with specific environment variables
$env:FLASK_ENV="development"
$env:AVG_PREP_MINUTES="5"
$env:SECRET_KEY="your-secret-key"
python app.py
```

### Database Operations
```powershell
# Initialize/recreate database schema
python scripts\run_init_db.py

# Check database tables structure
python scripts\list_tables.py

# Repair corrupted database
python scripts\repair_db.py

# Create chat tables (if needed)
python scripts\create_chat_tables.py
```

### Testing and Debugging
```powershell
# Test menu endpoint functionality
python scripts\check_menu.py

# Test reports functionality 
python tests_report_check.py

# Database sanity check
python scripts\sanity_check.py

# Dump chat data for inspection
python scripts\dump_chats.py
```

### Production Deployment
```powershell
# Run with Gunicorn (production server)
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Keep-alive service for cloud deployments
python keep_alive.py
```

## Core Architecture

### Application Structure
- **app.py**: Main Flask application with all routes and business logic (~5000+ lines)
- **config.py**: Centralized configuration management with environment-aware settings
- **utils.py**: Utility functions for validation, formatting, logging, and system operations
- **location_service.py**: Geolocation services using Serper API and Yandex Geocoder
- **keep_alive.py**: Health check endpoint for cloud deployments

### Database Design
- **SQLite** primary database (instance/restaurant.db)
- Multiple entity tables: users, staff, orders, menu_items, categories, etc.
- Automatic backup system in `backups/` directory
- Database migrations handled through `init_db()` function

### Multi-Role Authentication System
The system uses session-based authentication with different access levels:
- **session['user_type']**: Determines user role ('customer', 'staff', 'courier', 'admin', 'super_admin')
- **session['user_id']**: Unique identifier within role type
- Role-specific decorators and middleware for route protection

### Configuration Management
Environment-aware configuration through `Config` class supports:
- **Development vs Production** modes with different security/logging settings  
- **Database flexibility**: SQLite (development) or PostgreSQL (production)
- **External API integration**: Yandex Geocoder, Serper Places API
- **Business parameters**: prep times, delivery pricing, cashback rates
- **Localization**: 5 languages with timezone-aware operations

### Key Components

#### Order Management System
- Real-time status updates with WebSocket-like polling (10-second intervals)
- ETA calculations considering business hours (9:00-22:00 Asia/Tashkent)
- Multi-status workflow: pending → preparing → ready → completed/cancelled
- Automatic order numbering and tracking

#### Location Services (`LocationService`)
- Address validation with Uzbek location patterns
- Distance calculations using Haversine formula  
- Integration with Serper API for place searches
- Fallback geocoding with Yandex Maps API

#### Multilingual Support
- Dynamic language switching via session
- Currency formatting (UZS, USD, EUR)
- Timezone-aware datetime operations
- RTL language support (Arabic)

#### Business Analytics
- Excel export capabilities for order reports (daily/monthly/yearly)
- Real-time performance monitoring
- User action logging system
- System health metrics via `get_system_info()`

## Important Environment Variables

```powershell
# Core application
$env:FLASK_ENV="development"              # development|production
$env:SECRET_KEY="your-secure-secret-key"
$env:DATABASE_URL="sqlite:///instance/restaurant.db"

# Business configuration  
$env:AVG_PREP_MINUTES="7"                # Default order preparation time
$env:DELIVERY_BASE_PRICE="10000"         # Base delivery cost (UZS)
$env:CASHBACK_PERCENTAGE="1.0"           # Customer cashback rate

# External APIs
$env:SERPER_API_KEY="your-serper-key"    # Places search API
$env:YANDEX_GEOCODER_API="your-yandex-key"  # Address validation

# Localization
$env:DEFAULT_LANGUAGE="uz"               # uz|ru|en|tr|ar  
$env:TIMEZONE="Asia/Tashkent"
$env:DEFAULT_CURRENCY="UZS"

# Performance tuning
$env:REDIS_URL="redis://localhost:6379"  # Rate limiting storage
$env:THREAD_POOL_MAX_WORKERS="10"
```

## Database Schema Patterns

### User Management
- **users**: Customer accounts with phone/email validation
- **staff**: Employee accounts with role hierarchy
- **couriers**: Delivery personnel with location tracking

### Order Processing  
- **orders**: Main order records with status workflow
- **order_items**: Individual items within orders
- **menu_items**: Product catalog with categories and pricing

### Business Operations
- **transactions**: Payment and cashback records
- **deliveries**: Delivery tracking with courier assignment
- **analytics**: Aggregated business metrics

## Common Development Patterns

### Error Handling
All routes use standardized error responses via `create_response()` utility:
```python
return create_response(success=False, message="Error description", status_code=400)
```

### Logging Strategy
- **Structured logging** with detailed formatters for different environments
- **Rotating file handlers** (10MB max, 5 backups)
- **Separate error logs** for production debugging
- **User action logging** for audit trails

### Rate Limiting
Global rate limits applied to all endpoints:
- 1000 requests per day
- 200 requests per hour  
- 50 requests per minute

### Session Management
- 2-hour session lifetime
- Secure cookie settings in production
- Role-based access control throughout application

## Debugging Tips

### Common Issues
1. **Database locked errors**: Check for long-running transactions, use `SKIP_DB_INIT=1` during testing
2. **Location service failures**: Verify API keys and network connectivity  
3. **Session issues**: Clear browser cookies, check session configuration
4. **Import errors**: Ensure all dependencies installed, check Python path

### Log Locations
- **Application logs**: `logs/restaurant.log`
- **Error logs**: `logs/errors.log`  
- **User actions**: `logs/user_actions.log`

### Development Server
Run in development mode for detailed error messages and auto-reload:
```powershell
$env:FLASK_ENV="development"
python app.py
```
Application will be available at http://localhost:5000

## Business Logic Constants

- **Business Hours**: 09:00 - 22:00 (Asia/Tashkent timezone)
- **Order Status Flow**: pending → preparing → ready → delivered/completed
- **Delivery Distance Limit**: 50km from restaurant location  
- **Supported Image Formats**: PNG, JPG, JPEG, WebP (32MB max)
- **Session Duration**: 2 hours (7200 seconds)
- **Database Backup Retention**: 30 days automatic cleanup
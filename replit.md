# Overview

This is a comprehensive restaurant management system built with Flask, designed to handle customer orders, staff operations, courier delivery services, and administrative functions. The system provides a multi-role platform supporting customers, staff members, couriers, and super administrators with distinct interfaces and capabilities.

The application features order management with automatic ticket generation and ETA calculation, menu management with category support and image uploads, real-time order tracking, delivery services with location integration, and comprehensive analytics and reporting tools.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with responsive Bootstrap 5 styling
- **Multi-language Support**: Built-in translation system supporting Uzbek, Russian, English, Turkish, Arabic, and Persian
- **Progressive Web App (PWA)**: Service worker implementation with offline capabilities and caching
- **Real-time Updates**: Auto-refresh functionality for order status and dashboards (10-second intervals)
- **Responsive Design**: Mobile-first approach with CSS Grid and Flexbox layouts

## Backend Architecture
- **Framework**: Flask web framework with modular route organization
- **Session Management**: Flask sessions with configurable timeouts and security settings
- **Authentication**: Multi-role authentication system (customers, staff, couriers, super admin)
- **File Handling**: Image upload system for menu items with validation and storage
- **Error Handling**: Comprehensive error pages and logging system
- **Performance Monitoring**: Built-in performance dashboard and metrics tracking

## Data Storage Solutions
- **Primary Database**: SQLite for development with seamless migration path to PostgreSQL
- **File Storage**: JSON files for employee and user data persistence
- **Session Storage**: Server-side session management with configurable backends
- **Cache Strategy**: Built-in caching for menu items and frequently accessed data
- **Backup System**: Automated data backup and recovery mechanisms

## Authentication and Authorization
- **Multi-tier Access Control**: Four distinct user roles with specific permissions
- **Password Security**: Werkzeug password hashing with salt generation
- **Session Security**: HTTP-only cookies with CSRF protection and secure flags
- **Registration System**: Automated ID generation for staff and couriers
- **Role-based Navigation**: Dynamic menu generation based on user permissions

## Business Logic Components
- **Order Management**: Automated ticket generation with queue position tracking
- **ETA Calculation**: Dynamic preparation time estimation based on queue length
- **Menu Management**: Category-based organization with discount and availability controls
- **Delivery System**: Integrated courier assignment and tracking
- **Rating System**: Customer feedback collection and aggregation
- **Analytics Engine**: Real-time statistics and performance metrics

# External Dependencies

## Core Framework Dependencies
- **Flask 3.0.0**: Main web framework with latest features
- **Werkzeug 3.0.1**: WSGI utilities and security functions
- **Jinja2**: Template rendering engine (via Flask)
- **Bootstrap 5.3.2**: Frontend CSS framework via CDN

## Database and ORM
- **SQLite3**: Built-in Python database for development
- **Flask-SQLAlchemy 3.1.1**: ORM layer for database operations
- **Planned Migration**: PostgreSQL support for production deployment

## Security and Authentication
- **bcrypt 4.1.2**: Password hashing and verification
- **Flask-Limiter 3.5.0**: Rate limiting for API endpoints
- **Flask-CORS 4.0.0**: Cross-origin request handling
- **CSRF Protection**: Built-in Flask-WTF integration

## Media and File Processing
- **Pillow 10.1.0**: Image processing and validation
- **qrcode 7.4.2**: QR code generation for receipts
- **File Upload System**: Custom implementation with validation

## External API Services
- **Yandex Maps API**: Location services and address validation
- **Serper Places API**: Location search and validation services
- **SMS/Email Services**: Notification system integration (configurable)

## Production and Deployment
- **Gunicorn 21.2.0**: WSGI HTTP server for production
- **Flask-Compress 1.14**: Response compression middleware
- **Redis 5.0.1**: Session storage and caching backend
- **psutil 5.9.6**: System monitoring and performance metrics

## Background Processing
- **APScheduler 3.10.4**: Task scheduling and background jobs
- **Celery 5.3.4**: Distributed task processing
- **Threading**: Built-in Python threading for concurrent operations

## Development and Monitoring
- **python-dotenv 1.0.0**: Environment variable management
- **pytz 2023.3**: Timezone handling and localization
- **requests 2.31.0**: HTTP client for external API calls
- **Custom Logging**: Comprehensive logging system with rotation
// Email validation
export const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

// Phone validation (Uzbekistan format)
export const isValidPhone = (phone: string): boolean => {
    const phoneRegex = /^(\+998|998)?[0-9]{9}$/;
    const cleaned = phone.replace(/\s/g, '');
    return phoneRegex.test(cleaned);
};

// Password validation
export const isValidPassword = (password: string): {
    valid: boolean;
    errors: string[];
} => {
    const errors: string[] = [];

    if (password.length < 8) {
        errors.push('Parol kamida 8 ta belgidan iborat bo\'lishi kerak');
    }

    if (!/[A-Z]/.test(password)) {
        errors.push('Parol kamida bitta katta harfni o\'z ichiga olishi kerak');
    }

    if (!/[a-z]/.test(password)) {
        errors.push('Parol kamida bitta kichik harfni o\'z ichiga olishi kerak');
    }

    if (!/[0-9]/.test(password)) {
        errors.push('Parol kamida bitta raqamni o\'z ichiga olishi kerak');
    }

    return {
        valid: errors.length === 0,
        errors,
    };
};

// Required field validation
export const isRequired = (value: any): boolean => {
    if (typeof value === 'string') {
        return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
};

// Min length validation
export const minLength = (value: string, min: number): boolean => {
    return value.length >= min;
};

// Max length validation
export const maxLength = (value: string, max: number): boolean => {
    return value.length <= max;
};

// Number range validation
export const inRange = (value: number, min: number, max: number): boolean => {
    return value >= min && value <= max;
};

// URL validation
export const isValidUrl = (url: string): boolean => {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
};

// Credit card validation (basic Luhn algorithm)
export const isValidCardNumber = (cardNumber: string): boolean => {
    const cleaned = cardNumber.replace(/\s/g, '');

    if (!/^\d{16}$/.test(cleaned)) {
        return false;
    }

    let sum = 0;
    let isEven = false;

    for (let i = cleaned.length - 1; i >= 0; i--) {
        let digit = parseInt(cleaned[i]);

        if (isEven) {
            digit *= 2;
            if (digit > 9) {
                digit -= 9;
            }
        }

        sum += digit;
        isEven = !isEven;
    }

    return sum % 10 === 0;
};

// Form validation helper
export const validateForm = (
    values: Record<string, any>,
    rules: Record<string, Array<(value: any) => string | null>>
): Record<string, string> => {
    const errors: Record<string, string> = {};

    Object.keys(rules).forEach((field) => {
        const fieldRules = rules[field];
        const value = values[field];

        for (const rule of fieldRules) {
            const error = rule(value);
            if (error) {
                errors[field] = error;
                break;
            }
        }
    });

    return errors;
};

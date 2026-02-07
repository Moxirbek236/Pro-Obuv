export interface ApiResponse<T = any> {
    success: boolean;
    data?: T;
    message?: string;
    code?: number;
}

export interface ApiError {
    success: false;
    message: string;
    code: number;
    errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
    success: boolean;
    data: T[];
    page: number;
    limit: number;
    total: number;
    total_pages: number;
}

import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Filter, Search } from 'lucide-react';
import { productsApi } from '@/api/products';
import { Product, ProductFilters as FilterType } from '@/types/product.types';
import ProductCard from '@/components/product/ProductCard';
import ProductFilters from '@/components/product/ProductFilters';
import { useDebounce } from '@/hooks/useDebounce';

// Mock data generator for development
const generateMockProducts = (count: number): Product[] => {
    return Array.from({ length: count }).map((_, index) => ({
        id: index + 1,
        name: `Xavfsizlik Poyabzali ${index + 1}`,
        price: Math.floor(Math.random() * 500000) + 100000,
        category: ['tufli', 'etik', 'krosovka', 'mokasima', 'botik', 'tapochka'][Math.floor(Math.random() * 6)] as any,
        description: 'Yuqori sifatli charm va po\'lat burunli himoya.',
        image_url: `https://placehold.co/400x400?text=Product+${index + 1}`,
        available: true,
        stock_quantity: 50,
        rating: (Math.random() * 2) + 3,
        is_new: Math.random() > 0.8,
        discount_percentage: Math.random() > 0.8 ? 10 : 0,
    }));
};

const MenuPage: React.FC = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const [isMobileFiltersOpen, setIsMobileFiltersOpen] = useState(false);
    const [filters, setFilters] = useState<FilterType>({
        search: searchParams.get('q') || '',
        category: searchParams.get('category') as any || undefined,
    });

    const debouncedSearch = useDebounce(filters.search, 500);

    // In a real app, we would use useQuery to fetch data
    // For now, we'll use mock data and simulating API delay
    const { data: products, isLoading } = useQuery({
        queryKey: ['products', filters, debouncedSearch],
        queryFn: async () => {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 800));

            // Filter mock data
            let data = generateMockProducts(20);

            if (debouncedSearch) {
                data = data.filter(p => p.name.toLowerCase().includes(debouncedSearch.toLowerCase()));
            }

            if (filters.category) {
                data = data.filter(p => p.category === filters.category);
            }

            if (filters.minPrice) {
                data = data.filter(p => p.price >= filters.minPrice!);
            }

            if (filters.maxPrice) {
                data = data.filter(p => p.price <= filters.maxPrice!);
            }

            return { data };
        },
    });

    const handleFilterChange = (newFilters: FilterType) => {
        setFilters(newFilters);

        // Update URL params
        const params = new URLSearchParams();
        if (newFilters.search) params.set('q', newFilters.search);
        if (newFilters.category) params.set('category', newFilters.category);
        setSearchParams(params);
    };

    return (
        <div className="bg-gray-50 dark:bg-gray-900 min-h-screen py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col md:flex-row gap-6">

                    {/* Mobile Filter Button */}
                    <div className="md:hidden flex items-center justify-between mb-4">
                        <h1 className="text-2xl font-bold">Mahsulotlar</h1>
                        <button
                            onClick={() => setIsMobileFiltersOpen(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
                        >
                            <Filter className="w-5 h-5" />
                            <span>Filtrlar</span>
                        </button>
                    </div>

                    {/* Sidebar Filters */}
                    <aside className="hidden md:block w-64 flex-shrink-0">
                        <ProductFilters
                            filters={filters}
                            onFilterChange={handleFilterChange}
                        />
                    </aside>

                    {/* Mobile Filters Drawer */}
                    <ProductFilters
                        filters={filters}
                        onFilterChange={handleFilterChange}
                        isOpen={isMobileFiltersOpen}
                        onClose={() => setIsMobileFiltersOpen(false)}
                    />

                    {/* Main Content */}
                    <div className="flex-1">
                        {/* Search Bar */}
                        <div className="mb-6 relative">
                            <input
                                type="text"
                                placeholder="Mahsulotlarni qidirish..."
                                value={filters.search}
                                onChange={(e) => handleFilterChange({ ...filters, search: e.target.value })}
                                className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800"
                            />
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                        </div>

                        {/* Products Grid */}
                        {isLoading ? (
                            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
                                {[...Array(8)].map((_, i) => (
                                    <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-4 h-80 animate-pulse">
                                        <div className="w-full h-40 bg-gray-200 dark:bg-gray-700 rounded-md mb-4"></div>
                                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
                                        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                                    </div>
                                ))}
                            </div>
                        ) : products?.data?.length === 0 ? (
                            <div className="text-center py-20">
                                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-4">
                                    <Search className="w-8 h-8 text-gray-400" />
                                </div>
                                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                                    Hech narsa topilmadi
                                </h3>
                                <p className="text-gray-500">
                                    Sizning so'rovingiz bo'yicha mahsulotlar mavjud emas. Filtrlarni o'zgartirib ko'ring.
                                </p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
                                {products?.data?.map((product) => (
                                    <ProductCard key={product.id} product={product} />
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MenuPage;

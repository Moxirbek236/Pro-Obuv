import React, { useState } from 'react';
import { Filter, X, Check } from 'lucide-react';
import { ProductFilters as FilterType, ProductCategory } from '@/types/product.types';
import { PRODUCT_CATEGORIES } from '@/utils/constants';

interface ProductFiltersProps {
    filters: FilterType;
    onFilterChange: (newFilters: FilterType) => void;
    isOpen?: boolean;
    onClose?: () => void;
}

const ProductFilters: React.FC<ProductFiltersProps> = ({ filters, onFilterChange, isOpen, onClose }) => {
    const categories = Object.keys(PRODUCT_CATEGORIES) as ProductCategory[];
    const sizes = ['36', '37', '38', '39', '40', '41', '42', '43', '44', '45'];

    // Temporary local state for price inputs
    const [minPrice, setMinPrice] = useState(filters.minPrice?.toString() || '');
    const [maxPrice, setMaxPrice] = useState(filters.maxPrice?.toString() || '');

    const handleCategoryChange = (category: ProductCategory) => {
        onFilterChange({ ...filters, category: filters.category === category ? undefined : category });
    };

    const handleSizeChange = (size: string) => {
        const currentSizes = filters.sizes ? filters.sizes.split(',') : [];
        let newSizes;

        if (currentSizes.includes(size)) {
            newSizes = currentSizes.filter(s => s !== size);
        } else {
            newSizes = [...currentSizes, size];
        }

        onFilterChange({ ...filters, sizes: newSizes.length ? newSizes.join(',') : undefined });
    };

    const applyPriceFilter = () => {
        onFilterChange({
            ...filters,
            minPrice: minPrice ? Number(minPrice) : undefined,
            maxPrice: maxPrice ? Number(maxPrice) : undefined
        });
    };

    return (
        <div className={`
      fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-gray-800 shadow-xl transform transition-transform duration-300 ease-in-out
      md:relative md:transform-none md:w-full md:shadow-none md:bg-transparent
      ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
    `}>
            <div className="h-full overflow-y-auto p-4 md:p-0">
                <div className="flex items-center justify-between mb-6 md:hidden">
                    <h2 className="text-xl font-bold font-heading">Filtrlar</h2>
                    <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Categories */}
                <div className="mb-8">
                    <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">Kategoriyalar</h3>
                    <ul className="space-y-2">
                        {categories.map((cat) => (
                            <li key={cat}>
                                <button
                                    onClick={() => handleCategoryChange(cat)}
                                    className={`flex items-center w-full px-3 py-2 rounded-lg text-sm transition-colors ${filters.category === cat
                                            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300 font-medium'
                                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                                        }`}
                                >
                                    {PRODUCT_CATEGORIES[cat]}
                                    {filters.category === cat && <Check className="w-4 h-4 ml-auto" />}
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Price Range */}
                <div className="mb-8">
                    <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">Narx oralig'i (UZS)</h3>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                        <input
                            type="number"
                            placeholder="Min"
                            value={minPrice}
                            onChange={(e) => setMinPrice(e.target.value)}
                            className="input text-sm"
                        />
                        <input
                            type="number"
                            placeholder="Max"
                            value={maxPrice}
                            onChange={(e) => setMaxPrice(e.target.value)}
                            className="input text-sm"
                        />
                    </div>
                    <button
                        onClick={applyPriceFilter}
                        className="btn btn-outline w-full text-sm py-1"
                    >
                        Qo'llash
                    </button>
                </div>

                {/* Sizes */}
                <div className="mb-8">
                    <h3 className="font-semibold mb-4 text-gray-900 dark:text-white">O'lchamlar</h3>
                    <div className="grid grid-cols-4 gap-2">
                        {sizes.map((size) => {
                            const isSelected = filters.sizes?.split(',').includes(size);
                            return (
                                <button
                                    key={size}
                                    onClick={() => handleSizeChange(size)}
                                    className={`px-2 py-2 text-sm rounded border transition-colors ${isSelected
                                            ? 'bg-primary-600 text-white border-primary-600'
                                            : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:border-primary-500'
                                        }`}
                                >
                                    {size}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Reset Buttons */}
                <button
                    onClick={() => {
                        onFilterChange({});
                        setMinPrice('');
                        setMaxPrice('');
                    }}
                    className="btn btn-ghost w-full text-sm text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10"
                >
                    Filtrlarni tozalash
                </button>
            </div>
        </div>
    );
};

export default ProductFilters;

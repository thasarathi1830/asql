import React from 'react';
import { Search } from 'lucide-react';

interface SearchBarProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  className?: string;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  placeholder = 'Search by account, customer ID, or transaction hash...',
  className = '',
}) => {
  return (
    <div className={`relative flex items-center ${className}`}>
      <Search className="absolute left-3.5 w-4 h-4 text-slate-400 pointer-events-none" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-slate-900/80 border border-phantom-border rounded-lg pl-10 pr-4 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-phantom-accent focus:ring-1 focus:ring-phantom-accent transition-all"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 text-xs text-slate-500 hover:text-slate-300 font-mono"
        >
          CLEAR
        </button>
      )}
    </div>
  );
};


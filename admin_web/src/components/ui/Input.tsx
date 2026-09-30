import React, { type InputHTMLAttributes } from 'react';
import { cn } from './Button';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, id, 'aria-describedby': describedBy, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const errorId = `${inputId}-error`;
    return (
      <div className="w-full">
        {label && <label htmlFor={inputId} className="block text-sm font-medium text-text-muted mb-1">{label}</label>}
        <div className="relative">
          {icon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              "flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
              icon && "pl-10",
              error && "border-red-500 focus-visible:ring-red-500",
              className
            )}
            {...props}
            id={inputId}
            aria-invalid={error ? true : props['aria-invalid']}
            aria-describedby={[describedBy, error ? errorId : null].filter(Boolean).join(' ') || undefined}
          />
        </div>
        {error && <p id={errorId} role="alert" className="mt-1 text-xs text-red-500">{error}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

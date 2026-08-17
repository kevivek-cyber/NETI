import { forwardRef } from 'react';
import clsx from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={clsx(
          variant === 'primary' && 'primary',
          variant === 'secondary' && 'secondary',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? <span className="spinner" aria-hidden="true" /> : null}
        <span>{children}</span>
      </button>
    );
  }
);
Button.displayName = 'Button';

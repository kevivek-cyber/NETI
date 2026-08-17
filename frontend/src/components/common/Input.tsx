import { forwardRef } from 'react';
import clsx from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    return (
      <label htmlFor={id} className={clsx('field', className)}>
        {label}
        <input
          ref={ref}
          id={id}
          className={clsx(error && 'input-error')}
          {...props}
        />
        {error && <span className="error">{error}</span>}
      </label>
    );
  }
);
Input.displayName = 'Input';

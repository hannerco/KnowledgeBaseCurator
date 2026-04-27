import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  isLoading?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", isLoading = false, className = "", children, ...props }, ref) => {
    const baseClass = "block text-center w-full font-semibold text-sm rounded-lg py-2 transition-all duration-150 active:scale-[0.98]";

    const variantClass =
      variant === "primary"
        ? "bg-blue-950 hover:bg-blue-900 text-white shadow-md hover:shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
        : "border border-gray-200 text-gray-600 bg-white hover:bg-indigo-950 hover:text-white";

    return (
      <button
        ref={ref}
        disabled={isLoading || props.disabled}
        className={`${baseClass} ${variantClass} ${className}`}
        {...props}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-r-transparent" />
            {children}
          </span>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

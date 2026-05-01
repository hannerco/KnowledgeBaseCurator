import React from "react";

interface DividerProps {
  text?: string;
  className?: string;
}

export const Divider: React.FC<DividerProps> = ({ text, className = "" }) => {
  if (text) {
    return (
      <div className={`flex items-center gap-3 my-2.5 ${className}`}>
        <div className="flex-1 h-px bg-gray-200" />
        <span className="text-[10px] font-semibold tracking-widest text-gray-600 uppercase">
          {text}
        </span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>
    );
  }

  return <div className={`h-px bg-gray-200 ${className}`} />;
};

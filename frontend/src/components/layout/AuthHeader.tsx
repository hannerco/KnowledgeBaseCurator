"use client";
import { RiGraduationCapLine } from "react-icons/ri";
import Link from "next/link";


interface AuthHeaderProps {
  title?: string;
  subtitle?: string;
  loginLink?: string;
  headerText?: string;
  linkText?: string;
}

export const AuthHeader: React.FC<AuthHeaderProps> = ({
  title = "SchoolAI",
  loginLink = "/login",
  headerText = "¿ya tienes cuenta?",
  linkText = "inicia sesión",
}) => {
  return (
    <header className="bg-white shadow h-auto shrink-0">
      <nav
        aria-label="Global"
        className="mx-auto flex max-w-7xl items-center justify-between p-4 lg:px-8"
      >
        <div className="flex items-center lg:flex-1 gap-x-3">
          <RiGraduationCapLine className="h-8 w-auto text-white p-2 rounded bg-blue-950" />
          <h1 className="text-lg font-bold text-indigo-900">{title}</h1>
        </div>
        {headerText && linkText && (
          <div className="flex items-center gap-x-6">
            <h3 className="text-sm font-normal text-gray-400">
              {headerText}
            </h3>
            <div className="hidden lg:flex lg:flex-1 lg:justify-end">
              <Link href={loginLink} className="text-sm/6 font-semibold text-indigo-900">{linkText}</Link>
              
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};

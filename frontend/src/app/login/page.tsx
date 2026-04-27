import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="max-w-md w-full rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Login</h1>
        <p className="mt-2 text-sm text-slate-500">
          Esta página está en construcción. Por ahora puedes usar el registro.
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <Link
            href="/register"
            className="inline-flex items-center justify-center rounded-full bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800"
          >
            Ir a registro
          </Link>
        </div>
      </div>
    </div>
  );
}

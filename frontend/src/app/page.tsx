import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-center gap-6 py-32 px-16 bg-white dark:bg-black sm:items-start">

        <h1 className="text-3xl font-bold text-zinc-800 dark:text-white">
          Bienvenido
        </h1>

        <div className="flex gap-4">
          <Link
            href="/login"
            className="px-6 py-3 rounded-xl bg-black text-white font-medium shadow-md hover:bg-zinc-800 transition"
          >
            Iniciar sesión
          </Link>

          <Link
            href="/register"
            className="px-6 py-3 rounded-xl bg-white text-black border border-zinc-300 font-medium shadow-sm hover:bg-zinc-100 transition dark:bg-zinc-900 dark:text-white dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            Registrarse
          </Link>
        </div>

      </main>
    </div>
  );
}
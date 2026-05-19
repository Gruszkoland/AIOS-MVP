import Link from "next/link";

const links = [
  { href: "/upload", label: "Upload" },
  { href: "/account", label: "Account" },
  { href: "/history", label: "History" },
  { href: "/pricing", label: "Pricing" },
  { href: "/result", label: "Sample result" },
];

export function SiteHeader() {
  return (
    <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6 lg:px-10">
      <Link href="/" className="text-lg font-bold tracking-[0.2em] uppercase">
        PDF Signal Room
      </Link>
      <nav className="hidden gap-6 text-sm md:flex">
        {links.map((link) => (
          <Link key={link.href} href={link.href} className="text-[color:var(--muted)] transition hover:text-[color:var(--foreground)]">
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}

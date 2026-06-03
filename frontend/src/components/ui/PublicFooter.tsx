import { Link } from "react-router-dom";
import { LEGAL } from "../../legal/legalData";

// Footer público reutilizable con los enlaces legales obligatorios.
export function PublicFooter() {
  return (
    <footer className="border-t border-gray-100 py-8 mt-auto">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-500">
        <div className="font-semibold text-gray-900">
          Scal<span className="text-brand-600">IA</span>
        </div>
        <nav className="flex flex-wrap justify-center gap-x-5 gap-y-2">
          <Link to="/legal/aviso-legal" className="hover:text-brand-600">Aviso legal</Link>
          <Link to="/legal/privacidad" className="hover:text-brand-600">Privacidad</Link>
          <Link to="/legal/cookies" className="hover:text-brand-600">Cookies</Link>
          <Link to="/legal/terminos" className="hover:text-brand-600">Términos</Link>
        </nav>
        <div>© 2026 {LEGAL.companyName}. Todos los derechos reservados.</div>
      </div>
    </footer>
  );
}

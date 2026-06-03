import { type ReactNode } from "react";
import { Link } from "react-router-dom";
import { LEGAL, COOKIES } from "../../legal/legalData";
import { PublicFooter } from "../../components/ui/PublicFooter";

/* ----------------------------------------------------------------------------
 * Layout compartido para las páginas legales (públicas, sin auth).
 * -------------------------------------------------------------------------- */
function LegalLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <header className="border-b border-gray-100">
        <div className="max-w-3xl mx-auto px-6 py-5 flex items-center justify-between">
          <Link to="/" className="font-bold text-lg text-gray-900">
            Scal<span className="text-brand-600">IA</span>
          </Link>
          <Link to="/" className="text-sm text-brand-600 hover:underline">
            ← Volver al inicio
          </Link>
        </div>
      </header>

      <main className="flex-1">
        <article className="max-w-3xl mx-auto px-6 py-12 prose-legal">
          <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
          <p className="text-sm text-gray-400 mt-2 mb-10">
            Última actualización: {LEGAL.lastUpdated}
          </p>
          <div className="space-y-6 text-gray-700 leading-relaxed text-[15px]">
            {children}
          </div>

          <nav className="mt-14 pt-8 border-t border-gray-100 flex flex-wrap gap-x-6 gap-y-2 text-sm text-brand-600">
            <Link to="/legal/aviso-legal" className="hover:underline">Aviso legal</Link>
            <Link to="/legal/privacidad" className="hover:underline">Privacidad</Link>
            <Link to="/legal/cookies" className="hover:underline">Cookies</Link>
            <Link to="/legal/terminos" className="hover:underline">Términos</Link>
          </nav>
        </article>
      </main>

      <PublicFooter />
    </div>
  );
}

function H2({ children }: { children: ReactNode }) {
  return <h2 className="text-xl font-semibold text-gray-900 mt-8 mb-2">{children}</h2>;
}

/* ----------------------------------------------------------------------------
 * 1. Aviso legal (LSSI-CE, Ley 34/2002, art. 10)
 * -------------------------------------------------------------------------- */
export function LegalNotice() {
  return (
    <LegalLayout title="Aviso legal">
      <p>
        En cumplimiento del artículo 10 de la Ley 34/2002, de 11 de julio, de Servicios de
        la Sociedad de la Información y de Comercio Electrónico (LSSI-CE), se informa de los
        datos identificativos del titular de este sitio web y plataforma.
      </p>

      <H2>1. Titular</H2>
      <ul className="list-disc pl-6 space-y-1">
        <li><strong>Denominación social:</strong> {LEGAL.legalName}</li>
        <li><strong>Nombre comercial:</strong> {LEGAL.companyName}</li>
        <li><strong>CIF:</strong> {LEGAL.cif}</li>
        <li><strong>Domicilio social:</strong> {LEGAL.address}</li>
        <li><strong>Correo electrónico:</strong> {LEGAL.contactEmail}</li>
        <li><strong>Sitio web:</strong> {LEGAL.domain}</li>
      </ul>

      <H2>2. Objeto</H2>
      <p>
        {LEGAL.companyName} es una plataforma SaaS de marketing que asiste a sus usuarios en
        la creación, publicación y optimización de campañas publicitarias mediante
        inteligencia artificial. El presente aviso legal regula el uso del sitio web y de la
        plataforma.
      </p>

      <H2>3. Condiciones de uso</H2>
      <p>
        El acceso y uso de la plataforma atribuye la condición de usuario e implica la
        aceptación de este aviso legal, de los <Link to="/legal/terminos" className="text-brand-600 hover:underline">Términos y Condiciones</Link> y
        de la <Link to="/legal/privacidad" className="text-brand-600 hover:underline">Política de Privacidad</Link>. El
        usuario se compromete a hacer un uso lícito de los contenidos y servicios, conforme a
        la ley, la moral y el orden público.
      </p>

      <H2>4. Propiedad intelectual e industrial</H2>
      <p>
        Todos los contenidos del sitio (textos, código, diseños, logotipos, marcas y software)
        son titularidad de {LEGAL.legalName} o de terceros que han autorizado su uso, y están
        protegidos por la normativa de propiedad intelectual e industrial. Queda prohibida su
        reproducción, distribución o transformación sin autorización expresa.
      </p>

      <H2>5. Responsabilidad</H2>
      <p>
        {LEGAL.companyName} no se responsabiliza del contenido generado por los usuarios ni
        del uso que estos hagan de las campañas, copys, imágenes o landings creadas con la
        plataforma. El usuario es el único responsable del cumplimiento de las políticas
        publicitarias de las plataformas de terceros (Meta, etc.) y de la legalidad del
        contenido que publique.
      </p>

      <H2>6. Enlaces externos</H2>
      <p>
        El sitio puede contener enlaces a páginas de terceros. {LEGAL.companyName} no asume
        responsabilidad alguna sobre el contenido o disponibilidad de dichos sitios.
      </p>

      <H2>7. Legislación aplicable</H2>
      <p>
        Las presentes condiciones se rigen por la legislación española. Para cualquier
        controversia, las partes se someten a los juzgados y tribunales del domicilio del
        titular, salvo que la normativa de consumidores establezca otro fuero imperativo.
      </p>
    </LegalLayout>
  );
}

/* ----------------------------------------------------------------------------
 * 2. Política de privacidad (RGPD + LOPDGDD)
 * -------------------------------------------------------------------------- */
export function PrivacyPolicy() {
  return (
    <LegalLayout title="Política de privacidad">
      <p>
        Esta Política de Privacidad regula el tratamiento de los datos personales que
        {" "}{LEGAL.companyName} ({LEGAL.legalName}) realiza de acuerdo con el Reglamento (UE)
        2016/679 (RGPD) y la Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos
        Personales y garantía de los derechos digitales (LOPDGDD).
      </p>

      <H2>1. Responsable del tratamiento</H2>
      <ul className="list-disc pl-6 space-y-1">
        <li><strong>Responsable:</strong> {LEGAL.legalName}</li>
        <li><strong>CIF:</strong> {LEGAL.cif}</li>
        <li><strong>Domicilio:</strong> {LEGAL.address}</li>
        <li><strong>Contacto privacidad:</strong> {LEGAL.privacyEmail}</li>
      </ul>

      <H2>2. Datos que tratamos</H2>
      <p>Según tu relación con nosotros, tratamos las siguientes categorías de datos:</p>
      <ul className="list-disc pl-6 space-y-1">
        <li><strong>Datos de registro y cuenta:</strong> nombre, email, teléfono, contraseña cifrada, tipo de negocio.</li>
        <li><strong>Datos de facturación:</strong> gestionados a través de Stripe (no almacenamos datos completos de tarjeta).</li>
        <li><strong>Datos de uso:</strong> campañas, planes, configuración de empresa y credenciales de servicios conectados (Meta, Resend), almacenadas cifradas.</li>
        <li><strong>Datos de leads de tus campañas:</strong> como usuario de la plataforma, puedes capturar datos de terceros (tus propios clientes potenciales). Respecto de esos datos, tú actúas como responsable y {LEGAL.companyName} como encargado del tratamiento (ver apartado 9).</li>
      </ul>

      <H2>3. Finalidades y bases de legitimación</H2>
      <ul className="list-disc pl-6 space-y-2">
        <li><strong>Prestar el servicio</strong> y gestionar tu cuenta — base: ejecución de contrato (art. 6.1.b RGPD).</li>
        <li><strong>Facturación y cobro</strong> de la suscripción — base: ejecución de contrato y obligación legal (art. 6.1.b y 6.1.c).</li>
        <li><strong>Atención a consultas</strong> y soporte — base: ejecución de contrato / interés legítimo (art. 6.1.f).</li>
        <li><strong>Comunicaciones comerciales</strong> sobre nuestros servicios — base: consentimiento o interés legítimo, con opción de baja en cada comunicación.</li>
        <li><strong>Cumplimiento de obligaciones legales</strong> (fiscales, contables) — base: obligación legal (art. 6.1.c).</li>
      </ul>

      <H2>4. Conservación</H2>
      <p>
        Conservamos los datos mientras la relación contractual esté vigente y, tras su
        finalización, durante los plazos legalmente exigibles (p. ej. 6 años para
        obligaciones mercantiles y fiscales). Después se suprimen o anonimizan.
      </p>

      <H2>5. Destinatarios y encargados</H2>
      <p>
        Para prestar el servicio recurrimos a proveedores que actúan como encargados del
        tratamiento, con los que mantenemos contratos conforme al art. 28 RGPD:
      </p>
      <ul className="list-disc pl-6 space-y-1">
        <li><strong>Stripe</strong> — procesamiento de pagos.</li>
        <li><strong>Proveedor de hosting/infraestructura</strong> — alojamiento de la plataforma.</li>
        <li><strong>OpenAI</strong> — generación de contenido por IA.</li>
        <li><strong>Resend</strong> — envío de emails (con la API key del propio usuario).</li>
        <li><strong>Meta Platforms</strong> — publicación de campañas (con autorización del usuario).</li>
        <li><strong>Cloudinary</strong> — almacenamiento de archivos generados (PDF, imágenes).</li>
      </ul>

      <H2>6. Transferencias internacionales</H2>
      <p>
        Algunos proveedores (p. ej. OpenAI, Stripe, Meta) pueden tratar datos fuera del
        Espacio Económico Europeo. En esos casos las transferencias se amparan en las
        Cláusulas Contractuales Tipo de la Comisión Europea u otras garantías adecuadas
        previstas en el RGPD.
      </p>

      <H2>7. Tus derechos</H2>
      <p>
        Puedes ejercer los derechos de acceso, rectificación, supresión, oposición,
        limitación del tratamiento y portabilidad escribiendo a {LEGAL.privacyEmail},
        acreditando tu identidad. También puedes retirar el consentimiento en cualquier
        momento y presentar una reclamación ante la {LEGAL.authority} si consideras que el
        tratamiento no se ajusta a la normativa.
      </p>

      <H2>8. Seguridad</H2>
      <p>
        Aplicamos medidas técnicas y organizativas apropiadas (cifrado de credenciales en base
        de datos, contraseñas con hash, control de acceso) para proteger los datos frente a su
        pérdida, mal uso o acceso no autorizado.
      </p>

      <H2>9. Datos de tus leads (encargo de tratamiento)</H2>
      <p>
        Cuando capturas leads mediante landings y formularios creados con {LEGAL.companyName},
        tú eres el responsable de esos datos y nosotros los tratamos por cuenta tuya como
        encargado. Eres responsable de informar a esos terceros y de disponer de una base de
        legitimación válida. {LEGAL.companyName} solo tratará dichos datos para prestarte el
        servicio.
      </p>

      <H2>10. Cookies</H2>
      <p>
        El uso de cookies y tecnologías similares se detalla en nuestra{" "}
        <Link to="/legal/cookies" className="text-brand-600 hover:underline">Política de Cookies</Link>.
      </p>
    </LegalLayout>
  );
}

/* ----------------------------------------------------------------------------
 * 3. Política de cookies
 * -------------------------------------------------------------------------- */
export function CookiePolicy() {
  return (
    <LegalLayout title="Política de cookies">
      <p>
        Esta Política de Cookies explica qué cookies y tecnologías de almacenamiento similares
        utiliza {LEGAL.companyName}, conforme al artículo 22.2 de la LSSI-CE y a las
        directrices de la {LEGAL.authority}.
      </p>

      <H2>1. ¿Qué son las cookies?</H2>
      <p>
        Las cookies son pequeños archivos que se almacenan en tu dispositivo al visitar un
        sitio web. Junto a ellas usamos el almacenamiento local del navegador
        (<em>localStorage</em>), que cumple una función equivalente. En esta política, salvo
        que se indique lo contrario, el término «cookies» incluye ambas tecnologías.
      </p>

      <H2>2. Cookies que utilizamos</H2>
      <p>
        En la plataforma usamos exclusivamente <strong>cookies y almacenamiento técnicos o
        necesarios</strong>, exentos de consentimiento según el art. 22.2 LSSI-CE, ya que son
        imprescindibles para la prestación del servicio (mantener la sesión, recordar
        preferencias básicas):
      </p>

      <div className="overflow-x-auto mt-4">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="py-2 pr-4 font-medium">Nombre</th>
              <th className="py-2 pr-4 font-medium">Titular</th>
              <th className="py-2 pr-4 font-medium">Finalidad</th>
              <th className="py-2 pr-4 font-medium">Duración</th>
              <th className="py-2 font-medium">Tipo</th>
            </tr>
          </thead>
          <tbody>
            {COOKIES.map((c) => (
              <tr key={c.name} className="border-b border-gray-100 align-top">
                <td className="py-2 pr-4 font-mono text-xs">{c.name}</td>
                <td className="py-2 pr-4">{c.provider}</td>
                <td className="py-2 pr-4">{c.purpose}</td>
                <td className="py-2 pr-4 whitespace-nowrap">{c.duration}</td>
                <td className="py-2 capitalize">
                  {c.category === "necessary" ? "Técnica" : c.category}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <H2>3. Cookies de terceros en landings publicadas</H2>
      <p>
        Las landing pages que generan los usuarios de la plataforma pueden incorporar, por
        decisión del propio usuario, el píxel de Meta (Facebook) u otras herramientas de
        medición publicitaria. Esas cookies son responsabilidad del usuario que publica la
        landing, quien debe recabar el consentimiento correspondiente de sus visitantes. Esta
        política no cubre dichas cookies de terceros.
      </p>

      <H2>4. Gestión y desactivación</H2>
      <p>
        Al tratarse de cookies técnicas necesarias, no se requiere tu consentimiento, pero
        puedes eliminarlas o bloquearlas desde la configuración de tu navegador. Ten en cuenta
        que desactivarlas puede impedir el correcto funcionamiento de la plataforma (por
        ejemplo, no podrás mantener la sesión iniciada). Consulta la ayuda de tu navegador:
      </p>
      <ul className="list-disc pl-6 space-y-1">
        <li>Google Chrome, Mozilla Firefox, Safari, Microsoft Edge — sección «Privacidad y cookies».</li>
      </ul>

      <H2>5. Actualizaciones</H2>
      <p>
        Podemos actualizar esta política para adaptarla a cambios normativos o técnicos. Te
        recomendamos revisarla periódicamente. Última actualización: {LEGAL.lastUpdated}.
      </p>
    </LegalLayout>
  );
}

/* ----------------------------------------------------------------------------
 * 4. Términos y condiciones
 * -------------------------------------------------------------------------- */
export function Terms() {
  return (
    <LegalLayout title="Términos y condiciones">
      <p>
        Estos Términos y Condiciones regulan la contratación y el uso de la plataforma
        {" "}{LEGAL.companyName}, titularidad de {LEGAL.legalName}. Al registrarte aceptas
        quedar vinculado por ellos.
      </p>

      <H2>1. Objeto del servicio</H2>
      <p>
        {LEGAL.companyName} ofrece un servicio SaaS por suscripción para la creación,
        publicación y optimización de campañas de marketing asistidas por inteligencia
        artificial, con distintos planes y funcionalidades.
      </p>

      <H2>2. Registro y cuenta</H2>
      <p>
        Para usar la plataforma debes crear una cuenta con datos veraces y mantener la
        confidencialidad de tus credenciales. Eres responsable de toda actividad realizada
        desde tu cuenta. Debes ser mayor de edad y, si actúas en nombre de una empresa, tener
        capacidad para obligarla.
      </p>

      <H2>3. Planes, precios y facturación</H2>
      <ul className="list-disc pl-6 space-y-1">
        <li>Los precios y límites de cada plan se muestran en la web y pueden incluir periodo de prueba.</li>
        <li>La suscripción se renueva automáticamente por periodos mensuales salvo cancelación.</li>
        <li>Los pagos se procesan mediante Stripe. Los impuestos aplicables (IVA) se añadirán según corresponda.</li>
        <li>El saldo de escaneos del Research Mode se reinicia cada ciclo y no se acumula.</li>
      </ul>

      <H2>4. Derecho de desistimiento</H2>
      <p>
        Si eres consumidor, dispones de 14 días naturales para desistir. No obstante, al
        tratarse de contenido y servicios digitales, al solicitar el inicio inmediato de la
        prestación reconoces que pierdes el derecho de desistimiento una vez el servicio se ha
        ejecutado por completo, conforme al art. 103 del Real Decreto Legislativo 1/2007.
      </p>

      <H2>5. Cancelación</H2>
      <p>
        Puedes cancelar tu suscripción en cualquier momento desde tu cuenta. La cancelación
        surte efecto al final del periodo de facturación en curso, sin reembolso de los
        importes ya pagados salvo que la ley disponga lo contrario.
      </p>

      <H2>6. Uso aceptable</H2>
      <p>
        Te comprometes a no usar la plataforma para fines ilícitos, engañosos o que infrinjan
        derechos de terceros o las políticas publicitarias de las plataformas conectadas
        (Meta, etc.). Eres el único responsable del contenido que generes y publiques.
      </p>

      <H2>7. Propiedad intelectual</H2>
      <p>
        El software y la plataforma son propiedad de {LEGAL.legalName}. El contenido que
        generes mediante la plataforma (copys, imágenes, landings) es tuyo, sin perjuicio de
        las condiciones de los proveedores de IA empleados.
      </p>

      <H2>8. Limitación de responsabilidad</H2>
      <p>
        El servicio se presta «tal cual». {LEGAL.companyName} no garantiza resultados
        publicitarios concretos ni se responsabiliza de las decisiones de las plataformas de
        terceros (rechazos de anuncios, suspensiones de cuenta). En la medida permitida por la
        ley, nuestra responsabilidad se limita al importe abonado en los últimos 12 meses.
      </p>

      <H2>9. Protección de datos</H2>
      <p>
        El tratamiento de datos personales se rige por la{" "}
        <Link to="/legal/privacidad" className="text-brand-600 hover:underline">Política de Privacidad</Link>.
        Cuando captures datos de terceros mediante la plataforma, actuarás como responsable y
        {" "}{LEGAL.companyName} como encargado del tratamiento.
      </p>

      <H2>10. Modificaciones</H2>
      <p>
        Podemos modificar estos términos notificándolo con antelación razonable. El uso
        continuado tras la entrada en vigor implica su aceptación.
      </p>

      <H2>11. Ley aplicable y jurisdicción</H2>
      <p>
        Estos términos se rigen por la legislación española. Para consumidores aplica el fuero
        legalmente previsto; en el resto de casos, las partes se someten a los juzgados del
        domicilio del titular.
      </p>
    </LegalLayout>
  );
}

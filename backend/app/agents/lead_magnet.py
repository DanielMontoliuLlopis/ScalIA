import asyncio
import io
import json
import uuid
from typing import Any

from app.agents.base import BaseAgent

SYSTEM_PROMPT = """Eres un experto en marketing de contenidos y educación digital.
Tu trabajo es escribir lead magnets (PDFs educativos) que entreguen valor real y posicionen al negocio como autoridad.

REGLAS DE UN LEAD MAGNET QUE FUNCIONA:
- Entrega un quick win concreto que el lector pueda aplicar HOY
- 5-8 secciones, cada una con título claro y desarrollo de 2-4 párrafos
- Lenguaje conversacional, no académico
- Usa ejemplos y casos reales (puedes inventar ejemplos plausibles)
- Cada sección debe poder leerse de forma independiente
- La última sección debe enlazar con la oferta principal del negocio (CTA hacia post_conversion_url)
- Sin relleno — cada párrafo debe aportar
- Tono que conecte con los pain points reales de la audiencia (usa lenguaje EXACTO de la investigación)"""


class LeadMagnetAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        kwargs.setdefault("model", "gpt-4o")
        super().__init__(**kwargs)
        self.system_prompt = SYSTEM_PROMPT

    def _build_context(self, research: dict, copy: dict) -> str:
        lines = []
        if research.get("key_insight"):
            lines.append(f"Key insight: {research['key_insight']}")
        pain_points = research.get("pain_points", [])
        if pain_points:
            lines.append("Pain points reales:")
            for pp in pain_points[:4]:
                lines.append(f'  • "{pp.get("phrase", "")}" → {pp.get("insight", "")}')
        audience_lang = research.get("audience_language", [])
        if audience_lang:
            lines.append("Frases textuales audiencia: " + ", ".join(f'"{p}"' for p in audience_lang[:6]))
        copies = copy.get("copies", [])
        if copies:
            top = copies[0]
            lines.append(f"Hook ganador del copy: {top.get('hook', '')}")
        return "\n".join(lines)

    async def _generate_outline(
        self,
        business: str,
        business_type: str,
        audience: str,
        post_conversion_goal: str,
        post_conversion_url: str,
        context_str: str,
    ) -> dict:
        prompt = f"""Genera el contenido completo de un lead magnet PDF.

NEGOCIO: {business}
TIPO: {business_type}
AUDIENCIA: {audience}
OBJETIVO POST-CONVERSIÓN: {post_conversion_goal}
URL DEL CTA FINAL: {post_conversion_url or "no proporcionada"}

CONTEXTO:
{context_str}

INSTRUCCIONES:
1. Inventa un título magnético (max 12 palabras) que prometa un resultado concreto
2. Subtítulo que amplía el beneficio (max 20 palabras)
3. 5-7 secciones, cada una:
   - heading: título de la sección (max 8 palabras)
   - body: 2-4 párrafos separados por dos saltos de línea ("\\n\\n"). Concretos, accionables.
4. Última sección debe ser el CTA final hacia {post_conversion_goal} (mencionar la URL si existe)

Devuelve SOLO JSON:
{{
  "title": "Título del lead magnet",
  "subtitle": "Subtítulo que amplía la promesa",
  "sections": [
    {{"heading": "Título sección 1", "body": "Párrafo 1.\\n\\nPárrafo 2."}}
  ],
  "estimated_reading_minutes": 8
}}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")

    def _build_pdf(self, outline: dict, primary_color: str = "#6366f1") -> bytes:
        """Genera el PDF con reportlab."""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, PageBreak
        )
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2.5 * cm, bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        accent = HexColor(primary_color)

        cover_title = ParagraphStyle(
            "CoverTitle", parent=styles["Title"],
            fontSize=32, leading=38, alignment=TA_CENTER,
            textColor=accent, spaceAfter=20,
        )
        cover_sub = ParagraphStyle(
            "CoverSub", parent=styles["Normal"],
            fontSize=14, leading=20, alignment=TA_CENTER,
            textColor=HexColor("#555555"), spaceAfter=40,
        )
        section_heading = ParagraphStyle(
            "SectionHeading", parent=styles["Heading1"],
            fontSize=20, leading=26, textColor=accent,
            spaceBefore=20, spaceAfter=12,
        )
        body_style = ParagraphStyle(
            "Body", parent=styles["BodyText"],
            fontSize=11, leading=17, alignment=TA_JUSTIFY,
            textColor=HexColor("#222222"), spaceAfter=10,
        )

        story = []
        story.append(Spacer(1, 4 * cm))
        story.append(Paragraph(outline.get("title", "Lead Magnet"), cover_title))
        if outline.get("subtitle"):
            story.append(Paragraph(outline["subtitle"], cover_sub))
        story.append(PageBreak())

        for section in outline.get("sections", []):
            story.append(Paragraph(section.get("heading", ""), section_heading))
            body = section.get("body", "")
            for paragraph in body.split("\n\n"):
                clean = paragraph.strip().replace("\n", "<br/>")
                if clean:
                    story.append(Paragraph(clean, body_style))
            story.append(Spacer(1, 0.5 * cm))

        doc.build(story)
        return buf.getvalue()

    async def run_task(self, step: dict, context: dict | None = None) -> dict[str, Any]:
        context = context or {}
        research = context.get("ResearchAgent", {})
        copy = context.get("CopyAgent", {})

        business = step.get("business_description") or step.get("saas_description", "")
        business_type = step.get("business_type", "saas")
        audience = step.get("target_customer") or step.get("target_audience", "audiencia objetivo")
        post_conversion_goal = step.get("post_conversion_goal", "thank_you_only")
        post_conversion_url = step.get("post_conversion_url", "") or step.get("redirect_url", "")
        color_palette = step.get("color_palette", "indigo")

        from app.agents.landing import PALETTES
        primary_color = PALETTES.get(color_palette, PALETTES["indigo"])["primary"]

        context_str = self._build_context(research, copy)

        outline = await self._generate_outline(
            business=business,
            business_type=business_type,
            audience=audience,
            post_conversion_goal=post_conversion_goal,
            post_conversion_url=post_conversion_url,
            context_str=context_str,
        )

        # Generar PDF en thread pool (reportlab es síncrono)
        loop = asyncio.get_event_loop()
        pdf_bytes = await loop.run_in_executor(
            None, self._build_pdf, outline, primary_color
        )

        # Subir a Cloudinary
        pdf_url: str | None = None
        try:
            from app.tools.cloudinary_upload import upload_pdf_bytes
            public_id = f"lead_magnet_{uuid.uuid4().hex[:12]}"
            pdf_url = await loop.run_in_executor(
                None, lambda: upload_pdf_bytes(pdf_bytes, public_id=public_id)
            )
        except Exception as exc:
            print(f"[LeadMagnetAgent] Upload error: {exc}")

        return {
            "title": outline.get("title", "Lead magnet"),
            "subtitle": outline.get("subtitle"),
            "sections": outline.get("sections", []),
            "estimated_reading_minutes": outline.get("estimated_reading_minutes"),
            "pdf_url": pdf_url,
            "pdf_size_kb": round(len(pdf_bytes) / 1024, 1),
        }

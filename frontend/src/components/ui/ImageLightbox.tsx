import { useState } from "react";

interface Props {
  images: string[];
  title?: string;
}

export function ImageLightbox({ images, title }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!images.length) return null;

  return (
    <>
      {/* Grid de miniaturas */}
      <div className="grid grid-cols-4 gap-2">
        {images.map((url, i) => (
          <button
            key={i}
            onClick={() => setExpanded(i)}
            className="relative group cursor-pointer rounded-lg overflow-hidden border border-gray-200 hover:border-brand-400 transition-colors"
          >
            <img
              src={url}
              alt={`Imagen ${i + 1}`}
              className="w-full aspect-square object-cover group-hover:opacity-80 transition-opacity"
            />
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/30 transition-opacity">
              <span className="text-white text-sm font-medium">🔍</span>
            </div>
          </button>
        ))}
      </div>

      {/* Modal lightbox */}
      {expanded !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setExpanded(null)}
        >
          <div className="relative max-w-3xl w-full max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <p className="text-white text-sm font-medium">
                {title ? `${title} — ` : ""}Imagen {expanded + 1} de {images.length}
              </p>
              <button
                onClick={() => setExpanded(null)}
                className="text-white hover:text-gray-300 text-2xl leading-none font-bold"
              >
                ✕
              </button>
            </div>

            {/* Imagen ampliada */}
            <img
              src={images[expanded]}
              alt={`Imagen ${expanded + 1}`}
              className="w-full h-full object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />

            {/* Navegación */}
            <div className="flex items-center justify-between mt-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded((expanded - 1 + images.length) % images.length);
                }}
                disabled={images.length <= 1}
                className="px-3 py-1.5 bg-white/10 hover:bg-white/20 disabled:opacity-30 text-white rounded text-sm font-medium transition-colors"
              >
                ← Anterior
              </button>
              <div className="flex gap-1">
                {images.map((_, i) => (
                  <button
                    key={i}
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpanded(i);
                    }}
                    className={`w-2 h-2 rounded-full transition-colors ${
                      i === expanded ? "bg-white" : "bg-white/30"
                    }`}
                  />
                ))}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded((expanded + 1) % images.length);
                }}
                disabled={images.length <= 1}
                className="px-3 py-1.5 bg-white/10 hover:bg-white/20 disabled:opacity-30 text-white rounded text-sm font-medium transition-colors"
              >
                Siguiente →
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

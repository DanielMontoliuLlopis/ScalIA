import { useEffect, useRef, useState } from "react";
import { api } from "../../lib/api";
import type { Plan, CreativeAsset } from "../../store/plansStore";
import { usePlansStore } from "../../store/plansStore";

type CreativeType = "image_ai" | "image_upload" | "video_upload" | "reel_upload" | "meta_post" | "dco";

interface CreativeOption {
  id: CreativeType;
  title: string;
  description: string;
  icon: string;
}

const DCO_OPTION: CreativeOption = {
  id: "dco",
  title: "Creativo dinámico (DCO)",
  description: "Meta combina automáticamente titulares, textos e imágenes para hallar la mejor combinación. No necesitas elegir variantes.",
  icon: "⚡",
};

const OPTIONS_AB: CreativeOption[] = [
  {
    id: "image_ai",
    title: "Imagen generada por IA",
    description: "Generamos 2 imágenes automáticamente a partir del copy.",
    icon: "✨",
  },
  {
    id: "image_upload",
    title: "Subir mis imágenes",
    description: "Sube 2 imágenes JPG/PNG para las variantes A y B.",
    icon: "🖼️",
  },
  {
    id: "video_upload",
    title: "Subir video",
    description: "Sube 2 videos MP4 para feed Facebook/Instagram.",
    icon: "🎬",
  },
  {
    id: "reel_upload",
    title: "Subir Reel IG",
    description: "Video vertical 9:16 específico para Reels.",
    icon: "📱",
  },
  {
    id: "meta_post",
    title: "Usar post existente de Meta",
    description: "Promocionar un post ya publicado en tu página.",
    icon: "🔗",
  },
];

const OPTIONS_SINGLE: CreativeOption[] = [
  DCO_OPTION,
  {
    id: "image_ai",
    title: "Imagen generada por IA",
    description: "Generamos 1 imagen automáticamente a partir del copy.",
    icon: "✨",
  },
  {
    id: "image_upload",
    title: "Subir mi imagen",
    description: "Sube 1 imagen JPG/PNG para el anuncio.",
    icon: "🖼️",
  },
  {
    id: "video_upload",
    title: "Subir video",
    description: "Sube 1 video MP4 para feed Facebook/Instagram.",
    icon: "🎬",
  },
  {
    id: "reel_upload",
    title: "Subir Reel IG",
    description: "Video vertical 9:16 específico para Reels.",
    icon: "📱",
  },
  {
    id: "meta_post",
    title: "Usar post existente de Meta",
    description: "Promocionar un post ya publicado en tu página.",
    icon: "🔗",
  },
];

interface MetaPost {
  post_id: string;
  message: string;
  thumbnail_url: string | null;
  created_time: string;
  media_type: string;
}

interface UploadResponse {
  url: string;
  thumbnail_url: string | null;
  media_type: string;
  width: number | null;
  height: number | null;
}

interface Props {
  plan: Plan;
}

export function CreativeChoiceSelector({ plan }: Props) {
  const { upsertPlan } = usePlansStore();
  // DCO no es compatible con A/B: un solo ad con múltiples assets
  const OPTIONS = plan.ab_testing ? OPTIONS_AB : OPTIONS_SINGLE;
  const [selected, setSelected] = useState<CreativeType | null>(null);
  const [assetA, setAssetA] = useState<CreativeAsset | null>(null);
  const [assetB, setAssetB] = useState<CreativeAsset | null>(null);
  const [uploadingA, setUploadingA] = useState(false);
  const [uploadingB, setUploadingB] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [metaPosts, setMetaPosts] = useState<MetaPost[] | null>(null);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [postsError, setPostsError] = useState<string | null>(null);

  const inputARef = useRef<HTMLInputElement | null>(null);
  const inputBRef = useRef<HTMLInputElement | null>(null);

  const isUpload = selected === "image_upload" || selected === "video_upload" || selected === "reel_upload";
  const uploadKind = selected === "image_upload" ? "image" : "video";
  const accept =
    selected === "image_upload"
      ? "image/jpeg,image/png,image/webp"
      : "video/mp4,video/quicktime,video/webm";

  useEffect(() => {
    setAssetA(null);
    setAssetB(null);
    setError(null);
    if (selected === "meta_post" && !metaPosts && !loadingPosts) {
      setLoadingPosts(true);
      setPostsError(null);
      api
        .get<{ posts: MetaPost[] }>("/uploads/meta/page-posts")
        .then((r) => setMetaPosts(r.posts))
        .catch((e) => setPostsError(e instanceof Error ? e.message : "Error cargando posts"))
        .finally(() => setLoadingPosts(false));
    }
  }, [selected]);

  const handleUpload = async (variant: "A" | "B", file: File) => {
    const setter = variant === "A" ? setAssetA : setAssetB;
    const setLoading = variant === "A" ? setUploadingA : setUploadingB;
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("kind", uploadKind);
      const res = await api.upload<UploadResponse>("/uploads/creative", form);
      setter({
        url: res.url,
        thumbnail_url: res.thumbnail_url,
        media_type: res.media_type,
        width: res.width,
        height: res.height,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al subir");
    } finally {
      setLoading(false);
    }
  };

  const handlePickPost = (variant: "A" | "B", post: MetaPost) => {
    const asset: CreativeAsset = {
      post_id: post.post_id,
      thumbnail_url: post.thumbnail_url,
      media_type: post.media_type === "video" ? "video" : "image",
    };
    if (variant === "A") setAssetA(asset);
    else setAssetB(asset);
  };

  const canSubmit = (() => {
    if (!selected) return false;
    if (selected === "dco") return true;
    if (selected === "image_ai") return true;
    if (!plan.ab_testing) return !!assetA;
    return !!assetA && !!assetB;
  })();

  const handleConfirm = async () => {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { creative_type: selected };
      if (selected !== "image_ai") {
        body.creative_a = assetA;
        if (plan.ab_testing) body.creative_b = assetB;
      }
      const updated = await api.post<Plan>(`/plans/${plan.id}/creative-choice`, body);
      upsertPlan(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al enviar");
    } finally {
      setSubmitting(false);
    }
  };

  const renderVariantSlot = (variant: "A" | "B") => {
    const asset = variant === "A" ? assetA : assetB;
    const uploading = variant === "A" ? uploadingA : uploadingB;
    const ref = variant === "A" ? inputARef : inputBRef;

    if (selected === "meta_post") {
      return (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-2 min-h-[110px]">
          <p className="text-xs font-semibold text-gray-600 mb-1.5">Variante {variant}</p>
          {asset?.post_id ? (
            <div className="flex items-center gap-2">
              {asset.thumbnail_url && (
                <img src={asset.thumbnail_url} className="w-12 h-12 object-cover rounded" alt="" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-700 truncate">Post {asset.post_id}</p>
                <button
                  onClick={() => (variant === "A" ? setAssetA(null) : setAssetB(null))}
                  className="text-xs text-red-500 hover:underline"
                >
                  Cambiar
                </button>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400">Elige un post abajo</p>
          )}
        </div>
      );
    }

    return (
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-2 min-h-[110px] flex flex-col items-center justify-center gap-1.5">
        <p className="text-xs font-semibold text-gray-600">Variante {variant}</p>
        {asset?.url ? (
          <>
            {uploadKind === "image" ? (
              <img src={asset.url} className="w-20 h-20 object-cover rounded" alt="" />
            ) : (
              <video src={asset.url} className="w-20 h-20 object-cover rounded" muted />
            )}
            <button
              onClick={() => (variant === "A" ? setAssetA(null) : setAssetB(null))}
              className="text-xs text-red-500 hover:underline"
            >
              Quitar
            </button>
          </>
        ) : uploading ? (
          <p className="text-xs text-brand-600">Subiendo…</p>
        ) : (
          <button
            onClick={() => ref.current?.click()}
            className="text-xs bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 rounded-md"
          >
            Subir archivo
          </button>
        )}
        <input
          ref={ref}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleUpload(variant, f);
            e.target.value = "";
          }}
        />
      </div>
    );
  };

  return (
    <div className="mt-3 border border-brand-200 bg-brand-50/50 rounded-xl p-4">
      <div className="mb-3">
        <p className="text-xs font-bold text-brand-700 uppercase tracking-wide">Elige el tipo de creativo</p>
        <p className="text-sm text-gray-700 mt-0.5">
          Antes de generar el copy elige cómo se verá tu anuncio.
        </p>
      </div>

      <div className="space-y-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.id}
            onClick={() => setSelected(opt.id)}
            className={`w-full text-left rounded-lg border-2 p-3 transition-all ${
              selected === opt.id
                ? "border-brand-500 bg-white"
                : opt.id === "dco"
                ? "border-amber-200 bg-amber-50/60 hover:border-amber-400"
                : "border-gray-200 bg-white hover:border-brand-300"
            }`}
          >
            <div className="flex items-start gap-2.5">
              <span className="text-xl">{opt.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-1.5">
                  <p className="font-semibold text-gray-900 text-sm">{opt.title}</p>
                  {opt.id === "dco" && (
                    <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">RECOMENDADO</span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-0.5">{opt.description}</p>
              </div>
              <div
                className={`w-4 h-4 rounded-full border-2 flex-shrink-0 mt-1 ${
                  selected === opt.id ? "border-brand-600 bg-brand-600" : "border-gray-300"
                }`}
              >
                {selected === opt.id && (
                  <div className="w-1.5 h-1.5 rounded-full bg-white m-auto mt-0.5" />
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {isUpload && (
        <div className={`mt-3 grid gap-2 ${plan.ab_testing ? "grid-cols-2" : "grid-cols-1"}`}>
          {renderVariantSlot("A")}
          {plan.ab_testing && renderVariantSlot("B")}
        </div>
      )}

      {selected === "meta_post" && (
        <div className="mt-3 space-y-2">
          <div className={`grid gap-2 ${plan.ab_testing ? "grid-cols-2" : "grid-cols-1"}`}>
            {renderVariantSlot("A")}
            {plan.ab_testing && renderVariantSlot("B")}
          </div>

          {loadingPosts && <p className="text-xs text-gray-500">Cargando posts de tu página…</p>}
          {postsError && <p className="text-xs text-red-600">{postsError}</p>}

          {metaPosts && metaPosts.length === 0 && (
            <p className="text-xs text-gray-500">No hay posts en tu página Meta.</p>
          )}

          {metaPosts && metaPosts.length > 0 && (
            <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg divide-y divide-gray-100 bg-white">
              {metaPosts.map((p) => (
                <div key={p.post_id} className="flex items-start gap-2 p-2">
                  {p.thumbnail_url ? (
                    <img src={p.thumbnail_url} className="w-12 h-12 object-cover rounded" alt="" />
                  ) : (
                    <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center text-gray-400 text-xs">
                      {p.media_type}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-700 line-clamp-2">{p.message || "(sin texto)"}</p>
                    <p className="text-[10px] text-gray-400">{new Date(p.created_time).toLocaleDateString()}</p>
                  </div>
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() => handlePickPost("A", p)}
                      className="text-[10px] bg-brand-100 hover:bg-brand-200 text-brand-700 px-2 py-0.5 rounded"
                    >
                      {plan.ab_testing ? "A" : "Usar"}
                    </button>
                    {plan.ab_testing && (
                      <button
                        onClick={() => handlePickPost("B", p)}
                        className="text-[10px] bg-brand-100 hover:bg-brand-200 text-brand-700 px-2 py-0.5 rounded"
                      >
                        B
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}

      <button
        onClick={handleConfirm}
        disabled={!canSubmit || submitting}
        className="mt-3 w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-medium py-2 rounded-lg transition-colors"
      >
        {submitting ? "Aplicando…" : "Confirmar creativo y continuar"}
      </button>
    </div>
  );
}

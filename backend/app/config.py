from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/growthOS"
    REDIS_URL: str = "redis://localhost:6379"

    OPENAI_API_KEY: str = ""

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080

    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    RESEND_API_KEY: str = ""
    BRAVE_API_KEY: str = ""

    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # CORS — orígenes permitidos, separados por coma.
    # Vacío = solo localhost (dev). En producción: "https://app.tudominio.com"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # Owner / superadmin (bypass billing)
    OWNER_EMAILS: str = "llodamont@gmail.com"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_TRIAL_DAYS: int = 7
    STRIPE_CURRENCY: str = "eur"
    # Namespace de app en la cuenta Stripe: si compartes la cuenta con otro SaaS,
    # todos los objetos (products, prices, subscriptions, customers) llevan
    # metadata.app = <este valor> y el webhook ignora lo que no lo lleve.
    STRIPE_APP_NAMESPACE: str = "scalia"

    # Precios mensuales NORMALES en céntimos (EUR) — 3 tiers
    STRIPE_PRICE_STARTER_AMOUNT: int = 9700
    STRIPE_PRICE_GROWTH_AMOUNT: int = 24700
    STRIPE_PRICE_AGENCY_AMOUNT: int = 49700

    # Precios FUNDADOR (50% de por vida) en céntimos (EUR)
    STRIPE_PRICE_STARTER_FOUNDER_AMOUNT: int = 4800
    STRIPE_PRICE_GROWTH_FOUNDER_AMOUNT: int = 12300
    STRIPE_PRICE_AGENCY_FOUNDER_AMOUNT: int = 24800

    # Research Mode — suscripción mensual por escaneos (sin fundador) en céntimos (EUR)
    STRIPE_PRICE_RESEARCH_10_AMOUNT: int = 1500   # €15/mes → 10 escaneos
    STRIPE_PRICE_RESEARCH_100_AMOUNT: int = 9900  # €99/mes → 100 escaneos

    # Programa Fundadores — cupos limitados de por vida
    FOUNDER_SPOTS_LIMIT: int = 20


settings = Settings()

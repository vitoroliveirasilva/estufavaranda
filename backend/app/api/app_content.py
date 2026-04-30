from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import Blueprint, request, url_for
from werkzeug.exceptions import NotFound

from app.core.exceptions import ValidationError
from app.core.response import ok

app_content_bp = Blueprint("app_content", __name__)

_DEFAULT_LOCALE = "pt-BR"
_SUPPORTED_LOCALES = {_DEFAULT_LOCALE}


@dataclass(frozen=True, slots=True)
class AppContentSection:
    id: str
    title: str
    body: str


@dataclass(frozen=True, slots=True)
class AppContentItem:
    slug: str
    title: str
    description: str
    category: str
    content_type: str
    version: str
    locale: str
    icon: str
    published_at: str
    updated_at: str
    sections: tuple[AppContentSection, ...]


_APP_CONTENT: tuple[AppContentItem, ...] = (
    AppContentItem(
        slug="sobre-o-sistema",
        title="Sobre a Estufa da Varanda",
        description=(
            "Conheça a proposta da Estufa da Varanda e entenda como o sistema "
            "ajuda no cuidado diário das suas plantas."
        ),
        category="institutional",
        content_type="markdown",
        version="1.0.0",
        locale="pt-BR",
        icon="sprout",
        published_at="2026-04-30T00:00:00-03:00",
        updated_at="2026-04-30T00:00:00-03:00",
        sections=(
            AppContentSection(
                id="purpose",
                title="Propósito",
                body=(
                    "A Estufa da Varanda é uma plataforma criada para centralizar "
                    "o acompanhamento das suas plantas, reunindo informações sobre "
                    "regas, clima, fotos, eventos e cuidados em um só lugar."
                ),
            ),
            AppContentSection(
                id="features",
                title="Principais recursos",
                body=(
                    "O sistema permite cadastrar plantas, registrar regas, acompanhar "
                    "histórico climático, adicionar fotos, receber notificações e "
                    "consultar informações úteis para manter uma rotina de cuidado "
                    "mais organizada."
                ),
            ),
            AppContentSection(
                id="experience",
                title="Experiência de uso",
                body=(
                    "A experiência foi pensada para ser simples, visual e acessível, "
                    "facilitando o acompanhamento da evolução de cada planta ao longo "
                    "do tempo."
                ),
            ),
        ),
    ),
    AppContentItem(
        slug="politica-de-privacidade",
        title="Política de privacidade",
        description=(
            "Entenda quais informações podem ser utilizadas pela Estufa da Varanda "
            "e como elas ajudam no funcionamento do sistema."
        ),
        category="legal",
        content_type="markdown",
        version="1.0.0",
        locale="pt-BR",
        icon="shield-check",
        published_at="2026-04-30T00:00:00-03:00",
        updated_at="2026-04-30T00:00:00-03:00",
        sections=(
            AppContentSection(
                id="collected-data",
                title="Informações utilizadas",
                body=(
                    "A Estufa da Varanda pode utilizar dados informados pelo próprio "
                    "usuário, como nome das plantas, apelidos, locais de cultivo, "
                    "registros de rega, eventos, fotos e preferências relacionadas "
                    "ao uso do sistema."
                ),
            ),
            AppContentSection(
                id="usage",
                title="Uso das informações",
                body=(
                    "Essas informações são utilizadas para exibir históricos, gerar "
                    "visões organizadas, melhorar a experiência de uso e apoiar "
                    "funcionalidades como notificações, acompanhamento climático e "
                    "consulta de cuidados."
                ),
            ),
            AppContentSection(
                id="security",
                title="Segurança",
                body=(
                    "O sistema deve tratar as informações com medidas técnicas e "
                    "organizacionais adequadas, buscando reduzir riscos de acesso "
                    "indevido, perda ou alteração não autorizada dos dados."
                ),
            ),
            AppContentSection(
                id="user-control",
                title="Controle do usuário",
                body=(
                    "O usuário pode gerenciar os dados cadastrados no sistema por "
                    "meio das funcionalidades disponíveis, incluindo criação, edição "
                    "e exclusão de registros quando aplicável."
                ),
            ),
        ),
    ),
    AppContentItem(
        slug="termos-de-uso",
        title="Termos de uso",
        description=("Veja as condições gerais para utilização da Estufa da Varanda."),
        category="legal",
        content_type="markdown",
        version="1.0.0",
        locale="pt-BR",
        icon="file-text",
        published_at="2026-04-30T00:00:00-03:00",
        updated_at="2026-04-30T00:00:00-03:00",
        sections=(
            AppContentSection(
                id="acceptance",
                title="Aceite dos termos",
                body=(
                    "Ao utilizar a Estufa da Varanda, o usuário declara estar ciente "
                    "das condições de uso do sistema e das funcionalidades oferecidas "
                    "para organização dos cuidados com plantas."
                ),
            ),
            AppContentSection(
                id="responsibilities",
                title="Responsabilidades do usuário",
                body=(
                    "O usuário é responsável pelas informações inseridas no sistema, "
                    "incluindo dados de plantas, registros de cuidados, fotos, eventos "
                    "e demais conteúdos cadastrados em sua conta."
                ),
            ),
            AppContentSection(
                id="availability",
                title="Disponibilidade",
                body=(
                    "A plataforma pode passar por ajustes, manutenções, melhorias ou "
                    "indisponibilidades temporárias para evolução do serviço e correção "
                    "de falhas."
                ),
            ),
            AppContentSection(
                id="changes",
                title="Alterações nos termos",
                body=(
                    "Os termos podem ser atualizados para refletir mudanças no sistema, "
                    "em suas funcionalidades ou em requisitos legais aplicáveis."
                ),
            ),
        ),
    ),
    AppContentItem(
        slug="politica-de-cookies",
        title="Política de cookies",
        description=(
            "Entenda como cookies e tecnologias semelhantes podem ser usados no sistema."
        ),
        category="legal",
        content_type="markdown",
        version="1.0.0",
        locale="pt-BR",
        icon="cookie",
        published_at="2026-04-30T00:00:00-03:00",
        updated_at="2026-04-30T00:00:00-03:00",
        sections=(
            AppContentSection(
                id="what-are-cookies",
                title="O que são cookies",
                body=(
                    "Cookies são pequenos arquivos utilizados pelo navegador para "
                    "armazenar informações necessárias ao funcionamento de páginas, "
                    "sessões e preferências de uso."
                ),
            ),
            AppContentSection(
                id="usage",
                title="Como podem ser utilizados",
                body=(
                    "A Estufa da Varanda pode utilizar cookies ou tecnologias semelhantes "
                    "para manter sessões autenticadas, preservar preferências e melhorar "
                    "a estabilidade da experiência."
                ),
            ),
            AppContentSection(
                id="management",
                title="Gerenciamento",
                body=(
                    "O usuário pode controlar cookies diretamente nas configurações do "
                    "navegador, ciente de que algumas funcionalidades podem depender "
                    "deles para operar corretamente."
                ),
            ),
        ),
    ),
)

_APP_CONTENT_BY_SLUG: dict[str, AppContentItem] = {
    item.slug: item for item in _APP_CONTENT
}

_SLUG_ALIASES = {
    "about": "sobre-o-sistema",
    "sobre": "sobre-o-sistema",
    "sobre-o-app": "sobre-o-sistema",
    "sobre-o-sistema": "sobre-o-sistema",
    "privacy": "politica-de-privacidade",
    "privacy-policy": "politica-de-privacidade",
    "politica": "politica-de-privacidade",
    "politica-de-privacidade": "politica-de-privacidade",
    "terms": "termos-de-uso",
    "terms-of-use": "termos-de-uso",
    "termos": "termos-de-uso",
    "termos-de-uso": "termos-de-uso",
    "cookies": "politica-de-cookies",
    "cookies-policy": "politica-de-cookies",
    "politica-de-cookies": "politica-de-cookies",
}


def _parse_locale() -> str:
    raw_locale = request.args.get("locale", _DEFAULT_LOCALE)
    locale = raw_locale.strip() or _DEFAULT_LOCALE

    if locale not in _SUPPORTED_LOCALES:
        raise ValidationError(
            "Localidade inválida.",
            details={
                "locale": (
                    "Use uma localidade suportada. "
                    f"Valores aceitos: {', '.join(sorted(_SUPPORTED_LOCALES))}."
                )
            },
        )

    return locale


def _normalize_slug(slug: str) -> str:
    return slug.strip().lower()


def _resolve_slug(slug: str) -> str:
    normalized_slug = _normalize_slug(slug)
    return _SLUG_ALIASES.get(normalized_slug, normalized_slug)


def _get_content(slug: str, *, locale: str) -> AppContentItem:
    canonical_slug = _resolve_slug(slug)
    content = _APP_CONTENT_BY_SLUG.get(canonical_slug)

    if content is None or content.locale != locale:
        raise NotFound("Conteúdo não encontrado.")

    return content


def _build_markdown_content(content: AppContentItem) -> str:
    sections = "\n\n".join(
        f"## {section.title}\n\n{section.body}" for section in content.sections
    )
    return f"# {content.title}\n\n{content.description}\n\n{sections}"


def _serialize_section(section: AppContentSection) -> dict[str, str]:
    return {
        "id": section.id,
        "title": section.title,
        "body": section.body,
    }


def _serialize_summary(content: AppContentItem) -> dict[str, Any]:
    return {
        "slug": content.slug,
        "title": content.title,
        "description": content.description,
        "category": content.category,
        "content_type": content.content_type,
        "version": content.version,
        "locale": content.locale,
        "icon": content.icon,
        "published_at": content.published_at,
        "updated_at": content.updated_at,
        "links": {
            "self": url_for(
                "app_content.get_app_content",
                slug=content.slug,
                _external=False,
            )
        },
    }


def _serialize_detail(content: AppContentItem) -> dict[str, Any]:
    return {
        **_serialize_summary(content),
        "sections": [_serialize_section(section) for section in content.sections],
        "content": _build_markdown_content(content),
    }


def _get_content_response(slug: str):
    locale = _parse_locale()
    content = _get_content(slug, locale=locale)
    return ok(_serialize_detail(content))


@app_content_bp.get("/app-content")
def list_app_content():
    locale = _parse_locale()
    items = [
        _serialize_summary(content)
        for content in _APP_CONTENT
        if content.locale == locale
    ]

    return ok(
        items,
        meta={
            "total": len(items),
            "locale": locale,
            "supported_locales": sorted(_SUPPORTED_LOCALES),
        },
    )


@app_content_bp.get("/app-content/<string:slug>")
def get_app_content(slug: str):
    return _get_content_response(slug)


@app_content_bp.get("/about")
def get_about_content():
    return _get_content_response("sobre-o-sistema")


@app_content_bp.get("/privacy-policy")
def get_privacy_policy_content():
    return _get_content_response("politica-de-privacidade")


@app_content_bp.get("/terms-of-use")
def get_terms_of_use_content():
    return _get_content_response("termos-de-uso")


@app_content_bp.get("/cookies-policy")
def get_cookies_policy_content():
    return _get_content_response("politica-de-cookies")

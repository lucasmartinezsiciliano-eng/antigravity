"""
Instagram Service — instagrapi (acceso completo sin Graph API)

PUBLISHING:
  publish_photo()       → foto al feed
  publish_carousel()    → carrusel (hasta 10 imágenes)
  publish_reel()        → reel/video
  publish_story_photo() → historia con foto
  repost()              → reposta foto de barbero/cliente

COMMUNITY:
  send_dm()             → DM directo (códigos, colaboraciones)
  reply_to_comment()    → responder comentario
  like_post()           → dar like
  comment_post()        → comentar post
  follow_user()         → seguir usuario
  unfollow_user()       → dejar de seguir

DISCOVERY:
  get_mentions()        → posts donde etiquetan @xi.parfum
  get_hashtag_top()     → top posts de un hashtag
  get_hashtag_recent()  → posts recientes de un hashtag
  get_user_medias()     → posts de un usuario
  get_user_followers()  → seguidores de un usuario
  search_users()        → buscar usuarios por keyword
  get_location_medias() → posts de una ubicación

ANALYTICS:
  get_account_insights()→ métricas de la cuenta
  get_media_insights()  → métricas de un post concreto
  get_user_info()       → info pública de cualquier cuenta

STORIES:
  get_user_stories()    → historias activas de un usuario
  watch_stories()       → ver historias (te posiciona en sus notificaciones)

GROWTH:
  follow_followers_of() → seguir seguidores de una cuenta rival
  unfollow_non_followers() → limpieza de seguidos que no te siguen
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SESSION_PATH = Path(__file__).parent.parent.parent / "knowledge_base" / "instagrapi_session.json"
USERNAME = os.environ.get("INSTAGRAM_USERNAME", "xi.parfum")
PASSWORD = os.environ.get("INSTAGRAM_PASSWORD", "Barker2013...")

_client_cache = None


def _get_client(force_relogin: bool = False):
    global _client_cache
    if _client_cache and not force_relogin:
        return _client_cache

    try:
        from instagrapi import Client
    except ImportError:
        raise RuntimeError("pip install instagrapi")

    cl = Client()
    cl.delay_range = [2, 5]

    if SESSION_PATH.exists() and not force_relogin:
        try:
            cl.load_settings(str(SESSION_PATH))
            cl.login(USERNAME, PASSWORD)
            cl.get_timeline_feed()
            _client_cache = cl
            return cl
        except Exception:
            logger.info("Session expired — fresh login")

    cl = Client()
    cl.delay_range = [2, 5]
    cl.login(USERNAME, PASSWORD)
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    cl.dump_settings(str(SESSION_PATH))
    logger.info("Session saved → %s", SESSION_PATH)
    _client_cache = cl
    return cl


# ── PUBLISHING ────────────────────────────────────────────────────────────────

def publish_photo(image_path: str, caption: str, hashtags: list[str] = None) -> Optional[str]:
    """Publica una foto en el feed. Devuelve URL del post o None."""
    if hashtags:
        caption += "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    try:
        cl = _get_client()
        media = cl.photo_upload(image_path, caption)
        url = f"https://instagram.com/p/{media.code}/"
        logger.info("Photo published: %s", url)
        return url
    except Exception as e:
        logger.error("publish_photo: %s", e)
        return None


def publish_carousel(image_paths: list[str], caption: str, hashtags: list[str] = None) -> Optional[str]:
    """Publica un carrusel de hasta 10 imágenes. Ideal para contenido educativo."""
    if hashtags:
        caption += "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    try:
        cl = _get_client()
        paths = [Path(p) for p in image_paths]
        media = cl.album_upload(paths, caption)
        url = f"https://instagram.com/p/{media.code}/"
        logger.info("Carousel published (%d slides): %s", len(paths), url)
        return url
    except Exception as e:
        logger.error("publish_carousel: %s", e)
        return None


def publish_reel(video_path: str, caption: str, hashtags: list[str] = None,
                 thumbnail_path: Optional[str] = None) -> Optional[str]:
    """Publica un reel."""
    if hashtags:
        caption += "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags)
    try:
        cl = _get_client()
        extra = {"thumbnail": thumbnail_path} if thumbnail_path else {}
        media = cl.clip_upload(video_path, caption, **extra)
        url = f"https://instagram.com/p/{media.code}/"
        logger.info("Reel published: %s", url)
        return url
    except Exception as e:
        logger.error("publish_reel: %s", e)
        return None


def publish_story_photo(image_path: str) -> Optional[str]:
    """Publica una historia con foto."""
    try:
        cl = _get_client()
        cl.photo_upload_to_story(image_path)
        logger.info("Story published")
        return f"https://instagram.com/stories/{USERNAME}/"
    except Exception as e:
        logger.error("publish_story: %s", e)
        return None


def repost(media_url: str, caption: str, credit_username: str = None) -> Optional[str]:
    """Descarga y reposta contenido de barbero/cliente con crédito."""
    if credit_username:
        caption = f"📸 @{credit_username.lstrip('@')}\n\n{caption}"
    try:
        resp = requests.get(media_url, timeout=15)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(resp.content)
            tmp = f.name
        result = publish_photo(tmp, caption)
        Path(tmp).unlink(missing_ok=True)
        return result
    except Exception as e:
        logger.error("repost: %s", e)
        return None


# ── COMMUNITY ─────────────────────────────────────────────────────────────────

def send_dm(username: str, text: str) -> bool:
    """Envía un DM. Usado para códigos de descuento UGC."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        cl.direct_send(text, [user_id])
        logger.info("DM → @%s", username)
        return True
    except Exception as e:
        logger.error("send_dm @%s: %s", username, e)
        return False


def reply_to_comment(media_id: str, comment_id: str, text: str) -> bool:
    """Responde a un comentario en un post."""
    try:
        cl = _get_client()
        cl.media_comment(media_id, text, replied_to_comment_id=comment_id)
        return True
    except Exception as e:
        logger.error("reply_comment: %s", e)
        return False


def comment_post(media_id: str, text: str) -> bool:
    """Comenta en un post."""
    try:
        cl = _get_client()
        cl.media_comment(media_id, text)
        return True
    except Exception as e:
        logger.error("comment_post: %s", e)
        return False


def like_post(media_id: str) -> bool:
    """Da like a un post."""
    try:
        cl = _get_client()
        cl.media_like(media_id)
        return True
    except Exception as e:
        logger.error("like_post: %s", e)
        return False


def follow_user(username: str) -> bool:
    """Sigue a un usuario."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        cl.user_follow(user_id)
        logger.info("Followed @%s", username)
        return True
    except Exception as e:
        logger.error("follow @%s: %s", username, e)
        return False


def unfollow_user(username: str) -> bool:
    """Deja de seguir a un usuario."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        cl.user_unfollow(user_id)
        return True
    except Exception as e:
        logger.error("unfollow @%s: %s", username, e)
        return False


# ── DISCOVERY ─────────────────────────────────────────────────────────────────

def get_mentions(limit: int = 20) -> list[dict]:
    """Posts donde etiquetan @xi.parfum."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(USERNAME)
        tagged = cl.usertag_medias(user_id, amount=limit)
        return [_media_to_dict(m) for m in tagged]
    except Exception as e:
        logger.error("get_mentions: %s", e)
        return []


def get_hashtag_top(tag: str, limit: int = 20) -> list[dict]:
    """Top posts virales de un hashtag. Para detectar tendencias."""
    try:
        cl = _get_client()
        medias = cl.hashtag_medias_top(tag.lstrip("#"), amount=limit)
        return [_media_to_dict(m) for m in medias]
    except Exception as e:
        logger.error("hashtag_top #{}: {}".format(tag, e))
        return []


def get_hashtag_recent(tag: str, limit: int = 30) -> list[dict]:
    """Posts recientes de un hashtag. Para repostar contenido fresco."""
    try:
        cl = _get_client()
        medias = cl.hashtag_medias_recent(tag.lstrip("#"), amount=limit)
        return [_media_to_dict(m) for m in medias]
    except Exception as e:
        logger.error("hashtag_recent #{}: {}".format(tag, e))
        return []


def get_user_medias(username: str, limit: int = 12) -> list[dict]:
    """Posts recientes de cualquier cuenta. Para analizar competidores."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        medias = cl.user_medias(user_id, amount=limit)
        return [_media_to_dict(m) for m in medias]
    except Exception as e:
        logger.error("user_medias @%s: %s", username, e)
        return []


def get_user_followers(username: str, limit: int = 100) -> list[str]:
    """Lista de seguidores de una cuenta. Para estrategia de follow/outreach."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        followers = cl.user_followers(user_id, amount=limit)
        return [u.username for u in followers.values()]
    except Exception as e:
        logger.error("user_followers @%s: %s", username, e)
        return []


def search_users(query: str, limit: int = 10) -> list[dict]:
    """Busca usuarios por nombre/keyword. Para encontrar barberos/influencers."""
    try:
        cl = _get_client()
        results = cl.search_users(query, count=limit)
        return [
            {
                "username": u.username,
                "full_name": u.full_name,
                "followers": u.follower_count,
                "is_verified": u.is_verified,
                "is_business": u.is_business,
            }
            for u in results
        ]
    except Exception as e:
        logger.error("search_users '%s': %s", query, e)
        return []


def get_user_info(username: str) -> Optional[dict]:
    """Info pública de cualquier cuenta."""
    try:
        cl = _get_client()
        user = cl.user_info_by_username(username)
        return {
            "username": user.username,
            "full_name": user.full_name,
            "followers": user.follower_count,
            "following": user.following_count,
            "posts": user.media_count,
            "bio": user.biography,
            "is_verified": user.is_verified,
            "is_business": user.is_business,
            "profile_pic_url": str(user.profile_pic_url) if user.profile_pic_url else None,
            "engagement_rate": round((user.follower_count or 1) and 0, 2),
        }
    except Exception as e:
        logger.error("user_info @%s: %s", username, e)
        return None


# ── STORIES ───────────────────────────────────────────────────────────────────

def get_user_stories(username: str) -> list[dict]:
    """Historias activas de un usuario (si son públicas)."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        stories = cl.user_stories(user_id)
        return [
            {
                "story_id": str(s.id),
                "taken_at": s.taken_at.isoformat() if s.taken_at else None,
                "media_type": s.media_type,
                "thumbnail_url": str(s.thumbnail_url) if s.thumbnail_url else None,
                "mentions": [m.user.username for m in (s.usertags or []) if m.user],
            }
            for s in stories
        ]
    except Exception as e:
        logger.error("user_stories @%s: %s", username, e)
        return []


def watch_stories(username: str) -> bool:
    """Ve las historias de un usuario (apareces en sus vistas → notificación)."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(username)
        stories = cl.user_stories(user_id)
        if stories:
            cl.story_seen([s.id for s in stories])
            logger.info("Watched %d stories from @%s", len(stories), username)
        return True
    except Exception as e:
        logger.error("watch_stories @%s: %s", username, e)
        return False


# ── GROWTH ────────────────────────────────────────────────────────────────────

def follow_followers_of(target_username: str, limit: int = 50, min_followers: int = 100) -> list[str]:
    """
    Sigue seguidores de una cuenta rival/complementaria.
    Solo sigue cuentas con mínimo min_followers seguidores (filtra bots).
    """
    followed = []
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(target_username)
        followers = cl.user_followers(user_id, amount=limit * 3)

        for uid, user in list(followers.items())[:limit * 3]:
            if len(followed) >= limit:
                break
            try:
                info = cl.user_info(uid)
                if info.follower_count < min_followers:
                    continue
                if info.is_private:
                    continue
                cl.user_follow(uid)
                followed.append(info.username)
                logger.info("Followed @%s (%d followers)", info.username, info.follower_count)
                time.sleep(3)  # avoid rate limits
            except Exception:
                continue

        logger.info("Followed %d accounts from @%s's followers", len(followed), target_username)
        return followed
    except Exception as e:
        logger.error("follow_followers_of @%s: %s", target_username, e)
        return followed


def unfollow_non_followers(limit: int = 50) -> list[str]:
    """
    Deja de seguir cuentas que no te siguen de vuelta.
    Ejecutar periódicamente para mantener ratio seguidos/seguidores sano.
    """
    unfollowed = []
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(USERNAME)

        following = cl.user_following(user_id, amount=limit * 2)
        followers = cl.user_followers(user_id, amount=limit * 2)
        follower_ids = set(followers.keys())

        for uid, user in list(following.items()):
            if len(unfollowed) >= limit:
                break
            if uid not in follower_ids:
                try:
                    cl.user_unfollow(uid)
                    unfollowed.append(user.username)
                    logger.info("Unfollowed @%s (not following back)", user.username)
                    time.sleep(2)
                except Exception:
                    continue

        return unfollowed
    except Exception as e:
        logger.error("unfollow_non_followers: %s", e)
        return unfollowed


# ── ANALYTICS ─────────────────────────────────────────────────────────────────

def get_account_insights() -> dict:
    """Métricas de la cuenta propia."""
    try:
        cl = _get_client()
        user_id = cl.user_id_from_username(USERNAME)
        user = cl.user_info(user_id)
        medias = cl.user_medias(user_id, amount=12)

        total_likes = sum(m.like_count or 0 for m in medias)
        total_comments = sum(m.comment_count or 0 for m in medias)
        n = len(medias) or 1
        followers = user.follower_count or 1

        return {
            "followers": user.follower_count,
            "following": user.following_count,
            "posts": user.media_count,
            "avg_likes": round(total_likes / n),
            "avg_comments": round(total_comments / n),
            "engagement_rate": round((total_likes + total_comments) / n / followers * 100, 2),
            "best_post": max(medias, key=lambda m: (m.like_count or 0) + (m.comment_count or 0), default=None) and
                         f"https://instagram.com/p/{max(medias, key=lambda m: (m.like_count or 0)).code}/",
        }
    except Exception as e:
        logger.error("account_insights: %s", e)
        return {}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _media_to_dict(m) -> dict:
    thumb = None
    if hasattr(m, "thumbnail_url") and m.thumbnail_url:
        thumb = str(m.thumbnail_url)
    elif hasattr(m, "resources") and m.resources:
        r = m.resources[0]
        thumb = str(r.thumbnail_url) if r.thumbnail_url else None

    return {
        "media_id": str(m.pk),
        "shortcode": m.code,
        "username": m.user.username if m.user else "unknown",
        "post_url": f"https://instagram.com/p/{m.code}/",
        "thumbnail_url": thumb,
        "caption": m.caption_text or "",
        "like_count": m.like_count or 0,
        "comment_count": m.comment_count or 0,
        "timestamp": m.taken_at.isoformat() if m.taken_at else None,
        "media_type": m.media_type,
    }

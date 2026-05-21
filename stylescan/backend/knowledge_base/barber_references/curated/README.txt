CURATED REFERENCE IMAGES -- NUCAS/FADES (back-of-head only)
============================================================

CRITICAL: These images are the HAIRSTYLE REFERENCE passed to fal.ai FLUX
multi-image mode alongside the client's face photo.

!!! DO NOT use photos that show a person's face !!!
    FLUX will blend the reference person's face with the client's => wrong face.
    Use ONLY back-of-head / nape / nuca shots.

IDEAL PHOTO:
  - Client turned with their back to camera (face not visible)
  - Neck/nape line clearly visible
  - Fade level (low / mid / high / skin) visible on sides
  - Hair length and texture on crown clearly visible
  - Clean background (salon chair or neutral wall)
  - Professional barbershop "after" style

Specs:
  - Format: .jpg
  - Resolution: 768x1024 or larger (portrait)
  - 1 image per cut is enough

----------------------------------------------------------------------
15 CUTS TO GATHER -- Pinterest/Instagram search terms:

  FILE TO DROP                 SEARCH TERM (Pinterest / Instagram)
  -------------------------------------------------------------------
  skin_fade_textured.jpg       "skin fade nuca espaldas barberia"
                               OR "skin fade back nape barbershop"

  french_crop_low_fade.jpg     "french crop nuca fade"
                               OR "french crop back nape"

  modern_mullet_fade.jpg       "mullet moderno nuca espalda"
                               OR "modern mullet back nape fade"

  wolf_cut.jpg                 "wolf cut nuca hombre"
                               OR "wolf cut men back view"

  quiff_mid_fade.jpg           "quiff fade nuca espalda"
                               OR "quiff back nape men"

  buzz_cut_taper.jpg           "buzz cut taper nuca"
                               OR "buzz cut back nape"

  high_fade_hard_part.jpg      "high fade nuca espalda"
                               OR "high fade back view nape"

  curtain_bangs.jpg            "flequillo cortina nuca taper"
                               OR "curtain bangs back nape taper"

  zero_fade_beard.jpg          "skin fade barba nuca"
                               OR "zero fade beard back nape"

  classic_taper_natural.jpg    "taper clasico nuca"
                               OR "classic taper back nape"

  slick_back_low_fade.jpg      "slick back fade nuca"
                               OR "slick back low fade nape"

  natural_curls_taper.jpg      "rizos taper nuca"
                               OR "curly taper back nape men"

  pompadour_mid_fade.jpg       "pompadour fade nuca espalda"
                               OR "pompadour back nape mid fade"

  textured_fringe_taper.jpg    "flequillo texturizado taper nuca"
                               OR "textured fringe taper back nape"

  number2_full_beard.jpg       "numero 2 barba nuca"
                               OR "buzz cut beard back nape"
----------------------------------------------------------------------

Runtime resolution order (haircut_reference_service.py):
  1. Curated local file (THIS DIR)    <- highest priority, zero API cost
  2. Disk-cached Pexels URL
  3. Live Pexels search               <- pexels queries also target nucas now
  4. None -> text-only FLUX Kontext Max (explicit IDENTITY LOCK prompt)

Without curated images: text-only mode. Face is preserved via prompt locking.
With curated images:    multi-image mode. FLUX copies the hairstyle from the
                        nuca reference without any competing face to blend with.

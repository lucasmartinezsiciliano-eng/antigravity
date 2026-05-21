"""
Busca barberos influyentes en Instagram por hashtags de Madrid y Barcelona.
Extrae: username, seguidores, bio, email de contacto, ciudad estimada.
"""
import instaloader
import time
import json
import pandas as pd
from datetime import datetime

L = instaloader.Instaloader()

# Login con la cuenta que ya tenemos configurada
try:
    L.login("xi.parfum", "Barker2013...")
    print("Login OK")
except Exception as e:
    print(f"Login error: {e} — continuando sin login (menos datos)")

HASHTAGS = [
    "barberiamadrid",
    "barberomadrid",
    "barbersmadrid",
    "barberiabcn",
    "barberobcn",
    "barbershopbarcelona",
    "barberosespana",
    "barberosspain",
    "visagismomadrid",
    "cortedemadrid",
]

seen = set()
profiles = []

for tag in HASHTAGS:
    print(f"\n→ Hashtag: #{tag}")
    try:
        hashtag = instaloader.Hashtag.from_name(L.context, tag)
        count = 0
        for post in hashtag.get_top_posts():
            username = post.owner_username
            if username in seen:
                continue
            seen.add(username)
            try:
                profile = instaloader.Profile.from_username(L.context, username)
                followers = profile.followers
                if followers < 1000:  # filtrar cuentas pequeñas
                    continue
                bio = profile.biography or ""
                email = ""
                # Extraer email de bio
                import re
                email_match = re.search(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', bio)
                if email_match:
                    email = email_match.group(0)

                entry = {
                    "username": username,
                    "nombre": profile.full_name,
                    "seguidores": followers,
                    "siguiendo": profile.followees,
                    "posts": profile.mediacount,
                    "bio": bio[:150],
                    "email": email,
                    "url": f"https://instagram.com/{username}",
                    "hashtag_encontrado": tag,
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                }
                profiles.append(entry)
                print(f"  ✓ @{username} — {followers:,} seguidores")
                count += 1
                time.sleep(2)
            except Exception as e:
                print(f"  ✗ @{username}: {e}")
                time.sleep(1)
        print(f"  Total nuevos: {count}")
        time.sleep(5)
    except Exception as e:
        print(f"  ERROR en #{tag}: {e}")
        time.sleep(3)

# Ordenar por seguidores y guardar
df = pd.DataFrame(profiles)
if not df.empty:
    df = df.drop_duplicates(subset=["username"])
    df = df.sort_values("seguidores", ascending=False)
    output = "c:/Users/Pc2025/Desktop/ANTIGRAVITY/leads/barberos_influencers.xlsx"
    df.to_excel(output, index=False)
    print(f"\n{'='*50}")
    print(f"Total encontrados: {len(df)}")
    print(f"Con email: {df['email'].notna().sum()}")
    print(f"\nTOP 20:")
    print(df[["username","seguidores","email","bio"]].head(20).to_string())
    print(f"\nGuardado: {output}")
else:
    print("No se encontraron perfiles")

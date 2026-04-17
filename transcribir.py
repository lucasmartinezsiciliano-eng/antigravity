import whisper
import os
import sys

# Apuntar ffmpeg directamente (winget lo instaló aquí)
FFMPEG_PATH = r"C:\Users\Pc2025\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin"
os.environ["PATH"] = FFMPEG_PATH + os.pathsep + os.environ.get("PATH", "")

# Carpeta de audios
CARPETA = os.path.join(os.path.dirname(__file__), "audios")

def transcribir(archivo):
    print(f"\nCargando modelo Whisper...")
    model = whisper.load_model("base")
    print(f"Transcribiendo: {archivo}\n")
    result = model.transcribe(archivo, language="es")
    texto = result["text"]
    print("=" * 60)
    print("TRANSCRIPCIÓN:")
    print("=" * 60)
    print(texto)
    print("=" * 60)

    # Guardar transcripción en archivo
    nombre_salida = os.path.splitext(archivo)[0] + "_transcripcion.txt"
    with open(nombre_salida, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"\nGuardado en: {nombre_salida}")
    return texto

if __name__ == "__main__":
    # Si se pasa un archivo como argumento
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
    else:
        # Buscar audios en la carpeta
        archivos = [f for f in os.listdir(CARPETA) if f.endswith((".opus", ".mp3", ".mp4", ".m4a", ".wav", ".ogg"))]
        if not archivos:
            print("No hay audios en la carpeta 'audios/'")
            print("Pon el archivo de audio en: audios/")
            sys.exit(1)
        # Usar el más reciente
        archivos.sort(key=lambda f: os.path.getmtime(os.path.join(CARPETA, f)), reverse=True)
        archivo = os.path.join(CARPETA, archivos[0])
        print(f"Audio encontrado: {archivos[0]}")

    transcribir(archivo)

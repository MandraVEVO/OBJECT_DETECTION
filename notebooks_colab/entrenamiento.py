from google.colab import drive
drive.mount('/content/drive')

print("✅ Drive montado correctamente")

# ══════════════════════════════════════════════════════════════════
# CELDA 2 — Creacion de espacio con carpetas para videos y frames
# ══════════════════════════════════════════════════════════════════



import os


BASE = '/content/drive/MyDrive/mechdog_proyecto'

# Subcarpetas
VIDEOS_DIR   = f'{BASE}/videos_raw'    
FRAMES_DIR   = f'{BASE}/frames'        

#creacion de carpetas
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

print("Estructura de carpetas:")
print(f"Videos fuente  → {VIDEOS_DIR}")
print(f"Frames salida  → {FRAMES_DIR}")

# ══════════════════════════════════════════════════════════════════
# CELDA 3 — Verificar videos disponibles
# ══════════════════════════════════════════════════════════════════

import cv2

extensiones_validas = ('.mp4', '.mov', '.MP4', '.MOV', '.avi', '.AVI')

videos = sorted([
    f for f in os.listdir(VIDEOS_DIR)
    if f.endswith(extensiones_validas)
])

if not videos:
    print("⚠️  No se encontraron videos en:", VIDEOS_DIR)
    print("    Sube tus videos a esa carpeta y vuelve a ejecutar.")
else:
    print(f"✅ {len(videos)} videos encontrados:\n")
    total_dur = 0
    for v in videos:
        ruta = f'{VIDEOS_DIR}/{v}'
        cap  = cv2.VideoCapture(ruta)
        fps  = cap.get(cv2.CAP_PROP_FPS)
        tot  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        dur  = tot / fps if fps > 0 else 0
        tam  = os.path.getsize(ruta) / (1024*1024)
        cap.release()
        total_dur += dur
        print(f"  {v:<45} {dur:>5.1f}s  {fps:.0f}fps  {tam:.1f}MB")

    print(f"\n  Total: {total_dur:.0f}s  ({total_dur/60:.1f} minutos)")

# ══════════════════════════════════════════════════════════════════
# CELDA 4 — Mapa de clases (actualizado con caja y pasillo 2)
# ══════════════════════════════════════════════════════════════════

# Las claves más específicas van PRIMERO para evitar coincidencias parciales
MAPA_CLASES = {

    # ── Combos de múltiples objetos ──────────────────────────────
    '1mochilabien_1sillamal_2mochilabien': 'mochila_ok + silla_riesgo',
    '1mochilamal_2mochilasbien':           'mochila_riesgo + mochila_ok',
    '1mochilabien_1mochilamal':            'mochila_ok + mochila_riesgo',
    '1sillamal_1mochilabien_1cablebien':   'silla_riesgo + mochila_ok + cables_ok',
    '1mochilabien_1cajabien_1cablebien':   'mochila_ok + caja_ok + cables_ok',
    '1mochila1bolsabien':                  'mochila_ok + bolsa_ok',
    '2mochilasmal':                        'mochila_riesgo',
    '2mochilasbien':                       'mochila_ok',
    '2mochilabien':                        'mochila_ok',

    # ── Un solo objeto ────────────────────────────────────────────
    '1mochilamal':  'mochila_riesgo',
    '1mochilabien': 'mochila_ok',
    'mochilamal':   'mochila_riesgo',
    'mochilabien':  'mochila_ok',
    'sillamal':     'silla_riesgo',
    'mesamal':      'mesa_riesgo',
    'cablesbien':   'cables_ok',
    'cablebien':    'cables_ok',
    'cajabien':     'caja_ok',

    # ── Fondo libre — NO se etiqueta ─────────────────────────────
    'pasillolibre': 'fondo_libre',
}

def detectar_clase(nombre_video):
    nombre_lower = nombre_video.lower()
    for clave, clase in MAPA_CLASES.items():
        if clave in nombre_lower:
            return clase
    return '❓ sin clasificar'

print("✅ Mapa de clases listo con", len(MAPA_CLASES), "entradas")

# ══════════════════════════════════════════════════════════════════
# CELDA 4 — Verificar los 36 videos
# ══════════════════════════════════════════════════════════════════
import cv2

extensiones = ('.mp4', '.mov', '.MP4', '.MOV')

videos = sorted([
    f for f in os.listdir(VIDEOS_DIR)
    if any(f.lower().endswith(e.lower()) for e in extensiones)
])

print(f"✅ {len(videos)} videos encontrados:\n")
print(f"  {'Archivo':<58} {'Dur':>6}  {'~Imgs':>6}  Clase detectada")
print(f"  {'─'*110}")

total_dur       = 0
total_imgs_est  = 0
sin_clase       = []
doble_ext       = []

for v in videos:
    # Detectar doble extensión
    if v.count('.MP4') + v.count('.mp4') + v.count('.mov') > 1:
        doble_ext.append(v)

    ruta = f'{VIDEOS_DIR}/{v}'
    cap  = cv2.VideoCapture(ruta)
    fps  = cap.get(cv2.CAP_PROP_FPS)
    tot  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur  = tot / fps if fps > 0 else 0
    cap.release()

    imgs_est = int(tot / 20)
    clase    = detectar_clase(v)
    total_dur      += dur
    total_imgs_est += imgs_est

    if '❓' in clase:
        sin_clase.append(v)
        icono = "❓"
    elif 'fondo_libre' in clase:
        icono = "⬜"
    elif 'riesgo' in clase:
        icono = "🔴"
    else:
        icono = "🟢"

    print(f"  {icono} {v:<56} {dur:>5.1f}s  ~{imgs_est:>4}   {clase}")

print(f"  {'─'*110}")
print(f"  {'TOTAL':<58} {total_dur:>5.0f}s  ~{total_imgs_est}")
print(f"\n  Duración total           : {total_dur/60:.1f} minutos")
print(f"  Frames a generar (N=20)  : ~{total_imgs_est}")
print(f"  Tras selección manual    : ~{len(videos)*45} imágenes")

# Alertas
if doble_ext:
    print(f"\n  ⚠️  DOBLE EXTENSIÓN — renombra antes de continuar:")
    for f in doble_ext:
        print(f"     → {f}")

if sin_clase:
    print(f"\n  ❓ Sin clase detectada — revisa el nombre:")
    for f in sin_clase:
        print(f"     → {f}")

if not doble_ext and not sin_clase:
    print("\n  ✅ Todos los videos están listos para extracción")

# ══════════════════════════════════════════════════════════════════
# CELDA 5 — Función de extracción
# ══════════════════════════════════════════════════════════════════

def extraer_frames(video_path, output_dir, cada_n=20):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return 0, 0

    fps_real     = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duracion     = total_frames / fps_real if fps_real > 0 else 0

    frame_idx = 0
    guardados = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % cada_n == 0:
            ruta_out = os.path.join(output_dir, f"frame_{frame_idx:06d}.jpg")
            cv2.imwrite(ruta_out, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            guardados += 1
        frame_idx += 1

    cap.release()
    return guardados, duracion

print("✅ Función lista")

# ══════════════════════════════════════════════════════════════════
# CELDA 6 — Extraer todos los frames
# ══════════════════════════════════════════════════════════════════

CADA_N = 20

print(f"Extrayendo 1 frame cada {CADA_N} fotogramas...\n")
print(f"  {'Video':<58} {'Dur':>6}  {'Imgs':>5}  Clase")
print(f"  {'─'*100}")

resumen   = []
total_img = 0
errores   = []

for video in videos:
    ruta_video = f'{VIDEOS_DIR}/{video}'

    # Limpiar el nombre de carpeta eliminando extensiones intermedias
    nombre_base = video
    for ext in ['.MP4', '.mp4', '.MOV', '.mov']:
        nombre_base = nombre_base.replace(ext, '')
    nombre_base = nombre_base.strip('._- ')

    carpeta_out = f'{FRAMES_DIR}/{nombre_base}'
    clase       = detectar_clase(video)

    n, dur = extraer_frames(ruta_video, carpeta_out, CADA_N)

    if n == 0:
        errores.append(video)
        print(f"  ❌ {video:<56}  ERROR")
        continue

    total_img += n
    icono = "✅" if n >= 40 else "⚠️ "
    print(f"  {icono} {video:<56} {dur:>5.1f}s  {n:>5}   {clase}")

    resumen.append({
        'video':   video,
        'frames':  n,
        'clase':   clase,
        'carpeta': carpeta_out
    })

print(f"  {'─'*100}")
print(f"\n📊 RESULTADO")
print(f"  Videos OK   : {len(resumen)}")
print(f"  Errores     : {len(errores)}")
print(f"  Frames total: {total_img}")
print(f"  Promedio    : {total_img // max(len(resumen),1)} imgs/video")

if errores:
    print(f"\n  ❌ Con error (posible doble extensión):")
    for e in errores:
        print(f"     → {e}")


# ══════════════════════════════════════════════════════════════════
# CELDA 7 — Balance de clases para Roboflow
# ══════════════════════════════════════════════════════════════════

from collections import defaultdict

# Desagrega los combos en clases individuales
def desagregar_clases(clase_str):
    return [c.strip() for c in clase_str.split('+')]

conteo = defaultdict(int)
for item in resumen:
    for clase in desagregar_clases(item['clase']):
        conteo[clase] += item['frames']

print("Frames por clase (incluyendo combos desagregados):\n")
print(f"  {'Clase':<35} {'Frames':>7}  {'%':>6}  Balance")
print(f"  {'─'*75}")

total_etiquetable = sum(
    v for k, v in conteo.items() if 'fondo' not in k
)

for clase, n in sorted(conteo.items(), key=lambda x: -x[1]):
    if 'fondo' in clase:
        pct   = n / total_img * 100
        barra = '░' * int(pct / 2)
        print(f"  {clase:<35} {n:>6}   {pct:>5.1f}%  {barra}  (sin etiquetar)")
    else:
        pct   = n / total_etiquetable * 100
        barra = '█' * int(pct / 3)
        alerta = "  ⚠️ POCAS" if n < 80 else ""
        print(f"  {clase:<35} {n:>6}   {pct:>5.1f}%  {barra}{alerta}")

print(f"\n  Frames etiquetables totales : {total_etiquetable}")
print(f"""
──────────────────────────────────────────────────
GUÍA DE ETIQUETADO EN ROBOFLOW

Al subir las imágenes, etiqueta TODOS los objetos
visibles en cada frame según su clase:

  🔴 mochila_riesgo → bounding box sobre la mochila mal puesta
  🟢 mochila_ok     → bounding box sobre mochila bien puesta
  🔴 silla_riesgo   → bounding box sobre la silla obstruyendo
  🔴 mesa_riesgo    → bounding box sobre la mesa obstruyendo
  🟢 cables_ok      → bounding box sobre el cable ordenado
  🟢 caja_ok        → bounding box sobre la caja bien puesta
  🟢 bolsa_ok       → bounding box sobre la bolsa bien puesta

  ⬜ fondo_libre    → sube las imágenes SIN etiquetar nada

En videos con múltiples objetos (VID25-VID36),
dibuja un bounding box SEPARADO por cada objeto visible.
──────────────────────────────────────────────────
""")

# ══════════════════════════════════════════════════════════════════
# CELDA 8 — Vista previa (cambia IDX para ver otro video)
# ══════════════════════════════════════════════════════════════════

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

IDX = 0   # 0=primer video, 1=segundo, etc.

item        = resumen[IDX]
carpeta_ver = item['carpeta']
frames_disp = sorted([f for f in os.listdir(carpeta_ver) if f.endswith('.jpg')])
n_mostrar   = min(12, len(frames_disp))
cols, rows  = 4, (n_mostrar + 3) // 4

fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 3.2))
axes = axes.flatten()

for i in range(n_mostrar):
    img = mpimg.imread(f'{carpeta_ver}/{frames_disp[i]}')
    axes[i].imshow(img)
    axes[i].set_title(frames_disp[i], fontsize=7)
    axes[i].axis('off')

for j in range(n_mostrar, len(axes)):
    axes[j].axis('off')

plt.suptitle(
    f"{item['video']}  |  {item['clase']}  |  {len(frames_disp)} frames",
    fontsize=10, y=1.01
)
plt.tight_layout()
plt.show()
print(f"Quédate con ~40-50 de estos {len(frames_disp)} frames para Roboflow.")

# ══════════════════════════════════════════════════════════════════
# CELDA 0 — Reinstalar dependencias y montar Drive
# ══════════════════════════════════════════════════════════════════

!pip install ultralytics -q

from google.colab import drive
drive.mount('/content/drive')

from ultralytics import YOLO
import torch

print("✅ Ultralytics instalado")
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "❌ No GPU")

import os, zipfile

# Primero verifica el nombre exacto del ZIP
dataset_dir = '/content/drive/MyDrive/mechdog_proyecto/dataset'
print("Archivos en dataset/:")
for f in os.listdir(dataset_dir):
    tamanio = os.path.getsize(f'{dataset_dir}/{f}') / (1024*1024)
    print(f"  {f}  ({tamanio:.1f} MB)")


# Cambia este nombre por el que apareció arriba
ZIP_NAME = 'mechdog-detector.v1i.yolov8.zip'   # ← ajusta si es diferente
ZIP_PATH = f'/content/drive/MyDrive/mechdog_proyecto/dataset/{ZIP_NAME}'

# Limpiar y descomprimir de nuevo
import shutil
if os.path.exists('/content/dataset'):
    shutil.rmtree('/content/dataset')
os.makedirs('/content/dataset', exist_ok=True)

print(f"Descomprimiendo {ZIP_NAME}...")
with zipfile.ZipFile(ZIP_PATH, 'r') as z:
    # Ver primeros archivos dentro del ZIP
    nombres = z.namelist()
    print(f"Archivos en el ZIP: {len(nombres)}")
    print("Primeros 10:")
    for n in nombres[:10]:
        print(f"  {n}")

    # Descomprimir
    z.extractall('/content/dataset')

print("✅ Descomprimido")

# ══════════════════════════════════════════════════════════════════
# CELDA 0B — Restaurar variables de sesión
# ══════════════════════════════════════════════════════════════════

import os, zipfile, glob

EXTRACT_PATH = '/content/dataset'

# Descomprimir el dataset de nuevo si no existe
if not os.path.exists(EXTRACT_PATH):
    ZIP_PATH = '/content/drive/MyDrive/mechdog_proyecto/dataset/mechdog-detector.v1i.yolov8.zip'
    print("Descomprimiendo dataset...")
    os.makedirs(EXTRACT_PATH, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        z.extractall(EXTRACT_PATH)
    print("✅ Dataset listo")

# Localizar data.yaml
yaml_files = glob.glob(f'{EXTRACT_PATH}/**/*.yaml', recursive=True)
YAML_PATH  = yaml_files[0]

print(f"YAML_PATH = {YAML_PATH}")

# ══════════════════════════════════════════════════════════════════
# CELDA — Verificar qué hay en el dataset
# ══════════════════════════════════════════════════════════════════

import os

for root, dirs, files in os.walk('/content/dataset'):
    nivel = root.replace('/content/dataset', '').count(os.sep)
    if nivel <= 2:
        indent = '  ' * nivel
        n_imgs = len([f for f in files if f.endswith(('.jpg','.png'))])
        print(f"{indent}{os.path.basename(root)}/  ({n_imgs} imgs)")


# ══════════════════════════════════════════════════════════════════
# CELDA — Recrear splits valid y test desde train
# ══════════════════════════════════════════════════════════════════

import os, shutil, random

random.seed(42)

TRAIN_IMG = '/content/dataset/train/images'
TRAIN_LBL = '/content/dataset/train/labels'
VALID_IMG = '/content/dataset/valid/images'
VALID_LBL = '/content/dataset/valid/labels'
TEST_IMG  = '/content/dataset/test/images'
TEST_LBL  = '/content/dataset/test/labels'

for p in [VALID_IMG, VALID_LBL, TEST_IMG, TEST_LBL]:
    os.makedirs(p, exist_ok=True)

imagenes = [f for f in os.listdir(TRAIN_IMG) if f.endswith(('.jpg','.png'))]
random.shuffle(imagenes)

n_valid = int(len(imagenes) * 0.15)
n_test  = int(len(imagenes) * 0.15)

valid_imgs = imagenes[:n_valid]
test_imgs  = imagenes[n_valid:n_valid + n_test]

def mover(lista, src_img, src_lbl, dst_img, dst_lbl):
    for img_file in lista:
        shutil.move(os.path.join(src_img, img_file),
                    os.path.join(dst_img, img_file))
        lbl = os.path.splitext(img_file)[0] + '.txt'
        lbl_src = os.path.join(src_lbl, lbl)
        if os.path.exists(lbl_src):
            shutil.move(lbl_src, os.path.join(dst_lbl, lbl))

mover(valid_imgs, TRAIN_IMG, TRAIN_LBL, VALID_IMG, VALID_LBL)
mover(test_imgs,  TRAIN_IMG, TRAIN_LBL, TEST_IMG,  TEST_LBL)

print("✅ Splits recreados:")
for split, ruta in [('train', TRAIN_IMG), ('valid', VALID_IMG), ('test', TEST_IMG)]:
    n = len([f for f in os.listdir(ruta) if f.endswith(('.jpg','.png'))])
    print(f"  {split:<8}: {n} imágenes")

# ══════════════════════════════════════════════════════════════════
# CELDA — Corregir rutas del data.yaml
# ══════════════════════════════════════════════════════════════════

import yaml

with open(YAML_PATH, 'r') as f:
    config = yaml.safe_load(f)

config['path']  = '/content/dataset'
config['train'] = 'train/images'
config['val']   = 'valid/images'
config['test']  = 'test/images'

with open(YAML_PATH, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print("✅ data.yaml corregido")
print(f"  train → {config['train']}")
print(f"  val   → {config['val']}")
print(f"  test  → {config['test']}")


# ══════════════════════════════════════════════════════════════════
# CELDA 9 — Generar matriz de confusión estilo Edge Impulse
# ══════════════════════════════════════════════════════════════════

from ultralytics import YOLO
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

# Carga tu modelo entrenado
model = YOLO('/content/drive/MyDrive/mechdog_proyecto/modelos/v1_entrenamiento/weights/best.pt')

# Corre validación sobre el conjunto de test
metrics = model.val(
    data   = YAML_PATH,
    split  = 'test',
    conf   = 0.5,
    iou    = 0.5,
)

# Nombres de clases
nombres = list(metrics.names.values())
print("Clases:", nombres)


# ══════════════════════════════════════════════════════════════════
# CELDA 10 — Extraer matriz de confusión y mostrar como tabla
# ══════════════════════════════════════════════════════════════════

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# Obtener la matriz de confusión del objeto metrics
# Ultralytics la guarda en metrics.confusion_matrix.matrix
cm_raw = metrics.confusion_matrix.matrix  # shape: (n_clases+1, n_clases+1)

# Incluir "background" como última fila/columna (como Edge Impulse)
etiquetas = nombres + ['background']
n = len(etiquetas)

# Normalizar por fila (igual que Edge Impulse — % de cada clase real)
cm_norm = np.zeros_like(cm_raw, dtype=float)
for i in range(n):
    total = cm_raw[i].sum()
    if total > 0:
        cm_norm[i] = cm_raw[i] / total * 100

# ── Crear DataFrame para visualización ───────────────────────────
df = pd.DataFrame(
    cm_norm,
    index   = etiquetas,
    columns = etiquetas
)

print("Matriz de confusión normalizada (%):\n")
print(df.round(1).to_string())

# ══════════════════════════════════════════════════════════════════
# CELDA 3 — Visualización gráfica estilo Edge Impulse
# ══════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(12, 8))

# Colormap: verde para valores altos (correctos), rojo para bajos
cmap = mcolors.LinearSegmentedColormap.from_list(
    'ei_style',
    ['#FFEBEE', '#FFFFFF', '#E8F5E9', '#2E7D32'],
    N=256
)

im = ax.imshow(cm_norm, cmap=cmap, vmin=0, vmax=100, aspect='auto')

# Etiquetas ejes
ax.set_xticks(range(n))
ax.set_yticks(range(n))
ax.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=9)
ax.set_yticklabels(etiquetas, fontsize=9)
ax.set_xlabel('Predicho', fontsize=11, labelpad=10)
ax.set_ylabel('Real', fontsize=11, labelpad=10)
ax.set_title('Confusion Matrix — YOLOv8n (test set)', fontsize=13, pad=15)

# Valores dentro de cada celda
for i in range(n):
    for j in range(n):
        val = cm_norm[i, j]
        if val == 0:
            texto = '0%'
            color = '#CCCCCC'
        else:
            texto = f'{val:.1f}%'
            color = 'white' if val > 60 else 'black'
        ax.text(j, i, texto, ha='center', va='center',
                fontsize=8, color=color, fontweight='bold' if i==j else 'normal')

plt.colorbar(im, ax=ax, label='%', shrink=0.8)
plt.tight_layout()

# Guardar en Drive
ruta_fig = '/content/drive/MyDrive/mechdog_proyecto/resultados/confusion_matrix_yolov8.png'
plt.savefig(ruta_fig, dpi=150, bbox_inches='tight')
plt.show()
print(f"✅ Guardada en: {ruta_fig}")

# ══════════════════════════════════════════════════════════════════
# CELDA 4 — Tabla comparativa YOLOv8 vs FOMO (para el artículo)
# ══════════════════════════════════════════════════════════════════

# Resultados FOMO de Edge Impulse (los que te dio)
fomo_f1 = {
    'bolsa_ok':        0.81,
    'cables_ok':       0.83,
    'caja_ok':         0.85,
    'mesa_riesgo':     0.57,
    'mochila_ok':      0.87,
    'mochila_riesgo':  0.85,
    'silla_riesgo':    0.62,
}

# Resultados YOLOv8 (de tu entrenamiento)
yolo_ap50 = {}
for i, nombre in enumerate(metrics.names.values()):
    yolo_ap50[nombre] = float(metrics.box.ap50[i])

yolo_p    = {nombre: float(metrics.box.p[i])
             for i, nombre in enumerate(metrics.names.values())}
yolo_r    = {nombre: float(metrics.box.r[i])
             for i, nombre in enumerate(metrics.names.values())}

# Construir tabla
print("\n" + "="*72)
print(f"{'COMPARACIÓN POR CLASE — YOLOv8n vs FOMO MobileNetV2 0.35':^72}")
print("="*72)
print(f"{'Clase':<22} {'YOLOv8 P':>9} {'YOLOv8 R':>9} "
      f"{'YOLOv8 AP50':>12} {'FOMO F1':>9}")
print("─"*72)

for clase in sorted(fomo_f1.keys()):
    p    = yolo_p.get(clase, 0)
    r    = yolo_r.get(clase, 0)
    ap   = yolo_ap50.get(clase, 0)
    f1   = fomo_f1[clase]
    diff = ap - f1

    simbolo = "✅" if diff >= 0 else "⚠️"
    print(f"  {clase:<20} {p:>9.3f} {r:>9.3f} "
          f"{ap:>12.3f} {f1:>9.3f}  {simbolo}")

print("─"*72)

# Promedios
avg_ap   = np.mean(list(yolo_ap50.values()))
avg_fomo = np.mean(list(fomo_f1.values()))

print(f"  {'PROMEDIO':<20} {'':>9} {'':>9} "
      f"{avg_ap:>12.3f} {avg_fomo:>9.3f}")
print("="*72)

print(f"""
Notas:
  YOLOv8n  → evaluado con mAP@0.5 | hardware: laptop/GPU
  FOMO     → evaluado con F1 score | hardware: ESP32-CAM ($8 USD)

  Diferencia global de precisión : {(avg_ap - avg_fomo)*100:.1f} puntos porcentuales
  Reducción de costo hardware     : ~98% (de $600+ a $8 USD)
""")

# ══════════════════════════════════════════════════════════════════
# CELDA 4 — Tabla comparativa YOLOv8 vs FOMO actualizada 
# ══════════════════════════════════════════════════════════════════
print("\n" + "="*55)
print(f"{'Clase':<22} {'YOLOv8 AP50':>12} {'FOMO F1':>9}")
print("─"*55)

for clase in sorted(fomo_f1.keys()):
    ap = yolo_ap50.get(clase, 0)
    f1 = fomo_f1[clase]
    print(f"  {clase:<20} {ap:>12.3f} {f1:>9.3f}")

print("─"*55)
print(f"  {'PROMEDIO':<20} {avg_ap:>12.3f} {avg_fomo:>9.3f}")
print("="*55)
print(f"\n  Hardware YOLOv8 : Laptop RTX 4050")
print(f"  Hardware FOMO   : ESP32-CAM (~$8 USD)")
print(f"  Diferencia      : {(avg_ap - avg_fomo)*100:.1f} puntos porcentuales")

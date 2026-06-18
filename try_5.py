import cv2
import numpy as np
import requests
from flask import Flask, render_template_string, jsonify
import os
from datetime import datetime
from paddleocr import PaddleOCR
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')

ESP32_URL = "http://192.168.4.1/capture"

# Отключаем проверку интернета и инициализируем OCR
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
ocr = PaddleOCR(lang='en', use_angle_cls=True)  # добавлен параметр для определения ориентации

# Хранилище снимков
photos = []

# Порог резкости, при котором считаем фокус найденным
SHARPNESS_THRESHOLD = 60

def capture_from_esp():
    try:
        resp = requests.get(ESP32_URL, timeout=10)
        if resp.status_code == 200:
            return resp.content
        else:
            print(f"ESP32 error: {resp.status_code}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def compute_sharpness(jpeg_bytes):
    """Вычисляет резкость (дисперсию лапласиана) по градациям серого."""
    arr = np.frombuffer(jpeg_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    lap = cv2.Laplacian(img, cv2.CV_64F)
    return float(lap.var())

def recognize_text(jpeg_bytes):
    """
    Распознаёт текст на изображении.
    Возвращает (средняя_уверенность, распознанный_текст).
    """
    try:
        arr = np.frombuffer(jpeg_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return 0, "(ошибка декодирования)"

        # Выполняем OCR без дополнительной предобработки
        result = ocr.ocr(img, cls=True)
        if not result or not result[0]:
            return 0, "(текст не распознан)"

        # result[0] — список строк, каждая строка: [bbox, (text, confidence)]
        all_texts = []
        total_conf = 0.0
        for line in result[0]:
            if len(line) == 2:
                bbox, (text, conf) = line
                all_texts.append(text)
                total_conf += conf
            else:
                # fallback на случай нестандартного формата
                all_texts.append(str(line))
                total_conf += 0.5

        if all_texts:
            avg_conf = total_conf / len(all_texts)
            full_text = ' '.join(all_texts)
            return avg_conf, full_text
        else:
            return 0, "(текст не распознан)"
    except Exception as e:
        print(f"OCR error: {e}")
        import traceback
        traceback.print_exc()
        return 0, f"(ошибка OCR: {e})"

def save_jpeg(jpeg_bytes):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"photo_{timestamp}.jpg"
    filepath = os.path.join(STATIC_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(jpeg_bytes)
    print(f"Saved: {filepath}")
    return f"/static/{filename}"

# HTML-шаблон (без изменений, тот же, что в try_5.py)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>ESP32-CAM Автофокус + OCR</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 20px; padding: 20px; }
        h1 { text-align: center; color: #333; }
        .toolbar { text-align: center; margin: 20px 0; }
        .toolbar button { background-color: #007bff; color: white; border: none; padding: 12px 30px; border-radius: 30px; cursor: pointer; font-size: 18px; margin: 0 10px; }
        .toolbar button:disabled { background-color: #6c757d; cursor: not-allowed; }
        .toolbar .clear-btn { background-color: #dc3545; }
        .status-bar { background: #e9ecef; border-radius: 16px; padding: 15px; margin: 20px 0; text-align: center; font-size: 1.5rem; }
        .status-bar .up { color: #28a745; }
        .status-bar .down { color: #dc3545; }
        .status-bar .stop { color: #ffc107; font-weight: bold; }
        .gallery { display: flex; flex-wrap: wrap; gap: 25px; justify-content: center; }
        .card { flex: 0 1 320px; background: #fafafa; border-radius: 16px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card .photo { background: #e9ecef; border-radius: 12px; min-height: 200px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        .card .photo img { max-width: 100%; max-height: 300px; border-radius: 8px; }
        .card .info { margin-top: 12px; }
        .card .sharpness { font-weight: bold; margin: 5px 0; }
        .card .delta { font-weight: bold; margin: 5px 0; }
        .card .delta.up { color: #28a745; }
        .card .delta.down { color: #dc3545; }
        .card .delta.stop { color: #ffc107; }
        .card .ocr-text { background: #eef; padding: 8px; border-radius: 8px; font-family: monospace; font-size: 0.9rem; word-break: break-word; margin-top: 8px; }
        .card .timestamp { color: #666; font-size: 0.8rem; margin-top: 5px; }
        .loading { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; font-size: 24px; color: white; }
    </style>
</head>
<body>
<div class="container">
    <h1>📷 Автофокус ESP32-CAM + OCR</h1>
    <div class="toolbar">
        <button id="captureBtn">📸 Сделать снимок</button>
        <button id="clearBtn" class="clear-btn">🗑 Очистить все</button>
    </div>
    <div class="status-bar" id="statusBar">
        {% if photos %}
            {% set last = photos[0] %}
            {% if last.delta is not none %}
                {% if last.delta > 0 %}
                    <span class="up">▲ Резкость выросла на {{ last.delta|round(2) }}</span>
                {% elif last.delta < 0 %}
                    <span class="down">▼ Резкость упала на {{ (-last.delta)|round(2) }}</span>
                {% else %}
                    <span class="stop">⏹ Резкость не изменилась</span>
                {% endif %}
                {% if last.sharpness > 60 %}
                    <span class="stop"> | 🎯 Фокус найден (резкость > 60)</span>
                {% endif %}
            {% else %}
                <span>Сделайте первый снимок</span>
            {% endif %}
        {% else %}
            <span>Сделайте первый снимок</span>
        {% endif %}
    </div>
    <div class="gallery" id="gallery">
        {% for photo in photos %}
        <div class="card" data-id="{{ loop.index0 }}">
            <div class="photo">
                <img src="{{ photo.path }}?t={{ range(1000000) | random }}" alt="Снимок">
            </div>
            <div class="info">
                <div class="sharpness">🔍 Резкость: {{ photo.sharpness|round(2) }}</div>
                {% if photo.delta is not none %}
                    <div class="delta {% if photo.delta > 0 %}up{% elif photo.delta < 0 %}down{% else %}stop{% endif %}">
                        {% if photo.delta > 0 %}▲ +{{ photo.delta|round(2) }}{% elif photo.delta < 0 %}▼ {{ photo.delta|round(2) }}{% else %}⏹ 0.00{% endif %}
                    </div>
                {% endif %}
                <div class="ocr-text">📖 Распознано: {{ photo.text }}<br>Длина: {{ photo.text_len }} симв.</div>
                <div class="timestamp">🕒 {{ photo.timestamp }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
<div id="loading" class="loading">⏳ Загрузка...</div>

<script>
    function showLoading() { document.getElementById('loading').style.display = 'flex'; }
    function hideLoading() { document.getElementById('loading').style.display = 'none'; }

    async function capturePhoto() {
        showLoading();
        try {
            const resp = await fetch('/capture', { method: 'POST' });
            const data = await resp.json();
            if (data.success) {
                // Обновляем статус-бар
                const statusBar = document.getElementById('statusBar');
                if (data.delta !== undefined && data.delta !== null) {
                    let html = '';
                    if (data.delta > 0) {
                        html = `<span class="up">▲ Резкость выросла на ${data.delta.toFixed(2)}</span>`;
                    } else if (data.delta < 0) {
                        html = `<span class="down">▼ Резкость упала на ${(-data.delta).toFixed(2)}</span>`;
                    } else {
                        html = `<span class="stop">⏹ Резкость не изменилась</span>`;
                    }
                    if (data.sharpness > 60) {
                        html += ` <span class="stop">| 🎯 Фокус найден (резкость > 60)</span>`;
                    }
                    statusBar.innerHTML = html;
                } else {
                    statusBar.innerHTML = '<span>Сделайте первый снимок</span>';
                }

                // Добавляем новую карточку в галерею
                const gallery = document.getElementById('gallery');
                const card = document.createElement('div');
                card.className = 'card';
                card.dataset.id = data.index;
                let deltaHtml = '';
                if (data.delta !== undefined && data.delta !== null) {
                    let cls = data.delta > 0 ? 'up' : (data.delta < 0 ? 'down' : 'stop');
                    let sign = data.delta > 0 ? '▲ +' : (data.delta < 0 ? '▼ ' : '⏹ ');
                    deltaHtml = `<div class="delta ${cls}">${sign}${Math.abs(data.delta).toFixed(2)}</div>`;
                }
                card.innerHTML = `
                    <div class="photo"><img src="${data.path}?t=${Date.now()}" alt="Снимок"></div>
                    <div class="info">
                        <div class="sharpness">🔍 Резкость: ${data.sharpness.toFixed(2)}</div>
                        ${deltaHtml}
                        <div class="ocr-text">📖 Распознано: ${data.ocr_text}<br>Длина: ${data.text_length} симв.</div>
                        <div class="timestamp">🕒 ${data.timestamp}</div>
                    </div>
                `;
                gallery.prepend(card);
            } else {
                alert('Ошибка: ' + data.message);
            }
        } catch(e) { alert('Ошибка: ' + e); }
        finally { hideLoading(); }
    }

    async function clearAll() {
        if (!confirm('Удалить все снимки?')) return;
        showLoading();
        await fetch('/clear', { method: 'POST' });
        document.getElementById('gallery').innerHTML = '';
        document.getElementById('statusBar').innerHTML = '<span>Сделайте первый снимок</span>';
        hideLoading();
    }

    document.getElementById('captureBtn').onclick = capturePhoto;
    document.getElementById('clearBtn').onclick = clearAll;
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, photos=photos)

@app.route('/capture', methods=['POST'])
def capture():
    jpeg = capture_from_esp()
    if jpeg is None:
        return jsonify({"success": False, "message": "Не удалось получить фото с ESP32"})

    sharp = compute_sharpness(jpeg)
    confidence, ocr_text = recognize_text(jpeg)
    text_len = len(ocr_text) if "ошибка" not in ocr_text else 0
    path = save_jpeg(jpeg)
    timestamp = datetime.now().strftime("%H:%M:%S %d.%m.%Y")

    # Вычисляем изменение резкости относительно предыдущего снимка
    delta = None
    if photos:
        prev_sharp = photos[0]["sharpness"]
        delta = sharp - prev_sharp

    photo_data = {
        "path": path,
        "sharpness": sharp,
        "text": ocr_text,
        "text_len": text_len,
        "confidence": confidence,
        "timestamp": timestamp,
        "delta": delta
    }
    photos.insert(0, photo_data)

    return jsonify({
        "success": True,
        "path": path,
        "sharpness": sharp,
        "ocr_text": ocr_text,
        "text_length": text_len,
        "timestamp": timestamp,
        "delta": delta,
        "index": 0
    })

@app.route('/clear', methods=['POST'])
def clear():
    global photos
    photos = []
    for f in os.listdir(STATIC_DIR):
        if f.startswith("photo_"):
            os.remove(os.path.join(STATIC_DIR, f))
    return jsonify({"success": True})

if __name__ == '__main__':
    print(f"Сервер запущен: http://127.0.0.1:5000")
    print(f"Статика сохраняется в: {STATIC_DIR}")
    print("Подключитесь к Wi-Fi ESP32_CAM и нажмите кнопку на сайте")
    app.run(host='0.0.0.0', port=5000, debug=True)
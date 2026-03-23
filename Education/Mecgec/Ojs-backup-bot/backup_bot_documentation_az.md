# OJS Backup Bot — Tam Sənədləşmə

---

## Bot nədir, nə edir?

Bu bot OJS serverinin avtomatik ehtiyat nüsxəsini (backup) alır və Telegram kanalına göndərir. Saatda bir işə düşür, verilənlər bazasını və fayl sistemini sıxışdırır, Telegram-ın fayl limitini aşarsa parçalara bölür, kanalda yayınlayır.

Manual olaraq da işlədilə bilər — bot komutları vasitəsilə.

---

## Qurulum

```bash
pip install "python-telegram-bot[job-queue]"
python backup_bot.py
```

`[job-queue]` əlavəsi vacibdir. Bu olmadan `app.job_queue` işləmir — bot zamanlı tapşırıqları icra edə bilməz.

---

## Blok 1 — İmportlar

```python
import asyncio
import datetime
import functools
import glob
import logging
import os
import subprocess
import zoneinfo
from typing import Optional
```

| Modul | Nə üçün |
|-------|---------|
| `asyncio` | Asinxron proqramlaşdırma. Bot bütün işləri `async/await` ilə edir — eyni zamanda həm gözləyir, həm icra edir. |
| `datetime` | Tarix/saat hesablamaları — backup vaxtı, növbəti backup vaxtı, qalan vaxt. |
| `functools` | `@functools.wraps` — decorator yazdıqda funksiya adını, docstring-ini itirməmək üçün. |
| `glob` | Fayl axtarışı — wildcard pattern ilə. (`*.xz`, `*.part*` kimi). |
| `logging` | Konsola log yazmaq — `[INFO]`, `[WARNING]`, `[ERROR]`. |
| `os` | Fayl/qovluq əməliyyatları — yaratmaq, silmək, ölçü almaq, yol birləşdirmək. |
| `subprocess` | Sistem komutlarını Python içindən çalışdırmaq — `mysqldump`, `tar`, `xz`. |
| `zoneinfo` | Saat qurşağı idarəsi — `Asia/Baku` üçün. Python 3.9+ ilə standartdır. |
| `Optional` | Type hint — `Optional[str]` = ya `str`, ya `None`. |

---

```python
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest
```

| Import | Nə edir |
|--------|---------|
| `InlineKeyboardButton` | Mesajın altında görünən tıklanabilir düymə — mətn + `callback_data` daşıyır |
| `InlineKeyboardMarkup` | Düymə sıralarını bir layout-a birləşdirir, mesaja əlavə edilir |
| `Update` | Telegram-dan gələn hadisə obyekti — mesaj, düymə, komut... |
| `Application` | Botun özü — token, handler-lar, job queue hamısı burada toplanır |
| `CallbackQueryHandler` | Inline düymə basıldıqda hansı funksiyanın çağırılacağını qeyd edir |
| `CommandHandler` | `/start`, `/backup` kimi komutlara handler bağlamaq üçün |
| `ContextTypes` | Handler funksiyasının ikinci parametrinin tipi — bot, job_queue buradan gəlir |
| `HTTPXRequest` | Telegram-la HTTP bağlantısını idarə edir — timeout-lar burada ayarlanır |

---

## Blok 2 — CONFIG

```python
CONFIG = {
    "BOT_TOKEN":             "8605313454:AAFgz2d_...",
    "CHANNEL_ID":            -1003319837567,
    "BACKUP_DIR":            "/root/backups",
    "BACKUP_INTERVAL_HOURS": 1,
    "ADMIN_IDS":             [8246268807, 5187014948],
    "UPLOAD_DIR":            "/home/ojs_backup_bot/upload_from_bot",
}
```

Bu lüğət bütün dəyişdirilə bilən ayarları bir yerdə tutur. Kodu oxuyan kəs bu bir bloka baxıb hər şeyi anlayır.

---

### `BOT_TOKEN`

BotFather-dən alınan token. Botun kimliyi. Telegram bu tokena görə sorğunun hansı bota aid olduğunu bilir.

**Dəyişdirmə:** Başqa bot üçün işlədəcəksənsə, BotFather-dan yeni bot yarat, tokenini bura yaz.

```python
"BOT_TOKEN": "SENIN_BOT_TOKENIN"
```

**Diqqət:** Bu tokeni heç vaxt git-ə yükləmə. `.env` faylında saxlamaq daha doğrudur:
```python
import os
"BOT_TOKEN": os.environ["BOT_TOKEN"]
```

---

### `CHANNEL_ID`

Backup fayllarının göndəriləcəyi Telegram kanalının ID-si. Mənfi rəqəm — bu xüsusiyyət Telegram-ın supergroup/channel ID formatıdır.

Kanal ID-sini öyrənmək üçün: `@userinfobot`-a kanaldan bir mesaj forward et, o sənə ID-ni yazır.

**Dəyişdirmə:** Başqa kanal və ya qrupa göndərmək istəyirsənsə:
```python
"CHANNEL_ID": -1009876543210   # yeni kanal ID-si
```

Bot həmin kanalın **admin**i olmalıdır, əks halda fayl göndərə bilmir.

---

### `BACKUP_DIR`

Backup fayllarının müvəqqəti saxlandığı yerli qovluq. Bot backup yaradır, bura yazır, Telegram-a göndərir, **sonra silir**. Daimi saxlama yeri deyil.

**Dəyişdirmə:** Root qovluğu istifadə etmək istəmirsənsə:
```python
"BACKUP_DIR": "/home/ojs_backup_bot/backups"
```

Qovluq yoxdursa bot özü yaradır (`os.makedirs(..., exist_ok=True)`).

---

### `BACKUP_INTERVAL_HOURS`

Avtomatik backupun neçə saatda bir işləyəcəyi. `1` = saatda bir.

**Dəyişdirmə:**
```python
"BACKUP_INTERVAL_HOURS": 6     # 6 saatda bir
"BACKUP_INTERVAL_HOURS": 24    # gündə bir
"BACKUP_INTERVAL_HOURS": 0.5   # yarım saatda bir
```

Bu dəyər `main()` funksiyasında saniyəyə çevrilir:
```python
interval = CONFIG["BACKUP_INTERVAL_HOURS"] * 3600
```

---

### `ADMIN_IDS`

Botdan istifadə edə biləcək istifadəçilərin Telegram ID-lərinin siyahısı. Siyahıda olmayan biri `/backup` yazdıqda "Access denied" cavabını alır.

Telegram ID-ni öyrənmək: `@userinfobot`-a `/start` yaz, o sənin ID-ni yazır.

**Dəyişdirmə:** Yeni admin əlavə et:
```python
"ADMIN_IDS": [8246268807, 5187014948, 1122334455]
```

**Niyə siyahıdır?** Birdən çox şəxs botu idarə edə bilsin deyə. Məsələn sysadmin + müdir.

---

### `UPLOAD_DIR`

`/upload` komutundan backup Telegram kanalından servera yüklənəndə faylın harada saxlanacağı. İki alt qovluq yaradılır: `db/` və `files/`.

**Dəyişdirmə:**
```python
"UPLOAD_DIR": "/opt/ojs_downloads"
```

---

## Blok 3 — Sabit dəyərlər

```python
TZ           = zoneinfo.ZoneInfo("Asia/Baku")
TG_MAX_BYTES = 45 * 1024 * 1024   # 45 MB safe margin
```

### `TZ`

Bütün tarix/vaxt göstərmələri bu zonada hesablanır. Serverin sistem saat zonasından müstəqildir — server UTC-də işləsə belə, loglar AZT-də görünür.

**Dəyişdirmə:** Başqa ölkə üçün:
```python
TZ = zoneinfo.ZoneInfo("Europe/Istanbul")
TZ = zoneinfo.ZoneInfo("Europe/London")
```

---

### `TG_MAX_BYTES`

Telegram-ın fayl limiti texniki olaraq 50 MB-dır. Amma şəbəkə overhead-i, Telegram-ın daxili protokol yükü, chunk buffer-ları nəzərə alınıb **45 MB** seçilib.

Bu limit aşıldıqda bot faylı parçalara bölür (`_split_file` funksiyası).

**Dəyişdirmə:** Telegram Bot API-nın limiti dəyişsə (həmişə rəsmi sənədə bax):
```python
TG_MAX_BYTES = 48 * 1024 * 1024
```

---

## Blok 4 — Backup hədəfləri

```python
DB_USER = "user"
DB_PASS = "pass"
DB_NAME = "db"
```

Verilənlər bazası bağlantı məlumatları. `config.inc.php`-dakı dəyərlərlə eyni olmalıdır.

**Dəyişdirmə:** Başqa bir tətbiq üçün işlədəcəksənsə:
```python
DB_USER = "wp_user"
DB_PASS = "wordpress_password"
DB_NAME = "wordpress_db"
```

---

```python
BACKUP_ITEMS = [
    "/path/ojs_files/",
    "/path/ojs/public/",
    "/path/ojs/config.inc.php",
]
```

Fayl backup-ına daxil ediləcək yollar. Bunlar `tar` komutuna arqument kimi ötürülür.

| Yol | Nə var |
|-----|--------|
| `/path/ojs_files/` | Bütün yüklənmiş fayllar — məqalə PDF-ləri, şəkillər, qərar məktubları |
| `/path/ojs/public/` | Web-accessible public fayllar — TinyMCE şəkilləri, jurnal logoları |
| `/path/ojs/config.inc.php` | Konfiqurasiya faylı — DB şifrəsi, mail ayarları, hər şey |

**Dəyişdirmə:** Başqa qovluq əlavə etmək:
```python
BACKUP_ITEMS = [
    "/path/ojs_files/",
    "/path/ojs/public/",
    "/path/ojs/config.inc.php",
    "/etc/nginx/sites-available/ojs",   # Nginx konfiqurasyonu da əlavə et
]
```

Sil:
```python
BACKUP_ITEMS = [
    "/path/ojs_files/",      # yalnız fayllar, config-i backup etmə
]
```

---

```python
TAR_EXCLUDES = [
    "--exclude=*/cache/*",
    "--exclude=*/templates_c/*",
    "--exclude=*/.cache/*",
    "--exclude=*/logs/*",
    "--exclude=*/error_log",
    "--exclude=*thumb*",
    "--exclude=*.log",
    "--exclude=*.tmp",
    "--exclude=*.bak",
]
```

`tar` komutuna əlavə edilən "bunu daxil etmə" qaydaları. Bunlar sıxışdırma ölçüsünü azaldır, bərpa zamanı lazımsız faylları geri gətirmir.

| Qayda | Nə istisna edilir |
|-------|------------------|
| `*/cache/*` | OJS cache faylları — yenidən yaranır |
| `*/templates_c/*` | Smarty kompilyasiya faylları — yenidən yaranır |
| `*/.cache/*` | Gizli cache qovluqları |
| `*/logs/*` | Log qovluqları |
| `*/error_log` | PHP error log faylları |
| `*thumb*` | Thumbnail şəkillər — mənbə şəkillərdən yaranır |
| `*.log`, `*.tmp`, `*.bak` | Log, müvəqqəti, köhnə fayllar |

**Dəyişdirmə:** `node_modules` kimi başqa şeyləri istisna etmək:
```python
TAR_EXCLUDES = [
    ...mövcud qaydalar...,
    "--exclude=*/node_modules/*",
    "--exclude=*/__pycache__/*",
    "--exclude=*/venv/*",
]
```

---

## Blok 5 — MESSAGES

```python
MESSAGES = {
    "start": "...",
    "backup_started": "⏳ Backup started...",
    "backup_success": "✅ *Backup completed!*\n🕐 {timestamp}",
    ...
}
```

Bütün bot mesajları bir lüğətdə toplanıb. Faydası: kodu dəyişdirmədən mesaj mətnlərini dəyişmək olar.

`{timestamp}`, `{error}`, `{filename}` kimi yerlər Python-un `.format()` metodu ilə doldurulur:
```python
MESSAGES["backup_success"].format(timestamp="2026-01-01 10:00:00 AZT")
# → "✅ *Backup completed!*\n🕐 2026-01-01 10:00:00 AZT"
```

`channel_caption` mesajı kanalda hər faylın altında görünür:
```python
"channel_caption": (
    "{label}\n\n"
    "📁 File name: `{filename}`\n"
    "📦 File size: {size}\n"
    "📅 Backup date: {date}\n"
    "🕐 Backup time: {time}\n"
    "🌐 Server IP: `{server_ip}`"
),
```

`{label}` — "🗄 Database Backup" və ya "📂 Files Backup" olur.

**Backtick (`) işarəsi:** Telegram Markdown-da kod formatında göstərir — mono font, kopyalanması asan.

---

## Blok 6 — Logging

```python
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
```

Konsola yazılan log formatı. Çıxış belə görünür:
```
2026-01-15 10:00:01 | INFO     | __main__ | Scheduled backup triggered.
2026-01-15 10:00:02 | INFO     | __main__ | Step 1/2 — dumping database → /root/backups/ojs_db_2026-01-15_10-00.sql.xz
2026-01-15 10:00:08 | INFO     | __main__ | Step 2/2 — creating files archive → /root/backups/ojs_files_2026-01-15_10-00.tar.xz
```

`levelname)-8s` — level adını 8 simvol genişliyinə pad edir (INFO, WARNING, ERROR hamısı düz sıralanır).

`level=logging.INFO` — INFO və daha yüksək səviyyəlilər göstərilir. DEBUG mesajları gizlənir.

---

## Blok 7 — STATE

```python
state: dict = {
    "last_backup_time":  None,
    "last_db_parts":     [],
    "last_files_parts":  [],
    "backup_history":    [],
}
```

Bot işlədiyi müddətdə yaddaşda saxlanan məlumatlar. Fayla yazılmır — bot yenidən başlayanda sıfırlanır.

| Açar | Nə saxlayır |
|------|-------------|
| `last_backup_time` | Son backupun `datetime` obyekti — `/lbdate` komutunda görünür |
| `last_db_parts` | Son backupun DB fayl adları (parçalanmışsa siyahı) |
| `last_files_parts` | Son backupun fayl arxiv adları |
| `backup_history` | Bütün göndərilmiş faylların siyahısı — `/upload` komutunda seçim üçün istifadə olunur |

`backup_history` siyahısının hər elementi belə bir lüğətdir:
```python
{
    "type":     "db",                          # "db" və ya "files"
    "filename": "ojs_db_2026-01-15_10-00.sql.xz",
    "file_id":  "BQACAgIAAxkBAAI...",          # Telegram-ın fayl ID-si
    "date":     "2026-01-15",
    "time":     "10:00:00 AZT",
    "part_no":  1,                             # neçənci parça
    "parts":    1,                             # ümumi parça sayı
}
```

`file_id` — Telegram-ın öz fayl sistemi. Fayl bir dəfə göndərildikdən sonra bu ID ilə yenidən göndərmək, yükləmək mümkündür.

---

## Blok 8 — Admin qoruması (dekorator sistemi)

### `is_admin()`

```python
def is_admin(user_id: int) -> bool:
    return user_id in CONFIG["ADMIN_IDS"]
```

Sadə yoxlama. `ADMIN_IDS` siyahısında var mı? `True`. Yoxdur? `False`.

---

### `@admin_only` dekoratoru

```python
def admin_only(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or not is_admin(user.id):
            uid = user.id if user else "unknown"
            logger.warning("Unauthorized access by user_id=%s", uid)
            if update.message:
                await update.message.reply_text(
                    MESSAGES["unauthorized"], parse_mode="Markdown"
                )
            elif update.callback_query:
                await update.callback_query.answer("Access denied.", show_alert=True)
            return
        return await func(update, context)
    return wrapper
```

**Dekorator nədir?** Bir funksiyaya əlavə davranış qoşmaq üçün istifadə olunan mexanizmdir. `@admin_only` yazıldıqda həmin funksiya çağırılmadan əvvəl admin yoxlaması keçirilir.

```python
@admin_only
async def cmd_backup(update, context):
    ...
```

Bu yazı əslində budur:
```python
async def cmd_backup(update, context):
    ...
cmd_backup = admin_only(cmd_backup)
```

Yəni `cmd_backup` artıq `wrapper` funksiyasıdır — əvvəlcə admin yoxlayır, admin isə əsl funksiyanı çağırır.

`@functools.wraps(func)` — wrapper-ın adı, docstring-i əsl funksiyanınkı kimi qalır. Olmasa debug zamanı hər funksiya `wrapper` adında görünərdi.

İki fərqli cavab yolu:
- `update.message` var → mesaj cavabı yazır
- `update.callback_query` var → popup alert göstərir

---

### `@admin_callback` dekoratoru

```python
def admin_callback(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or not is_admin(user.id):
            await update.callback_query.answer("Access denied.", show_alert=True)
            return
        return await func(update, context)
    return wrapper
```

`admin_only` ilə demək olar ki, eynidir, amma yalnız callback query üçün nəzərdə tutulub. Callback query-də `update.message` yoxdur — bu yüzündən sadələşdirilmiş versiya.

---

## Blok 9 — Köməkçi funksiyalar (Helpers)

### `_now()`

```python
def _now() -> datetime.datetime:
    return datetime.datetime.now(TZ)
```

Hazırki vaxtı AZT zonasında qaytarır. `datetime.datetime.now()` sistemin UTC-sini verir, `TZ` ilə zonalı versiya alınır.

---

### `_fmt_dt()`

```python
def _fmt_dt(dt: datetime.datetime) -> str:
    return dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S AZT")
```

`datetime` obyektini oxunaqlı string-ə çevirir: `2026-01-15 10:00:00 AZT`.

`strftime` format kodları:
- `%Y` → 4 rəqəmli il: `2026`
- `%m` → ay: `01`
- `%d` → gün: `15`
- `%H` → saat (24h): `10`
- `%M` → dəqiqə: `00`
- `%S` → saniyə: `00`

---

### `_human_size()`

```python
def _human_size(path: str) -> str:
    size = os.path.getsize(path)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
```

Fayl ölçüsünü oxunaqlı formata çevirir: `47.3 MB`, `1.2 GB`.

`os.path.getsize()` baytda qaytarır. Loop hər addımda 1024-ə bölür, uyğun ölçü tapılana qədər.

---

### `_get_server_ip()`

```python
def _get_server_ip() -> str:
    import urllib.request
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        import socket
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "unknown"
```

Serverın xarici IP ünvanını tapır. Kanalda göndərilən mesajda göstərilir.

1. Əvvəlcə `https://api.ipify.org`-a sorğu atar — bu sayt sadəcə sənin IP-ni yazır.
2. İnternet yoxdursa `socket.gethostbyname()` ilə lokal IP-ni alır.
3. Hər ikisi uğursuz olsa `"unknown"` qaytarır.

`timeout=5` — 5 saniyə cavab gəlməsə dayanır, proqramı bloklamır.

---

### `_split_file()`

```python
def _split_file(path: str, chunk_size: int = TG_MAX_BYTES) -> list:
    parts, part_num = [], 0
    with open(path, "rb") as src:
        while True:
            chunk = src.read(chunk_size)
            if not chunk:
                break
            part_num += 1
            part_path = f"{path}.part{part_num}"
            with open(part_path, "wb") as dst:
                dst.write(chunk)
            parts.append(part_path)
    os.remove(path)
    logger.info("Split %s into %d part(s)", os.path.basename(path), len(parts))
    return parts
```

45 MB-dan böyük faylları parçalara bölür.

**Necə işləyir:**
1. Mənbə faylı binary oxuma rejimində aç (`"rb"`)
2. Hər dəfə 45 MB oxu
3. Parça adını yarat: `ojs_db_2026-01-15.sql.xz.part1`, `.part2`, ...
4. Parçanı yaz
5. Mənbə faylı sil (disk yeri qazanmaq üçün)
6. Parça yollarının siyahısını qaytar

Bərpa zamanı:
```bash
cat ojs_db_2026-01-15.sql.xz.part* > ojs_db_2026-01-15.sql.xz
xz -d ojs_db_2026-01-15.sql.xz
mysql -u ojs_user -p ojs_db < ojs_db_2026-01-15.sql
```

`cat` komutları parçaları birləşdirir — `part1`, `part2`, `part3` birləşib orijinal fayl olur.

---

## Blok 10 — Backup yaratmaq

```python
def create_backup():
    backup_dir = CONFIG["BACKUP_DIR"]
    os.makedirs(backup_dir, exist_ok=True)

    ts            = _now().strftime("%Y-%m-%d_%H-%M")
    db_archive    = os.path.join(backup_dir, f"ojs_db_{ts}.sql.xz")
    files_archive = os.path.join(backup_dir, f"ojs_files_{ts}.tar.xz")
    ...
```

Fayl adları vaxt damğası ilə yaradılır: `ojs_db_2026-01-15_10-00.sql.xz`.

`os.path.join()` — platformadan asılı olmadan düzgün yol yaradır (`/root/backups/ojs_db_...`).

---

### Addım 1 — Verilənlər bazası dump

```python
dump_cmd = (
    f'mysqldump -u {DB_USER} -p"{DB_PASS}" {DB_NAME}'
    f' --single-transaction --skip-comments --compact'
    f' | xz -T0 -6 > {db_archive}'
)
result = subprocess.run(
    dump_cmd, shell=True, capture_output=True,
    text=True, executable="/bin/bash",
)
```

`mysqldump` verilənlər bazasını SQL formatında çıxarır. Birbaşa `| xz` ilə sıxışdırılır — diska yazılmadan pipe ilə keçir.

**Flag-ların mənası:**

| Flag | Nə edir |
|------|---------|
| `--single-transaction` | InnoDB cədvəllər üçün — dump zamanı cədvəlləri kilitləmir, sayt işləməyə davam edir |
| `--skip-comments` | SQL faylındakı MySQL versiyon şərhlərini atlar — fayl kiçilir |
| `--compact` | `SET` ifadələrini, boş sətirləri atlar — fayl daha da kiçilir |

**`xz -T0 -6` nədir?**

`xz` LZMA2 alqoritmli sıxışdırma alətidir. `gzip`-dən daha yüksək sıxışdırma nisbəti verir, amma daha yavaş işləyir.

| Parametr | Mənası |
|----------|--------|
| `-T0` | Bütün CPU nüvələrini işlət (0 = auto-detect) |
| `-6` | Sıxışdırma səviyyəsi (1-9, 6 = sürət/ölçü balansı) |

Daha kiçik fayl istəyirsənsə:
```bash
xz -T0 -9    # çox yavaş, maksimum sıxışdırma
```

Daha sürətli istəyirsənsə:
```bash
xz -T0 -3    # sürətli, az sıxışdırma
```

`subprocess.run(..., shell=True)` — komutun `bash` içərisindən icra olunmasını təmin edir. `|` (pipe) operatoru işləsin deyə `shell=True` şərtdir.

`capture_output=True` — stdout/stderr gizlənir, `result.stdout`, `result.stderr`-da saxlanır.

`result.returncode != 0` — uğursuzluq kodu. 0 = uğurlu, başqa = xəta.

---

### Addım 2 — Fayl arxivi

```python
tar_cmd = ["tar"] + TAR_EXCLUDES + ["--xz", "-cf", files_archive] + BACKUP_ITEMS
result = subprocess.run(
    tar_cmd, capture_output=True, text=True,
    env={**os.environ, "XZ_OPT": "-T0 -6"},
)
if result.returncode > 1:
    raise RuntimeError(...)
```

`tar` komutunun siyahı formatında verilməsi — `shell=False` (daha təhlükəsiz), pipe operatoru lazım olmadığı üçün.

**`--xz` flag-ı:** `tar` özü `xz` ilə sıxışdırır. Ayrıca `| xz` yazmağa ehtiyac yoxdur.

**`XZ_OPT` mühit dəyişəni:** `tar --xz` işlədəndə `xz`-ə parametr ötürmək üçün bu mühit dəyişəni istifadə olunur. `-T0 -6` burada da tətbiq edilir.

`{**os.environ, "XZ_OPT": "-T0 -6"}` — mövcud mühit dəyişənlərini kopyalayır, `XZ_OPT`-u əlavə edir.

`returncode > 1` — `tar` bəzən 1 ilə bitir (məsələn, sıxışdırma zamanı fayl dəyişdi — "file changed as we read it" xəbərdarlığı). Bu kritik xəta deyil. Yalnız 2+ xəta kimi qəbul edilir.

---

### Parçalamaq qərarı

```python
db_parts = (
    _split_file(db_archive)
    if os.path.getsize(db_archive) > TG_MAX_BYTES
    else [db_archive]
)
```

Fayl 45 MB-dan böyükdürsə `_split_file()` çağırılır, deyilsə tek elementli siyahı qaytarılır. Nəticə hər iki halda siyahıdır — bu sonrakı `for` loop-un eyni formatlı işləməsini təmin edir.

---

### `cleanup_backups()`

```python
def cleanup_backups(*paths):
    for path in paths:
        try:
            os.remove(path)
        except OSError as e:
            logger.warning("Could not remove %s: %s", path, e)
```

Telegram-a göndərildikdən sonra lokal faylları silir. `*paths` — istənilən sayda fayl yolu qəbul edir.

`try/except` — silinmə zamanı xəta olsa (fayl artıq yoxdursa) proqram çökmür, sadəcə xəbərdarlıq yazır.

---

## Blok 11 — Göndərmə mexanizmi

### `_send_file()`

```python
async def _send_file(app, path, caption):
    filename    = os.path.basename(path)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            with open(path, "rb") as f:
                msg = await app.bot.send_document(
                    chat_id=CONFIG["CHANNEL_ID"],
                    document=f,
                    filename=filename,
                    caption=caption,
                    parse_mode="Markdown",
                )
            return msg.document.file_id
        except Exception as exc:
            if attempt < max_retries:
                await asyncio.sleep(5 * attempt)
            else:
                raise
```

Faylı kanalda göndərir, `file_id`-ni qaytarır.

**Retry mexanizmi:** 3 cəhd. Uğursuz olduqda:
- 1-ci uğursuzluq → 5 saniyə gözlə, yenidən cəhd et
- 2-ci uğursuzluq → 10 saniyə gözlə, yenidən cəhd et
- 3-cü uğursuzluq → xəta qaldır

`asyncio.sleep(5 * attempt)` — asinxron gözləmə. Bu müddətdə bot digər işləri görə bilər (məsələn, başqa komuta cavab verə bilər).

`msg.document.file_id` — Telegram hər göndərilən faylı öz serverlarında saxlayır və unikal ID verir. Bu ID ilə faylı yenidən göndərmək, yükləmək mümkündür — `backup_history`-də saxlanır.

---

### `run_and_send_backup()`

```python
async def run_and_send_backup(app, notify_chat_id=None, triggered_by="scheduler"):
```

Backup axışının baş orqestratoru. Həm manual (`/backup`), həm avtomatik (cron) halda bu funksiya çağırılır.

`notify_chat_id` — xəbərdarlıq mesajlarının hansı chata gedəcəyi. Manual backup zamanı istifadəçinin chat_id-si, avtomatik zamanı `None` (yalnız kanala gedir).

```python
async def _reply(text):
    if notify_chat_id:
        await app.bot.send_message(...)
```

Bu daxili funksiya — `notify_chat_id` varsa mesaj göndərir, yoxdursa heç nə etmir. Kodun təkrarlanmasının qarşısını alır.

**Göndərmə növbəsi (send_queue):**

```python
send_queue = []
for i, path in enumerate(db_parts, 1):
    send_queue.append((path, caption, "db", i, len(db_parts)))
for i, path in enumerate(file_parts, 1):
    send_queue.append((path, caption, "files", i, len(file_parts)))
```

Əvvəlcə bütün DB parçaları, sonra bütün fayl parçaları. `enumerate(db_parts, 1)` → 1-dən başlayan sıra nömrəsi.

Ardıcıl göndərmə:
```python
for path, caption, ftype, part_no, total_parts in send_queue:
    file_id = await _send_file(app, path, caption)
    state["backup_history"].append({...})
```

Hər göndərilən fayl `backup_history`-ə əlavə edilir. Bu, `/upload` komutunun əsasıdır.

---

## Blok 12 — Komut handler-ları

### `/start` — `cmd_start`

```python
@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MESSAGES["start"], parse_mode="Markdown")
```

Botun kartviziti. `MESSAGES["start"]` mətni göndərir.

`parse_mode="Markdown"` — `*qalın*`, `` `kod` ``, `_italic_` formatları işlənir.

---

### `/backup` — `cmd_backup`

```python
@admin_only
async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_and_send_backup(
        app=context.application,
        notify_chat_id=update.effective_chat.id,
        triggered_by="manual",
    )
```

Manual backup başladır. `notify_chat_id` olaraq istifadəçinin chat ID-si verilir — proses boyunca mesajlar o chata gedir.

---

### `/lbdate` — `cmd_lbdate`

```python
@admin_only
async def cmd_lbdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs = context.job_queue.get_jobs_by_name("hourly_backup")
    if jobs:
        next_run = jobs[0].next_t
        now      = datetime.datetime.now(datetime.timezone.utc)
        delta    = next_run - now
        total_s  = max(int(delta.total_seconds()), 0)
        mins     = total_s // 60
        secs     = total_s % 60
        remaining = f"{mins} min {secs} sec"
```

Job queue-dan `"hourly_backup"` adlı tapşırığı tapır. `next_t` — növbəti icra vaxtı (UTC). `now - next_t` fərqi verilir.

`max(..., 0)` — vaxt keçmişdədirsə (neqativ) 0 göstərir.

`_build_lbdate_text()` bu məlumatları formatlı mətnə çevirir — son backup vaxtı, fayl adları, növbəti backup.

---

### `/usage` — İnline Keyboard

```python
def _usage_main_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗄 Database", callback_data="usage_db"),
        InlineKeyboardButton("📂 Files",    callback_data="usage_files"),
    ]])
```

**Inline Keyboard nədir?**

Normal Telegram klaviaturasından (ReplyKeyboard) fərqlidir. İnline keyboard mesajın altında görünür, mesajla birlikdədir. Basıldıqda mesaj göndərmir — bir "callback" siqnalı göndərir.

```
┌─────────────────────────────────────┐
│ 📖 How to use backup files          │
│ ...                                 │
│                                     │
│  [🗄 Database]  [📂 Files]          │
└─────────────────────────────────────┘
```

`InlineKeyboardMarkup([[btn1, btn2]])` — içdəki siyahı sıraları, xaricdəki siyahı düymə sıralarını təmsil edir.

```python
# Bir sırada iki düymə
[[btn1, btn2]]

# İki sırada, hər birində bir düymə
[[btn1], [btn2]]

# Üç sıra
[[btn1, btn2], [btn3], [btn4, btn5]]
```

---

**`callback_data` nədir?**

Düyməyə basıldıqda Telegram botuna "arxa planda" göndərilən mətn. İstifadəçi görmür — bot görür. Maksimum 64 simvol.

```python
InlineKeyboardButton("🗄 Database", callback_data="usage_db")
```

İstifadəçi bu düyməyə bassanda bot `update.callback_query.data == "usage_db"` alır.

`CallbackQueryHandler(cb_usage, pattern="^usage_")` — `usage_` ilə başlayan bütün callback_data dəyərləri `cb_usage` funksiyasına yönləndirilir.

---

### `cb_usage` — Callback handler

```python
@admin_callback
async def cb_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()     # ← bu mütləq lazımdır!

    if query.data == "usage_main":
        await query.edit_message_text(...)
    elif query.data == "usage_db":
        await query.edit_message_text(...)
    elif query.data == "usage_files":
        await query.edit_message_text(...)
```

`query.answer()` — Telegram-a "callback alındı" siqnalı. Bu çağırılmazsa istifadəçi tərəfindəki düymə "yükləniyor" animasiyasında qalır, Telegram bir müddət sonra timeout verir.

`query.edit_message_text()` — yeni mesaj göndərmir. **Mövcud mesajı dəyişdirir.** Bu, chat-ın spam olmaması üçün vacibdir — hər düymə basımında yeni mesaj əvəzinə eyni mesaj yenilənir.

---

## Blok 13 — `/upload` sistemi

### `_upload_main_kb()`

```python
def _upload_main_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗄 Database", callback_data="upload_list_db"),
        InlineKeyboardButton("📂 Files",    callback_data="upload_list_files"),
    ]])
```

İlk ekran — DB mi, Files mi seçim.

---

### `_upload_list_kb()` — Səhifələmə (Pagination)

```python
UPLOAD_PAGE_SIZE      = 8    # bir səhifədə neçə backup
UPLOAD_PAGE_THRESHOLD = 10   # neçədən sonra səhifələmə başlasın

def _upload_list_kb(ftype, page: int = 0):
    indexed = [(i, r) for i, r in enumerate(state["backup_history"]) if r["type"] == ftype]
    if not indexed:
        return None
    indexed.reverse()    # ən yeni üstdə
    total = len(indexed)
```

`backup_history`-dən seçilmiş tipin (db/files) backup-larını götürür, orijinal index-lə birlikdə siyahı yaradır. `indexed.reverse()` — ən son backup ən üstdə görünsün.

**Orijinal index niyə lazımdır?**

Siyahı reverse edildi. Əgər düymənin `callback_data`-sına görünüş sırasını yazsaydıq, tıklandıqda `backup_history`-dəki yanlış elementin indexi alınardı. Orijinal index saxlandığından:

```python
InlineKeyboardButton(_label(rec), callback_data=f"upload_get_{orig_idx}")
```

`upload_get_3` basılanda `backup_history[3]`-ü götürürük — həmişə düzgün.

**Səhifələmə məntiqi:**

```python
if total <= UPLOAD_PAGE_THRESHOLD:
    # 10-dan az backup — səhifələmə yox, hamısı bir yerdə
    ...
else:
    # 10+ backup — səhifə-səhifə göstər
    total_pages = (total + UPLOAD_PAGE_SIZE - 1) // UPLOAD_PAGE_SIZE
    page_records = indexed[start: start + UPLOAD_PAGE_SIZE]
    ...
    buttons.append([back_btn, fwd_btn])
```

`(total + UPLOAD_PAGE_SIZE - 1) // UPLOAD_PAGE_SIZE` — yuxarıya yuvarlayan bölmə. Məsələn 23 backup, 8 per page → `(23+7)//8 = 3` səhifə.

Navigation düymələri:
- `◀ Geri` — əvvəlki səhifə. Birinci səhifədəsə `upload_main`-ə gedir.
- `İrəli ▶` — növbəti səhifə. Son səhifədəsə `upload_main`-ə gedir.

---

### `cb_upload` — Upload callback handler

```python
@admin_callback
async def cb_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
```

Bütün `upload_` prefiksi olan callback-lar buraya gəlir.

**`upload_get_N` — faylı serverə yüklə:**

```python
if data.startswith("upload_get_"):
    idx      = int(data.split("_")[-1])
    rec      = state["backup_history"][idx]
    file_id  = rec["file_id"]
    ...
    tg_file = await context.bot.get_file(file_id)
    await tg_file.download_to_drive(target_path)
```

`file_id` ilə Telegram-dan fayl obyekti alınır, `download_to_drive()` ilə yerli diskə yüklənir.

**`upload_page_TYPE_N` — səhifə dəyişikliyi:**

```python
if data.startswith("upload_page_"):
    _, _, ftype, pg = data.split("_")
    kb = _upload_list_kb(ftype, page=int(pg))
```

`"upload_page_db_2".split("_")` → `["upload", "page", "db", "2"]`. `ftype="db"`, `pg="2"`.

---

## Blok 14 — Zamanlı backup (Scheduled Job)

```python
async def scheduled_backup(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Scheduled backup triggered.")
    await run_and_send_backup(app=context.application, triggered_by="scheduler")
```

`context.application` — botun `Application` obyekti. Job içindən bota çatmaq üçün buna ehtiyac var.

---

## Blok 15 — `main()` — Hər şeyin toplanması

```python
def main():
    request = HTTPXRequest(
        connect_timeout=10,
        read_timeout=300,
        write_timeout=300,
        pool_timeout=30,
    )
```

**HTTP timeout-ları:**

| Timeout | Mənası | Dəyər |
|---------|--------|-------|
| `connect_timeout` | Telegram serverinə bağlanmaq üçün maksimum gözləmə | 10 san |
| `read_timeout` | Cavab almaq üçün maksimum gözləmə | 300 san |
| `write_timeout` | Fayl göndərərkən maksimum gözləmə | 300 san |
| `pool_timeout` | Bağlantı pool-undan boş slot gözləmə | 30 san |

`read_timeout=300` və `write_timeout=300` — 300 saniyə = 5 dəqiqə. Böyük backup faylların göndərilməsi üçün kifayət qədər vaxt.

---

```python
app = (
    Application.builder()
    .token(CONFIG["BOT_TOKEN"])
    .request(request)
    .build()
)
```

Builder pattern ilə `Application` yaradılır. `request` obyekti xüsusi timeout-larla verilir.

---

```python
app.add_handler(CommandHandler("start",  cmd_start))
app.add_handler(CommandHandler("backup", cmd_backup))
app.add_handler(CommandHandler("lbdate", cmd_lbdate))
app.add_handler(CommandHandler("usage",  cmd_usage))
app.add_handler(CommandHandler("upload", cmd_upload))

app.add_handler(CallbackQueryHandler(cb_usage,  pattern="^usage_"))
app.add_handler(CallbackQueryHandler(cb_upload, pattern="^upload_"))
```

Handler qeydiyyatı. `pattern="^usage_"` — regex. `^` = sətrin başı. Yəni `callback_data` `usage_` ilə başlayırsa `cb_usage`-ə get.

Bu ayrılma vacibdir: `cb_usage` yalnız `usage_*` callback-ları idarə edir, `cb_upload` yalnız `upload_*`. Qarışıqlıq olmur.

---

```python
interval = CONFIG["BACKUP_INTERVAL_HOURS"] * 3600
app.job_queue.run_repeating(
    scheduled_backup,
    interval=interval,
    first=interval,
    name="hourly_backup",
)
```

`run_repeating` — işi müntəzəm intervallarla işlədir.

| Parametr | Mənası |
|----------|--------|
| `scheduled_backup` | Hansı funksiya çağırılsın |
| `interval` | Neçə saniyədə bir (3600 = 1 saat) |
| `first=interval` | **İlk icra nə vaxt?** `interval` saniyə sonra — yəni bot başlayanda deyil, 1 saat sonra. |
| `name="hourly_backup"` | İşin adı — `get_jobs_by_name()` ilə tapmaq üçün |

`first=interval` yerinə `first=0` yazsaydın bot başlar-başlamaz ilk backup başlardı.

---

```python
app.run_polling(drop_pending_updates=True)
```

Bot polling rejimində başlayır. `drop_pending_updates=True` — bot offline ikən gəlmiş mesajlar atılır. Beləcə bot yenidən başlayanda köhnə `/backup` komutları geri qayıtmır.

---

## Bərpa — Tam prosedur

Backup faylları var, server çökdü. Nə etmək lazımdır?

### 1. Verilənlər bazasını bərpa et

**Tək fayl:**
```bash
xz -d ojs_db_2026-01-15_10-00.sql.xz
mysql -u ojs_user -p ojs_db < ojs_db_2026-01-15_10-00.sql
```

**Parçalanmış fayl:**
```bash
# Parçaları birləşdir
cat ojs_db_2026-01-15_10-00.sql.xz.part* > ojs_db_2026-01-15_10-00.sql.xz

# Sıxışdırmanı aç
xz -d ojs_db_2026-01-15_10-00.sql.xz

# Verilənlər bazasına yüklə
mysql -u ojs_user -p ojs_db < ojs_db_2026-01-15_10-00.sql
```

### 2. Faylları bərpa et

**Tək fayl:**
```bash
tar -xJf ojs_files_2026-01-15_10-00.tar.xz -C /
```

`-C /` — arxivin içindəki mütləq yolları işlədərək `/` kökündən çıxarır. Fayllar avtomatik olaraq `/path/ojs_files/` və `/path/ojs/public/`-a gedəcək.

**Parçalanmış fayl:**
```bash
cat ojs_files_2026-01-15_10-00.tar.xz.part* > ojs_files_2026-01-15_10-00.tar.xz
tar -xJf ojs_files_2026-01-15_10-00.tar.xz -C /
```

### 3. İcazələri düzəlt

```bash
chown -R www-data:www-data /path/ojs_files
chown -R www-data:www-data /path/ojs/public
```

---

## Başqa layihəyə uyğunlaşdırmaq

Bu bot OJS üçün yazılmış olsa da, hər hansı verilənlər bazası + fayl sistemi kombinasiyası üçün uyğunlaşdırmaq asandır.

### WordPress üçün

```python
DB_USER = "wp_user"
DB_PASS = "wp_password"
DB_NAME = "wordpress"

BACKUP_ITEMS = [
    "/path/wordpress/wp-content/uploads/",
    "/path/wordpress/wp-config.php",
]

TAR_EXCLUDES = [
    "--exclude=*/cache/*",
    "--exclude=*/backup*",
    "--exclude=*.log",
]
```

### Django üçün

```python
DB_USER = "django_user"
DB_PASS = "django_pass"
DB_NAME = "django_db"

BACKUP_ITEMS = [
    "/path/myproject/media/",
    "/path/myproject/.env",
    "/etc/nginx/sites-available/myproject",
]
```

### PostgreSQL üçün

`create_backup()` funksiyasında `dump_cmd` dəyişdirilir:

```python
dump_cmd = (
    f'PGPASSWORD="{DB_PASS}" pg_dump -U {DB_USER} -h localhost {DB_NAME}'
    f' | xz -T0 -6 > {db_archive}'
)
```

---

## Qısa yekun

Bu bot kiçik bir Python faylıdır, amma içərisindəki hər mexanizm konkret bir problemə həll gətirir:

- **CONFIG lüğəti** — bir yerdə bütün dəyişkən parametrlər
- **`admin_only` dekoratoru** — icazəsiz girişə qarşı qoruma
- **`xz -T0 -6`** — çox nüvəli sürətli sıxışdırma
- **`_split_file()`** — Telegram limitini aşan fayllar üçün parçalama
- **Retry mexanizmi** — şəbəkə problemlərini öz-özünə həll etmə
- **`backup_history` state**-i — `/upload` komutunun yaddaşı
- **Inline keyboard + callback_data** — Telegram-da interaktiv menü
- **`job_queue.run_repeating()`** — saat başı avtomatik icra
- **`drop_pending_updates=True`** — yenidən başlayanda köhnə komutları atla

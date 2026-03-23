# OJS — Open Journal Systems

---

## OJS nədir?

OJS-i bir redaksiya binası kimi düşün. Binanın içərisindəki hər otaq bir funksiyadır: müəlliflər buradan əlyazmalarını göndərir, redaktorlar növbəti otaqda bunları sıralayır, referee otağında ekspertlər səssizcə oxuyur, korrektor masasında düzəlişlər edilir, son olaraq mətbəə otağında nəşr edilir. Bütün bu axışı bir proqram idarə edir — OJS.

Tam adı **Open Journal Systems**. PKP (Public Knowledge Project) tərəfindən hazırlanmış, GNU GPL v3 lisenziyası ilə pulsuz paylaşılan, PHP ilə yazılmış akademik jurnal idarəetmə sistemidir. 2001-ci ildə ilk versiyası çıxdı, bu gün dünyada **44.000+ jurnal** OJS işlədir, 148 ölkədə, 60+ dildə.

Nə edir:
- Müəllif məqalə göndərir
- Redaktor bölüşdürür, referee (reviewer) tapır
- Referee anonim şəkildə rəy yazır
- Redaktor qərar verir: qəbul, rədd, düzəliş
- Kopyaeditor, layout editor düzəlişlər edir
- Nəşr edilir, saytda yayımlanır
- Google Scholar, DOAJ, OAI-PMH vasitəsilə indekslənir

---

## OJS necə işləyir? — Texniki mexanizm

OJS bir PHP tətbiqidir. Köhnə WordPress kimi deyil — Laravel-in bazasına kecib, lakin özünün xüsusi MVC arxitekturası var (PKP lib).

**İşləmə axışı:**

```
Brauzer → Nginx (443/80)
              ↓
         PHP-FPM (OJS PHP kodu icra olunur)
              ↓
         MariaDB/MySQL (verilənlər)
         +
         Fayl sistemi (/var/ojs_files)
              ↓
         Nginx → Brauzer (cavab)
```

OJS-in iki əsas "qatı" var:

**Presentation Layer (görünüş):** Smarty şablon mühərriki. Tpl faylları. Brauzerə HTML göndərilir.

**Business Layer (məntiq):** `pages/`, `controllers/`, `classes/` qovluqlarındakı PHP sinifləri. Submission, Review, Publication — hamısı ayrı workflow obyektləridir.

**Verilənlər:** MariaDB/MySQL. Bütün metadata, istifadəçilər, jurnallar, submission-lar burada. Faylların özü isə diskdə (`/var/ojs_files`) saxlanır, verilənlər bazasında deyil.

**URL mexanizmi:**

OJS URL-ları belə görünür:
```
https://horizonmsj.com/index.php/horizon/article/view/123
                                    ↑          ↑       ↑
                               jurnal adı   page    id
```

`restful_urls = On` olduqda:
```
https://horizonmsj.com/horizon/article/view/123
```

`index.php` URL-dan düşür. Nginx `try_files` ilə bunu həll edir.

---

## Qurulum — sıfırdan

### Server tələbləri

| Komponent | Minimum | Tövsiyə |
|-----------|---------|---------|
| PHP | 8.1 | 8.2 / 8.3 |
| Verilənlər bazası | MySQL 5.7 / MariaDB 10.3 | MariaDB 10.6+ |
| Nginx | 1.18+ | 1.24+ |
| RAM | 1 GB | 2 GB+ |
| Disk | 10 GB | 50 GB+ |
| OS | Ubuntu 20.04 | Ubuntu 24.04 |

### 1. Sistem yenilənir

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. PHP-FPM qurulur

```bash
sudo apt install -y php8.3-fpm php8.3-cli php8.3-mysql php8.3-xml \
  php8.3-mbstring php8.3-curl php8.3-intl php8.3-zip php8.3-gd \
  php8.3-json php8.3-opcache
```

OJS üçün ayrıca PHP-FPM pool yaratmaq tövsiyə edilir:

```bash
sudo cp /etc/php/8.3/fpm/pool.d/www.conf /etc/php/8.3/fpm/pool.d/ojs.conf
sudo nano /etc/php/8.3/fpm/pool.d/ojs.conf
```

Pool faylında dəyişdirilər:
```ini
[ojs]                                    ; pool adı
user = www-data
group = www-data
listen = /run/php/php8.3-fpm-ojs.sock   ; ayrı socket
listen.owner = www-data
listen.group = www-data
pm = dynamic
pm.max_children = 20
pm.start_servers = 5
pm.min_spare_servers = 3
pm.max_spare_servers = 10
```

`php.ini` ayarları:
```bash
sudo nano /etc/php/8.3/fpm/php.ini
```

```ini
upload_max_filesize = 256M
post_max_size = 256M
memory_limit = 256M
max_execution_time = 300
date.timezone = Asia/Baku
```

### 3. MariaDB qurulur

```bash
sudo apt install -y mariadb-server mariadb-client
sudo mysql_secure_installation
```

Verilənlər bazası və istifadəçi yaradılır:

```sql
CREATE DATABASE ojs_db CHARACTER SET utf8 COLLATE utf8_general_ci;
CREATE USER 'ojs_user'@'localhost' IDENTIFIED BY 'MecgecEpic!2026Auuu';
GRANT ALL PRIVILEGES ON ojs_db.* TO 'ojs_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Nginx qurulur

```bash
sudo apt install -y nginx
```

### 5. OJS yüklənir

```bash
cd /var/www
sudo wget https://pkp.sfu.ca/ojs/download/ojs-3.4.0-10.tar.gz
sudo tar -xzf ojs-3.4.0-10.tar.gz
sudo mv ojs-3.4.0-10 ojs
sudo chown -R www-data:www-data /var/www/ojs
```

Fayl qovluğu yaradılır (web-accessible olmamalıdır):

```bash
sudo mkdir -p /var/ojs_files
sudo chown -R www-data:www-data /var/ojs_files
sudo chmod -R 755 /var/ojs_files
```

---

## Nginx konfiqurasiyası

`/etc/nginx/sites-available/ojs` faylı (bizim real konfiqurasiya):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name horizonmsj.com;
    return 301 https://$host$request_uri;   # HTTP → HTTPS
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name horizonmsj.com;

    root /var/www/ojs;
    index index.php;

    # Certbot tərəfindən əlavə edilmiş SSL
    ssl_certificate /etc/letsencrypt/live/horizonmsj.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/horizonmsj.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Böyük faylların yüklənməsi üçün (məqalə PDF-ləri)
    client_max_body_size 256M;

    # Ayrı log faylları
    access_log /var/log/nginx/ojs-access.log;
    error_log  /var/log/nginx/ojs-error.log;

    # Konfiqurasiya faylına birbaşa giriş QADAĞANDIR
    location ~ config\.inc\.php$ { deny all; }

    # Gizli fayllara (.git, .env) giriş QADAĞANDIR
    location ~ /\.                { deny all; }

    # OJS URL yönləndirilməsi
    location / {
        try_files $uri $uri/ /index.php$uri?$args;
    }

    # PHP-FPM ilə PHP fayllarının işlənməsi
    location ~ \.php(/|$) {
        fastcgi_split_path_info ^(.+?\\.php)(/.*)$;

        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO       $fastcgi_path_info;
        fastcgi_param PATH_TRANSLATED $document_root$fastcgi_path_info;

        include fastcgi_params;
        fastcgi_pass unix:/run/php/php8.3-fpm-ojs.sock;   # OJS pool-u
        fastcgi_read_timeout 300;                          # Uzun əməliyyatlar üçün
        fastcgi_buffers 16 16k;
        fastcgi_buffer_size 32k;
        fastcgi_index index.php;
    }

    # Setup wizard yönləndirilməsi
    location ~ ^/index\.php/index/(en|az|tr)/admin/wizard/(\d+)$ {
        return 302 /index.php/index/$1/admin/contexts;
    }
}
```

**Aktiv et:**
```bash
sudo ln -s /etc/nginx/sites-available/ojs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## `config.inc.php` — hər parametrin mənası

Bu fayl OJS-in beynidir. `/var/www/ojs/config.inc.php`. Birinci sətri silinə bilməz (`<?php exit;`) — əks halda fayl brauzerə açıq gəlir, bütün şifrələr görünür.

---

### `[general]` bölməsi

```ini
app_key = "base64:8ok72OpQKkfE+..."
```
Laravel-dən gəlir. Cookie şifrələməsində işlənir. Qurulum zamanı avtomatik yaradılır. Dəyişsən bütün sessiyalar sıfırlanır.

```ini
installed = On
```
OJS qurulubmu? `Off` olduqda setup wizard yenidən açılır. Qurulumdan sonra avtomatik `On` olur.

```ini
base_url = "https://horizonmsj.com"
```
**Çox vacib.** OJS-in öz URL-ini necə tanıdığı. E-maillərdəki linklər, asset URL-ları — hamısı buradan gedir. Yanlış yazılsa, sistem xəta verir.

```ini
session_cookie_name = OJSSID
```
Brauzer cookie-sinin adı. Başqa OJS qurulumu eyni domendədirsə, adları fərqli olmalıdır — əks halda session-lar qarışır.

```ini
session_lifetime = 30
```
"Məni xatırla" seçildikdə neçə gün aktiv qalsın. 0 yazılsa — brauzer bağlananda session biter.

```ini
time_zone = Asia/Baku
```
Bütün tarix/vaxt göstərmələri bu zona ilə hesablanır. PHP timezone siyahısından götürülür.

```ini
restful_urls = Off
```
`On` olduqda URL-lərdən `index.php` silinir. Nginx-in `try_files` direktivinin düzgün yazılması şərtdir. Bizim qurulumda `Off` — çünki bəzi yönləndirmə problemləri yaşanmışdı.

```ini
allowed_hosts = "[\"horizonmsj.com\", \"46.101.225.20\"]"
```
HOST header injection hücumlarına qarşı qoruma. Yalnız bu host adlarından gələn sorğular qəbul edilir. Serverə IP ilə girişin lazım olduğu hallar üçün IP də əlavə edilib.

```ini
trust_x_forwarded_for = Off
```
Reverse proxy arxasındakı real IP-ni almaq üçün. Nginx özü reverse proxy olduğundan `Off` saxlanılıb — Nginx artıq real IP-ni `REMOTE_ADDR`-ə yazır.

```ini
enable_minified = On
```
JavaScript faylları sıxışdırılmış (minified) versiyada yüklənsin. Production-da `On` olmalıdır — əks halda JS faylları 10x böyük gəlir.

```ini
user_validation_period = 28
```
Yeni istifadəçi 28 günün içərisində e-mailini doğrulamazsa hesab silinir. Bot qeydiyyatlarına qarşı effektiv müdafiədir.

---

### `[database]` bölməsi

```ini
driver = mariadb
host = localhost
username = ojs_user
password = "MecgecEpic!2026Auuu"
name = ojs_db
persistent = Off
collation = utf8_general_ci
```

`persistent = Off` — verilənlər bazası bağlantısı hər sorğudan sonra bağlanır. Yüksək trafikli saylarda connection pooling üçün `On` edilə bilər, amma əksər hosting mühitlərində problemlər çıxarır.

`collation = utf8_general_ci` — Azərbaycan dili üçün diqqət: `utf8mb4_unicode_ci` daha doğrudur (emoji və bəzi simvollara dəstək üçün), amma köhnə qurulumlarla uyğunluq üçün `utf8_general_ci` saxlanılır.

---

### `[cache]` bölməsi

```ini
web_cache = Off
web_cache_hours = 1
```

`web_cache = On` olduqda giriş etməmiş ziyarətçilər üçün statik səhifələr `cache/` qovluğuna yazılır. Yüksək trafik varsa performansı əhəmiyyətli artırır. Amma **diqqət**: jurnal metadata dəyişsə, cache təmizlənməyincə köhnə məlumat görünər. Abunə əsaslı jurnallarda heç vaxt aktiv etmə.

---

### `[i18n]` bölməsi

```ini
locale = en
connection_charset = utf8
```

`locale` — sistem default dili. Bu, OJS-in interfeys dilini deyil, sistem mesajlarının default dilini müəyyənləşdirir. Jurnal dillərini admin panelindən `Site Settings → Languages` hissəsindən idarə edirsən.

---

### `[files]` bölməsi

```ini
files_dir = /var/ojs_files
public_files_dir = public
public_user_dir_size = 5000
```

`files_dir` — **ən vacib parametrlərdən biri.** Bütün yüklənən fayllar (məqalə PDF-ləri, qərar məktubları, review faylları) buraya gedir. Bu qovluq web-accessible olmamalıdır — birbaşa URL ilə açılmamalıdır. Nginx konfiqurasiyamızda bu qovluğa `/var/ojs_files` — web root-dan kənarda yerləşdirilmişdir.

`public_files_dir = public` — İstifadəçilərin TinyMCE editor ilə yüklədiyi şəkillər, editoriallar üçün açıq fayllar. Bu `public/` qovluğu web root-un içindədir (`/var/www/ojs/public`).

`public_user_dir_size = 5000` — kilobyte. Hər istifadəçinin public qovluğunun maksimum ölçüsü (5 MB). 0 yazılsa — yükləmə qadağandır.

---

### `[security]` bölməsi

```ini
force_ssl = On
force_login_ssl = On
session_check_ip = On
encryption = sha1
salt = "MecgecEpic!2026Auuu"
api_key_secret = "a5e219bdf287d04f4bab5561d8ffe0270e83ce32..."
reset_seconds = 7200
```

`force_ssl = On` — Hər sorğu HTTPS-ə yönləndirilir. Sessiya cookie-ləri `Secure` flag ilə işarələnir.

`session_check_ip = On` — Sessiya zamanı istifadəçinin IP dəyişsə, sessiya etibarsız sayılır. Mobilə keçəndə operator dəyişirsə problem çıxara bilər — belə hallarda `Off` edilir.

`encryption = sha1` — Köhnə şifrə hashı metodu. Yeni qeydiyyatlar artıq bcrypt işlədir, amma köhnə hesablarla geriyə uyğunluq üçün saxlanılır.

`salt` — Şifrə sıfırlama hash-larında istifadə olunan gizli duz. Dəyişdirilərsə bütün aktiv şifrə sıfırlama linkləri etibarsız olur.

`api_key_secret` — REST API çağrılarında istifadəçilərin API key-lərini şifrələmək üçün.

`reset_seconds = 7200` — Şifrə sıfırlama linkinin ömrü. 7200 saniyə = 2 saat.

```ini
allowed_html = "a[href|target|title],em,strong,..."
```

Xülasə sahələrində, bioqrafiyalarda icazə verilən HTML teqləri. Burada olmayan hər teq avtomatik silinir (XSS qoruması).

---

### `[email]` bölməsi — mail ayarları

```ini
[email]
default = smtp
smtp = On
smtp_server = smtp.gmail.com
smtp_port = 587
smtp_auth = tls
smtp_username = horizonmsj@gmail.com
smtp_password = rbdcpcnstpdiknfr
allow_envelope_sender = On
default_envelope_sender = horizonmsj@gmail.com
force_default_envelope_sender = On
force_dmarc_compliant_from = On
dmarc_compliant_from_displayname = '%n via %s'
require_validation = Off
```

Bu bölmə standart konfiqurasiyada yoxdur — bizim qurulumda əl ilə əlavə edilmişdir.

**Niyə Gmail SMTP?** DigitalOcean-da port 25 infrastruktur səviyyəsində bloklanmışdır. Yəni OJS-in öz sendmail/Postfix üzərindən göndərməsi mümkün deyil. Gmail App Password (2FA aktiv olduqda yaranan 16 simvollu şifrə) istifadə edilir.

| Parametr | İzah |
|----------|------|
| `smtp_server` | Gmail-in SMTP serveri |
| `smtp_port = 587` | STARTTLS portu (TLS şifrəli) |
| `smtp_auth = tls` | STARTTLS — əvvəl plain bağlantı, sonra şifrəli |
| `smtp_username` | Gmail hesabın ünvanı |
| `smtp_password` | Gmail App Password (hesab şifrəsi deyil!) |
| `force_default_envelope_sender` | Bütün maillər bu ünvandan göndərilsin |
| `force_dmarc_compliant_from` | Gmail DMARC qaydalarına uyğun From header |
| `dmarc_compliant_from_displayname` | Görünən ad: "Müəllif Adı via Horizon MSJ" |

**Mail portlarını anlamaq:**

| Port | Protokol | İstifadə |
|------|----------|---------|
| 25 | SMTP | Server-server göndərmə. DigitalOcean bloklayır. |
| 465 | SMTPS | SSL ilə şifrəli SMTP. Köhnə standard. |
| **587** | **SMTP+STARTTLS** | **Müasir standart. Gmail, Mailgun, hamısı.** |
| 993 | IMAPS | IMAP SSL. Mail almaq. |
| 995 | POP3S | POP3 SSL. Mail almaq (köhnə). |

---

### `[queues]` bölməsi

```ini
default_connection = "database"
default_queue = "queue"
job_runner = On
job_runner_max_jobs = 30
job_runner_max_execution_time = 30
job_runner_max_memory = 80
```

OJS 3.4+ versiyasından işləyən Laravel queue sistemi. E-mail göndərmə, statistika hesablama, metadata ixracı kimi ağır əməliyyatlar dərhal icra olunmur — bir növbəyə (queue) əlavə edilir.

`job_runner = On` — Hər HTTP sorğusunun sonunda növbədəki işlər icra edilir. Kiçik saytlar üçün yetərlidir.

Yüksək trafikli saytlar üçün cron ilə daha yaxşıdır:
```bash
* * * * * php /var/www/ojs/lib/pkp/tools/scheduler.php run >> /dev/null 2>&1
```

---

### `[schedule]` bölməsi

```ini
task_runner = On
task_runner_interval = 60
scheduled_tasks_report_error_only = On
```

Zamanlı tapşırıqlar: statistika toplamaq, xatırlatma e-mailləri göndərmək, abunəlikləri yoxlamaq. `task_runner_interval = 60` saniyədə bir yoxlayır.

---

### `[oai]` bölməsi

```ini
oai = On
repository_id = "ojs.horizonmsj.com"
oai_max_records = 100
```

OAI-PMH (Open Archives Initiative Protocol for Metadata Harvesting). Jurnalın metadata-sını xarici sistemlər (Google Scholar, DOAJ, BASE) avtomatik toplayır. `repository_id` — bu jurnalın unikal kimliyi. Dəyişdirilməsin — mövcud OAI record-larının ID-ləri dəyişər.

---

### `[captcha]` bölməsi

```ini
recaptcha = off
altcha = off
captcha_on_register = on
captcha_on_login = on
```

Google reCaptcha və ya ALTCHA (açıq mənbəli alternativ). `altcha` daha gözəl seçimdir — istifadəçi bir şey etmir, arxa planda JavaScript hesablama edir, botu ayırd edir.

---

### `[debug]` bölməsi

```ini
show_stacktrace = Off
display_errors = Off
```

**Production-da ikisi də `Off` olmalıdır.** `On` olduqda qonaqlar verilənlər bazası şifrəsini, fayl yollarını, bütün texniki xəta məlumatlarını görə bilər.

Development mühitində:
```ini
show_stacktrace = On
display_errors = On
deprecation_warnings = On
```

---

## UFW — Firewall ayarları

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'     # 80 + 443
sudo ufw enable
sudo ufw status
```

OJS üçün xüsusi olaraq başqa portlar açılmır. MariaDB (3306) yalnız lokal işləyir — kənardan giriş qadağandır.

Vəziyyəti yoxlamaq:
```bash
sudo ufw status verbose
```

```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW IN    Anywhere
Nginx Full                 ALLOW IN    Anywhere
```

---

## OJS-i brauzerə çıxarmaq — Kurulum Sehrbazı

Hər şey qurulduqdan sonra `https://horizonmsj.com` ünvanına girilər. OJS setup wizard açılır:

1. **Dil seçimi** — interfeys dili
2. **Admin hesabı** — super administrator
3. **Verilənlər bazası** — driver, host, ad, istifadəçi, şifrə
4. **Fayl qovluğu** — `/var/ojs_files`
5. **Qurulumu tamamla**

Bundan sonra `config.inc.php`-da `installed = On` avtomatik yazılır.

---

## Rol sistemi

OJS-də hər istifadəçinin bir rolu var:

| Rol | Nə edir |
|-----|---------|
| **Site Admin** | Bütün jurnalları idarə edir, plugin qurur |
| **Journal Manager** | Bir jurnalın hər şeyini idarə edir |
| **Editor** | Submission-ları assign edir, qərar verir |
| **Section Editor** | Müəyyən bölmənin submission-larını idarə edir |
| **Reviewer** | Ekspert rəy yazır (anonim) |
| **Author** | Məqalə göndərir |
| **Copyeditor** | Mətn düzəlişi edir |
| **Layout Editor** | Final nəşr fayllarını hazırlayır |
| **Proofreader** | Son yoxlama |
| **Reader** | Yalnız oxuyur (açıq giriş) |

---

## OJS-də submission axışı

```
Müəllif məqaləni göndərir (5 addımlı wizard)
         ↓
Editor görür → Section Editor-a assign edir
         ↓
Reviewer tap → Dəvət göndər → Referee razılaşır
         ↓
Referee rəy yazır (anket + fayllar)
         ↓
Editor bütün rəyləri oxuyur → Qərar:
  → Accept (qəbul)
  → Revisions Required (düzəliş istə)
  → Resubmit for Review (yenidən bax)
  → Decline (rədd)
         ↓
Qəbul edilsə → Copyediting mərhələsi
         ↓
Layout Editor PDF/HTML hazırlayır
         ↓
Proofreader yoxlayır
         ↓
Publication: sayı (issue) yarad → Məqaləni əlavə et → Nəşr et
```

---

## Pluginlər

WordPress-i düşün. Plugin sistemi demək olar ki, eynidir — core koda toxunmadan funksionallıq əlavə edilir.

OJS-də iki növ plugin mövcuddur:

### Plugin növləri (qovluğa görə)

| Qovluq | Növ | Nə edir |
|--------|-----|---------|
| `plugins/generic/` | Generic | Ümumi funksionallıq (ən çox istifadə edilən) |
| `plugins/themes/` | Theme | Görünüş/dizayn |
| `plugins/gateways/` | Gateway | Xarici sistemlərə körpü (OAI-PMH) |
| `plugins/importexport/` | Import/Export | Məlumat giriş/çıxışı (XML, CSV) |
| `plugins/reports/` | Report | Hesabat generatoru |
| `plugins/blocks/` | Block | Kənarda görünən blok (sidebar) |
| `plugins/auth/` | Auth | Alternativ giriş (LDAP, Shibboleth) |
| `plugins/pubIds/` | PubId | DOI, URN kimi nəşr ID sistemləri |
| `plugins/metadata/` | Metadata | Əlavə metadata sxemləri |
| `plugins/paymethod/` | Payment | Ödəniş metodları (PayPal) |

---

### Mövcud əsas pluginlər

**Trafik/Statistika:**
- **Usage Statistics** — məqalə görüntülənmə, yükləmə sayı
- **Google Analytics** — GA4 inteqrasiyası

**İndeksləmə/Keşfedilmə:**
- **Google Scholar Indexing** — Scholar metadata
- **DOAJ Export** — DOAJ üçün XML ixracı
- **Crossref Reference Linking** — DOI inteqrasiyası
- **OAI-PMH Server** — metadata harvesting

**Redaksiya:**
- **Reviewer Recommendations** — referee tövsiyə formu
- **Email Templates** — xüsusi e-mail şablonları

**Görünüş:**
- **Default Theme** — standart görünüş
- **Health Sciences Theme** — tibb jurnalları üçün
- **Manuscript Theme** — sadə, akademik
- **Classic Theme** — köhnə OJS görünüşü

**Fayl/Məzmun:**
- **PDF.js Viewer** — PDF-i brauzerdə göstər
- **HTML Galley** — HTML məqalə görünüşü
- **ORCiD Profile** — ORCID ID inteqrasiyası

**Backup:**
- **Backup Plugin** — `.tar.gz` backup

---

### Plugin quraşdırma — Avto (Plugin Gallery)

**Site Admin → Administration → Plugin Gallery**

1. Siyahıdan plugin tap
2. "Install" düyməsini bas
3. OJS GitHub-dan avtomatik yükləyir
4. Qurulur, aktivləşdirilir

Bu üsul yalnız internet bağlantısı olan serverdə işləyir. Plugin Gallery-dəki pluginlər PKP-nin rəsmi siyahısındandır.

---

### Plugin quraşdırma — Manual

**Plugin Gallery-də olmayan pluginlər üçün:**

1. Plugin-in GitHub/ZIP faylını yüklə
2. OJS admin panelindən **Installed Plugins → Upload a New Plugin**
3. `.tar.gz` faylını yüklə, **Save**

Və ya birbaşa serverə:

```bash
# Plugin ZIP-i yüklə
cd /var/www/ojs/plugins/generic/
sudo wget https://github.com/pkp/pluginName/archive/refs/tags/v1.0.tar.gz
sudo tar -xzf v1.0.tar.gz
sudo mv pluginName-1.0 pluginName
sudo chown -R www-data:www-data pluginName/
```

Bundan sonra OJS admin panelindən **Website Settings → Plugins → Installed Plugins**-dən tapa bilərsən.

**Diqqət:** Manual yüklənən pluginlər `version.xml` faylı olmadan OJS verilənlər bazasında qeydiyyatdan keçmir. Buna görə həmişə `version.xml` olan arxivi istifadə et.

---

## Plugin yazmaq — Addım-addım

Biz `generic` tipli plugin yazacağıq. Bu ən çox istifadə edilən növdür.

### Fayl strukturu

```
plugins/generic/myplugin/
├── index.php           ← Plugin yükləyicisi
├── MyPlugin.inc.php    ← Əsas plugin sinifi
├── version.xml         ← Versiya məlumatı
├── locale/
│   ├── en/
│   │   └── locale.po   ← İngilis dil faylı
│   └── az/
│       └── locale.po   ← Azərbaycan dil faylı
└── templates/
    └── myTemplate.tpl  ← Smarty şablonu (əgər lazımdırsa)
```

---

### `index.php`

```php
<?php
// Plugin-i yüklə, nümunəsini qaytar
require_once('MyPlugin.inc.php');
return new MyPlugin();
```

---

### `version.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE version SYSTEM "../../../lib/pkp/dtd/pluginVersion.dtd">
<version>
    <application>MyPlugin</application>
    <type>plugins.generic</type>
    <release>1</release>
    <major>1</major>
    <minor>0</minor>
    <revision>0</revision>
    <build>0</build>
    <date>2026-01-01</date>
    <lazy-load>0</lazy-load>
    <syscompat>3.4.0</syscompat>
    <class>MyPlugin</class>
</version>
```

---

### `MyPlugin.inc.php` — Əsas sinif

```php
<?php

import('lib.pkp.classes.plugins.GenericPlugin');

class MyPlugin extends GenericPlugin {

    /**
     * Plugin adını qaytar (çox dil dəstəyi üçün)
     */
    public function getDisplayName() {
        return __('plugins.generic.myPlugin.displayName');
    }

    /**
     * Plugin açıqlamasını qaytar
     */
    public function getDescription() {
        return __('plugins.generic.myPlugin.description');
    }

    /**
     * Plugin qeydiyyatı — OJS bu funksiyanı plugin yükləyəndə çağırır
     * $category: plugin növü
     * $path: plugin fayl yolu
     */
    public function register($category, $path, $mainContextId = null) {
        // Əvvəlcə parent register çağır
        if (parent::register($category, $path, $mainContextId)) {
            // Plugin aktiv deyilsə heç nə etmə
            if ($this->getEnabled()) {
                // Hook bağla: hər məqalə görüntüləndikdə bizim funksiya çağırılsın
                HookRegistry::register(
                    'Templates::Article::Main',
                    [$this, 'callbackArticleMain']
                );
            }
            return true;
        }
        return false;
    }

    /**
     * Hook callback-i — məqalə açıldıqda çağırılır
     * $hookName: hook adı
     * $params: [&$smarty, &$output] — Smarty nümunəsi və çıxış
     */
    public function callbackArticleMain($hookName, $params) {
        $smarty =& $params[1];
        $output =& $params[2];

        // Smarty-yə dəyişən ötür
        $smarty->assign('myPluginMessage', 'Bu məqaləyə əlavə məlumat');

        // Şablon render et, çıxışa əlavə et
        $output .= $smarty->fetch(
            $this->getTemplateResource('myTemplate.tpl')
        );

        return false; // false = digər hook-lar da işləsin
    }

    /**
     * Plugin ayarları üçün admin paneli formu
     */
    public function getActions($request, $verb) {
        $router = $request->getRouter();
        import('lib.pkp.classes.linkAction.request.AjaxModal');

        $actions = parent::getActions($request, $verb);

        if ($this->getEnabled()) {
            $actions = array_merge(
                [new LinkAction(
                    'settings',
                    new AjaxModal(
                        $router->url($request, null, null, 'manage', null, [
                            'verb' => 'settings',
                            'plugin' => $this->getName(),
                            'category' => 'generic',
                        ]),
                        $this->getDisplayName()
                    ),
                    __('manager.plugins.settings'),
                    null
                )],
                $actions
            );
        }

        return $actions;
    }
}
```

---

### `templates/myTemplate.tpl` — Smarty şablonu

```smarty
{* Plugin tərəfindən render edilən blok *}
<div class="my-plugin-block">
    <p>{$myPluginMessage}</p>
</div>
```

---

### Locale faylı — `locale/en/locale.po`

```po
msgid "plugins.generic.myPlugin.displayName"
msgstr "My Custom Plugin"

msgid "plugins.generic.myPlugin.description"
msgstr "This plugin does something useful."
```

---

### Hook-lar nədir?

Hook sistemi OJS-in əsas genişlənmə mexanizmidir. Sadə dillə: OJS müəyyən nöqtələrdə "bu nöqtədə biri bir şey əlavə etmək istəyirmi?" deyə soruşur. Plugin "bəli" cavabı verir, öz kodunu icra edir.

Ən çox istifadə edilən hook-lar:

| Hook | Nə zaman çağırılır |
|------|--------------------|
| `Templates::Article::Main` | Məqalə oxu səhifəsi yükləndikdə |
| `Templates::Common::Header` | Hər səhifənin header-i |
| `Templates::Common::Footer` | Hər səhifənin footer-i |
| `SubmissionFile::insertObject` | Fayl yüklənəndə |
| `Schema::get::submission` | Submission schema yüklənəndə |
| `Mail::send` | E-mail göndərilmədən əvvəl |
| `LoadHandler` | URL işlənmədən əvvəl |

---

## Theme plugin yazmaq

Theme plugin vizual görünüşü idarə edir. Generic plugin-dən fərqi: `ThemePlugin` sinifindən genişlənir, CSS/JS öz qovluğundadır.

### Fayl strukturu

```
plugins/themes/mytheme/
├── index.php
├── MyTheme.inc.php     ← ThemePlugin sinifi
├── version.xml
├── styles/
│   ├── index.less      ← Əsas LESS (CSS preprocesor)
│   └── variables.less  ← Rəng dəyişənləri
├── templates/
│   ├── frontend/
│   │   ├── pages/
│   │   │   ├── index.tpl       ← Jurnal ana səhifəsi
│   │   │   └── article.tpl     ← Məqalə səhifəsi
│   │   └── components/
│   │       ├── header.tpl
│   │       └── footer.tpl
└── locale/
    └── en/locale.po
```

---

### `MyTheme.inc.php`

```php
<?php

import('lib.pkp.classes.plugins.ThemePlugin');

class MyTheme extends ThemePlugin {

    /**
     * Theme qeydiyyatı — stil fayllarını əlavə et
     */
    public function init() {
        // Valideyn tema əsas alına bilər (parent theme)
        // $this->setParent('defaultThemePlugin');

        // CSS əlavə et
        $this->addStyle(
            'stylesheet',
            'styles/index.css'    // LESS-dən compile edilmiş
        );

        // JavaScript əlavə et
        $this->addScript(
            'custom-js',
            'js/main.js'
        );

        // Özəl rəng dəyişənini tema ayarlarına əlavə et
        $this->addOption('headerColor', 'colour', [
            'label'   => 'plugins.themes.mytheme.options.headerColor',
            'default' => '#1a1a1a',
        ]);

        $this->addOption('bodyFont', 'radio', [
            'label'   => 'plugins.themes.mytheme.options.bodyFont',
            'options' => [
                'sans'  => 'Sans-serif',
                'serif' => 'Serif',
            ],
            'default' => 'sans',
        ]);
    }

    public function getDisplayName() {
        return __('plugins.themes.mytheme.name');
    }

    public function getDescription() {
        return __('plugins.themes.mytheme.description');
    }
}
```

---

### `templates/frontend/pages/index.tpl` — Jurnal ana səhifəsi

```smarty
{**
 * templates/frontend/pages/index.tpl
 * Jurnalin ana səhifəsi şablonu
 *}
{include file="frontend/components/header.tpl" pageTitleTranslated=$currentJournal->getLocalizedName()}

<main class="journal-home">

    {* Jurnal başlığı *}
    <section class="journal-header">
        <h1>{$currentJournal->getLocalizedName()}</h1>
        {if $currentJournal->getLocalizedDescription()}
            <div class="journal-description">
                {$currentJournal->getLocalizedDescription()}
            </div>
        {/if}
    </section>

    {* Son sayı *}
    {if $currentIssue}
        <section class="current-issue">
            <h2>{translate key="journal.currentIssue"}</h2>
            <a href="{url router=$smarty.const.ROUTE_PAGE page="issue" op="view" path=$currentIssue->getBestIssueId()}">
                {$currentIssue->getIssueIdentification()}
            </a>
        </section>
    {/if}

    {* Elanlar *}
    {if $announcements|@count}
        <section class="announcements">
            <h2>{translate key="announcement.announcements"}</h2>
            {foreach from=$announcements item=announcement}
                <article>
                    <h3>{$announcement->getLocalizedTitle()}</h3>
                    <p>{$announcement->getLocalizedDescriptionShort()}</p>
                </article>
            {/foreach}
        </section>
    {/if}

</main>

{include file="frontend/components/footer.tpl"}
```

---

### Theme aktiv etmək

Admin panelindən: **Journal Settings → Website → Appearance → Theme**. Listdən öz theme-ni seç, **Save** et.

---

## Backup

### Default Backup Plugini

OJS-in default backup plugin-i — `plugins/generic/backup/`. Admin panelindən aktiv edirsən: **Website Settings → Plugins → Generic Plugins → Backup → Activate**.

Sonra: **Administration → Backup**. Bir düyməyə basırsən, `.tar.gz` faylı yaranır: verilənlər bazası dump + fayl sistemi. Amma bu yalnız manual backup üçündür.

---

### Avtomatik Telegram Backup Botu

Bizim qurulumda əl ilə yazılmış `backup_bot.py` işlənir. Saatda bir avtomatik backup edir, Telegram-a göndərir.

**Nə edir:**
- MariaDB-ni `mysqldump` ilə dump edir
- `/var/ojs_files` qovluğunu tar ilə sıxışdırır
- `xz` ilə maksimum sıxışdırır
- Telegram-ın 2GB fayl limitini aşarsa hissə-hissə göndərir
- `/backup`, `/lbdate` (son backup tarixi), `/usage` (disk istifadəsi), `/upload` komutları var

**Cron ilə:**
```bash
0 * * * * /path/to/venv/bin/python /home/user/backup_bot.py --cron >> /var/log/backup_bot.log 2>&1
```

---

### Manual backup

```bash
# Verilənlər bazası
mysqldump -u ojs_user -p ojs_db > ojs_backup_$(date +%Y%m%d).sql

# Fayllar
tar -czf ojs_files_$(date +%Y%m%d).tar.gz /var/ojs_files

# OJS kodu (plugins, config)
tar -czf ojs_code_$(date +%Y%m%d).tar.gz /var/www/ojs
```

Bərpa etmək üçün:

```bash
# Verilənlər bazası bərpası
mysql -u ojs_user -p ojs_db < ojs_backup_20260101.sql

# Fayl bərpası
tar -xzf ojs_files_20260101.tar.gz -C /
```

---

## OJS güncəlləmə

```bash
# 1. Backup al
mysqldump -u ojs_user -p ojs_db > backup_before_upgrade.sql
tar -czf files_backup.tar.gz /var/ojs_files

# 2. Yeni versiyonu yüklə
cd /var/www
wget https://pkp.sfu.ca/ojs/download/ojs-3.4.0-10.tar.gz
tar -xzf ojs-3.4.0-10.tar.gz

# 3. Köhnə config-i köçür
cp /var/www/ojs/config.inc.php /var/www/ojs-3.4.0-10/config.inc.php

# 4. Köhnə qovluqla əvəz et
mv /var/www/ojs /var/www/ojs_old
mv /var/www/ojs-3.4.0-10 /var/www/ojs
chown -R www-data:www-data /var/www/ojs

# 5. Verilənlər bazasını yenilə
cd /var/www/ojs
php tools/upgrade.php upgrade
```

---

## OJS problem həll etmək

**502 Bad Gateway:**
```bash
sudo systemctl status php8.3-fpm
sudo journalctl -u php8.3-fpm -n 50
```

**Fayl yükləmə xətası:**
```bash
ls -la /var/ojs_files
sudo chown -R www-data:www-data /var/ojs_files
```

**E-mail getmir:**
```bash
# OJS-dən test maili: Administration → Email → Send Test Email
# Log yoxla:
sudo tail -f /var/log/nginx/ojs-error.log
```

**PHP xətaları görmək (müvəqqəti):**
```ini
; config.inc.php-da müvəqqəti On et
display_errors = On
show_stacktrace = On
```

**Cache təmizlə:**
```bash
rm -rf /var/www/ojs/cache/fc-*
rm -rf /var/www/ojs/cache/t_compile/*
rm -rf /var/www/ojs/cache/wc-*
```

**Verilənlər bazası cədvəllərini yenilə:**
```bash
php /var/www/ojs/tools/dbXMLtoSQL.php upgrade
```

---

## Faydalı fayllar və qovluqlar

| Yol | Nə var |
|-----|--------|
| `/var/www/ojs/config.inc.php` | Əsas konfiqurasiya |
| `/var/www/ojs/plugins/` | Bütün pluginlər |
| `/var/www/ojs/public/` | Web-accessible public fayllar |
| `/var/www/ojs/cache/` | Cache faylları |
| `/var/www/ojs/lib/pkp/` | PKP core library |
| `/var/www/ojs/classes/` | OJS-ə xas sinif faylları |
| `/var/www/ojs/templates/` | Default Smarty şablonları |
| `/var/www/ojs/pages/` | URL handler-ları |
| `/var/ojs_files/` | Yüklənmiş fayllar (article PDFs) |
| `/var/log/nginx/ojs-access.log` | Nginx giriş log-u |
| `/var/log/nginx/ojs-error.log` | Nginx xəta log-u |

---

## Qısa yekun

OJS mürəkkəb görünür, amma çəpər-çəpərdir. Xaricdən PHP + MariaDB + Nginx birləşməsidir. İçəridən submission workflow + plugin arxitekturası + rol sistemi.

Hər şeyin mərkəzindədir `config.inc.php`. Hər şeyin giriş nöqtəsidir `index.php`. Hər şeyin genişlənmə yolu plugin-lərdir.

Qurulduqdan sonra gündəlik istifadə sadədir. Texniki iş yalnız qurulum, güncəlləmə, plugin əlavəsi zamanı lazım olur.

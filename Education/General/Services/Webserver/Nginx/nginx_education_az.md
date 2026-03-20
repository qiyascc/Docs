# Nginx

---

## Web server nədir?

Bir restoran düşün. Müştəri gəlir, sifariş verir. Ofisiant sifarişi alır, mətbəxə aparır, mətbəx hazırlayır, ofisiant geri gətirir. Müştəri bilmir ki, arxada nə oldu — o yalnız sifariş verdi, yeməyi aldı.

Web server da ofisiantdır. Brauzer bir saytı açmaq istəyir — bu bir sifarişdir. Web server o sifarişi alır, arxada lazım olan hər şeyi tapır (HTML, CSS, fayl, verilənlər bazasından gələn məlumat), birləşdirir, brauzerə göndərir. Brauzerin işi yoxdur ki, bu arxada necə baş verdi.

Texniki tərifi: web server HTTP/HTTPS protokolları üzərindən gələn sorğuları qəbul edən, cavab hazırlayan və göndərən proqram (və ya kompüterdir).

Web server iki şey edə bilir:

**Statik məzmun**: HTML, CSS, JS, şəkil, PDF — fayl diskdədir, birbaşa göndərilir. Heç bir emal yoxdur.

**Dinamik məzmun**: İstifadəçiyə görə dəyişən məlumat. Bu halda web server arxaya bir proqrama (Django, PHP, Node.js) ötürür, o proqram emal edir, nəticəni web serverə qaytarır, web server isə brauzerə göndərir.

---

## HTTP və HTTPS: protokollar

Web serverə müraciət edəndə iki protokoldan biri işlənir.

**HTTP** (HyperText Transfer Protocol): Brauzer ilə server arasındakı danışıq dilidir. Problem: şifrəsizdir. Aradakı biri trafiyi dinləsə, hər şeyi görür.

**HTTPS** = HTTP + TLS şifrələməsi. Eyni danışıqdır, amma şifrəlidir. Aradakı biri dinləsə, görcəyi yalnız anlamsız şifrəli mətn olacaq.

| Protokol | Port | Şifrə | Nə zaman |
|----------|------|--------|----------|
| HTTP | 80 | Yoxdur | Yalnız test/lokal |
| HTTPS | 443 | TLS ilə | Hər production sayt |

Bugün hər ciddi sayt HTTPS-dir. Brauzer HTTP saytları "Təhlükəsiz deyil" kimi işarələyir, Google sıralamada geri salır.

---

## Apache: qısaca

Apache 1995-ci ildə yaranıb. Uzun illər dünyanın ən çox istifadə edilən web serveri olub.

**İşləmə prinsipi — proses əsaslıdır:**

Hər gələn sorğu üçün ayrı bir proses (və ya thread) yaradır. 1000 eyni zamanlı istifadəçi varsa — 1000 proses. Hər proses RAM tutur. Trafik artdıqca RAM bitir, server yavaşlayır.

**Güclü tərəfləri:**
- `.htaccess` dəstəyi — qovluq səviyyəsində konfiqurasiya. Shared hosting üçün əvəzsizdir.
- Modul sistemi çox zəngindir, PHP-ni birbaşa içinə yükləyə bilir (`mod_php`).
- Legacy tətbiqlər Apache-yə alışmış ola bilir.

**Zəif tərəfləri:**
- Yüksək trafik altında resurs istehlakı çoxdur.
- Statik faylları Nginx qədər sürətli vermir.

Apache hələ də işlənir. Köhnə WordPress qurulumlarında, shared hostingdə standartdır. Amma yeni layihə başlayırsansa, Nginx seçimi daha ağlabatandır.

---

## Nginx: əsas mövzu

Nginx (oxunuşu: "engine-x") 2004-cü ildə Igor Sysoev tərəfindən yazılmışdır. Məqsəd aydın idi: Apache-nin yüksək trafik altında yaşadığı problem — "C10K problemi" (10.000 eyni zamanlı bağlantı) — həll etmək.

Bugün dünyadakı ən yüksək trafikli saytların əksəriyyəti Nginx işlədir: Netflix, Airbnb, GitHub, WordPress.com, Dropbox.

---

### Nginx necə işləyir?

Apache hər sorğu üçün ayrı proses açırdı. Nginx fərqli düşündü.

Nginx-in **event-driven (hadisə əsaslı)** arxitekturası var. Bir az belə düşün:

Apache bir çağrı mərkəzidir — hər müştəri üçün bir operator. 1000 müştəri — 1000 operator. Hamısı oturub gözləyir, biri bir şey istəyəndə o operatora keçir.

Nginx isə bir operator + çox ekranlı monitor sistemidir. Bir operator minlərlə bağlantıya eyni zamanda baxır. Biri cavab istəyəndə cavab verir, digəri yükləyənə qədər başqasına baxır. Heç biri boş oturmur.

Texniki olaraq: Nginx-in bir **master prosesi** var, o bir neçə **worker prosesi** yaradır. Hər worker prosesi minlərlə bağlantıya eyni zamanda xidmət edir, bloklanmır. RAM istifadəsi sabitdir — trafik artsa belə proses sayı artmır.

<br>

**Nəticə:**

| | Apache | Nginx |
|---|---|---|
| Memarlıq | Proses əsaslı | Hadisə əsaslı (async) |
| Eyni zamanlı bağlantı | Hər biri üçün proses | Bir worker minlərini idarə edir |
| RAM istifadəsi | Trafiklə birlikdə artır | Sabit qalır |
| Statik fayл | Orta | Çox sürətli |
| Dinamik məzmun | Birbaşa (mod_php) | Proxy ilə (PHP-FPM) |
| `.htaccess` | Var | Yoxdur (mərkəzi konfiq) |
| Konfiqurasiya | Dağınıq ola bilər | Mərkəzi, səliqəli |

---

## Nginx qurulması

```bash
sudo apt update
sudo apt install nginx
```

Qurulduqdan sonra avtomatik başlayır. Yoxlamaq üçün:

```bash
sudo systemctl status nginx
```

Çıxışda `Active: active (running)` görünürsə — işləyir.

Brauzerdə serverın IP-sinə girsən, Nginx-in "Welcome to nginx!" səhifəsini görürsən. Bu o deməkdir ki, port 80-dən cavab verir.

---

## UFW — Firewall

Server qurulduqda bütün portlar açıq gəlmir. UFW (Uncomplicated Firewall) Ubuntu-nun standart güvənlik duvarıdır. Hansı portun açıq, hansının bağlı olacağını idarə edir.

### UFW niyə lazımdır?

Server internetə açıqdır. Hər port açıq olsa — hər kəs hər şeyə bağlana bilər. UFW deyir: "Yalnız bu portlara icazə var, qalanları bağlıdır."

### UFW əsas komutları

```bash
sudo ufw status           # Firewall aktivdirmi, hansı qaydalar var
sudo ufw enable           # UFW-ni aktiv et
sudo ufw disable          # UFW-ni söndür (tövsiyə edilmir)
```

### Port və xidmət əlavə etmək

```bash
sudo ufw allow OpenSSH         # SSH bağlantısına icazə ver (port 22)
sudo ufw allow 22              # Eyni şey — port nömrəsi ilə
sudo ufw allow 80              # HTTP
sudo ufw allow 443             # HTTPS
sudo ufw allow 'Nginx HTTP'    # Nginx HTTP profili (port 80)
sudo ufw allow 'Nginx HTTPS'   # Nginx HTTPS profili (port 443)
sudo ufw allow 'Nginx Full'    # Nginx hər ikisi (80 + 443)
```

### Port silmək

```bash
sudo ufw delete allow 80
sudo ufw delete allow 'Nginx HTTP'
```

### Standart quruluş

```bash
sudo ufw allow OpenSSH      # SSH-i unutma — itirərsən serverə girə bilməzsən!
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Çıxış belə görünməlidir:

```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
Nginx Full                 ALLOW       Anywhere
OpenSSH (v6)               ALLOW       Anywhere (v6)
Nginx Full (v6)            ALLOW       Anywhere (v6)
```

**Diqqət:** UFW-ni aktiv etmədən öncə mütləq `OpenSSH`-ə icazə ver. Unutsan — SSH bağlantın kəsilər, serverə girə bilməzsən.

---

## Nginx komutları

```bash
sudo systemctl start nginx      # Başlat
sudo systemctl stop nginx       # Dayandır
sudo systemctl restart nginx    # Yenidən başlat (bağlantılar kəsilir)
sudo systemctl reload nginx     # Konfiqurasiyanı yenilə (bağlantılar kəsilmir)
sudo systemctl enable nginx     # Server açılışında avtomatik başlat
sudo systemctl status nginx     # Hal-hazırkı vəziyyəti göstər

sudo nginx -t                   # Konfiqurasiyanı yoxla (syntax error var mı?)
sudo nginx -T                   # Konfiqurasiyanı göstər (test + print)
```

**`nginx -t`** çox vacibdir. Konfiqurasiyanı dəyişdirəndə mütləq əvvəl `nginx -t` çalıştır. Xəta varsa, `reload` etməzdən qabaq görürsən — sayt yerə düşmür.

---

## Konfiqurasiya strukturu

Nginx-in bütün konfiqurasiyası `/etc/nginx/` qovluğundadır:

```
/etc/nginx/
├── nginx.conf              ← Əsas konfiqurasiya faylı
├── sites-available/        ← Mövcud saytların konfiqurasyonları (hamısı)
│   ├── default
│   └── qiyas.cc
├── sites-enabled/          ← Aktiv saytlar (sites-available-dən simlink)
│   ├── default → ../sites-available/default
│   └── qiyas.cc → ../sites-available/qiyas.cc
├── conf.d/                 ← Əlavə konfiqurasiyalar
├── snippets/               ← Paylaşılan hissələr (SSL, FastCGI...)
└── mime.types              ← Fayl növlərinin MIME tipləri
```

**Məntiq:** Konfiqurasiyanı `sites-available`-da yazırsan. Aktiv etmək istəyəndə `sites-enabled`-a simlink yaradırsan. Söndürmək istəyəndə simlinki silirsən — original fayl durur.

```bash
# Saytı aktiv et
sudo ln -s /etc/nginx/sites-available/qiyas.cc /etc/nginx/sites-enabled/

# Saytı söndür
sudo rm /etc/nginx/sites-enabled/qiyas.cc
```

---

## Server block — sayt konfiqurasiyası

Server block (Apache-də "Virtual Host" deyilir) bir domenin necə xidmət ediləcəyini müəyyən edir.

### Sadə statik sayt

```nginx
server {
    listen 80;
    listen [::]:80;

    server_name qiyas.cc www.qiyas.cc;

    root /var/www/qiyas.cc/html;
    index index.html index.htm;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

| Direktiv | Nə edir |
|----------|---------|
| `listen 80` | Port 80-dən gözlə (HTTP) |
| `listen [::]:80` | IPv6 üçün eyni |
| `server_name` | Bu konfiqurasiya hansı domenlərə aid olsun |
| `root` | Fayllar harada yerləşir |
| `index` | Default fayl nə olsun |
| `try_files` | Fayl varsa ver, yoxdursa 404 qaytar |

### Faylı yarat, aktiv et:

```bash
sudo mkdir -p /var/www/qiyas.cc/html
sudo nano /etc/nginx/sites-available/qiyas.cc
# ... konfiqurasiyanı yaz ...

sudo ln -s /etc/nginx/sites-available/qiyas.cc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Reverse proxy — Django / Node.js üçün

Bu Nginx-in ən çox istifadə edilən ssenarisidir. Django, FastAPI, Node.js — bunlar öz HTTP serverləriyle işləyir (Gunicorn, Uvicorn, Express). Amma bu serverləri birbaşa internetə açmaq olmaz. Nginx önə oturur:

```
İstifadəçi → Nginx (443/80) → Gunicorn (8000, yalnız lokal)
```

Nginx dışarıya açıq, Gunicorn yalnız lokal. Nginx hər sorğunu Gunicorn-a ötürür, Gunicorn cavab hazırlayır, Nginx brauzerə göndərir.

```nginx
server {
    listen 80;
    server_name qiyas.cc www.qiyas.cc;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/qiyas.cc/static/;
    }

    location /media/ {
        alias /var/www/qiyas.cc/media/;
    }
}
```

`/static/` və `/media/` qovluqları Nginx birbaşa verir — Gunicorn-a ötürmür. Statik fayllar üçün Nginx çox daha sürətlidir.

---

## Certbot — pulsuz SSL sertifikatı

HTTPS üçün SSL/TLS sertifikatı lazımdır. Bu sertifikat bir sertifikat orqanı (CA) tərəfindən verilir. **Let's Encrypt** pulsuz sertifikat verən qeyri-kommersiya CA-dır. **Certbot** isə Let's Encrypt ilə avtomatik işləyən alətdir.

Certbot nə edir:
1. Let's Encrypt-ə müraciət edir
2. Domenin sənin olduğunu sübut edir (HTTP challenge)
3. Sertifikatı yükləyir
4. Nginx konfiqurasiyasını avtomatik dəyişir
5. Yeniləməni (renewal) avtomatik idarə edir

Sertifikatların ömrü 90 gündür. Certbot bunu avtomatik yeniləyir — sən bir daha əl vurmusan.

### Certbot qurulması

```bash
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### Sertifikat alma

Əvvəlcə domenin serverə işarə etdiyini yoxla (DNS A record). Sonra:

```bash
sudo certbot --nginx -d qiyas.cc -d www.qiyas.cc
```

Certbot soruşacaq:
- E-mail ünvanı (bildiriş üçün)
- Şərtləri qəbul edirsənmi?
- HTTP-ni HTTPS-ə yönləndir?

"Redirect" seçsən — http://qiyas.cc-yə gələn hər kəs avtomatik https://qiyas.cc-yə köçürülür.

### Bundan sonra Nginx konfiqurasyonu belə görünür:

```nginx
server {
    listen 443 ssl;
    server_name qiyas.cc www.qiyas.cc;

    ssl_certificate /etc/letsencrypt/live/qiyas.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qiyas.cc/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name qiyas.cc www.qiyas.cc;
    return 301 https://$host$request_uri;  # HTTP → HTTPS yönləndir
}
```

### Yeniləməni test et

```bash
sudo certbot renew --dry-run
```

"Congratulations, all simulated renewals succeeded" görünsə — avtomatik yeniləmə düzgün qurulub. Bir daha əl vurmağa ehtiyac yoxdur.

### Sertifikat vəziyyətini yoxla

```bash
sudo certbot certificates
```

---

## UFW + Certbot birlikdə

Certbot qurulduqdan sonra UFW-də `Nginx Full` aktiv olmalıdır (həm 80, həm 443). Əgər əvvəl yalnız `Nginx HTTP` əlavə etmişdinsə:

```bash
sudo ufw allow 'Nginx Full'
sudo ufw delete allow 'Nginx HTTP'
sudo ufw status
```

---

## `location` bloku — URL yönləndirməsi

Nginx-də hər URL-in necə işlənəcəyini `location` ilə müəyyən edirsən.

```nginx
location / {
    # Kök URL — hamısını Gunicorn-a ötür
    proxy_pass http://127.0.0.1:8000;
}

location /static/ {
    # Statik faylları Nginx birbaşa versin
    alias /var/www/qiyas.cc/static/;
    expires 30d;          # 30 gün brauzer cache-i
    add_header Cache-Control "public";
}

location /api/ {
    # API sorğularını başqa porta ötür
    proxy_pass http://127.0.0.1:8001;
}

location ~* \.(jpg|jpeg|png|gif|ico|svg)$ {
    # Şəkil faylları — regex ilə tutma
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location = /favicon.ico {
    # Tam URL uyğunluğu
    log_not_found off;
    access_log off;
}
```

**Uyğunluq prioriteti:**

1. `= /yol` — tam uyğunluq (ən yüksək prioritet)
2. `^~ /yol` — başlanğıc uyğunluğu, regex yoxlanmaz
3. `~` — böyük/kiçik hərfə həssas regex
4. `~*` — böyük/kiçik hərfə həssas olmayan regex
5. `/yol` — adi başlanğıc uyğunluğu

---

## Gzip sıxışdırma

Faylları göndərməzdən sıxışdırır. Ölçü azalır, sürət artır.

```nginx
# nginx.conf içərisində http {} blokunda
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_proxied any;
gzip_types
    text/plain
    text/css
    text/javascript
    application/javascript
    application/json
    application/xml
    image/svg+xml;
```

---

## Rate limiting — sorğu limiti

DDoS hücumlarına qarşı, brute force-a qarşı sorğu sürətini məhdudlaşdırmaq:

```nginx
# http {} blokunda
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

# server {} blokunda
location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://127.0.0.1:8000;
}
```

Bu konfiqurasiya hər IP-dən saniyədə maksimum 10 sorğuya icazə verir. 20-lik "burst" (sürtkü) tolerantlığı var.

---

## Log faylları

```bash
# Giriş log-u — kim, nə vaxt, nə istəyib
sudo tail -f /var/log/nginx/access.log

# Xəta log-u — nə problem var
sudo tail -f /var/log/nginx/error.log
```

Xüsusi sayt üçün ayrı log:

```nginx
server {
    access_log /var/log/nginx/qiyas.cc.access.log;
    error_log  /var/log/nginx/qiyas.cc.error.log;
}
```

---

## Problem həll etmək

**Sayt açılmır:**
```bash
sudo nginx -t                          # Konfiqurasiya xətası varmı?
sudo systemctl status nginx            # Nginx işləyirmi?
sudo ufw status                        # Port açıqdırmı?
sudo tail -n 50 /var/log/nginx/error.log  # Xəta mesajı nədir?
```

**502 Bad Gateway:**
Nginx işləyir, amma arxadakı tətbiq (Gunicorn, Uvicorn) işləmir.
```bash
sudo systemctl status gunicorn         # Gunicorn aktivdirmi?
sudo journalctl -u gunicorn -n 50      # Gunicorn log-u
```

**Sertifikat xətası:**
```bash
sudo certbot certificates              # Sertifikat vəziyyəti
sudo certbot renew --dry-run           # Yeniləmə testi
```

---

## Tam quruluş: sıfırdan işlək sayt

```bash
# 1. Nginx qur
sudo apt update && sudo apt install nginx

# 2. UFW ayarla
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# 3. Sayt qovluğu yarat
sudo mkdir -p /var/www/qiyas.cc
sudo chown -R $USER:$USER /var/www/qiyas.cc

# 4. Konfigurasiya faylı yaz
sudo nano /etc/nginx/sites-available/qiyas.cc

# 5. Aktiv et
sudo ln -s /etc/nginx/sites-available/qiyas.cc /etc/nginx/sites-enabled/

# 6. Test et, yenidən yüklə
sudo nginx -t && sudo systemctl reload nginx

# 7. Certbot qur
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# 8. Sertifikat al
sudo certbot --nginx -d qiyas.cc -d www.qiyas.cc

# 9. Yenidən yüklə
sudo systemctl reload nginx
```

---

## Qısa yekun

Web server internetlə tətbiqin arasındakı "ofisiant"dır. Apache proseslərlə, Nginx hadisələrlə işləyir — ikincisi daha az resursla daha çox bağlantıya xidmət edir.

Nginx qurmaq 2 əmrdir. Amma düzgün işlətmək üçün bilmək lazımdır: UFW niyə lazımdır, server block necə yazılır, reverse proxy nədir, Certbot necə işləyir.

Bir saytı sıfırdan HTTPS ilə ayağa qaldırmaq üçün lazım olan hər şey yuxarıdadır.

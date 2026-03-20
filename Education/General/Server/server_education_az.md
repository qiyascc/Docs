# Server

---

## Server nədir?

Server əslində adi bir kompüterdir. Fərqi yoxdur — içərisində prosessor var, RAM var, disk var. Amma fərq ondadır ki, bu kompüter 7/24 işləyir, ekranı yoxdur (bəzən olur), klaviaturası yoxdur, yanında oturmursan. Ona uzaqdan bağlanırsan, əmr yazırsan, işini görürsən.

Evdəki kompüterin bir faylı yalnız sən açırsan. Serverdəki fayla eyni anda yüzlərlə adam müraciət edə bilir. Bu sadəcə onun üzərinə qoyulmuş rol fərqidir.

---

## Server əməliyyat sistemləri

Kompüterə əməliyyat sistemi lazımdır. Serverlərə də. Amma serverlər üçün istifadə olunan əməliyyat sistemləri bir az fərqlidir — çünki orada ekranda video izləmirsən, grafik interfeys lazım deyil. Lazım olan şey: sabitlik, sürət, uzaqdan idarə.

### Linux

Linux açıq mənbəli bir əməliyyat sistemidir. Yəni kodu hamı görə bilər, istəyən dəyişiklik edə bilər. Bu səbəbdən onlarca fərqli "Linux versiyası" (distribution / distro) mövcuddur.

Serverlərdə Linux-un seçilməsinin səbəbi sadədir: pulsuz, etibarlı, yüngül və terminalla mükəmməl işləyir. Dünya üzrə serverlerin böyük əksəriyyəti Linux ilə işləyir.

**Məşhur Linux distroları:**

| Distro | Nə üçün?|
|---|---|
| Ubuntu | Ən geniş yayılmış, sənədləşməsi zəngin |
| Debian | Stabil, server üçün güclü |
| CentOS / AlmaLinux | Korporativ mühitlər |
| Arch Linux | Tam nəzarət istəyənlər üçün |

### Windows Server

Microsoft-un server versiyasıdır. Grafik interfeysi var, tanış görünür. .NET, MSSQL, Active Directory kimi Microsoft ekosistemi ilə işləyirsənsə məna kəsb edir.

Amma Linux ilə müqayisədə: lisenziya pullu, resurs istehlakı yüksəkdir, server mühitlərindəki payı daha aşağıdır.

Seçim sualı belədir: hansı texnologiya ilə işləyirsən? Django, Python, Node.js → Linux. Böyük korporativ Windows altyapısı → Windows Server.

---

## Bizim server

Bizim serverimiz **Ubuntu Linux**-dur. Ubuntu, Linux-un ən populyar versiyalarından biridir, sənədləşməsi genişdir, cəmiyyəti böyükdür, problemlər üçün həmişə cavab tapmaq olur.

Bundan sonra hər şeyi Ubuntu üzərindən izah edəcəyik.

---

### Server əslində bir kompüterdir

Bunu bir daha vurğulamaq lazımdır, çünki ilk dəfə serverə bağlanan insanlar onu mücərrəd bir şey kimi təsəvvür edir.

Serverin içərisində:
- CPU var
- RAM var
- SSD/HDD var
- Şəbəkə kartı var
- Əməliyyat sistemi var

Fərqi nədir? Onun qarşısında oturmursan. Ona şəbəkə üzərindən (SSH ilə) bağlanırsan, əmrlər yazırsan, o da icra edir. Nəticəni sənə göndərir.

---

### Terminal və komutlar

Serverə bağlandıqdan sonra sənin əsas alətin terminaldır. Ekranda heç bir düymə yoxdur, sən əmr (komut) yazırsan, Enter basırsan, sistem icra edir.

```bash
ls
```

Bu əmr cari qovluqdakı faylların siyahısını göstərir. `ls` = list. Siyahıla.

```bash
pwd
```

Bu əmr hazırda hansı qovluqda olduğunu göstərir. `pwd` = print working directory.

Komutlar belə işləyir: sən bir söz yazırsan, arxasına lazım olsa əlavə məlumat verirsən, sistem anlayır və işi görür.

---

### Flag nədir?

Komutlara əlavə davranış vermək üçün **flag** istifadə olunur. Flaglar adətən `-` işarəsindən sonra gəlir.

Məsələn:

```bash
ls
```
sadəcə faylları göstərir.

```bash
ls -l
```
faylları ətraflı (uzun format) göstərir — icazələr, sahibi, ölçü, tarix.

```bash
ls -a
```
gizli faylları da göstərir (nöqtə ilə başlayan fayllar).

```bash
ls -la
```
hər ikisini birlikdə işlədə bilərsən.

Flaglar hər komuta xas deyil. Hər komutun özünəməxsus flagları var. Bilmədikdə:

```bash
ls --help
```

Bu flagı demək olar ki, hər komutda işlədə bilərsən — o komutun nə etdiyini və hansı flaglarının olduğunu göstərir.

---

### Standart komutlar

Bunlar gündəlik işdə ən çox istifadə olunan komutlardır:

**Naviqasiya:**

```bash
pwd              # Hazırki qovluğun yolunu göstər
ls               # Qovluqdakı faylları listələ
ls -la           # Ətraflı, gizli fayllarla birlikdə
cd /home/user    # Həmin qovluğa keç
cd ..            # Bir üst qovluğa get
cd ~             # Ev qovluğuna qayıt
```

**Fayl/Qovluq əməliyyatları:**

```bash
mkdir layihə          # Yeni qovluq yarat
touch fayl.txt        # Boş fayl yarat
cp fayl.txt /tmp/     # Fayl kopyala
mv fayl.txt yeni.txt  # Fayl adını dəyiş və ya köçür
rm fayl.txt           # Fayl sil
rm -rf qovluq/        # Qovluğu içindəkilərlə birlikdə sil (diqqətlə!)
```

**Fayl oxuma:**

```bash
cat fayl.txt          # Faylın içinə bax
less fayl.txt         # Səhifə-səhifə oxu (q ilə çıxılır)
head -n 20 fayl.txt   # İlk 20 sətri göstər
tail -f log.txt       # Sonu canlı izlə (loglar üçün əla)
```

**Sistem:**

```bash
whoami               # Hansı user olduğunu göstər
hostname             # Serverin adını göstər
df -h                # Disk istifadəsini göstər
free -h              # RAM istifadəsini göstər
top                  # Canlı prosesləri göstər (q ilə çıxılır)
htop                 # Daha gözəl versiyası (qurulum lazım ola bilər)
uptime               # Serverin nə qədərdir işlədiyini göstər
```

**Şəbəkə:**

```bash
ping google.com      # Əlaqəni yoxla
curl https://...     # URL-ə sorğu göndər
wget https://...     # Faylı yüklə
```

---

### Root nədir?

Linux-da hər istifadəçinin (user) müəyyən icazələri var. Bəzi faylları oxuya bilər, bəzilərini oxuya bilməz. Bəzi proqramları qura bilər, bəzilərini qura bilməz.

**Root isə hamısını edə bilər.**

Root sistemin sahibidir. Sil, yaz, qur, sök — heç bir məhdudiyyət yoxdur. Bu güclü olduğu qədər təhlükəlidir. Bir yanlış komut bütün sistemi poza bilər.

Root-un terminal görünüşü belə olur:

```
root@server:~#
```

Normal userin görünüşü isə belə:

```
qiyas@server:~$
```

`#` işarəsi root olduğunu bildirir. `$` isə normal user.

Root ilə hər zaman işləmək tövsiyə edilmir. Lazım olan iş üçün root səlahiyyətini alırsan, işi görürsən, qayıdırsan.

---

### sudo nədir?

`sudo` = **s**uper**u**ser **do**. Yəni "bu əmri super istifadəçi kimi icra et."

Root kimi davamlı girmək əvəzinə, lazım olanda bir əmrin önünə `sudo` yazırsan:

```bash
sudo apt update
```

Bu `apt update` əmrini root icazəsiyle işlədər. Sistem sənin şifrəni soruşacaq, doğru girərsən, icra olar.

**sudo nə zaman lazımdır?**

- Sistem paketlərini quranda (`apt install`)
- Sistem fayllarını dəyişdirəndə (`/etc/` içərisindəki fayllar)
- Servisleri başladanda/dayandıranda (`systemctl`)
- Digər userların fayllarına müdaxilə edəndə

**Kim sudo işlədə bilər?**

Hamı yox. Yalnız `sudo` qrupuna daxil edilmiş istifadəçilər.

---

### İstifadəçilər (Users)

Serverə birdən çox adam bağlana bilər. Hər birinin ayrı hesabı olur.

**Hazırki userları gör:**

```bash
cat /etc/passwd
```

Bu faylda sistemdəki bütün istifadəçilər var.

**Yeni user yarat:**

```bash
sudo adduser mecgec
```

Sistem şifrə soruşacaq, digər məlumatlar (ad, telefon) Enter ilə keçilə bilər.

Bu əmr avtomatik olaraq:
- `/home/elvin` qovluğunu yaradır
- Standart konfiqurasiya fayllarını kopyalayır
- Useri sistemə əlavə edir

**Useri sil:**

```bash
sudo deluser mecgec
sudo deluser --remove-home mecgec   # Ev qovluğunu da sil
```

**Userin şifrəsini dəyiş:**

```bash
sudo passwd mecgec
```

---

### Root-a access vermək

Yeni yaratdığın user heç nə edə bilməz, sudo yoxdur. Root icazəsi vermək üçün onu `sudo` qrupuna əlavə etmək lazımdır:

```bash
sudo usermod -aG sudo mecgec
```

`-aG` flagı nə edir? `-a` = append (əlavə et), `-G` = qrupa. Yəni "elvin-i sudo qrupuna əlavə et, digər qruplardan çıxartma."

Yoxlamaq üçün:

```bash
groups mecgec
```

Çıxışda `sudo` görünürsə, icazə verilib.

---

### Qruplar

Qruplar istifadəçiləri bir araya toplamaq üçündür. Məsələn bir layihənin üzərində 5 nəfər işləyir, onların hamısına eyni qovluğa icazə vermək istəyirsən. Hər birini ayrı-ayrı əlavə etmək əvəzinə bir qrup yaradırsan, qovluğu həmin qrupa verirsən, adamları qrupa əlavə edirsən.

**Qrup yarat:**

```bash
sudo groupadd cc_group
```

**Useri qrupa əlavə et:**

```bash
sudo usermod -aG cc_group mecgec
```

**Qovluğun qrupunu dəyiş:**

```bash
sudo chgrp cc_group /var/www/cc_group
```

**Mövcud qrupları gör:**

```bash
cat /etc/group
```

---

### İcazə kodları (Permissions)

Linux-da hər faylın üç növ sahibi var:

- **u** — user (faylın sahibi)
- **g** — group (faylın qrupu)
- **o** — other (başqaları)

Hər birinin üç növ icazəsi var:

- **r** — read (oxu)
- **w** — write (yaz)
- **x** — execute (icra et)

`ls -l` ilə faylları göstərəndə belə bir şey görürsən:

```
-rwxr-xr--  1 qiyas  dev  1024 Mar 10 10:00 script.sh
```

Bu sətrin əvvəlindəki `-rwxr-xr--` hissəsi icazə kodudur. Belə oxunur:

```
- rwx r-x r--
│ │││ │││ │││
│ │││ │││ └── other: oxuya bilər, yaza bilməz, icra edə bilməz
│ │││ └────── group: oxuya bilər, yaza bilməz, icra edə bilər
│ └────────── user: oxuya bilər, yaza bilər, icra edə bilər
└──────────── fayl tipi (- = fayl, d = qovluq)
```

**Rəqəmsal sistem:**

Hər icazənin rəqəm qarşılığı var:

| İcazə | Rəqəm |
|-------|-------|
| r     | 4     |
| w     | 2     |
| x     | 1     |
| yox   | 0     |

Üçlüyü toplayırsan:

- `rwx` = 4+2+1 = **7**
- `r-x` = 4+0+1 = **5**
- `r--` = 4+0+0 = **4**
- `---` = 0+0+0 = **0**

Yəni `chmod 754` deməkdir:
- User: 7 → rwx (hər şey)
- Group: 5 → r-x (oxu + icra)
- Other: 4 → r-- (yalnız oxu)

**İcazə dəyiş:**

```bash
chmod 755 script.sh       # Rəqəmsal üsul
chmod +x script.sh        # Hər kəsə icra icazəsi əlavə et
chmod u+w fayl.txt        # Yalnız sahibə yazma icazəsi əlavə et
chmod o-r fayl.txt        # Başqalarından oxuma icazəsini al
```

**Sahibi dəyiş:**

```bash
sudo chown mecgec fayl.txt             # Sahibi dəyiş
sudo chown mecgec:cc_group fayl.txt    # Sahibi və qrupu dəyiş
sudo chown -R mecgec /var/www/site/    # Qovluğu içindəkilərlə dəyiş
```

**Ən çox istifadə olunan icazə dəyərləri:**

| Dəyər | Nə deməkdir | Nə üçün |
|-------|-------------|---------|
| 755 | Sahibi hər şey, qalanlar oxu+icra | Qovluqlar, skriptlər |
| 644 | Sahibi oxu+yaz, qalanlar oxu | Konfiqurasiya faylları |
| 600 | Yalnız sahibi oxu+yaz | Şifrəli açarlar (.pem, .env) |
| 777 | Hamı hər şey | Demək olar ki, heç vaxt istifadə edilməz |

---

### Servera qurulum

Ubuntu serverə proqram qurmaq üçün **APT** paket meneceri istifadə olunur.

**Paket siyahısını yenilə:**

```bash
sudo apt update
```

Bu əmr proqramların mövcud versiyalarını internet üzərindən yeniləyir. Qurulum etmir, yalnız siyahını güncəlləyir.

**Proqram qur:**

```bash
sudo apt install nginx
sudo apt install python3
sudo apt install git
```

Birdən çox proqramı eyni anda qura bilərsən:

```bash
sudo apt install nginx git curl wget unzip
```

**Proqramı sil:**

```bash
sudo apt remove nginx
sudo apt purge nginx       # Konfiqurasiya fayllarını da sil
```

**Qurulmuş proqramları yenilə:**

```bash
sudo apt upgrade
```

**Proqramın qurulu olub-olmadığını yoxla:**

```bash
which python3
python3 --version
nginx -v
```

---

### Python və virtual environment (venv)

Serverdə Python ilə işləyəndə **mütləq** virtual environment istifadə olunmalıdır. Bu qaydanı bir dəfə anla, həmişə tətbiq et.

**Nə üçün lazımdır?**

Serverdə fərqli layihələr var. Layihə A `requests` kitabxanasının 2.26 versiyasını istəyir. Layihə B isə 2.31 istəyir. İkisi eyni sistemi paylaşırsa, biri digərini pozar.

Virtual environment hər layihəyə öz ayrıca "kitabxana çantası" verir. Biri digərindən xəbərsizdir.

**Virtual environment yarat:**

```bash
cd /var/www/nahibe_project
python3 -m venv venv
```

Bu, layihənin içinə `venv/` adlı qovluq yaradır.

**Aktivləşdir:**

```bash
source venv/bin/activate
```

Aktivləşdikdən sonra terminal belə görünür:

```
(venv) qiyas@server:/var/www/nahibe_project$
```

Ön tərəfdəki `(venv)` aktiv olduğunu göstərir. İndi `pip install` ilə qurulan hər şey yalnız bu layihəyə aiddir.

**Kitabxana qur:**

```bash
pip install django
pip install -r requirements.txt
```

**Deaktivləşdir:**

```bash
deactivate
```

**`requirements.txt` nədir?**

Layihənin asılılıqlarını sadalayan fayldır. Başqa serverə köçürdükdə:

```bash
pip freeze > requirements.txt    # Mövcud kitabxanaları yaz
pip install -r requirements.txt  # Yeni serverdə qur
```

---

### SSH ilə servera bağlanmaq

Serverin qarşısında oturmusunsa ekrana baxırsan. Amma demək olar ki, heç vaxt belə olmur. Serverə uzaqdan bağlanmaq üçün **SSH** istifadə olunur.

```bash
ssh qiyas@192.168.1.100
```

Şifrəni soruşacaq, girəcəksən.

**SSH açarı ilə giriş (şifrəsiz):**

Şifrə yazmaqdan yorulmamaq üçün açar cütü istifadə olunur.

Öz kompütərindən:

```bash
ssh-keygen -t ed25519 -C "qiyas@mecgec_computer"
```

Bu iki fayl yaradır:
- `~/.ssh/id_ed25519` — gizli açar (heç vaxt paylaşma)
- `~/.ssh/id_ed25519.pub` — ictimai açar (servera qoyulacaq)

İctimai açarı serverə göndər:

```bash
ssh-copy-id qiyas@192.168.1.100
```

Bundan sonra şifrəsiz bağlanacaqsan.

---

### Servisleri idarə etmək (systemctl)

Ubuntu-da proqramlar servis (xidmət) kimi işləyir. Nginx, PostgreSQL, Django app — hamısı arxa planda servis kimi çalışır.

```bash
sudo systemctl start nginx       # Başlat
sudo systemctl stop nginx        # Dayandır
sudo systemctl restart nginx     # Yenidən başlat
sudo systemctl reload nginx      # Konfiqurasiyani yenilə (dayandırmadan)
sudo systemctl status nginx      # Halını göstər
sudo systemctl enable nginx      # Server açıldığında avtomatik başlat
sudo systemctl disable nginx     # Avtomatik başlatmanı söndür
```

Bir problemi araşdıranda:

```bash
sudo journalctl -u nginx -f      # Nginx loglarını canlı izlə
sudo journalctl -u nginx --since "1 hour ago"
```

---

### Faylların yerləşdiyi standart qovluqlar

Ubuntu-da hər şeyin yeri var:

| Qovluq | Nə üçün |
|--------|---------|
| `/home/user/` | İstifadəçinin ev qovluğu |
| `/etc/` | Konfiqurasiya faylları |
| `/var/www/` | Web layihələri (Nginx default) |
| `/var/log/` | Log faylları |
| `/tmp/` | Müvəqqəti fayllar |
| `/usr/bin/` | Qurulmuş proqramlar |
| `/opt/` | Üçüncü tərəf proqramlar |

---

### .env faylı və gizli məlumatlar

Layihənin içindəki şifrələri, API açarlarını heç vaxt birbaşa koda yazma. Bunlar `.env` faylında saxlanır:

```
DATABASE_URL=postgresql://user:şifrə@localhost/db
SECRET_KEY=çox_gizli_açar
DEBUG=False
```

Bu faylın icazəsi mütləq məhdudlaşdırılmalıdır:

```bash
chmod 600 .env
```

Yalnız sahibi oxuya bilər. Başqa heç kim.

`.gitignore` faylına da əlavə et ki, git-ə yüklənməsin:

```
.env
venv/
__pycache__/
```

---

## Qısa yekun

Server mürəkkəb görünür, amma əslində tanış anlayışlardan ibarətdir. Kompüterdir, əməliyyat sistemi var, fayllar var, istifadəçilər var, icazələr var. Fərq yalnız ekranın olmaması və terminalla danışmaqdır.

Öyrənilən hər yeni komut bir alətdir. Zamanla bunları istifadə etdikcə əzbərləyəcəksən, çünki əllər özü öyrənir — oxuyaraq deyil.

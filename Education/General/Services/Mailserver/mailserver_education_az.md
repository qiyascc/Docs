# Mail Server

---

## Mail server nədir?

Mail server bir poçt şöbəsidir. Adi poçt şöbəsini düşün — sən bir məktub yazırsan, üstünə ünvan yazırsan, şöbəyə verirsən. Şöbə baxır ki, bu məktub hara gedir, onu oraya göndərir. Alıcı tərəfdə başqa bir şöbə var, oraya gəlir, saxlanır, adam gəlib götürür.

Mail server da tam belədir. Sadəcə məktub əvəzinə elektron poçt var, poçt şöbəsi əvəzinə server var.

Texniki tərifi belədir: mail server elektron poçtların göndərilməsini, qəbul edilməsini, yönləndirilməsini və saxlanmasını idarə edən proqram (və ya proqramlar toplusu) ilə işləyən serverdir.

---

## Mail server necə işləyir?

Bir e-mail göndərdiyin anda arxada bir neçə şey baş verir. Bunları anlamaq üçün üç protokolu bilmək lazımdır: **SMTP**, **IMAP**, **POP3**.

Protokol nədir? İki tərəfin bir-biri ilə danışmaq üçün razılaşdığı qayda toplusudur. Məsələn sən turka danışırsan, o da sənə türkcə cavab verir — bu bir "protokol"dur, ortaq dil. E-mail protokolları da belədir: göndərən server, alan server, e-mail proqramı — hamısı eyni qaydalar əsasında danışır.

---

### SMTP — göndərən

**SMTP** = Simple Mail Transfer Protocol.

Poçt anologiyasına qayıdaq: SMTP poçtçudur. Sən məktubu ona verirsən, o aparır.

Sən "Göndər" düyməsini basanda e-mail proqramın (Gmail, Outlook, Thunderbird) SMTP serverinə bağlanır, özünü tanıdır, məktubu verir. SMTP serveri baxır: bu məktub hara gedir? DNS-dən alıcının domeninin MX record-una baxır (MX record = o domenin mail serverinin ünvanı), oraya bağlanır, məktubu təhvil verir.

Beləliklə, SMTP yalnız göndərmək üçündür. Almaq üçün deyil.

**SMTP portları:**

| Port | İzah |
|------|------|
| 25 | Server-server arası köhnə üsul, ISP-lər çox vaxt bağlayır |
| 587 | E-mail proqramından göndərmək üçün standart (STARTTLS) |
| 465 | SSL ilə şifrəli göndərmə |

---

### IMAP — almaq (sinxron)

**IMAP** = Internet Message Access Protocol.

Poçt qutusu serverdə qalır. Sən oraya baxırsan, oxuyursan, silirsən — amma məktublar hər zaman serverdir. Evdəki telefonundan da, işdəki kompüterindən də, planşetindən də eyni qutuya girəndə eyni məktubları görürsən. Birindən oxuduğun məktub digərindən də oxunmuş görünür. Sinxrondur.

Bu gün demək olar ki, hər kəs IMAP işlədir. Gmail, Outlook, bütün müasir poçt xidmətləri IMAP-a əsaslanır.

**IMAP portları:**

| Port | İzah |
|------|------|
| 143 | Şifrəsiz (istifadə edilmir) |
| 993 | TLS/SSL ilə şifrəli (standart) |

---

### POP3 — almaq (yükləyib sil)

**POP3** = Post Office Protocol version 3.

Köhnə üsuldur. Serverdəki məktubları yükləyir, sonra orada silir. Telefona yükləndi, bitdi. Başqa bir cihazdan baxanda artıq orada yoxdur.

Üstünlüyü: internet olmadan da oxuya bilirsən, çünki məktub artıq bilavasitə cihazındadır. Dezavantajı: çox cihazda işlətmək mümkün deyil, sinxronizasiya yoxdur.

Dövrümüzdə POP3-ü yalnız çox xüsusi hallarda istifadə edirlər.

**POP3 portları:**

| Port | İzah |
|------|------|
| 110 | Şifrəsiz |
| 995 | TLS/SSL ilə şifrəli (standart) |

---

### Bir mailin tam yolu

Qiyas `qiyas@qiyas.cc` adresindən `mecgec@gmail.com` adresinə məktub göndərir. Arxada nə olur?

```
1. Qiyas "Göndər" basır
        ↓
2. E-mail proqramı qiyas.cc-nin SMTP serverinə (port 587) bağlanır
        ↓
3. SMTP serveri DNS-ə soruşur: "gmail.com-un MX record-u nədir?"
        ↓
4. DNS cavab verir: "gmail-smtp-in.l.google.com"
        ↓
5. qiyas.cc SMTP serveri Gmail-in SMTP serverinə (port 25) bağlanır,
   məktubu təhvil verir
        ↓
6. Gmail SMTP serveri məktubu qəbul edir, mecgec-in qutusu saxlayır
        ↓
7. Mecgec telefonunda Gmail açır → IMAP (port 993) ilə serverə bağlanır,
   yeni məktubu görür
```

Sadə dillə: göndərən SMTP işlənir, alanın tərəfindən IMAP/POP3 işlənir.

---

## Socket mexanizması — HTTP ilə fərqi nədir?

Bu məqamda bir az texniki dərinliyə gedəcəyik. Çünki mail serverləri HTTP kimi işləmir — işləmə prinsipi fərqlidir.

### HTTP necə işləyir?

Normal veb sayta girəndə nə olur:

```
Sən: "Salam, /haqqında.html səhifəsini ver"
Server: "Buyur, bu faylın məzmunudur."
Bağlantı qırılır.
```

Bu **request-response** modelidir. Sən soruşursan, server cavab verir, bağlantı bağlanır. Serverə ehtiyacın olmayanda onunla heç bir əlaqən yoxdur.

### SMTP/IMAP necə işləyir?

Mail protokolları isə bir **TCP socket əlaqəsi** açır — bu əlaqə danışıq boyunca açıq qalır.

Poçt şöbəsi anologiyası ilə desək: HTTP elə bir şöbədir ki, sən bir kağız verib dərhal çıxırsan. Mail server isə elə bir şöbədir ki, içəri girəndən çıxana qədər bütün söhbət ardıcıl şəkildə gedir, geri dönüş olmadan:

```
[SMTP bağlantısının görünüşü]

Server: 220 qiyas.cc ESMTP ready
Sən:    EHLO mail.sender.com
Server: 250-qiyas.cc Hello
        250-SIZE 52428800
        250 STARTTLS
Sən:    MAIL FROM:<qiyas@qiyas.cc>
Server: 250 OK
Sən:    RCPT TO:<mecgec@gmail.com>
Server: 250 OK
Sən:    DATA
Server: 354 Start mail input, end with <CRLF>.<CRLF>
Sən:    [məktubun məzmunu]
        .
Server: 250 Message accepted
Sən:    QUIT
Server: 221 Bye
```

Bu mətn əsaslı bir protokoldur. Hər sətir bir komutdur, server rəqəmsal kodla cavab verir (220, 250, 354, 221...). HTTP-nin `GET /page HTTP/1.1` forması da beləcə mətn əsaslıdır — amma fərq ondadır ki, SMTP sessiyası bitənə qədər socket açıq qalır, aralıqda state saxlanır (kim göndərir, kim alır, məzmun nədir).

### Fərq nədir xülasəsi:

| | HTTP | SMTP/IMAP |
|---|---|---|
| Bağlantı | Hər request üçün qısa | Sessiya boyunca açıq |
| Model | Soruşursan → alırsan | Dialoq əsaslı (state var) |
| Protokol | Request/Response | Komut/Cavab sessiyası |
| Port | 80 / 443 | 25, 587, 465 / 143, 993 |
| Yön | Client serverdən çəkir | Server clientə push edə bilər (IMAP IDLE) |

Bir maraqlı detal: IMAP-da **IDLE** komandu var. Bununla e-mail proqramın serverə deyir ki, "mən buradayam, yeni məktub gələndə mənə xəbər ver." Server yeni məktub gəlincə əlaqə açıq qaldığı üçün dərhal bildiriş göndərir. Bu, real-time inbox bildirişlərinin arxasındakı mexanizmdir.

---

## Açıq mənbəli mail serverlər (self-hosted)

Öz serverinda mail server qura bilərsən. Tam nəzarət səndədir: məlumatlar səndə qalır, istədiyin qaydanı qoyursan, heç bir üçüncü tərəfə etibar etmirsən.

Amma bir şeyi qabaqcadan bil: mail server qurmaq texniki cəhətdən çətin deyil, amma **etibarlı tutmaq** çətindir. Spam reputasiyası, SPF/DKIM/DMARC qurulması, IP bloklanmaması — bunlar ciddi iş tələb edir. Kiçik layihə üçün adətən hazır servisdən istifadə etmək daha ağlabatandır.

Buna baxmayaraq variantlar bunlardır:

---

### Tam paket (hər şey bir arada)

Bu paketlər yalnız SMTP deyil, IMAP, webmail, spam filter, antivirus, admin paneli — hamısını birlikdə qurur.

| Server | Xülasə | Texnologiya |
|--------|---------|-------------|
| **Mailcow** | Ən populyar Docker-əsaslı tam paket. Postfix + Dovecot + SOGo + SpamAssassin. Web UI gözəldir. | Docker |
| **Mail-in-a-Box** | Ən sadə başlanğıc. Bir əmrlə qurulur, az texniki bilik tələb edir. | Ubuntu |
| **iRedMail** | Bir klikdə qurulan klassik seçim. ClamAV + Roundcube webmail daxildir. | Linux (Ubuntu/Debian/CentOS) |
| **Modoboa** | Python/Django ilə yazılıb, gözəl web paneli var. Postfix + Dovecot ilə inteqrasiya. | Python/Django |
| **Stalwart** | Müasir, Rust ilə yazılmış, SMTP+IMAP+JMAP dəstəyi. Sürətli, yüngül. | Rust |
| **Mox** | Yeni nəsil, tək fayl, özü TLS idarə edir. Az texniki narahatlıq. | Go |

---

### Komponent əsaslı (özün yığırsan)

Daha çox nəzarət istəyirsənsə, ayrı-ayrı alətləri birləşdirirsən:

| Alət | Nə edir |
|------|---------|
| **Postfix** | Dünyanın ən çox istifadə edilən MTA-sı (Mail Transfer Agent). Məktubları göndərir/yönləndirir. |
| **Dovecot** | Ən populyar IMAP/POP3 serveri. Postfix ilə birlikdə işlənir. |
| **SpamAssassin** | Spam filteri. Gələn məktubları analiz edib spam qiymətləndirməsi verir. |
| **ClamAV** | Antivirus. Məktub əkləri taranır. |
| **Roundcube** | Açıq mənbəli webmail interfeysi. Browserdan oxumaq üçün. |
| **PostfixAdmin** | Postfix üçün veb-əsaslı admin paneli. Domain, mailbox, alias idarəsi. |

Klassik kombinasiya: **Postfix + Dovecot + SpamAssassin + Roundcube**.

---

### Test üçün

Proqramlaşdırma zamanı real mail göndərmədən test etmək üçün:

| Alət | Nə edir |
|------|---------|
| **Mailhog** | Lokal saxta SMTP serveri. Göndərdiyin bütün mailləri tutur, brauzerdan izlə bilərsən. Real heç yerə getmir. |
| **smtp4dev** | Oxşar — Windows/Linux/Mac üçün fake SMTP. |
| **Mailtrap** | Onlayn versiya. Development mühitindəki məktubları "tutur", inbox-a getmir. |

---

## Xarici (3rd party) mail serverlar

Özün qurmaq istəmirsənsə, başqasının serverini işlədirsən. Ən tanınan nümunələr:

### Gmail (Google Workspace)
`@gmail.com` ünvanın var isə, Google-un serverləri sənin məktublarını idarə edir. Google Workspace ilə korporativ `@şirkətin.com` ünvanı da qura bilərsən. Hər şey onların infrastrukturundadır — sən yalnız girişi idarə edirsən.

### GoDaddy Mail
Domain qeydiyyatı ilə birlikdə mail hosting satırlar. Domenini GoDaddy-dən alıbsa, onların mail xidmətinə qoşulmaq asan olur.

### Microsoft 365 (Outlook/Exchange)
Korporativ mühitlər üçün standart. Exchange Server əsasında işləyir, Active Directory ilə inteqrasiya güclüdür.

### Zoho Mail
Pulsuz planı olan korporativ mail servisi. Kiçik şirkətlər üçün məşhur seçimdir.

---

**Xarici servislər necə işləyir?**

Prinsip eynidir — SMTP, IMAP, DNS MX record. Amma fərq ondadır ki, infrastrukturun idarəsi sənin deyil. Sən domenivin DNS-ə MX record yazırsan: "bu domenə gələn mailləri `mail.google.com`-a göndər." Google/Microsoft/GoDaddy o məktubları qəbul edir, saxlayır, sənin adına idarə edir.

```
Məktub gəldi → DNS-ə bax → MX record nə yazıb? → Ora göndər
```

---

## Transaksion mail API-lar (SendGrid, Mailgun, Postmark...)

İndi fərqli bir kateqoriyaya keçirik. Bunlar nə mail server qurmaqdır, nə Gmail kimi şəxsi poçtdur. Bunlar **sənin tətbiqinin adına mail göndərən xidmətlərdir**.

### Nə üçün lazımdır?

Bir sayt düşün. İstifadəçi qeydiyyat keçir → "Xoş gəldin" maili gəlir. Şifrəni unutdu → "Şifrəni sıfırla" linki gəlir. Sifariş verdi → "Sifarişin qəbul edildi" maili gəlir.

Bu mailləri kim göndərir? Sən özün mail server qursaydın, IP reputasiyasını idarə etməli, spam siyahılarından uzaq durmalı, SPF/DKIM/DMARC qurmaq, serveri 24/7 ayaq üstə saxlamaq lazım gələcəkdi. Bütün bu məsuliyyət əvəzinə SendGrid, Mailgun kimiləri deyir ki: "Sen sadece API-ı çağır, biz göndərərik."

### Necə işləyir?

```python
import requests

requests.post(
    "https://api.sendgrid.com/v3/mail/send",
    headers={"Authorization": "Bearer SG.xxxx"},
    json={
        "to": [{"email": "mecgec@gmail.com"}],
        "from": {"email": "noreply@qiyas.cc"},
        "subject": "Xoş gəldin!",
        "content": [{"type": "text/plain", "value": "Hesabın yaradıldı."}]
    }
)
```

Bir HTTP POST sorğusu. Bunun arxasında nə var?

1. Sənin sorğun SendGrid-in serverinə gedir
2. SendGrid öz SMTP infrastrukturundan məktubu göndərir
3. Onların IP-ləri artıq reputasiyalıdır, spam filter keçir
4. Sənə göndərilib-göndərilmədiyini, açılıb-açılmadığını webhook ilə bildirir

SMTP üzərindən də işlətmək molar — bu halda sən e-mail proqramı kimi SMTP bağlantısı açırsan, amma server sənin server deyil, SendGrid-in serveridir.

---

### Əsas xidmətlər

| Xidmət | Xülasə | Qiymət |
|--------|---------|--------|
| **SendGrid** | Ən köhnə və ən böyük. Həm transaksion, həm marketing. Twilio tərəfindən alınıb. | Günlük 100 email pulsuz |
| **Mailgun** | Developer-first. REST API güclüdür, e-mail validation xüsusiyyəti var. Sinch tərəfindən alınıb. | Gündə 100 email pulsuz |
| **Postmark** | Yalnız transaksion email üçün. Deliverability ən yüksəkdir, 45 günlük log saxlayır. | 100 email/ay pulsuz, sonra $15/10k |
| **Amazon SES** | Ən ucuz. AWS-in xidmətidir. Qurulması mürəkkəbdir amma texniki bilikli komandalara ideal. | 1000 email = $0.10 |
| **Brevo (əvvəlki Sendinblue)** | Həm transaksion, həm marketing. UI sadədir. | Aylıq 300 email pulsuz |
| **Resend** | Ən yeni nəsil, developer təcrübəsinə diqqət edib. React Email ilə template yazmaq mümkündür. | Aylıq 3000 email pulsuz |
| **MailerSend** | Sərfəli qiymət, sadə UI, kiçik komandalara uyğun. | Aylıq 3000 email pulsuz |

---

### Hansını seçmək lazımdır?

**Başlanğıc layihə / şəxsi tətbiq** → Resend və ya Brevo. Pulsuz limitin kifayət edir, qurulması asandır.

**Django/Python tətbiqi, az həcm** → Mailgun. API-ı sadədir, Django ilə inteqrasiyası yaxşıdır.

**Kritik transaksion maillər (şifrə sıfırlama, ödəniş bildirişi)** → Postmark. Deliverability ən etibarlıdır.

**Çox yüksək həcm, AWS infrastrukturu var** → Amazon SES. Qiymət/keyfiyyət nisbəti qazanan.

**Həm marketing, həm transaksion eyni yerdə** → SendGrid. Hər şeyi bir platformada idarə etmək istəyəndə.

---

### Django-da istifadə nümunəsi (Mailgun)

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'postmaster@mg.qiyas.cc'
EMAIL_HOST_PASSWORD = 'key-xxxxxxxx'
DEFAULT_FROM_EMAIL = 'noreply@qiyas.cc'
```

```python
# views.py
from django.core.mail import send_mail

send_mail(
    subject='Xoş gəldin!',
    message='Hesabın uğurla yaradıldı.',
    from_email='noreply@qiyas.cc',
    recipient_list=['mecgec@gmail.com'],
)
```

Bu qədər. Django öz SMTP backend-i üzərindən Mailgun-a bağlanır, Mailgun göndərir.

---

## SPF, DKIM, DMARC — üç vacib DNS ayarı

İstər öz serverini qurasan, istər SendGrid işlədəsən — bu üç DNS ayarı olmadan maillərin spam qutusuna düşəcək.

**SPF** (Sender Policy Framework): "Mənim domenimin adından yalnız bu IP-lər mail göndərə bilər" deyirsən. Mailsever baxır: bu IP-dən gələn mail, bu domenin adına iddia edir — SPF record-a uy mu?

**DKIM** (DomainKeys Identified Mail): Göndərən server məktuba rəqəmsal imza vurur. Alıcı server DNS-dən açıq açarı çəkib imzanı yoxlayır. Məktub yolda dəyişdirilib-dəyişdirilməyib anlayır.

**DMARC** (Domain-based Message Authentication): SPF və ya DKIM uğursuz olsa nə etsin? Quarantine? Reject? Bunun siyasətini özün müəyyən edirsən.

Bu üçü DNS TXT record-ları ilə qurulur. SendGrid, Mailgun kimilər qeydiyyat zamanı bunu necə quracağını addım-addım göstərir.

---

## Qısa yekun

Mail server mövzusuna baxanda ilk baxışda mürəkkəb görünür: SMTP, IMAP, POP3, SPF, DKIM... Amma prinsipdə çox sadədir.

Bir məktub göndərmək üçün: SMTP bir tərəfdə, MX record bir tərəfdə, alıcı tərəfdə IMAP.

Öz serverini qurasan ya hazır xidmət istifadə edəsən — seçim yükün nə qədər olduğuna, texniki resursuna, məlumatların harada saxlanmasına bağlıdır.

Tətbiq yazırsan və o tətbiqin istifadəçilərinə mail göndərəcəksən — Mailgun, Resend, Brevo kimi xidmətlərdən birini seç, API-ını inteqrasiya et, DNS ayarlarını qur, işinə bax.

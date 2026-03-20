# PHP `mail()` funksiyası

---

## Ümumi mənzərə

SendGrid, Mailgun, SMTP bağlantısı — bunların heç biri yoxdur. Sən sadəcə PHP kodunun içinə bir sətir yazırsan:

```php
mail('mecgec@gmail.com', 'Salam', 'Bu bir test məktubudur.');
```

Məktub gedir.

Bu necə mümkündür? PHP haraya bağlandı? Hansı server göndərdi? Şifrə soruşmadı, port yazmadın, heç nə olmadı — necə getdi?

Cavab serverinin özündədir.

---

## `mail()` niyə ayrıca bir mail servisinə ehtiyac duymur?

PHP `mail()` funksiyası birbaşa **serverın öz mail transfer agentinə (MTA)** müraciət edir.

MTA nədir? Xatırla — mailserver sənədlərindən. MTA məktubu göndərən proqramdır. Postfix, Sendmail, Exim — bunlar MTA-lardır. Linux serverlərinin əksəriyyətində bunlardan biri qurulmuşdur, arxa planda sakitcə işləyir.

PHP `mail()` çağıranda arxada belə bir şey baş verir:

```
PHP kodu
    ↓
php.ini-dəki "sendmail_path" parametrinə bax
    ↓
Adətən: /usr/sbin/sendmail -t -i
    ↓
Sendmail/Postfix məktubu götürür
    ↓
Serverın öz SMTP prosesi üzərindən göndərir
```

Yəni PHP özü heç bir şey göndərmir. O, serverın içindəki bir proqrama ötürür, o proqram göndərir. PHP sadəcə bir "aracı"dır.

Poçt anologiyası: sən məktubu yazırsan, qonşunun qutusuna atırsan. Qonşun hər gün bütün məktubları götürüb poçtxanaya aparır. Sən poçtxanaya getmirsən, şifrə vermirsən. Amma məktub yenə də gedir.

---

## Serverda nə lazımdır?

`mail()` işləsin deyə serverdə iki şey olmalıdır:

**1. MTA qurulmuş olmalıdır**

Ən çox istifadə edilən: **Postfix** və ya **Sendmail**.

Ubuntu serverdə yoxlamaq:

```bash
which sendmail
# /usr/sbin/sendmail

postfix status
# postfix/postfix-script: the Postfix mail system is running
```

Qurulmayıbsa:

```bash
sudo apt install postfix
# Qurulum zamanı "Internet Site" seç
# System mail name: serverin domain adını yaz (məs. qiyas.cc)
```

**2. `php.ini`-də `sendmail_path` düzgün yazılmış olmalıdır**

```ini
; /etc/php/8.x/cli/php.ini və ya /etc/php/8.x/apache2/php.ini

sendmail_path = /usr/sbin/sendmail -t -i
```

Bu standart qurulumda artıq belədir. Əksər hallarda dəyişdirməyə ehtiyac olmur.

Yoxlamaq üçün:

```bash
php -i | grep sendmail
# sendmail_path => /usr/sbin/sendmail -t -i
```

---

## Funksiya imzası

```php
mail(
    string $to,
    string $subject,
    string $message,
    array|string $additional_headers = [],
    string $additional_params = ''
): bool
```

| Parametr | Nə edir |
|----------|---------|
| `$to` | Alıcının e-mail ünvanı |
| `$subject` | Məktubun mövzusu |
| `$message` | Məktubun məzmunu |
| `$additional_headers` | Əlavə başlıqlar: From, CC, BCC, Content-Type və s. |
| `$additional_params` | Sendmail-ə əlavə komut parametrləri |

Geri qaytardığı dəyər `bool`dur: `true` göndərildi (MTA-ya çatdı), `false` göndərilmədi.

Diqqət: `true` məktubun çatdığını deyil, MTA-ya ötürüldüyünü bildirir. MTA sonradan xəta verə bilər — PHP bunu bilmir.

---

## Sadə nümunə

```php
<?php

$to      = 'mecgec@gmail.com';
$subject = 'Xoş gəldin!';
$message = 'Hesabın uğurla yaradıldı. Platformamıza xoş gəldin.';

$result = mail($to, $subject, $message);

if ($result) {
    echo 'Məktub göndərildi.';
} else {
    echo 'Göndərmə zamanı xəta baş verdi.';
}
```

---

## Header-lar ilə düzgün istifadə

Yuxarıdakı nümunədə `From` başlığı yoxdur. Bu problem yaradır — bəzi mail serverlər kimliyi bilinməyən məktubları red edir və ya spam qutusuna salır. Həmişə `From` başlığını əlavə et:

```php
<?php

$to      = 'mecgec@gmail.com';
$subject = 'Hesab doğrulaması';
$message = 'Doğrulama kodunuz: 482910';

$headers = [
    'From'         => 'noreply@qiyas.cc',
    'Reply-To'     => 'support@qiyas.cc',
    'Content-Type' => 'text/plain; charset=UTF-8',
    'X-Mailer'     => 'PHP/' . phpversion(),
];

mail($to, $subject, $message, $headers);
```

`$headers` massiv kimi verəndə PHP 7.2+ avtomatik formatlar. Köhnə PHP versiyalarında string kimi yazılırdı:

```php
// Köhnə üsul (hələ də işləyir)
$headers  = "From: noreply@qiyas.cc\r\n";
$headers .= "Reply-To: support@qiyas.cc\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
```

Başlıqlar arasında mütləq `\r\n` istifadə et — `\n` bəzi mail serverlərində problem yaradır. Bu SMTP protokolunun tələbidir.

---

## HTML mail göndərmək

Düz mətn əvəzinə HTML göndərmək üçün `Content-Type`-ı dəyiş:

```php
<?php

$to      = 'mecgec@gmail.com';
$subject = 'Xoş gəldin!';

$message = '
<!DOCTYPE html>
<html>
<body>
    <h2>Hesabın yaradıldı</h2>
    <p>Salam, <strong>Mecgec</strong>!</p>
    <p>Platformamıza xoş gəldin.</p>
    <a href="https://qiyas.cc/dashboard">Panelə keç</a>
</body>
</html>
';

$headers = [
    'From'         => 'noreply@qiyas.cc',
    'Content-Type' => 'text/html; charset=UTF-8',
    'MIME-Version' => '1.0',
];

mail($to, $subject, $message, $headers);
```

Bir vacib qeyd: HTML mail göndərəndə **həm HTML, həm plain text versiyasını** birlikdə göndərmək doğrudur. Bunu `multipart/alternative` content type ilə edirlər. Bu `mail()` ilə çətin olduğundan bunu PHPMailer kimi kitabxanalar asan edir — amma prinsipi anlamaq üçün `mail()` mükəmməldir.

---

## CC və BCC

```php
<?php

$headers = [
    'From'    => 'noreply@qiyas.cc',
    'CC'      => 'qiyas@qiyas.cc',
    'BCC'     => 'archive@qiyas.cc',
];

mail('mecgec@gmail.com', 'Mövzu', 'Məzmun', $headers);
```

CC — alıcı görür, digər alıcılar da görür ki, CC var.
BCC — alıcı görmür. Gizli nüsxə. Arxivləmə, izləmə üçün istifadə olunur.

---

## Çox alıcıya göndərmək

```php
<?php

$recipients = [
    'mecgec@gmail.com',
    'nahibe@gmail.com',
    'test@qiyas.cc',
];

$to = implode(', ', $recipients);

mail($to, 'Bildiriş', 'Sistem yeniləndi.', ['From' => 'noreply@qiyas.cc']);
```

Amma dikkat: çox sayda alıcıya belə göndərmək ideal deyil. Biri bounce edəndə hamısı pozulur. Çox alıcı varsa, loop ilə ayrı-ayrı göndər:

```php
foreach ($recipients as $recipient) {
    mail($recipient, 'Bildiriş', 'Sistem yeniləndi.', ['From' => 'noreply@qiyas.cc']);
}
```

---

## `mail()` nə vaxt işləmir?

`mail()` bütün mühitlərdə işləmir. Bilmək lazımdır:

**Shared hosting:** Bəzən host provider `mail()`-i söndürür və ya limit qoyur. Niyə? Spam göndərənlər uzun illər shared hostingdə `mail()` ilə milyonlarla spam göndərib. Bu yüzündən hostlar ehtiyatlıdır.

**Localhost (öz kompüterin):** Lokal kompüterdə MTA adətən olmur. `mail()` çağırsan, false qaytarır. Test üçün ya SMTP-yə keç (PHPMailer ilə), ya da Mailhog kimi fake SMTP istifadə et.

**Docker konteyner:** Konteynerin içi minimal olur, Postfix yoxdur. Mail göndərəcəksənsə ya Postfix qurmalısan, ya da SMTP relay istifadə etməlisən.

**VPS/dedicated server:** Postfix qurulubsa, düzgün konfiqurasiya edilibsə — işləyir.

---

## `mail()` vs PHPMailer vs SMTP

Üçü də PHP-dən mail göndərmək üçündür. Fərqləri nədir?

| | `mail()` | PHPMailer/Symfony Mailer | SMTP API (SendGrid...) |
|---|---|---|---|
| Qurulum | Heç nə | Composer paketi | API key + HTTP |
| SMTP bağlantısı | Hayır, MTA üzərindən | Bəli, istədiyin SMTP | Hayır, HTTP POST |
| HTML mail | Çətin | Asan | Asan |
| Attachment | Çətin | Asan | Asan |
| Deliverability | Aşağı (IP reputasiyası) | Orta-yüksək | Yüksək |
| Debug imkanı | Az | Yaxşı | Əla (dashboard, log) |
| İstifadə yeri | Sadə serverda sürətli həll | Öz serveran, daha çox nəzarət | Production tətbiqlər |

`mail()` kiçik, sadə hallar üçündür. Sən bir admin formu yazırsan, serverdə bir skript işləyir, ara-sıra bir bildiriş göndərmək lazımdır — `mail()` işlənir. Amma minlərlə istifadəçiyə mail göndərəcəksənsə, şifrə sıfırlama kimi kritik maillər varsa — PHPMailer + etibarlı SMTP relay seç.

---

## Xəta ayıklama

`mail()` false qaytarıbsa nə etmək lazımdır?

```php
// PHP 8.0+ üçün
ini_set('display_errors', 1);
error_reporting(E_ALL);

$result = mail($to, $subject, $message, $headers);

if (!$result) {
    error_log('mail() failed: ' . print_r(error_get_last(), true));
}
```

Mail log-larına bax:

```bash
# Postfix log-u
sudo tail -f /var/log/mail.log

# Sistem mail log-u
sudo tail -f /var/log/syslog | grep postfix
```

Ən çox rast gəlinən problem: **SPF/DKIM olmadığı üçün spam qutusuna düşür.** Serverin IP-sindən göndərilən məktubun spam olmadığını Gmail/Outlook kimi servislərin başa düşməsi üçün DNS ayarları mütləq lazımdır.

---

## Qısa yekun

`mail()` PHP-nin ən sadə mail göndərmə üsuludur. Sehrli deyil — arxada serverın MTA-sına ötürür, o göndərir. Serverdə Postfix (və ya Sendmail) qurulu olmalıdır, `php.ini`-də `sendmail_path` yazılı olmalıdır, bu qədər.

Sadə hallarda — işləyir, kifayətdir. Mürəkkəb hallarda — PHPMailer kimi kitabxana götür, özünə hörmət et.

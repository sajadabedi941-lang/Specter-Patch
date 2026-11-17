# دکمه‌های ساخت موشک J / L / M / N در کارخانهٔ موشکی

**Zero Hour اجرا نشد.** اعتبارسنجی ایستا ≠ تأیید داخل بازی.

## اشیاء زنده از Patch (حدس زده نشد)

از `_SPEC_DATA_ONE.big` ریلیز `cc-vt72b-nk-hwasong` + `CommandSet.ini` (ControlBar فقط همین فایل را می‌خواند):

| اسلات | دکمه | Object | قیمت | BuildTime |
| ---: | --- | --- | ---: | ---: |
| ۱۰ | `CB_*_MISSILE_J` / عراق `CB_MISSILE_J` | موشک J همان کشور | بدون تغییر | بدون تغییر |
| ۱۲ | `CB_FACTORY_SLOT_L` | `Factory_KhormsharOnce` | 20000 | 10s |
| ۱۳ | `CB_FACTORY_SLOT_M` | `Factory_RS24YarsOnce` | 27000 | 22s |
| ۱۴ | `CB_FACTORY_SLOT_N` | `Factory_DF41Once` | 30000 | 22s |

عراق اسلات ۱۱ را `CB_MISSILE_K` (`Iraq_Alhussaien`) نگه می‌دارد. کشورهای دیگر اسلات ۱۱ = `CB_FACTORY_SLOT_K` (همان Object، قیمت ۲۰۰۰۰). این PR اسلات K را عوض نکرد.

`CommandSet.ini` بایت‌به‌بایت همان #720 است (SHA `a23df0bc…`). دکمهٔ تکراری ساخته نشد.

## تصاویر

نام‌های درخواستی `Neon` / `Futuristic` / `Nuclear` به‌عنوان MappedImage یا TGA در Patch نبودند. تصویر جدید ساخته نشد.

| درخواست | ButtonImage نهایی | Texture واقعی | منبع قبلی |
| --- | --- | --- | --- |
| J → Neon | `Neon` | `specter_missile_j.tga` | PR #571 ART extract |
| L → Futuristic | `Futuristic` | `specter_missile_l.tga` | PR #571 ART extract |
| M → Nuclear | `Nuclear` | `specter_missile_m.tga` | از `specter_missile_m.png` ریلیز EGKM، همان روش TGA ۲۴بیت #571 |
| N → تصویر اختصاصی N | `pla_df41` | اطلس `Pla_Icons01.tga` | `HandCreatedMappedImages.INI` (نام واقعی Patch) |

MappedImageهای `Neon` / `Futuristic` / `Nuclear` در `zSpecterJLMN_Images.INI` به همان TGA موجود اشاره می‌کنند. Overlay `0_SPECTER_MissileJLMNCameos.big` مسیرهای `Art\Textures\specter_missile_{j,l,m}.tga` را first-win می‌کند (`0_` قبل از `_SPEC_ART_ONE.big`). `pla_df41` از قبل در ART اطلس است.

صف ساخت L/M: `SelectPortrait` / `ButtonImage` روی `Factory_KhormsharOnce` و `Factory_RS24YarsOnce` به همان MappedImageها. Object چین `Factory_DF41Once` همچنان `pla_df41`.

## جدول کشورها

کارخانهٔ همهٔ کشورهای غیرعراق: `Country_MissileFactoryCommandSet`. عراق: `Iraq_AlFahdMissileFactoryCommandSet`.

تصویر L/M/N برای همه یکسان است: Futuristic / Nuclear / pla_df41.

| کشور | کارخانه CommandSet | اسلات ۱۰ J | Object J |
| --- | --- | --- | --- |
| Iraq | Iraq_AlFahdMissileFactoryCommandSet | CB_MISSILE_J | Iraq_AlMansour |
| America | America_MissileFactoryCommandSet | CB_AMERICA_MISSILE_J | America_PK |
| Britain | Britain_MissileFactoryCommandSet | CB_BRITAIN_MISSILE_J | Britain_Trafalgar |
| China | China_MissileFactoryCommandSet | CB_CHINA_MISSILE_J | China_DF5B |
| France | France_MissileFactoryCommandSet | CB_FRANCE_MISSILE_J | France_Gaulle |
| Germany | Germany_MissileFactoryCommandSet | CB_GERMANY_MISSILE_J | Germany_Walkure |
| India | India_MissileFactoryCommandSet | CB_INDIA_MISSILE_J | India_Agni5 |
| Iran | Iran_MissileFactoryCommandSet | CB_IRAN_MISSILE_J | Iran_Simorgh |
| Israel | Israel_MissileFactoryCommandSet | CB_ISRAEL_MISSILE_J | Israel_Keren |
| Italy | Italy_MissileFactoryCommandSet | CB_ITALY_MISSILE_J | Italy_Roma |
| Japan | Japan_MissileFactoryCommandSet | CB_JAPAN_MISSILE_J | Japan_Tenrai |
| Libya | Libya_MissileFactoryCommandSet | CB_LIBYA_MISSILE_J | Libya_GreatManMadeRiver |
| NorthKorea | NorthKorea_MissileFactoryCommandSet | CB_NORTHKOREA_MISSILE_J | NorthKorea_Hwasong17 |
| Pakistan | Pakistan_MissileFactoryCommandSet | CB_PAKISTAN_MISSILE_J | Pakistan_Shaheen3 |
| Russia | Russia_MissileFactoryCommandSet | CB_RUSSIA_MISSILE_J | Russia_Voevoda |
| SaudiArabia | SaudiArabia_MissileFactoryCommandSet | CB_SAUDIARABIA_MISSILE_J | SaudiArabia_AlWad |
| SouthAfrica | SouthAfrica_MissileFactoryCommandSet | CB_SOUTHAFRICA_MISSILE_J | SouthAfrica_RSA3 |
| SouthKorea | SouthKorea_MissileFactoryCommandSet | CB_SOUTHKOREA_MISSILE_J | SouthKorea_Cheonwang |
| Spain | Spain_MissileFactoryCommandSet | CB_SPAIN_MISSILE_J | Spain_Iberia |
| Sweden | Sweden_MissileFactoryCommandSet | CB_SWEDEN_MISSILE_J | Sweden_Yggdrasil |
| Syria | Syria_MissileFactoryCommandSet | CB_SYRIA_MISSILE_J | Syria_Barada |
| Turkey | Turkey_MissileFactoryCommandSet | CB_TURKEY_MISSILE_J | Turkey_Gokturk |
| UAE | UAE_MissileFactoryCommandSet | CB_UAE_MISSILE_J | UAE_AlWatan |
| Ukraine | Ukraine_MissileFactoryCommandSet | CB_UKRAINE_MISSILE_J | Ukraine_Tryzub |
| Vietnam | Vietnam_MissileFactoryCommandSet | CB_VIETNAM_MISSILE_J | Vietnam_LacViet |

مصر و Arabic Alliance کارخانهٔ موشکی در DATA زنده ندارند.

فهرست A–I هر کشور و A–K عراق جابه‌جا نشد. CommandSet تولید عراق به کشور دیگر کپی نشد.

## خارج از محدوده

- Command Center ژاپن/ویتنام/کره (#720) — `Japan_CommandCenterCommandSet` همچنان فقط VT72B
- Overlay Global Store `0_SPECTER_GlobalStoreCameos.big` (#721)
- رادار، پهپاد، موشک‌های A–I، قیمت/زمان/یک‌کلیپ L/M/N
- جایگزینی `_SPEC_ART_ONE.big`

## فایل‌ها

| فایل | بایت | SHA-256 |
| --- | ---: | --- |
| `_SPEC_DATA_ONE.big` | 374075482 | `c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac` |
| `0_SPECTER_MissileJLMNCameos.big` | 147733 | `618c6dabb192b8033f074a005e5141af2a756182be746d71f2c2fdda125fbfae` |
| `CommandSet.ini` (بدون تغییر #720) | 450827 | `a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87` |
| `CommandButton.ini` | 1337374 | `60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba` |

## نصب

1. `_SPEC_DATA_ONE.big` را کنار `generals.exe` بگذارید.
2. `CommandSet.ini` را در `Data\INI\CommandSet.ini` بگذارید.
3. `CommandButton.ini` را در `Data\INI\CommandButton.ini` بگذارید (ControlBar این مسیر را first-win می‌کند).
4. `0_SPECTER_MissileJLMNCameos.big` را کنار `generals.exe` بگذارید. پیشوند `0_` بماند.
5. Overlay #721 (`0_SPECTER_GlobalStoreCameos.big`) را نگه دارید. ART ONE/TWO را عوض نکنید.

یا `Install_MissileJLMNButtons.bat`.

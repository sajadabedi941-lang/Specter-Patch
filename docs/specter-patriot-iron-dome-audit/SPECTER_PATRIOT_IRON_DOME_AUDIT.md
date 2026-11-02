# ممیزی فقط‌خواندنی SPECTER — سامانه‌های Patriot و Iron Dome

تاریخ تولید: **۲ نوامبر ۲۰۲۶، ۱۸:۰۶ به وقت ایران (Asia/Tehran)**  
مخزن: `sajadabedi941-lang/Specter-Patch`  
وضعیت: هیچ فایل بازی، DATA، ART، BIG، CommandSet یا تنظیماتی تغییر نکرد. Zero Hour اجرا نشد. آرشیو New donor و منابع خارجی استفاده نشد.

همراه این گزارش: `SPECTER_PATRIOT_IRON_DOME_AUDIT.xlsx` (۱۳ برگه با کاتالوگ Object، سلاح، UI، ART، CSF، کلون و مسیر+BIG).

---

## نتیجه نهایی

| سامانه | نتیجه | آیا همین حالا به‌صورت authentic قابل ساخت و استفاده است؟ |
|---|---|---|
| **Patriot** | **موجود ولی ناقص** | خیر. واحد overlay به نام Patriot قابل ساخت است ولی Patriot واقعی نیست. سایت packed MIM-104F/PAC-3 از بولدوزر آمریکا ساخته می‌شود و به خانواده Patriot نزدیک‌تر است، اما رادار AN/MPQ ندارد. |
| **Iron Dome** | **موجود ولی ناقص** | خیر. واحد overlay به نام Iron Dome قابل ساخت است ولی هنر و سلاح Pantsir است. سایت packed با مدل اختصاصی `Isr_Ironedome_l` از بولدوزر AirF ساخته می‌شود و سلاح ABM دارد، اما رادار EL/M-2084 و نام Tamir ندارد. |

هیچ‌کدام **کاملاً غایب** نیستند (Object و مسیر تولید وجود دارد). هیچ‌کدام **موجود و عملیاتی** به‌معنای سامانه کامل (پرتابگر + رادار اختصاصی + رهگیری معتبر) نیستند.

---

## محدوده، روش و last-wins

لایه‌های فعال فعلی SPECTER که بررسی شد:

| ترتیب تقریبی بارگذاری ZH (الفبایی `*.big`، later same-path wins؛ loose `Data/` بر همه BIG) | لایه | منبع در این مخزن | فایل‌ها |
|---|---|---|---|
| زود | `INIZH.big` استوک ZH | **در این مخزن نیست** | CommandSet/Button/MappedImages استوک؛ cameo `SAPatriot` ممکن است فقط اینجا باشد |
| سپس | `_SPEC_ART_ONE.big` | `art_data.part01–22.rar` تاریخ ۲۰۲۶-۰۸-۱۸ | ۲۷۸۷ فایل، ۵۲۴٬۸۰۰٬۹۵۵ بایت، SHA-256 `bb5d15325e227bad247450dc379bbf85b8bbd620beacc9b2f8db89976b1989d7` |
| سپس | `_SPEC_DATA_ONE.big` | همان RAR، ۲۰۲۶-۰۸-۱۸ (جفت فعلی ART) | ۲۵۳۹ فایل، ۳۶۱٬۶۹۵٬۳۴۰ بایت، SHA-256 `c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05` |
| بعدتر اگر کپی شود | `_SPECTER_PATCH_FINAL.big` | `patch/Release/SPECTER_PATCH_FINAL/` | ۱۴۸۱ فایل؛ شامل `America_AD_Patriot.ini` و UI فاز G/F+ |
| آخر | overlay loose `Data/` | `patch/Data/` | اگر installer کپی کند بر BIG پیروز می‌شود |

`Launch_Specter.bat` فقط `_SPEC_DATA_ONE.big` و `_SPEC_ART_ONE.big` را کنار `generals.exe` می‌گذارد؛ overlay و patch BIG را کپی نمی‌کند.

نسخه zip قدیمی‌تر `_SPEC_DATA_ONE.zip` (۲۰۲۶-۰۷-۲۱، ۳۴۹٬۳۴۸٬۳۰۷ بایت) به‌عنوان DATA فعلی استفاده نشد؛ جفت ART+DATA داخل `art_data` جدیدتر است.

ControlBar اسپکتر فقط اسلات‌های **۱–۱۴** را نشان می‌دهد. اسلات ۱۵+ در INI هست و در UI نیست.

نام‌های جستجو شده علاوه بر Patriot / Iron Dome: `PAC-3`, `PAC3`, `MIM-104`, `MIM104F`, `Tamir`, `AN/MPQ`, `EL/M-2084`, `David's Sling`, `IroneDome`. صرف شباهت نام معادل سامانه اعلام نشد.

---

# گزارش Patriot

## ۱. آیا سامانه در بازی وجود دارد؟ Object و نام نمایشی

**بله، چند تعریف جدا وجود دارد. هیچ‌کدام یک باتری کامل Patriot با رادار AN/MPQ نیستند.**

### A) واحد overlay — زنده اگر overlay یا patch BIG نصب باشد

| فیلد | مقدار | مسیر / BIG |
|---|---|---|
| Object | `America_AD_Patriot` | `patch/Data/INI/Object/Specter/PatchSystems/AirDefense/America_AD_Patriot.ini` (last-wins overlay). همان مسیر در `_SPECTER_PATCH_FINAL.big`. **در `_SPEC_DATA_ONE.big` نیست.** |
| DisplayName key | `OBJECT:America_AD_Patriot` | INI خط ۱۱۴ |
| متن TXT | `America Patriot` (کلید تکراری آخر در `FactionExpansion_PhaseG_Strings.txt` بر `America AD Patriot` می‌برد) | `patch/Data/English/FactionExpansion_PhaseG_Strings.txt` |
| متن generals.csf | **کلید موجود نیست** | overlay CSF ۸۰۳۷ کلید؛ packed DATA CSF ۸۱۵۱ کلید |
| Side | `America` | همان INI |
| EditorSorting | `VEHICLE` | TEL متحرک، نه سایت ثابت |

بدون CSF، موتور ZH معمولاً کلید خام یا نام خالی نشان می‌دهد مگر اینکه TXT جداگانه لود شود (ZH استوک TXT را لود نمی‌کند). وضعیت نام نمایشی: **موجود ولی غیرفعال/نامعتبر برای CSF.**

### B) سایت packed MIM-104F / PAC-3 — نزدیک‌ترین خانواده Patriot در DATA فعلی

| Object | DisplayName | Side | فایل در `_SPEC_DATA_ONE.big` |
|---|---|---|---|
| `America_MIM104F` | `OBJECT:SamSite` → CSF «SAM Site» | America | `Data/INI/Object/Specter/United States Of America/AirDefense Installation/MIM104F_Site.ini` |
| `America_MIM104F_Launcher` | `OBJECT:MIM104F` → CSF «MIM104F Patriot / PAC3 Missiles / ABM / AAM / MultiAttack» | America | `…/MIM_104F.ini` |
| `America_MIM104F_ABM_Launcher` | همان `OBJECT:MIM104F` | America | `…/MIM_104F_ABM.ini` |
| `AmericaMobileSamSiteMIM104F` | `OBJECT:MIM104F` | America | `…/Wheeled/MIM104F.ini` (`ReplaceObject = America_MIM104F`) |

CSF دکمه: `CONTROLBAR:ConstructAmerica_MIM104F` = `MIM104F Patriot`.

این سایت از نظر نام Object «Patriot» نیست، ولی CSF و سلاح PAC-3 آن را خانواده Patriot/PAC-3 معرفی می‌کنند. معادل قطعی باتری MIM-104 کامل (با رادار) اعلام نشد.

### C) `AmericaPatriotBattery` — شباهت نام؛ Patriot نیست

| فیلد | مقدار | شواهد |
|---|---|---|
| Object | `AmericaPatriotBattery` | `patch/Data/INI/Object/Specter/United States Of America/Buildings/C-RAM.ini` و همان مسیر در DATA BIG |
| DisplayName | `OBJECT:CRAM` | CSF: «C-RAM Base Defense / 20mm AAAG / …» |
| Model | `US_CRAM` | `Art/W3D/US_CRAM.W3D` در ART BIG |
| سلاح | `20mm_HEIT-SD_LPWS_*` | توپ C-RAM نه موشک Patriot |
| دکمه بولدوزر | `CONTROLBAR:ConstructAmericaPatriotBattery` = **`C-RAM`** | overlay/packed CSF |

نام Object از ZH استوک مانده است. **صرف این نام دلیل وجود Patriot نیست.**

## ۲. پرتابگر، رادار و اجزای مکمل

| جزء authentic Patriot | وضعیت در SPECTER فعلی |
|---|---|
| پرتابگر M901 / LS | **پیدا نشد.** overlay از TEL فهد-۳ استفاده می‌کند. packed از `US_MIM104F_L` استفاده می‌کند. |
| رادار AN/MPQ-53 یا AN/MPQ-65 | **پیدا نشد** (جستجوی نام در INI/CSF/W3D). |
| ECS / AN/MSQ-104 | **پیدا نشد.** |
| موشک PAC-2 / PAC-3 | PAC-3 به‌عنوان پرتابه و سایت MIM-104F **موجود** است. overlay به‌جای PAC-3 از AIM-120 استفاده می‌کند. |

`America_AD_Patriot` یک خودرو تکی DeployStyle است (Pack/Unpack). رادار جدا ندارد.

`America_MIM104F` پد `Spec_SamUsCnfg` است با `SpawnBehavior` چهار برده: `America_MIM104F_Launcher` و `America_MIM104F_ABM_Launcher`. KindOf سایت شامل `SPAWNS_ARE_THE_WEAPONS` است. رادار Object جدا ندارد.

## ۳. مدل‌های W3D و تصاویر

منبع ART: `_SPEC_ART_ONE.big`.

| Asset | نقش | وضعیت | مسیر در BIG |
|---|---|---|---|
| `Irq_Fahad3` / `Irq_Fahad3D` / `Irq_Fahad3_A` / `Irq_Fahad3_AD` | مدل overlay Patriot | **موجود — مدل فهد-۳ عراق است نه Patriot** | `Art/W3D/Irq_Fahad3.W3D` و سه حالت دیگر |
| `US_MIM104F` / `US_MIM104F_L` | TEL/launcher MIM-104F | **موجود** | `Art/W3D/US_MIM104F.W3D`, `Art/W3D/US_MIM104F_L.W3D` + `Art/Textures/US_MIM104F.dds` |
| `PAC-3` | پرتابه PAC-3 | **موجود** | `Art/W3D/PAC-3.W3D` |
| `US_AIM120` | پرتابه overlay Patriot | **موجود — AIM-120 نه PAC-3** | `Art/W3D/US_AIM120.W3D` |
| `US_CRAM` | مدل AmericaPatriotBattery | **موجود — C-RAM** | `Art/W3D/US_CRAM.W3D` |
| `Spec_SamUsCnfg` | پد سایت آمریکا | **موجود** | `Art/W3D/Spec_SamUsCnfg.W3D` |
| `SAPatriot` | ButtonImage ساخت overlay | **پیدا نشد در SPEC ART** | احتمالاً فقط INIZH استوک |
| `us_mim90d` | SelectPortrait overlay | **پیدا نشد در SPEC ART** | — |
| `us_mim104e` | ButtonImage MIM-104F | **پیدا نشد در SPEC ART** | — |

## ۴. Weapon و Projectile و هدف‌گیری / رهگیری

### Overlay `America_Weapon_Patriot`

- فایل last-wins: `patch/Data/INI/Weapon_FactionExpansion.ini` (مسیر یکتا؛ در packed DATA نیست). همان فایل در patch BIG.
- `ProjectileObject = America_Projectile_Patriot`
- پرتابه: `patch/Data/INI/Object/Specter/PatchSystems/Projectile_FactionExpansion_PhaseC.ini` — مدل `US_AIM120`، `MissileAIUpdate TryToFollowTarget = Yes`، `Locomotor = AIM-120CLocomotor`، `KindOf` شامل `PROJECTILE SMALL_MISSILE`
- `AntiAirborneVehicle = Yes`, `AntiAirborneInfantry = Yes`, `AntiGround = No`
- **AntiBallisticMissile / AntiProjectile / AntiSmallMissile تعریف نشده**
- ClipSize 4، AttackRange 650
- واحد فقط `SECONDARY` و `TERTIARY` دارد؛ **PRIMARY ندارد**
- Draw واحد **WeaponLaunchBone ندارد**
- KindOf واحد: `PRELOAD SELECTABLE NO_HEAL_ICON DONT_AUTO_CRUSH_INFANTRY CAN_CAST_REFLECTIONS VEHICLE SCORE` — **`CAN_ATTACK` ندارد**

وضعیت رزمی overlay: **ناقص / احتمالاً خراب** (ممکن است شلیک نکند یا نتواند هدف هوایی را به‌درستی درگیر کند). این استنتاج فایلی است؛ ZH اجرا نشد.

### Packed MIM-104F

- `12x_LRSAM_PAC3F_MSE` → `PAC-3_Object` ، صدای `MIM104_Fire`
- `10x_PAC3_MSE_ABM` → `PAC3_ABM_Object`
- هر دو در `patch/Data/INI/Weapon.ini` و packed `Data/INI/Weapon.ini`
- سلاح ABM فلگ `AntiBallisticMissile` دارد
- مدل پرتابه `PAC-3.W3D` موجود است
- `FireOCL` قفل هدف روی برخی سلاح‌های PAC-3 هست

وضعیت رزمی MIM-104F: **کامل‌تر از overlay** برای ضد هوایی/ABM روی کاغذ؛ رادار جدا و cameo کامل نیست.

### باقی‌مانده ZH

`Weapon PatriotMissileWeapon` / `PatriotMissileWeaponAir` / `PatriotMissileAssistWeapon` در `Weapon.ini` با `ProjectileObject = PatriotMissile` (مدل `AVRaptor_M`). این سلاح استوک ZH است و به `America_AD_Patriot` وصل نیست.

## ۵. CommandSet و CommandButton و دکمه ساخت

### مسیر overlay / patch BIG (قابل ساخت)

| جزء | مقدار | فایل |
|---|---|---|
| دکمه | `Command_ConstructAmerica_AD_Patriot` | `patch/Data/INI/CommandButton_PhaseG_Identity.ini` و patch BIG |
| Command | `UNIT_BUILD` | همان |
| Object | `America_AD_Patriot` | همان |
| ButtonImage | `SAPatriot` | در SPEC ART پیدا نشد |
| TextLabel | `CONTROLBAR:ConstructAmerica_AD_Patriot` | در CSF نیست؛ در TXT هست |
| منوی تولید | `America_MilitaryHQCommandSet` اسلات **۴** (قابل‌رؤیت ۱–۱۴) | `patch/Data/INI/CommandSet_FactionExpansion_Armies.ini` (در packed DATA نیست) |
| ساختمان | `America_MilitaryHQ` | `patch/Data/INI/Object/Specter/PatchSystems/MilitaryHQ/MilitaryHQ_StockFactions.ini` |
| نوار خود واحد | `S400ECommandSet` اسلات ۱/۳/۵ = سوئیچ AA/ABM | `CommandSet.ini` در overlay و packed DATA **موجود** |
| دکمه‌های حالت | `Command_AADS_AA_Mode` / `Command_AADS_ABM_Mode` | `CommandButton.ini` |

در packed DATA بدون overlay: `Command_ConstructAmerica_AD_Patriot` **وجود ندارد** و `America_MilitaryHQCommandSet` **وجود ندارد**. پس با `Launch_Specter.bat` تنها، این واحد ساخته نمی‌شود.

### مسیر packed DATA (بولدوزر آمریکا)

`AmericaDozerCommandSet` در `_SPEC_DATA_ONE.big` `Data/INI/CommandSet.ini`:

| اسلات | دکمه | Object واقعی | قابل‌رؤیت |
|---|---|---|---|
| ۷ | `Command_ConstructAmericaPatriotBattery` | `AmericaPatriotBattery` = **C-RAM** | بله |
| ۱۰ | `Command_ConstructAmerica_MIM104F` | `America_MIM104F` = سایت PAC-3 | بله |
| ۴ | `Command_ConstructAmerica_HeavyAirBase` | Heavy Air Base نه Patriot | بله |

اگر overlay `CommandSet.ini` loose کپی شود، اسلات ۴ بولدوزر به `Command_ConstructAmericaPatriotPAC3MSE` عوض می‌شود (همان Object `America_MIM104F`).

## ۶. کشور و دسترسی

| تعریف | کشور | ساختمان / منو | پیش‌نیاز | سقف |
|---|---|---|---|---|
| `America_AD_Patriot` | America | `America_MilitaryHQ` اسلات ۴ (شروع overlay FactionAmerica) | `SCIENCE_Rank3` | ۱۰ ، `Patch_AirDefense` |
| `America_MIM104F` | America | بولدوزر آمریکا اسلات ۱۰ | `AmericaPowerPlant` | ۳ |
| `Japan_AD_Patriot` | Japan | `Japan_WarFactoryCommandSet` اسلات **۱۵** | `SCIENCE_Rank3` | ۱۰ | 

اسلات ۱۵ کارخانه ژاپن **روی ControlBar دیده نمی‌شود**. افزون بر این، overlay loose هم `CommandSet_Japan.ini` و هم `CommandSet_ZZZZ_WarFactoryRebuild.ini` را با نام `Japan_WarFactoryCommandSet` دارد؛ ZH روی تعریف تکراری CommandSet کرش می‌کند. Patch BIG فقط `CommandSet_Japan.ini` را دارد نه ZZZZ.

## ۷. کامل و فعال در برابر بلااستفاده / ناقص / خراب

| تعریف | وضعیت |
|---|---|
| `America_AD_Patriot` | INI و دکمه HQ فعال‌اند اگر overlay/patch نصب باشد. هویت 3D Patriot نیست. CSF ندارد. CAN_ATTACK ندارد. استخوان شلیک ندارد. رهگیری بالستیک ندارد. **ناقص / احتمالاً خراب رزمی** |
| `America_MIM104F` + launcherها | در DATA BIG فعال و از بولدوزر قابل ساخت. مدل MIM-104F و PAC-3 موجود. رادار جدا و cameo `us_mim104e` نیست. Display سایت = SAM Site. **موجود و تا حدی عملیاتی به‌عنوان سایت PAC-3 نه باتری کامل Patriot** |
| `AmericaPatriotBattery` | فعال ولی **C-RAM**. باقی‌مانده نام ZH. |
| `Weapon PatriotMissileWeapon` / `Object PatriotMissile` | باقی‌مانده ZH؛ به واحد overlay وصل نیست |
| کلیدهای TXT فاز G | موجود روی دیسک؛ موتور ZH CSF می‌خواند نه TXT |

## ۸. Cloneها و نسخه‌های تکراری

| نام | چیست | طبقه‌بندی |
|---|---|---|
| `Japan_AD_Patriot` | کپی نزدیک `America_AD_Patriot` با `Japan_Weapon_PatriotPAC3` و `Japan_Projectile_PatriotPAC3` (باز هم `US_AIM120` + فهد-۳) | کلون overlay؛ تولید اسلات ۱۵ نامرئی |
| `Boss_PatriotBattery` | در `Boss_Faction_Objects.ini` overlay؛ مدل `US_CRAM` | کلون C-RAM |
| `Lazr_AmericaPatriotBattery` / `SupW_AmericaPatriotBattery` | دکمه‌های ژنرال لیزر/EMP در `CommandButton.ini` | کلون استوک ZH |
| `AmericaMobileSamSiteMIM104F` | سایت چرخ‌دار با `ReplaceObject = America_MIM104F` | پوشاننده / کلون سایت |
| `ArabVehicleMIM104ELauncher_*` | MIM-104E ائتلاف عربی، مدل `Arb_MIM104E_L` | خانواده مرتبط نه USA Patriot |
| `PAC-3_Object{,1,2,3}` / `PAC3_ABM_Object` | پرتابه مشترک؛ THAAD و IRIS-T و Khordad هم از مدل `PAC-3` استفاده می‌کنند | پرتابه مشترک — شباهت مدل ≠ Patriot بودن آن واحدها |
| `DamagedPatriotAAM` / `DamagedPatriotABM` | حفره بازسازی launcher MIM-104F | باقی‌مانده آسیب |

## ۹. نام‌های مرتبط که Patriot نیستند

- `AmericaPatriotBattery` = C-RAM.
- `OBJECT:PatriotBattery` در CSF هنوز «Patriot Missile System» است ولی Object زنده `DisplayName = OBJECT:CRAM` دارد.
- `Sa8OSAmissile` DisplayName `OBJECT:PatriotMissile` دارد؛ مدل در packed DATA = `AVRaptor_M`. معادل Patriot اعلام نشد.
- `AN/MPQ` در INI/CSF/W3D فعلی پیدا نشد.
- `Command_ConstructAmericaVehicleAN_TPY2` در ZZZZ WarFactory برای ژاپن ظاهر می‌شود؛ TPY-2 رادار THAAD است نه Patriot، و آن CommandSet کلون USA است.

## آیا Patriot همین حالا قابل ساخت است؟

| نصب | `America_AD_Patriot` | سایت `America_MIM104F` | `AmericaPatriotBattery` |
|---|---|---|---|
| فقط Launch_Specter (ART+DATA BIG) | خیر (Object در DATA BIG نیست) | بله، بولدوزر اسلات ۱۰ | بله، ولی C-RAM است |
| overlay loose یا `_SPECTER_PATCH_FINAL.big` | بله، HQ آمریکا اسلات ۴ بعد از Rank 3 | بله اگر CommandSet.ini packed/overlay بولدوزر را نگه دارد | بله، C-RAM |
| قابل استفاده authentic | خیر | تا حدی به‌عنوان PAC-3 بدون رادار جدا | خیر |

**نتیجه Patriot: موجود ولی ناقص.**

---

# گزارش Iron Dome

## ۱. آیا سامانه در بازی وجود دارد؟ Object و نام نمایشی

**بله، دو خط موازی. هیچ‌کدام سامانه کامل Iron Dome با رادار EL/M-2084 و رهگیر Tamir نیستند.**

### A) واحد overlay — نام صریح Iron Dome

| فیلد | مقدار | مسیر / BIG |
|---|---|---|
| Object | `Israel_AD_IronDome` | `patch/Data/INI/Object/Specter/Israel Defense Forces/AirDefense/Israel_AD_IronDome.ini` |
| همان مسیر در DATA BIG | بله | `_SPEC_DATA_ONE.big` و `_SPECTER_PATCH_FINAL.big` — last-wins = overlay loose |
| DisplayName key | `OBJECT:Israel_AD_IronDome` | INI خط ۷۸ |
| متن TXT | `Israel Iron Dome Battery` | `patch/Data/English/FactionExpansion_PhaseFPlus_Strings.txt` |
| متن generals.csf | **کلید موجود نیست** | — |
| Side | `Israel` | overlay faction نه AirF |
| مدل | `RUS_9K96S2` / `RUS_9K96S2D` | Pantsir-class روسی |

### B) سایت packed با مدل اختصاصی Iron Dome

| Object | DisplayName | Side در DATA BIG | فایل |
|---|---|---|---|
| `AirF_AmericaPatriotBattery` | `OBJECT:SamSite` | AmericaAirForceGeneral | `Data/INI/Object/Specter/Israel Defense Forces/AirDefense Sites/IroneDomeSite.ini` |
| `ISI_IroneDome` | `OBJECT:IroneDome` → CSF «Irondome / Multitargeting / …» | AmericaAirForceGeneral | `…/IroneDome_AA.ini` |
| `ISI_IroneDome_ABM` | `OBJECT:IroneDomeABM` — **کلید CSF نیست** | AmericaAirForceGeneral | `…/IroneDome_ABM.ini` |
| `IroneDomeDamagedDamaged(_ABM)` | `OBJECT:DamagedIroneDome` | همان | همان فایل‌ها |

نام سایت `AirF_AmericaPatriotBattery` باقی‌مانده ZH است. محتوا spawnکننده Iron Dome است نه Patriot. دکمه AirF: `CONTROLBAR:Constructisiironedome` = `Irone Dome`.

در packed PlayerTemplate، اسرائیل همان `FactionAmericaAirForceGeneral` است (کامنت INI: Israel). Overlay کشور جدا `FactionIsrael` با `Israel_MilitaryHQ` اضافه می‌کند.

## ۲. پرتابگر، رادار و اجزای مکمل

| جزء authentic Iron Dome | وضعیت |
|---|---|
| پرتابگر Tamir | Packed: مدل `Isr_Ironedome_l` **موجود**. Overlay: مدل Pantsir. نام Tamir **پیدا نشد**. |
| رادار EL/M-2084 | **پیدا نشد.** |
| BMC | **پیدا نشد.** |
| کشف موشک کوچک | Overlay `StealthDetectorUpdate ExtraRequiredKindOf = SMALL_MISSILE` (کشف، نه درگیری) |

سایت packed: `SpawnNumber = 4`، `SpawnTemplateName = ISI_IroneDome_ABM ISI_IroneDome`، پد `Spec_SamZGCnfg`. رادار Object جدا ندارد.

## ۳. مدل‌های W3D و تصاویر

| Asset | نقش | وضعیت | مسیر |
|---|---|---|---|
| `RUS_9K96S2` / `RUS_9K96S2D` | overlay Iron Dome | **موجود — Pantsir نه Iron Dome** | `Art/W3D/RUS_9K96S2.W3D` |
| `Isr_Ironedome_l` | پرتابگر packed | **موجود — هنر اختصاصی** | `Art/W3D/Isr_Ironedome_l.W3D` |
| `ISI_IroneDome_M` | موشک packed | **موجود** | `Art/W3D/ISI_IroneDome_M.W3D` |
| `Spec_SamZGCnfg` | پد سایت | **موجود** | `Art/W3D/Spec_SamZGCnfg.W3D` |
| `Spec_Indic_AAM` / `Spec_Indic_ABM` | نشانگر حالت launcher | **موجود** | `Art/W3D/Spec_Indic_AAM.W3D` و ABM |
| `rus_pantsirs1m` | Portrait overlay | **پیدا نشد در SPEC ART** | — |
| `isi_ironedome` | Cameo سایت packed | **پیدا نشد در SPEC ART** (فقط W3D هم‌نام موشک هست) | — |
| `SAPatriot` | ButtonImage دکمه overlay Iron Dome | **پیدا نشد در SPEC ART** | دکمه Iron Dome از cameo Patriot استوک استفاده می‌کند |

## ۴. Weapon و Projectile و هدف‌گیری / رهگیری

### Overlay `Israel_AD_IronDome`

| اسلات | سلاح | پرتابه | ضد هوایی | ضد بالستیک | فایل سلاح |
|---|---|---|---|---|---|
| PRIMARY | `Israel_Weapon_AntiDrone` | `Israel_Projectile_AntiDrone` مدل `AIM-9X` | Yes | تعریف نشده | `Weapon_FactionExpansion.ini` |
| TERTIARY | `57E6M-R` | `57E6M_R_MissileObject` مدل `Irq_R27CF` | Yes | **No** (صریح) | `Weapon.ini` خط ۲۲۶۹۰ |
| SECONDARY | کامنت شده | — | — | — | — |

`57E6M-R`: `AntiBallisticMissile = No`, `AntiProjectile = No`, `AntiSmallMissile = No`. این سلاح Pantsir است نه Tamir.

پرتابه antidrone: `MissileAIUpdate TryToFollowTarget = Yes` ولی `FuelLifetime = 700` (کوتاه). KindOf واحد overlay **CAN_ATTACK دارد**.

وضعیت overlay: **ناقص / برای رهگیری راکت/موشک نامعتبر.**

### Packed `ISI_IroneDome` / `_ABM`

| سلاح | فلگ‌های هدف | پرتابه | مدل |
|---|---|---|---|
| `IroneDome_AA` | AntiAirborneVehicle=Yes, AntiBallisticMissile=No | `IroneDomeMissileObject` | variations `ISI_IroneDome_M` |
| `IroneDome_ABM` | **AntiBallisticMissile=Yes**, AntiSmallMissile=Yes | `IroneDomeMissileObject_ABM` | `ISI_IroneDome_M` |
| `IroneDome_MT_LockControl_*` | قفل چندهدفه | `PAC3_ABM_Object` / `GenericMultiEngageModeObject` | — |

`WeaponSpeed = 9999999999` روی سلاح‌های packed (الگوی قفل آنی SPECTER). `FireOCL` قفل هدف دارد. Locomotor پرتابه‌ها `PAC-3MissileLocomotor*`.

وضعیت packed: **رهگیری ABM روی کاغذ معتبرتر از overlay**؛ نام Tamir نیست و رادار جدا نیست.

## ۵. CommandSet و CommandButton و دکمه ساخت

### Overlay / patch — کشور Israel

| جزء | مقدار | فایل |
|---|---|---|
| دکمه | `Command_ConstructIsrael_AD_IronDome` | `patch/Data/INI/CommandButton_PhaseFPlus_Tech.ini` |
| Object | `Israel_AD_IronDome` | همان |
| ButtonImage | `SAPatriot` | cameo غلط |
| HQ | `Israel_MilitaryHQCommandSet` اسلات **۱** | `CommandSet_FactionExpansion_Armies.ini` |
| Barracks | `Israel_BarracksCommandSet` اسلات ۱ | `CommandSet_Israel_Integrity.ini` |
| WarFactory 1/2/3 | اسلات ۱ Iron Dome + اسلات ۲ Barak8 | همان Integrity |
| نوار واحد | `GLAVehicleQuadCannon` (حرکت/گارد/توقف) | در packed و overlay **موجود** — نوار استوک Quad Cannon نه Iron Dome |

در packed DATA بدون overlay: دکمه `Command_ConstructIsrael_AD_IronDome` **نیست**. Object در DATA BIG هست ولی منوی تولید overlay را ندارد.

### Packed AirF dozer — سایت

`AirF_AmericaDozerCommandSet` در DATA BIG:

| اسلات | دکمه | Object |
|---|---|---|
| ۷ | `AirF_Command_ConstructAmericaPatriotBattery` | `AirF_AmericaPatriotBattery` (سایت Iron Dome) |
| ۴ | `Command_ConstructIsrael_HeavyAirBase` | Heavy Air Base |
| ۱۰ | `Command_ConstructIsraelBuildingC-RAM` | C-RAM اسرائیل |

اگر overlay `CommandSet.ini` loose نصب شود، اسلات ۴ AirF می‌شود `Command_ConstructIsraelIronDomeBattery` که **همان** `AirF_AmericaPatriotBattery` را می‌سازد (alias). TextLabel این دکمه در CSF **نیست**.

## ۶. کشور و دسترسی

| تعریف | کشور / Side | تولید از | پیش‌نیاز | سقف |
|---|---|---|---|---|
| `Israel_AD_IronDome` | Israel | `Israel_MilitaryHQ` اسلات ۱؛ Barracks integrity | ندارد (برخلاف Patriot Rank3) | ۱۰ ، `Patch_AirDefense` |
| سایت `AirF_AmericaPatriotBattery` | AmericaAirForceGeneral (اسرائیل packed) | بولدوزر AirF اسلات ۷ | `AirF_AmericaPowerPlant` | ۳ |
| launcherهای spawn | AmericaAirForceGeneral | spawn از سایت؛ قابل ساخت مستقیم از منو نیستند | — | برده‌های سایت |

`Barak8` سامانه جدا اسرائیل است و Iron Dome نیست.

## ۷. کامل و فعال در برابر بلااستفاده / ناقص / خراب

| تعریف | وضعیت |
|---|---|
| `Israel_AD_IronDome` | Object در DATA+overlay فعال. با overlay از HQ اسرائیل ساخته می‌شود. هنر Pantsir، سلاح Pantsir، بدون ABM، CSF ندارد. **ناقص** |
| `AirF_AmericaPatriotBattery` + `ISI_IroneDome*` | در DATA BIG فعال. مدل اختصاصی و سلاح ABM دارد. از بولدوزر AirF اسلات ۷ ساخته می‌شود. نام Patriot ZH، بدون رادار، cameo در ART نیست. **موجود و تا حدی عملیاتی به‌عنوان سایت پرتابگر** |
| `IroneDomeMissileObject` والد | مدل `AVRaptor_M`؛ variations `_1/_2/_3` مدل درست `ISI_IroneDome_M` دارند | ناقص در والد، کامل‌تر در variation |
| TXT فاز F+ | روی دیسک هست؛ CSF ندارد | نام نمایشی overlay برای ZH نامعتبر |

## ۸. Cloneها و نسخه‌های تکراری

| نام | نقش |
|---|---|
| `Israel_AD_IronDome` | واحد overlay / packed همان مسیر |
| `AirF_AmericaPatriotBattery` | سایت packed با نام Patriot |
| `ISI_IroneDome` / `ISI_IroneDome_ABM` | جفت AA/ABM |
| `IroneDomeDamagedDamaged(_ABM)` | حفره بازسازی |
| `IroneDomeMissileObject{,_1,_2,_3,_ABM}` | کلون پرتابه |
| `Command_ConstructIsraelIronDomeBattery` | alias دکمه همان سایت AirF |
| `AirF_Command_ConstructAmericaPatriotBattery` | دکمه اصلی سایت |
| C-RAM اسرائیل / `IsraelBuildingC-RAM` | پدافند توپخانه‌ای جدا؛ Iron Dome نیست |

## ۹. نام‌های مرتبط که Iron Dome نیستند

- Tamir: **پیدا نشد** در Object/Weapon/CSF/W3D.
- EL/M-2084: **پیدا نشد**.
- David's Sling / Arrow: در این ممیزی به‌عنوان Iron Dome اعلام نشدند (جستجوی Arrow در این محدوده خالی بود).
- `Barak8`: سامانه جدا.
- `AirF_AmericaPatriotBattery`: نام Patriot، محتوا Iron Dome site — شباهت نام Patriot دلیل Patriot بودن نیست؛ محتوا هم باتری کامل Iron Dome نیست.
- `RUS_9K96S2` / Pantsir: هنر قرضی overlay؛ Pantsir ≠ Iron Dome.

## آیا Iron Dome همین حالا قابل ساخت است؟

| نصب | `Israel_AD_IronDome` | سایت `ISI_IroneDome` از `AirF_AmericaPatriotBattery` |
|---|---|---|
| فقط Launch_Specter | Object در DATA هست ولی دکمه/HQ overlay نیست → **عملاً از منو ساخته نمی‌شود** | بله، بولدوزر AirF اسلات ۷ (فکشن AirF/اسرائیل packed) |
| overlay یا patch BIG | بله، HQ اسرائیل اسلات ۱ | بله اگر CommandSet AirF باقی بماند |
| authentic Tamir+رادار | خیر | خیر |

**نتیجه Iron Dome: موجود ولی ناقص.**

---

## فهرست فشرده فایل‌های مرتبط (مسیر + BIG)

کاتالوگ کامل در Excel برگه `FileCatalog` / `Objects` / `Weapons` / `Assets_W3D_Images` است. موارد اصلی:

### Patriot

| فایل | حاوی | لایه last-wins |
|---|---|---|
| `patch/Data/INI/Object/Specter/PatchSystems/AirDefense/America_AD_Patriot.ini` | Object `America_AD_Patriot` | overlay ؛ همچنین `_SPECTER_PATCH_FINAL.big` |
| `patch/Data/INI/Object/Specter/Japan Self-Defense Forces/AirDefense/Japan_AD_Patriot.ini` | کلون ژاپن | overlay / patch BIG |
| `patch/Data/INI/Object/Specter/Japan Self-Defense Forces/Projectiles/Japan_Projectile_PatriotPAC3.ini` | پرتابه ژاپن | overlay / patch BIG |
| `patch/Data/INI/Weapon_FactionExpansion.ini` | `America_Weapon_Patriot` | overlay / patch BIG (مسیر یکتا) |
| `patch/Data/INI/Weapon_Japan.ini` | `Japan_Weapon_PatriotPAC3` | overlay |
| `patch/Data/INI/Object/Specter/PatchSystems/Projectile_FactionExpansion_PhaseC.ini` | `America_Projectile_Patriot` | overlay |
| `patch/Data/INI/CommandButton_PhaseG_Identity.ini` | دکمه ساخت | overlay / patch BIG |
| `patch/Data/INI/CommandSet_FactionExpansion_Armies.ini` | HQ آمریکا اسلات ۴ | overlay / patch BIG |
| `Data/INI/Object/Specter/United States Of America/AirDefense Installation/MIM104F_Site.ini` | `America_MIM104F` | `_SPEC_DATA_ONE.big` |
| `Data/INI/Object/Specter/United States Of America/AirDefense Installation/MIM_104F.ini` | launcher AAM | DATA BIG |
| `Data/INI/Object/Specter/United States Of America/AirDefense Installation/MIM_104F_ABM.ini` | launcher ABM | DATA BIG |
| `patch/Data/INI/Object/Specter/United States Of America/Buildings/C-RAM.ini` | `AmericaPatriotBattery` = C-RAM | overlay last-wins روی DATA |
| `Art/W3D/Irq_Fahad3.W3D` (+ A/AD/D) | هنر overlay | `_SPEC_ART_ONE.big` |
| `Art/W3D/US_MIM104F.W3D` / `US_MIM104F_L.W3D` / `PAC-3.W3D` | هنر packed | ART BIG |

### Iron Dome

| فایل | حاوی | لایه |
|---|---|---|
| `patch/Data/INI/Object/Specter/Israel Defense Forces/AirDefense/Israel_AD_IronDome.ini` | Object overlay | overlay last-wins ؛ DATA و patch BIG هم دارند |
| `patch/Data/INI/CommandButton_PhaseFPlus_Tech.ini` | دکمه HQ | overlay / patch BIG |
| `patch/Data/INI/CommandSet_FactionExpansion_Armies.ini` | `Israel_MilitaryHQCommandSet` اسلات ۱ | overlay / patch BIG |
| `patch/Data/INI/CommandSet_Israel_Integrity.ini` | Barracks/WF | overlay / DATA / patch |
| `Data/INI/Object/Specter/Israel Defense Forces/AirDefense Sites/IroneDomeSite.ini` | `AirF_AmericaPatriotBattery` | DATA BIG |
| `…/IroneDome_AA.ini` / `IroneDome_ABM.ini` | launcherها | DATA BIG |
| `Data/INI/Object/Specter/Israel Defense Forces/Israel_WeaponObjects.ini` | `IroneDomeMissileObject*` | DATA BIG |
| `Data/INI/Weapon.ini` | `IroneDome_AA` / `IroneDome_ABM` / `57E6M-R` | overlay loose اگر کپی شود last-wins روی DATA |
| `Art/W3D/RUS_9K96S2.W3D` | هنر overlay Pantsir | ART BIG |
| `Art/W3D/Isr_Ironedome_l.W3D` | پرتابگر packed | ART BIG |
| `Art/W3D/ISI_IroneDome_M.W3D` | موشک packed | ART BIG |

---

## محدودیت شواهد

- این محیط Zero Hour را اجرا نمی‌کند. «قابل ساخت» یعنی دکمه در اسلات ۱–۱۴ به Object تعریف‌شده وصل است، نه مشاهده بازی زنده.
- `INIZH.big` در مخزن نیست؛ cameoهای استوک مثل `SAPatriot` ممکن است در نصب واقعی ZH باشند.
- New donor بررسی نشد.
- فایل بازی تغییر نکرد.

---

## خروجی‌ها

- Markdown: `docs/specter-patriot-iron-dome-audit/SPECTER_PATRIOT_IRON_DOME_AUDIT.md`
- Excel: `docs/specter-patriot-iron-dome-audit/SPECTER_PATRIOT_IRON_DOME_AUDIT.xlsx`
  - برگه‌ها: Verdict, LoadOrder, Patriot_Q1_Q9, IronDome_Q1_Q9, Objects, Weapons, CommandSets, CommandButtons, Assets_W3D_Images, CSF_Strings, Clones, FileCatalog, MethodNotes

# تشخیص: چرا ۱۲ سامانه Global Market موشک ورودی را هدف نمی‌گیرند

منبع: فقط SPE.part001.rar تا SPE.part058.rar  
BIGهای مؤثر: `_SPEC_DATA_ONE.big`، `INIZH.big`، `0_SPECTER_ABMDedicatedRadar.big`  
هیچ فایل بازی تغییر نکرده است. Pantsir-S1M و Krasukha-4 خارج از محدوده بودند.

## مرجع Patriot (Defence Art آمریکا)

دکمهٔ فعال در `AmericaDozerCommandSet` (last-win: `CommandSet_ZZZZ_ZGlobalStoreFive.ini`):

| اسلات | دکمه | آبجکت مؤثر | نقش واقعی |
|---|---|---|---|
| 7 | `Command_ConstructAmericaPatriotBattery` | `AmericaPatriotBattery` از `C-RAM.ini` | C-RAM توپ ۲۰ میلی‌متری، نه موشک پاتریوت |
| 10 | `Command_ConstructAmerica_MIM104F` | `America_MIM104F` | سایت Patriot / PAC-3 در Defence Art |

Patriot موشکی که در بازی کار می‌کند **`America_MIM104F`** است، نه تعریف وانیلا `FactionBuilding.ini`.

زنجیرهٔ شلیک به موشک بالستیک:

1. سایت `America_MIM104F` (`MIM104F_Site.ini`)  
   `KindOf` شامل `SPAWNS_ARE_THE_WEAPONS` است؛ خودش سلاح ندارد.  
   `SpawnBehavior` بلافاصله هر دو لانچر را می‌سازد:  
   `America_MIM104F_Launcher` **و** `America_MIM104F_ABM_Launcher`
2. شلیک به موشک ورودی از لانچر ABM است:  
   **Weapon:** `10x_PAC3_MSE_ABM` (`Weapon.ini`)  
   **Projectile:** `PAC3_ABM_Object`  
   `AntiBallisticMissile = Yes`  
   `AntiAirborneVehicle = No`  
   `AntiGround = No`  
   `DamageType = CRUSH`  
   برد ۱۵۰۰ / حداقل ۳۰۰  
   `KindOf = CAN_ATTACK`، `AutoAcquireEnemiesWhenIdle = Yes`، `VisionRange = 1600`
3. سلاح AA همان سایت (`12x_LRSAM_PAC3F_MSE`) برای هواپیما است:  
   `AntiBallisticMissile = No`، `DamageType = PENALTY`

هدف مهاجم (نمونه `Projectile_Russia_Iskander` و سایر SRBMها):

- `KindOf = PROJECTILE BALLISTIC_MISSILE`
- `Armor = SRBMArmor`

`SRBMArmor` مؤثر (`Armor.ini`):

| DamageType | درصد | اثر روی `estimateWeaponDamage` |
|---|---|---|
| CRUSH | 100% | شلیک مجاز است |
| FALLING | 0% | `INVALID_SHOT`؛ حمله شروع نمی‌شود |
| PENALTY | 0% | همان |
| STATUS | 888% | بیم ردیابی می‌تواند «بزند» ولی منهدم نمی‌کند |

موتور (توضیح داخل overlay `0_SPECTER_ABMDedicatedRadar`):  
`getAbleToUseWeaponAgainstTarget` وقتی تخمین آسیب صفر باشد `INVALID_SHOT` برمی‌گرداند.  
`AntiBallisticMissile = Yes` به‌تنهایی کافی نیست.

C-RAM (اسلات ۷) هم می‌تواند موشک بزند:  
`20mm_HEIT-SD_LPWS_AA` با `AntiBallisticMissile = Yes` و `DamageType = CRUSH`. این Patriot موشکی نیست.

## الگوی Global Market

فروشگاه جهانی `Iraq_MICCommandSet` است  
(last-win: `CommandSet_ZZZZ_IraqMicToWfRadarAd.ini`).  
دکمه‌ها `Iraq_MIC_*` می‌سازند، نه نسخهٔ اصلی کشور.

هر ۱۲ سامانه وسیلهٔ packed هستند، نه سایت آماده مثل Patriot:

- سلاح‌های روی خود وسیله فقط خودکشی استقرارند: `S400R_Deploy` / `S400R_Deploy_ABM` / `92N6R_Deploy`  
  (`DeathType = SPLATTED` یا `EXTRA_8`، `RadiusDamageAffects = SELF SUICIDE`)
- لانچرها باید اول `Upgrade_AADS_AA_Mode` یا `Upgrade_AADS_ABM_Mode` بگیرند، بعد دکمهٔ استقرار.  
  `S400ECommandSet` به‌تنهایی دکمهٔ شلیک رهگیر ندارد.
- رادارها با `Command_RadarDeployCommand` (اسلات SECONDARY) مستقر می‌شوند.
- شلیک واقعی، اگر وجود داشته باشد، از آبجکت‌های OCL پس از استقرار است (FCS یا CombatMode).

## جدول ۱۲ سامانه

ستون «علت»: حرف A–F طبق درخواست.  
`اثبات‌شده` از متن INI است. `فرضیه` نیازمند تست داخل بازی است.

| # | سامانه | تعریف مؤثر | تفاوت اصلی با Patriot | علت | روش تأیید داخل بازی |
|---|---|---|---|---|---|
| 1 | Arrow | `Iraq_MIC_Arrow` → استقرار AA: `OCL_Arrow_Deployed` می‌سازد `THAAD_FireControlSystem` با `8x_LRSAM_THAAD`. استقرار ABM: overlay `OCL_Arrow_Deployed_ABM` می‌سازد `THAAD_FireControlSystem_ABM` (`Hq9_AA_Missile_ABM` / CRUSH) + `S400R_FireControlSystem_AUM` (`4x_MRSAM_9M96E2` / CRUSH) | packed بدون `CAN_ATTACK` و بدون سلاح رهگیر؛ برخلاف Patriot هر دو لانچر را خودکار نمی‌سازد. AA: `AntiBallisticMissile = No` و `PENALTY`. ABM پس از overlay از نظر تعریف باید بزند | **A** packed. **C** در حالت AA (اثبات‌شده). ABM پس از overlay: تعریف کافی برای شلیک است؛ اگر باز هم نزند **F** | بساز، بدون استقرار موشک بفرست (نباید شلیک کند). حالت AA را مستقر کن (نباید BM را بگیرد). حالت ABM را مستقر کن؛ اگر FCS با نشان ABM شلیک CRUSH کرد overlay فعال است |
| 2 | AN/TPY-2 اسرائیل | `Iraq_MIC_AN_TPY2` → `OCL_AN_TPY2I_Deployed` → `IsraelTPY2CombatMode`. سلاح PRIMARY: `RadarTrackingBeam` (STATUS / FAERIE_FIRE). `VisionRange` 900. بدون FCS رهگیر | رادار شناسایی است، نه پرتابگر. Patriot سلاح منهدم‌کننده با CRUSH دارد | **A** (اثبات‌شده: قابلیت شلیک رهگیر ندارد). پس از استقرار بیم ردیابی `AntiBallisticMissile = Yes` دارد ولی آسیب STATUS است نه انهدام | مستقر کن. اگر بیم روی موشک می‌نشیند شناسایی هست. انتظار انهدام از خود رادار منطقی نیست |
| 3 | 92N6R | `Iraq_MIC_92N6R` → `OCL_92N6R_Deployed` → `Russia_92N6R_CombatMode`. همان `RadarTrackingBeam` + `VisionRange` 800/900 + StealthDetector 800 | رادار؛ شلیک رهگیر ندارد | **A** (اثبات‌شده) | مثل TPY-2: استقرار، دیدن بیم STATUS، نبود موشک رهگیر |
| 4 | S-400 | `Iraq_MIC_S400` → AA: `OCL_S400R_Deployed` → `S400R_FireControlSystem` / `4x_LRAAM_48N6` (PENALTY، AntiBM No). ABM: `OCL_S400R_Deployed_ABM` → `S400R_FireControlSystem_ABM` / `3x_LRSAM_40N6KMissile_ABM` (**FALLING**) **و** `S400R_FireControlSystem_AUM` / `4x_MRSAM_9M96E2` (**CRUSH**، AntiBM Yes). Overlay این OCL را عوض نکرده | Patriot یک سلاح CRUSH ABM آماده دارد. S-400 ABM اصلی FALLING است (شلیک شروع نمی‌شود)؛ شاهد آتش AUM است | packed **A**. AA **C** (اثبات‌شده). سلاح ۴۰N۶ **C** به‌خاطر FALLING (اثبات‌شده). AUM از تعریف باید بزند؛ اگر نزند **F** (برد حداقل ۷۰۰، Vision AUM = ۹۰۰) | AA مستقر: نباید BM بگیرد. ABM مستقر: اگر فقط FCS با نشان ABM تلاش کند و شلیک نشود FALLING است؛ اگر موشک ۹M۹۶ شلیک شد AUM کار می‌کند |
| 5 | 96L6-TSP | `Iraq_MIC_96L6TSP` → `OCL_96L6TSP_Deployed` → `RussiaVehicle96L6TSPCombatMode`. بدون PRIMARY. فقط `92N6R_Pack`. `VisionRange` 200. StealthDetector 900. WaveEmitter / DataLink | رادار بدون بیم ردیابی و بدون رهگیر. Patriot Vision 1600 و سلاح CRUSH دارد | **A** (اثبات‌شده: سلاح قابل‌شلیک به BM ندارد). شناسایی دوربرد **B** محتمل چون VisionRange فقط ۲۰۰ است | مستقر کن. موشک را در فاصلهٔ میانی بفرست؛ اگر در مه جنگ دیده نشود B است. انتظار شلیک رهگیر نیست |
| 6 | S-500 | `Iraq_MIC_S500`. AA: `OCL_S500_Deployed` → `S500_FireControlSystem` overlay = `Specter_S500_77H6_AAM` (PENALTY، AntiBM No). ABM overlay: `OCL_S500_Deployed_ABM` → `S500_FireControlSystem_ABM` (`Hq9_AA_Missile_ABM` CRUSH) + AUM CRUSH. تعریف SPEC بدون overlay: هر دو FCS از `77H6Missile_ABM` FALLING و OCL_ABM حتی FCS حالت AA را می‌ساخت | Patriot از ابتدا لانچر CRUSH می‌سازد. S-500 بدون overlay نمی‌توانست حمله را شروع کند | packed **A**. AA **C** (اثبات‌شده). ABM پس از overlay باید بزند؛ تأیید **F** | بدون overlay شلیک ABM نباید شروع شود. با BIG `0_SPECTER_ABMDedicatedRadar` حالت ABM باید مثل شاهد HQ-9 شلیک CRUSH کند |
| 7 | HQ-9 | `Iraq_MIC_HQ9`. AA: `OCL_HQ9_Deployed` فقط `ChinaVehicleHQ9_CombatMode` می‌سازد؛ **FCS ندارد**. ABM: `OCL_HQ9_Deployed_ABM` → `HQ9_FireControlSystem_ABM` با PRIMARY `Hq9_AA_Missile_ABM` (CRUSH، AntiBM Yes) و SECONDARY `4x_MRSAM_9M83ME_ACM` (CRUSH، AntiBM Yes). Overlay HQ-9 را last-win نکرده | Patriot همیشه لانچر ABM دارد. HQ-9 در حالت AA اصلاً سلاح رهگیر ندارد؛ در ABM همان سلاح شاهد CRUSH را دارد | packed **A**. AA مستقر **A** (اثبات‌شده: FCS نیست). ABM از تعریف باید بزند؛ اگر نزند **F** (حداقل برد ۸۰۰) | AA مستقر: هیچ رهگیری نباید دیده شود. ABM مستقر: اگر HQ-9 شلیک کرد و Patriot هم شلیک می‌کند، مشکل Global Market از حالت استقرار است نه از AntiBM |
| 8 | HT-233 | `Iraq_MIC_HT233` → `OCL_HT233_Deployed` → `ChinaVehicleHT233_CombatMode`. بدون PRIMARY. `VisionRange` 100. StealthDetector 720. WaveEmitter | رادار بدون بیم ردیابی و بدون رهگیر | **A** (اثبات‌شده). شناسایی **B** محتمل (Vision 100 در برابر برد موشک) | استقرار؛ بررسی دیدن موشک در فاصلهٔ کوتاه در برابر دور. شلیک رهگیر نباید رخ دهد |
| 9 | TRML-4D | `Iraq_MIC_TRML4D` → `OCL_TRML4D_Deployed` → `NatoVehicleTRML4D_CombatMode`. بدون PRIMARY. `VisionRange` 100. StealthDetector 700 | رادار؛ نه پرتابگر | **A** (اثبات‌شده). **B** محتمل برای شناسایی دور | مثل HT-233 |
| 10 | IRIS-T | `Iraq_MIC_IRIST`. AA: `OCL_IRIST_Deployed` → `IRIST_FireControlSystem` / `8x_LRSAM_IRIS-T` (PENALTY، AntiBM No). ABM: `OCL_IRIST_Deployed_ABM` → `IRIST_FireControlSystem_ABM` / `THAADMissile_ABM` (**FALLING**، AntiBM Yes). Overlay این FCS/OCL را عوض نکرده و AUM هم اضافه نکرده | Patriot CRUSH می‌زند. IRIS-T ABM پرچم AntiBM دارد ولی FALLING در برابر SRBMArmor صفر است پس حمله شروع نمی‌شود | packed **A**. AA **C**. ABM **C** (اثبات‌شده: INVALID_SHOT به‌خاطر FALLING، نه به‌خاطر نبود AntiBM) | ABM را مستقر کن. FCS با نشان ABM باید هدف را «ببیند» ولی شلیک نکند. همین آزمایش روی Patriot باید شلیک CRUSH بدهد |
| 11 | AN/TPY-2 آمریکا | `Iraq_MIC_US_AN_TPY2` → `OCL_AN_TPY2_Deployed` → `US_AN_TPY2_CombatMode`. همان `RadarTrackingBeam`. `KindOf` packed شامل `CAN_ATTACK` است ولی سلاح فقط Deploy است با `AutoChooseSources = SECONDARY NONE` | رادار آمریکایی؛ لانچر Patriot نیست | **A** (اثبات‌شده) | مثل TPY-2 اسرائیل |
| 12 | THAAD | `Iraq_MIC_THAAD` → همان FCS تاد/آرو. AA: `8x_LRSAM_THAAD` PENALTY AntiBM No. ABM overlay: `THAAD_FireControlSystem_ABM` = `Hq9_AA_Missile_ABM` CRUSH + AUM. تعریف SPEC: `THAADMissile_ABM` FALLING | packed با `CAN_ATTACK` ولی سلاح‌ها فقط Deploy خودکشی‌اند و `AutoAcquire = No`. Patriot لانچر آماده با CRUSH دارد | packed **A**. AA **C**. ABM پس از overlay باید بزند؛ **F** برای تأیید | مثل Arrow: AA نزند؛ ABM با overlay باید شلیک CRUSH کند |

## مقایسهٔ AntiBallisticMissile (به‌تنهایی علت قطعی نیست)

| سلاح | AntiBM | DamageType | در برابر SRBMArmor | نتیجهٔ هدف‌گیری |
|---|---|---|---|---|
| `10x_PAC3_MSE_ABM` (Patriot) | Yes | CRUSH | 100% | شلیک می‌کند (مرجع) |
| `20mm_HEIT-SD_LPWS_AA` (C-RAM) | Yes | CRUSH | 100% | شلیک می‌کند |
| `Hq9_AA_Missile_ABM` | Yes | CRUSH | 100% | شاهد آتش overlay |
| `4x_MRSAM_9M96E2` (AUM) | Yes | CRUSH | 100% | شاهد دوم |
| `THAADMissile_ABM` / `77H6Missile_ABM` / `3x_LRSAM_40N6KMissile_ABM` | Yes | FALLING | 0% | INVALID_SHOT |
| `8x_LRSAM_THAAD` / `8x_LRSAM_IRIS-T` / `4x_LRAAM_48N6` / `12x_LRSAM_PAC3F_MSE` | No | PENALTY | 0% | نوع هدف + زره هر دو مانع‌اند |
| `RadarTrackingBeam` | Yes | STATUS | 888% | می‌تواند «بگیرد» ولی منهدم نمی‌کند |

## تفکیک رادار / پرتابگر

رادار مستقل (انتظار شلیک از خودشان بدون قابلیت جدید منطقی نیست):

- AN/TPY-2 اسرائیل
- 92N6R
- 96L6-TSP
- HT-233
- TRML-4D
- AN/TPY-2 آمریکا

پرتابگر (پس از استقرار AA/ABM باید FCS ساخته شود):

- Arrow، S-400، S-500، HQ-9، IRIS-T، THAAD

## جمع‌بندی علت‌ها

1. Patriot Defence Art یک سایت است که همان لحظه لانچر ABM با `CAN_ATTACK` + `AutoAcquire Yes` + سلاح CRUSH می‌سازد.
2. هر ۱۲ واحد Global Market در حالت packed رهگیر نیستند (A). لانچرها بدون انتخاب حالت AA/ABM و استقرار، FCS نمی‌سازند.
3. شش رادار اصولاً پرتابگر نیستند (A). سه تای آن‌ها (96L6، HT-233، TRML-4D) حتی بیم ردیابی هم ندارند و VisionRange آن‌ها ۱۰۰–۲۰۰ است (B محتمل).
4. حالت AA پرتابگرها `AntiBallisticMissile = No` و `PENALTY` دارند (C).
5. چند سلاح ABM با وجود `AntiBallisticMissile = Yes` به‌خاطر `FALLING` در برابر `SRBMArmor` حمله را شروع نمی‌کنند (C). IRIS-T ABM هنوز روی این تعریف است. overlay فقط Arrow / THAAD / S-500 ABM را به سلاح CRUSH شاهد برده است.
6. HQ-9 ABM و S-400 AUM از روی INI باید بتوانند بزنند. اگر در بازی نمی‌زنند، علت از AntiBM نیست و باید استقرار، حداقل برد، و دیده شدن هدف تست شود (F).

اصلاح اعمال نشده است. منتظر دستور جداگانه برای تغییر فایل‌ها.

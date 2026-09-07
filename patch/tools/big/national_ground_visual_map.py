"""ART-only visual upgrades for National Ground Forces.

Object names, weapons, costs, CommandButtons, and CommandSets stay unchanged.
Only Model= (and matching Animation=) may change.
"""

from __future__ import annotations

# object -> (new_model_stem, reason)
# Omit units that already use the best available mesh.
VISUAL_UPGRADES = {
    # Japan
    "JapanVehicleType16": ("NAT_Cortale", "Type 16 is a wheeled 105mm MCV; Centauro is the closest packed/donor class (no Type 16 W3D)"),
    "JapanVehicleType16AT": ("NAT_Cortale", "Type 16 AT keeps the wheeled MCV silhouette"),
    "JapanVehicleType89": ("LSF89", "Donor Type 89 tracked IFV (LSF89) replaces wheeled LSFJP89W stand-in"),
    "JapanVehicleType96": ("JP96", "Donor Type 96 WAPC"),
    "JapanVehicleType12": ("AGMZJP88", "Donor Japan Type 12 SSM truck (JapanType12 texture)"),
    "JapanVehicleType12Btry": ("AGMZJP88", "Type 12 battery uses the same donor SSM truck"),
    # South Korea
    "SouthKoreaTankK1A2": ("LSFXK2", "Donor K2 Black Panther (LSFXK2) for the primary ROK MBT slot"),
    "SouthKoreaVehicleK9": ("LSFSKK55", "Donor K9 Thunder SPH"),
    "SouthKoreaVehicleCheongung": ("KVKMSAM", "Donor KM-SAM / Cheongung TEL"),
    # Germany
    "GermanyTankLeopard2A6": ("LSFB2A6", "Donor Leopard 2A6"),
    "GermanyVehiclePuma": ("LSFMZS", "Donor Puma IFV (GermanyArmorPuma / LSFMZS)"),
    "GermanyVehicleGepard": ("LSFLIEBAO", "Donor Gepard / Flakpanzer (猎豹)"),
    "GermanyVehiclePzH2000": ("LSFzh2000", "Donor PzH 2000"),
    "GermanyVehicleBoxerAA": ("LSFBoxerAA", "Donor Boxer air-defense variant"),
    "GermanyVehicleFennek": ("LSFPHD", "Light 4x4 recon (VBL/Fennek class) instead of Stryker"),
    # France
    "FranceTankLeclerc": ("LSFLKLR", "Donor Leclerc (LSFLKLR + fraleclerc textures)"),
    "FranceVehicleVBCI": ("LSFVBCI", "Donor VBCI replaces NAT_VBCI"),
    "FranceVehicleCaesar": ("LSFkaisa", "Donor CAESAR (LSFkaisa)"),
    "FranceVehicleMistral": ("LSFAMX30SA", "Donor AMX-30SA Roland/Mistral SPAAG"),
    "FranceVehicleJaguar": ("LSFamx10", "AMX-10RC / Jaguar wheeled recon already donor-correct"),
    # Britain / Italy extras with real donor meshes
    "ItalyTankAriete": ("LSFITGY", "Donor Ariete (LSFITGY)"),
    "ItalyTankArieteC1": ("LSFITGY", "Ariete C1 uses the same donor Ariete hull"),
    # Turkey
    "TurkeyTankLeopard2A4": ("LSFB2A6", "Turkish Leopard 2A4 uses donor 2A6 hull (no Altay/Leo2A4-named W3D)"),
    "TurkeyVehicleKorkut": ("LSFLIEBAO", "Korkut is a tracked SPAAG; Gepard-class LSFLIEBAO is the closest donor"),
    "TurkeyVehicleAltay": ("LSFBAO2", "No TURALTAY W3D in New Donor; Leopard 2 family LSFBAO2 is the realistic stand-in"),
    # Ukraine
    "UkraineTankT84": ("LSFPKT84", "Donor T-84 hull (LSFPKT84 / T84 textures)"),
    "UkraineVehicleBTR4": ("LSFIDBTR80", "No BTR-4 W3D; Indian/Soviet BTR-80 8x8 is closer than a Chinese ZBL hull"),
    "UkraineVehicleGepard": ("LSFLIEBAO", "Ukrainian Gepard uses the donor Gepard mesh"),
    # Sweden
    "SwedenTankStrv121": ("strv121", "Dedicated donor Strv 121"),
    "SwedenVehicleLvkv90": ("LSFlvkvA2", "Donor Lvkv 90 / lvkvA2 SPAAG"),
    "SwedenVehicleCV90AT": ("LSFCV90120", "Donor CV90 120mm"),
    "SwedenVehicleGiraffe": ("ARTHUR", "Donor ARTHUR artillery-hunting radar"),
    # India
    "IndiaTankArjun": ("LSFAQIONG", "Donor Arjun (阿琼 / LSFAQIONG)"),
    "IndiaVehicleAkash": ("LSFHQ9", "Akash is a truck/TEL SAM; donor HQ-9 is the closest SAM TEL (no Akash W3D)"),
    "IndiaVehicleTunguska": ("LSFIndia2C6", "Donor Indian 2S6 Tunguska"),
    "IndiaVehicleK9Vajra": ("LSFSKK55", "Donor K9 Vajra / K9 SPH"),
    "IndiaVehicleBMP2": ("LSFIDBMP2", "Donor Indian BMP-2 Sarath"),
    "IndiaVehicleKestrel": ("LSFIDBTR80", "8x8/BTR-class APC closer than BTR-90"),
    # Pakistan
    "PakistanTankAlKhalid": ("hld", "Donor MBT-2000 / Al-Khalid hull (hld)"),
    "PakistanTankAlZarrar": ("LSFAZL", "Donor Al-Zarrar"),
    "PakistanVehicleHQ9P": ("LSFHQ9", "Donor HQ-9 TEL"),
    # Saudi Arabia
    "SaudiArabiaTankM1A2": ("M1A2sudarb", "Donor Saudi M1A2 Abrams (M1A2sudarb)"),
    "SaudiArabiaVehiclePatriot": ("pac3_sudarb", "Donor Saudi Patriot PAC-3 TEL"),
    "SaudiArabiaVehiclePatriotBtry": ("pac3_sudarb", "Patriot battery uses the same Saudi PAC-3 donor"),
    "SaudiArabiaVehicleMPQ53": ("radarsude", "Donor Saudi air-defense radar van"),
    # UAE
    "UAETankLeclerc": ("LSFLKLR", "UAE Leclerc tropical uses donor Leclerc hull"),
    "UAEVehicleRabdan": ("LSFVBCI", "No Rabdan W3D; donor VBCI is a western 8x8 IFV (closer than a Chinese ZBL)"),
    "UAEVehiclePatria": ("LSFVBCI", "Patria / Rabdan APC uses donor 8x8 APC"),
    # South Africa
    "SouthAfricaTankOlifant": ("LSFhaojiao", "Donor Olifant (LSFhaojiao)"),
    "SouthAfricaVehicleRatel": ("LSFmihuan", "Donor Ratel (LSFmihuan)"),
    "SouthAfricaVehicleRooikat": ("LSFshanmao", "Donor Rooikat (LSFshanmao)"),
    "SouthAfricaVehicleRooikat76": ("LSFshanmao", "Rooikat 76 uses the same donor hull"),
}

# Already correct or no closer real mesh in New Donor.
KEEP_AS_IS = {
    "JapanTankType10": "Already LSFJapan10Tank",
    "JapanTankType90": "Already LSF90tank",
    "JapanVehicleType87": "Already LSFJP87V",
    "JapanVehicleType99": "Already LSFJP99",
    "JapanVehicleM270": "Already LSFJPM270",
    "SouthKoreaVehicleK21": "Already LSFK21",
    "SouthKoreaVehicleChunmoo": "Already KVChunmoo",
    "SouthKoreaTankK1A1": "Already LSFK1A1",
    "GermanyTankLeopard2A7": "Packed NAT_L2A7V is already the Specter Leopard 2A7",
    "GermanyVehicleIRIST": "Existing NAT_IRIST_SLX object reused; do not overwrite",
    "GermanyVehicleBoxer": "Already LSFBoxer",
    "FranceTankAMX30": "Already LSFAMX30",
    "FranceVehicleAMX10RC": "Already LSFamx10",
    "BritainTankChallenger2": "Already LSFChallenger2",
    "BritainVehicleWarrior": "Already LSFWarrior",
    "BritainVehicleAS90": "Already LSFAS90",
    "SwedenTankStrv122": "Already strv122",
    "SwedenVehicleCV90": "Already LSFCV90",
    "SwedenVehicleCV90R": "Already LSFCV90",
    "SwedenVehiclePatgb203": "Already PATGB203",
    "SwedenVehicleIRIST": "Existing IRIS-T object reused",
    "IndiaTankT90S": "Already IndiaT90S Bhishma",
    "UAEVehicleHIMARS": "Packed NAT_M142 is already HIMARS (no LSFUSAHIMARS W3D in archive)",
    "UAEVehiclePantsir": "Packed Arb_PantsirS1 is already Pantsir",
    "SaudiArabiaVehicleLAV25": "No LAV W3D; US_M1296 is the imported LAV/Stryker class",
    "SaudiArabiaVehicleLAV": "No LAV W3D; US_M1126 is the imported LAV APC class",
    "TurkeyVehicleBora": "No Bora W3D; LSFIskander remains the realistic ballistic TEL",
    "UkraineVehicleHrim2": "No Neptune / R-360 W3D; Hrim-2 stays Iskander-class ballistic TEL",
}

PROTECTED_SIDES = {
    "America",
    "USA",
    "Russia",
    "China",
    "PLA",
    "Iran",
    "Iraq",
    "Egypt",
    "Israel",
    "NorthKorea",
    "NATO",
    "Nato",
}

# Never overwrite these packed ART stems.
PROTECTED_ART_STEMS = {
    "us_m1a2sep2",
    "rus_t90a",
    "chi_ztz99a2",
    "irn_",
    "irq_t72m1",
}

SPECTER Iraq strategic TEL visibility ART fix

Install this _SPEC_ART_ONE.big over current live s ART.
Keep the current live s DATA (s-iraq-factory-commandset).
Do not replace DATA.

All 8 new Iraqi strategic TELs were invisible after construction
because cloned W3D HLod prototype names still said IRQ_9P117 /
IRQ_ABBAS_L / RUS_9K720K / IRQ_SARAB7 / IRQ_LAMIAA /
IRAQ_ALHUSAIN_L / RUS_RS24 while INI Model= used IQ_*TEL.
The engine looks up the model by HLod name, not filename.

This ART pack renames those HLod names to the IQ_* filename stems.
Donor W3Ds, shared atlases, factory flags, and DATA are unchanged.

Residual: 16-character damaged/hulk stems (IQ_AlHusseinTELD/R,
IQ_AlHijarahTELD/R, IQ_Ababil100TELD/R) cannot fit the 15-char
W3D HLod name field. Default constructed TEL and all projectile
models are <=15 and are patched. Damaged/hulk for those three
units may still fail to render without a DATA Model= rename.

Static validation only. The game was not launched in this environment.

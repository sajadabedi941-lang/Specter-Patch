SPECTER Iraq_VT72BCommandSet crash fix (DATA-only)

Install this complete replacement _SPEC_DATA_ONE.big over the
current live Al-Fahd500 DATA. Keep the existing Al-Fahd ART.

Root cause: slot 19 on Iraq_VT72BCommandSet overflows the ZH
CommandSet array (max 18). Factory construct moved to Worker
unused slot 12. Slots 1-18 and Clear Mines are unchanged.

Static validation only. The game was not launched.

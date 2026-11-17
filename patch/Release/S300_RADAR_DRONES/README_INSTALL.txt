SPECTER — Global Store S-300 + Radar Sarab_3/Lamina
===================================================

One installer. Two already-merged patches. Not two ZIPs inside a ZIP.

Lineage: radar-sarab-lamina-19 then gs-s300 (MIC shop files only).

Zero Hour was not run. Static INI/BIG validation only.

Install
-------
1. Close Zero Hour.
2. Unzip SPECTER_S300_RADAR_DRONES_INSTALL.zip next to generals.exe.
3. Run Install_S300RadarDrones.bat once.
4. Do not replace ART or 0_ overlays.

The BAT copies only DATA + CommandSet.ini + CommandButton.ini +
PlayerTemplate.ini. It refuses to run if ART is sitting next to it,
and it checks both GS S-300 and 19-country Radar markers before and
after copy.

SHA-256
-------
  DATA  aa40e6d1e68058becbe8d197a94c9ba05a5ef1af6bda25a14f5e82e9ea4ece53
  CS    13264095c91e610458e92bbc324aaa4d82d11bfdba597cd26cdf31d42e771213
  CB    1264aef1606ca9e6d1d68db0c211a793403d385417bc66238175c757f7350250
  PT    d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e
  ZIP   818f6f554565379e241a783bd9c1f308fc2aaded1d944d95059e47fe120c3474

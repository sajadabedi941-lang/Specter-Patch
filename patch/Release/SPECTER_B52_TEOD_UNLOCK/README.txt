SPECTER_B52_TEOD_UNLOCK
======================

AmericaJetB52 button unlock using the proven AmericaJetB2 force-unlock method.

Object: AmericaJetB52
Button: Command_ConstructTEODAmericaJetB52

CommandSet force-replace (base / _T / _T1 / _T2 / _T3):
  B-52 slots -> Command_ConstructTEODAmericaJetB52
  B-2 slot 5 kept as Command_ConstructTEODAmericaJetB2

Object unlock:
  Buildable = Ignore_Prerequisites  (Specter-proven B-2 value)
  Prerequisites empty
  KindOf without IGNORED_IN_GUI (SELECTABLE)

Removed gates:
  StrategyCenter / GeneralPromotion (SCIENCE_Rank*) / Science /
  RequiredObject / Prerequisites

Files:
  Data\INI\ZZZZZZZZ_ZZZ_USA_B52_FORCE_UNLOCK.ini
  Data\INI\ZZZZZZZZ_ZZZZ_USA_B52_BUTTON_UNLOCK.ini  (CI last-wins after RUNTIME)
  Data\INI\ZZZZZZZZ_ZZZZ_USA_AIRFIELD_B2_RUNTIME.ini (B-52 slots -> TEOD)

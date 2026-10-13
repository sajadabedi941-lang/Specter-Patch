# Global Store expansion to 19 countries

The existing Iraq Global Store (`Iraq_MIC`) is copied to 19 countries.
Group A replaces Strategy Center construction (MENA7 has no Strategy
Center; the empty country MIC / Global Market slot is the analogue).
Group B replaces C-RAM construction.

Name remains **Global Store**, cost **$7,000**, description title
**Global Aerospace Market**. Production slots 1–14 plus Sell at 15
are unchanged. The isolated `IQ__IQFlag_HsGM` flag cloth is scaled
1.25; War Factory / Command Center flags are untouched.

Units that required the replaced Strategy Center or MENA MIC are
retargeted to that country's Global Store so tech trees still unlock.
Strategy Center upgrades and C-RAM weapons are not merged into Global Store.
RUNTIME_TEST=NOT RUN

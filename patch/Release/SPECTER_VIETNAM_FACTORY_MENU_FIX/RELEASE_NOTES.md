# Vietnam missile factory menu fix

- Root cause: PR #626 left A-H and the Vietnam factory CommandSet only in satellite INI files.
- Live CommandSet.ini still constructed the shared Sell-only factory.
- Fix splices the chain into CommandSet.ini and CommandButton.ini, matching Iraq / WarFactory.
- ART, 9P117, Iraq A-M, Kashtan, Falaq, and Abbas Bio unchanged.
- Static validation only. Not in-game tested.

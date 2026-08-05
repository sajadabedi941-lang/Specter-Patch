SPECTER_B2_STABLE_MERGE
=======================

Purpose
-------
Named stable merge / release backup of the working USA B-2 Spirit state
after merging the B-2 working branch into the main patch line.

What is frozen in this backup
-----------------------------
- Object: AmericaJetB2
- Visual model: AVB3bmbr / AVB3bmbr_D / AVB3bmbr_D1
- Scale: 0.85 (final)
- B-1R separated (no US_B1R attach; BurnerFX hidden)
- Weapon stack unchanged (USA_B2_Spirit_BunkerBuster)
- AI / JetAIUpdate / locomotor unchanged (B-52 behavior stack)
- USA Airfield production works (Command_ConstructTEODAmericaJetB2)
- Buildable = Ignore_Prerequisites; empty Prerequisites; BuildCost 2500

Merge notes
-----------
- Working B-2 branch merged into main patch branch
- Conflicts resolved keeping the working B-2 / stubbed-AAB side
- No intentional gameplay, weapons, stealth, cost, AI, or balance edits
  in the merge/backup step itself

Install
-------
See INSTALL.txt

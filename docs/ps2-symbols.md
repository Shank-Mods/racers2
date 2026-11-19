# PS2 symbol name map

The North American PlayStation 2 release of LEGO Racers 2 (`SLUS_200.42`,
SHA-256 `4525f89a6a07c4c4a4af996cd279b1719b7179c679fd474f22b61f032a5bb810`)
shipped unstripped. It was built with Metrowerks CodeWarrior for PS2
(`MW MIPS C Compiler 2.4.1.01`) from the same codebase as the PC game; the PC
executable even contains the PS2 product codes (see the region flag at
application dispatch slot `0x7c`).

The ELF contains:

| Content | Count |
| --- | ---: |
| Named functions (`FUNC` symbols) | 5,367 |
| ...of which C++ methods (mangled, with parameter types) | 3,335 in 399 classes |
| Named global objects (`OBJECT` symbols) | 4,419 |
| Source files named by static-initialiser symbols | ~100 |
| Files with full debug info (`.debug`) | 2 (`Overlay\Font.cpp`, `Overlay\Loading Screens.cpp`) |

Original source paths have the form `E:\Dev\Lego Racers 2\Game Code\...`.
The executable itself is not part of this repository.

## Name map

[`research/ps2-symbols/ps2-name-map.csv`](../research/ps2-symbols/ps2-name-map.csv)
pairs **735 PC functions** with PS2 symbols. Each row gives the PC address,
the name currently used in this repository, the PS2 address and symbol, a
readable `Class::Method`, a confidence grade and the evidence.

These are **name suggestions, not applied renames**. No source is changed.

Coverage worth noting:

- 230 of the PC functions have no descriptive name yet.
- 28 of the 41 unfinished post-menu placeholders are identified, for example
  `RestartSecondaryRace` / `StartSecondarySessionRace` / `FinishSecondaryRace`
  = `cRaceManager::RestartRace` / `NextRace` / `QuitRace`, and
  `ConfigureControllerSelectionLayout` = `cGameManager::CreateInGameManagers`.
- Several current guesses differ from the originals, e.g.
  `SetControllerMenuMode` = `cLegoRacer::PlaySound` (four rare float constants)
  and `SelectControllerSceneRecord` = `cLegoRacer::CreateARacer` ("Player %d").

## Method

1. **References.** Every PS2 game function is decoded (a minimal MIPS decoder
   tracks `lui`/`addiu`/`ori` register values, loads and `mtc1`, since
   Capstone stops at EE-specific opcodes) and every PC function is
   disassembled. Each function's referenced strings and float constants are
   recorded. SDK/C-library names (`sce*`, `_*`, all-lowercase) are excluded.
2. **Anchors.** Pairs are scored by shared strings and constants weighted by
   rarity (anything used by more than four functions on either side is
   ignored). A pair is kept only if it is each side's best candidate, at least
   1.5x the runner-up, and shares a string or at least three rare constants.
   This gives 176 anchors.
3. **Call graph.** From matched pairs, unmatched callees are aligned when both
   sides have the same number of unmatched callees and every already-matched
   callee agrees; single unmatched callers are paired the same way. A pair needs
   an unambiguous vote, a free target and a loose size ratio (0.2–3.0).
   Iterated to convergence.

## Confidence and validation

| Grade | Pairs | Rule |
| --- | ---: | --- |
| high | 174 | anchored on a shared string or at least three rare constants |
| medium | 301 | other anchors; call-graph pairs with two or more votes or found in the first three rounds |
| low | 260 | later single-vote call-graph pairs, and any pair far from the rest of its class |

Two independent checks:

- **Class locality.** Methods of one PS2 class should land close together on
  PC. 3.3% of matched methods fall more than 32 KB from their class median;
  those are graded low.
- **Name agreement.** Where the repository already has a descriptive name, the
  PS2 name shares a word with it in 74% of high, 74% of medium and 74% of low
  pairs. Because near-certain string-anchored pairs agree at the same rate,
  most disagreement reflects differing names (`cFileCat` vs `FileManager`,
  `cLocalisationStringsManager` vs `LocalizedStringTable`) rather than wrong
  pairs. A manual spot check of low-grade pairs found most coherent and a few
  doubtful; treat the low grade as roughly 80–85% reliable.

The PS2 build is a different ISA, compiler and platform layer (`cPS2Renderer`,
`cPS2SoundInterface`), so the map helps naming and structure, not instruction
matching. Struct layouts are only available for the two files with debug info.

## Reproducing

With your own copy of the PS2 disc, extract `SLUS_200.42`, then:

```sh
sh tools/ps2/run.sh /path/to/SLUS_200.42 "../LEGO Racers 2/LEGO Racers 2.exe"
```

The script checks the ELF hash and needs Capstone (installed with reccmp). It
was run against the North American PC executable
(`074899f5...a748f168`), whose code layout matches the supported European one.

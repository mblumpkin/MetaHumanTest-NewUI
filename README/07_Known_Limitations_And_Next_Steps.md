# 07 — Known limitations and next steps

## Placeholder / sample data (works, but not real yet)
| What | Where it comes from now | How to make it real |
|---|---|---|
| Video cards | 5 sample moments copied from Figma (`CPP_UW_IHPCVideosRow` constructor) | `SetMoments` / `AddMoment` from your recording system |
| Graph lines | `GenerateDemoData` (smooth sample curves) | `SetSeries` with motion-capture / muscle data |
| Active Muscles list | 6 names from the level's Muscles folder | `SetActiveMuscles` |
| Severity values | 0.17 / 0.41 read off the Figma card ticks | your injury-risk calculation |

## Interpretations (decisions made where Figma did not say)
* **Saved Videos opens the analysis panel.** The panel shows saved clips, graphs and tagged points, and frame 5 shows
  it with the menu closed. Change with *Analysis Panel Tab* on `WBP_IHPC_HUD`.
* **Profile, Progress, History & Timeline, Settings** open an **empty** panel styled like Figma frame 5 "Rectangle 26"
  (step 4) — their content is not in the requested components. (The desktop frames on the same Figma page show
  sub-menus such as *Manage Information, MRI & Cam Scan, Timeline…*; they can be built inside `…Content` next.)
* **Close "X"** is not in Figma: it was designed to match the HUD (navy circle like the title bar, white rounded X like
  the menu arrow) and sits on the panel's rounded top-right corner, because inside the corner it would cover the
  "Show graphs" header of Component 3.
* **Every panel closes the nav bar** when it opens (before step 4 only Saved Videos did); the other tabs used to leave
  the menu open.
* **Switches = filters.** Figma draws all four switches off with all lines visible, so "none on" = show all; turning
  some on shows only those lines.
* **One accordion section open at a time** (keeps the panel within the screen; Figma shows one open).
* **Active Muscles / Tagged Points open state** is not designed in Figma; a simple list in the same style is used.
* **Zoom** shows a large Movement Graph in the empty viewer area; **Inspect** closes it (otherwise fires an event for a
  future 3D close-up).
* **Clicking a card / tagged point** pauses the avatar animation and jumps to the moment's time.
* **Title vertical position**: centred in the bar (the Figma frame includes an iPad status bar that PC builds do not have).

### Timeline (step 2)
* **Record does not write a video file.** It saves a *moment* ("Recording N": when it started on the animation and on
  the clock) as a new Saved Videos card, Tagged Point and marker. Capturing real video needs Take Recorder / Movie
  Render Queue hooked into *On Recording Saved* ([05](05_How_To_Change_Things.md)). New clips get severity 0 (no analysis).
* **Fast-forward = jump to the next marker** (the icon is ▷|, "skip next"); with no marker ahead it jumps to the end.
  **Restart** = jump to the start.
* **Markers** = saved videos + recordings + bookmarks made in this session. Bookmarks are not saved between sessions yet.
* **Scrubbing pauses** while you drag and resumes afterwards if it was playing.
* **Position**: centred at the bottom in step 2; since step 3 it is 125 px left of centre like Figma, beside the new layer
  switcher.
* The **prototype timeline** (`WB_AmationTimeline`, `WCPP_AnimationTimeline`) is still in the project, just not created.

### Layer switcher (step 3)
* **UI only — the real layers are a teammate's work.** The buttons drive the placeholder's existing opacity code (the
  `Fade` material parameter + skeleton alignment + hair strands/cards). There is **no muscle layer yet**, so **Muscles**
  just sets Fade 0.5 (body half see-through) as a stand-in; change `MusclesFade` or use *On Layer Changed* when the muscle
  layer exists. The placeholder's Muscle and Skeleton buttons had no code, its MetaHuman button set Fade 0.2 — that is
  now the **Skeleton** button.
* **Body = Fade 1.0.** Going back to Body makes the body fully visible again (like dragging the old slider to the top);
  the skeleton stays where the teammate's code placed it, just hidden inside the body.
* **Skeleton selected look** is not drawn in Figma; it was made in the same style as the other selected buttons
  (dark glossy circle + white icon).
* **Orange badge** on the skeleton button (in Figma) is **hidden** at the team's request — it had no meaning yet. It can
  be turned back on with *Show Skeleton Badge* / `SetSkeletonBadgeVisible`.
* **The slider is gone.** The placeholder had a vertical slider for any opacity value; the Figma design has only the
  three buttons, so the slider is kept but hidden (the parent class needs it). Make it visible in
  `WBP_IHPC_LayerSwitcher` if you want fine control back.
* **Safety guard:** if the possessed pawn has no meshes tagged `WholePart` / `SkeletonPart` / `FacePart`, the buttons only
  change their highlight and log a warning, instead of crashing like the placeholder would.
* **Narrow windows:** the timeline (1048 px) and switcher (204 px) need about 1370 px of width side by side, like the
  1366 px Figma frame; in a narrower game window they overlap the screen edges.
* The placeholder `WB_AnatomyViewSwitcher` (`/Game/Widget`) is still in the project, just not created.

## Visual differences from Figma
* **Font**: Avenir (already in the project) instead of Inter. See [05](05_How_To_Change_Things.md) to switch.
* **Charts**: drawn live instead of the Figma chart picture — same layout, axes and label style, real data lines.
* **Frosted-glass blur** is not used (Figma panels here are plain semi-transparent fills, which match).
* The first card starts 24 px in and the row clips at that edge (Figma clips at the row edge).

## Things noticed in the existing project (not changed)
* Play-In-Editor logs `CommonUI without a CommonGameViewportClient` and two Game Features / OpenXR errors — these were
  there before and do not affect this UI.
* `CPP_UW_AnatomyViewSwitcher.cpp` has three `double → float` truncation warnings (lines 164, 182, 202).
* The older `WBP_Header` draft (`Content/UserInterface/Widgets`) is no longer created by the level; delete it if not needed.
* The project folder is also a Perforce workspace; the Unreal editor's Perforce session had expired ("Your session has
  expired, please login again") during this work.

## Actions / characters (2026-11-08)

* **Grant** is not assembled yet: `MHC_Grant` has no texture sources and downloading them needs the MetaHuman cloud
  login. After logging in: `tools/ue/add_metahuman_pawn.sh Grant /Game/MadisonTesting/GrantMHCharacter/MHC_Grant`
  (MetaHuman-Anatomy-IHPC repo).
* The mocap action clips play as recorded: Running faces the camera, the pelvis drifts up to ~1 m before the loop.
* Deep, wide stances stretch an inner-thigh muscle (weights transferred from Abby's body).

## Suggested next steps
1. Connect real saved videos (recording → `AddMoment`).
2. Feed real motion data into the graphs (`SetSeries`) and make the **Download** export that data.
3. Build the Profile / Progress / History & Timeline / Settings screens (Figma desktop frames show their sub-menus).
4. Use the empty viewer area for a 3D close-up (e.g. a Scene Capture of the avatar) and hook it to **Inspect**.
5. Optionally switch to the Inter font.
6. Timeline: capture real video when recording (Take Recorder / Movie Render Queue on *On Recording Saved*), keep
   bookmarks between sessions, and run the injury-risk analysis on new clips to give them a real severity.
7. Layer switcher: when the muscle layer is ready, set the real behaviour for **Muscles** (and Body / Skeleton if they
   change) — either new Fade values in Class Defaults or a handler on *On Layer Changed*.

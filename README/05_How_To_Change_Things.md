# 05 — How to change things

## Change a colour, font, text, size or position
Open the Widget Blueprint in `Content/UserInterface/IHPC/Widgets`, select the widget in the **Hierarchy**, change it in
**Details**, **Compile**, **Save**. Keep the names marked (C++) in [04](04_Widget_Blueprints.md).

* Tab fonts / colours: open `WBP_IHPC_NavTab` → **Class Defaults** → *IHPC | Style*.
* Chevron colours / arrows: `WBP_IHPC_HUD` → Class Defaults → *IHPC | Style*.
* Accordion chevrons / list font: `WBP_IHPC_GraphAccordion` → Class Defaults.

## Switch the font to Inter (like Figma)
1. Download Inter (free, OFL licence) and drag `Inter-Medium.ttf` and `Inter-Bold.ttf` into the Content Browser
   (e.g. `/Game/UserInterface/IHPC/Fonts`). Answer **Yes** when Unreal asks to create a Font asset.
2. Replace the Avenir font in the TextBlocks and in the Class Defaults listed above
   (Avenir Medium → Inter Medium, Avenir Heavy → Inter Bold). Sizes stay the same.

## Make a different tab open the analysis panel
`WBP_IHPC_HUD` → Class Defaults → **Analysis Panel Tab**.

## Add a screen for Profile / Progress / History & Timeline / Settings
Each of these tabs already opens its own empty panel (styled like Figma "Rectangle 26") with the close "X" — opening /
closing is handled by C++. To fill one:
1. Open `WBP_IHPC_HUD`, find e.g. `ProfilePanel` → **`ProfileContent`** (an empty Canvas Panel, 1217 × 798).
2. Drop your widgets (or your own Widget Blueprint for the screen) inside `ProfileContent`. Keep the top-right corner
   free for the X.
3. Keep the names `ProfilePanel` / `ProgressPanel` / `HistoryTimelinePanel` / `SettingsPanel` (C++ shows/hides them).
To react in Blueprint as well, use the HUD's **On Tab Changed** event.

## The close "X"
* **Look**: `WBP_IHPC_HUD` → `PanelCloseButton` → Style (Normal / Hovered / Pressed brushes); the X picture is
  `PanelCloseIcon` (`T_IHPC_Close`, made by `make_close_icon()` in `make_ui_textures.py`).
* **Position**: `PanelCloseButton`'s slot (anchored top-centre; x 600, y 175.5 = the panel's top-right corner). If you move
  or resize the panels, move it with them.
* **Close from code / a key**: call **Close Panel** on the HUD (`GetMainHUD()->ClosePanel()` from the player controller).
  **Is Any Panel Open** tells you whether one is showing.

## Show real saved videos instead of the sample cards
From Blueprint or C++, build an array of **IHPC Tagged Moment** (Title, Date Text, Time Text, Severity 0–1, Normalized
Time 0–1) and call **Set Moments** on the videos row (get it from the analysis panel's `VideosRow`). The Tagged Points
list is filled from the same data when the panel is constructed; call **Set Tagged Points** on the accordion if you
change the data later. **Add Moment** appends one card (e.g. after a new recording).

## Show real graph data
Call **Set Series** on `MovementGraph` / `ActiveMusclesGraph` (array of **IHPC Graph Series**: Name, Line Color,
Legend Color, Values, Visible). Keep the order Bones, Nerves, Muscles, Tendons so the switches still match. Values are
evenly spaced across the width; adjust **Min Value / Max Value / Value Ticks** if your data uses a different range. Set
**Generate Demo Data If Empty** off to stop sample curves appearing.

## Show real active muscles
Call **Set Active Muscles** on the accordion with an array of names.

## Timeline / playback bar
* **Speeds** the slow/fast buttons step through: `WBP_IHPC_Timeline` → Class Defaults → *Speed Steps*; starting speed =
  *Default Speed Index*.
* **Don't start playback when recording starts**: untick *Play When Recording Starts*.
* **Names of new clips/bookmarks**: *Recording Title Format* / *Bookmark Title Format* (`{0}` = the number).
* **Move the bar** (now 125 px left of centre like Figma, beside the layer switcher): select `Timeline` in `WBP_IHPC_HUD`
  and change its position / anchors. If you change the track length inside `WBP_IHPC_Timeline`, set *Track Length* to match.
* **Make fast-forward something else** (e.g. skip 5 seconds, or play at 4×): change
  `UCPP_UW_IHPCTimeline::FastForwardToNextMarker` (C++), or bind your own logic to the button in the Blueprint.
* **Save real video files when recording**: hook into *On Recording Saved* (HUD/Timeline) or extend
  `UCPP_UW_IHPCTimeline::ToggleRecording` — for example start/stop a Take Recorder or Movie Render capture there.
* **Get the old prototype timeline back**: `BP_PlayerController` → Class Defaults → *Timeline Widget Class* =
  `WB_AmationTimeline` (and delete `Timeline` from `WBP_IHPC_HUD` so there are not two).

## Actions menu (Running / Tennis Forehand / Soccer Warmup)

* The 4th tab is labelled **Actions** (`Tab_HistoryTimeline` → `HistoryTimelinePanel` → `ActionsList`).
* **Add an action:** duplicate a button in `ActionsList`, name it `Action_<Name>` (e.g. `Action_Squat`), change its
  label. No C++ change: `UCPP_UW_IHPCHud` binds every Button whose name starts with `Action_` (*Action Button Prefix*).
  Then give each pawn a clip: pawn Blueprint → *AnimationTimelineComp* → *Action Clips* → key `<Name>` → the clip
  (Abby8: a clip on Abby's skeleton; Beau / Madi / Grant: the clip retargeted to `metahuman_base_skel`).
* *Close Actions Panel On Select* (HUD Class Defaults) closes the panel after a pick; *Action Selected Color* is the
  playing action's fill. Clicking the playing action again returns to walk / jog / run.
* From Blueprint / C++: `GetMainHUD()->SelectAction("Running")`, or directly on the pawn's
  `UAnimationTimelineComp::PlayAction` / `StopAction`.

## Layer switcher (Body / Muscles / Skeleton)

> **2026-11-08:** the buttons go to fixed *skin amounts* — Body **1.0**, Muscles **0.5**, Skeleton **0.0**
> (`BodySkinAmount` / `MusclesSkinAmount` / `SkeletonSkinAmount` in `WBP_IHPC_LayerSwitcher` Class Defaults; reveal
> depth = 1 − amount). Untick *Use Skin Amounts* to jump to the named layers' own depths instead.
* **What each button does**: `WBP_IHPC_LayerSwitcher` → Class Defaults → *IHPC | Layers* → **Body Fade** (1.0),
  **Muscles Fade** (0.5), **Skeleton Fade** (0.2). The value goes to the avatar's `Fade` material parameter through the
  teammate's `CPP_UW_AnatomyViewSwitcher` code (below 0.9 the hair also switches to cards).
* **Hook up the real layers** (e.g. show the muscle mesh): in the Widget Blueprint's Event Graph add **On Layer Changed**
  (*IHPC | Events*) and switch on `Layer`; or in C++ bind `OnLayerChanged`. Call **Select Layer** to change layer from
  anywhere (keyboard shortcut, tutorial…), **Get Selected Layer** to read it.
* **Which button is selected at start**: *Default Layer*. Tick *Apply Default Layer On Start* to also apply its Fade.
* **Orange badge on Skeleton**: hidden now. To show it again tick *Show Skeleton Badge* (Class Defaults), or call
  **Set Skeleton Badge Visible** at runtime (e.g. to flag something new).
* **Move it**: select `LayerSwitcher` in `WBP_IHPC_LayerSwitcher` and change its position (anchored bottom-centre,
  now x 533, y -45). The timeline's position is in `WBP_IHPC_HUD` → `Timeline`.
* **Bring back the opacity slider**: set `AnatomyViewSwitcher_Slider` to *Visible* and give it a position/size; it already
  drives the avatar like the old placeholder slider.
* **Go back to the placeholder**: `BP_PlayerController` → Class Defaults → *Anatomy View Switcher Widget Class* =
  `WB_AnatomyViewSwitcher`.
* **New pictures** (e.g. after the Figma file changes): re-download `ihpc ui rttd 2` into
  `SourceArt/Figma/Original/layers_f1_raw_1.png` (frame 1) / `layers_f4_raw_1.png` (frame 4), run
  `make_ui_textures.py`, then `ue_import_textures.py`.

## Icons look blurry / pixelated
Open the texture in `/Game/UserInterface/IHPC/Textures`: keep **Mip Gen Settings = Simple Average** (or *Sharpen 1–3* for
crisper) and **Filter = Trilinear**. *No Mipmaps* makes icons that are drawn smaller than the texture look jagged.

**Ragged light/dark rim around a button or icon** = the colour stored in its invisible pixels is leaking into the edge
when Unreal shrinks it. Always make textures with `make_ui_textures.py` (its last step, `bleed_all_outputs()`, fixes
this for every PNG); if you add a PNG made elsewhere, put it in `SourceArt/Figma/UE/` and re-run the script before
importing, or run `bleed_transparent_edges()` on it.

## The HUD and the player controller
* **Which HUD / its draw order**: `BP_PlayerController` → Class Defaults → *UI* → **Main HUD Widget Class** /
  **Main HUD Z Order** (10 = above the other widgets).
* **Reach the HUD from the controller** (e.g. a key that opens the panel): in C++ `GetMainHUD()->SelectTab(EIHPCNavTab::SavedVideos)`;
  in Blueprint *Get Main HUD* → *Select Tab*. Other useful HUD calls: *Toggle Nav Bar*, *Set Analysis Panel Open*.

## React to clicks in Blueprint
All events are under *IHPC | Events* on the widgets: `On Tab Changed`, `On Moment Selected`, `On Tagged Point Clicked`,
`On Graphs Exported`, `On Zoom Requested`, `On Inspect Clicked`, and on the timeline `On Recording Saved`,
`On Bookmark Added`, `On Marker Clicked`, `On Speed Changed`, and on the layer switcher `On Layer Changed`.

## Change where the CSV goes / its format
`UCPP_UW_IHPCGraphAccordion::ExportGraphsToCSV` in `Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp`.

## After the Figma file changes
1. Download the changed assets into `SourceArt/Figma/Original/` (same names).
2. `python -I Tools/FigmaUI/make_ui_textures.py` (from the project folder).
3. Import: in Unreal **Tools → Execute Python Script…** → `Tools/FigmaUI/ue_import_textures.py` (replaces the textures).
4. Update numbers in the Widget Blueprints by hand, using [02](02_Figma_To_Unreal_Map.md) as the checklist.

## Editing the C++
Close Unreal (Live Coding is on, so command-line builds are blocked while it is open), then build:
```
"C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" MetaHumanTestEditor Win64 Development "-Project=<project folder>/MetaHumanTest.uproject" -WaitMutex
```
or open `MetaHumanTest.sln` and build **Development Editor**. Small changes inside existing functions can also be
applied with Live Coding (Ctrl+Alt+F11) while the editor is open; adding new classes or `UPROPERTY`s needs a full build.

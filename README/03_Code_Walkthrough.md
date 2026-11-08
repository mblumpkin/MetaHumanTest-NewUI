# 03 — Code walkthrough (every file, every function)

All new C++ lives in `Source/MetaHumanTest/Public/IHPC_UI/` (headers) and `Source/MetaHumanTest/Private/IHPC_UI/`
(code). Every file also has comments inside it; this page explains the same code in plain language, in the order the
pieces depend on each other. Line links point at the version on GitHub.

- [Unreal ideas used everywhere](#unreal-ideas-used-everywhere)
- [Build.cs change](#buildcs-change)
- [IHPCTypes.h — shared data](#ihpctypesh--shared-data)
- [IHPCUILibrary — helpers](#ihpcuilibrary--helpers)
- [CPP_UW_IHPCToggleSwitch — Component 4](#cpp_uw_ihpctoggleswitch--component-4)
- [CPP_UW_IHPCNavTab — one tab](#cpp_uw_ihpcnavtab--one-tab)
- [CPP_UW_IHPCLineGraph — live graph](#cpp_uw_ihpclinegraph--live-graph)
- [CPP_UW_IHPCListRow — list rows](#cpp_uw_ihpclistrow--list-rows)
- [CPP_UW_IHPCGraphAccordion — Component 3](#cpp_uw_ihpcgraphaccordion--component-3)
- [CPP_UW_IHPCVideoCard — one card](#cpp_uw_ihpcvideocard--one-card)
- [CPP_UW_IHPCVideosRow — videos row](#cpp_uw_ihpcvideosrow--videos-row)
- [CPP_UW_IHPCAnalysisPanel — the panel](#cpp_uw_ihpcanalysispanel--the-panel)
- [CPP_UW_IHPCHud — title bar, menu, tabs](#cpp_uw_ihpchud--title-bar-menu-tabs)
- [CPP_UW_IHPCTimeline — playback / timeline bar](#cpp_uw_ihpctimeline--playback--timeline-bar) *(added in step 2)*
- [CPP_UW_IHPCLayerSwitcher — Body / Muscles / Skeleton buttons](#cpp_uw_ihpclayerswitcher--body--muscles--skeleton-buttons) *(added in step 3)*
- [CPP_PlayerController — creates the HUD](#cpp_playercontroller--creates-the-hud) *(existing file, small addition)*
- [What happens when you click…](#what-happens-when-you-click)

---

## Unreal ideas used everywhere

| Code | Meaning |
|---|---|
| `UCLASS()` / `GENERATED_BODY()` | Registers the class with Unreal so Blueprints, the editor and saving know about it. |
| `UCLASS(Abstract)` | You cannot place the C++ class itself — you make a Widget Blueprint *child* of it (where the look is built). |
| `class ... : public UUserWidget` | Every widget here is a "User Widget" — the same thing a Widget Blueprint is. |
| `UPROPERTY(EditAnywhere, ...)` | A setting that shows up in the Blueprint's **Details** panel (Class Defaults). |
| `UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> TabButton;` | "The Widget Blueprint **must** contain a Button called `TabButton`; give me a pointer to it." If the name is wrong the Blueprint will not compile. `BindWidgetOptional` = may be missing. |
| `UFUNCTION(BlueprintCallable)` / `BlueprintPure` | The function can be called from Blueprint graphs (Pure = no side effects, no exec pin). |
| `DECLARE_DYNAMIC_MULTICAST_DELEGATE...` + `UPROPERTY(BlueprintAssignable)` | An **event** other code/Blueprints can listen to (`OnTabClicked`, `OnMomentSelected`...). `Broadcast(...)` fires it. |
| `Button->OnClicked.AddUniqueDynamic(this, &Class::Handler)` | "When this button is clicked, call my `Handler`." *Unique* = never bind twice. Handlers must be `UFUNCTION()`. |
| `NativePreConstruct()` | Runs in the **UMG designer** *and* in game → used to make the designer preview look right. |
| `NativeConstruct()` | Runs once when the widget appears in game → used to bind events and set the starting state. |
| `NativeTick()` | Runs every frame while the widget is on screen. |
| `ESlateVisibility::Visible / Collapsed / Hidden / HitTestInvisible / SelfHitTestInvisible` | Visible = drawn + clickable. Collapsed = gone, takes no space. Hidden = invisible but keeps its space. HitTestInvisible = drawn, clicks pass through it and its children. SelfHitTestInvisible = clicks pass through it but its children can still be clicked. |
| `LOCTEXT("Key", "Text")` | Text that can be translated later. |

---

## Build.cs change

[`MetaHumanTest.Build.cs`](../Source/MetaHumanTest/MetaHumanTest.Build.cs) — adds `"UMG", "Slate", "SlateCore"` to
`PrivateDependencyModuleNames`. UMG gives the widget classes (Button, TextBlock…); Slate/SlateCore give the low-level
drawing used by the line graph (lines, text measuring).

---

## IHPCTypes.h — shared data

[`Public/IHPC_UI/IHPCTypes.h`](../Source/MetaHumanTest/Public/IHPC_UI/IHPCTypes.h) contains only data definitions:

* **`EIHPCNavTab`** — `None, Profile, Progress, SavedVideos, HistoryTimeline, Settings`. Each nav tab has one of these as
  its id; the HUD uses it to know which tab was clicked.
* **`EIHPCAnatomyLayer`** *(step 3)* — `Body, Muscles, Skeleton`: the three layer-switcher buttons.
* **`EIHPCAccordionSection`** — `None, ShowGraphs, ActiveMuscles, TaggedPoints` (which accordion section is open).
* **`FIHPCTaggedMoment`** — one saved video / tagged point: `Title`, `DateText`, `TimeText`, `Severity` (0..1 → tick
  position on the green-red bar), `NormalizedTime` (0..1 → where on the animation the moment is). It has a constructor
  so sample data can be written in one line.
* **`FIHPCGraphSeries`** — one line on a graph: `Name`, `LineColor`, `LegendColor`, `Values` (the numbers, evenly spaced
  left → right) and `bVisible`.
* **`FIHPCSimpleEvent`** (no data) and **`FIHPCMomentEvent`** (carries one `FIHPCTaggedMoment`) — event types several
  widgets share.

---

## IHPCUILibrary — helpers

[`Public/IHPC_UI/IHPCUILibrary.h`](../Source/MetaHumanTest/Public/IHPC_UI/IHPCUILibrary.h),
[`Private/IHPC_UI/IHPCUILibrary.cpp`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp).
A `UBlueprintFunctionLibrary` = a bag of static functions, also callable from any Blueprint.

* [`FindAvatarTimeline`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L9) — gets player 0's pawn
  (`UGameplayStatics::GetPlayerPawn`) and returns its `UAnimationTimelineComp` (the existing component that drives the
  avatar animation scrubbing), or `nullptr` if there is none.
* [`SeekAvatarTimeline`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L17) — finds the timeline; if missing,
  logs a warning and returns `false`. Otherwise calls `Pause()` (so playback does not immediately move away) and
  `SetNormalizedTime(time clamped to 0..1)`.
* [`GetAvatarTimelineTime`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L35) — returns
  `GetNormalizedTime()` or `-1` when there is no timeline (the graphs hide their playhead on `-1`).
* [`FigmaColor`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L120) — `"B3CA7F"` → `FColor::FromHex` →
  `FLinearColor` (this conversion turns sRGB into linear, which is what Unreal draws with) → sets the alpha.
* [`SeverityToColor`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L129) — four colour stops sampled from the
  Figma card bar (green `70BF44` at 0, yellow `F2DE1C` at .45, orange `F7A21F` at .75, red `ED1C24` at 1). Finds the two
  stops around the value and blends them (`LerpUsingHSV`). Used for the dots in the Tagged Points list.

*Added with the timeline (step 2):*
* [`PlayAvatar`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L41) — if the animation is at the end
  (≥ 0.999) and `bRestartIfAtEnd`, jump to 0 first; then `PlayForward()`.
* [`PauseAvatar`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L57) — `Pause()`.
* [`IsAvatarPlaying`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L68) — reads the component's public
  `bIsPlaying`.
* [`SetAvatarPlaySpeed`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L74) /
  [`GetAvatarPlaySpeed`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L87) — write / read the component's
  public `PlaySpeed`, which `UAnimationTimelineComp::TickComponent` multiplies into every frame's progress, so it takes
  effect immediately (minimum 0.01; `-1` returned when there is no timeline).
* [`FormatFigmaDate`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L93) — `"Jan 4th, 2026"`: month
  abbreviation + day + st/nd/rd/th (11th–13th are always "th") + year.
* [`FormatFigmaTime`](../Source/MetaHumanTest/Private/IHPC_UI/IHPCUILibrary.cpp#L113) — `"13:55 p.m."`: 24-hour time with
  a.m./p.m., exactly the Figma card style.

---

## CPP_UW_IHPCToggleSwitch — Component 4

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCToggleSwitch.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCToggleSwitch.cpp)

* Needs a CheckBox named **`SwitchCheckBox`** (its style = the two toggle textures, set in the Blueprint).
* `bStartsOn` — starting state. `OnToggled(Switch, bIsOn)` — event fired when the user flips it (passes itself so one
  handler can serve the four switches).
* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCToggleSwitch.cpp#L7) — `SetIsChecked(bStartsOn)`
  so the designer shows the right state.
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCToggleSwitch.cpp#L18) — binds the CheckBox's
  `OnCheckStateChanged` to `HandleCheckStateChanged`.
* [`SetIsOn(bOn, bBroadcast)`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCToggleSwitch.cpp#L28) — change it from
  code; `SetIsChecked` does not fire the CheckBox event, so `bBroadcast` lets the caller decide whether to fire `OnToggled`.
* [`IsOn`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCToggleSwitch.cpp#L40) — current state.
* [`HandleCheckStateChanged`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCToggleSwitch.cpp#L45) — re-broadcasts as
  `OnToggled(this, bIsChecked)`.

---

## CPP_UW_IHPCNavTab — one tab

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCNavTab.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp)

* Needs a Button **`TabButton`** containing a TextBlock **`TabLabel`**.
* Settings: `TabId`, `Label`, `NormalFont`, `HighlightFont`, `HighlightScale` (1.2 = 24/20 px), `NormalColor` (white),
  `HighlightColor` (`#B3CA7F`). Event: `OnTabClicked(TabId)`.
* [`SetTabIdAndDefaultLabel`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp#L8) — called by the HUD: sets
  the id, and the label only if the designer did not type one.
* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp#L21) — if no fonts were chosen, use
  the TextBlock's font for both; show the label; set the scale pivot to the centre (so the text grows evenly); apply the
  look.
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp#L46) — binds the button's `OnClicked`,
  `OnHovered`, `OnUnhovered`.
* [`SetSelected`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp#L59) — remembers selection, refreshes look.
* [`HandleClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp#L65) — fires `OnTabClicked(TabId)`;
  the tab itself does not decide what selection means — the HUD does.
* [`HandleHovered` / `HandleUnhovered`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp#L70) — remember the
  hover state, refresh.
* [`RefreshVisuals`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCNavTab.cpp#L82) — highlight = selected **or**
  hovered → highlight font, green colour, 1.2× render scale; otherwise normal font, white, 1×. Using a *render* scale
  (not a bigger font) means the tab's layout size never changes, so the other tabs do not jump.

---

## CPP_UW_IHPCLineGraph — live graph

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCLineGraph.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp)

Replaces the chart *pictures* in Figma with a real graph so the switches, export and playhead can work. It has no
Widget Blueprint — it draws itself in `NativePaint`. Put it in a box with a size (it has no natural size).

Settings: `Series`, `bGenerateDemoDataIfEmpty`, `DemoSeed`, `MinValue`/`MaxValue` (−1.2 / 0.7), `ValueTicks`
(.5, 0, −.5, −1), `PlotPadding` (room for labels), colours, `LabelFont`, `LineThickness`, `bShowPlayhead`, `PlayheadColor`.

* [Constructor](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L16) — default label font = Unreal's
  built-in Roboto 8 (`ConstructorHelpers::FObjectFinder` loads it once; skipped on dedicated servers).
* [`MakeDefaultSeriesLayout`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L28) — the four lines from
  the Figma legend: Bones, Nerves, Muscles, Tendons. Legend colours are the exact Figma colours; line colours are brighter
  versions so they read on the dark panel.
* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L53) — no data + demo allowed →
  `GenerateDemoData(DemoSeed)` (so the designer shows curves too).
* [`SetSeries`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L64) /
  [`SetSeriesVisible`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L69) — replace all data / show or
  hide one line by index.
* [`GenerateDemoData`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L77) — remembers each line's
  visibility, rebuilds the 4-line layout, and for each line makes a seeded random stream (same seed → same curve every
  time), picks 3 frequencies + 3 phases + an offset, and fills `NumSamples` values with the sum of three sine waves
  (= a smooth organic line), clamped inside the axis range. Restores visibility.
* [`ValueToY`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L121) — maps a value to a pixel row
  (screen Y grows downward, values grow upward → `1 - alpha`).
* [`FormatTick`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L128) — whole numbers as `"0"`,
  `"-1"`; halves as `".5"`, `"-.5"` (Figma style, no leading zero).
* [`NativePaint`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLineGraph.cpp#L146) — called every frame to draw:
  1. Works out the plot rectangle from the widget size minus `PlotPadding`; gives up if smaller than 20 px.
  2. Prepares a `DrawLine` helper (`FSlateDrawElement::MakeLines`, anti-aliased) that also applies the widget's opacity.
  3. **Grid**: a faint horizontal line at every value tick + 4 faint vertical lines (5 columns).
  4. **Axes**: left and bottom lines (1.5 px) + small tick marks on the bottom axis.
  5. **Labels**: measures each tick text (`FontMeasure->Measure`) so it can be right-aligned against the axis, then draws
     it with `MakeText`.
  6. **Data lines**: for each visible series with ≥ 2 values, converts every value to a point and draws one polyline.
  7. **Playhead**: if a time ≥ 0 was given, a vertical green line at that fraction of the width.
  Each step uses a higher *layer* number so later things draw on top. Returns the top layer used.
* `SetPlayheadTime(t)` (header) — the accordion/panel call this every frame with the timeline position.

---

## CPP_UW_IHPCListRow — list rows

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCListRow.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCListRow.cpp)

Figma only shows the Active Muscles / Tagged Points sections *closed*, so this is a simple on-style row:
`[coloured dot]  Primary text ……… secondary text`. It builds its own widgets in code.

* [`MakeRoundedBrush`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCListRow.cpp#L14) — a brush that draws a
  rounded rectangle in one colour.
* [`BuildTreeIfNeeded`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCListRow.cpp#L29) — if not built yet: creates a
  flat Button (invisible normally, faint white rounded box on hover/press) as the root; inside it a Horizontal Box with a
  8 × 8 dot (Size Box + Border), the primary TextBlock (fills the row) and the secondary TextBlock (right side); binds
  the button click.
* [`Setup`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCListRow.cpp#L87) — fills the texts and fonts (secondary is
  3 pt smaller, 65% white, hidden if empty), colours the dot, and makes the row ignore the mouse if it is not clickable.
* [`RebuildWidget`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCListRow.cpp#L113) — makes sure the tree exists before
  Unreal turns the widget into its on-screen form.
* [`HandleClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCListRow.cpp#L119) — fires `OnRowClicked(this)`;
  the owner reads `RowIndex` to know which item it was.

---

## CPP_UW_IHPCGraphAccordion — Component 3

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCGraphAccordion.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp)

Required widgets: `Header_ShowGraphs/ActiveMuscles/TaggedPoints` (Buttons), `Chevron_*` (Images), `Content_*` (panels),
`MovementGraph`, `ActiveMusclesGraph`, `Toggle_Bones/Nerves/Muscles/Tendons`, `DownloadButton`, `ZoomButton`,
`ActiveMusclesList`, `TaggedPointsList` (Vertical Boxes).
Settings: `StartOpenSection`, `bSeekTimelineOnTaggedPointClick`, `ChevronUpTexture`, `ChevronDownTexture`, `ListFont`,
`ActiveMuscles`. Events: `OnZoomRequested`, `OnGraphsExported(FilePath)`, `OnTaggedPointClicked(Moment)`.

* [Constructor](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L23) — fallback list font; six sample
  muscle names that exist in the level's Muscles folder.
* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L48) — shows the starting
  section and the muscles list in the designer.
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L58) — binds the 3 headers,
  download, zoom and the 4 switches; if both graphs use the same seed, gives the second one a different seed; then opens
  the starting section, applies the switch filter and builds both lists.
* [`NativeTick`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L93) — while "Show graphs" is open,
  pushes the timeline position into both graphs' playheads every frame.
* [`OpenSection` / `ToggleSection` / header handlers](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L110)
  — open one section (closing the others); clicking the open one closes it.
* [`RefreshSections`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L125) — for each section: open →
  content visible + up chevron; closed → content collapsed + down chevron.
* [`GetToggles`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L154) — the 4 switches in the same
  order as the graph lines (Bones, Nerves, Muscles, Tendons).
* [`ApplyToggleFilter`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L165) — any switch on? For
  each line: show it if no switch is on, or if its own switch is on. Applies to both graphs.
* [`HandleDownload` / `HandleZoom`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L188) — export /
  fire `OnZoomRequested` (the panel shows the big graph).
* [`ExportGraphsToCSV`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L198) — makes
  `Saved/IHPC_Exports/`, builds a file name with the date and time, writes a header row
  (`Graph,Sample,NormalizedTime,Bones,Nerves,Muscles,Tendons`) then one row per sample for each graph, saves it, logs the
  path, puts the path in the download icon's tooltip and fires `OnGraphsExported`. Returns the path (empty on failure).
* [`SetActiveMuscles` / `SetTaggedPoints`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L267) —
  store new data and rebuild the matching list.
* [`RebuildActiveMusclesList`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L285) — clears the
  list and adds one non-clickable row per muscle (dot = brightened "Muscles" legend colour).
* [`RebuildTaggedPointsList`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L306) — one clickable
  row per moment: title, time, severity-coloured dot; listens to the row click.
* [`HandleTaggedPointRowClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L329) — looks up
  the moment by the row's index, jumps the avatar timeline there (if enabled) and fires `OnTaggedPointClicked`.

---

## CPP_UW_IHPCVideoCard — one card

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCVideoCard.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideoCard.cpp)

Required: `CardButton`, `TitleText`, `DateText`, `TimeText`, `SeverityTick`; optional `SelectionHighlight`.
Settings: `Moment` (preview data), `TickTravelWidth` (237 = 240 card − 3 tick). Event: `OnCardClicked(Card)`.

* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideoCard.cpp#L8) — show the moment and hide
  the highlight (designer + game).
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideoCard.cpp#L15) — bind the card button.
* [`SetMoment`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideoCard.cpp#L24) /
  [`ApplyMoment`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideoCard.cpp#L30) — copy the three texts and move the
  tick sideways by `Severity × TickTravelWidth` (render translation, so layout is untouched).
* [`SetSelected`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideoCard.cpp#L43) — show/hide the green outline.
* [`HandleClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideoCard.cpp#L51) — fire `OnCardClicked(this)`.

---

## CPP_UW_IHPCVideosRow — videos row

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCVideosRow.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp)

Required: ScrollBox `CardScrollBox` (horizontal) and Slider `ScrollSlider` (the thin indicator).
Settings: `Moments` (the cards), `CardClass` (= `WBP_IHPC_VideoCard`), `CardSpacing`, `bSeekTimelineOnSelect`.
Event: `OnMomentSelected(Moment)`. Functions: `SetMoments`, `AddMoment`, `GetMoments`.

* [Constructor](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L14) — the 5 Figma sample cards
  (Soleus/Neck, Jan 4th 2026, 13:55 p.m.; severity 0.17 / 0.41 = where the tick sits on the Figma cards; times spread
  0.1 → 0.9 along the animation).
* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L33) — build the cards (so the
  designer shows them).
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L39) — bind the slider's value
  change and mouse capture begin/end; build the cards.
* [`NativeTick`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L52) — keep the indicator in sync with
  mouse-wheel scrolling.
* [`SetMoments` / `AddMoment`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L62) — change data, rebuild.
* [`RebuildCards`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L74) — clears the scroll box; for each
  moment creates a `CardClass` widget, gives it the moment, listens to its click, adds it with `CardSpacing` on the right
  (not after the last card).
* [`HandleCardClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L106) — unhighlight the old card,
  highlight the new one, jump the avatar timeline to its moment (if enabled), fire `OnMomentSelected`.
* [`HandleSliderChanged`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L133) — slider 0..1 → scroll
  offset 0..end.
* [`HandleSliderCaptureBegin/End`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L142) — remember when
  the user is dragging, so the tick-sync does not fight the drag.
* [`SyncSliderToScroll`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCVideosRow.cpp#L145) — if nothing to scroll,
  hide the thumb; else set the slider to offset ÷ end.

---

## CPP_UW_IHPCAnalysisPanel — the panel

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCAnalysisPanel.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp)

Required: `GraphAccordion`, `VideosRow`, `InspectButton`; optional `ZoomedGraphContainer`, `ZoomedGraph`.
Event: `OnInspectClicked`. Functions: `SetZoomedGraphVisible`, `IsZoomedGraphVisible`.

* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L12) — start with the big
  graph hidden.
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L18) — listen to the accordion's
  zoom event; copy the videos row's moments into the accordion's Tagged Points list; bind the inspect button.
* [`NativeTick`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L39) — while the big graph is shown,
  update its playhead.
* [`SetZoomedGraphVisible`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L50) — when showing, copy
  the small Movement Graph's lines (including which are switched on) into the big one; show/collapse the container.
* [`HandleZoomRequested`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L91) — toggle the big graph.
* [`HandleInspectClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L96) — if the big graph is
  open, close it; otherwise fire `OnInspectClicked`.

---

## CPP_UW_IHPCHud — title bar, menu, tabs

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCHud.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp)

Required: `NavBar`, `ChevronGroup`, `ChevronButton`, `ChevronCircle`, `ChevronIcon`, `Tab_Profile`, `Tab_Progress`,
`Tab_SavedVideos`, `Tab_HistoryTimeline`, `Tab_Settings`; optional `AnalysisPanel`, `Timeline`, and *(step 4)*
`ProfilePanel`, `ProgressPanel`, `HistoryTimelinePanel`, `SettingsPanel` (empty panels styled like Figma "Rectangle 26")
and `PanelCloseButton` (the close "X").
Settings: `AnalysisPanelTab` (Saved Videos), `bStartWithNavBarOpen`, `NavBarHeight` (88), the two chevron textures,
the two circle colours. Event: `OnTabChanged(NewTab)`.

* [Constructor](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L16) — circle colours from Figma
  (`#1D3C55` @ 44% closed, white @ 86% open).
* [`GetTabs`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L24) — the 5 tabs as a list.
* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L29) — gives each tab its id and default
  label (so names cannot get mixed up), shows the starting open/closed state in the designer.
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L49) — makes the HUD itself
  click-through (`SelfHitTestInvisible`) so empty areas still reach the 3D view; binds the chevron and the 5 tabs; sets
  the starting state; selects nothing (panel closed).
* [`HandleChevronClicked` → `ToggleNavBar`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L105).
* [`SetNavBarOpen`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L110) — show/collapse the nav bar, refresh
  the chevron.
* [`RefreshChevron`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L120) — move the circle down by
  `NavBarHeight` when open (render translation), set the circle colour, swap the arrow picture.
* [`HandleTabClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L144) — clicking the selected tab
  unselects it; otherwise selects the clicked tab.
* [`SelectTab`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L154-L172) — highlight only the matching tab; `RefreshPanels`; if that tab has a panel, close
  the nav bar (Figma frame 5); fire `OnTabChanged`.
* [`GetPanelForTab`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L174-L192) *(step 4)* — which panel a tab opens: the analysis panel for `AnalysisPanelTab`
  (Saved Videos), otherwise `ProfilePanel` / `ProgressPanel` / `HistoryTimelinePanel` / `SettingsPanel`; nothing for
  None.
* [`RefreshPanels`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L194-L209) *(step 4)* — shows the selected tab's panel (`Visible`, so it blocks clicks to the
  3D view behind it), collapses all the others, and shows the close "X" only while a panel is open.
* [`HandlePanelCloseClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L211-L214) → [`ClosePanel`](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCHud.h#L111-L113) *(step 4)* — `SelectTab(None)`: panel
  closed, no tab highlighted. Also callable from Blueprint; [`IsAnyPanelOpen`](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCHud.h#L120-L121) tells whether one is open.
* [`SetAnalysisPanelOpen`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L216-L226) — show/collapse the analysis panel directly (and the X with it).

---

## CPP_UW_IHPCTimeline — playback / timeline bar

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCTimeline.h) ·
[code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp) · Figma layer `ihpc ui (1)ee 1` (frame 1) +
the `x1.5` text layer. Replaces the old prototype `WCPP_AnimationTimeline` / `WB_AmationTimeline` (still in the project,
no longer created).

Required widgets: `RecordButton`, `RestartButton`, `PauseButton`, `SlowDownButton`, `SpeedUpButton`, `PlayButton`,
`FastForwardButton`, `BookmarkButton` (Buttons), `TrackProgress` (ProgressBar), `ScrubSlider` (Slider), `ThumbGroup`,
`SpeedText` (TextBlock), `MarkerLayer` (Canvas Panel); optional `RecordingIndicator`.
Settings: `SpeedSteps` (0.25, 0.5, 1, 1.5, 2, 3), `DefaultSpeedIndex` (2 = 1×), `bPlayWhenRecordingStarts`,
`TrackLength` (513), `MarkerSize` (19), `DesignerPreviewTime` (0.545), `MarkerTexture`, `RecordingTint`,
`RecordingTitleFormat` ("Recording {0}"), `BookmarkTitleFormat` ("Bookmark {0}").
Events: `OnRecordingSaved`, `OnBookmarkAdded`, `OnMarkerClicked`, `OnSpeedChanged`.

* [Constructor](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L18) — red tint `#FF6B6B`, the two title
  formats.
* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L30) — clamp the starting speed,
  show it on the knob; in the designer put the knob at 54.5% like Figma; build markers; hide the red dot.
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L50) — bind the 8 buttons; bind the
  scrub slider's value change + mouse capture begin/end; apply the starting speed to the avatar; build markers.
* [`NativeTick`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L77) — every frame: (1) unless the user is
  dragging, read the animation time and move the knob / dark part / slider to it; (2) if the component's speed changed
  (from anywhere), update the "x…" text; (3) while recording, pulse the red dot's opacity with a sine wave.
* [`GetCurrentTime`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L111) — animation time, `-1` (no
  timeline) becomes 0.
* [`ShowTime`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L116) — progress bar percent = time (dark
  played part); knob render-translated `time × TrackLength` from the start of the track.
* [`ShowSpeed`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L130) — `"x"` + number with 0–2 decimals
  (`x1`, `x1.5`, `x0.25`).
* [Button handlers](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L146) — each calls the matching public
  function below (so Blueprint can call the same actions).
* [`Play` / `Pause`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L155) — `PlayAvatar` (restarts if at
  the end) / `PauseAvatar`.
* [`Restart`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L165) — seek to 0 **without** pausing, so it
  keeps playing if it was playing.
* [`SlowDown` / `SpeedUp` / `SetSpeedIndex`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L171) — move
  one step through `SpeedSteps` (clamped at both ends), set the avatar speed, update the text, fire `OnSpeedChanged`.
* [`FastForwardToNextMarker`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L199) — find the smallest
  marker time that is still ahead of now (+0.001 so the marker you are on does not count); none → the end (1.0); seek there
  without pausing.
* [`AddBookmark`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L215) — "Bookmark N" at the current time
  with today's date/time → new marker → `OnBookmarkAdded`.
* [`ToggleRecording`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L222) — **start**: remember the
  animation time and the clock time, start playing (if `bPlayWhenRecordingStarts`), tint the button red, show the red dot,
  tooltip "Stop recording". **Stop**: restore the button, hide the dot, build "Recording N" (date/time = when it started,
  time on the animation = where it started) → new marker → `OnRecordingSaved`.
* [`MakeMoment`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L265) — builds an `FIHPCTaggedMoment`;
  severity 0 because a new clip has no injury-risk analysis yet.
* [`HandleScrubBegin`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L275) — remember whether it was
  playing and pause, so the animation does not fight the mouse.
* [`HandleScrubChanged`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L286) — only while dragging: seek
  to the slider value and move the knob.
* [`HandleScrubEnd`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L296) — resume playing if it was
  playing before.
* [`SetMarkers` / `AddMarker`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L309) — change the list,
  rebuild.
* [`RebuildMarkers`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L321) — clear the marker canvas; in
  the designer with no data show Figma's three markers (8%, 37%, 86%); build one button style from `MarkerTexture`
  (hover 1.2× brighter, pressed 0.8×); for each marker create a Button with a tooltip ("Title - time"), anchor it to the
  vertical middle of the track, centre it on `time × TrackLength`.
* [`HandleMarkerClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCTimeline.cpp#L376) — button clicks carry no
  data, so find the marker button under the mouse (`IsHovered`), jump there and pause, fire `OnMarkerClicked`.

**Supporting changes (step 2)**
* `UCPP_UW_IHPCGraphAccordion::`[`AddTaggedPoint`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCGraphAccordion.cpp#L279)
  — append one row to Tagged Points.
* `UCPP_UW_IHPCAnalysisPanel::`[`AddSavedVideo`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L66)
  (new card + new tagged point), [`AddTaggedPoint`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L78),
  [`GetSavedVideos`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCAnalysisPanel.cpp#L86).
* `UCPP_UW_IHPCHud`: optional `Timeline` widget. In
  [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L49) the timeline's markers start as the
  saved videos and its two events are bound;
  [`HandleRecordingSaved`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L85) → `AddSavedVideo`,
  [`HandleBookmarkAdded`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCHud.cpp#L93) → `AddTaggedPoint`.

---

## CPP_UW_IHPCLayerSwitcher — Body / Muscles / Skeleton buttons

[header](../Source/MetaHumanTest/Public/IHPC_UI/CPP_UW_IHPCLayerSwitcher.h) · [code](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp) · Figma layers `ihpc ui rttd 2` + `Rectangle 24` (frame 1). Replaces the top-left
placeholder `WB_AnatomyViewSwitcher` and **keeps its functionality**.

**The key idea — a child class, not a copy.** The placeholder's opacity code lives in the teammate's
`UCPP_UW_AnatomyViewSwitcher` (`Public/CPP_UW_AnatomyViewSwitcher.h`, not changed). Its slider handler
`OnSliderValueChanged2(Value)` finds the pawn's skeletal meshes tagged `WholePart` / `SkeletonPart` / `FacePart` and the
groom tagged `HairPart`, lines the skeleton up with the body's pelvis, sets the material parameter **`Fade`** = Value on
the body, face and hair, and swaps the hair to cards below 0.9. `UCPP_UW_IHPCLayerSwitcher` **inherits** from that class,
so all of this comes along unchanged; the new class only adds the look and decides which `Fade` each button sends. It
sends it through the parent's own slider (`AnatomyViewSwitcher_Slider`, hidden in the Widget Blueprint), which is
exactly what dragging the placeholder slider did. Because the controller's *Anatomy View Switcher Widget Class* is a
`TSubclassOf<UCPP_UW_AnatomyViewSwitcher>`, the child class fits into it without touching `CPP_PlayerController`.

Required widgets: `BodyLayer_Btn`, `MusclesLayer_Btn`, `SkeletonLayer_Btn` (Buttons); optional `SkeletonBadge` (Image);
plus, for the parent, `AnatomyMetaHuman_Btn` (Button) and `AnatomyViewSwitcher_Slider` (Slider), both Collapsed.
Settings (*IHPC | Layers*): `DefaultLayer` (Body), `bApplyDefaultLayerOnStart` (off), `BodyFade` (1.0), `MusclesFade`
(0.5), `SkeletonFade` (0.2). Look (*IHPC | Style*): the six `…SelectedTexture` / `…UnselectedTexture`, `ButtonSize`
(46.66), `HoveredTint` (1.15), `PressedTint` (0.8), `bShowSkeletonBadge`.
Event: `OnLayerChanged(Layer, Fade)`.

* [`NativePreConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L12-L18) — runs in the designer too: select the default layer and paint the buttons, so the
  Widget Blueprint already looks like Figma while editing.
* [`NativeConstruct`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L20-L45) — `Super::NativeConstruct()` first (the parent binds its slider and button), then bind
  the three new buttons; optionally apply the default layer's Fade at start (off = like the placeholder, nothing changes
  until a click).
* [`HandleBodyClicked` / `HandleMusclesClicked` / `HandleSkeletonClicked`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L47-L49) — one line each: `SelectLayer(...)`.
* [`SelectLayer`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L51-L59) — remember the layer, repaint the buttons, send that layer's Fade to the avatar, fire
  `OnLayerChanged`. Also callable from Blueprint.
* [`GetFadeForLayer`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L61-L70) — Body → `BodyFade`, Muscles → `MusclesFade`, Skeleton → `SkeletonFade`.
* [`CanDriveAvatarLayers`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L72-L102) — safety check: the parent uses the three tagged meshes **without null checks**
  (and prints each one's mesh asset name), so if the current pawn lacks a `WholePart`, `SkeletonPart` or `FacePart`
  skeletal mesh (or one has no mesh asset), it would crash. This returns false in that case.
* [`ApplyFadeToAvatar`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L104-L132) — if the check fails, log one warning and stop (the buttons still change and the
  event still fires). Otherwise `AnatomyViewSwitcher_Slider->SetValue(Fade)`, which calls the parent's
  `OnSliderValueChanged2`. `USlider::SetValue` only notifies when the value *changes*, so if the slider is already at
  that value it broadcasts `OnValueChanged` itself — every click re-applies (useful after switching pawns).
* [`SetSkeletonBadgeVisible`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L134-L138) — show / hide the orange badge.
* [`RefreshVisuals`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L140-L151) — each button gets its *selected* or *unselected* texture; the badge is
  `HitTestInvisible` (it must not steal the skeleton button's clicks) or `Collapsed`.
* [`ApplyButtonLook`](../Source/MetaHumanTest/Private/IHPC_UI/CPP_UW_IHPCLayerSwitcher.cpp#L153-L179) — builds the button style from one texture: Normal (tint 1), Hovered (1.15),
  Pressed (0.8), Disabled (0.5), no padding.

---

## CPP_PlayerController — creates the HUD

Existing project file ([header](../Source/MetaHumanTest/CPP_PlayerController.h) · [code](../Source/MetaHumanTest/CPP_PlayerController.cpp)); only these lines were
added, following the same pattern as the anatomy switcher and pawn switcher:

* [`#include "IHPC_UI/CPP_UW_IHPCHud.h"`](../Source/MetaHumanTest/CPP_PlayerController.h#L11) — so the controller knows the HUD class.
* [`MainHUDWidgetClass`](../Source/MetaHumanTest/CPP_PlayerController.h#L82-L85) — `TSubclassOf<UCPP_UW_IHPCHud>`, *EditAnywhere*: the Widget
  Blueprint to create. Set to `WBP_IHPC_HUD` in `BP_PlayerController` → Class Defaults → *UI*.
* [`MainHUDZOrder`](../Source/MetaHumanTest/CPP_PlayerController.h#L87-L89) — draw order, default **10** so the HUD is above the other widgets
  (they are added with the default 0).
* [`GetMainHUD()`](../Source/MetaHumanTest/CPP_PlayerController.h#L91-L94) — *BlueprintPure* getter for the created HUD, so the controller or a
  Blueprint can reach it later (e.g. `GetMainHUD()->SelectTab(EIHPCNavTab::SavedVideos)` from a key press).
* [`MainHUDWidget`](../Source/MetaHumanTest/CPP_PlayerController.h#L115-L117) — private `UPROPERTY()` pointer to the instance (the `UPROPERTY`
  keeps it from being garbage-collected).
* [In `BeginPlay`](../Source/MetaHumanTest/CPP_PlayerController.cpp#L85-L94) — right after the pawn switcher: if a class is set,
  `CreateWidget<UCPP_UW_IHPCHud>(this, MainHUDWidgetClass)` (owner = this controller) and
  `AddToViewport(MainHUDZOrder)`.

Because the controller is the owner, `GetOwningPlayer()` inside the HUD widgets is this controller.

---

## What happens when you click…

**Pressing Play in the editor (start-up)**
`ACPP_PlayerController::BeginPlay` → creates the anatomy switcher and pawn switcher → creates `WBP_IHPC_HUD`
(`MainHUDWidgetClass`) and adds it at Z-order 10 → the HUD's `NativeConstruct` binds the chevron, tabs and timeline, gives
the timeline its markers (the saved videos) and starts with the menu closed and the panel hidden.

**The round arrow**
`ChevronButton.OnClicked` → `UCPP_UW_IHPCHud::HandleChevronClicked` → `ToggleNavBar` → `SetNavBarOpen(true)` → `NavBar`
visible → `RefreshChevron` (circle moves down 88, turns white, arrow becomes blue ▲).

**"Saved Videos"**
`TabButton.OnClicked` (inside `Tab_SavedVideos`) → `UCPP_UW_IHPCNavTab::HandleClicked` → `OnTabClicked(SavedVideos)` →
`UCPP_UW_IHPCHud::HandleTabClicked` → `SelectTab(SavedVideos)` → tab turns green, `SetAnalysisPanelOpen(true)`,
`SetNavBarOpen(false)`, `OnTabChanged` fired.

**A video card**
`CardButton.OnClicked` → `UCPP_UW_IHPCVideoCard::HandleClicked` → `OnCardClicked(card)` →
`UCPP_UW_IHPCVideosRow::HandleCardClicked` → green outline on that card → `UIHPCUILibrary::SeekAvatarTimeline(moment
time)` → `UAnimationTimelineComp::Pause()` + `SetNormalizedTime()` (the avatar pose jumps) → next frame the graphs'
`NativeTick` reads the new time and the playhead moves.

**The close "X"** *(step 4)*
`PanelCloseButton.OnClicked` → `UCPP_UW_IHPCHud::HandlePanelCloseClicked` → `ClosePanel` → `SelectTab(None)` → every tab
un-highlighted → `RefreshPanels` (all panels and the X collapsed) → `OnTabChanged(None)`.

**"Profile"** *(step 4)*
`HandleTabClicked(Profile)` → `SelectTab(Profile)` → `GetPanelForTab` = `ProfilePanel` → `RefreshPanels` shows it (others
collapsed) + shows the X → nav bar closed.

**The "Bones" switch**
CheckBox → `UCPP_UW_IHPCToggleSwitch::HandleCheckStateChanged` → `OnToggled(switch, true)` →
`UCPP_UW_IHPCGraphAccordion::HandleToggleChanged` → `ApplyToggleFilter` → `SetSeriesVisible` on both graphs → next
`NativePaint` only draws the Bones line.

**Download**
`DownloadButton.OnClicked` → `HandleDownload` → `ExportGraphsToCSV` → file in `Saved/IHPC_Exports/`.

**Timeline: Speed up**
`SpeedUpButton.OnClicked` → `UCPP_UW_IHPCTimeline::HandleSpeedUp` → `SpeedUp` → `SetSpeedIndex(+1)` →
`UIHPCUILibrary::SetAvatarPlaySpeed(1.5)` (the component's `PlaySpeed`) → knob text "x1.5" → `OnSpeedChanged`.

**Timeline: Record (twice)**
1st click → `ToggleRecording` (start): remembers time + clock, plays, button turns red, red dot pulses.
2nd click → `ToggleRecording` (stop): "Recording 1" moment → `AddMarker` (orange dot on the track) →
`OnRecordingSaved` → `UCPP_UW_IHPCHud::HandleRecordingSaved` → `UCPP_UW_IHPCAnalysisPanel::AddSavedVideo` →
`VideosRow->AddMoment` (new card) + `GraphAccordion->AddTaggedPoint` (new row).

**Timeline: Bookmark**
`BookmarkButton.OnClicked` → `AddBookmark` → "Bookmark 1" marker → `OnBookmarkAdded` → HUD → `AddTaggedPoint`.

**Timeline: Fast-forward**
`FastForwardToNextMarker` → nearest marker after now → `SeekAvatarTimeline(t, no pause)` → next frame the knob moves there.

**Layer switcher: Skeleton**
`SkeletonLayer_Btn.OnClicked` → `UCPP_UW_IHPCLayerSwitcher::HandleSkeletonClicked` → `SelectLayer(Skeleton)` → buttons
repainted (Skeleton dark, others light) → `ApplyFadeToAvatar(0.2)` → `CanDriveAvatarLayers` (tagged parts found) →
`AnatomyViewSwitcher_Slider->SetValue(0.2)` → parent `UCPP_UW_AnatomyViewSwitcher::OnSliderValueChanged2(0.2)` → skeleton
lined up, `Fade` = 0.2 on body/face/hair, hair → cards → `OnLayerChanged(Skeleton, 0.2)`.

**Timeline: dragging the knob**
Slider mouse capture begin → `HandleScrubBegin` (pause, remember) → each move `HandleScrubChanged` → `SeekAvatarTimeline`
→ release `HandleScrubEnd` (resume if it was playing).

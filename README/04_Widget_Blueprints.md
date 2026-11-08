# 04 — Widget Blueprints

Folder: `Content/UserInterface/IHPC/Widgets/` (`/Game/UserInterface/IHPC/Widgets`).

**Rule:** names marked **(C++)** are used by the C++ parent class (`BindWidget`). You can move, restyle, resize or wrap
them, but **do not rename or delete them** — the Blueprint will refuse to compile and tell you which one is missing.
Everything else is free to change.

Parent class = the C++ class in [03_Code_Walkthrough.md](03_Code_Walkthrough.md). Class Defaults (the settings in the
Details panel when nothing is selected) hold the textures/fonts listed at the bottom of each section.

---

## WBP_IHPC_HUD — parent `CPP_UW_IHPCHud`
Full screen. Created by **`CPP_PlayerController::BeginPlay`** from `BP_PlayerController` → *Main HUD Widget Class*
(owner = the player controller, Z-order = *Main HUD Z Order*, 10), like the anatomy switcher and pawn switcher.

```
HudCanvas (Canvas Panel, not hit-testable itself)
├─ Timeline (C++, optional)     WBP_IHPC_Timeline, bottom-centre 125 px left of centre (Figma), 28 above the bottom, 1048×102   (step 2)
├─ AnalysisPanel (C++)          WBP_IHPC_AnalysisPanel, top-centre, y 167, 1217×798, hidden until Saved Videos
├─ ProfilePanel (C++, optional)          Border, same slot as AnalysisPanel, rounded box black 62 %, radius 29 (step 4)
│  └─ ProfileContent                     empty Canvas Panel — put the Profile screen here
├─ ProgressPanel (C++, optional)         same  └─ ProgressContent
├─ HistoryTimelinePanel (C++, optional)  same  └─ HistoryTimelineContent
├─ SettingsPanel (C++, optional)         same  └─ SettingsContent
├─ PanelCloseButton (C++, optional)      38×38 on the panel's top-right corner (centre 8.5 px in from both edges),
│  │                                     navy #1D3C55 circle + white rim 35 %; hover #274A65, pressed #183C55
│  └─ PanelCloseIcon                     T_IHPC_Close 16×16, not clickable itself
├─ ChevronGroup (C++)           Size Box 83×83, centre at (screen centre, 105) — moved down 88 when the menu opens
│  └─ ChevronOverlay
│     ├─ ChevronCircle (C++)    rounded image, colour set by C++
│     ├─ ChevronIcon (C++)      arrow texture, swapped by C++
│     └─ ChevronButton (C++)    invisible button over the circle
├─ NavBar (C++)                 Vertical Box, y 105, full width — collapsed until opened
│  ├─ NavBarSize (88 tall)
│  │  └─ NavBarBackground       #274A65
│  │     └─ TabRow (Horizontal Box, centred)
│  │        ├─ Tab_Profile (C++)          WBP_IHPC_NavTab
│  │        ├─ TabSeparator_1             1×23 white 33%, 32 px each side
│  │        ├─ Tab_Progress (C++)
│  │        ├─ TabSeparator_2
│  │        ├─ Tab_SavedVideos (C++)
│  │        ├─ TabSeparator_3
│  │        ├─ Tab_HistoryTimeline (C++)
│  │        ├─ TabSeparator_4
│  │        └─ Tab_Settings (C++)
│  └─ NavBarShadow              T_IHPC_DropShadow
└─ TitleBar                     Vertical Box, full width
   ├─ TitleBarSize (105 tall)
   │  └─ TitleBarOverlay
   │     ├─ TitleBarBackground  #1D3C55
   │     ├─ TitleGlow           T_IHPC_TitleGlow 576×54
   │     └─ TitleText           "AVATAR INJURY PREVENTION TECHNOLOGY", Avenir Heavy 18
   └─ TitleBarShadow            T_IHPC_DropShadow
```
Drawing order = list order (title bar on top, so the circle's top half hides behind it).
Class Defaults: `ChevronClosedTexture` = `T_IHPC_HeaderChevron_Down`, `ChevronOpenTexture` = `T_IHPC_HeaderChevron_Up_Blue`,
`AnalysisPanelTab` = Saved Videos, `NavBarHeight` = 88.

## WBP_IHPC_Timeline — parent `CPP_UW_IHPCTimeline` (step 2)
Figma layer `ihpc ui (1)ee 1`. Lives inside `WBP_IHPC_HUD` as `Timeline`.
```
TimelineSize (1048×102)
└─ TimelineCanvas (click-through)
   ├─ TrackProgress (C++)       ProgressBar (274,44) 513×10.67 — fill #183C55 (played), background #7CAFD2, Scale fill
   ├─ ScrubSlider (C++)         invisible Slider (274,28) 513×43 — drag/click to scrub
   ├─ MarkerLayer (C++)         Canvas (274,44) 513×10.67 — C++ adds one button per marker
   ├─ ThumbGroup (C++)          Overlay 44×44 centred on the START of the track — C++ slides it along
   │  ├─ ThumbImage             T_IHPC_TL_Thumb
   │  └─ SpeedText (C++)        "x1.5", Avenir Medium 9
   ├─ RecordButton (C++)        (20.3,28) 45.7×45.7, T_IHPC_TL_Record
   │  └─ RecordIcon             same picture as content, tinted red by C++ while recording
   ├─ RestartButton (C++)       (75.7,21.7) 58×58
   ├─ PauseButton (C++)         (143.3,18) 65×65
   ├─ SlowDownButton (C++)      (217,29) 46×45.7
   ├─ SpeedUpButton (C++)       (798.7,27) 46×46
   ├─ PlayButton (C++)          (854,18) 65×65
   ├─ FastForwardButton (C++)   (927.3,22.7) 56.3×56
   ├─ BookmarkButton (C++)      (991.7,28) 45.7×45.7
   └─ RecordingIndicator (C++, optional)   12×12 red dot over the record button, hidden until recording
```
Class Defaults: `MarkerTexture` = `T_IHPC_TL_Marker`, `TrackLength` 513, `MarkerSize` 19, `SpeedSteps`
0.25 / 0.5 / 1 / 1.5 / 2 / 3, `DefaultSpeedIndex` 2.

## WBP_IHPC_LayerSwitcher — parent `CPP_UW_IHPCLayerSwitcher` (step 3)
Figma layers `ihpc ui rttd 2` + `Rectangle 24`. Created by `CPP_PlayerController` (`BP_PlayerController` →
*Anatomy View Switcher Widget Class*), **not** inside the HUD — same place the placeholder `WB_AnatomyViewSwitcher` was.
```
LayerRoot (full screen, click-through)
├─ LayerSwitcher             Canvas 204×65, anchor bottom-centre, position (533, -45), alignment (0.5, 1)
│  ├─ Pill                   (0,0) 204×65, rounded box #1D3C55 at 26 %, radius 32.5 — catches clicks between buttons
│  ├─ BodyLayer_Btn (C++)    (20.12, 9.36) 46.66×46.66 — picture set by C++ (T_IHPC_LS_Body_On / _Off)
│  ├─ MusclesLayer_Btn (C++) (79.0, 9.36)  46.66×46.66 — T_IHPC_LS_Muscles_On / _Off
│  ├─ SkeletonLayer_Btn (C++)(137.87, 9.36) 46.66×46.66 — T_IHPC_LS_Skeleton_On / _Off
│  └─ SkeletonBadge (C++, optional)  (168.5, 8.15) 16.8×16.8, T_IHPC_LS_Badge, not clickable — hidden (Collapsed)
├─ AnatomyMetaHuman_Btn (C++ parent)       Collapsed — required by the teammate's class, not used
└─ AnatomyViewSwitcher_Slider (C++ parent) Collapsed, 0..1, value 1 — the new buttons set it from C++
```
**Move the whole switcher** by changing `LayerSwitcher`'s position (the children are relative to it).
Class Defaults: the six button textures, `ButtonSize` 46.66, Fades (Body 1.0 / Muscles 0.5 / Skeleton 0.2),
`DefaultLayer` Body, `bShowSkeletonBadge` **off** (badge hidden); copied from the placeholder: `GroomStrandsAsset` = `Hair_S_UpdoBuns`, `GroomCardsAsset` =
`Hair_S_UpdoBuns1`, `PawnToSpawn` = `BP_SkeletonModel`.

## WBP_IHPC_NavTab — parent `CPP_UW_IHPCNavTab`
```
TabButton (C++)       Button, invisible in every state
└─ TabLabel (C++)     TextBlock, Avenir Medium 15, centred
```
Class Defaults: `NormalFont` Avenir Medium 15, `HighlightFont` Avenir Heavy 15, `HighlightScale` 1.2,
`NormalColor` white, `HighlightColor` #B3CA7F. The HUD fills in each tab's `TabId` and `Label`.

## WBP_IHPC_AnalysisPanel — parent `CPP_UW_IHPCAnalysisPanel`
```
PanelSize (1217×798)
└─ PanelBackground            rgba(0,0,0,0.62), radius 29 (blocks clicks to the 3D view while open)
   └─ PanelCanvas
      ├─ ViewerFrame          (25,21) 870×559, rgba(0,0,0,0.29) r11
      ├─ ZoomedGraphContainer (C++, optional)  (47,49) 827×508 — hidden until zoom
      │  └─ ZoomedGraphStack
      │     ├─ ZoomedGraphTitle   "Movement Graph"
      │     └─ ZoomedGraph (C++, optional)  CPP_UW_IHPCLineGraph
      ├─ InspectButton (C++)  (835,519) 33×33
      │  └─ InspectIcon       T_IHPC_InspectCode
      ├─ VideosArea           (25,599) 870×171, rgba(49,49,49,0.66) r11
      ├─ VideosRow (C++)      WBP_IHPC_VideosRow (31,605) 858×160
      └─ GraphAccordion (C++) WBP_IHPC_GraphAccordion (910,26), auto height
```

## WBP_IHPC_GraphAccordion — parent `CPP_UW_IHPCGraphAccordion`
```
AccordionSize (286 wide)
└─ Sections (Vertical Box)
   ├─ Header_ShowGraphs (C++)          Button 47 tall, rgba(217,217,217,0.2) r11
   │  └─ … _Label "Show graphs" + Chevron_ShowGraphs (C++)
   ├─ Content_ShowGraphs (C++)         Size Box 560 tall (gap 7 above, 9 below)
   │  └─ ShowGraphsPanel               rgba(0,0,0,0.41) r11
   │     └─ ShowGraphsCanvas
   │        ├─ MovementGraphTitle      "Movement Graph"
   │        ├─ MovementGraph (C++)     (11,45) 268×142, DemoSeed 1
   │        ├─ ActiveMusclesTitle      "Active Muscles"
   │        ├─ ActiveMusclesGraph (C++) (11,233) 268×142, DemoSeed 8
   │        ├─ Toggle_Bones / Toggle_Nerves / Toggle_Muscles / Toggle_Tendons (C++)  WBP_IHPC_ToggleSwitch at x 22
   │        ├─ Legend_* (5×18 colour bars at x 70)   Label_* (text at x 80)
   │        ├─ DownloadButton (C++) → DownloadIcon   (214,523) 30×30
   │        └─ ZoomButton (C++) → ZoomIcon           (251,528) 20×19
   ├─ Header_ActiveMuscles (C++) … + Chevron_ActiveMuscles (C++)   (13 above)
   ├─ Content_ActiveMuscles (C++)      Border rgba(0,0,0,0.41) r11, padding 8
   │  └─ ActiveMuscles_ListSize (max 260) → ActiveMuscles_Scroll → ActiveMusclesList (C++)
   ├─ Header_TaggedPoints (C++) … + Chevron_TaggedPoints (C++)
   └─ Content_TaggedPoints (C++)
      └─ TaggedPoints_ListSize → TaggedPoints_Scroll → TaggedPointsList (C++)
```
Class Defaults: `ChevronUpTexture` / `ChevronDownTexture`, `ListFont` Avenir Medium 11, `StartOpenSection` None,
`ActiveMuscles` (sample names).

## WBP_IHPC_ToggleSwitch — parent `CPP_UW_IHPCToggleSwitch`
```
SwitchSize (38×20)
└─ SwitchCheckBox (C++)   style: unchecked = T_IHPC_Toggle_Off, checked = T_IHPC_Toggle_On (hover slightly brighter)
```

## WBP_IHPC_VideosRow — parent `CPP_UW_IHPCVideosRow`
```
RowCanvas
├─ ScrollTrack            (3,7) 842×15, white 5%, fully rounded
├─ ScrollSlider (C++)     (8,10) 832×9, no bar, thumb 62×9 rgba(153,191,222,0.51), Indent Handle on
└─ CardScrollBox (C++)    (24,41) 834×119, horizontal, no scrollbar — C++ adds the cards here
```
Class Defaults: `CardClass` = `WBP_IHPC_VideoCard`, `CardSpacing` 23, `Moments` = the 5 sample cards.

## WBP_IHPC_VideoCard — parent `CPP_UW_IHPCVideoCard`
```
CardSize (240×95)
└─ CardOverlay
   ├─ CardBackground          T_IHPC_VideoCard_BG (Figma card art without text)
   ├─ CardContent (Canvas, click-through)
   │  ├─ TitleText (C++)      (84,21) Avenir Heavy 13, ends with "…" if too long
   │  ├─ DateText (C++)       (84,47) Avenir Medium 10
   │  ├─ TimeText (C++)       (84,63) Avenir Medium 10
   │  ├─ SeverityTick (C++)   (0,0) 3×13 white — moved sideways by C++
   │  └─ SelectionHighlight (C++, optional)  green #B3CA7F outline, hidden until selected
   └─ CardButton (C++)        invisible button over the whole card (faint white on hover)
```

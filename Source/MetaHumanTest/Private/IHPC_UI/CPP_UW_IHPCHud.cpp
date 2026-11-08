// CPP_UW_IHPCHud.cpp - title bar + side bar + side panels + timeline + reset view. See header.

#include "IHPC_UI/CPP_UW_IHPCHud.h"

#include "IHPC_UI/CPP_UW_IHPCActionsPanel.h"
#include "IHPC_UI/CPP_UW_IHPCChatPanel.h"
#include "IHPC_UI/CPP_UW_IHPCGraphCard.h"
#include "IHPC_UI/CPP_UW_IHPCGraphsPanel.h"
#include "IHPC_UI/CPP_UW_IHPCLayerSwitcher.h"
#include "IHPC_UI/CPP_UW_IHPCLineGraph.h"
#include "IHPC_UI/CPP_UW_IHPCSideBar.h"
#include "IHPC_UI/CPP_UW_IHPCSideTab.h"
#include "IHPC_UI/CPP_UW_IHPCTaggedPointsList.h"
#include "IHPC_UI/CPP_UW_IHPCTimeline.h"
#include "IHPC_UI/CPP_UW_IHPCVideosRow.h"
#include "IHPC_UI/IHPCUILibrary.h"

#include "../../CPP_MouseFunctionComp.h"   // module root (not on the include path)
#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"

#define LOCTEXT_NAMESPACE "IHPCHud"

UCPP_UW_IHPCHud::UCPP_UW_IHPCHud(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	ResetViewColor = UIHPCUILibrary::FigmaColor(TEXT("0C273D"), 0.66f);
	GraphBookmarkTitleFormat = LOCTEXT("GraphBookmark", "{0} bookmark {1}");
}

// ============================================================================
// Setup
// ============================================================================

void UCPP_UW_IHPCHud::NativePreConstruct()
{
	Super::NativePreConstruct();
	ApplyStyles();

	// Designer preview: show the starting panel (or none), already slid in.
	SelectedTab = StartTab;
	DisplayedTab = StartTab;
	RefreshPanelContent();
	ApplyPanelSlide(StartTab != EIHPCSideTab::None ? 1.f : 0.f);
	if (ZoomedGraphPanel)
	{
		ZoomedGraphPanel->SetVisibility(ESlateVisibility::Collapsed);
	}
}

void UCPP_UW_IHPCHud::NativeConstruct()
{
	Super::NativeConstruct();

	// Empty areas of the HUD must not swallow clicks: the 3D view underneath needs them
	// for orbit / pan / zoom (see CPP_PlayerController::HandleMouseMove).
	SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	ApplyStyles();

	if (SideBar)
	{
		SideBar->OnTabClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleSideTabClicked);
		if (UCPP_UW_IHPCChatPanel* Chat = SideBar->GetChatPanel())
		{
			Chat->OnMessageSent.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleChatMessageSent);
		}
	}
	if (PanelCloseButton)
	{
		PanelCloseButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandlePanelCloseClicked);
		PanelCloseButton->SetToolTipText(LOCTEXT("ClosePanel", "Close"));
	}
	if (ResetViewButton)
	{
		ResetViewButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleResetViewClicked);
		ResetViewButton->SetToolTipText(LOCTEXT("ResetView", "Reset view"));
	}
	if (ZoomedGraphCloseButton)
	{
		ZoomedGraphCloseButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleZoomedGraphCloseClicked);
	}

	// Action panel: tell the HUD (and Blueprints) when the avatar's action changes.
	if (ActionsPanel)
	{
		ActionsPanel->OnActionSelected.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleActionSelected);
	}

	// Graphs panel: the card's zoom icon shows the big graph, its bookmark icon drops a bookmark.
	if (GraphsPanel && GraphsPanel->GetGraphCard())
	{
		GraphsPanel->GetGraphCard()->OnZoomRequested.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleZoomRequested);
		GraphsPanel->GetGraphCard()->OnBookmarkRequested.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleGraphBookmarkRequested);
	}

	// The Timeline panel lists the same moments as the Saved Videos cards (plus bookmarks / recordings made later),
	// and the timeline bar's orange markers start as the saved videos.
	if (TaggedPointsList && TaggedPointsList->GetTaggedPoints().Num() == 0)
	{
		TaggedPointsList->SetTaggedPoints(GetSavedVideos());
	}
	if (Timeline)
	{
		Timeline->SetMarkers(GetSavedVideos());
		Timeline->OnRecordingSaved.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleRecordingSaved);
		Timeline->OnBookmarkAdded.AddUniqueDynamic(this, &UCPP_UW_IHPCHud::HandleBookmarkAdded);
	}

	SetZoomedGraphVisible(false);
	bPanelSlideApplied = false;
	SelectSideTab(StartTab);
	PanelSlideAlpha = (StartTab != EIHPCSideTab::None) ? 1.f : 0.f;   // start already in place, no slide
	ApplyPanelSlide(PanelSlideAlpha);
}

void UCPP_UW_IHPCHud::ApplyStyles()
{
	UIHPCUILibrary::ApplyPictureButtonStyle(PanelCloseButton, RoundButtonTexture, CloseButtonSize);
	UIHPCUILibrary::ApplyPictureButtonStyle(ZoomedGraphCloseButton, RoundButtonTexture, CloseButtonSize);
	UIHPCUILibrary::ApplyRoundedButtonStyle(ResetViewButton, ResetViewColor, 34.f, 1.6f, 0.7f);
}

void UCPP_UW_IHPCHud::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// 1. Slide the side panel in / out (and move the side bar + timeline with it).
	const float Target = IsAnyPanelOpen() ? 1.f : 0.f;
	if (!bPanelSlideApplied || !FMath::IsNearlyEqual(PanelSlideAlpha, Target))
	{
		PanelSlideAlpha = (PanelSlideTime <= 0.f) ? Target
			: FMath::FInterpConstantTo(PanelSlideAlpha, Target, InDeltaTime, 1.f / PanelSlideTime);
		ApplyPanelSlide(PanelSlideAlpha);
		if (PanelSlideAlpha <= 0.f && DisplayedTab != SelectedTab)
		{
			DisplayedTab = SelectedTab;   // finished sliding out
			RefreshPanelContent();
		}
	}

	// 2. Reset-view button: only while the camera is away from its starting view.
	if (ResetViewButton)
	{
		const UCPP_MouseFunctionComp* CameraControl = UIHPCUILibrary::FindAvatarCameraControl(this);
		const bool bShow = CameraControl && (!bShowResetViewOnlyWhenMoved || CameraControl->IsViewChanged());
		const ESlateVisibility Wanted = bShow ? ESlateVisibility::Visible : ESlateVisibility::Collapsed;
		if (ResetViewButton->GetVisibility() != Wanted)
		{
			ResetViewButton->SetVisibility(Wanted);
		}
	}

	// 3. The big graph gets the same playhead as the small ones.
	if (bZoomedGraphVisible && ZoomedGraph)
	{
		ZoomedGraph->SetPlayheadTime(UIHPCUILibrary::GetAvatarTimelineTime(this));
	}
}

// ============================================================================
// Side panels
// ============================================================================

void UCPP_UW_IHPCHud::HandleSideTabClicked(EIHPCSideTab Tab)
{
	ToggleSideTab(Tab);
}

void UCPP_UW_IHPCHud::ToggleSideTab(EIHPCSideTab Tab)
{
	SelectSideTab(Tab == SelectedTab ? EIHPCSideTab::None : Tab);
}

void UCPP_UW_IHPCHud::HandlePanelCloseClicked()
{
	ClosePanel();
}

void UCPP_UW_IHPCHud::SelectSideTab(EIHPCSideTab Tab)
{
	SelectedTab = Tab;
	if (SideBar)
	{
		SideBar->SetSelectedTab(Tab);
	}

	// Opening (or switching): show the new content right away. Closing: keep the old content until it slid out.
	if (Tab != EIHPCSideTab::None)
	{
		DisplayedTab = Tab;
		RefreshPanelContent();
	}
	if (Tab != EIHPCSideTab::Graphs)
	{
		SetZoomedGraphVisible(false);   // the big graph belongs to the Graphs panel
	}
	if (Tab == EIHPCSideTab::Actions && ActionsPanel)
	{
		ActionsPanel->RefreshCards();   // the (possibly switched) pawn's actions
	}
	if (Timeline && bCompactTimelineWhenPanelOpen)
	{
		Timeline->SetCompact(Tab != EIHPCSideTab::None);
	}

	OnSideTabChanged.Broadcast(Tab);
	OnTabChanged.Broadcast(NavTabFromSideTab(Tab));
}

UWidget* UCPP_UW_IHPCHud::GetPanelForSideTab(EIHPCSideTab Tab) const
{
	switch (Tab)
	{
	case EIHPCSideTab::Actions:        return ActionsPanel;
	case EIHPCSideTab::PoseEstimation: return PoseEstimationContent;
	case EIHPCSideTab::Graphs:         return GraphsPanel;
	case EIHPCSideTab::Timeline:       return TaggedPointsList;
	case EIHPCSideTab::SavedVideos:    return SavedVideosList;
	case EIHPCSideTab::Settings:       return SettingsContent;
	default:                           return nullptr;
	}
}

void UCPP_UW_IHPCHud::RefreshPanelContent()
{
	const EIHPCSideTab AllTabs[] = { EIHPCSideTab::Actions, EIHPCSideTab::PoseEstimation, EIHPCSideTab::Graphs,
	                                 EIHPCSideTab::Timeline, EIHPCSideTab::SavedVideos, EIHPCSideTab::Settings };
	for (const EIHPCSideTab Tab : AllTabs)
	{
		if (UWidget* Content = GetPanelForSideTab(Tab))
		{
			Content->SetVisibility(Tab == DisplayedTab ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
		}
	}

	// Header = the tab's own name and picture (e.g. "Graphs" + the frosted graph icon).
	const UCPP_UW_IHPCSideTab* Tab = SideBar ? SideBar->GetTab(DisplayedTab) : nullptr;
	if (PanelTitle && Tab)
	{
		PanelTitle->SetText(Tab->Label);
	}
	if (PanelIcon && Tab && Tab->NormalTexture)
	{
		PanelIcon->SetBrushFromTexture(Tab->NormalTexture, /*bMatchSize*/ false);
	}
}

void UCPP_UW_IHPCHud::ApplyPanelSlide(float Alpha)
{
	bPanelSlideApplied = true;
	// Ease in / out so the slide does not start or stop abruptly.
	const float Eased = FMath::InterpEaseInOut(0.f, 1.f, FMath::Clamp(Alpha, 0.f, 1.f), 2.f);

	if (SidePanel)
	{
		SidePanel->SetRenderTranslation(FVector2D((Eased - 1.f) * SidePanelWidth, 0.f));
		// Visible (not just drawn) while open: the panel blocks clicks from reaching the 3D view behind it.
		SidePanel->SetVisibility(Alpha > 0.f ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
	if (SideBar)
	{
		SideBar->SetRenderTranslation(FVector2D(Eased * SideBarShiftWhenPanelOpen, 0.f));
	}
	if (Timeline)
	{
		Timeline->SetRenderTranslation(FVector2D(Eased * ContentShiftWhenPanelOpen, 0.f));
	}
	if (ZoomedGraphPanel)
	{
		ZoomedGraphPanel->SetRenderTranslation(FVector2D(Eased * ContentShiftWhenPanelOpen, 0.f));
	}
}

void UCPP_UW_IHPCHud::SetSideBarExpanded(bool bExpanded)
{
	if (SideBar)
	{
		SideBar->SetExpanded(bExpanded);
	}
}

bool UCPP_UW_IHPCHud::IsSideBarExpanded() const
{
	return SideBar && SideBar->IsExpanded();
}

UCPP_UW_IHPCLayerSwitcher* UCPP_UW_IHPCHud::GetLayerSwitcher() const
{
	return SideBar ? SideBar->GetLayerSwitcher() : nullptr;
}

UCPP_UW_IHPCChatPanel* UCPP_UW_IHPCHud::GetChatPanel() const
{
	return SideBar ? SideBar->GetChatPanel() : nullptr;
}

// ============================================================================
// Actions
// ============================================================================

bool UCPP_UW_IHPCHud::SelectAction(FName ActionName)
{
	return ActionsPanel ? ActionsPanel->SelectAction(ActionName) : false;
}

FName UCPP_UW_IHPCHud::GetPlayingAction() const
{
	return ActionsPanel ? ActionsPanel->GetPlayingAction() : NAME_None;
}

void UCPP_UW_IHPCHud::RefreshActionButtons()
{
	if (ActionsPanel)
	{
		ActionsPanel->RefreshCards();
	}
}

void UCPP_UW_IHPCHud::HandleActionSelected(FName PlayingAction, bool bStartedAction)
{
	OnActionChanged.Broadcast(PlayingAction);
	if (bCloseActionsPanelOnSelect && bStartedAction && SelectedTab == EIHPCSideTab::Actions)
	{
		ClosePanel();
	}
}

// ============================================================================
// Saved videos / tagged points / bookmarks
// ============================================================================

TArray<FIHPCTaggedMoment> UCPP_UW_IHPCHud::GetSavedVideos() const
{
	return SavedVideosList ? SavedVideosList->GetMoments() : TArray<FIHPCTaggedMoment>();
}

void UCPP_UW_IHPCHud::AddSavedVideo(const FIHPCTaggedMoment& Moment)
{
	if (SavedVideosList)
	{
		SavedVideosList->AddMoment(Moment);   // new card at the end of the list
	}
	AddTaggedPoint(Moment);
}

void UCPP_UW_IHPCHud::AddTaggedPoint(const FIHPCTaggedMoment& Moment)
{
	if (TaggedPointsList)
	{
		TaggedPointsList->AddTaggedPoint(Moment);
	}
}

void UCPP_UW_IHPCHud::HandleRecordingSaved(const FIHPCTaggedMoment& Moment)
{
	AddSavedVideo(Moment);   // the timeline already added its marker
}

void UCPP_UW_IHPCHud::HandleBookmarkAdded(const FIHPCTaggedMoment& Moment)
{
	AddTaggedPoint(Moment);  // the timeline already added its marker
}

void UCPP_UW_IHPCHud::HandleGraphBookmarkRequested(const FText& RegionName)
{
	// Same as the timeline's bookmark button, titled with the body region: marker + Timeline panel row.
	const FIHPCTaggedMoment Moment = UIHPCUILibrary::MakeMomentNow(this,
		FText::Format(GraphBookmarkTitleFormat, RegionName, FText::AsNumber(++GraphBookmarkCount)));
	if (Timeline)
	{
		Timeline->AddMarker(Moment);
	}
	AddTaggedPoint(Moment);
}

// ============================================================================
// Zoomed graph, reset view, chat
// ============================================================================

void UCPP_UW_IHPCHud::HandleZoomRequested()
{
	SetZoomedGraphVisible(!bZoomedGraphVisible);   // zoom icon toggles the large graph
}

void UCPP_UW_IHPCHud::HandleZoomedGraphCloseClicked()
{
	SetZoomedGraphVisible(false);
}

void UCPP_UW_IHPCHud::SetZoomedGraphVisible(bool bVisible)
{
	bZoomedGraphVisible = bVisible;

	// Copy the lines (and which ones are switched on) from the open region's Movement Graph.
	const UCPP_UW_IHPCGraphCard* Card = GraphsPanel ? GraphsPanel->GetGraphCard() : nullptr;
	if (bVisible && ZoomedGraph && Card && Card->GetMovementGraph())
	{
		ZoomedGraph->SetSeries(Card->GetMovementGraph()->GetSeries());
	}
	if (bVisible && ZoomedGraphTitle && Card)
	{
		ZoomedGraphTitle->SetText(Card->RegionName.IsEmpty()
			? LOCTEXT("ZoomTitle", "Movement Graph")
			: FText::Format(LOCTEXT("ZoomTitleRegion", "Movement Graph - {0}"), Card->RegionName));
	}
	if (ZoomedGraphPanel)
	{
		ZoomedGraphPanel->SetVisibility(bVisible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
}

void UCPP_UW_IHPCHud::HandleResetViewClicked()
{
	ResetView();
}

void UCPP_UW_IHPCHud::ResetView()
{
	if (UCPP_MouseFunctionComp* CameraControl = UIHPCUILibrary::FindAvatarCameraControl(this))
	{
		CameraControl->ResetView();
	}
}

void UCPP_UW_IHPCHud::HandleChatMessageSent(const FText& Message)
{
	OnChatMessageSent.Broadcast(Message);
}

// ============================================================================
// OLD nav bar calls
// ============================================================================

EIHPCSideTab UCPP_UW_IHPCHud::SideTabFromNavTab(EIHPCNavTab Tab)
{
	switch (Tab)
	{
	case EIHPCNavTab::SavedVideos:     return EIHPCSideTab::SavedVideos;
	case EIHPCNavTab::HistoryTimeline: return EIHPCSideTab::Actions;    // the old 4th tab was relabelled "Actions"
	case EIHPCNavTab::Settings:        return EIHPCSideTab::Settings;
	default:                           return EIHPCSideTab::None;       // Profile / Progress are not in the new design
	}
}

EIHPCNavTab UCPP_UW_IHPCHud::NavTabFromSideTab(EIHPCSideTab Tab)
{
	switch (Tab)
	{
	case EIHPCSideTab::SavedVideos: return EIHPCNavTab::SavedVideos;
	case EIHPCSideTab::Actions:     return EIHPCNavTab::HistoryTimeline;
	case EIHPCSideTab::Settings:    return EIHPCNavTab::Settings;
	default:                        return EIHPCNavTab::None;
	}
}

void UCPP_UW_IHPCHud::SelectTab(EIHPCNavTab Tab)
{
	if (Tab == EIHPCNavTab::Profile || Tab == EIHPCNavTab::Progress)
	{
		UE_LOG(LogTemp, Log, TEXT("[IHPC] SelectTab: Profile / Progress are not in the side bar design; closing the panel."));
	}
	SelectSideTab(SideTabFromNavTab(Tab));
}

EIHPCNavTab UCPP_UW_IHPCHud::GetSelectedTab() const
{
	return NavTabFromSideTab(SelectedTab);
}

#undef LOCTEXT_NAMESPACE

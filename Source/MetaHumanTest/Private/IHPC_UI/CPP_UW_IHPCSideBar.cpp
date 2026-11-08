// CPP_UW_IHPCSideBar.cpp - the side bar (BOT, layer buttons, tabs, chevron). See header.

#include "IHPC_UI/CPP_UW_IHPCSideBar.h"

#include "IHPC_UI/CPP_UW_IHPCChatPanel.h"
#include "IHPC_UI/CPP_UW_IHPCLayerSwitcher.h"
#include "IHPC_UI/CPP_UW_IHPCSideTab.h"
#include "IHPC_UI/IHPCUILibrary.h"

#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/Texture2D.h"

#define LOCTEXT_NAMESPACE "IHPCSideBar"

UCPP_UW_IHPCSideBar::UCPP_UW_IHPCSideBar(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

TArray<UCPP_UW_IHPCSideTab*> UCPP_UW_IHPCSideBar::GetTabs() const
{
	return { Tab_Actions, Tab_PoseEstimation, Tab_Graphs, Tab_Timeline, Tab_SavedVideos, Tab_Settings };
}

UCPP_UW_IHPCSideTab* UCPP_UW_IHPCSideBar::GetTab(EIHPCSideTab Tab) const
{
	switch (Tab)
	{
	case EIHPCSideTab::Actions:        return Tab_Actions;
	case EIHPCSideTab::PoseEstimation: return Tab_PoseEstimation;
	case EIHPCSideTab::Graphs:         return Tab_Graphs;
	case EIHPCSideTab::Timeline:       return Tab_Timeline;
	case EIHPCSideTab::SavedVideos:    return Tab_SavedVideos;
	case EIHPCSideTab::Settings:       return Tab_Settings;
	default:                           return nullptr;
	}
}

void UCPP_UW_IHPCSideBar::NativePreConstruct()
{
	Super::NativePreConstruct();

	// Each tab knows which tab it is, so the designer cannot mix them up.
	const TPair<UCPP_UW_IHPCSideTab*, EIHPCSideTab> Ids[] = {
		{ Tab_Actions, EIHPCSideTab::Actions }, { Tab_PoseEstimation, EIHPCSideTab::PoseEstimation },
		{ Tab_Graphs, EIHPCSideTab::Graphs }, { Tab_Timeline, EIHPCSideTab::Timeline },
		{ Tab_SavedVideos, EIHPCSideTab::SavedVideos }, { Tab_Settings, EIHPCSideTab::Settings } };
	for (const auto& Id : Ids)
	{
		if (Id.Key)
		{
			Id.Key->TabId = Id.Value;
		}
	}

	ApplyStyles();
	bExpanded = bStartExpanded;
	RefreshExpanded();
	bChatOpen = bStartChatOpen;
	if (ChatPanel)
	{
		ChatPanel->SetVisibility(bChatOpen ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
	}
}

void UCPP_UW_IHPCSideBar::NativeConstruct()
{
	Super::NativeConstruct();

	// Empty parts of the side bar's canvas must not swallow clicks meant for the 3D view.
	SetVisibility(ESlateVisibility::SelfHitTestInvisible);

	for (UCPP_UW_IHPCSideTab* Tab : GetTabs())
	{
		if (Tab)
		{
			Tab->OnTabClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCSideBar::HandleTabClicked);
		}
	}
	if (ExpandButton)
	{
		ExpandButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCSideBar::HandleExpandClicked);
	}
	if (BotButton)
	{
		BotButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCSideBar::HandleBotClicked);
		BotButton->SetToolTipText(LOCTEXT("BotTooltip", "Assistant"));
	}

	ApplyStyles();
	SetExpanded(bStartExpanded);
	SetChatOpen(bStartChatOpen);
	SetSelectedTab(SelectedTab);
}

void UCPP_UW_IHPCSideBar::ApplyStyles()
{
	UIHPCUILibrary::ApplyPictureButtonStyle(BotButton, BotTexture, BotButtonSize, 1.1f, 0.85f);
	UIHPCUILibrary::ApplyPictureButtonStyle(ExpandButton, ExpandButtonTexture, ExpandButtonSize);
}

void UCPP_UW_IHPCSideBar::SetExpanded(bool bInExpanded)
{
	const bool bChanged = bExpanded != bInExpanded;
	bExpanded = bInExpanded;
	RefreshExpanded();
	if (bChanged)
	{
		OnExpandedChanged.Broadcast();
	}
}

void UCPP_UW_IHPCSideBar::RefreshExpanded()
{
	if (ExtraTabs)
	{
		ExtraTabs->SetVisibility(bExpanded ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (ExpandIcon)
	{
		if (UTexture2D* Texture = bExpanded ? CollapseTexture.Get() : ExpandTexture.Get())
		{
			ExpandIcon->SetBrushFromTexture(Texture, /*bMatchSize*/ false);
		}
	}
	if (ExpandButton)
	{
		ExpandButton->SetToolTipText(bExpanded ? LOCTEXT("Collapse", "Hide tabs") : LOCTEXT("Expand", "Show all tabs"));
		if (UVerticalBoxSlot* ChevronSlot = Cast<UVerticalBoxSlot>(ExpandButton->Slot))
		{
			FMargin ChevronPadding = ChevronSlot->GetPadding();
			ChevronPadding.Top = bExpanded ? ExpandedChevronGap : CollapsedChevronGap;
			ChevronSlot->SetPadding(ChevronPadding);
		}
	}
}

void UCPP_UW_IHPCSideBar::SetSelectedTab(EIHPCSideTab Tab)
{
	SelectedTab = Tab;
	for (UCPP_UW_IHPCSideTab* SideTab : GetTabs())
	{
		if (SideTab)
		{
			SideTab->SetSelected(Tab != EIHPCSideTab::None && SideTab->TabId == Tab);
		}
	}
}

void UCPP_UW_IHPCSideBar::SetChatOpen(bool bOpen)
{
	bChatOpen = bOpen;
	if (ChatPanel)
	{
		// SelfHitTestInvisible: the window's empty margins pass clicks through, its buttons / text box still work.
		ChatPanel->SetVisibility(bOpen ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
		if (bOpen)
		{
			ChatPanel->FocusInput();
		}
	}
}

void UCPP_UW_IHPCSideBar::HandleTabClicked(EIHPCSideTab Tab)
{
	OnTabClicked.Broadcast(Tab);
}

void UCPP_UW_IHPCSideBar::HandleExpandClicked()
{
	ToggleExpanded();
}

void UCPP_UW_IHPCSideBar::HandleBotClicked()
{
	ToggleChat();
}

#undef LOCTEXT_NAMESPACE

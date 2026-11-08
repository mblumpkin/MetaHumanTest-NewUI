// CPP_UW_IHPCGraphsPanel.cpp - the Graphs side panel (body-region accordion). See header.

#include "IHPC_UI/CPP_UW_IHPCGraphsPanel.h"

#include "IHPC_UI/CPP_UW_IHPCAccordionHeader.h"
#include "IHPC_UI/CPP_UW_IHPCGraphCard.h"

#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

#define LOCTEXT_NAMESPACE "IHPCGraphsPanel"

UCPP_UW_IHPCGraphsPanel::UCPP_UW_IHPCGraphsPanel(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// Figma frame 20, top to bottom.
	Regions = {
		LOCTEXT("Arms", "Arms"), LOCTEXT("Legs", "Legs"), LOCTEXT("Torso", "Torso"), LOCTEXT("Neck", "Neck"),
		LOCTEXT("Chest", "Chest"), LOCTEXT("Hip", "Hip"), LOCTEXT("Biceps", "Biceps"), LOCTEXT("LowerBack", "Lower back"),
	};
}

void UCPP_UW_IHPCGraphsPanel::NativePreConstruct()
{
	Super::NativePreConstruct();
	// Not in the UMG designer: there the graph card is shown where it was placed (moving a designed widget
	// around inside the designer's preview confuses its hierarchy view).
	if (IsDesignTime())
	{
		return;
	}
	BuildHeaders();
	OpenRegionIndex = Regions.IsValidIndex(StartOpenRegion) ? StartOpenRegion : INDEX_NONE;
	Relayout();
}

void UCPP_UW_IHPCGraphsPanel::NativeConstruct()
{
	Super::NativeConstruct();
	BuildHeaders();
	OpenRegion(Regions.IsValidIndex(StartOpenRegion) ? StartOpenRegion : INDEX_NONE);
}

void UCPP_UW_IHPCGraphsPanel::BuildHeaders()
{
	if (!HeaderClass || !RegionList)
	{
		return;
	}
	if (Headers.Num() == Regions.Num())
	{
		return;   // already built (NativeConstruct runs again when the HUD is re-added to the viewport)
	}
	Headers.Reset();
	for (int32 i = 0; i < Regions.Num(); ++i)
	{
		UCPP_UW_IHPCAccordionHeader* Header = CreateWidget<UCPP_UW_IHPCAccordionHeader>(this, HeaderClass);
		if (!Header)
		{
			continue;
		}
		Header->SectionIndex = i;
		Header->SetLabel(Regions[i]);
		Header->OnHeaderClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCGraphsPanel::HandleHeaderClicked);
		Headers.Add(Header);
	}
}

void UCPP_UW_IHPCGraphsPanel::Relayout()
{
	if (!RegionList)
	{
		return;
	}
	RegionList->ClearChildren();
	if (GraphCard)
	{
		GraphCard->RemoveFromParent();   // it may start anywhere in the Blueprint
	}

	bool bPreviousWasCard = false;
	for (int32 i = 0; i < Headers.Num(); ++i)
	{
		UCPP_UW_IHPCAccordionHeader* Header = Headers[i];
		if (!Header)
		{
			continue;
		}
		const bool bOpen = (i == OpenRegionIndex);
		Header->SetOpen(bOpen);

		if (UVerticalBoxSlot* HeaderSlot = RegionList->AddChildToVerticalBox(Header))
		{
			const float Top = (i == 0) ? 0.f : (bPreviousWasCard ? CardToHeaderSpacing : HeaderSpacing);
			HeaderSlot->SetPadding(FMargin(0.f, Top, 0.f, 0.f));
			HeaderSlot->SetHorizontalAlignment(HAlign_Fill);
		}
		bPreviousWasCard = false;

		if (bOpen && GraphCard)
		{
			if (UVerticalBoxSlot* CardSlot = RegionList->AddChildToVerticalBox(GraphCard))
			{
				CardSlot->SetPadding(FMargin(0.f, HeaderToCardSpacing, 0.f, 0.f));
				CardSlot->SetHorizontalAlignment(HAlign_Fill);
			}
			bPreviousWasCard = true;
		}
	}

	if (GraphCard && !GraphCard->GetParent())
	{
		// No region open: keep the card in the list (so it stays alive and bound) but hidden.
		if (UVerticalBoxSlot* CardSlot = RegionList->AddChildToVerticalBox(GraphCard))
		{
			CardSlot->SetPadding(FMargin(0.f));
		}
		GraphCard->SetVisibility(ESlateVisibility::Collapsed);
	}
	else if (GraphCard)
	{
		GraphCard->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	}
}

void UCPP_UW_IHPCGraphsPanel::OpenRegion(int32 RegionIndex)
{
	OpenRegionIndex = Regions.IsValidIndex(RegionIndex) ? RegionIndex : INDEX_NONE;
	if (GraphCard && OpenRegionIndex != INDEX_NONE)
	{
		GraphCard->SetRegion(Regions[OpenRegionIndex], OpenRegionIndex);
	}
	Relayout();
	OnRegionChanged.Broadcast(OpenRegionIndex, Regions.IsValidIndex(OpenRegionIndex) ? Regions[OpenRegionIndex] : FText::GetEmpty());
}

void UCPP_UW_IHPCGraphsPanel::ToggleRegion(int32 RegionIndex)
{
	OpenRegion(RegionIndex == OpenRegionIndex ? INDEX_NONE : RegionIndex);
}

void UCPP_UW_IHPCGraphsPanel::HandleHeaderClicked(UCPP_UW_IHPCAccordionHeader* Header)
{
	if (Header)
	{
		ToggleRegion(Header->SectionIndex);
	}
}

#undef LOCTEXT_NAMESPACE

// CPP_UW_IHPCTaggedPointsList.cpp - the Timeline side panel's list of tagged points. See header.

#include "IHPC_UI/CPP_UW_IHPCTaggedPointsList.h"

#include "IHPC_UI/CPP_UW_IHPCListRow.h"
#include "IHPC_UI/IHPCUILibrary.h"

#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/Font.h"
#include "UObject/ConstructorHelpers.h"

UCPP_UW_IHPCTaggedPointsList::UCPP_UW_IHPCTaggedPointsList(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	// Fallback font (the Widget Blueprint sets Avenir Medium).
	if (!IsRunningDedicatedServer())
	{
		static ConstructorHelpers::FObjectFinder<UFont> DefaultFont(*UWidget::GetDefaultFontName());
		ListFont = FSlateFontInfo(DefaultFont.Object, 12, FName("Bold"));
	}
}

void UCPP_UW_IHPCTaggedPointsList::NativeConstruct()
{
	Super::NativeConstruct();
	RebuildRows();
}

void UCPP_UW_IHPCTaggedPointsList::SetTaggedPoints(const TArray<FIHPCTaggedMoment>& Points)
{
	TaggedPoints = Points;
	RebuildRows();
}

void UCPP_UW_IHPCTaggedPointsList::AddTaggedPoint(const FIHPCTaggedMoment& Point)
{
	TaggedPoints.Add(Point);
	RebuildRows();
}

void UCPP_UW_IHPCTaggedPointsList::RebuildRows()
{
	if (EmptyText)
	{
		EmptyText->SetVisibility(TaggedPoints.Num() == 0 ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (!PointsList)
	{
		return;
	}
	PointsList->ClearChildren();

	for (int32 i = 0; i < TaggedPoints.Num(); ++i)
	{
		const FIHPCTaggedMoment& Moment = TaggedPoints[i];
		UCPP_UW_IHPCListRow* Row = CreateWidget<UCPP_UW_IHPCListRow>(this, UCPP_UW_IHPCListRow::StaticClass());
		// Dot colour = the same green-to-red severity colour as the video card's bar.
		Row->Setup(Moment.Title, Moment.TimeText, UIHPCUILibrary::SeverityToColor(Moment.Severity), ListFont, /*bClickable*/ true);
		Row->RowIndex = i;
		Row->OnRowClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCTaggedPointsList::HandleRowClicked);
		if (UVerticalBoxSlot* RowSlot = PointsList->AddChildToVerticalBox(Row))
		{
			RowSlot->SetPadding(FMargin(0.f, i > 0 ? RowSpacing : 0.f, 0.f, 0.f));
		}
	}
}

void UCPP_UW_IHPCTaggedPointsList::HandleRowClicked(UCPP_UW_IHPCListRow* Row)
{
	if (!Row || !TaggedPoints.IsValidIndex(Row->RowIndex))
	{
		return;
	}
	const FIHPCTaggedMoment& Moment = TaggedPoints[Row->RowIndex];
	if (bSeekTimelineOnClick)
	{
		UIHPCUILibrary::SeekAvatarTimeline(this, Moment.NormalizedTime);
	}
	OnTaggedPointClicked.Broadcast(Moment);
}

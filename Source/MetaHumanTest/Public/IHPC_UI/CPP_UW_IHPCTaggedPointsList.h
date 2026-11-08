// CPP_UW_IHPCTaggedPointsList.h
// -----------------------------------------------------------------------------
// Content of the "Timeline" side panel (side bar tab: list with bullets). The FINAL FESTIVAL page does not draw
// this panel's content, so it shows what the old "Tagged Points" accordion section showed:
//
//   (o) Soleus Muscle (R) ........... 13:55 p.m.     <- dot colour = severity (green -> red)
//   (o) Neck Axis (C2) .............. 13:55 p.m.
//   (o) Recording 1 ................. 15:02 p.m.     <- added by the timeline's Record button
//   (o) Arms 15:04 p.m. ............. 15:04 p.m.     <- added by a bookmark (timeline or graph card)
//
// Clicking a row jumps the avatar animation to that moment (same as clicking its orange marker on the timeline).
//
// Widget Blueprint: /Game/UserInterface/IHPC/Widgets/WBP_IHPC_TaggedPointsList
//   Needs a VerticalBox "PointsList" (inside a ScrollBox); rows are UCPP_UW_IHPCListRow, made in code.
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IHPC_UI/IHPCTypes.h"
#include "CPP_UW_IHPCTaggedPointsList.generated.h"

class UTextBlock;
class UVerticalBox;
class UCPP_UW_IHPCListRow;

UCLASS(Abstract)
class METAHUMANTEST_API UCPP_UW_IHPCTaggedPointsList : public UUserWidget
{
	GENERATED_BODY()

public:
	UCPP_UW_IHPCTaggedPointsList(const FObjectInitializer& ObjectInitializer);

	/** Jump the avatar animation to a moment when its row is clicked. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Behaviour")
	bool bSeekTimelineOnClick = true;

	/** Row text font. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	FSlateFontInfo ListFont;

	/** Space between rows (px). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	float RowSpacing = 4.f;

	UPROPERTY(BlueprintAssignable, Category = "IHPC|Events")
	FIHPCMomentEvent OnTaggedPointClicked;

	UFUNCTION(BlueprintCallable, Category = "IHPC|TaggedPoints")
	void SetTaggedPoints(const TArray<FIHPCTaggedMoment>& Points);

	UFUNCTION(BlueprintCallable, Category = "IHPC|TaggedPoints")
	void AddTaggedPoint(const FIHPCTaggedMoment& Point);

	UFUNCTION(BlueprintPure, Category = "IHPC|TaggedPoints")
	TArray<FIHPCTaggedMoment> GetTaggedPoints() const { return TaggedPoints; }

protected:
	virtual void NativeConstruct() override;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UVerticalBox> PointsList;

	/** Optional "nothing here yet" text, shown while the list is empty. */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> EmptyText;

private:
	UFUNCTION() void HandleRowClicked(UCPP_UW_IHPCListRow* Row);

	void RebuildRows();

	UPROPERTY()
	TArray<FIHPCTaggedMoment> TaggedPoints;
};

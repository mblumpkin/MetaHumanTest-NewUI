// CPP_UW_IHPCGraphsPanel.h
// -----------------------------------------------------------------------------
// Content of the "Graphs" side panel (side bar tab: line chart). Figma page "FINAL FESTIVAL", frames 20-22:
// an accordion of body regions. Click a region to open its graphs; only one region is open at a time.
//
//   [ Arms        v ]      <- WBP_IHPC_AccordionHeader (270 x 47), 10 px apart
//   [ Legs        ^ ]      <- open
//   +---------------+
//   |  graph card   |      <- the ONE WBP_IHPC_GraphCard, moved under whichever header is open
//   +---------------+         (10 px below its header, 17 px above the next one - Figma frame 21)
//   [ Torso       v ]
//   ...  Neck, Chest, Hip, Biceps, Lower back
//
// The headers are made in code from Regions (so a region is added by typing its name in Class Defaults).
//
// Widget Blueprint: /Game/UserInterface/IHPC/Widgets/WBP_IHPC_GraphsPanel
//   Needs a VerticalBox "RegionList" (inside a ScrollBox) and a WBP_IHPC_GraphCard "GraphCard" (any parent: it is
//   moved into RegionList in code).
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IHPC_UI/IHPCTypes.h"
#include "CPP_UW_IHPCGraphsPanel.generated.h"

class UVerticalBox;
class UCPP_UW_IHPCAccordionHeader;
class UCPP_UW_IHPCGraphCard;

/** The open region changed (Index = INDEX_NONE / -1 when all are closed). */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FIHPCRegionChanged, int32, RegionIndex, const FText&, RegionName);

UCLASS(Abstract)
class METAHUMANTEST_API UCPP_UW_IHPCGraphsPanel : public UUserWidget
{
	GENERATED_BODY()

public:
	UCPP_UW_IHPCGraphsPanel(const FObjectInitializer& ObjectInitializer);

	/** Body regions, top to bottom (Figma: Arms, Legs, Torso, Neck, Chest, Hip, Biceps, Lower back). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Graphs")
	TArray<FText> Regions;

	/** Region open when the panel first appears (-1 = all closed, Figma frame 20). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Graphs")
	int32 StartOpenRegion = -1;

	/** Widget Blueprint used for each header (WBP_IHPC_AccordionHeader). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Setup")
	TSubclassOf<UCPP_UW_IHPCAccordionHeader> HeaderClass;

	/** Gap between two closed headers (Figma: 10). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Layout")
	float HeaderSpacing = 10.f;

	/** Gap between an open header and its graph card (Figma: 10). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Layout")
	float HeaderToCardSpacing = 10.f;

	/** Gap between the graph card and the next header (Figma: 17). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Layout")
	float CardToHeaderSpacing = 17.f;

	UPROPERTY(BlueprintAssignable, Category = "IHPC|Events")
	FIHPCRegionChanged OnRegionChanged;

	/** Opens one region (and closes the others). -1 closes all. */
	UFUNCTION(BlueprintCallable, Category = "IHPC|Graphs")
	void OpenRegion(int32 RegionIndex);

	/** Opens the region, or closes it if it is open (what a header click does). */
	UFUNCTION(BlueprintCallable, Category = "IHPC|Graphs")
	void ToggleRegion(int32 RegionIndex);

	UFUNCTION(BlueprintPure, Category = "IHPC|Graphs")
	int32 GetOpenRegion() const { return OpenRegionIndex; }

	UFUNCTION(BlueprintPure, Category = "IHPC|Graphs")
	UCPP_UW_IHPCGraphCard* GetGraphCard() const { return GraphCard; }

protected:
	virtual void NativePreConstruct() override;
	virtual void NativeConstruct() override;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UVerticalBox> RegionList;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCGraphCard> GraphCard;

private:
	UFUNCTION() void HandleHeaderClicked(UCPP_UW_IHPCAccordionHeader* Header);

	/** Creates the headers (once per Regions change). */
	void BuildHeaders();

	/** Puts headers + the graph card into RegionList in the right order with the right gaps. */
	void Relayout();

	UPROPERTY()
	TArray<TObjectPtr<UCPP_UW_IHPCAccordionHeader>> Headers;

	int32 OpenRegionIndex = INDEX_NONE;
};

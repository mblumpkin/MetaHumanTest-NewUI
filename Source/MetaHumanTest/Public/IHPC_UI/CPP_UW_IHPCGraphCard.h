// CPP_UW_IHPCGraphCard.h
// -----------------------------------------------------------------------------
// The open section of the Graphs panel (Figma page "FINAL FESTIVAL", frames 21 / 22, "Rectangle 47" group):
//
//   +--------------------------------+   270 x 447, rgba(0,0,0,0.41), radius 11
//   |         Movement Graph         |
//   |   [ live line graph ]          |
//   |         Active Muscles         |
//   |   [ live line graph ]          |
//   |  (o)| Bones                    |   <- toggle switches = line filters
//   |  (o)| Nerves                   |
//   |  (o)| Muscles                  |
//   |  (o)| Tendons                  |
//   |               [bm] [dl] [zoom] |   <- bookmark / download (CSV) / zoom (large graph)
//   +--------------------------------+
//
// Same content and behaviour as "Show graphs" in the old accordion (Component 3), for ONE body region at a time:
//   * Toggles: none on = every line shows (the Figma state); turn some on to show only those lines.
//   * Download: both graphs -> <Project>/Saved/IHPC_Exports/IHPC_Graphs_<Region>_<date>_<time>.csv
//   * Zoom: asks the HUD to show a large copy of the Movement Graph (OnZoomRequested).
//   * Bookmark (new in Figma): asks the HUD to bookmark the current moment for this region (OnBookmarkRequested);
//     it becomes an orange marker on the timeline and a row in the Timeline panel.
//   * A green playhead on both graphs follows the avatar animation.
// Until real data is connected, SetRegion gives every region its own sample curves (GenerateDemoData).
//
// Widget Blueprint: /Game/UserInterface/IHPC/Widgets/WBP_IHPC_GraphCard (inside WBP_IHPC_GraphsPanel).
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IHPC_UI/IHPCTypes.h"
#include "CPP_UW_IHPCGraphCard.generated.h"

class UButton;
class UCPP_UW_IHPCLineGraph;
class UCPP_UW_IHPCToggleSwitch;

/** Fired when the CSV export finishes (full file path). */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIHPCGraphExportFinished, const FString&, FilePath);

UCLASS(Abstract)
class METAHUMANTEST_API UCPP_UW_IHPCGraphCard : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Body region the graphs are for (e.g. "Arms"). Used in the CSV file name and in bookmark titles. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Graphs")
	FText RegionName;

	/** Give each region different sample curves (only while the graphs show demo data). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Graphs")
	bool bNewDemoDataPerRegion = true;

	// ---------------------------------------------------------------- events

	UPROPERTY(BlueprintAssignable, Category = "IHPC|Events")
	FIHPCSimpleEvent OnZoomRequested;

	/** The bookmark icon was clicked. Text = the region name. */
	UPROPERTY(BlueprintAssignable, Category = "IHPC|Events")
	FIHPCTextEvent OnBookmarkRequested;

	UPROPERTY(BlueprintAssignable, Category = "IHPC|Events")
	FIHPCGraphExportFinished OnGraphsExported;

	// ---------------------------------------------------------------- functions

	/** Shows the graphs for a body region. Seed changes the sample curves while there is no real data. */
	UFUNCTION(BlueprintCallable, Category = "IHPC|Graphs")
	void SetRegion(const FText& InRegionName, int32 Seed);

	/** Writes both graphs to <Project>/Saved/IHPC_Exports/IHPC_Graphs_<Region>_<date>_<time>.csv; returns the path. */
	UFUNCTION(BlueprintCallable, Category = "IHPC|Graphs")
	FString ExportGraphsToCSV();

	UFUNCTION(BlueprintPure, Category = "IHPC|Graphs")
	UCPP_UW_IHPCLineGraph* GetMovementGraph() const { return MovementGraph; }

	UFUNCTION(BlueprintPure, Category = "IHPC|Graphs")
	UCPP_UW_IHPCLineGraph* GetActiveMusclesGraph() const { return ActiveMusclesGraph; }

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCLineGraph> MovementGraph;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCLineGraph> ActiveMusclesGraph;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCToggleSwitch> Toggle_Bones;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCToggleSwitch> Toggle_Nerves;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCToggleSwitch> Toggle_Muscles;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCToggleSwitch> Toggle_Tendons;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> DownloadButton;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> ZoomButton;
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UButton> BookmarkButton;

private:
	UFUNCTION() void HandleDownload();
	UFUNCTION() void HandleZoom();
	UFUNCTION() void HandleBookmark();
	UFUNCTION() void HandleToggleChanged(UCPP_UW_IHPCToggleSwitch* Switch, bool bIsOn);

	/** Shows / hides the lines according to the four toggles. */
	void ApplyToggleFilter();

	/** Bones, Nerves, Muscles, Tendons (= the series order of UCPP_UW_IHPCLineGraph::MakeDefaultSeriesLayout). */
	TArray<UCPP_UW_IHPCToggleSwitch*> GetToggles() const;
};

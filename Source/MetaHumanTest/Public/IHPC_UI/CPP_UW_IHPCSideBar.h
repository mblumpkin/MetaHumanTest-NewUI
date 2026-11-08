// CPP_UW_IHPCSideBar.h
// -----------------------------------------------------------------------------
// The SIDE BAR on the left of the screen (Figma page "FINAL FESTIVAL"). It replaced the old drop-down nav bar:
// the nav bar's tabs are now extra round tabs in this bar.
//
//    (BOT)          <- assistant avatar: opens / closes the chat window (Figma component "BOT")
//   +-----+         <- pill "Rectangle 24": rgba(12,39,61,0.59), 69 wide, fully rounded
//   | (=) |   Body      \
//   | (m) |   Muscles    > layer switcher (WBP_IHPC_LayerSwitcher, same C++ as before - drives the AnatomyView)
//   | (s) |   Skeleton  /
//   |  -  |  ---------------------------------------------------- ExtraTabs (hidden while collapsed)
//   | (a) |   Action
//   |  -  |
//   | (p) |   Pose Estimation
//   | (g) |   Graphs
//   |  -  |
//   | (t) |   Timeline
//   | (v) |   Saved Videos
//   | (o) |   Settings
//   |     |  ----------------------------------------------------
//   | (^) |   chevron: down = expand (frame 15), up = collapse (frame 16)
//   +-----+
//
// Collapsed (Figma frames 15 / 17): only the BOT, the three layer buttons and the down chevron (pill 272 tall).
// Expanded (frames 16 / 18 / 19-22): all tabs (pill 689 tall). The pill shrinks / grows by itself (auto size).
// Clicking a tab fires OnTabClicked; the HUD opens / closes that tab's panel and calls SetSelectedTab.
//
// Widget Blueprint: /Game/UserInterface/IHPC/Widgets/WBP_IHPC_SideBar (lives inside WBP_IHPC_HUD as "SideBar").
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IHPC_UI/IHPCTypes.h"
#include "CPP_UW_IHPCSideBar.generated.h"

class UButton;
class UImage;
class UTexture2D;
class UCPP_UW_IHPCSideTab;
class UCPP_UW_IHPCLayerSwitcher;
class UCPP_UW_IHPCChatPanel;

UCLASS(Abstract)
class METAHUMANTEST_API UCPP_UW_IHPCSideBar : public UUserWidget
{
	GENERATED_BODY()

public:
	UCPP_UW_IHPCSideBar(const FObjectInitializer& ObjectInitializer);

	// ---------------------------------------------------------------- settings

	/** Start with every tab showing (Figma frame 16) instead of collapsed (frame 15). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Behaviour")
	bool bStartExpanded = false;

	/** Open the chat window when the game starts. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Behaviour")
	bool bStartChatOpen = false;

	/** Assistant avatar picture (Figma "ihpc ui fe-05 1", drawn as a 69 px circle). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> BotTexture;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	FVector2D BotButtonSize = FVector2D(69.f, 69.f);

	/** Empty frosted glass circle behind the chevron (Icons/Button.png). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> ExpandButtonTexture;

	/** Figma "Group 30": 57 x 57. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	FVector2D ExpandButtonSize = FVector2D(57.f, 57.f);

	/** White chevron pointing down, shown while collapsed (click = expand). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> ExpandTexture;

	/** White chevron pointing up, shown while expanded (click = collapse). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> CollapseTexture;

	/** Space above the chevron (Figma: 32 px below Settings when expanded, 27 px below Skeleton when collapsed). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Layout")
	float ExpandedChevronGap = 32.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Layout")
	float CollapsedChevronGap = 27.f;

	// ---------------------------------------------------------------- events

	/** A tab was clicked (the HUD opens / closes its panel). */
	UPROPERTY(BlueprintAssignable, Category = "IHPC|Events")
	FIHPCSideTabEvent OnTabClicked;

	/** The bar was expanded / collapsed. */
	UPROPERTY(BlueprintAssignable, Category = "IHPC|Events")
	FIHPCSimpleEvent OnExpandedChanged;

	// ---------------------------------------------------------------- functions

	UFUNCTION(BlueprintCallable, Category = "IHPC|SideBar")
	void SetExpanded(bool bInExpanded);

	UFUNCTION(BlueprintCallable, Category = "IHPC|SideBar")
	void ToggleExpanded() { SetExpanded(!bExpanded); }

	UFUNCTION(BlueprintPure, Category = "IHPC|SideBar")
	bool IsExpanded() const { return bExpanded; }

	/** Shows Tab in its selected (dark blue) look and every other tab normal. None = no tab selected. */
	UFUNCTION(BlueprintCallable, Category = "IHPC|SideBar")
	void SetSelectedTab(EIHPCSideTab Tab);

	/** The round tab button for Tab (null for None). Its Label / NormalTexture are used for the panel title. */
	UFUNCTION(BlueprintPure, Category = "IHPC|SideBar")
	UCPP_UW_IHPCSideTab* GetTab(EIHPCSideTab Tab) const;

	/** The Body / Muscles / Skeleton buttons at the top of the bar. */
	UFUNCTION(BlueprintPure, Category = "IHPC|SideBar")
	UCPP_UW_IHPCLayerSwitcher* GetLayerSwitcher() const { return LayerSwitcher; }

	UFUNCTION(BlueprintPure, Category = "IHPC|SideBar")
	UCPP_UW_IHPCChatPanel* GetChatPanel() const { return ChatPanel; }

	UFUNCTION(BlueprintCallable, Category = "IHPC|Chat")
	void SetChatOpen(bool bOpen);

	UFUNCTION(BlueprintCallable, Category = "IHPC|Chat")
	void ToggleChat() { SetChatOpen(!IsChatOpen()); }

	UFUNCTION(BlueprintPure, Category = "IHPC|Chat")
	bool IsChatOpen() const { return bChatOpen; }

	TArray<UCPP_UW_IHPCSideTab*> GetTabs() const;

protected:
	virtual void NativePreConstruct() override;
	virtual void NativeConstruct() override;

	/** The assistant avatar (opens the chat window). */
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> BotButton;

	/** Everything between the layer buttons and the chevron (separators + the six tabs). Hidden while collapsed. */
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UWidget> ExtraTabs;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> ExpandButton;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UImage> ExpandIcon;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCSideTab> Tab_Actions;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCSideTab> Tab_PoseEstimation;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCSideTab> Tab_Graphs;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCSideTab> Tab_Timeline;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCSideTab> Tab_SavedVideos;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UCPP_UW_IHPCSideTab> Tab_Settings;

	/** WBP_IHPC_LayerSwitcher, stacked vertically (it used to be its own widget at the bottom right). */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UCPP_UW_IHPCLayerSwitcher> LayerSwitcher;

	/** WBP_IHPC_ChatPanel, to the right of the BOT avatar. Hidden until the avatar is clicked. */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UCPP_UW_IHPCChatPanel> ChatPanel;

private:
	UFUNCTION() void HandleTabClicked(EIHPCSideTab Tab);
	UFUNCTION() void HandleExpandClicked();
	UFUNCTION() void HandleBotClicked();

	/** Shows / hides the extra tabs, swaps the chevron and its tooltip, sets the gap above it. */
	void RefreshExpanded();

	void ApplyStyles();

	bool bExpanded = false;
	bool bChatOpen = false;
	EIHPCSideTab SelectedTab = EIHPCSideTab::None;
};

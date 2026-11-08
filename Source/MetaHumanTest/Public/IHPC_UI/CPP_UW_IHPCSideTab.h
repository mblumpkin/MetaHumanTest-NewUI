// CPP_UW_IHPCSideTab.h
// -----------------------------------------------------------------------------
// ONE round icon button in the side bar (Figma page "FINAL FESTIVAL", frames 16-22).
// The side bar's extra tabs (they replaced the old drop-down nav bar):
//   Action (running man) | Pose Estimation (stick figure), Graphs (line chart) |
//   Timeline (list), Saved Videos (film strip), Settings (gear)
//
// Two looks, from the high-quality pictures in <Project>/Icons:
//   NormalTexture : frosted glass circle + white icon   (e.g. "Graph.png")
//   ActiveTexture : dark blue glossy circle + white icon (e.g. "Active Graph.png") - the selected tab
// Both pictures are 211 x 211; the active one fills its picture, the normal circle is inset 12 px, so drawn at the
// same size (55 x 55 as in Figma) the selected tab looks a bit bigger, like in Figma frame 20.
//
// Widget Blueprint: /Game/UserInterface/IHPC/Widgets/WBP_IHPC_SideTab
//   It must contain a Button named "TabButton". The side bar (WBP_IHPC_SideBar) holds one per tab and sets TabId.
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IHPC_UI/IHPCTypes.h"
#include "CPP_UW_IHPCSideTab.generated.h"

class UButton;
class UTexture2D;

UCLASS(Abstract)
class METAHUMANTEST_API UCPP_UW_IHPCSideTab : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Which tab this is. Set on each instance in WBP_IHPC_SideBar. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Tab")
	EIHPCSideTab TabId = EIHPCSideTab::None;

	/** Name of the tab: tooltip on the button and title of the panel it opens (e.g. "Graphs"). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Tab")
	FText Label;

	/** Frosted glass circle + white icon (Icons/<Name>.png). Also used as the panel title icon. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> NormalTexture;

	/** Dark blue glossy circle + white icon (Icons/Active <Name>.png), shown while the tab is selected. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> ActiveTexture;

	/** Size the button picture is drawn at (Figma: 55 x 54, square pictures -> 55 x 55). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	FVector2D ButtonSize = FVector2D(55.f, 55.f);

	/** Brightness while the mouse is over the button / while it is pressed (same as the timeline buttons). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	float HoveredTint = 1.15f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	float PressedTint = 0.8f;

	/** Broadcast when the user clicks this tab. The side bar forwards it to the HUD. */
	UPROPERTY(BlueprintAssignable, Category = "IHPC|Tab")
	FIHPCSideTabEvent OnTabClicked;

	/** Selected tabs show the ActiveTexture. */
	UFUNCTION(BlueprintCallable, Category = "IHPC|Tab")
	void SetSelected(bool bInSelected);

	UFUNCTION(BlueprintPure, Category = "IHPC|Tab")
	bool IsSelected() const { return bSelected; }

protected:
	virtual void NativePreConstruct() override;   // runs in the UMG designer too, so the icon shows while editing
	virtual void NativeConstruct() override;

	UPROPERTY(meta = (BindWidget))
	TObjectPtr<UButton> TabButton;

private:
	UFUNCTION()
	void HandleClicked();

	/** Gives the button the normal or active picture (with hover / pressed brightness). */
	void RefreshVisuals();

	bool bSelected = false;
};

// CPP_UW_IHPCActionCard.h
// -----------------------------------------------------------------------------
// ONE card in the Action panel. Figma page "FINAL FESTIVAL", frame 19 ("Rectangle 101 ... 110"):
//
//   +---------------------------+
//   | Idle         (mannequin)  |   269 x 147, radius 14. Picture: mannequin on dark navy, with a gradient to
//   |                           |   rgba(211,216,169,0.53) at the bottom (baked into T_IHPC_ActionCard).
//   +---------------------------+   Label: Avenir Heavy 20 px (15 pt), white, top-left.
//
// The card shows one FIHPCActionInfo. Clicking it tells the Action panel, which plays the action on the avatar.
// The playing action's card gets the green outline (SelectionHighlight); actions the possessed pawn cannot do are
// greyed out (disabled).
//
// Widget Blueprint: /Game/UserInterface/IHPC/Widgets/WBP_IHPC_ActionCard
//   Needs a Button "CardButton" and a TextBlock "CardLabel"; optional Image "CardPicture" and widget
//   "SelectionHighlight".
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "IHPC_UI/IHPCTypes.h"
#include "CPP_UW_IHPCActionCard.generated.h"

class UButton;
class UImage;
class UTextBlock;
class UCPP_UW_IHPCActionCard;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIHPCActionCardClicked, UCPP_UW_IHPCActionCard*, Card);

UCLASS(Abstract)
class METAHUMANTEST_API UCPP_UW_IHPCActionCard : public UUserWidget
{
	GENERATED_BODY()

public:
	/** What this card shows. Editable in the designer for previewing; the Action panel sets it in game. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Card")
	FIHPCActionInfo Info;

	/** Index in the Action panel's Actions list (set by the panel). */
	UPROPERTY(BlueprintReadOnly, Category = "IHPC|Card")
	int32 CardIndex = INDEX_NONE;

	UPROPERTY(BlueprintAssignable, Category = "IHPC|Card")
	FIHPCActionCardClicked OnCardClicked;

	UFUNCTION(BlueprintCallable, Category = "IHPC|Card")
	void SetInfo(const FIHPCActionInfo& InInfo);

	UFUNCTION(BlueprintPure, Category = "IHPC|Card")
	FIHPCActionInfo GetInfo() const { return Info; }

	/** Green outline on the card of the action the avatar is doing. */
	UFUNCTION(BlueprintCallable, Category = "IHPC|Card")
	void SetPlaying(bool bInPlaying);

	UFUNCTION(BlueprintPure, Category = "IHPC|Card")
	bool IsPlaying() const { return bPlaying; }

	/** False = greyed out and not clickable (the possessed pawn has no clip for this action). */
	UFUNCTION(BlueprintCallable, Category = "IHPC|Card")
	void SetAvailable(bool bAvailable);

protected:
	virtual void NativePreConstruct() override;
	virtual void NativeConstruct() override;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> CardButton;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> CardLabel;

	/** The card picture. If the action has its own Picture it replaces the Blueprint's picture. */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UImage> CardPicture;

	/** Outline shown while this card's action is playing. */
	UPROPERTY(meta = (BindWidgetOptional)) TObjectPtr<UWidget> SelectionHighlight;

private:
	UFUNCTION()
	void HandleClicked();

	/** Copies Info into the label / picture. */
	void ApplyInfo();

	bool bPlaying = false;
};

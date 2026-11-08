// CPP_UW_IHPCAccordionHeader.h
// -----------------------------------------------------------------------------
// ONE header row of the Graphs panel accordion (Figma page "FINAL FESTIVAL", frames 20-22):
//
//   [ Arms                                   v ]    270 x 47, rgba(217,217,217,0.2), radius 11
//                                                   label Inter Bold 16 -> Avenir Heavy 12 pt at x 21,
//                                                   chevron 14 x 9 at x 236 (down = closed, up = open)
//
// Widget Blueprint: /Game/UserInterface/IHPC/Widgets/WBP_IHPC_AccordionHeader
//   Needs a Button "HeaderButton", a TextBlock "HeaderLabel" and an Image "HeaderChevron".
//   The Graphs panel creates one per body region.
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "CPP_UW_IHPCAccordionHeader.generated.h"

class UButton;
class UImage;
class UTextBlock;
class UTexture2D;
class UCPP_UW_IHPCAccordionHeader;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIHPCAccordionHeaderClicked, UCPP_UW_IHPCAccordionHeader*, Header);

UCLASS(Abstract)
class METAHUMANTEST_API UCPP_UW_IHPCAccordionHeader : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "IHPC|Header")
	FText Label;

	/** Chevron while the section is open (Figma: up). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> ChevronOpenTexture;

	/** Chevron while the section is closed (Figma: down). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC|Style")
	TObjectPtr<UTexture2D> ChevronClosedTexture;

	/** Which section this header is (set by the panel that creates it). */
	UPROPERTY(BlueprintReadOnly, Category = "IHPC|Header")
	int32 SectionIndex = INDEX_NONE;

	UPROPERTY(BlueprintAssignable, Category = "IHPC|Header")
	FIHPCAccordionHeaderClicked OnHeaderClicked;

	UFUNCTION(BlueprintCallable, Category = "IHPC|Header")
	void SetLabel(const FText& InLabel);

	UFUNCTION(BlueprintCallable, Category = "IHPC|Header")
	void SetOpen(bool bInOpen);

	UFUNCTION(BlueprintPure, Category = "IHPC|Header")
	bool IsOpen() const { return bOpen; }

protected:
	virtual void NativePreConstruct() override;
	virtual void NativeConstruct() override;

	UPROPERTY(meta = (BindWidget)) TObjectPtr<UButton> HeaderButton;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UTextBlock> HeaderLabel;
	UPROPERTY(meta = (BindWidget)) TObjectPtr<UImage> HeaderChevron;

private:
	UFUNCTION()
	void HandleClicked();

	void RefreshVisuals();

	bool bOpen = false;
};

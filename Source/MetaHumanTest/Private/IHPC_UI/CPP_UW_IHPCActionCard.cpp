// CPP_UW_IHPCActionCard.cpp - one card in the Action panel. See header.

#include "IHPC_UI/CPP_UW_IHPCActionCard.h"

#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"

void UCPP_UW_IHPCActionCard::NativePreConstruct()
{
	Super::NativePreConstruct();
	ApplyInfo();          // designer preview shows the label
	SetPlaying(bPlaying);
}

void UCPP_UW_IHPCActionCard::NativeConstruct()
{
	Super::NativeConstruct();
	if (CardButton)
	{
		CardButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCActionCard::HandleClicked);
	}
}

void UCPP_UW_IHPCActionCard::SetInfo(const FIHPCActionInfo& InInfo)
{
	Info = InInfo;
	ApplyInfo();
}

void UCPP_UW_IHPCActionCard::ApplyInfo()
{
	if (CardLabel)
	{
		CardLabel->SetText(Info.Label);
	}
	if (CardPicture && Info.Picture)
	{
		CardPicture->SetBrushFromTexture(Info.Picture, /*bMatchSize*/ false);
	}
}

void UCPP_UW_IHPCActionCard::SetPlaying(bool bInPlaying)
{
	bPlaying = bInPlaying;
	if (SelectionHighlight)
	{
		SelectionHighlight->SetVisibility(bPlaying ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
	}
}

void UCPP_UW_IHPCActionCard::SetAvailable(bool bAvailable)
{
	SetIsEnabled(bAvailable);
	SetRenderOpacity(bAvailable ? 1.f : 0.45f);
	if (CardButton)
	{
		CardButton->SetToolTipText(bAvailable ? FText::GetEmpty()
			: NSLOCTEXT("IHPCActionCard", "NoClip", "This character has no animation for this action yet."));
	}
}

void UCPP_UW_IHPCActionCard::HandleClicked()
{
	OnCardClicked.Broadcast(this);
}

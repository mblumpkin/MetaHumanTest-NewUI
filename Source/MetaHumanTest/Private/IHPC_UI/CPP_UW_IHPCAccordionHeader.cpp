// CPP_UW_IHPCAccordionHeader.cpp - one header row of the Graphs panel accordion. See header.

#include "IHPC_UI/CPP_UW_IHPCAccordionHeader.h"

#include "Components/Button.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Engine/Texture2D.h"

void UCPP_UW_IHPCAccordionHeader::NativePreConstruct()
{
	Super::NativePreConstruct();
	RefreshVisuals();
}

void UCPP_UW_IHPCAccordionHeader::NativeConstruct()
{
	Super::NativeConstruct();
	if (HeaderButton)
	{
		HeaderButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCAccordionHeader::HandleClicked);
	}
	RefreshVisuals();
}

void UCPP_UW_IHPCAccordionHeader::SetLabel(const FText& InLabel)
{
	Label = InLabel;
	RefreshVisuals();
}

void UCPP_UW_IHPCAccordionHeader::SetOpen(bool bInOpen)
{
	bOpen = bInOpen;
	RefreshVisuals();
}

void UCPP_UW_IHPCAccordionHeader::HandleClicked()
{
	OnHeaderClicked.Broadcast(this);
}

void UCPP_UW_IHPCAccordionHeader::RefreshVisuals()
{
	if (HeaderLabel && !Label.IsEmpty())
	{
		HeaderLabel->SetText(Label);
	}
	if (HeaderChevron)
	{
		if (UTexture2D* Texture = bOpen ? ChevronOpenTexture.Get() : ChevronClosedTexture.Get())
		{
			HeaderChevron->SetBrushFromTexture(Texture, /*bMatchSize*/ false);
		}
	}
}

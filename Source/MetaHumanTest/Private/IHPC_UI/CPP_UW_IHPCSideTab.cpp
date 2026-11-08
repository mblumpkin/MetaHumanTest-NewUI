// CPP_UW_IHPCSideTab.cpp - one round icon button in the side bar. See header.

#include "IHPC_UI/CPP_UW_IHPCSideTab.h"

#include "IHPC_UI/IHPCUILibrary.h"

#include "Components/Button.h"
#include "Engine/Texture2D.h"

void UCPP_UW_IHPCSideTab::NativePreConstruct()
{
	Super::NativePreConstruct();
	if (TabButton)
	{
		TabButton->SetToolTipText(Label);
	}
	RefreshVisuals();
}

void UCPP_UW_IHPCSideTab::NativeConstruct()
{
	Super::NativeConstruct();
	if (TabButton)
	{
		TabButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCSideTab::HandleClicked);
	}
	RefreshVisuals();
}

void UCPP_UW_IHPCSideTab::SetSelected(bool bInSelected)
{
	if (bSelected != bInSelected)
	{
		bSelected = bInSelected;
		RefreshVisuals();
	}
}

void UCPP_UW_IHPCSideTab::HandleClicked()
{
	OnTabClicked.Broadcast(TabId);   // the HUD decides what selecting this tab means
}

void UCPP_UW_IHPCSideTab::RefreshVisuals()
{
	UTexture2D* Texture = (bSelected && ActiveTexture) ? ActiveTexture.Get() : NormalTexture.Get();
	UIHPCUILibrary::ApplyPictureButtonStyle(TabButton, Texture, ButtonSize, HoveredTint, PressedTint);
}

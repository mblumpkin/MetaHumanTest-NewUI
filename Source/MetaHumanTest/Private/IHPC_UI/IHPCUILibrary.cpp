// IHPCUILibrary.cpp - see IHPCUILibrary.h for what each function is for.

#include "IHPC_UI/IHPCUILibrary.h"

#include "AnimationTimelineComp.h"   // existing project component that scrubs the avatar animation
#include "../../CPP_MouseFunctionComp.h"   // module root (not on the include path): mouse orbit / pan / zoom
#include "Components/Button.h"
#include "Engine/Texture2D.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

UAnimationTimelineComp* UIHPCUILibrary::FindAvatarTimeline(const UObject* WorldContextObject)
{
	// Player 0's pawn is the avatar the user is looking at (same pawn the existing
	// WCPP_AnimationTimeline widget talks to).
	APawn* Pawn = UGameplayStatics::GetPlayerPawn(WorldContextObject, 0);
	return Pawn ? Pawn->FindComponentByClass<UAnimationTimelineComp>() : nullptr;
}

bool UIHPCUILibrary::SeekAvatarTimeline(const UObject* WorldContextObject, float NormalizedTime, bool bPauseAfterSeek)
{
	UAnimationTimelineComp* Timeline = FindAvatarTimeline(WorldContextObject);
	if (!Timeline)
	{
		UE_LOG(LogTemp, Warning, TEXT("[IHPC UI] No AnimationTimelineComp on the player pawn - cannot jump to %.2f"), NormalizedTime);
		return false;
	}

	// Stop playback first so the timeline does not immediately move away from the moment.
	if (bPauseAfterSeek)
	{
		Timeline->Pause();
	}
	Timeline->SetNormalizedTime(FMath::Clamp(NormalizedTime, 0.f, 1.f));
	return true;
}

float UIHPCUILibrary::GetAvatarTimelineTime(const UObject* WorldContextObject)
{
	const UAnimationTimelineComp* Timeline = FindAvatarTimeline(WorldContextObject);
	return Timeline ? Timeline->GetNormalizedTime() : -1.f;
}

bool UIHPCUILibrary::PlayAvatar(const UObject* WorldContextObject, bool bRestartIfAtEnd)
{
	UAnimationTimelineComp* Timeline = FindAvatarTimeline(WorldContextObject);
	if (!Timeline)
	{
		return false;
	}
	// At the end of the clip, pressing play should start again instead of doing nothing.
	if (bRestartIfAtEnd && Timeline->GetNormalizedTime() >= 0.999f)
	{
		Timeline->SetNormalizedTime(0.f);
	}
	Timeline->PlayForward();
	return true;
}

bool UIHPCUILibrary::PauseAvatar(const UObject* WorldContextObject)
{
	UAnimationTimelineComp* Timeline = FindAvatarTimeline(WorldContextObject);
	if (!Timeline)
	{
		return false;
	}
	Timeline->Pause();
	return true;
}

bool UIHPCUILibrary::IsAvatarPlaying(const UObject* WorldContextObject)
{
	const UAnimationTimelineComp* Timeline = FindAvatarTimeline(WorldContextObject);
	return Timeline && Timeline->IsPlaying();
}

bool UIHPCUILibrary::SetAvatarPlaySpeed(const UObject* WorldContextObject, float Speed)
{
	UAnimationTimelineComp* Timeline = FindAvatarTimeline(WorldContextObject);
	if (!Timeline)
	{
		return false;
	}
	// PlaySpeed is used every frame by UAnimationTimelineComp::TickComponent, so changing it
	// takes effect immediately, even while the animation is playing.
	Timeline->PlaySpeed = FMath::Max(Speed, 0.01f);
	return true;
}

float UIHPCUILibrary::GetAvatarPlaySpeed(const UObject* WorldContextObject)
{
	const UAnimationTimelineComp* Timeline = FindAvatarTimeline(WorldContextObject);
	return Timeline ? Timeline->PlaySpeed : -1.f;
}

FText UIHPCUILibrary::FormatFigmaDate(const FDateTime& When)
{
	static const TCHAR* Months[] = { TEXT("Jan"), TEXT("Feb"), TEXT("Mar"), TEXT("Apr"), TEXT("May"), TEXT("Jun"),
	                                 TEXT("Jul"), TEXT("Aug"), TEXT("Sep"), TEXT("Oct"), TEXT("Nov"), TEXT("Dec") };
	const int32 Day = When.GetDay();
	// 1st, 2nd, 3rd, 4th ... 11th, 12th, 13th ... 21st, 22nd, 23rd ...
	const TCHAR* Suffix = TEXT("th");
	if (Day % 100 < 11 || Day % 100 > 13)
	{
		switch (Day % 10)
		{
		case 1: Suffix = TEXT("st"); break;
		case 2: Suffix = TEXT("nd"); break;
		case 3: Suffix = TEXT("rd"); break;
		default: break;
		}
	}
	return FText::FromString(FString::Printf(TEXT("%s %d%s, %d"), Months[When.GetMonth() - 1], Day, Suffix, When.GetYear()));
}

FText UIHPCUILibrary::FormatFigmaTime(const FDateTime& When)
{
	// Figma shows "13:55 p.m." (24-hour clock + a.m./p.m.), so keep exactly that style.
	const int32 Hour = When.GetHour();
	return FText::FromString(FString::Printf(TEXT("%02d:%02d %s"), Hour, When.GetMinute(), Hour < 12 ? TEXT("a.m.") : TEXT("p.m.")));
}

FLinearColor UIHPCUILibrary::FigmaColor(const FString& Hex, float Opacity)
{
	// Figma colours are sRGB. Building an FColor and converting it to FLinearColor
	// does the sRGB -> linear conversion Unreal expects, so the colour on screen matches Figma.
	FLinearColor Color = FLinearColor(FColor::FromHex(Hex));
	Color.A = FMath::Clamp(Opacity, 0.f, 1.f);
	return Color;
}

FLinearColor UIHPCUILibrary::SeverityToColor(float Severity)
{
	// Colours sampled from the bar at the top of the Figma video cards.
	struct FStop { float At; const TCHAR* Hex; };
	static const FStop Stops[] = {
		{ 0.00f, TEXT("70BF44") },   // green
		{ 0.45f, TEXT("F2DE1C") },   // yellow
		{ 0.75f, TEXT("F7A21F") },   // orange
		{ 1.00f, TEXT("ED1C24") },   // red
	};

	const float S = FMath::Clamp(Severity, 0.f, 1.f);
	for (int32 i = 1; i < UE_ARRAY_COUNT(Stops); ++i)
	{
		if (S <= Stops[i].At)
		{
			const float Alpha = (S - Stops[i - 1].At) / (Stops[i].At - Stops[i - 1].At);
			return FLinearColor::LerpUsingHSV(FigmaColor(Stops[i - 1].Hex), FigmaColor(Stops[i].Hex), Alpha);
		}
	}
	return FigmaColor(Stops[UE_ARRAY_COUNT(Stops) - 1].Hex);
}

void UIHPCUILibrary::ApplyPictureButtonStyle(UButton* Button, UTexture2D* Texture, FVector2D Size, float HoveredTint, float PressedTint)
{
	if (!Button || !Texture)
	{
		return;   // keep whatever look the Widget Blueprint has
	}

	auto MakeBrush = [&](float Tint, float Alpha)
	{
		FSlateBrush Brush;
		Brush.SetResourceObject(Texture);
		Brush.ImageSize = Size;
		Brush.DrawAs = ESlateBrushDrawType::Image;
		Brush.TintColor = FSlateColor(FLinearColor(Tint, Tint, Tint, Alpha));
		return Brush;
	};

	FButtonStyle Style = Button->GetStyle();
	Style.SetNormal(MakeBrush(1.f, 1.f));
	Style.SetHovered(MakeBrush(HoveredTint, 1.f));
	Style.SetPressed(MakeBrush(PressedTint, 1.f));
	Style.SetDisabled(MakeBrush(0.5f, 0.5f));
	Style.SetNormalPadding(FMargin(0.f));
	Style.SetPressedPadding(FMargin(0.f));
	Button->SetStyle(Style);
	Button->SetBackgroundColor(FLinearColor::White);
}

void UIHPCUILibrary::ApplyRoundedButtonStyle(UButton* Button, FLinearColor Color, float CornerRadius, float HoveredTint, float PressedTint)
{
	if (!Button)
	{
		return;
	}
	auto Scaled = [&Color](float Tint)
	{
		return FLinearColor(Color.R * Tint, Color.G * Tint, Color.B * Tint, Color.A);
	};
	FButtonStyle Style = Button->GetStyle();
	Style.SetNormal(MakeRoundedBrush(Color, CornerRadius));
	Style.SetHovered(MakeRoundedBrush(Scaled(HoveredTint), CornerRadius));
	Style.SetPressed(MakeRoundedBrush(Scaled(PressedTint), CornerRadius));
	FLinearColor Disabled = Color;
	Disabled.A *= 0.5f;
	Style.SetDisabled(MakeRoundedBrush(Disabled, CornerRadius));
	Style.SetNormalPadding(FMargin(0.f));
	Style.SetPressedPadding(FMargin(0.f));
	Button->SetStyle(Style);
	Button->SetBackgroundColor(FLinearColor::White);
}

FSlateBrush UIHPCUILibrary::MakeRoundedBrush(FLinearColor Color, float CornerRadius)
{
	FSlateBrush Brush;
	Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
	Brush.TintColor = FSlateColor(Color);
	Brush.OutlineSettings.CornerRadii = FVector4(CornerRadius, CornerRadius, CornerRadius, CornerRadius);
	Brush.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
	Brush.OutlineSettings.Color = FSlateColor(FLinearColor::Transparent);
	Brush.OutlineSettings.Width = 0.f;
	return Brush;
}

UCPP_MouseFunctionComp* UIHPCUILibrary::FindAvatarCameraControl(const UObject* WorldContextObject)
{
	APawn* Pawn = UGameplayStatics::GetPlayerPawn(WorldContextObject, 0);
	return Pawn ? Pawn->FindComponentByClass<UCPP_MouseFunctionComp>() : nullptr;
}

FIHPCTaggedMoment UIHPCUILibrary::MakeMomentNow(const UObject* WorldContextObject, const FText& Title, float Severity)
{
	const FDateTime Now = FDateTime::Now();
	const float Time = FMath::Max(GetAvatarTimelineTime(WorldContextObject), 0.f);
	return FIHPCTaggedMoment(Title, FormatFigmaDate(Now), FormatFigmaTime(Now), FMath::Clamp(Severity, 0.f, 1.f), Time);
}

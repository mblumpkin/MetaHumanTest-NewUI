// IHPCTypes.h
// -----------------------------------------------------------------------------
// Shared data types for the IHPC (Avatar Injury Prevention) UI that was built
// from the Figma file "Avatar Injury Prevention Program".
//
// Nothing in this file draws anything. It only describes the DATA the widgets
// pass around, so every widget agrees on the same shapes:
//   * EIHPCSideTab         - the tabs in the side bar (Figma page "FINAL FESTIVAL"), which replaced the nav bar
//   * EIHPCNavTab          - the five tabs of the OLD drop-down nav bar (kept so old Blueprint calls still compile)
//   * EIHPCAnatomyLayer    - the three layer buttons at the top of the side bar (Body / Muscles / Skeleton)
//   * EIHPCAccordionSection- the three sections of the old graph accordion
//   * FIHPCActionInfo      - one card in the Action panel (Idle, Running, Jogging ...)
//   * FIHPCTaggedMoment    - one saved video / tagged point (a video card)
//   * FIHPCGraphSeries     - one coloured line in a line graph
// -----------------------------------------------------------------------------

#pragma once

#include "CoreMinimal.h"
#include "IHPCTypes.generated.h"

class UTexture2D;

/** The tabs in the SIDE BAR (Figma page "FINAL FESTIVAL", frames 16-22). Each one opens its panel on the left of
 *  the screen. None = no tab selected / no panel open.
 *  Side bar order, top to bottom: Actions | Pose Estimation, Graphs | Timeline, Saved Videos, Settings. */
UENUM(BlueprintType)
enum class EIHPCSideTab : uint8
{
	None           UMETA(DisplayName = "None"),
	Actions        UMETA(DisplayName = "Action (running man)"),
	PoseEstimation UMETA(DisplayName = "Pose Estimation (stick figure)"),
	Graphs         UMETA(DisplayName = "Graphs (line chart)"),
	Timeline       UMETA(DisplayName = "Timeline (tagged points list)"),
	SavedVideos    UMETA(DisplayName = "Saved Videos (film strip)"),
	Settings       UMETA(DisplayName = "Settings (gear)")
};

/** The tabs in the OLD drop-down nav bar (Figma page "Default iPad Version": "Profile", "Progress", "Saved Videos",
 *  "History & Timeline" and "Settings"). The nav bar was replaced by the side bar (EIHPCSideTab); this enum is kept
 *  so Blueprints that call SelectTab(...) / listen to OnTabChanged keep compiling. None = no tab selected. */
UENUM(BlueprintType)
enum class EIHPCNavTab : uint8
{
	None            UMETA(DisplayName = "None"),
	Profile         UMETA(DisplayName = "Profile"),
	Progress        UMETA(DisplayName = "Progress"),
	SavedVideos     UMETA(DisplayName = "Saved Videos"),
	HistoryTimeline UMETA(DisplayName = "History & Timeline"),
	Settings        UMETA(DisplayName = "Settings")
};

/** The three round buttons of the layer switcher (Figma "ihpc ui rttd 2"): which part of the avatar is shown. */
UENUM(BlueprintType)
enum class EIHPCAnatomyLayer : uint8
{
	Body     UMETA(DisplayName = "Body (layers icon)"),
	Muscles  UMETA(DisplayName = "Muscles"),
	Skeleton UMETA(DisplayName = "Skeleton")
};

/** The sections of the graph accordion (Figma "Component 3"). Only one can be open at a time. */
UENUM(BlueprintType)
enum class EIHPCAccordionSection : uint8
{
	None          UMETA(DisplayName = "None (all closed)"),
	ShowGraphs    UMETA(DisplayName = "Show graphs"),
	ActiveMuscles UMETA(DisplayName = "Active Muscles"),
	TaggedPoints  UMETA(DisplayName = "Tagged Points")
};

/**
 * One saved video / tagged moment. A video card in the "videos row" shows one of these,
 * and the "Tagged Points" list in the accordion shows the same data.
 * Example from Figma: "Soleus Muscle (R)", "Jan 4th, 2026", "13:55 p.m."
 */
USTRUCT(BlueprintType)
struct FIHPCTaggedMoment
{
	GENERATED_BODY()

	/** Big bold line on the card, e.g. "Soleus Muscle (R)". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FText Title;

	/** First small line, e.g. "Jan 4th, 2026". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FText DateText;

	/** Second small line, e.g. "13:55 p.m.". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FText TimeText;

	/** Where the white tick sits on the green-to-red bar at the top of the card.
	 *  0 = far left (green, low risk) ... 1 = far right (red, high risk). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float Severity = 0.f;

	/** Where this moment is on the avatar's animation timeline (0 = start, 1 = end).
	 *  Clicking the card jumps the existing animation timeline to this point. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float NormalizedTime = 0.f;

	FIHPCTaggedMoment() = default;

	FIHPCTaggedMoment(const FText& InTitle, const FText& InDate, const FText& InTime, float InSeverity, float InNormalizedTime)
		: Title(InTitle), DateText(InDate), TimeText(InTime), Severity(InSeverity), NormalizedTime(InNormalizedTime)
	{
	}
};

/**
 * One card in the Action panel (Figma frame 19: "Idle", "Running", "Jugging", "Jumping").
 * Clicking the card plays ActionName on the possessed pawn's UAnimationTimelineComp (its Action Clips map, per pawn).
 *   * bIsDefault ("Idle"): always available. Plays the pawn's "Idle" clip if it has one, otherwise goes back to the
 *     pawn's own animation (StopAction + the walk / jog / run speed it had before a card changed it).
 *   * LocomotionSpeed >= 0: used when the pawn has NO clip for ActionName - the card drives the pawn's built-in
 *     walk / jog / run instead (ACPP_AbbyCharacter::Speed, 0 = walk, 0.62 = jog, 1 = run).
 *   * Otherwise a pawn without the clip shows the card greyed out.
 */
USTRUCT(BlueprintType)
struct FIHPCActionInfo
{
	GENERATED_BODY()

	/** Text on the card, e.g. "Running". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FText Label;

	/** Key in the pawn's AnimationTimelineComp > Action Clips, e.g. "Running", "TennisForehand". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FName ActionName;

	/** The "Idle" card: always clickable, means "no special action". Exactly one card should have this. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	bool bIsDefault = false;

	/** If >= 0 and the pawn has no clip for ActionName: set the pawn's locomotion speed to this (0 walk ... 1 run). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC", meta = (ClampMin = "-1", ClampMax = "1"))
	float LocomotionSpeed = -1.f;

	/** Optional picture for this card (empty = the panel's Default Card Picture). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	TObjectPtr<UTexture2D> Picture = nullptr;

	FIHPCActionInfo() = default;

	FIHPCActionInfo(const FText& InLabel, FName InActionName, bool bInIsDefault = false, float InLocomotionSpeed = -1.f)
		: Label(InLabel), ActionName(InActionName), bIsDefault(bInIsDefault), LocomotionSpeed(InLocomotionSpeed)
	{
	}
};

/** One coloured line in a line graph (e.g. the "Bones" line). */
USTRUCT(BlueprintType)
struct FIHPCGraphSeries
{
	GENERATED_BODY()

	/** Name shown in the legend and written to the CSV export, e.g. "Bones". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FText Name;

	/** Colour of the line on the graph. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FLinearColor LineColor = FLinearColor::White;

	/** Colour of the little legend bar next to the toggle (exact Figma colour). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	FLinearColor LegendColor = FLinearColor::White;

	/** The data points, evenly spaced from the left edge to the right edge of the graph. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	TArray<float> Values;

	/** If false the line is not drawn (controlled by the Bones/Nerves/Muscles/Tendons toggles). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "IHPC")
	bool bVisible = true;
};

// -----------------------------------------------------------------------------
// Events ("delegates") shared by several widgets. Blueprint can bind to these.
// -----------------------------------------------------------------------------

/** An event with no data, e.g. "zoom button clicked". */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FIHPCSimpleEvent);

/** An event that carries one tagged moment, e.g. "this video card was chosen". */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIHPCMomentEvent, const FIHPCTaggedMoment&, Moment);

/** A side bar tab was clicked / the open side panel changed. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIHPCSideTabEvent, EIHPCSideTab, Tab);

/** An event that carries a piece of text, e.g. "the user sent this chat message". */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FIHPCTextEvent, const FText&, Text);

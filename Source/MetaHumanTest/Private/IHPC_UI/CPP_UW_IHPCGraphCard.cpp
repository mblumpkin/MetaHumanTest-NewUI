// CPP_UW_IHPCGraphCard.cpp - the open section of the Graphs panel. See header.

#include "IHPC_UI/CPP_UW_IHPCGraphCard.h"

#include "IHPC_UI/CPP_UW_IHPCLineGraph.h"
#include "IHPC_UI/CPP_UW_IHPCToggleSwitch.h"
#include "IHPC_UI/IHPCUILibrary.h"

#include "Components/Button.h"
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

#define LOCTEXT_NAMESPACE "IHPCGraphCard"

void UCPP_UW_IHPCGraphCard::NativeConstruct()
{
	Super::NativeConstruct();

	if (DownloadButton) DownloadButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCGraphCard::HandleDownload);
	if (ZoomButton)     ZoomButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCGraphCard::HandleZoom);
	if (BookmarkButton) BookmarkButton->OnClicked.AddUniqueDynamic(this, &UCPP_UW_IHPCGraphCard::HandleBookmark);

	for (UCPP_UW_IHPCToggleSwitch* Toggle : GetToggles())
	{
		if (Toggle)
		{
			Toggle->OnToggled.AddUniqueDynamic(this, &UCPP_UW_IHPCGraphCard::HandleToggleChanged);
		}
	}

	// The two graphs should not show identical sample curves.
	if (ActiveMusclesGraph && MovementGraph && ActiveMusclesGraph->DemoSeed == MovementGraph->DemoSeed)
	{
		ActiveMusclesGraph->GenerateDemoData(ActiveMusclesGraph->DemoSeed + 7);
	}
	ApplyToggleFilter();
}

void UCPP_UW_IHPCGraphCard::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	// Playhead on both graphs follows the avatar animation (-1 hides it when there is no timeline).
	const float Time = UIHPCUILibrary::GetAvatarTimelineTime(this);
	if (MovementGraph)      MovementGraph->SetPlayheadTime(Time);
	if (ActiveMusclesGraph) ActiveMusclesGraph->SetPlayheadTime(Time);
}

void UCPP_UW_IHPCGraphCard::SetRegion(const FText& InRegionName, int32 Seed)
{
	RegionName = InRegionName;

	// Sample curves only: real data (SetSeries on the graphs) is never replaced.
	if (bNewDemoDataPerRegion)
	{
		if (MovementGraph && MovementGraph->IsShowingDemoData())
		{
			MovementGraph->GenerateDemoData(MovementGraph->DemoSeed + Seed * 13);
		}
		if (ActiveMusclesGraph && ActiveMusclesGraph->IsShowingDemoData())
		{
			ActiveMusclesGraph->GenerateDemoData(ActiveMusclesGraph->DemoSeed + 7 + Seed * 13);
		}
	}
	ApplyToggleFilter();   // new curves come in all visible - re-apply the switches
}

TArray<UCPP_UW_IHPCToggleSwitch*> UCPP_UW_IHPCGraphCard::GetToggles() const
{
	return { Toggle_Bones, Toggle_Nerves, Toggle_Muscles, Toggle_Tendons };
}

void UCPP_UW_IHPCGraphCard::HandleToggleChanged(UCPP_UW_IHPCToggleSwitch* Switch, bool bIsOn)
{
	ApplyToggleFilter();
}

void UCPP_UW_IHPCGraphCard::ApplyToggleFilter()
{
	const TArray<UCPP_UW_IHPCToggleSwitch*> Toggles = GetToggles();
	bool bAnyOn = false;
	for (const UCPP_UW_IHPCToggleSwitch* Toggle : Toggles)
	{
		bAnyOn |= (Toggle && Toggle->IsOn());
	}
	for (int32 i = 0; i < Toggles.Num(); ++i)
	{
		// No toggle on -> show everything (Figma default). Otherwise only the switched-on lines.
		const bool bShow = !bAnyOn || (Toggles[i] && Toggles[i]->IsOn());
		if (MovementGraph)      MovementGraph->SetSeriesVisible(i, bShow);
		if (ActiveMusclesGraph) ActiveMusclesGraph->SetSeriesVisible(i, bShow);
	}
}

void UCPP_UW_IHPCGraphCard::HandleDownload()
{
	ExportGraphsToCSV();
}

void UCPP_UW_IHPCGraphCard::HandleZoom()
{
	OnZoomRequested.Broadcast();
}

void UCPP_UW_IHPCGraphCard::HandleBookmark()
{
	OnBookmarkRequested.Broadcast(RegionName);
}

FString UCPP_UW_IHPCGraphCard::ExportGraphsToCSV()
{
	// <Project>/Saved/IHPC_Exports/IHPC_Graphs_Arms_20260106_135500.csv
	FString Region = RegionName.ToString();
	Region.ReplaceInline(TEXT(" "), TEXT(""));
	Region = FPaths::MakeValidFileName(Region);
	const FString Folder = FPaths::ProjectSavedDir() / TEXT("IHPC_Exports");
	IFileManager::Get().MakeDirectory(*Folder, /*Tree*/ true);
	const FString FileName = Region.IsEmpty()
		? FString::Printf(TEXT("IHPC_Graphs_%s.csv"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")))
		: FString::Printf(TEXT("IHPC_Graphs_%s_%s.csv"), *Region, *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
	const FString FilePath = FPaths::ConvertRelativePathToFull(Folder / FileName);

	FString Csv;
	const FString RegionColumn = RegionName.ToString().Replace(TEXT(","), TEXT(" "));
	auto AppendGraph = [&Csv, &RegionColumn](const TCHAR* GraphName, const UCPP_UW_IHPCLineGraph* Graph)
	{
		if (!Graph)
		{
			return;
		}
		const TArray<FIHPCGraphSeries> Series = Graph->GetSeries();

		// Header row: Region,Graph,Sample,NormalizedTime,Bones,Nerves,Muscles,Tendons
		if (Csv.IsEmpty())
		{
			Csv += TEXT("Region,Graph,Sample,NormalizedTime");
			for (const FIHPCGraphSeries& S : Series)
			{
				Csv += TEXT(",") + S.Name.ToString();
			}
			Csv += LINE_TERMINATOR;
		}

		int32 NumSamples = 0;
		for (const FIHPCGraphSeries& S : Series)
		{
			NumSamples = FMath::Max(NumSamples, S.Values.Num());
		}
		for (int32 i = 0; i < NumSamples; ++i)
		{
			const float T = NumSamples > 1 ? static_cast<float>(i) / (NumSamples - 1) : 0.f;
			Csv += FString::Printf(TEXT("%s,%s,%d,%.4f"), *RegionColumn, GraphName, i, T);
			for (const FIHPCGraphSeries& S : Series)
			{
				Csv += S.Values.IsValidIndex(i) ? FString::Printf(TEXT(",%.5f"), S.Values[i]) : FString(TEXT(","));
			}
			Csv += LINE_TERMINATOR;
		}
	};

	AppendGraph(TEXT("Movement Graph"), MovementGraph);
	AppendGraph(TEXT("Active Muscles"), ActiveMusclesGraph);

	if (FFileHelper::SaveStringToFile(Csv, *FilePath))
	{
		UE_LOG(LogTemp, Log, TEXT("[IHPC UI] Graphs exported to %s"), *FilePath);
		if (DownloadButton)
		{
			// Hovering the download icon tells the user where the file went.
			DownloadButton->SetToolTipText(FText::Format(LOCTEXT("SavedTo", "Saved to {0}"), FText::FromString(FilePath)));
		}
		OnGraphsExported.Broadcast(FilePath);
		return FilePath;
	}
	UE_LOG(LogTemp, Error, TEXT("[IHPC UI] Could not write %s"), *FilePath);
	return FString();
}

#undef LOCTEXT_NAMESPACE

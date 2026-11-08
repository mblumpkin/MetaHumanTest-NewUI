// Mouse camera control on the pawn: orbit (RMB), pan (LMB) and zoom (wheel) the pawn's spring arm.
// The player controller only routes the input here.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CPP_MouseFunctionComp.generated.h"

class USpringArmComponent;

UCLASS( ClassGroup=(Custom), meta=(BlueprintSpawnableComponent) )
class METAHUMANTEST_API UCPP_MouseFunctionComp : public UActorComponent
{
	GENERATED_BODY()

public:
	UCPP_MouseFunctionComp();

	/** Rotate the camera around the character by a mouse delta (pixels). Callable from Blueprint / Python
	 *  (scripted camera moves, screenshots), the controller calls it while the right button is held. */
	UFUNCTION(BlueprintCallable, Category="Mouse")
	void OrbitFromMouse(const FVector2D& MouseDelta);

	/** Move the camera closer (+) / farther (-) by scroll steps. */
	UFUNCTION(BlueprintCallable, Category="Mouse")
	void ZoomCamera(float AxisValue);

	/** Slide the camera target by a mouse delta (pixels). */
	UFUNCTION(BlueprintCallable, Category="Mouse")
	void PanFromMouse(const FVector2D& MouseDelta);

	/** Re-read the spring arm's current rotation / length (call after moving it from somewhere else). */
	UFUNCTION(BlueprintCallable)
	void SyncFromCurrentSpringArm();

	/** Put the camera back where it was before the first orbit / pan / zoom (the IHPC HUD's round "reset view"
	 *  button, Figma FINAL FESTIVAL frame 17). Does nothing if the view was never moved. */
	UFUNCTION(BlueprintCallable, Category="Mouse")
	void ResetView();

	/** True once the user has orbited / panned / zoomed away from the starting view. */
	UFUNCTION(BlueprintPure, Category="Mouse")
	bool IsViewChanged() const;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Mouse")
	TObjectPtr<USpringArmComponent> SpringArmComponent = nullptr;

	UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Mouse Speed")
	float YawSpeedDegPerPx = 1.f;

	UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Mouse Speed")
	float PitchSpeedDegPerPx = 1.f;

	/** Orbit pitch limits, so the camera can't flip over the top or under the floor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mouse Speed")
	float MinPitch = -80.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Mouse Speed")
	float MaxPitch = 80.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="MetaHuman")
	TArray<TObjectPtr<AActor>> PlayerPlaceHolders;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Pan")
	float PanSpeed = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zoom")
	float ZoomSpeed = 50.f;  // how fast we zoom per scroll step

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zoom")
	float MinZoom = 50.f;   // closest

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Zoom")
	float MaxZoom = 1200.f;  // farthest

	/** Current spring arm length we're using */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Zoom")
	float CurrentCameraDistance = 0.f;

	FRotator CurrentArmRot;

protected:
	virtual void BeginPlay() override;

private:
	/** Remembers the spring arm's view the first time the user moves it (the view ResetView goes back to). */
	void RememberStartViewIfNeeded();

	bool bHasStartView = false;
	FRotator StartArmRotation = FRotator::ZeroRotator;
	FVector StartArmLocation = FVector::ZeroVector;
	float StartArmLength = 0.f;
};
